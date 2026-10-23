#!/usr/bin/env python3
"""產生廣播用「開始／結束」提示音（SOP-21）。純 Python 合成波形，ffmpeg 只負責量響度與轉 mp3。

用法（在 HA 容器內執行，ffmpeg 只在容器內有）：
  python3 /config/scripts/make_chimes.py            # 產生全部
  python3 /config/scripts/make_chimes.py weather_start weather_end   # 只產生指定的
  python3 /config/scripts/make_chimes.py --list     # 列出清單

設計原則：
  * 開始音依「資訊類別」不同；結束音是同一組音符「反向下行、較短、較輕」，最後落在較低的音，有收尾感。
  * 緊急類（地震、疏散、緊急模式）用警報感（方波＋奇次諧波、起音很快）；
    天氣、保全用中性電子音／鐘聲；一般生活通知用柔和鐘琴式衰減。
  * 響度以 LUFS 為目標（開始音約 -13.5，緊急類 -12.5，結束音比開始音輕約 3 dB），峰值限制在 -1.5 dBFS。
  * 想調整音色或音符：只改下面的 SPECS 表格，再重跑本腳本；其他程式不用動。
輸出：/media/<name>.mp3（44.1 kHz、單聲道）
"""
import math, os, re, struct, subprocess, sys, tempfile, wave

SR = 44100
OUT_DIR = os.environ.get("CHIME_OUT", "/media")

# ── 音色：每個泛音 (倍頻, 相對振幅, 衰減速率/秒)；alarm 用方波近似（奇次諧波 1/n） ──
TIMBRES = {
    "bell":   dict(partials=[(1, 1.0, 5.0), (2, 0.45, 8.0), (3.0, 0.18, 12.0)], attack=0.003),
    "soft":   dict(partials=[(1, 1.0, 6.5), (2, 0.30, 10.0)], attack=0.006),
    "electro": dict(partials=[(1, 1.0, 2.2), (2, 0.35, 3.0), (3, 0.12, 4.0)], attack=0.008),
    "alarm":  dict(partials=[(1, 1.0, 0.0), (3, 0.33, 0.0), (5, 0.20, 0.0), (7, 0.14, 0.0)], attack=0.003, hard=True),
}

# ── 音效表：events = (開始秒, 長度秒, 起始頻率Hz, 結束頻率Hz（滑音，同起始＝不滑）, 力度 0~1) ──
# lufs：目標響度；tail：最後一個音後面保留的衰減尾巴（秒）
C5, E5, G5, C6 = 523.25, 659.25, 783.99, 1046.5
SPECS = {
    # ── 開始音 ──
    "weather_start": dict(timbre="electro", lufs=-13.5, tail=0.35, events=[
        (0.00, 0.20, C5, C5, 1.0), (0.20, 0.20, E5, E5, 1.0), (0.40, 0.20, G5, G5, 1.0), (0.60, 0.55, C6, C6, 1.0)]),
    "evac_start": dict(timbre="alarm", lufs=-12.5, tail=0.05, events=[
        (0.25 * i, 0.23, 960.0 if i % 2 == 0 else 770.0, 960.0 if i % 2 == 0 else 770.0, 1.0) for i in range(8)]),
    "emergency_start": dict(timbre="alarm", lufs=-12.5, tail=0.10, events=[
        (0.00, 0.14, 1000.0, 1000.0, 1.0), (0.24, 0.14, 1000.0, 1000.0, 1.0), (0.48, 0.14, 1000.0, 1000.0, 1.0),
        (0.72, 0.60, 500.0, 500.0, 0.9)]),
    "security_start": dict(timbre="bell", lufs=-13.5, tail=0.30, events=[
        (0.00, 0.30, 880.0, 880.0, 1.0), (0.30, 0.30, 660.0, 660.0, 1.0),
        (0.60, 0.30, 880.0, 880.0, 1.0), (0.90, 0.35, 660.0, 660.0, 1.0)]),
    "quake_report_start": dict(timbre="alarm", lufs=-13.0, tail=0.10, events=[
        (0.00, 0.12, 880.0, 880.0, 1.0), (0.20, 0.12, 880.0, 880.0, 1.0), (0.42, 0.50, 220.0, 220.0, 0.95)]),
    # ── 結束音（對應開始音：同音色、下行、較短、較輕） ──
    "weather_end": dict(timbre="electro", lufs=-16.5, tail=0.30, events=[
        (0.00, 0.13, C6, C6, 1.0), (0.13, 0.13, G5, G5, 1.0), (0.26, 0.13, E5, E5, 1.0), (0.39, 0.45, C5, C5, 1.0)]),
    "evac_end": dict(timbre="alarm", lufs=-15.5, tail=0.20, events=[
        (0.00, 1.00, 770.0, 480.0, 1.0)]),
    "emergency_end": dict(timbre="alarm", lufs=-15.5, tail=0.15, events=[
        (0.00, 0.15, 500.0, 500.0, 0.9), (0.27, 0.15, 500.0, 500.0, 0.6), (0.52, 0.30, 330.0, 330.0, 0.5)]),
    "security_end": dict(timbre="bell", lufs=-16.5, tail=0.30, events=[
        (0.00, 0.40, 660.0, 660.0, 1.0), (0.08, 0.40, 440.0, 440.0, 0.4)]),
    "quake_end": dict(timbre="alarm", lufs=-20.0, tail=0.15, events=[
        (0.00, 0.28, 880.0, 880.0, 0.8), (0.30, 0.38, 660.0, 660.0, 0.7)]),
    "visitor_end": dict(timbre="bell", lufs=-17.0, tail=0.25, events=[
        (0.00, 0.30, 784.0, 784.0, 1.0), (0.28, 0.38, 587.0, 587.0, 1.0)]),
    "notice_end_general": dict(timbre="soft", lufs=-17.0, tail=0.25, events=[
        (0.00, 0.28, 880.0, 880.0, 1.0), (0.26, 0.34, 659.0, 659.0, 1.0)]),
    "notice_end_important": dict(timbre="bell", lufs=-16.5, tail=0.25, events=[
        (0.00, 0.30, 784.0, 784.0, 1.0), (0.28, 0.36, 587.0, 587.0, 1.0)]),
    "scene_end": dict(timbre="soft", lufs=-17.0, tail=0.20, events=[
        (0.00, 0.40, C6, C6, 1.0)]),
}


def synth(spec):
    tb = TIMBRES[spec["timbre"]]
    total = max(e[0] + e[1] for e in spec["events"]) + spec["tail"]
    n = int(total * SR) + 1
    buf = [0.0] * n
    hard = tb.get("hard", False)
    for (t0, dur, f0, f1, vel) in spec["events"]:
        i0 = int(t0 * SR)
        length = int((dur + (0.0 if hard else spec["tail"])) * SR)
        phase = [0.0] * len(tb["partials"])
        for k in range(length):
            i = i0 + k
            if i >= n:
                break
            t = k / SR
            f = f0 + (f1 - f0) * min(t / dur, 1.0)
            s = 0.0
            for pi, (mult, amp, dec) in enumerate(tb["partials"]):
                phase[pi] += 2 * math.pi * f * mult / SR
                env = math.exp(-dec * t) if dec else 1.0
                s += amp * env * math.sin(phase[pi])
            # 起音（避免爆音）與結尾淡出
            a = min(t / tb["attack"], 1.0)
            if hard:
                rel = 0.02
                a *= min(max((dur - t) / rel, 0.0), 1.0)
            else:
                a *= min(1.0, max((length / SR - t) / 0.03, 0.0))
            buf[i] += vel * a * s
    peak = max(abs(x) for x in buf) or 1.0
    return [x / peak * 0.8 for x in buf]


def write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, x)) * 32767)) for x in samples))


def measure(path):
    """回傳 (整體響度 LUFS, 真峰值 dBFS)。為了讓 ebur128 有足夠長度，量測時尾端補靜音。"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "apad=pad_dur=1.5,ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    t = r.stderr
    # ebur128 會先逐行印出即時數值（開頭常是 -70），最後才有 Summary；只讀 Summary 之後的內容
    t = t[t.rfind("Summary:"):] if "Summary:" in t else t
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", t).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", t).group(1))
    return lufs, tp


def encode(name, spec):
    tmp = tempfile.mkdtemp(prefix="chime_")
    raw = os.path.join(tmp, name + ".wav")
    write_wav(raw, synth(spec))
    lufs, _tp = measure(raw)
    gain = spec["lufs"] - lufs
    out = os.path.join(OUT_DIR, name + ".mp3")
    part = out + ".part.mp3"
    for _ in range(3):  # 編碼後再量一次響度，修正增益（mp3 編碼與量測方式會有約 1 dB 偏差）
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                        f"volume={gain:.2f}dB,alimiter=limit=0.76:attack=2:release=20", "-ar", str(SR), "-ac", "1",
                        "-b:a", "96k", part], check=True, timeout=60)
        os.replace(part, out)
        lufs2, tp2 = measure(out)
        if abs(lufs2 - spec["lufs"]) <= 0.3:
            break
        gain += spec["lufs"] - lufs2
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                "default=nw=1:nk=1", out], capture_output=True, text=True).stdout.strip())
    os.remove(raw)
    os.rmdir(tmp)
    return dur, lufs2, tp2


def main(argv):
    if "--list" in argv:
        for k, v in SPECS.items():
            print(f"{k:22s} {v['timbre']:8s} target {v['lufs']:6.1f} LUFS")
        return 0
    names = [a for a in argv if not a.startswith("--")] or list(SPECS)
    bad = [n for n in names if n not in SPECS]
    if bad:
        print("unknown:", bad, file=sys.stderr)
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    for n in names:
        dur, lufs, tp = encode(n, SPECS[n])
        print(f"{n:22s} {dur:5.2f} s  {lufs:6.1f} LUFS  peak {tp:5.1f} dBFS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

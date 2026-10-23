#!/usr/bin/env python3
"""產生廣播用「開始／結束」提示音（SOP-21，V4.2.3 第二版）。純 Python 合成波形，ffmpeg 負責迴響、響度與 mp3。

用法（在 HA 容器內執行，ffmpeg 只在容器內有）：
  python3 /config/scripts/make_chimes.py                       # 產生全部
  python3 /config/scripts/make_chimes.py weather_start weather_end   # 只產生指定的
  python3 /config/scripts/make_chimes.py --list                # 列出清單
  python3 /config/scripts/make_chimes.py --json                # 以 JSON 輸出每個檔案的長度（給 announce 對照表用）

風格：
  * 一般類（一般／重要／情境／訪客／天氣／保全）＝「廣播前音樂」：機場、車站、百貨公司廣播前的短旋律＋和弦，
    鐘琴／顫音琴音色加大廳迴響，有氣勢、辨識度高；每一類旋律不同。
  * 緊急模式＝銅管重擊和弦（鏗、鏗、鏗～）。
  * 地震＝仿日本「緊急地震速報」那種成對的刺耳雙音（三全音）快速嗶聲；
    疏散＝防空警報式上下起伏的警笛（wail）。這兩類是外地警報常用的聲音，一聽就知道是災害。
  * 結束音＝同一組旋律「反向下行、較短、較輕」，最後落在低音和弦（有收尾感）；警報類的結束音是警笛／嗶聲漸弱。
  * 想調整音色或音符：只改下面的 SPECS 表格，再重跑本腳本；其他程式不用動（announce 的長度對照表可用 --json 取得）。
輸出：/media/<name>.mp3（44.1 kHz、立體聲）
"""
import json, math, os, re, struct, subprocess, sys, tempfile, wave

SR = 44100
OUT_DIR = os.environ.get("CHIME_OUT", "/media")

# ── 音色：partials = (倍頻, 相對振幅, 衰減速率/秒)；hard＝持續音（警報／警笛），其餘為敲擊音 ──
TIMBRES = {
    "vibes":   dict(partials=[(1, 1.0, 2.6), (2.756, 0.40, 4.5), (5.404, 0.16, 7.5)], attack=0.002),
    "celesta": dict(partials=[(1, 1.0, 4.5), (2, 0.55, 6.5), (3, 0.28, 8.5), (4, 0.12, 11.0)], attack=0.001),
    "pad":     dict(partials=[(1, 1.0, 0.9), (1.004, 0.8, 0.9), (2, 0.28, 1.4)], attack=0.05),
    "brass":   dict(partials=[(1, 1.0, 1.3), (2, 0.8, 1.6), (3, 0.6, 1.9), (4, 0.45, 2.2), (5, 0.3, 2.6), (6, 0.2, 3.0)], attack=0.014),
    "siren":   dict(partials=[(1, 1.0, 0.0), (2, 0.45, 0.0), (3, 0.22, 0.0), (4, 0.10, 0.0)], attack=0.03, hard=True, rel=0.05),
    "chirp":   dict(partials=[(1, 1.0, 0.0), (2, 0.30, 0.0), (3, 0.18, 0.0)], attack=0.001, hard=True, rel=0.012),
}

N = dict(C4=261.63, G4=392.0, A4=440.0, B4=493.88, C5=523.25, D5=587.33, E5=659.25, F5=698.46, G5=783.99, A5=880.0,
         B5=987.77, C6=1046.5, D6=1174.66, E6=1318.5, G6=1567.98, F6=1396.9, A3=220.0, D4=293.66, E4=329.63)
C_MAJ = [N["C5"], N["E5"], N["G5"], N["C6"]]

# 事件 = (開始秒, 長度秒, 頻率或頻率清單, 滑音結束頻率(None=不滑), 力度, 音色(None=用整體音色))
def ev(t, d, f, vel=1.0, glide=None, timbre=None):
    return (t, d, f if isinstance(f, list) else [f], glide, vel, timbre)

SPECS = {
    # ═════ 一般生活通知：廣播前音樂 ═════
    "notice_general_start": dict(timbre="vibes", lufs=-13.5, tail=0.65, echo="aecho=0.8:0.82:60|130|210:0.35|0.22|0.12", events=[
        ev(0.00, 0.35, N["G5"]), ev(0.27, 0.35, N["C6"]), ev(0.54, 0.40, N["E6"]),
        ev(0.95, 1.00, C_MAJ, 0.85)]),
    "notice_general_end": dict(timbre="vibes", lufs=-16.5, tail=0.55, echo="aecho=0.8:0.82:60|130|210:0.35|0.22|0.12", events=[
        ev(0.00, 0.28, N["E6"]), ev(0.20, 0.28, N["C6"]), ev(0.40, 0.45, N["G5"]),
        ev(0.65, 0.80, [N["C5"], N["G5"]], 0.75)]),
    "notice_important_start": dict(timbre="vibes", lufs=-13.0, tail=0.70, echo="aecho=0.8:0.84:55|120|200|300:0.38|0.26|0.16|0.08", events=[
        ev(0.00, 0.20, N["E5"]), ev(0.15, 0.20, N["G5"]), ev(0.30, 0.20, N["C6"]), ev(0.45, 0.25, N["E6"]),
        ev(0.78, 1.10, [N["C6"], N["E6"], N["G6"]], 0.9),
        ev(0.78, 1.10, [N["C4"], N["G4"]], 0.8, timbre="brass")]),
    "notice_important_end": dict(timbre="vibes", lufs=-16.0, tail=0.60, echo="aecho=0.8:0.84:55|120|200|300:0.38|0.26|0.16|0.08", events=[
        ev(0.00, 0.22, N["E6"]), ev(0.17, 0.22, N["C6"]), ev(0.34, 0.25, N["G5"]),
        ev(0.60, 0.80, [N["C4"], N["G4"]], 0.7, timbre="brass")]),
    "scene_start": dict(timbre="celesta", lufs=-14.0, tail=0.55, echo="aecho=0.8:0.8:50|110|190:0.32|0.2|0.1", events=[
        ev(0.00, 0.22, N["G5"]), ev(0.12, 0.22, N["C6"]), ev(0.24, 0.22, N["E6"]), ev(0.36, 0.25, N["G6"]),
        ev(0.65, 0.70, [N["E6"], N["G6"]], 0.8)]),
    "scene_end": dict(timbre="celesta", lufs=-17.0, tail=0.50, echo="aecho=0.8:0.8:50|110|190:0.32|0.2|0.1", events=[
        ev(0.00, 0.22, N["G6"]), ev(0.13, 0.22, N["E6"]), ev(0.26, 0.45, N["C6"])]),
    "visitor_start": dict(timbre="vibes", lufs=-13.5, tail=0.50, echo="aecho=0.8:0.82:60|130|210:0.35|0.22|0.12", events=[
        ev(0.00, 0.50, N["B5"]), ev(0.42, 0.60, N["G5"]), ev(1.05, 0.50, N["B5"]), ev(1.47, 0.75, N["G5"])]),
    "visitor_end": dict(timbre="vibes", lufs=-17.0, tail=0.55, echo="aecho=0.8:0.82:60|130|210:0.35|0.22|0.12", events=[
        ev(0.00, 0.40, N["G5"]), ev(0.30, 0.70, N["D5"], 0.9)]),
    # ═════ 天氣災害：向上的旋律＋懸浮和弦（像氣象播報前）═════
    "weather_start": dict(timbre="vibes", lufs=-13.5, tail=0.65, echo="aecho=0.8:0.85:65|140|230:0.38|0.25|0.14", events=[
        ev(0.00, 0.30, N["C5"]), ev(0.17, 0.30, N["E5"]), ev(0.34, 0.30, N["G5"]), ev(0.51, 0.30, N["C6"]), ev(0.68, 0.32, N["E6"]),
        ev(0.98, 1.10, [N["G5"], N["B5"], N["D6"]], 0.85, timbre="pad"),
        ev(0.98, 0.90, [N["D6"], N["G6"]], 0.55)]),
    "weather_end": dict(timbre="vibes", lufs=-16.5, tail=0.60, echo="aecho=0.8:0.85:65|140|230:0.38|0.25|0.14", events=[
        ev(0.00, 0.22, N["E6"]), ev(0.17, 0.22, N["C6"]), ev(0.34, 0.25, N["G5"]),
        ev(0.55, 0.90, [N["C5"], N["G5"]], 0.7, timbre="pad")]),
    # ═════ 保全：小調「叮咚」重複三次，有警戒感 ═════
    "security_start": dict(timbre="vibes", lufs=-13.5, tail=0.50, echo="aecho=0.8:0.8:50|110|190:0.33|0.2|0.1", events=[
        ev(0.00, 0.30, N["A5"]), ev(0.30, 0.30, N["F5"]),
        ev(0.65, 0.30, N["A5"]), ev(0.95, 0.35, N["F5"]),
        ev(1.32, 0.75, [N["A4"], N["E5"]], 0.85, timbre="brass")]),
    "security_end": dict(timbre="vibes", lufs=-16.0, tail=0.55, echo="aecho=0.8:0.8:50|110|190:0.33|0.2|0.1", events=[
        ev(0.00, 0.28, N["A5"]), ev(0.26, 0.28, N["F5"]),
        ev(0.55, 0.80, [N["A3"], N["E4"]], 0.8, timbre="brass")]),
    # ═════ 緊急模式：銅管重擊和弦 ═════
    "emergency_start": dict(timbre="brass", lufs=-12.5, tail=0.45, echo="aecho=0.8:0.78:45|95|160:0.3|0.18|0.1", events=[
        ev(0.00, 0.22, [N["A4"], N["E5"], N["A5"]], 1.0), ev(0.32, 0.22, [N["A4"], N["E5"], N["A5"]], 1.0),
        ev(0.64, 0.22, [N["A4"], N["E5"], N["A5"]], 1.0), ev(1.00, 1.00, [N["A4"], N["E5"], N["A5"], N["E6"]], 1.0)]),
    "emergency_end": dict(timbre="brass", lufs=-15.5, tail=0.40, echo="aecho=0.8:0.78:45|95|160:0.3|0.18|0.1", events=[
        ev(0.00, 0.22, [N["D4"], N["A4"]], 0.9), ev(0.30, 0.70, [N["A3"], N["E4"]], 0.8)]),
    # ═════ 地震：仿日本緊急地震速報的成對刺耳雙音（三全音）嗶聲 ═════
    "quake_start": dict(timbre="chirp", lufs=-12.5, tail=0.30, echo="aecho=0.8:0.7:35|80:0.25|0.12", events=
        [ev(0.72 * g + 0.20 * p, 0.13, [1046.5, 1480.0], 0.95) for g in range(3) for p in range(2)]),
    "quake_report_start": dict(timbre="chirp", lufs=-13.0, tail=0.30, echo="aecho=0.8:0.7:35|80:0.25|0.12", events=
        [ev(0.72 * g + 0.20 * p, 0.13, [1046.5, 1480.0], 0.9) for g in range(2) for p in range(2)]),
    "quake_end": dict(timbre="chirp", lufs=-16.5, tail=0.45, echo="aecho=0.8:0.78:45|95|160:0.3|0.18|0.1", events=[
        ev(0.00, 0.14, [1244.5, 880.0], 0.8), ev(0.22, 0.14, [1046.5, 740.0], 0.7), ev(0.50, 0.30, [880.0, 622.0], 0.55)]),
    # ═════ 疏散：防空警報式警笛（wail），上下起伏 ═════
    "evac_start": dict(timbre="siren", lufs=-12.5, tail=0.25, echo="aecho=0.8:0.75:60|130:0.3|0.16", events=[
        ev(0.00, 0.90, 450.0, 1.0, glide=950.0), ev(0.90, 0.90, 950.0, 1.0, glide=450.0), ev(1.80, 0.90, 450.0, 1.0, glide=950.0)]),
    "evac_end": dict(timbre="siren", lufs=-15.5, tail=0.30, echo="aecho=0.8:0.75:60|130:0.3|0.16", events=[
        ev(0.00, 1.40, 800.0, 0.8, glide=300.0)]),
}


def synth(spec):
    base = TIMBRES[spec["timbre"]]
    total = max(e[0] + e[1] for e in spec["events"]) + spec["tail"]
    n = int(total * SR) + 1
    buf = [0.0] * n
    for (t0, dur, freqs, glide, vel, tname) in spec["events"]:
        tb = TIMBRES[tname] if tname else base
        hard = tb.get("hard", False)
        i0 = int(t0 * SR)
        length = int((dur if hard else dur + spec["tail"]) * SR)
        rel = tb.get("rel", 0.02)
        for f0 in freqs:
            f1 = glide if glide else f0
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
                    s += amp * (math.exp(-dec * t) if dec else 1.0) * math.sin(phase[pi])
                a = min(t / tb["attack"], 1.0)
                if hard:
                    a *= min(max((dur - t) / rel, 0.0), 1.0)
                else:
                    a *= min(1.0, max((length / SR - t) / 0.03, 0.0))
                buf[i] += vel * a * s / len(freqs) ** 0.5
    peak = max(abs(x) for x in buf) or 1.0
    return [x / peak * 0.8 for x in buf]


def write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, x)) * 32767)) for x in samples))


def measure(path):
    """回傳 (整體響度 LUFS, 真峰值 dBFS)。量測時尾端補靜音，讓 ebur128 有足夠長度；只讀 Summary 之後的內容。"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "apad=pad_dur=1.5,ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    t = r.stderr
    t = t[t.rfind("Summary:"):] if "Summary:" in t else t
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", t).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", t).group(1))


def encode(name, spec):
    tmp = tempfile.mkdtemp(prefix="chime_")
    raw = os.path.join(tmp, name + ".wav")
    write_wav(raw, synth(spec))
    lufs, _ = measure(raw)
    gain = spec["lufs"] - lufs - 1.0
    out = os.path.join(OUT_DIR, name + ".mp3")
    part = out + ".part.mp3"
    echo = spec.get("echo", "aecho=0.8:0.8:60|130:0.3|0.18")
    for _ in range(4):  # 加上迴響後再量響度、修正增益
        af = (f"volume={gain:.2f}dB,{echo},pan=stereo|c0=c0|c1=c0,adelay=0|9,"
              f"alimiter=limit=0.76:attack=2:release=20")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "2",
                        "-b:a", "128k", part], check=True, timeout=60)
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
            print(f"{k:24s} {v['timbre']:8s} target {v['lufs']:6.1f} LUFS")
        return 0
    names = [a for a in argv if not a.startswith("--")] or list(SPECS)
    bad = [n for n in names if n not in SPECS]
    if bad:
        print("unknown:", bad, file=sys.stderr)
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    res = {}
    for n in names:
        dur, lufs, tp = encode(n, SPECS[n])
        res[n] = round(dur, 2)
        if "--json" not in argv:
            print(f"{n:24s} {dur:5.2f} s  {lufs:6.1f} LUFS  peak {tp:5.1f} dBFS")
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

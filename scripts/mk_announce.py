#!/usr/bin/env python3
"""合成「提示音 + 語音」單一音檔（供 script.announce 使用）。

用法：mk_announce.py <提示音檔路徑|none> <base64 文字> [結束音檔路徑|none]
成功：stdout 輸出 "<檔名>|<長度秒>"，結束碼 0；失敗：結束碼 1（呼叫端退回即時語音）。
輸出位置：/media/ann_<hash>.mp3（HA media-source: local）；同文字同提示音（與結束音）使用快取。
V4.2.3：新增選用的第 3 參數「結束音」（SOP-21）：串成「開始音＋0.15 秒＋語音＋0.25 秒＋結束音」；沒給或檔案不存在時
        行為與快取鍵都跟以前完全相同（向下相容）。
"""
import asyncio, base64, hashlib, os, subprocess, sys, time, glob

VOICE = "zh-TW-HsiaoChenNeural"
OUT_DIR = "/media"
KEEP_DAYS = 14

def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, timeout=10)
    return float(r.stdout.strip())

def main():
    chime = sys.argv[1]
    text = base64.b64decode(sys.argv[2]).decode("utf-8").strip()
    if not text:
        return 1
    end = sys.argv[3] if len(sys.argv) > 3 else "none"
    has_end = end != "none" and os.path.exists(end)
    if has_end:
        key = hashlib.sha1(f"{os.path.basename(chime)}|{os.path.basename(end)}|{VOICE}|{text}".encode()).hexdigest()[:16]
    else:
        key = hashlib.sha1(f"{os.path.basename(chime)}|{VOICE}|{text}".encode()).hexdigest()[:16]
    out = os.path.join(OUT_DIR, f"ann_{key}.mp3")
    if not os.path.exists(out):
        import edge_tts
        tts_path = f"/tmp/ann_{key}.tts.mp3"
        asyncio.run(asyncio.wait_for(edge_tts.Communicate(text, VOICE).save(tts_path), timeout=20))
        tmp = out + ".part.mp3"
        if has_end:
            # 開始音（可無）＋0.15 秒＋語音＋0.25 秒＋結束音
            fmt = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
            ins, segs, k = [], [], 0
            if chime != "none" and os.path.exists(chime):
                ins += ["-i", chime]; segs.append(f"[{k}:a]{fmt}[a{k}]"); k += 1
                ins += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]; segs.append(f"[{k}:a]atrim=0:0.15[a{k}]"); k += 1
            ins += ["-i", tts_path]; segs.append(f"[{k}:a]{fmt}[a{k}]"); k += 1
            ins += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]; segs.append(f"[{k}:a]atrim=0:0.25[a{k}]"); k += 1
            ins += ["-i", end]; segs.append(f"[{k}:a]{fmt}[a{k}]"); k += 1
            fc = ";".join(segs) + ";" + "".join(f"[a{i}]" for i in range(k)) + f"concat=n={k}:v=0:a=1[o]"
            cmd = ["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", fc, "-map", "[o]", "-b:a", "128k", tmp]
        elif chime != "none" and os.path.exists(chime):
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", chime, "-i", tts_path,
                   "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                   "-filter_complex",
                   "[0:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
                   "[1:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"
                   "[2:a]atrim=0:0.15[s];[a0][s][a1]concat=n=3:v=0:a=1[o]",
                   "-map", "[o]", "-b:a", "128k", tmp]
        else:
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tts_path, "-ar", "44100", "-ac", "2",
                   "-b:a", "128k", tmp]
        subprocess.run(cmd, check=True, timeout=30)
        os.replace(tmp, out)
        os.remove(tts_path)
        # 清除過期檔案
        now = time.time()
        for f in glob.glob(os.path.join(OUT_DIR, "ann_*.mp3")):
            if now - os.path.getmtime(f) > KEEP_DAYS * 86400:
                os.remove(f)
    print(f"{os.path.basename(out)}|{duration(out):.2f}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERR {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""合成「提示音 + 語音」單一音檔（供 script.announce 使用）。

用法：mk_announce.py <提示音檔路徑|none> <base64 文字>
成功：stdout 輸出 "<檔名>|<長度秒>"，結束碼 0；失敗：結束碼 1（呼叫端退回即時語音）。
輸出位置：/media/ann_<hash>.mp3（HA media-source: local）；同文字同提示音使用快取。
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
    key = hashlib.sha1(f"{os.path.basename(chime)}|{VOICE}|{text}".encode()).hexdigest()[:16]
    out = os.path.join(OUT_DIR, f"ann_{key}.mp3")
    if not os.path.exists(out):
        import edge_tts
        tts_path = f"/tmp/ann_{key}.tts.mp3"
        asyncio.run(asyncio.wait_for(edge_tts.Communicate(text, VOICE).save(tts_path), timeout=20))
        tmp = out + ".part.mp3"
        if chime != "none" and os.path.exists(chime):
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

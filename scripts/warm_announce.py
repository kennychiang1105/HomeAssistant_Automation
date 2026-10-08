#!/usr/bin/env python3
"""預先合成常用廣播音檔（快取暖機）。

為什麼：即時合成約需 1.7 秒（Edge TTS 網路＋ffmpeg），地震預警這類分秒必爭的廣播不能等；
       預先合成後只剩播放延遲（約 0.6 秒），斷網時也能播。
做法：以與 mk_announce.py 完全相同的檔名規則（sha1(提示音檔名|語音|文字)）產生 /media/ann_<hash>.mp3；
       已存在的檔案只更新修改時間（避免被 14 天清理刪除）。
由 00-2L廣播快取暖機AI 在 HA 啟動後與每日 03:30 執行（背景執行，log：/config/warm_announce.log）。
清單：地震預警第一句（震度 3~7 × 3~60 秒，短句）、地震第二句、門鈴、車庫回家等固定句。
"""
import asyncio, hashlib, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

VOICE = "zh-TW-HsiaoChenNeural"
OUT_DIR = "/media"
CHIME_DIR = "/media"

def key_path(chime, text):
    key = hashlib.sha1(f"{os.path.basename(chime)}|{VOICE}|{text}".encode()).hexdigest()[:16]
    return os.path.join(OUT_DIR, f"ann_{key}.mp3")

def make(chime, text):
    out = key_path(chime, text)
    if os.path.exists(out):
        os.utime(out, None)
        return "touch"
    import edge_tts
    key = os.path.basename(out)[4:-4]
    tts_path = f"/tmp/warm_{key}.tts.mp3"
    asyncio.run(asyncio.wait_for(edge_tts.Communicate(text, VOICE).save(tts_path), timeout=30))
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
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", tts_path, "-ar", "44100", "-ac", "2", "-b:a", "128k", tmp]
    subprocess.run(cmd, check=True, timeout=40)
    os.replace(tmp, out)
    os.remove(tts_path)
    return "new"

def build_list():
    items = []
    # 地震預警第一句（短句，約 3 秒念完；秒數為「念到數字時」的剩餘秒數，由 eq99 扣掉延遲後挑選）
    levels = ["3", "4", "5", "5弱", "5強", "6", "6弱", "6強", "7"]
    for lv in levels:
        for n in range(3, 61):
            items.append(("none", f"地震預警！預估{lv}級，{n}秒後到達！"))
    items.append(("none", "地震！地震！立即就地趴下，掩護，穩住！"))
    items.append((f"{CHIME_DIR}/CWBEEW.mp3", "發生地震，請就地避難掩護！立即就地趴下、掩護、穩住並抓住桌腳，保護頭頸部。"))
    # 第一句播完立即接的第二句（eq99；提示音 CWBEEW.mp3）
    items.append((f"{CHIME_DIR}/CWBEEW.mp3", "請就地避難掩護！立即就地趴下、掩護、穩住並抓住桌腳，保護頭頸部。"))
    items.append((f"{CHIME_DIR}/chime_doorbell.mp3", "大門有人按門鈴！請注意門外來訪客人。"))
    items.append((f"{CHIME_DIR}/chime_important.mp3", "有人即將到家，車庫鐵門正在打開。有人即將到家，車庫鐵門正在打開。"))
    items.append((f"{CHIME_DIR}/chime_important.mp3", "保全系統通知 請注意二樓大門沒有完全關閉，目前為虛掩狀態，請注意！"))
    items.append(("none", "車庫鐵門即將開啟"))
    items.append(("none", "車庫鐵門即將關閉，請注意安全。"))
    return items

def main():
    items = build_list()
    stats = {"new": 0, "touch": 0, "fail": 0}
    t0 = time.time()
    def run(it):
        try:
            return make(*it)
        except Exception as e:
            print("FAIL", it[1][:30], e, flush=True)
            return "fail"
    with ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(run, items):
            stats[r] += 1
    print(f"done {len(items)} items in {time.time()-t0:.0f}s: {stats}", flush=True)

if __name__ == "__main__":
    main()

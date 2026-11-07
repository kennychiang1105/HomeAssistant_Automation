import cv2, os, re, datetime as dt, time, json
# 第 3 批（2026-11-07）：10/31 09:39 之後還沒訓練過的車庫影片，每 4 秒一張
base = r'\\jnas916p\Family\UniFi'
out = r'C:\ai_lab\garage\frames3'
os.makedirs(out, exist_ok=True)
pat = re.compile(r'^(\d{1,2})-(\d{1,2})-(\d{4}), (\d+)\.(\d\d)\.(\d\d)(am|pm) GMT\+8 - .*\[847848288CA2\]\.mp4$')


def start(n):
    m = pat.match(n)
    if not m:
        return None
    h = int(m[4]) % 12 + (12 if m[7] == 'pm' else 0)
    return dt.datetime(int(m[3]), int(m[1]), int(m[2]), h, int(m[5]), int(m[6]))


meta = []
t0 = time.time()
seen = set()
days = ['2026-10-31', '2026-11-01', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-07']
for d in days:
    p = os.path.join(base, 'UniFi-Protect_' + d)
    if not os.path.isdir(p):
        continue
    for n in sorted(os.listdir(p)):
        s = start(n)
        if not s or s < dt.datetime(2026, 10, 31, 9, 39):
            continue
        cap = cv2.VideoCapture(os.path.join(p, n))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        step = int(round(fps * 4))
        i = 0
        while True:
            ok = cap.grab()
            if not ok:
                break
            if i % step == 0:
                ok, fr = cap.retrieve()
                if ok:
                    ts = s + dt.timedelta(seconds=i / fps)
                    key = ts.strftime('%m%d_%H%M%S')
                    if key not in seen:
                        seen.add(key)
                        fr = cv2.resize(fr, (1344, 756))
                        cv2.imwrite(os.path.join(out, 'g_%s.jpg' % key), fr, [cv2.IMWRITE_JPEG_QUALITY, 88])
                        meta.append(key)
            i += 1
        cap.release()
    print(d, len(meta), round(time.time() - t0), flush=True)
json.dump(meta, open(r'C:\ai_lab\garage\frames3_index.json', 'w'))
print('DONE', flush=True)

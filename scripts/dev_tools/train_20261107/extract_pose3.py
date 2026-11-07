import cv2, json, os, re, sys, time, datetime as dt
from ultralytics import YOLO
# 第 3 批（2026-11-07）：還沒訓練過的頂樓影片（10/29 10:06～10/30 00:00、10/31 09:13 之後），直接從 NAS 讀，每秒 2 幀跑姿態
base = r'\\jnas916p\Family\UniFi'
pat = re.compile(r'^(\d{1,2})-(\d{1,2})-(\d{4}), (\d+)\.(\d\d)\.(\d\d)(am|pm) GMT\+8 - .*\[70A7410D7177\]\.mp4$')
RANGES = [(dt.datetime(2026, 10, 29, 10, 6), dt.datetime(2026, 10, 30, 0, 0)), (dt.datetime(2026, 10, 31, 9, 13), dt.datetime(2026, 11, 8, 0, 0))]


def start(n):
    m = pat.match(n)
    if not m:
        return None
    h = int(m[4]) % 12 + (12 if m[7] == 'pm' else 0)
    return dt.datetime(int(m[3]), int(m[1]), int(m[2]), h, int(m[5]), int(m[6]))


clips = []
for d in ['2026-10-29', '2026-10-30', '2026-10-31', '2026-11-01', '2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06', '2026-11-07']:
    p = os.path.join(base, 'UniFi-Protect_' + d)
    if not os.path.isdir(p):
        continue
    for n in sorted(os.listdir(p)):
        s = start(n)
        if s and any(a <= s < b for a, b in RANGES):
            clips.append((s, os.path.join(p, n)))
clips.sort()
cmap = []
for i, (s, path) in enumerate(clips):
    cmap.append({'clip': 't3%03d_%s.mp4' % (i, s.strftime('%m%d_%H%M%S')), 'start': s.strftime('%Y-%m-%d %H:%M:%S'), 'path': path})
os.makedirs(r'C:\ai_lab\topfloor\clips3', exist_ok=True)
print('clips', len(cmap), flush=True)
m = YOLO(r'C:\ai_lab\topfloor\yolo11m-pose.pt')
outp = r'C:\ai_lab\topfloor\obs_pose3.json'
out = json.load(open(outp)) if os.path.exists(outp) else {}
t0 = time.time()
for k, c in enumerate(cmap):
    cap = cv2.VideoCapture(c['path'])
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    nfr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    c['dur'] = int(round(nfr / fps)) if nfr else 0
    if c['clip'] in out:
        cap.release()
        continue
    step = max(1, int(round(fps / 2)))
    i = 0
    rows = []
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            ok, fr = cap.retrieve()
            if not ok:
                break
            H, W = fr.shape[:2]
            r = m.predict(fr, imgsz=640, conf=0.25, verbose=False, device=0)[0]
            ps = []
            if r.boxes is not None and len(r.boxes):
                for b, cf, kk in zip(r.boxes.xyxyn.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.keypoints.data.cpu().numpy()):
                    kp = [[round(float(x) / W, 4), round(float(y) / H, 4), round(float(sc), 3)] for x, y, sc in kk]
                    ps.append({'conf': round(float(cf), 3), 'box': [round(float(v), 4) for v in b], 'kp': kp})
            rows.append([round(i / fps, 2), ps])
        i += 1
    cap.release()
    out[c['clip']] = rows
    if k % 10 == 0:
        json.dump(out, open(outp, 'w'))
        print(k, len(cmap), c['clip'], len(rows), round(time.time() - t0), flush=True)
json.dump(out, open(outp, 'w'))
json.dump(cmap, open(r'C:\ai_lab\topfloor\clips3\clipmap.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('DONE', len(out), round(time.time() - t0), flush=True)

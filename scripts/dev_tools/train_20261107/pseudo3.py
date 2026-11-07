"""第 3 批（2026-11-07）：新畫面（frames3）的偵測框自動標註：原版 YOLO11m（1280）＋目前的車庫微調版（960），合併後當訓練標籤。"""
import os, json, time
from ultralytics import YOLO
D = r'C:\ai_lab\garage\frames3'
names = sorted(os.listdir(D))
out = {}
t0 = time.time()
for tag, path, imgsz, VEH, PER in (('m1280', r'C:\ai_lab\garage\yolo11m.pt', 1280, {2, 3, 5, 7}, 0),
                                   ('ft960', r'C:\ai_lab\garage\runs\garage_m\weights\best.pt', 960, {0}, 1)):
    m = YOLO(path)
    B = 16
    for i in range(0, len(names), B):
        rs = m.predict([os.path.join(D, n) for n in names[i:i + B]], imgsz=imgsz, conf=0.2, iou=0.5, verbose=False, device=0, half=True)
        for n, r in zip(names[i:i + B], rs):
            dets = []
            for b, c, k in zip(r.boxes.xyxyn.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.boxes.cls.cpu().numpy()):
                k = int(k)
                if k == PER:
                    dets.append({'cls': 'person', 'conf': round(float(c), 3), 'box': [round(float(v), 4) for v in b]})
                elif k in VEH:
                    dets.append({'cls': 'car', 'conf': round(float(c), 3), 'box': [round(float(v), 4) for v in b]})
            out.setdefault(n, {})[tag] = dets
    print(tag, 'done', round(time.time() - t0), flush=True)
json.dump(out, open(r'C:\ai_lab\garage\pseudo3.json', 'w'))
print('DONE', len(out), flush=True)

import os, json, sys, time
from ultralytics import YOLO
D = r'C:\ai_lab\garage\frames'
names = sorted(os.listdir(D))
m = YOLO('yolo11x.pt')
VEH = {2, 3, 5, 7}
out = {}
t0 = time.time()
B = 16
for i in range(0, len(names), B):
    batch = [os.path.join(D, n) for n in names[i:i + B]]
    rs = m.predict(batch, imgsz=1280, conf=0.2, iou=0.5, verbose=False, device=0, half=True)
    for n, r in zip(names[i:i + B], rs):
        dets = []
        for b, c, k in zip(r.boxes.xyxyn.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.boxes.cls.cpu().numpy()):
            k = int(k)
            if k == 0:
                dets.append({'cls': 'person', 'conf': round(float(c), 3), 'box': [round(float(v), 4) for v in b]})
            elif k in VEH:
                dets.append({'cls': 'car', 'conf': round(float(c), 3), 'box': [round(float(v), 4) for v in b]})
        out[n] = dets
    if (i // B) % 10 == 0:
        print(i, len(names), round(time.time() - t0), flush=True)
json.dump(out, open(r'C:\ai_lab\garage\pseudo_x.json', 'w'))
print('DONE', flush=True)

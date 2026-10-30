import json, sys, os, numpy as np
from ultralytics import YOLO
model, imgsz = sys.argv[1], int(sys.argv[2])
D = r'C:\ai_lab\garage\frames'
d = np.load(r'C:\ai_lab\garage\emb.npz')
names = list(d['names'])
sat = d['sat']
cl = json.load(open(r'C:\ai_lab\garage\clusters.json'))
roi = json.load(open(r'C:\ai_lab\garage\garage_roi.json', encoding='utf-8'))
occ = {'front': {1, 3, 5, 6, 7, 8, 9, 10, 11, 13}, 'back': {0, 2, 3, 4, 6, 9, 10, 12, 13}}
emp = {'front': {0, 2, 4}, 'back': {1, 8, 11}}
m = YOLO(model)
CAR = {2, 3, 5, 7} if 'yolo11m.pt' in model or 'yolo11x.pt' in model else {0}
val = [i for i, n in enumerate(names) if n[2:6] in ('1029', '1030')]
res = {}
B = 16
for k in range(0, len(val), B):
    ids = val[k:k + B]
    rs = m.predict([os.path.join(D, names[i]) for i in ids], imgsz=imgsz, conf=0.3, iou=0.5, verbose=False, device=0)
    for i, r in zip(ids, rs):
        res[i] = [(b.tolist()) for b, c in zip(r.boxes.xyxyn.cpu().numpy(), r.boxes.cls.cpu().numpy()) if int(c) in CAR]
for slot in ('front', 'back'):
    box = roi['slots'][slot]['body']
    L = np.array(cl[slot])

    def hit(i):
        return any(box[0] <= (b[0] + b[2]) / 2 <= box[2] and box[1] <= (b[1] + b[3]) / 2 <= box[3] for b in res[i])
    for nm, S in (('occupied', occ[slot]), ('empty', emp[slot])):
        for mode, sel in (('IR', sat < 8), ('color', sat >= 8)):
            idx = [i for i in val if L[i] in S and sel[i]]
            if idx:
                h = sum(hit(i) for i in idx)
                print(model.split('\\')[-1], imgsz, slot, nm, mode, 'n', len(idx), 'car-in-slot %.1f%%' % (100 * h / len(idx)))

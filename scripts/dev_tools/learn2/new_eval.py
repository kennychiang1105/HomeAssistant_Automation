import numpy as np, json, os, cv2
from PIL import Image
from ultralytics import YOLO
src = open(r'C:\ai_lab\garage\embed_frames.py', encoding='utf-8-sig').read().split("\nD=")[0]
ns = {}
exec(src, ns)
embed, crop, roi = ns['embed'], ns['crop'], ns['roi']
D = r'C:\ai_lab\garage\frames2'
names = sorted(os.listdir(D))
occm = json.load(open(r'C:\ai_lab\garage\occ_model.json'))
yolo = YOLO(r'C:\ai_lab\garage\runs\garage_m\weights\best.pt')
res = {}
E = {'front': [], 'back': []}
for i, n in enumerate(names):
    im = Image.open(os.path.join(D, n)).convert('RGB')
    row = {}
    for s in ('front', 'back'):
        e = embed(crop(im, roi['slots'][s]['body']))
        E[s].append(e)
        z = float(np.dot(np.array(occm[s]['w']), e) + occm[s]['b'])
        row[s] = 1 / (1 + np.exp(-z))
    res[n] = row
np.savez(r'C:\ai_lab\garage\emb2.npz', names=np.array(names), front=np.array(E['front']), back=np.array(E['back']))
# YOLO（獨立於 CLIP 分類器）
det = {}
B = 16
for k in range(0, len(names), B):
    rs = yolo.predict([os.path.join(D, n) for n in names[k:k + B]], imgsz=640, conf=0.3, verbose=False, device=0)
    for n, r in zip(names[k:k + B], rs):
        det[n] = [b.tolist() for b, c in zip(r.boxes.xyxyn.cpu().numpy(), r.boxes.cls.cpu().numpy()) if int(c) == 0]
rows = []
for n in names:
    r = {'name': n}
    for s in ('front', 'back'):
        bx = roi['slots'][s]['body']
        y = any(bx[0] <= (b[0] + b[2]) / 2 <= bx[2] and bx[1] <= (b[1] + b[3]) / 2 <= bx[3] for b in det[n])
        r[s] = (round(res[n][s], 3), bool(y))
    rows.append(r)
json.dump(rows, open(r'C:\ai_lab\garage\new_eval.json', 'w'))
for s in ('front', 'back'):
    agree = sum(1 for r in rows if (r[s][0] > 0.5) == r[s][1])
    dis = [r for r in rows if (r[s][0] > 0.5) != r[s][1]]
    unsure = [r for r in rows if 0.2 < r[s][0] < 0.8]
    print(s, 'frames', len(rows), 'CLIP-classifier vs YOLO agree %.1f%%' % (100 * agree / len(rows)), 'disagree', len(dis), 'unsure(0.2-0.8)', len(unsure))

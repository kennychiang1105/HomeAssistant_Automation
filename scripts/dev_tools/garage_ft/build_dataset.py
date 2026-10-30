import json, os, shutil, numpy as np, cv2, random
random.seed(0)
D = r'C:\ai_lab\garage\frames'
names = sorted(os.listdir(D))
d = np.load(r'C:\ai_lab\garage\emb.npz')
assert list(d['names']) == names
sat = d['sat']
cl = json.load(open(r'C:\ai_lab\garage\clusters.json'))
roi = json.load(open(r'C:\ai_lab\garage\garage_roi.json', encoding='utf-8'))
M = json.load(open(r'C:\ai_lab\garage\pseudo_m640.json'))
X = json.load(open(r'C:\ai_lab\garage\pseudo_x.json'))
occ = {'front': {1, 3, 5, 6, 7, 8, 9, 10, 11, 13}, 'back': {0, 2, 3, 4, 6, 9, 10, 12, 13}}
SB = {s: roi['slots'][s]['body'] for s in ('front', 'back')}


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0


def merge(cands, thr=0.5):
    out = []
    for c in sorted(cands, key=lambda z: -z['conf']):
        if all(iou(c['box'], o['box']) < thr for o in out):
            out.append(c)
    return out


def in_slot(b, s):
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return SB[s][0] <= cx <= SB[s][2] and SB[s][1] <= cy <= SB[s][3]


lab = {}
for n in names:
    cars = merge([x for x in M[n] if x['cls'] == 'car' and x['conf'] >= 0.3] + [x for x in X[n] if x['cls'] == 'car' and x['conf'] >= 0.4])
    ppl = merge([x for x in M[n] + X[n] if x['cls'] == 'person' and x['conf'] >= 0.5])
    lab[n] = {'car': cars, 'person': ppl}
# 後位有車但沒偵測到：沿用同一天最近一張有偵測的後位車框（車停著不動）
miss = 0
for slot in ('front', 'back'):
    L = np.array(cl[slot])
    idx = [i for i in range(len(names)) if L[i] in occ[slot]]
    have = {i: next((c for c in lab[names[i]]['car'] if in_slot(c['box'], slot)), None) for i in idx}
    for i in idx:
        if have[i] is None:
            day = names[i][2:6]
            near = [j for j in idx if have[j] and names[j][2:6] == day]
            if near:
                j = min(near, key=lambda j: abs(j - i))
                lab[names[i]]['car'].append({'cls': 'car', 'conf': 0.3, 'box': have[j]['box'], 'prop': True})
                miss += 1
print('propagated boxes for missed occupied-slot frames:', miss)
# 切分：10/26～10/28 訓練、10/29～10/30 驗證
root = r'C:\ai_lab\garage\yolo_ds'
if os.path.exists(root):
    shutil.rmtree(root)
for sp in ('train', 'val'):
    os.makedirs(r'%s\images\%s' % (root, sp))
    os.makedirs(r'%s\labels\%s' % (root, sp))
n_tr = n_va = n_gray = 0


def write(sp, name, img, items):
    cv2.imwrite(r'%s\images\%s\%s.jpg' % (root, sp, name), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    with open(r'%s\labels\%s\%s.txt' % (root, sp, name), 'w') as f:
        for k, c in ((0, 'car'), (1, 'person')):
            for x in items[c]:
                b = x['box']
                f.write('%d %.5f %.5f %.5f %.5f\n' % (k, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0], b[3] - b[1]))


for i, n in enumerate(names):
    sp = 'val' if n[2:6] in ('1029', '1030') else 'train'
    img = cv2.imread(os.path.join(D, n))
    write(sp, n[:-4], img, lab[n])
    if sp == 'train':
        n_tr += 1
        # 彩色畫面轉成「紅外線風格」（灰階＋提高對比）一份，補紅外線樣本
        if sat[i] >= 8 and random.random() < 0.5:
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            g = cv2.convertScaleAbs(g, alpha=1.15, beta=-10)
            write('train', n[:-4] + '_ir', cv2.merge([g, g, g]), lab[n])
            n_gray += 1
    else:
        n_va += 1
open(root + r'\data.yaml', 'w').write('path: %s\ntrain: images/train\nval: images/val\nnames:\n  0: car\n  1: person\n' % root.replace('\\', '/'))
print('train', n_tr, '+ir', n_gray, 'val', n_va)

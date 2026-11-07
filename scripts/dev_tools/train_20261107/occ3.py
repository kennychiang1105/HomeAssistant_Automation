"""第 3 批（2026-11-07）：車位有沒有車（CLIP 特徵＋邏輯迴歸）加入 10/31～11/07 新畫面重新訓練，依日期留一和現行 v2 比較。用法：occ3.py [save]
新資料標籤：現行模型很有把握（≥0.9／≤0.1，人工抽查 3,868 張中這兩類全部正確）＋困難正樣本（模型 0.1～0.9、但微調 YOLO 的車框中心在車位內且蓋住車位 ≥ 50%，
例如有人擋在車前）；其餘（車卡在門口、Tesla 停在兩車位中間）不標。"""
import numpy as np, json, sys
from sklearn.linear_model import LogisticRegression
d1 = np.load(r'C:\ai_lab\garage\emb.npz'); d2 = np.load(r'C:\ai_lab\garage\emb2.npz'); d3 = np.load(r'C:\ai_lab\garage\emb3.npz')
cl = json.load(open(r'C:\ai_lab\garage\clusters.json'))
rows2 = {r['name']: r for r in json.load(open(r'C:\ai_lab\garage\new_eval.json'))}
rows3 = {r['name']: r for r in json.load(open(r'C:\ai_lab\garage\eval3.json'))}
P3 = json.load(open(r'C:\ai_lab\garage\pseudo3.json'))
roi = json.load(open(r'C:\ai_lab\garage\garage_roi.json', encoding='utf-8'))
old = json.load(open(r'C:\ai_lab\garage\occ_model_v2.json'))
occ = {'front': {1, 3, 5, 6, 7, 8, 9, 10, 11, 13}, 'back': {0, 2, 3, 4, 6, 9, 10, 12, 13}}
emp = {'front': {0, 2, 4}, 'back': {1, 8, 11}}
names3 = list(d3['names'])
days3 = np.array([n[2:6] for n in names3])


def cover(b, r):
    ix = max(0, min(b[2], r[2]) - max(b[0], r[0])); iy = max(0, min(b[3], r[3]) - max(b[1], r[1]))
    return ix * iy / ((r[2] - r[0]) * (r[3] - r[1]))


def prob(m, X):
    return 1 / (1 + np.exp(-(X @ np.array(m['w']) + m['b'])))


out = {}
for slot in ('front', 'back'):
    R = roi['slots'][slot]['body']
    lab = np.array(cl[slot]); y1 = np.full(len(lab), -1)
    for c in occ[slot]: y1[lab == c] = 1
    for c in emp[slot]: y1[lab == c] = 0
    X1, Y1 = d1[slot][y1 >= 0], y1[y1 >= 0]
    y2 = []
    for n in d2['names']:
        p = rows2[n][slot][0]
        y2.append(0 if p < 0.1 else 1 if p > 0.9 else (1 if 0.2 < p < 0.8 else -1))
    y2 = np.array(y2)
    X2, Y2 = d2[slot][y2 >= 0], y2[y2 >= 0]
    y3, hard = [], []
    for n in names3:
        p = rows3[n][slot][0]
        boxes = [x['box'] for x in P3[n].get('ft960', []) if x['cls'] == 'car' and x['conf'] >= 0.5]
        parked = any(R[0] <= (b[0] + b[2]) / 2 <= R[2] and R[1] <= (b[1] + b[3]) / 2 <= R[3] and cover(b, R) >= 0.5 for b in boxes)
        if p >= 0.9:
            y3.append(1); hard.append(False)
        elif p <= 0.1:
            y3.append(0); hard.append(False)
        elif parked:
            y3.append(1); hard.append(True)
        else:
            y3.append(-1); hard.append(False)
    y3 = np.array(y3); hard = np.array(hard)
    X3 = d3[slot]
    print('==', slot, '| 舊資料', len(Y1) + len(Y2), '| 新資料標註', int((y3 >= 0).sum()), '（有車', int((y3 == 1).sum()), '空', int((y3 == 0).sum()), '困難正樣本', int(hard.sum()), '）未標', int((y3 < 0).sum()))
    po = prob(old, X3) if False else prob(old[slot], X3)
    tot = {'old': [0, 0, 0, 0, 0], 'new': [0, 0, 0, 0, 0]}   # 標註幀數、判對、很有把握但判錯、困難正樣本很有把握判對、全部幀很有把握的數量
    for dday in sorted(set(days3)):
        te = days3 == dday
        tr3 = (~te) & (y3 >= 0)
        Xa = np.vstack([X1, X2, X3[tr3]]); Ya = np.concatenate([Y1, Y2, y3[tr3]])
        clf = LogisticRegression(C=10, max_iter=5000, class_weight='balanced').fit(Xa, Ya)
        pn = clf.predict_proba(X3[te])[:, 1]
        for k, pp in (('old', po[te]), ('new', pn)):
            yy, hh = y3[te], hard[te]
            m = yy >= 0
            tot[k][0] += m.sum()
            tot[k][1] += ((pp[m] > 0.5) == yy[m]).sum()
            tot[k][2] += (((pp[m] >= 0.8) & (yy[m] == 0)) | ((pp[m] <= 0.2) & (yy[m] == 1))).sum()
            tot[k][3] += ((pp[hh] >= 0.8)).sum()
            tot[k][4] += ((pp >= 0.8) | (pp <= 0.2)).sum()
    nh = int(hard.sum())
    for k in ('old', 'new'):
        a = tot[k]
        print('  %-3s 標註幀 %d 判對 %.2f%% | 很有把握卻判錯 %d | 困難正樣本（有人擋等）很有把握判有車 %d/%d | 全部 %d 幀中很有把握的 %.1f%%' % (
            k, a[0], 100 * a[1] / a[0], a[2], a[3], nh, len(names3), 100 * a[4] / len(names3)))
    Xa = np.vstack([X1, X2, X3[y3 >= 0]]); Ya = np.concatenate([Y1, Y2, y3[y3 >= 0]])
    clf = LogisticRegression(C=10, max_iter=5000, class_weight='balanced').fit(Xa, Ya)
    p = clf.predict_proba(Xa)[:, 1]
    print('  final n', len(Ya), 'train acc %.4f' % ((p > 0.5) == Ya).mean())
    out[slot] = {'w': [round(float(v), 6) for v in clf.coef_[0]], 'b': round(float(clf.intercept_[0]), 6), 'n': int(len(Ya))}
if 'save' in sys.argv:
    json.dump(out, open(r'C:\ai_lab\garage\occ_model_v3.json', 'w'))
    print('saved occ_model_v3.json')

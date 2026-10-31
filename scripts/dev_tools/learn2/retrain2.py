import numpy as np, json
from sklearn.linear_model import LogisticRegression
d1 = np.load(r'C:\ai_lab\garage\emb.npz'); d2 = np.load(r'C:\ai_lab\garage\emb2.npz')
names2 = list(d2['names'])
cl = json.load(open(r'C:\ai_lab\garage\clusters.json'))
rows = {r['name']: r for r in json.load(open(r'C:\ai_lab\garage\new_eval.json'))}
occ = {'front': {1, 3, 5, 6, 7, 8, 9, 10, 11, 13}, 'back': {0, 2, 3, 4, 6, 9, 10, 12, 13}}
emp = {'front': {0, 2, 4}, 'back': {1, 8, 11}}
out = json.load(open(r'C:\ai_lab\garage\occ_model.json'))
for slot in ('front', 'back'):
    lab = np.array(cl[slot]); y1 = np.full(len(lab), -1)
    for c in occ[slot]: y1[lab == c] = 1
    for c in emp[slot]: y1[lab == c] = 0
    m1 = y1 >= 0
    X1, Y1 = d1[slot][m1], y1[m1]
    # 新資料標註：分類器很有把握（<0.1 或 >0.9）採用；不確定的（0.2～0.8）經看圖確認全部是「有車」（車子進出中、紅燈眩光、全黑車蓋）
    y2 = []
    for n in names2:
        p = rows[n][slot][0]
        y2.append(0 if p < 0.1 else 1 if p > 0.9 else (1 if 0.2 < p < 0.8 else -1))
    y2 = np.array(y2); m2 = y2 >= 0
    X2, Y2 = d2[slot][m2], y2[m2]
    day2 = np.array([n[2:6] for n in names2])[m2]
    print(slot, 'new labeled', m2.sum(), 'occ', (Y2 == 1).sum(), 'empty', (Y2 == 0).sum())
    # 新日（10/31）留出測試：舊資料＋10/30 新資料訓練 → 測 10/31（含不確定那些）
    te = day2 == '1031'; tr = ~te
    Xtr, Ytr = np.vstack([X1, X2[tr]]), np.concatenate([Y1, Y2[tr]])
    for nm, (Xa, Ya) in (('old-only', (X1, Y1)), ('old+new(1030)', (Xtr, Ytr))):
        clf = LogisticRegression(C=10, max_iter=5000, class_weight='balanced').fit(Xa, Ya)
        p = clf.predict_proba(X2[te])[:, 1]
        pred = (p > 0.5).astype(int)
        hard = (np.array([rows[n][slot][0] for n in np.array(names2)[m2][te]]) > 0.2) & (np.array([rows[n][slot][0] for n in np.array(names2)[m2][te]]) < 0.8)
        print(' ', nm, '10/31 test n', te.sum(), 'acc %.3f' % (pred == Y2[te]).mean(), 'hard n', hard.sum(), 'hard acc %.3f' % ((pred == Y2[te])[hard].mean() if hard.any() else float('nan')))
    # 最終模型：舊＋全部新資料
    Xa, Ya = np.vstack([X1, X2]), np.concatenate([Y1, Y2])
    clf = LogisticRegression(C=10, max_iter=5000, class_weight='balanced').fit(Xa, Ya)
    p = clf.predict_proba(Xa)[:, 1]
    print('  final n', len(Ya), 'train acc %.4f' % ((p > 0.5) == Ya).mean(), 'min P|occ %.2f max P|empty %.2f' % (p[Ya == 1].min(), p[Ya == 0].max()))
    out[slot] = {'w': [round(float(v), 6) for v in clf.coef_[0]], 'b': round(float(clf.intercept_[0]), 6), 'n': int(len(Ya))}
json.dump(out, open(r'C:\ai_lab\garage\occ_model_v2.json', 'w'))
print('saved v2')

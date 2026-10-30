import numpy as np, json, os
from PIL import Image
from sklearn.linear_model import LogisticRegression
src = open(r'C:\ai_lab\garage\embed_frames.py', encoding='utf-8-sig').read().split("\nD=")[0]
ns = {}
exec(src, ns)
embed, crop, roi = ns['embed'], ns['crop'], ns['roi']
d = np.load(r'C:\ai_lab\garage\emb.npz')
cl = json.load(open(r'C:\ai_lab\garage\clusters.json'))
occ = {'front': {1, 3, 5, 6, 7, 8, 9, 10, 11, 13}, 'back': {0, 2, 3, 4, 6, 9, 10, 12, 13}}
emp = {'front': {0, 2, 4}, 'back': {1, 8, 11}}
L = r'C:\ai_lab\garage\live'
fs = sorted(os.listdir(L))
out = {}
for slot in ('front', 'back'):
    lab = np.array(cl[slot])
    y = np.full(len(lab), -1)
    for c in occ[slot]:
        y[lab == c] = 1
    for c in emp[slot]:
        y[lab == c] = 0
    m = y >= 0
    X, yy = d[slot][m], y[m]
    live = np.array([embed(crop(Image.open(os.path.join(L, f)).convert('RGB'), roi['slots'][slot]['body'])) for f in fs])
    X = np.vstack([X, live])
    yy = np.concatenate([yy, np.zeros(len(live), dtype=int)])
    clf = LogisticRegression(C=10, max_iter=5000, class_weight='balanced').fit(X, yy)
    p = clf.predict_proba(X)[:, 1]
    print(slot, 'n', len(yy), 'train acc %.4f' % ((p > 0.5) == yy).mean(), 'min P(occ|occ) %.3f max P(occ|empty) %.3f' % (p[yy == 1].min(), p[yy == 0].max()))
    out[slot] = {'w': [round(float(v), 6) for v in clf.coef_[0]], 'b': round(float(clf.intercept_[0]), 6), 'n': int(len(yy))}
out['box'] = {s: roi['slots'][s]['body'] for s in ('front', 'back')}
json.dump(out, open(r'C:\ai_lab\garage\occ_model.json', 'w'))
print('saved')

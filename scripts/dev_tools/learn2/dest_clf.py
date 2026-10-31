import json, datetime as dt, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
sets = [(r'C:\ai_lab\topfloor\obs_pose.json', r'C:\ai_lab\topfloor\clips\clipmap.json', r'C:\ai_lab\topfloor\events.json'),
        (r'C:\ai_lab\topfloor\obs_pose2.json', r'C:\ai_lab\topfloor\clips2\clipmap.json', r'C:\ai_lab\topfloor\events2.json')]
X, Y, G, N = [], [], [], []


def mainp(ps):
    best, bs = None, 0
    for p in ps:
        b = p['box']
        a = max(0, (b[2] - b[0]) * (b[3] - b[1])) * p['conf']
        if p['conf'] >= 0.4 and a > bs:
            best, bs = p, a
    return best


def feat(rows):
    fr = [(t, mainp(ps)) for t, ps in rows]
    det = [(t, p) for t, p in fr if p]
    if len(det) < 4:
        return None
    xs = np.array([(p['box'][0] + p['box'][2]) / 2 for t, p in det])
    ys = np.array([p['box'][3] for t, p in det])
    hs = np.array([p['box'][3] - p['box'][1] for t, p in det])
    ts = np.array([t for t, p in det])
    k = det[-1][1]['kp']
    last = det[-min(4, len(det)):]
    face = np.mean([(q['kp'][0][2] > 0.5) + (q['kp'][1][2] > 0.5) + (q['kp'][2][2] > 0.5) for t, q in last]) / 3
    orient = np.mean([(q['kp'][5][0] - q['kp'][6][0]) if (q['kp'][5][2] > 0.4 and q['kp'][6][2] > 0.4) else 0 for t, q in last])
    ank = np.mean([(q['kp'][15][2] > 0.4) + (q['kp'][16][2] > 0.4) for t, q in last]) / 2
    n = len(xs)
    return [xs[-1], ys[-1], hs[-1], xs[-1] - xs[0], xs[0], xs[-1] - xs[max(0, n - 3)], xs[-1] - xs[max(0, n - 6)], hs[-1] - hs[0], hs.max(), ys.max(), n,
            face, orient, ank, (ts[-1] - ts[0]), xs.max() - xs.min(), xs.mean()]


for obsf, mapf, evf in sets:
    obs = json.load(open(obsf)); cm = {m['clip']: m for m in json.load(open(mapf, encoding='utf-8-sig'))}; ev = json.load(open(evf))
    for c, rows in obs.items():
        s = dt.datetime.strptime(cm[c]['start'], '%Y-%m-%d %H:%M:%S').timestamp(); e = s + cm[c]['dur']
        allp = [p for t, p in ev if s - 1 <= t <= e + 30]
        lab = 'study' if 'enter_study' in allp else 'bedroom' if 'enter_bedroom' in allp else None
        if lab is None:
            continue
        f = feat(rows)
        if f is None:
            continue
        X.append(f); Y.append(1 if lab == 'study' else 0); G.append(cm[c]['start'][:10]); N.append(c)
X = np.nan_to_num(np.array(X, float)); Y = np.array(Y); G = np.array(G)
import sys
if 'nopose' in sys.argv: X[:, 11:14] = 0
if 'xyonly' in sys.argv: X = X[:, [0,1,2,3,4,5,6,7,8,9,10,14,15,16]]
print('samples', len(Y), 'study', Y.sum(), 'bedroom', (Y == 0).sum(), 'days', sorted(set(G)))
for name, mk in (('logreg', lambda: LogisticRegression(C=1.0, max_iter=5000, class_weight='balanced')),
                 ('gboost', lambda: GradientBoostingClassifier(n_estimators=60, max_depth=2, random_state=0))):
    pred = np.zeros(len(Y), int)
    for g in sorted(set(G)):
        te = G == g; tr = ~te
        if len(set(Y[tr])) < 2:
            continue
        from sklearn.preprocessing import StandardScaler
        sc = StandardScaler().fit(X[tr])
        m = mk().fit(sc.transform(X[tr]), Y[tr])
        pred[te] = m.predict(sc.transform(X[te]))
    print(name, 'leave-one-day-out acc %.3f' % (pred == Y).mean(), 'study recall %.2f' % ((pred == 1) & (Y == 1)).sum() / max(1, (Y == 1).sum()) if False else '',
          'study recall %.2f bedroom recall %.2f' % (((pred == 1) & (Y == 1)).sum() / max(1, (Y == 1).sum()), ((pred == 0) & (Y == 0)).sum() / max(1, (Y == 0).sum())))
# 現行規則基準：用 x 位移方向（≥ +0.05 臥室、≤ −0.05 書房，其餘看不出）
dx = X[:, 3]
rule = np.where(dx >= 0.05, 0, np.where(dx <= -0.05, 1, -1))
ok = (rule == Y)
print('current rule: acc %.3f (undecided %d)' % (ok.mean(), (rule == -1).sum()), 'study recall %.2f bedroom recall %.2f' % (((rule == 1) & (Y == 1)).sum() / Y.sum(), ((rule == 0) & (Y == 0)).sum() / (Y == 0).sum()))

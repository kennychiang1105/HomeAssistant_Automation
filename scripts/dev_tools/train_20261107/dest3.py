"""第 3 批（2026-11-07）：頂樓去向（書房／臥室）學習式分類重新訓練與驗證。
A) 片段層級：舊模型（部署中，10/27～10/31 訓練）直接測新資料（真正的樣本外）；新模型＝舊＋新資料，依日期留一驗證。
B) 追蹤器層級：用主機上的 topfloor_track.py（topfloor_track_host.py）逐幀重播新影片，比較部署中 DEST_LR 與「不含該日」重新訓練的 DEST_LR 判出的去向。
用法：dest3.py [save]（save＝把用全部資料訓練的新權重存成 dest_lr_v3.json）"""
import json, sys, datetime as dt, numpy as np, copy
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, r'C:\ai_lab\topfloor')
import topfloor_track_host as T

sets = [(r'C:\ai_lab\topfloor\obs_pose.json', r'C:\ai_lab\topfloor\clips\clipmap.json', r'C:\ai_lab\topfloor\events.json', 1),
        (r'C:\ai_lab\topfloor\obs_pose2.json', r'C:\ai_lab\topfloor\clips2\clipmap.json', r'C:\ai_lab\topfloor\events2.json', 2),
        (r'C:\ai_lab\topfloor\obs_pose3.json', r'C:\ai_lab\topfloor\clips3\clipmap.json', r'C:\ai_lab\topfloor\events3.json', 3)]
XY = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16]
ORDER = 'x_last,y_last,h_last,dx_total,x_first,dx_last3,dx_last6,dh_total,h_max,y_max,n,duration,x_range,x_mean'


def mainp(ps):
    best, bs = None, 0
    for p in ps:
        b = p['box']
        a = max(0, (b[2] - b[0]) * (b[3] - b[1])) * p['conf']
        if p['conf'] >= 0.4 and a > bs:
            best, bs = p, a
    return best


def feat(rows):
    det = [(t, mainp(ps)) for t, ps in rows]
    det = [(t, p) for t, p in det if p]
    if len(det) < 4:
        return None
    xs = np.array([(p['box'][0] + p['box'][2]) / 2 for t, p in det])
    ys = np.array([p['box'][3] for t, p in det])
    hs = np.array([p['box'][3] - p['box'][1] for t, p in det])
    ts = np.array([t for t, p in det])
    n = len(xs)
    f = [xs[-1], ys[-1], hs[-1], xs[-1] - xs[0], xs[0], xs[-1] - xs[max(0, n - 3)], xs[-1] - xs[max(0, n - 6)], hs[-1] - hs[0], hs.max(), ys.max(), n,
         0, 0, 0, (ts[-1] - ts[0]), xs.max() - xs.min(), xs.mean()]
    return [f[i] for i in XY]


S = []      # 每段：dict(x, y, day, set, clip, rows, start)
for obsf, mapf, evf, k in sets:
    obs = json.load(open(obsf))
    cm = {m['clip']: m for m in json.load(open(mapf, encoding='utf-8-sig'))}
    ev = json.load(open(evf))
    for c, rows in obs.items():
        if c not in cm:
            continue
        s = dt.datetime.strptime(cm[c]['start'], '%Y-%m-%d %H:%M:%S').timestamp()
        e = s + (cm[c].get('dur') or (rows[-1][0] if rows else 0))
        allp = [p for t, p in ev if s - 1 <= t <= e + 30]
        lab = 'study' if 'enter_study' in allp else 'bedroom' if 'enter_bedroom' in allp else None
        if lab is None:
            continue
        f = feat(rows)
        if f is None:
            continue
        S.append({'x': f, 'y': 1 if lab == 'study' else 0, 'day': cm[c]['start'][:10], 'set': k, 'clip': c, 'rows': rows, 's': s})
X = np.nan_to_num(np.array([z['x'] for z in S], float))
Y = np.array([z['y'] for z in S])
G = np.array([z['day'] for z in S])
K = np.array([z['set'] for z in S])
print('samples', len(Y), 'study', int(Y.sum()), 'bedroom', int((Y == 0).sum()), '| set3', int((K == 3).sum()), 'study', int(Y[K == 3].sum()))
print('days', sorted(set(G)))


def fit(Xa, Ya):
    sc = StandardScaler().fit(Xa)
    m = LogisticRegression(C=1.0, max_iter=5000, class_weight='balanced').fit(sc.transform(Xa), Ya)
    return {'mean': [round(float(v), 6) for v in sc.mean_], 'scale': [round(float(v), 6) for v in sc.scale_],
            'w': [round(float(v), 6) for v in m.coef_[0]], 'b': round(float(m.intercept_[0]), 6), 'n': int(len(Ya)), 'order': ORDER}


def prob(lr, x):
    z = lr['b'] + sum(w * (v - mu) / sc for w, v, mu, sc in zip(lr['w'], x, lr['mean'], lr['scale']))
    return 1 / (1 + np.exp(-z))


def rep(pred, y, tag):
    pred, y = np.array(pred), np.array(y)
    st = ((pred == 1) & (y == 1)).sum() / max(1, (y == 1).sum())
    bd = ((pred == 0) & (y == 0)).sum() / max(1, (y == 0).sum())
    print('  %-46s n=%3d acc %.3f  書房判對 %.2f  臥室判對 %.2f' % (tag, len(y), (pred == y).mean(), st, bd))


OLD = copy.deepcopy(T.DEST_LR)
m3 = K == 3
print('== A) 片段層級（新資料 set3）')
rep([1 if prob(OLD, x) >= 0.5 else 0 for x in X[m3]], Y[m3], '部署中模型（舊資料訓練）直接測新資料')
# 新模型：舊＋新，依日期留一（只看新資料的日期）
pred = []
for i in np.where(m3)[0]:
    tr = G != G[i]
    lr = fit(X[tr], Y[tr])
    pred.append(1 if prob(lr, X[i]) >= 0.5 else 0)
rep(pred, Y[m3], '新模型（舊＋新，留一日驗證）')
pred_all = []
for g in sorted(set(G)):
    te = G == g
    lr = fit(X[~te], Y[~te])
    pred_all += [(i, 1 if prob(lr, X[i]) >= 0.5 else 0) for i in np.where(te)[0]]
pa = np.zeros(len(Y), int)
for i, p in pred_all:
    pa[i] = p
rep(pa, Y, '新模型（舊＋新，全部日期留一）')


# 追蹤器層級
def run_tracker(rows, lr):
    T.DEST_LR = lr
    cfg = dict(T.DEFAULT_CFG)
    tr = T.Tracker(cfg)
    ex = []
    for t, ps in rows:
        o = tr.add(t, [{'conf': p['conf'], 'box': p['box']} for p in ps])
        if o.get('exit'):
            ex.append(o['exit'])
    f = tr.finalize()
    if f.get('exit'):
        ex.append(f['exit'])
    dests = [e['dest'] for e in ex if e.get('dest') in ('study', 'bedroom')]
    return dests[-1] if dests else ''


print('== B) 追蹤器層級（主機 topfloor_track.py 重播新影片，最後去向）')
res = {'old': [], 'new': []}
for g in sorted(set(G[m3])):
    te = (G == g)
    lr_new = fit(X[~te], Y[~te])
    for i in np.where(te & m3)[0]:
        truth = 'study' if Y[i] == 1 else 'bedroom'
        res['old'].append((truth, run_tracker(S[i]['rows'], OLD)))
        res['new'].append((truth, run_tracker(S[i]['rows'], lr_new)))
T.DEST_LR = OLD
for k in ('old', 'new'):
    r = res[k]
    n = len(r)
    ok = sum(1 for a, b in r if a == b)
    und = sum(1 for a, b in r if b == '')
    st = [b for a, b in r if a == 'study']
    bd = [b for a, b in r if a == 'bedroom']
    print('  %-4s n=%d 判對 %d（%.1f%%）看不出 %d | 書房 %d 段：判對 %d 判成臥室 %d | 臥室 %d 段：判對 %d 判成書房 %d' % (
        k, n, ok, 100 * ok / max(1, n), und, len(st), st.count('study'), st.count('bedroom'), len(bd), bd.count('bedroom'), bd.count('study')))
if 'save' in sys.argv:
    final = fit(X, Y)
    json.dump(final, open(r'C:\ai_lab\topfloor\dest_lr_v3.json', 'w'))
    print('saved dest_lr_v3.json n', final['n'])

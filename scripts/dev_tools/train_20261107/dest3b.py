"""第 3 批 B 案：用追蹤器實際判斷去向時的「那一段」特徵訓練（訓練與上線用同一種特徵），依日期留一，在追蹤器層級比較。用法：dest3b.py [save]"""
import json, sys, math, copy, numpy as np
sys.argv_ = list(sys.argv)
sys.argv = ['dest3.py']
exec(open(r'C:\ai_lab\topfloor\dest3.py', encoding='utf-8').read().split("OLD = copy.deepcopy")[0])
sys.argv = sys.argv_
OLD = copy.deepcopy(T.DEST_LR)
ORIG_PROB = T.dest_lr_prob
REC = []


def seg_feat(seg):
    det = [f['p'] for f in seg if f['p']]
    if len(det) < 4:
        return None
    xs = [p['x'] for p in det]
    ys = [p['y'] for p in det]
    hs = [p['h'] for p in det]
    n = len(xs)
    ts = [f['t'] for f in seg if f['p']]
    return [xs[-1], ys[-1], hs[-1], xs[-1] - xs[0], xs[0], xs[-1] - xs[max(0, n - 3)], xs[-1] - xs[max(0, n - 6)], hs[-1] - hs[0], max(hs), max(ys), n,
            ts[-1] - ts[0], max(xs) - min(xs), sum(xs) / n]


def rec_prob(seg):
    f = seg_feat(seg)
    if f is not None:
        REC.append(f)
    return ORIG_PROB(seg)


def tracker_dest(rows, lr, record=False):
    T.DEST_LR = lr
    T.dest_lr_prob = rec_prob if record else ORIG_PROB
    del REC[:]
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
    T.dest_lr_prob = ORIG_PROB
    dests = [e['dest'] for e in ex if e.get('dest') in ('study', 'bedroom')]
    return (dests[-1] if dests else ''), (REC[-1] if REC else None)


# 收集每段在追蹤器裡最後一次房門口判斷的特徵
SF, SY, SG, IDX = [], [], [], []
for i, z in enumerate(S):
    d, f = tracker_dest(z['rows'], OLD, record=True)
    if f is not None:
        SF.append(f); SY.append(z['y']); SG.append(z['day']); IDX.append(i)
SF = np.nan_to_num(np.array(SF, float)); SY = np.array(SY); SG = np.array(SG); IDX = np.array(IDX)
print('追蹤器房門口判斷樣本', len(SY), '書房', int(SY.sum()))


def summarize(r, tag):
    n = len(r); ok = sum(1 for a, b in r if a == b); und = sum(1 for a, b in r if b == '')
    st = [b for a, b in r if a == 'study']; bd = [b for a, b in r if a == 'bedroom']
    print('  %-28s n=%d 判對 %d（%.1f%%）看不出 %d | 書房 %d：對 %d 錯 %d | 臥室 %d：對 %d 錯 %d' % (
        tag, n, ok, 100 * ok / max(1, n), und, len(st), st.count('study'), st.count('bedroom'), len(bd), bd.count('bedroom'), bd.count('study')))


for scope, sel in (('新資料（set3）', K == 3), ('全部資料', K > 0)):
    print('==', scope)
    res = {'舊模型（部署中）': [], 'A 整段特徵重訓': [], 'B 判斷段特徵重訓': []}
    for g in sorted(set(G[sel])):
        te = G == g
        lrA = fit(X[~te], Y[~te])
        trB = SG != g
        lrB = fit(SF[trB], SY[trB])
        for i in np.where(te & sel)[0]:
            truth = 'study' if Y[i] == 1 else 'bedroom'
            res['舊模型（部署中）'].append((truth, tracker_dest(S[i]['rows'], OLD)[0]))
            res['A 整段特徵重訓'].append((truth, tracker_dest(S[i]['rows'], lrA)[0]))
            res['B 判斷段特徵重訓'].append((truth, tracker_dest(S[i]['rows'], lrB)[0]))
    for k, r in res.items():
        summarize(r, k)
T.DEST_LR = OLD
if 'save' in sys.argv:
    final = fit(SF, SY)
    json.dump(final, open(r'C:\ai_lab\topfloor\dest_lr_v3.json', 'w'))
    print('saved dest_lr_v3.json（判斷段特徵）n', final['n'])

"""頂樓去向：學習式分類的採用門檻（dest_lr_hi／lo，現行 0.70／0.30）掃描，追蹤器層級，全部 261 段（舊模型對舊資料是樣本內，另列新資料 set3）。"""
import json, sys, copy, numpy as np
sys.argv = ['dest3.py']
exec(open(r'C:\ai_lab\topfloor\dest3.py', encoding='utf-8').read().split("OLD = copy.deepcopy")[0])
OLD = copy.deepcopy(T.DEST_LR)


def run(rows, hi, lo, dx=None):
    cfg = dict(T.DEFAULT_CFG)
    cfg['dest_lr_hi'], cfg['dest_lr_lo'] = hi, lo
    if dx is not None:
        cfg['exit_dx'] = dx
    tr = T.Tracker(cfg)
    ex = []
    for t, ps in rows:
        o = tr.add(t, [{'conf': p['conf'], 'box': p['box']} for p in ps])
        if o.get('exit'):
            ex.append(o['exit'])
    f = tr.finalize()
    if f.get('exit'):
        ex.append(f['exit'])
    d = [e['dest'] for e in ex if e.get('dest') in ('study', 'bedroom')]
    return d[-1] if d else ''


T.DEST_LR = OLD
for hi, lo in ((0.70, 0.30), (0.65, 0.35), (0.60, 0.40), (0.55, 0.45), (0.50, 0.50), (0.75, 0.25), (0.80, 0.20)):
    for scope, sel in (('set3', K == 3), ('all', K > 0)):
        r = [('study' if Y[i] else 'bedroom', run(S[i]['rows'], hi, lo)) for i in np.where(sel)[0]]
        ok = sum(a == b for a, b in r); wrong = sum(b != '' and a != b for a, b in r); und = sum(b == '' for a, b in r)
        print('hi %.2f lo %.2f %-4s n=%d 判對 %d 判錯 %d 看不出 %d' % (hi, lo, scope, len(r), ok, wrong, und))

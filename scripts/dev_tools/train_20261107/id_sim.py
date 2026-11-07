"""身分樣板補學模擬：用車牌證實（或排除法）的判錯／不採用畫面當新樣板，依日期留一，比較補學前後（現行門檻 score≥0.85、margin≥0.02）。
用法：id_sim.py [K]（每種情況最多取 K 張樣板，預設 6）  ；加 save 會輸出要補學的清單 id_learn.json（用全部日期挑）"""
import json, sys, collections, numpy as np
from PIL import Image
src = open(r'C:\ai_lab\garage\embed_frames.py', encoding='utf-8-sig').read().split("\nD=")[0]
ns = {}
exec(src, ns)
embed, crop = ns['embed'], ns['crop']
exec(open(r'C:\ai_lab\garage\id_eval.py', encoding='utf-8').read().split("print('frames'")[0])
K = int([a for a in sys.argv[1:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[1:]) else 6
G0 = json.load(open(r'C:\ai_lab\garage\gallery_now.json'))
rows_by = {r['name']: r for r in rows}
LABEL = {('front', 'luxgen_n7'): 'luxgen_n7:door', ('back', 'luxgen_n7'): 'luxgen_n7:inside',
         ('front', 'tesla_model3'): 'tesla_model3:door', ('back', 'tesla_model3'): 'tesla_model3:door'}


def classify(e, gallery):
    per = {}
    for g in gallery:
        per.setdefault(g['label'], []).append(float(np.dot(e, g['e'])))
    best = sorted(((max(v), l) for l, v in per.items()), reverse=True)
    base = {}
    for sim, l in best:
        base.setdefault(l.split(':')[0], []).append((sim, l))
    ranked = sorted(((v[0][0], b) for b, v in base.items()), reverse=True)
    return {'identity': ranked[0][1], 'score': ranked[0][0], 'second': ranked[1][0] if len(ranked) > 1 else None}


gal0 = [{'label': g['label'], 'e': np.asarray(g['emb'], dtype=np.float32)} for g in G0]
E = {}
diff = []
for name, n, lab, src_, idr, occ in L:
    im = Image.open(r'C:\ai_lab\garage\frames3\%s' % name).convert('RGB')
    e = embed(crop(im, rows_by[name]['slots'][n]['det']['box']))
    E[(name, n)] = e
    c = classify(e, gal0)
    if idr.get('score') is not None:
        diff.append(abs(c['score'] - idr['score']))
print('重現 add-on 分數：差異中位數 %.4f 最大 %.4f（n=%d）' % (np.median(diff), max(diff), len(diff)))


def judge(c, smin=0.85, mmin=0.02):
    if c['score'] < smin or (c['second'] is not None and c['score'] - c['second'] < mmin):
        return None
    return c['identity']


days = sorted(set(name[2:6] for name, *_ in L))


def pick_templates(pool):
    """每種（車位, 真實身分）挑判錯／不採用的畫面，時間上分散（相隔 ≥ 60 秒），最多 K 張"""
    out = []
    by = collections.defaultdict(list)
    for name, n, lab, src_, idr, occ in pool:
        c = classify(E[(name, n)], gal0)
        if judge(c) != lab:
            by[(n, lab)].append((name, n, lab))
    for k, v in by.items():
        v.sort()
        sel, last = [], None
        for name, n, lab in v:
            t = int(name[7:9]) * 3600 + int(name[9:11]) * 60 + int(name[11:13]) + int(name[2:6]) * 86400
            if last is None or t - last >= 60:
                sel.append((name, n, lab)); last = t
        step = max(1, len(sel) / K)
        out += [sel[int(i * step)] for i in range(min(K, len(sel)))]
    return out


tot = {'base': collections.Counter(), 'new': collections.Counter()}
for d in days:
    pool = [x for x in L if x[0][2:6] != d]
    tpl = pick_templates(pool)
    gal = gal0 + [{'label': LABEL[(n, lab)], 'e': E[(name, n)]} for name, n, lab in tpl]
    for name, n, lab, src_, idr, occ in L:
        if name[2:6] != d:
            continue
        for k, g in (('base', gal0), ('new', gal)):
            j = judge(classify(E[(name, n)], g))
            tot[k][(n, lab, 'ok' if j == lab else ('reject' if j is None else 'WRONG'))] += 1
for k in ('base', 'new'):
    c = tot[k]
    print('==', k)
    for n in ('front', 'back'):
        for lab in ('luxgen_n7', 'tesla_model3'):
            print('   %-5s %-12s 判對 %3d 判錯 %3d 不採用 %3d' % (n, lab, c[(n, lab, 'ok')], c[(n, lab, 'WRONG')], c[(n, lab, 'reject')]))
if 'save' in sys.argv:
    tpl = pick_templates(L)
    json.dump([{'name': name, 'slot': n, 'label': LABEL[(n, lab)]} for name, n, lab in tpl], open(r'C:\ai_lab\garage\id_learn.json', 'w'), indent=1)
    print('補學清單', len(tpl), collections.Counter(LABEL[(n, lab)] + '@' + n for name, n, lab in tpl))

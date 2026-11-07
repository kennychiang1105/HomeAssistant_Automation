"""身分辨識評估：add-on 的 CLIP 樣板 kNN（id）vs 車牌證實的身分（車牌依位置歸屬車位，另一車位用排除法）。
輸入：C:\\ai_lab\\garage\\id_out.jsonl（idbatch.py 的結果）。輸出各門檻下的判對／判錯／不採用，並列出判錯的畫面。"""
import json, sys, collections
PLATES = {'EAK8030': 'luxgen_n7', 'EBH8030': 'tesla_model3'}
FAM = ('luxgen_n7', 'tesla_model3')
rows = [json.loads(l) for l in open(r'C:\ai_lab\garage\id_out.jsonl', encoding='utf-8') if l.strip()]
rows = [r for r in rows if 'slots' in r]


def plate_car(t):
    if t in PLATES:
        return PLATES[t]
    near = [c for p, c in PLATES.items() if len(p) == len(t) and sum(a != b for a, b in zip(p, t)) == 1]
    return near[0] if len(set(near)) == 1 else None


def assign(r):
    out = {}
    for p in r.get('plates') or []:
        if p.get('conf', 0) < 0.8:
            continue
        cx, cy = p['cx'], p['cy']
        best = None
        for n, v in r['slots'].items():
            d = v.get('det')
            if not d:
                continue
            b = d['box']
            if not (b[0] <= cx <= b[2] and b[1] <= cy <= b[3]):
                continue
            ry = (cy - b[1]) / max(1e-6, b[3] - b[1]); rx = (cx - b[0]) / max(1e-6, b[2] - b[0])
            if not (0.45 <= ry <= 0.98 and 0.05 <= rx <= 0.95):
                continue
            sc = abs(ry - 0.72)
            if best is None or sc < best[0]:
                best = (sc, n)
        c = plate_car(p['text'])
        if best and c:
            out[best[1]] = c
    return out


L = []   # (name, slot, label, src, id dict, occ)
for r in rows:
    pa = assign(r)
    for n, v in r['slots'].items():
        if not v.get('det'):
            continue
        lab, src = None, None
        if n in pa:
            lab, src = pa[n], 'plate'
        else:
            other = [k for k in pa if k != n]
            if other and r['slots'][other[0]].get('det'):
                lab, src = FAM[1 - FAM.index(pa[other[0]])], 'excl'
        if lab:
            L.append((r['name'], n, lab, src, v.get('id') or {}, v.get('occ')))
print('frames', len(rows), 'labeled slot-frames', len(L), collections.Counter((n, lab, src) for _, n, lab, src, _, _ in L).most_common())


def judge(idr, smin, mmin):
    if not idr or idr.get('score', 0) < smin:
        return None
    sec = idr.get('second')
    if sec is not None and idr['score'] - sec < mmin:
        return None
    return idr['identity']


for smin, mmin in ((0.85, 0.02), (0.85, 0.03), (0.85, 0.04), (0.88, 0.02), (0.90, 0.02), (0.85, 0.05)):
    c = collections.Counter()
    for name, n, lab, src, idr, occ in L:
        j = judge(idr, smin, mmin)
        c[(n, 'ok' if j == lab else ('reject' if j is None else 'WRONG'))] += 1
    print('score>=%.2f margin>=%.2f' % (smin, mmin), ' '.join('%s:%s=%d' % (k[0], k[1], v) for k, v in sorted(c.items())))
wrong = [(name, n, lab, src, idr) for name, n, lab, src, idr, occ in L if judge(idr, 0.85, 0.02) not in (None, lab)]
print('判錯（現行門檻）', len(wrong))
for w in wrong[:60]:
    print('  ', w[0], w[1], 'truth', w[2], w[3], 'id', w[4].get('identity'), w[4].get('label'), w[4].get('score'), w[4].get('second'))
json.dump(wrong, open(r'C:\ai_lab\garage\id_wrong.json', 'w'))
# 分數差距分布
for n in ('front', 'back'):
    ok_m = sorted(round(idr['score'] - (idr.get('second') or 0), 3) for name, s, lab, src, idr, occ in L if s == n and idr and idr.get('identity') == lab)
    bad_m = sorted(round(idr['score'] - (idr.get('second') or 0), 3) for name, s, lab, src, idr, occ in L if s == n and idr and idr.get('identity') != lab)
    q = lambda a, f: a[int(f * (len(a) - 1))] if a else None
    print(n, '判對的 margin 10/50/90 分位', q(ok_m, 0.1), q(ok_m, 0.5), q(ok_m, 0.9), '| 判錯的 margin', bad_m[:20])

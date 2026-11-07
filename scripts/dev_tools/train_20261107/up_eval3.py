"""頂樓「上樓提早判斷」在新影片（set3，10/29～11/07）上的表現：真值＝影片期間有 08-5J arrive_up 事件。"""
import json, sys, datetime as dt, collections
sys.path.insert(0, r'C:\ai_lab\topfloor')
import topfloor_track_host as T
obs = json.load(open(r'C:\ai_lab\topfloor\obs_pose3.json'))
cm = {m['clip']: m for m in json.load(open(r'C:\ai_lab\topfloor\clips3\clipmap.json', encoding='utf-8-sig'))}
ev = json.load(open(r'C:\ai_lab\topfloor\events3.json'))
cfg = dict(T.DEFAULT_CFG)
for a in sys.argv[1:]:
    k, v = a.split('=')
    cfg[k] = float(v)
c = collections.Counter()
lead = []
fp = []
for clip, rows in obs.items():
    m = cm[clip]
    s = dt.datetime.strptime(m['start'], '%Y-%m-%d %H:%M:%S').timestamp()
    e = s + (m.get('dur') or (rows[-1][0] if rows else 0))
    ups = [t for t, p in ev if p == 'arrive_up' and s - 1 <= t <= e + 2]
    tr = T.Tracker(cfg)
    fire = None
    for t, ps in rows:
        o = tr.add(s + t, [{'conf': p['conf'], 'box': p['box']} for p in ps])
        if o.get('fire') == 'up' and fire is None:
            fire = s + t
    truth = bool(ups)
    if truth and fire:
        c['TP'] += 1
        lead.append(round(ups[0] - fire, 1))
    elif truth:
        c['FN'] += 1
    elif fire:
        c['FP'] += 1
        fp.append(clip)
    else:
        c['TN'] += 1
print(dict(c), 'recall %.2f' % (c['TP'] / max(1, c['TP'] + c['FN'])), 'precision %.2f' % (c['TP'] / max(1, c['TP'] + c['FP'])))
lead.sort()
print('提早秒數（實體 arrive_up − 模型判上樓；正＝模型較早）中位數', lead[len(lead) // 2] if lead else None, '分布', lead)
print('誤判上樓的片段', fp[:20])

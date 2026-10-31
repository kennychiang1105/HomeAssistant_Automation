import sys, json, datetime as dt, statistics as st
sys.path.insert(0, r'C:\ai_lab\topfloor')
import topfloor_track as T
cfg = dict(T.DEFAULT_CFG)
import os
cfg.update(json.loads(os.environ.get('TFCFG','{}')))
obs = json.load(open(r'C:\ai_lab\topfloor\obs_pose.json'))
cm = {m['clip']: m for m in json.load(open(r'C:\ai_lab\topfloor\clips\clipmap.json', encoding='utf-8-sig'))}
ev = json.load(open(r'C:\ai_lab\topfloor\events.json'))
rows = []
for c, fr in sorted(obs.items()):
    s = dt.datetime.strptime(cm[c]['start'], '%Y-%m-%d %H:%M:%S').timestamp()
    e = s + cm[c]['dur']
    ups = [t for t, p in ev if p == 'arrive_up' and s - 1 <= t <= e + 1]
    if not ups:
        continue
    tr = T.Tracker(cfg)
    first_det = None
    fire = None
    for t, ps in fr:
        pp = [{'conf': p['conf'], 'box': p['box']} for p in ps]
        o = tr.add(t, pp)
        if first_det is None and o.get('main'):
            first_det = t
        if o.get('fire') == 'up' and fire is None:
            fire = (t, o['frames'], o['detected'])
    if fire:
        rows.append((c[:4], round(first_det, 1), fire[0], fire[2], round(ups[0] - s, 1), round(fire[0] - first_det, 1), round(fire[0] - (ups[0] - s), 1)))
print('clip first_det fire_t detected_frames sensor_event_t  fire-first_det(s)  fire-sensor(s; negative=earlier)')
for r in rows:
    print(r)
print('n', len(rows), 'median fire-first_det %.1f' % st.median(r[5] for r in rows), 'median fire-sensor %.1f' % st.median(r[6] for r in rows))

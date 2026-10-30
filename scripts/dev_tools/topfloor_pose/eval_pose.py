import sys, json, datetime as dt, collections
sys.path.insert(0, r'C:\ai_lab\topfloor')
import topfloor_track as T

cfg = dict(T.DEFAULT_CFG)
for a in sys.argv[1:]:
    if a == 'down_on':
        cfg['descend_on'] = True
    if a == 'fire_both':
        cfg['fire_dirs'] = ['up', 'down']
src = r'C:\ai_lab\topfloor\obs_pose.json'
obs = json.load(open(src))
cm = {m['clip']: m for m in json.load(open(r'C:\ai_lab\topfloor\clips\clipmap.json', encoding='utf-8-sig'))}
ev = json.load(open(r'C:\ai_lab\topfloor\events.json'))


def truth(c):
    s = dt.datetime.strptime(cm[c]['start'], '%Y-%m-%d %H:%M:%S').timestamp()
    e = s + cm[c]['dur']
    inn = [p for t, p in ev if s - 1 <= t <= e + 1]
    after = [p for t, p in ev if e < t <= e + 30]
    d = None
    if 'arrive_up' in inn:
        d = 'up'
    elif any(p in ('down_start', 'leave_study_down', 'down') for p in inn + after):
        d = 'down'
    allp = inn + after
    dest = 'study' if 'enter_study' in allp else ('bedroom' if 'enter_bedroom' in allp else ('stairs' if d == 'down' else None))
    return d, dest


dirconf = collections.Counter()
fconf = collections.Counter()
dconf = collections.Counter()
rows_out = []
for c, rows in sorted(obs.items()):
    tr = T.Tracker(cfg)
    fires = []
    ex = []
    for t, ps in rows:
        pp = [{'conf': p['conf'], 'box': p['box']} for p in ps]
        o = tr.add(t, pp)
        if o.get('fire'):
            fires.append((t, o['fire']))
        if o.get('exit'):
            ex.append(o['exit'])
    f = tr.finalize()
    if f.get('exit'):
        ex.append(f['exit'])
    d, dest = truth(c)
    det = len([1 for t, ps in rows if T.main_person([{'conf': p['conf'], 'box': p['box']} for p in ps], cfg)])
    first = next((x[1] for x in fires if x[1] in ('up', 'down')), '-')
    fin = f['dir']
    dests = [e['dest'] for e in ex if e.get('dest')]
    got = dests[-1] if dests else '-'
    dirconf[(d or 'none', first)] += 1
    fconf[(d or 'none', fin)] += 1
    if dest:
        dconf[(dest, got)] += 1
    rows_out.append((c[:4], cm[c]['start'][5:], d, dest, det, first, fin, got))
print('first-fire (truth,got):', dict(dirconf))
print('final dir (truth,got):', dict(fconf))
print('exit dest (truth,got):', dict(dconf))
if '-v' in sys.argv:
    for r in rows_out:
        print(r)


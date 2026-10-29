import sys,json,os,sqlite3,datetime as dt,collections
sys.path.insert(0,'/config/scripts')
import topfloor_track as T
cfg=T.load_cfg('/config/topfloor_ai')
for a in sys.argv[1:]:
    if a.startswith('{'): cfg.update(json.loads(a))
obs=json.load(open('/config/tfclips/obs_new.json'))
cm={m['clip']:m for m in json.load(open('/config/tfclips/new/clipmap.json',encoding='utf-8-sig'))}
db=sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro",uri=True)
evs=[]
for ts,d in db.execute("""select e.time_fired_ts,d.shared_data from events e join event_types t on t.event_type_id=e.event_type_id left join event_data d on d.data_id=e.data_id where t.event_type='topfloor_path' and e.time_fired_ts>?""",(dt.datetime(2026,10,27).timestamp(),)):
    try: evs.append((ts,json.loads(d)['path']))
    except Exception: pass
evs.sort()
manual=[(dt.datetime(2026,10,29,0,23,30).timestamp(),dt.datetime(2026,10,29,0,25,30).timestamp(),'down')]
def truth(c):
    s=dt.datetime.strptime(cm[c]['start'],'%Y-%m-%d %H:%M:%S').timestamp(); e=s+cm[c]['dur']
    inn=[p for t,p in evs if s-1<=t<=e+1 and p!='vacant_landing']
    after=[p for t,p in evs if e<t<=e+30 and p!='vacant_landing']
    d=None
    if any(p=='arrive_up' for p in inn): d='up'
    elif any(p in('down_start','leave_study_down','down') for p in inn+after): d='down'
    for a,b,l in manual:
        if s<=b and e>=a: d='down'
    dest=None
    allp=inn+after
    if 'enter_study' in allp: dest='study'
    elif 'enter_bedroom' in allp: dest='bedroom'
    elif d=='down': dest='stairs'
    return d,dest,inn
dirconf=collections.Counter(); fconf=collections.Counter(); dconf=collections.Counter(); bad=[]
for c,rows in sorted(obs.items()):
    tr=T.Tracker(cfg); fires=[]; ex=[]
    for t,ps in rows:
        o=tr.add(t,ps)
        if o.get('fire'): fires.append((t,o['fire']))
        if o.get('exit'): ex.append(o['exit'])
    f=tr.finalize()
    if f.get('exit'): ex.append(f['exit'])
    d,dest,inn=truth(c)
    det=len([1 for t,ps in rows if T.main_person(ps,cfg)])
    first=next((x[1] for x in fires if x[1] in('up','down')),'-')
    fin=f['dir']
    dests=[e['dest'] for e in ex if e.get('dest')]
    got=dests[-1] if dests else '-'
    key=(d or 'none')
    dirconf[(key,first)]+=1; fconf[(key,fin)]+=1
    if dest: dconf[(dest,got)]+=1
    if (d and fin!=d) or (d is None and det>=4 and fin in('up','down')) or (dest and got!=dest):
        bad.append((c,cm[c]['start'][5:],cm[c]['dur'],'truth',d,dest,'det',det,'first',first,'final',fin,'exit',got,f.get('reason','')[:50]))
print('cfg fire_dirs',cfg['fire_dirs'])
print('first-fire (truth,got):',dict(dirconf))
print('final dir (truth,got):',dict(fconf))
print('exit dest (truth,got):',dict(dconf))
for b in bad: print(b)
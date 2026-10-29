import sys,json,sqlite3,datetime as dt,collections
sys.path.insert(0,'/config/scripts')
import topfloor_track as T
cfg=T.load_cfg('/config/topfloor_ai')
for a in sys.argv[1:]:
    if a.startswith('{'): cfg.update(json.loads(a))
obs=json.load(open('/config/tfclips/obs_new.json'))
cm={m['clip']:m for m in json.load(open('/config/tfclips/new/clipmap.json',encoding='utf-8-sig'))}
db=sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro",uri=True)
ups=[];downs=[]
for ts,d in db.execute("""select e.time_fired_ts,d.shared_data from events e join event_types t on t.event_type_id=e.event_type_id left join event_data d on d.data_id=e.data_id where t.event_type='topfloor_path' and e.time_fired_ts>?""",(dt.datetime(2026,10,27).timestamp(),)):
    p=json.loads(d)['path']
    if p=='arrive_up': ups.append(ts)
    if p in('leave_study_down','down_start','down'): downs.append(ts)
downs.append(dt.datetime(2026,10,29,0,24,0).timestamp())
res=[]
for c,rows in sorted(obs.items()):
    tr=T.Tracker(cfg); fires=[]
    for t,ps in rows:
        o=tr.add(t,ps)
        if o.get('fire'): fires.append((t,o['fire']))
    f=tr.finalize()
    s=dt.datetime.strptime(cm[c]['start'],'%Y-%m-%d %H:%M:%S').timestamp(); e=s+cm[c]['dur']
    nxt=[u-e for u in ups if 0<=u-e<=900]
    prv=[s-u for u in ups if 0<=s-u<=60]
    dn=[x for x in downs if s-30<=x<=e+30]
    det=len([1 for t,ps in rows if T.main_person(ps,cfg)])
    first=next((x[1] for x in fires if x[1] in('up','down')),'-')
    res.append((c,cm[c]['start'][5:],det,first,f['dir'],'up_within15min' if nxt else '','after_up<60s' if prv else '','sensor_down' if dn else ''))
fd=[r for r in res if r[4]=='down' and r[2]>=4]
print('final=down & det>=4 clips:',len(fd),' validated by next-up<=15min or sensor_down:',len([r for r in fd if r[5] or r[7]]))
for r in fd:
    if not (r[5] or r[7]): print('UNVALIDATED',r)
fdn=[r for r in res if r[3]=='down']
print('first-fire down clips:',len(fdn),[ (r[0][:4],r[1],r[4],r[5],r[7]) for r in fdn])
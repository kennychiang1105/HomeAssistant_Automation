import sys,json,os,collections
sys.path.insert(0,'/config/scripts')
import topfloor_track as T
cfg=T.load_cfg('/config/topfloor_ai')
if len(sys.argv)>1 and sys.argv[1]=='--cfg':
    cfg.update(json.loads(sys.argv[2]))
M=json.load(open('/config/tfclips/map.json',encoding='utf-8-sig'))
FPS=float(os.environ.get('FPS','1'))
cache_p='/config/tfclips/obs_%g.json'%FPS
obs=json.load(open(cache_p)) if os.path.exists(cache_p) else {}
import glob,subprocess,tempfile
def observe(clip):
    """?????????add-on?????????????????????????????"""
    if clip in obs: return obs[clip]
    d=tempfile.mkdtemp(prefix='tfo_')
    subprocess.run(['ffmpeg','-loglevel','error','-i','/config/tfclips/'+clip,'-vf','fps=%g,scale=640:-1'%FPS,d+'/f%04d.jpg'],check=True)
    rows=[]
    for i,f in enumerate(sorted(glob.glob(d+'/*.jpg'))):
        try: rows.append([i/FPS,T.vision_persons('http://local-garage-vision:8099',f)])
        except Exception as e: rows.append([i/FPS,[]])
        os.remove(f)
    os.rmdir(d); obs[clip]=rows
    return rows
byclip=collections.defaultdict(list)
for m in M: byclip[m['clip']].append(m)
res={}
for clip,evs in byclip.items():
    rows=observe(clip)
    tr=T.Tracker(cfg); fires=[]
    for t,persons in rows:
        o=tr.add(t,persons)
        if o['fire']: fires.append((t,o['fire']))
    res[clip]=(fires,tr.finalize(),evs)
json.dump(obs,open(cache_p,'w'))
exp={'arrive_up':'up','down_start':'down','leave_study_down':'down','down':'down'}
conf=collections.Counter(); fconf=collections.Counter(); delays=[]; bad=[]
for clip,(fires,fin,evs) in res.items():
    want={exp[e['label']] for e in evs}
    first=next(((t,d) for t,d in fires if d in('up','down')),None)
    got=first[1] if first else 'nofire'
    fgot=fin['dir']
    for w in want:
        conf[(w,got)]+=1
        fconf[(w,fgot)]+=1
    ok=(got in want)
    if first and ok:
        delays.append(first[0]-min(e['offset'] for e in evs))
    if not ok: bad.append((clip,sorted(want),got,fgot,[ (e['label'],e['ev'],e['offset']) for e in evs][:2],fires[:3],fin['reason']))
print('config:',{k:cfg[k] for k in ('up_x','up_dx','up_start_max','down_x','down_dx')})
print('confusion (want,first_fire):',dict(conf))
tot=sum(conf.values()); okn=sum(v for (w,g),v in conf.items() if w==g)
print('accuracy early-decision: %d/%d = %.0f%%'%(okn,tot,100*okn/max(tot,1)))
fok=sum(v for (w,g),v in fconf.items() if w==g)
print('final-class confusion:',dict(fconf),'accuracy %d/%d = %.0f%%'%(fok,tot,100*fok/max(tot,1)))
if delays:
    delays.sort(); print('fire time vs 08-5J event (s, negative=earlier): median %.1f  min %.1f  max %.1f'%(delays[len(delays)//2],delays[0],delays[-1]))
for b in bad: print('MISS',b)


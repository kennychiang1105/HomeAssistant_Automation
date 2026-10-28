import sys,json,os,glob,subprocess,tempfile
sys.path.insert(0,'/config/scripts')
import topfloor_track as T
cfg=T.load_cfg('/config/topfloor_ai')
FPS=2.0
M=json.load(open('/config/tfclips/negmap.json',encoding='utf-8-sig'))
cache='/config/tfclips/obs_neg.json'
obs=json.load(open(cache)) if os.path.exists(cache) else {}
fp=0
for m in M:
    clip=m['clip']
    if clip not in obs:
        d=tempfile.mkdtemp(prefix='tfn_')
        subprocess.run(['ffmpeg','-loglevel','error','-i','/config/tfclips/'+clip,'-vf','fps=2,scale=640:-1',d+'/f%04d.jpg'],check=True)
        rows=[]
        for i,f in enumerate(sorted(glob.glob(d+'/*.jpg'))):
            try: rows.append([i/FPS,T.vision_persons('http://local-garage-vision:8099',f)])
            except Exception: rows.append([i/FPS,[]])
            os.remove(f)
        os.rmdir(d); obs[clip]=rows
        json.dump(obs,open(cache,'w'))
    tr=T.Tracker(cfg); fires=[]
    for t,ps in obs[clip]:
        o=tr.add(t,ps)
        if o['fire']: fires.append((t,o['fire']))
    fin=tr.finalize()
    det=len([1 for t,ps in obs[clip] if T.main_person(ps,cfg)])
    flag='FALSE-POSITIVE' if fires else 'ok'
    if fires: fp+=1
    print(clip,m['label'],m['ev'],'detected frames',det,'fires',fires,'final',fin['dir'],flag)
print('false positives: %d / %d'%(fp,len(M)))

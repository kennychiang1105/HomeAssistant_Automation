import sys,json,os,glob,subprocess,tempfile,time
sys.path.insert(0,'/config/scripts')
import topfloor_track as T
FPS=2.0
D='/config/tfclips/new/'
cache='/config/tfclips/obs_new.json'
obs=json.load(open(cache)) if os.path.exists(cache) else {}
t0=time.time()
for clip in sorted(os.listdir(D)):
    if not clip.endswith('.mp4') or clip in obs: continue
    d=tempfile.mkdtemp(prefix='tfn_')
    subprocess.run(['ffmpeg','-loglevel','error','-i',D+clip,'-vf','fps=2,scale=640:-1',d+'/f%04d.jpg'],check=True)
    rows=[]
    for i,f in enumerate(sorted(glob.glob(d+'/*.jpg'))):
        try: rows.append([i/FPS,T.vision_persons('http://local-garage-vision:8099',f)])
        except Exception: rows.append([i/FPS,[]])
        os.remove(f)
    os.rmdir(d); obs[clip]=rows
    json.dump(obs,open(cache,'w'))
    print(clip,len(rows),round(time.time()-t0),flush=True)
print('DONE',flush=True)
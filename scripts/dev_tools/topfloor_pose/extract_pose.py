import cv2, json, os, sys, time
from ultralytics import YOLO
m=YOLO('yolo11m-pose.pt')
D=r'C:\ai_lab\topfloor\clips'
out={}
t0=time.time()
for f in sorted(os.listdir(D)):
    if not f.endswith('.mp4'): continue
    cap=cv2.VideoCapture(os.path.join(D,f)); fps=cap.get(cv2.CAP_PROP_FPS) or 25
    step=max(1,int(round(fps/2))); i=0; rows=[]
    while True:
        ok,fr=cap.read()
        if not ok: break
        if i%step==0:
            H,W=fr.shape[:2]
            r=m.predict(fr,imgsz=640,conf=0.25,verbose=False,device=0)[0]
            ps=[]
            if r.boxes is not None and len(r.boxes):
                for b,c,k in zip(r.boxes.xyxyn.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.keypoints.data.cpu().numpy()):
                    kp=[[round(float(x)/W,4),round(float(y)/H,4),round(float(s),3)] for x,y,s in k]
                    ps.append({'conf':round(float(c),3),'box':[round(float(v),4) for v in b],'kp':kp})
            rows.append([round(i/fps,2),ps])
        i+=1
    cap.release(); out[f]=rows
    print(f,len(rows),round(time.time()-t0),flush=True)
json.dump(out,open(r'C:\ai_lab\topfloor\obs_pose.json','w'))
print('DONE')
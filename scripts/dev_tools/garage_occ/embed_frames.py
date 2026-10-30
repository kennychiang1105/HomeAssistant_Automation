import onnxruntime as ort, numpy as np, json, os, cv2, time
from PIL import Image
roi=json.load(open(r'C:\ai_lab\garage\garage_roi.json',encoding='utf-8'))
so=ort.SessionOptions(); so.intra_op_num_threads=8
clip=ort.InferenceSession(r'C:\ai_lab\garage\clip_visual.onnx',so,providers=['CPUExecutionProvider'])
MEAN=np.array([0.48145466,0.4578275,0.40821073],dtype=np.float32); STD=np.array([0.26862954,0.26130258,0.27577711],dtype=np.float32)
def embed(img):
    w,h=img.size; s=224/max(w,h); nw,nh=max(1,round(w*s)),max(1,round(h*s))
    c=Image.new('RGB',(224,224),(0,0,0)); c.paste(img.resize((nw,nh),Image.BICUBIC),((224-nw)//2,(224-nh)//2))
    a=((np.asarray(c,dtype=np.float32)/255.0-MEAN)/STD).transpose(2,0,1)[None].astype(np.float32)
    e=clip.run(None,{clip.get_inputs()[0].name:a})[0][0]; return e/np.linalg.norm(e)
def crop(img,box,pad=0.04):
    W,H=img.size; w,h=box[2]-box[0],box[3]-box[1]
    return img.crop((max(0,int((box[0]-w*pad)*W)),max(0,int((box[1]-h*pad)*H)),min(W,int((box[2]+w*pad)*W)),min(H,int((box[3]+h*pad)*H))))
D=r'C:\ai_lab\garage\frames'
names=sorted(os.listdir(D)); E={'front':[],'back':[]}; sat=[]; t0=time.time()
for i,n in enumerate(names):
    im=Image.open(os.path.join(D,n)).convert('RGB')
    a=np.asarray(im.resize((336,189)))
    sat.append(float((a.max(2).astype(int)-a.min(2).astype(int)).mean()))
    for s in ('front','back'):
        E[s].append(embed(crop(im,roi['slots'][s]['body'])))
    if i%200==0: print(i,len(names),round(time.time()-t0),flush=True)
np.savez(r'C:\ai_lab\garage\emb.npz',names=np.array(names),front=np.array(E['front']),back=np.array(E['back']),sat=np.array(sat))
print('DONE')

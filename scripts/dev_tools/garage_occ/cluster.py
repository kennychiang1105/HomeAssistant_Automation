import numpy as np, json, os, cv2
from sklearn.cluster import KMeans
d=np.load(r'C:\ai_lab\garage\emb.npz'); names=d['names']; sat=d['sat']
roi=json.load(open(r'C:\ai_lab\garage\garage_roi.json',encoding='utf-8'))
os.makedirs(r'C:\ai_lab\garage\clusters',exist_ok=True)
res={}
for slot in ('front','back'):
    X=d[slot]; ir=(sat<8).astype(int)           # 紅外線（無彩度）
    km=KMeans(n_clusters=14,n_init=5,random_state=0).fit(X); lab=km.labels_
    res[slot]=lab.tolist()
    b=roi['slots'][slot]['body']; rows=[]
    for k in range(14):
        idx=np.where(lab==k)[0]; rng=np.random.default_rng(k); pick=rng.choice(idx,size=min(6,len(idx)),replace=False)
        tiles=[]
        for i in pick:
            im=cv2.imread(os.path.join(r'C:\ai_lab\garage\frames',names[i])); H,W=im.shape[:2]
            c=im[int(b[1]*H):int(b[3]*H),int(b[0]*W):int(b[2]*W)]; c=cv2.resize(c,(240,180))
            tiles.append(c)
        while len(tiles)<6: tiles.append(np.zeros((180,240,3),np.uint8))
        row=np.hstack(tiles)
        cv2.putText(row,'C%d n=%d IR=%.0f%%'%(k,len(idx),100*ir[idx].mean()),(5,20),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,255),2)
        rows.append(row)
    cv2.imwrite(r'C:\ai_lab\garage\clusters\%s_a.jpg'%slot,np.vstack(rows[:7]),[cv2.IMWRITE_JPEG_QUALITY,80])
    cv2.imwrite(r'C:\ai_lab\garage\clusters\%s_b.jpg'%slot,np.vstack(rows[7:]),[cv2.IMWRITE_JPEG_QUALITY,80])
json.dump(res,open(r'C:\ai_lab\garage\clusters.json','w'))
print('ok')
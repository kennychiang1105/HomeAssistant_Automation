import sys, json, collections, datetime, math
sys.path.insert(0,'/config/scripts')
import numpy as np
import topfloor_track as T
cfg=T.load_cfg('/config/topfloor_ai')
lab=json.load(open('/config/tfclips/tf_labels.json')); eps=json.load(open('/config/tfclips/tf_eps.json'))
DEST={'enter_bedroom':'bedroom','leave_study_bedroom':'bedroom','enter_study':'study','down':'stairs','down_start':'stairs','leave_study_down':'stairs'}
good=[(t,DEST[p]) for t,p,s,_ in lab if p in DEST and not s.startswith('cam') and s not in ('bed_lamp_on','study_on')]
CL=['bedroom','study','stairs']
def feats(seg):
    d=[f['p'] for f in seg]; xs=np.array([p['x'] for p in d]); ys=np.array([p['y'] for p in d]); hs=np.array([p['h'] for p in d])
    n=len(d); k=min(3,n)
    return [xs[0],ys[0],hs[0],xs[-1],ys[-1],hs[-1],xs[-1]-xs[0],hs[-1]-hs[0],xs.min(),xs.max(),xs[-k:].mean(),ys[-k:].mean(),hs[-k:].mean(),math.log(n),
            (seg[-1]['t']-seg[0]['t']), xs.std(), xs[-1]-xs[-k], float(xs[-1]>=0.86), float(xs[-1]<=0.45)]
X=[];Y=[];D=[];R=[];EX=[]
for e in eps:
    tr=T.Tracker(cfg); frames=[]
    exits=[]
    for f in e:
        o=tr.add(f['t'],f['p'])
        if o.get('exit'): exits.append((f['t'],o['exit'], [dict(x) for x in tr.frames if x['p'] and x['t']>0]))
    # 重算每個 exit 的段落（以 exit_mark 切）
    det_all=[x for x in tr.frames if x['p']]
    tr2=T.Tracker(cfg); marks=[]
    for f in e:
        o=tr2.add(f['t'],f['p'])
        if o.get('exit'): marks.append((f['t'],o['exit'],tr2.exit_mark))
    fin=tr2.finalize()
    prev=0
    allseg=[]
    for te,ex,mk in marks:
        seg=[x for x in det_all if prev<x['t']<=mk]; prev=mk
        allseg.append((te,ex,seg))
    if fin.get('exit'):
        seg=[x for x in det_all if x['t']>prev]; allseg.append((e[-1]['t'],fin['exit'],seg))
    for te,ex,seg in allseg:
        if len(seg)<cfg['exit_min_det']: continue
        c=[(abs(L-te),d) for L,d in good if -30<=L-te<=25]
        ds=set(d for _,d in c)
        if len(ds)!=1: continue
        X.append(feats(seg)); Y.append(CL.index(list(ds)[0])); D.append(datetime.datetime.fromtimestamp(te).strftime('%m%d')); R.append(ex['dest'] or '?')
X=np.array(X); Y=np.array(Y); D=np.array(D)
print('樣本',len(Y),collections.Counter(CL[i] for i in Y), '天數',len(set(D)))
base=sum(1 for r,y in zip(R,Y) if r==CL[y]); print('現行規則正確',base,'/',len(Y), '(%.0f%%)'%(100*base/len(Y)))
def fit(X,Y,lam,it=3000,lr=0.3):
    mu=X.mean(0); sd=X.std(0)+1e-6; Z=(X-mu)/sd
    W=np.zeros((Z.shape[1],3)); b=np.zeros(3); Yh=np.eye(3)[Y]
    for _ in range(it):
        S=Z@W+b; S-=S.max(1,keepdims=True); P=np.exp(S); P/=P.sum(1,keepdims=True)
        G=(P-Yh)/len(Z); W-=lr*(Z.T@G+lam*W); b-=lr*G.sum(0)
    return mu,sd,W,b
def pred(m,X):
    mu,sd,W,b=m; S=((X-mu)/sd)@W+b; S-=S.max(1,keepdims=True); P=np.exp(S); return P/P.sum(1,keepdims=True)
for lam in (0.003,0.01,0.03,0.1):
    ok=0; ok_hi=0; n_hi=0
    for d in sorted(set(D)):
        te=D==d; tr_=~te
        if te.sum()==0 or tr_.sum()<20: continue
        m=fit(X[tr_],Y[tr_],lam); P=pred(m,X[te]); pr=P.argmax(1); ok+=(pr==Y[te]).sum()
        hi=P.max(1)>=0.6; ok_hi+=((pr==Y[te])&hi).sum(); n_hi+=hi.sum()
    print('lam',lam,'留一天驗證 正確',ok,'/',len(Y),'(%.0f%%)'%(100*ok/len(Y)),' 信心≥0.6:',ok_hi,'/',n_hi)
np.save('/config/tfclips/tf_X.npy',X); np.save('/config/tfclips/tf_Y.npy',Y); json.dump(list(D),open('/config/tfclips/tf_D.json','w'))
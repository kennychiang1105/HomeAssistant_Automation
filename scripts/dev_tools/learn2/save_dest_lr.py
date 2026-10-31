import json, datetime as dt, numpy as np, sys
sys.argv=['x','xyonly']
exec(open(r'C:\ai_lab\topfloor\dest_clf.py',encoding='utf-8').read().split("for name, mk in")[0])
from sklearn.preprocessing import StandardScaler
sc=StandardScaler().fit(X)
m=LogisticRegression(C=1.0,max_iter=5000,class_weight='balanced').fit(sc.transform(X),Y)
out={'mean':[round(float(v),6) for v in sc.mean_],'scale':[round(float(v),6) for v in sc.scale_],'w':[round(float(v),6) for v in m.coef_[0]],'b':round(float(m.intercept_[0]),6),'n':int(len(Y)),
     'order':'x_last,y_last,h_last,dx_total,x_first,dx_last3,dx_last6,dh_total,h_max,y_max,n,duration,x_range,x_mean'}
json.dump(out,open(r'C:\ai_lab\topfloor\dest_lr.json','w'))
print('saved', out['n'])
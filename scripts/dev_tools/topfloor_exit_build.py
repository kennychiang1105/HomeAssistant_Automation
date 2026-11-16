"""建立去向評估資料：從 recorder 的 topfloor_path 事件（只取感應器來源）與 /share/learn_collect/topfloor 的逐幀紀錄，輸出 tfclips/tf_labels.json、tf_eps.json；之後執行 topfloor_exit_eval.py（HA 容器內，有 numpy）。在主機用 sudo python3 執行。"""
import sys, json, glob, sqlite3, collections, datetime
sys.path.insert(0,'/homeassistant/scripts')
import topfloor_track as T
cfg=T.load_cfg('/homeassistant/topfloor_ai')
# --- labels from recorder
c=sqlite3.connect('file:/homeassistant/home-assistant_v2.db?mode=ro',uri=True)
lab=[]
for ts,sd in c.execute("select e.time_fired_ts, d.shared_data from events e join event_types t using(event_type_id) join event_data d using(data_id) where t.event_type='topfloor_path' order by e.time_fired_ts"):
    try: j=json.loads(sd)
    except: continue
    ev=j.get('evidence','')
    src=ev.split('｜')[0] if '｜' in ev else ''
    lab.append((ts,j.get('path'),src,ev))
print('labels',len(lab), collections.Counter((p,s) for _,p,s,_ in lab).most_common(30))
json.dump(lab,open('/homeassistant/tfclips/tf_labels.json','w'),ensure_ascii=False)
# --- episodes from collected frames
eps=[]
for d in sorted(glob.glob('/share/learn_collect/topfloor/2026*')):
    rows=[]
    for line in open(d+'/index.jsonl',encoding='utf-8'):
        try: r=json.loads(line)
        except: continue
        rows.append(r)
    rows.sort(key=lambda r:r['t'])
    cur=[]
    for r in rows:
        if cur and r['t']-cur[-1]['t']>cfg['idle_reset_s']:
            eps.append(cur); cur=[]
        cur.append(r)
    if cur: eps.append(cur)
print('episodes',len(eps), 'frames', sum(len(e) for e in eps))
json.dump([[ {'t':r['t'],'p':[{'conf':p['c'],'box':p['b']} for p in r['persons']]} for r in e] for e in eps],open('/homeassistant/tfclips/tf_eps.json','w'))
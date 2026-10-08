# 頂樓感應燈 7 天紀錄分析（唯讀）。用法：cat 此檔 | ssh kenny1105@192.168.68.97 'python3 -'
# 只讀 HA 紀錄庫（mode=ro），不需複製資料庫。DAYS 可改。
import sqlite3,time,json,collections,datetime as dt
c=sqlite3.connect("file:/homeassistant/home-assistant_v2.db?mode=ro",uri=True)
NOW=time.time(); DAYS=7; SINCE=NOW-DAYS*86400
def L(ts): return dt.datetime.fromtimestamp(ts).strftime('%m/%d %H:%M:%S')
def rows(e):
    return c.execute("""select s.state,s.last_updated_ts,s.context_id_bin,s.context_user_id_bin,s.context_parent_id_bin,a.shared_attrs
      from states s join states_meta m on m.metadata_id=s.metadata_id left join state_attributes a on a.attributes_id=s.attributes_id
      where m.entity_id=? and s.last_updated_ts>? order by s.last_updated_ts""",(e,SINCE)).fetchall()
# automation context map
ctx={}
for cid,data in c.execute("""select e.context_id_bin, d.shared_data from events e join event_types t on t.event_type_id=e.event_type_id
   left join event_data d on d.data_id=e.data_id where t.event_type in ('automation_triggered','script_started') and e.time_fired_ts>?""",(SINCE-3600,)):
    try: ctx[cid]=json.loads(data).get('name') or json.loads(data).get('entity_id')
    except: pass
def who(r):
    st,ts,cid,uid,pid,_=r
    if cid in ctx: return 'A:'+ctx[cid][:22]
    if pid in ctx: return 'A:'+ctx[pid][:22]
    if uid: return 'USER'
    if pid: return 'PARENT?'
    return 'DEVICE/外部'
CAM="binary_sensor.wu_lou_she_ying_ji_person_detected"
cam=rows(CAM)
visits=[];on=None
for r in cam:
    if r[0]=='on' and on is None: on=r[1]
    elif r[0]!='on' and on is not None: visits.append([on,r[1]]); on=None
mv=[]
for v in visits:
    if mv and v[0]-mv[-1][1]<5: mv[-1][1]=v[1]
    else: mv.append(v)
print("== 攝影機有人：原始 on 段 %d，合併(間隔<5s) %d 段，日均 %.0f"%(len(visits),len(mv),len(mv)/7))
dur=[v[1]-v[0] for v in mv]; dur.sort()
print("   停留秒數 中位 %.0f / 90%% %.0f / 最長 %.0f"%(dur[len(dur)//2],dur[int(len(dur)*.9)],dur[-1]))
pir={}
for k in ['left','right']:
    pir[k]=[r[1] for r in rows("binary_sensor.shu_fang_gan_ying_kai_guan_motion_"+k) if r[0]=='on']
    print("== PIR %s on 次數 %d（日均 %.0f）"%(k,len(pir[k]),len(pir[k])/7))
lines={}
for k in ['stairs','bedroom','studyroom']:
    _rs=rows("input_datetime.topfloor_%s_line_last_triggered"%k); _out=[]; _prev=None
    for r in _rs:
        if r[0]!=_prev and r[0] not in ('unknown','unavailable') and _prev is not None: _out.append(r[1])
        _prev=r[0]
    lines[k]=_out
def near(lst,t,w): return any(abs(x-t)<=w for x in lst)
def cam_near(t,w):
    return any(v[0]-w<=t<=v[1]+w for v in mv)
print("== 跨線（以 08-5G 寫入時間計）")
for k,lst in lines.items():
    dup=sum(1 for a,b in zip(lst,lst[1:]) if b-a<3)
    ghost=[t for t in lst if not cam_near(t,10) and not near(pir['left'],t,10) and not near(pir['right'],t,10)]
    print("   %-9s 次數 %3d  3秒內重複 %2d  前後10秒無攝影機/PIR(疑似雜訊) %2d (%.0f%%)"%(k,len(lst),dup,len(ghost),100*len(ghost)/max(1,len(lst))))
alll=sorted(lines['stairs']+lines['bedroom']+lines['studyroom'])
nol=[v for v in mv if not any(v[0]-5<=t<=v[1]+10 for t in alll)]
longv=[v for v in mv if v[1]-v[0]>=4]
nol_long=[v for v in longv if not any(v[0]-5<=t<=v[1]+10 for t in alll)]
print("== 攝影機停留≥4秒的通行 %d 段，其中完全沒有任何跨線 %d 段 (%.0f%%)"%(len(longv),len(nol_long),100*len(nol_long)/max(1,len(longv))))
# PIR right with camera but no stairs line
pr_cam=[t for t in pir['right'] if cam_near(t,5)]
pr_cam_nos=[t for t in pr_cam if not near(lines['stairs'],t,15)]
print("== PIR右(走道)且攝影機有人 %d 次，其中 15 秒內無樓梯線 %d 次 (%.0f%%)"%(len(pr_cam),len(pr_cam_nos),100*len(pr_cam_nos)/max(1,len(pr_cam))))
pl_nostudy=[t for t in pir['left'] if not near(lines['studyroom'],t,15) and cam_near(t,10)]
print("== PIR左且攝影機前後10秒有人 %d 次中 15秒內無書房線 %d 次"%(sum(1 for t in pir['left'] if cam_near(t,10)),len(pl_nostudy)))
# hours
hc=collections.Counter(dt.datetime.fromtimestamp(v[0]).hour for v in longv)
print("== 攝影機通行(≥4s)每小時分布:", ' '.join('%02d:%d'%(h,hc[h]) for h in range(24)))
# lights
def sessions(e):
    rs=rows(e); out=[]; cur=None
    for r in rs:
        if r[0]=='on' and cur is None: cur=(r[1],who(r),r[5])
        elif r[0]=='off' and cur is not None: out.append((cur[0],r[1],cur[1],who(r),cur[2])); cur=None
    return out,rs
for e,nm in [('light.yeelink_color5_13b8_light','5F梯廳燈13b8'),('light.yeelink_color5_0fb7_light','4F樓梯燈0fb7')]:
    ss,_=sessions(e)
    print("== %s 開燈 %d 次；開燈來源/關燈來源統計"%(nm,len(ss)))
    cnt=collections.Counter((s[2],s[3]) for s in ss)
    for k,v in cnt.most_common(12): print("   %3d  開:%-26s 關:%s"%(v,k[0],k[1]))
    manual_auto=[s for s in ss if not s[2].startswith('A:08-5C') and s[3].startswith('A:08-5C')]
    print("   非08-5C開、卻被08-5C關：%d 次"%len(manual_auto))
    for s in manual_auto[:8]: print("     ",L(s[0]),'開',s[2],'→',L(s[1]),'關 (%.0fs)'%(s[1]-s[0]))
ss,_=sessions('switch.shu_fang_deng')
print("== 書房燈 開 %d 次"%len(ss))
cnt=collections.Counter((s[2],s[3]) for s in ss)
for k,v in cnt.most_common(12): print("   %3d  開:%-26s 關:%s"%(v,k[0],k[1]))
longs=[s for s in ss if s[1]-s[0]>=1800]
print("   亮超過30分鐘 %d 次："%len(longs))
for s in longs:
    lastm=max([t for t in pir['left']+pir['right'] if s[0]<=t<=s[1]] or [s[0]])
    print("     %s 開(%s) → %s 關(%s)  亮 %.0f 分；最後一次PIR動作到關燈 %.0f 分"%(L(s[0]),s[2],L(s[1]),s[3],(s[1]-s[0])/60,(s[1]-lastm)/60))
# 坎燈 brightness
_,rs=sessions('light.ding_lou_kan_deng')
print("== 坎燈 開燈事件（亮度%%、來源、時間）— 22:00~09:00")
nb=collections.Counter()
for r in rs:
    if r[0]!='on': continue
    h=dt.datetime.fromtimestamp(r[1]).hour
    if not (h>=22 or h<9): continue
    try: b=json.loads(r[5] or '{}').get('brightness')
    except: b=None
    nb[(who(r),round((b or 0)/2.55))]+=1
for k,v in sorted(nb.items(),key=lambda x:-x[1])[:15]: print("   %3d  %s  亮度%s%%"%(v,k[0],k[1]))
# 08-5F decisions
dec=collections.Counter(r[0][:40] for r in rows('input_text.topfloor_debug_last_decision'))
print("== 08-5F 決策紀錄"); [print("   %3d %s"%(v,k)) for k,v in dec.most_common(10)]
# others: camera visits when iPhone not on 5F AP
aps=['70:a7:41:e4:54:1f','70:a7:41:e4:5a:bf','d0:21:f9:f2:fc:4c']
ip=[]
for r in rows('device_tracker.iphone_17_pro_max_kenny'):
    try: ap=(json.loads(r[5] or '{}').get('ap_mac') or '').lower()
    except: ap=''
    ip.append((r[1],ap in aps,r[0]))
def at5(t):
    st=None
    for ts,f,s in ip:
        if ts<=t: st=(f,s)
        else: break
    return st
o=[v for v in longv if at5(v[0]) and not at5(v[0])[0]]
print("== 攝影機通行(≥4s)時你的 iPhone 不在 5F AP：%d / %d 段（可能是其他人或剛上樓 AP 未切換）"%(len(o),len(longv)))

import collections
alll=sorted([(t,k) for k in lines for t in lines[k]])
print("== 疑似雜訊跨線的時段分布（無攝影機/PIR ±10s）")
for k in lines:
    g=[t for t in lines[k] if not cam_near(t,10) and not near(pir['left'],t,10) and not near(pir['right'],t,10)]
    hc=collections.Counter(dt.datetime.fromtimestamp(t).hour for t in g)
    print("  ",k,' '.join('%02d:%d'%(h,hc[h]) for h in range(24) if hc[h]))
    # nearest camera event distance for ghosts
    ds=[]
    for t in g:
        d=min([abs(v[0]-t) for v in mv]+[abs(v[1]-t) for v in mv]+[99999]); ds.append(d)
    ds.sort(); print("     最近攝影機事件距離(秒) 中位 %.0f, 25%% %.0f"%(ds[len(ds)//2], ds[len(ds)//4]) if ds else '')
# line to camera-on lag for non-ghost
lag=[]
for t in lines['stairs']:
    cands=[v[0]-t for v in mv if -30<=v[0]-t<=30]
    if cands: lag.append(min(cands,key=abs))
lag.sort(); print("== 樓梯線相對攝影機開始偵測的時間差(秒，負=攝影機先) 中位 %.1f, 10%% %.1f, 90%% %.1f, n=%d"%(lag[len(lag)//2],lag[len(lag)//10],lag[int(len(lag)*.9)],len(lag)) if lag else '')
# kan deng attrs sample
for r in rows('light.ding_lou_kan_deng')[-40:]:
    if r[0]=='on': print("坎燈on屬性樣本:",(r[5] or '')[:200]); break
# study false off: off by 08-5C auto-off then re-on within 120s
ss,_=sessions('switch.shu_fang_deng')
fo=[(a,b) for a,b in zip(ss,ss[1:]) if a[3].startswith('A:08-5C頂樓樓梯感應燈自動關閉') and b[0]-a[1]<=120]
print("== 書房燈被『樓梯自動關閉』關掉後 2 分鐘內又被打開：%d / %d 次"%(len(fo),sum(1 for s in ss if s[3].startswith('A:08-5C頂樓樓梯感應燈自動關閉'))))
for a,b in fo[:10]: print("    %s 關 → %s 又開(%s) 間隔 %.0fs"%(L(a[1]),L(b[0]),b[2],b[0]-a[1]))
# study short sessions (<60s)
sh=[s for s in ss if s[1]-s[0]<60]; print("== 書房燈亮不到 60 秒就關：%d 次"%len(sh))
# 08-5F webhook-up validity
dec=[(r[1],r[0]) for r in rows('input_text.topfloor_debug_last_decision')]
aps=['70:a7:41:e4:54:1f','70:a7:41:e4:5a:bf','d0:21:f9:f2:fc:4c']
ip=[]
for r in rows('device_tracker.iphone_17_pro_max_kenny'):
    try: ap=(json.loads(r[5] or '{}').get('ap_mac') or '').lower()
    except: ap=''
    ip.append((r[1],ap in aps))
def at5(t):
    st=None
    for ts,f in ip:
        if ts<=t: st=f
        else: break
    return st
wu=[t for t,d in dec if d.startswith('Webhook 上樓')]
bad=[t for t in wu if not any(at5(t+x) for x in (0,30,60,120,180))]
print("== 08-5F Webhook 上樓判定 %d 次，其中之後 3 分鐘內 iPhone 都沒連上 5F AP：%d 次"%(len(wu),len(bad)))
for t in bad[:8]: print("    ",L(t))
# stairs light night brightness of 08-5C turn on (13b8)
nbr=collections.Counter()
for r in rows('light.yeelink_color5_13b8_light'):
    if r[0]=='on' and (lambda h: h>=22 or h<7)(dt.datetime.fromtimestamp(r[1]).hour):
        try: b=json.loads(r[5] or '{}').get('brightness')
        except: b=None
        nbr[(who(r)[:20],round((b or 0)/2.55))]+=1
print("== 夜間(22~07) 5F梯廳燈開啟亮度:",nbr.most_common(6))

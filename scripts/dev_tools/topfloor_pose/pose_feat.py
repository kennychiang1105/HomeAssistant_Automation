import json, sys, datetime as dt, numpy as np
obs = json.load(open(r'C:\ai_lab\topfloor\obs_pose.json'))
cm = {m['clip']: m for m in json.load(open(r'C:\ai_lab\topfloor\clips\clipmap.json', encoding='utf-8-sig'))}
# 標籤：08-5J 動線事件（上樓／下樓）＋使用者確認的 10/29 00:24 下樓
ev = json.load(open(r'C:\ai_lab\topfloor\events.json'))


def main_person(ps):
    best, bs = None, 0
    for p in ps:
        b = p['box']
        a = max(0, (b[2] - b[0]) * (b[3] - b[1])) * p['conf']
        if a > bs:
            best, bs = p, a
    return best


def feats(rows):
    fr = []
    for t, ps in rows:
        p = main_person(ps)
        if not p or p['conf'] < 0.4:
            continue
        k = p['kp']
        face = (k[0][2] > 0.5) + (k[1][2] > 0.5) + (k[2][2] > 0.5)           # 鼻子＋雙眼可見數
        sh_vis = k[5][2] > 0.4 and k[6][2] > 0.4
        # 面向鏡頭時，人的左肩（索引 5）在畫面右側（x 較大）
        orient = (k[5][0] - k[6][0]) if sh_vis else 0.0
        ank = (k[15][2] > 0.4) + (k[16][2] > 0.4)
        b = p['box']
        fr.append({'t': t, 'cx': (b[0] + b[2]) / 2, 'bot': b[3], 'h': b[3] - b[1], 'face': face, 'orient': orient, 'ank': ank, 'conf': p['conf']})
    return fr


out = []
for c, rows in sorted(obs.items()):
    fr = feats(rows)
    s = dt.datetime.strptime(cm[c]['start'], '%Y-%m-%d %H:%M:%S').timestamp()
    e = s + cm[c]['dur']
    truth = None
    for t, p in ev:
        if s - 1 <= t <= e + 1 and p == 'arrive_up':
            truth = 'up'
        if s - 1 <= t <= e + 1 and p in ('leave_study_down', 'down_start', 'down'):
            truth = truth or 'down'
    if len(fr) < 3:
        out.append((c, cm[c]['start'][5:], truth, len(fr), None))
        continue
    face_frac = np.mean([f['face'] >= 2 for f in fr])
    dx = fr[-1]['cx'] - fr[0]['cx']
    dh = fr[-1]['h'] - fr[0]['h']
    ank_frac = np.mean([f['ank'] >= 1 for f in fr])
    first = fr[0]
    out.append((c, cm[c]['start'][5:], truth, len(fr), dict(face=round(face_frac, 2), dx=round(dx, 2), dh=round(dh, 2), ank=round(ank_frac, 2),
                                                          f_bot=round(first['bot'], 2), f_h=round(first['h'], 2), l_cx=round(fr[-1]['cx'], 2))))
for o in out:
    print(o)

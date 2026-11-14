#!/usr/bin/env python3
"""車尾左方向燈偵測（V4.3.0-beta 4）：看 3 秒短片，車尾左後角（車頭朝鐵門時＝畫面上車身的左側）的橘色像素比例隨時間一亮一滅＝打左方向燈。
用法：garage_turn_signal.py --clip /config/www/snap/x.mp4 --slot front [--vision http://local-garage-vision:8099] [--side left]
輸出 JSON：{blink, flashes, peak, floor, series, box, side, people}。--selftest 用合成序列驗證。只讀影片，不碰 HA。
V4.3.16（2026-11-07）：查車身框的同一次 add-on 呼叫順便數畫面上「車外的人」（people，信心 ≥ PERSON_MIN；偵測到閃爍時再補看最後一幀，取較多者；add-on 連不上＝-1），
  給 HA 判斷「人還沒全部上車」先不開鐵門。"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import numpy as np
from PIL import Image

ROI = '/config/garage_roi.json'
FPS = 10
# 左後角區域（相對車身偵測框）：x 0～22%、y 18～56%
# 真實影片校正（2026-10-27 Luxgen 左方向燈在尾燈長條最左端，約車身框左 4%、高度 31%）
REGION = {'left': (0.0, 0.10, 0.24, 0.40), 'right': (0.90, 1.0, 0.24, 0.40)}
# 「車外有人在走動」的信心門檻：11-07 14:33～14:34 實測，走動的人 0.84～0.93；坐在車內（隔著車窗）0.27～0.45；牆角靜物 0.25～0.33
PERSON_MIN = 0.60
VEHICLE_CLS = ('car', 'truck', 'bus', 'motorcycle')


def in_car(pb, vb):
    """人框是不是「坐在車裡」：85% 以上落在車身框內、頭在車頂以下、框底在車底以上（腳沒踩在地上）。
    後位的車離鏡頭近，隔著車窗看到的駕駛信心可到 0.68～0.79（11-02 07:42）；站在車旁／後車廂的人頭會高過車頂或框底到地面，不會被排除
    （11-07 05:37 搬後車廂、11-04 07:48 站在副駕門邊、11-07 14:34 走向副駕都保留）。"""
    ix = max(0.0, min(pb[2], vb[2]) - max(pb[0], vb[0]))
    iy = max(0.0, min(pb[3], vb[3]) - max(pb[1], vb[1]))
    pa = max(1e-6, (pb[2] - pb[0]) * (pb[3] - pb[1]))
    vh = vb[3] - vb[1]
    return (ix * iy / pa) >= 0.85 and pb[1] >= vb[1] + 0.03 * vh and pb[3] <= vb[3] - 0.08 * vh


def outside_people(persons, vboxes):
    """車外的人：信心 ≥ PERSON_MIN、而且不是坐在任何一輛車裡。"""
    return [p for p in persons if p.get('conf', 0) >= PERSON_MIN and p.get('box') and not any(in_car(p['box'], v) for v in vboxes)]


def amber_frac(rgb):
    """橘黃色（色相約 15～50°、飽和度高、亮）像素比例；煞車燈的純紅（色相 <15°）不算。"""
    hsv = np.asarray(Image.fromarray(rgb).convert('HSV'), dtype=np.float32)
    h = hsv[..., 0] * 360.0 / 255.0
    s, v = hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    m = (h >= 15) & (h <= 50) & (s >= 0.45) & (v >= 0.60)
    return float(m.mean())


def _decide_window(a, min_swing, min_flashes, max_run):
    base = {'blink': False, 'flashes': 0, 'peak': 0.0, 'floor': 0.0}
    if len(a) < 12:
        return base
    hi, lo = float(np.percentile(a, 92)), float(np.percentile(a, 8))
    base.update({'peak': round(hi, 4), 'floor': round(lo, 4)})
    if hi - lo < min_swing or hi < 1.3 * lo + min_swing / 2:
        return base
    on = a > (hi + lo) / 2
    runs, cur, n = [], on[0], 0
    for v in on:
        if v == cur:
            n += 1
        else:
            runs.append((bool(cur), n))
            cur, n = v, 1
    runs.append((bool(cur), n))
    flashes = sum(1 for st, ln in runs if st and 2 <= ln <= max_run)       # 頭尾被剪斷的亮區段只要 ≥2 幀也算
    too_long = any(ln > max_run for st, ln in runs[1:-1])
    # 規律性：相鄰亮起的間隔要接近（真實 ≈ 9 幀），車子移動造成的不規則起伏不算
    pos, k = [], 0
    for st, ln in runs:
        if st:
            pos.append(k)
        k += ln
    gaps = [b - a_ for a_, b in zip(pos, pos[1:])]
    regular = bool(gaps) and 5 <= min(gaps) and max(gaps) <= 20 and max(gaps) <= 1.6 * min(gaps)
    base.update({'flashes': flashes, 'blink': bool(flashes >= min_flashes and regular and not too_long)})
    return base


def decide(series, min_swing=0.005, min_flashes=2, max_run=8, win=30, step=5):
    """series：每幀橘色比例（10fps）。方向燈＝約 1Hz 短促亮暗交替（真實影片：亮約 0.5 秒、暗約 0.4 秒）：3 秒視窗內亮的區段 ≥min_flashes 次，且每段亮／暗都不超過 max_run 幀（0.8 秒）。
    車子移動、陽光反光造成的橘色是「慢慢升高再降低」的長區段，不算。影片比 3 秒長時用滑動視窗，任一視窗成立即可。"""
    a = np.asarray(series, dtype=np.float32)
    if len(a) <= win + step:
        return _decide_window(a, min_swing, min_flashes, max_run)
    best = _decide_window(a[:win], min_swing, min_flashes, max_run)
    for s0 in range(step, len(a) - win + 1, step):
        r = _decide_window(a[s0:s0 + win], min_swing, min_flashes, max_run)
        if r['blink'] and not best['blink'] or (r['blink'] == best['blink'] and r['flashes'] > best['flashes']):
            best = r
    return best


def decide_both(sl, sr):
    """左方向燈、右方向燈、雙黃燈（危險警示燈，左右同時閃）任一成立即出門訊號（V4.3.10）。
    雙黃燈左右同步閃，兩側互相佐證，所以門檻放寬（振幅 0.003、閃 2 次）；單邊維持 0.005。"""
    rl, rr = decide(sl), decide(sr)
    hl = decide(sl, min_swing=0.003)
    hr = decide(sr, min_swing=0.003)
    if hl['blink'] and hr['blink']:
        out, kind = (rl if rl['flashes'] >= rr['flashes'] else rr), 'hazard'
        out = dict(out, blink=True)
    elif rl['blink'] or rr['blink']:
        out, kind = (rl, 'left') if rl['blink'] else (rr, 'right')
    else:
        out, kind = (rl if rl['peak'] >= rr['peak'] else rr), ''
    out = dict(out)
    out['kind'] = kind
    out['peak_left'], out['peak_right'] = rl['peak'], rr['peak']
    return out


def vision_query(url, jpg, roi, slot):
    """車身框＋畫面上的人＋所有車輛框（同一次 add-on 呼叫）。回傳 (box 或 None, persons 清單, 車輛框清單)。"""
    q = 'slots=' + ';'.join('%s=%s' % (n, ','.join(str(x) for x in s['body'])) for n, s in roi['slots'].items()) + '&plate=0'
    req = urllib.request.Request(url.rstrip('/') + '/analyze?' + q, data=jpg, method='POST', headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read().decode())
    d = ((res.get('slots') or {}).get(slot) or {}).get('det')
    vboxes = [s['det']['box'] for s in (res.get('slots') or {}).values() if s.get('det') and s['det'].get('box')]
    vboxes += [x['box'] for x in (res.get('dets') or []) if x.get('cls') in VEHICLE_CLS and x.get('conf', 0) >= 0.3 and x.get('box')]
    return (d['box'] if d else None), (res.get('persons') or []), vboxes


def vision_box(url, jpg, roi, slot):
    return vision_query(url, jpg, roi, slot)[0]


def vision_people(url, jpg):
    """只跑人物偵測（較快），回傳 persons 清單。"""
    req = urllib.request.Request(url.rstrip('/') + '/analyze?slots=front=0,0,1,1&plate=0&persons_only=1', data=jpg, method='POST',
                                 headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode()).get('persons') or []


def analyse_clip(clip, slot, side, vision, box_override=None):
    roi = json.load(open(ROI, encoding='utf-8'))
    tmp = tempfile.mkdtemp(prefix='turn_')
    try:
        r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-nostdin', '-i', clip, '-vf', 'fps=%d,scale=1344:-1' % FPS, '-q:v', '3', tmp + '/%04d.jpg'],
                           capture_output=True, text=True, timeout=60)
        frames = sorted(glob.glob(tmp + '/*.jpg'))
        if r.returncode != 0 or len(frames) < 8:
            return {'error': 'ffmpeg: %s frames=%d %s' % (r.returncode, len(frames), r.stderr[:100])}
        box = box_override
        people = None                      # None＝無法判斷（沒有 add-on 或連不上）
        vboxes = []
        if vision:
            try:
                vb, ps, vboxes = vision_query(vision, open(frames[len(frames) // 2], 'rb').read(), roi, slot)
                box = box or vb
                people = outside_people(ps, vboxes)
            except Exception:  # noqa: BLE001
                pass
        if not box:
            box = roi['slots'][slot]['body']
        bw, bh = box[2] - box[0], box[3] - box[1]
        sides = ['left', 'right'] if side == 'both' else [side]
        ser = {s: [] for s in sides}
        for f in frames:
            im = Image.open(f).convert('RGB')
            W, H = im.size
            for s in sides:
                x0, x1, y0, y1 = REGION[s]
                c = im.crop((int((box[0] + bw * x0) * W), int((box[1] + bh * y0) * H), int((box[0] + bw * x1) * W), int((box[1] + bh * y1) * H)))
                ser[s].append(round(amber_frac(np.asarray(c)), 4))
        if side == 'both':
            out = decide_both(ser['left'], ser['right'])
            out['series'] = ser['left']
            out['series_right'] = ser['right']
        else:
            out = decide(ser[side])
            out['kind'] = side if out['blink'] else ''
            out['series'] = ser[side]
        # 偵測到閃爍才補看最後一幀（最接近現在），兩幀取人數多的
        if vision and out.get('blink') and people is not None:
            try:
                last = outside_people(vision_people(vision, open(frames[-1], 'rb').read()), vboxes)
                if len(last) > len(people):
                    people = last
            except Exception:  # noqa: BLE001
                pass
        out.update({'side': side, 'slot': slot, 'box': [round(v, 3) for v in box],
                    'people': len(people) if people is not None else -1,
                    'people_conf': [round(p.get('conf', 0), 2) for p in (people or [])]})
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def analyse_snap(snap, slot, vision):
    """單張快照檢查車外人數（V4.4.6：方向燈暫緩開門後，定時確認人是否已上車）。"""
    roi = json.load(open(ROI, encoding='utf-8'))
    with open(snap, 'rb') as f:
        jpg = f.read()
    if not vision:
        return {'slot': slot, 'box': None, 'people': -1, 'people_conf': [], 'error': 'vision url required'}
    try:
        box, ps, vboxes = vision_query(vision, jpg, roi, slot)
    except Exception as e:  # noqa: BLE001
        return {'slot': slot, 'box': None, 'people': -1, 'people_conf': [], 'error': str(e)[:120]}
    people = outside_people(ps, vboxes)
    return {
        'slot': slot,
        'box': [round(v, 3) for v in box] if box else None,
        'people': len(people),
        'people_conf': [round(p.get('conf', 0), 2) for p in people],
    }


def selftest():
    err = []
    steady = [0.001] * 30
    if decide(steady)['blink']:
        err.append('常亮／無燈被判成閃爍')
    blink = ([0.03] * 3 + [0.001] * 4) * 5            # 約 1.4Hz 閃爍（10fps）
    if not decide(blink)['blink']:
        err.append('閃爍沒被偵測 %s' % decide(blink))
    one = [0.001] * 12 + [0.03] * 5 + [0.001] * 13     # 只亮一次（反光／路過）
    if decide(one)['blink']:
        err.append('只亮一次被判成閃爍')
    bump = [0.0] * 20 + [round(0.05 * (1 - abs(i - 20) / 20), 4) for i in range(40)] + [0.0] * 20       # 車子移動：橘色慢慢升高再降低
    if decide(bump)['blink']:
        err.append('慢速起伏被判成閃爍')
    weak = ([0.004] * 3 + [0.0005] * 4) * 5            # 幅度太小
    if decide(weak)['blink']:
        err.append('微弱變化被判成閃爍')
    hz = ([0.012] * 4 + [0.0015] * 5) * 3               # 雙黃燈：左右同步、幅度較小
    r = decide_both(hz, hz)
    if not (r['blink'] and r['kind'] == 'hazard'):
        err.append('雙黃燈沒被偵測 %s' % r)
    r = decide_both(([0.03] * 3 + [0.001] * 4) * 5, [0.001] * 35)
    if not (r['blink'] and r['kind'] == 'left'):
        err.append('左方向燈 %s' % r)
    r = decide_both([0.001] * 35, ([0.03] * 3 + [0.001] * 4) * 5)
    if not (r['blink'] and r['kind'] == 'right'):
        err.append('右方向燈 %s' % r)
    r = decide_both([0.001] * 30, [0.001] * 30)
    if r['blink']:
        err.append('無燈被判成有')
    r = decide_both(one, one)
    if r['blink']:
        err.append('兩側各只亮一次被判成雙黃燈')
    two = [0.001] * 4 + ([0.03] * 3 + [0.001] * 5) * 2        # 2 秒短片（20 幀）：閃兩次
    if not decide(two)['blink']:
        err.append('2 秒短片閃兩次沒偵測 %s' % decide(two))
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    img[:10, :10] = (255, 170, 30)                     # 橘
    img[10:, :10] = (230, 20, 20)                      # 紅（煞車燈）
    f = amber_frac(img)
    if not 0.2 < f < 0.3:
        err.append('橘色比例不對 %s（紅色不該算）' % f)
    # 車內／車外的人（真實畫面的框，11-02、11-04、11-07）
    lux, tes_b, tes_near = [0.48, 0.0, 0.96, 0.81], [0.0, 0.5, 0.6, 0.99], [0.0, 0.27, 0.83, 0.99]
    for pb, vb, want, name in [([0.0, 0.48, 0.18, 0.78], tes_near, True, '11-02 後位駕駛（隔車窗）'),
                               ([0.13, 0.35, 0.31, 0.68], [0.0, 0.19, 0.84, 0.99], True, '11-02 後位駕駛 2'),
                               ([0.48, 0.09, 0.68, 0.86], lux, False, '11-07 05:37 搬後車廂'),
                               ([0.87, 0.18, 1.0, 0.78], [0.34, 0.18, 0.91, 0.94], False, '11-04 站在副駕門邊'),
                               ([0.27, 0.08, 0.40, 0.62], tes_b, False, '11-07 14:34 走向副駕'),
                               ([0.60, 0.17, 0.66, 0.49], tes_near, False, '11-02 站在櫃子前')]:
        if in_car(pb, vb) != want:
            err.append('in_car 判斷錯：%s' % name)
    ps = [{'conf': 0.9, 'box': [0.0, 0.48, 0.18, 0.78]}, {'conf': 0.88, 'box': [0.48, 0.09, 0.68, 0.86]}, {'conf': 0.4, 'box': [0.1, 0.28, 0.14, 0.52]}]
    if len(outside_people(ps, [tes_near, lux])) != 1:
        err.append('outside_people 應只剩搬後車廂的人 %s' % outside_people(ps, [tes_near, lux]))
    print(json.dumps({'selftest': 'PASS' if not err else 'FAIL', 'errors': err}, ensure_ascii=False))
    return 0 if not err else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clip')
    ap.add_argument('--snap', help='單張快照檢查車外人數（配合 --vision）')
    ap.add_argument('--slot', default='front')
    ap.add_argument('--side', default='both', choices=['left', 'right', 'both'])
    ap.add_argument('--vision')
    ap.add_argument('--box', help='除錯：直接指定車身框 x0,y0,x1,y1（比例）')
    ap.add_argument('--delete', action='store_true', help='分析完刪掉短片或快照')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.clip or a.snap):
        ap.error('--clip or --snap required')
    try:
        if a.snap:
            print(json.dumps(analyse_snap(a.snap, a.slot, a.vision), ensure_ascii=False))
        else:
            print(json.dumps(analyse_clip(a.clip, a.slot, a.side, a.vision, [float(v) for v in a.box.split(',')] if a.box else None), ensure_ascii=False))
    finally:
        if a.delete:
            target = a.snap or a.clip
            if target:
                try:
                    os.remove(target)
                except OSError:
                    pass


if __name__ == '__main__':
    main()

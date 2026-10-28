#!/usr/bin/env python3
"""頂樓攝影機逐秒人物軌跡分析（V4.3.4-beta 3）

流程：動靜期間每秒一張快照 → Garage Vision add-on（persons_only=1，只跑 YOLO 人物偵測）→ 這支腳本累積軌跡並「提早決定」方向。
  上樓（up）：人在樓梯口往走道（畫面右側）離開；下樓（down）：人往畫面左下的樓梯口走進去；
  pass：只在走道經過；none：有動靜但連續幾幀都沒有人（降雜訊）；unknown：看不出來。
每個方向在一次動靜中只決定一次（fire），之後只輸出狀態。區域與門檻預設值寫在 DEFAULT_CFG，可由 /config/topfloor_ai/topfloor_roi.json 覆蓋（回放學習後調整）。

用法（在 HA 容器內執行，路徑是容器路徑）：
  python3 topfloor_track.py --frame /config/www/snap/tf_cur.jpg --vision http://local-garage-vision:8099      # 增量處理一幀，輸出 JSON
  python3 topfloor_track.py --finalize                                                                      # 動靜結束：輸出最後分類並清掉軌跡
  python3 topfloor_track.py --replay-clip clip.mp4 [--fps 1]                                                # 回放錄影（和上線同一套邏輯）
  python3 topfloor_track.py --selftest
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

DEFAULT_CFG = {
    'fire_dirs': ['up'],       # 哪些方向可以「提早決定」並發事件。下樓（down）先不發：回放 25 段沒有上下樓標籤的走道錄影，down 誤報 9 段（走道上走向鏡頭也會符合），
                               # 召回又只有 2/9，等累積更多標籤與規則調準再開；down 仍會輸出在 dir／最後分類供記錄
    'min_conf': 0.35,          # 人物偵測最低信心
    'idle_reset_s': 15,        # 超過這麼久沒有新幀，軌跡歸零
    'none_frames': 4,          # 連續幾幀都沒人 → none
    'up_x': 0.68,              # 上樓：目前位置要在畫面右側（走道）
    'up_dx': 0.08,             # 上樓：比第一次看到的位置再往右至少這麼多
    'up_start_max': 0.66,      # 上樓：第一次看到的位置要在這個 x 以左（從樓梯口側出現）
    'up_min_det': 2,
    'down_x': 0.50,            # 下樓：目前位置要在畫面左側（樓梯口）
    'down_dx': 0.20,           # 下樓：比軌跡最右邊再往左至少這麼多
    'down_min_det': 2,
    'pass_min_det': 4,         # 結束時偵測幀數 ≥ 這個且位移小 → pass
    'pass_max_dx': 0.15,
    'emerge_y': 0.97,          # 上樓（爬上來）：第一次看到時腳在畫面外（框底貼著畫面底邊）
    'emerge_h': 0.40,          #   且只露出頭肩（框高小於這個）
    'emerge_dh': 0.15,         #   之後框高要增加至少這麼多
    'far_y': 0.92,             # 下樓（走向樓梯）：第一次看到時腳還在畫面內（距離遠）
    'approach_dy': 0.06,       #   之後腳底 y 增加至少這麼多（走近鏡頭）
    'approach_dh': 0.12,       #   且框高增加至少這麼多
    'stair_x': 0.45,           # 軌跡結束在樓梯口區（x 小於這個、腳底接近畫面底）→ 傾向下樓
    'stair_bottom': 0.90,
    # ── 最後去向（人消失在畫面哪裡）：往左下樓梯口（x≈0.35、腳底貼底）消失＝下樓；在右側房門口區（x≥0.60）消失＝進房，
    #    書房與臥室門的位置差不多，所以用走動方向分辨（往右走到門口＝臥室，從右邊緣往左走到門口＝書房）。區域與門檻可用 topfloor_roi.json 覆蓋
    'exit_gap_s': 2.5,         # 人消失超過這麼久（秒）才判斷去向
    'exit_min_det': 2,         # 這一段至少要偵測到幾幀
    'exit_stairs_x': 0.45,     # 最後位置 x 小於這個、腳底 y 不小於 exit_stairs_y → 樓梯口（下樓）
    'exit_stairs_y': 0.90,
    'exit_edge_x': 0.86,       # 最後位置 x 不小於這個 → 右邊緣（臥室側）
    'exit_door_x': 0.60,       # 最後位置 x 不小於這個 → 在房門口區消失（書房／臥室）；再用走動方向分辨
    'exit_dx': 0.05,           # 房門口區消失時，位移（最後 x － 第一次 x）≥ +這個＝臥室、≤ －這個＝書房
}


def load_cfg(workdir):
    cfg = dict(DEFAULT_CFG)
    p = os.path.join(workdir, 'topfloor_roi.json')
    if os.path.exists(p):
        try:
            cfg.update(json.load(open(p, encoding='utf-8')))
        except Exception:  # noqa: BLE001
            pass
    return cfg


def main_person(persons, cfg):
    """多人時取最大的那個（離攝影機最近、信心高）"""
    best, bs = None, 0.0
    for p in persons or []:
        if p.get('conf', 0) < cfg['min_conf']:
            continue
        b = p['box']
        area = max(0.0, (b[2] - b[0]) * (b[3] - b[1]))
        s = area * p['conf']
        if s > bs:
            best, bs = p, s
    if best is None:
        return None
    b = best['box']
    return {'x': round((b[0] + b[2]) / 2, 3), 'y': round(b[3], 3), 'h': round(b[3] - b[1], 3), 'conf': best['conf']}


def decide(frames, cfg):
    """frames: [{'t', 'p': None|{x,y,h,conf}}]。回傳 {'dir', 'conf', 'reason'}；dir 為 up / down / none / unknown（pass 只在 final 判）"""
    det = [f['p'] for f in frames if f['p']]
    if not det:
        if len(frames) >= cfg['none_frames']:
            return {'dir': 'none', 'conf': 0.8, 'reason': '連續 %d 幀都沒人' % len(frames)}
        return {'dir': 'unknown', 'conf': 0.0, 'reason': '還沒看到人'}
    xs = [p['x'] for p in det]
    cur, mn, mx = xs[-1], min(xs), max(xs)
    first, last = det[0], det[-1]
    # 上樓（從樓梯爬上來）：第一次看到時只有頭肩從畫面底邊冒出來（腳在畫面外：y 貼底、框很矮），之後越來越高；或從樓梯口側往右走出去
    emerge = len(det) >= 2 and first['y'] >= cfg['emerge_y'] and first['h'] <= cfg['emerge_h'] and (last['h'] - first['h']) >= cfg['emerge_dh']
    walk_right = len(det) >= cfg['up_min_det'] and cur >= cfg['up_x'] and (cur - xs[0]) >= cfg['up_dx'] and xs[0] <= cfg['up_start_max']
    up = emerge or walk_right
    # 下樓：①從遠處（腳還看得到、y 不貼底）走向鏡頭／樓梯口（y 變大、框變高）；②往左進入樓梯口並逐漸沉下去
    approach = len(det) >= 2 and first['y'] <= cfg['far_y'] and (last['y'] - first['y']) >= cfg['approach_dy'] and (last['h'] - first['h']) >= cfg['approach_dh']
    to_stairs = len(det) >= cfg['down_min_det'] and cur <= cfg['down_x'] and (mx - cur) >= cfg['down_dx']
    dn = approach or to_stairs
    if emerge:
        dn = False      # 頭肩從畫面底邊冒出來＝爬樓梯上來，優先於其他下樓規則
    if up and dn:
        up_m, dn_m = cur - xs[0], mx - cur
        up, dn = up_m >= dn_m, dn_m > up_m
    if up:
        return {'dir': 'up', 'conf': round(min(1.0, 0.6 + (cur - xs[0])), 2), 'reason': '往右離開樓梯口 x %.2f→%.2f' % (xs[0], cur)}
    if dn:
        return {'dir': 'down', 'conf': round(min(1.0, 0.6 + (mx - cur) / 2), 2), 'reason': '往左進入樓梯口 x %.2f→%.2f' % (mx, cur)}
    return {'dir': 'unknown', 'conf': 0.0, 'reason': '方向還不明確（x %.2f，範圍 %.2f～%.2f）' % (cur, mn, mx)}


def final_class(frames, cfg, decided):
    """動靜結束後的最終分類"""
    det = [f['p'] for f in frames if f['p']]
    if decided:
        return {'dir': decided, 'conf': 0.9, 'reason': '提早決定'}
    if not det:
        return {'dir': 'none', 'conf': 0.8, 'reason': '整段動靜都沒有人'}
    xs = [p['x'] for p in det]
    last = det[-1]
    if len(det) >= cfg['pass_min_det'] and (max(xs) - min(xs)) <= cfg['pass_max_dx']:
        return {'dir': 'pass', 'conf': 0.6, 'reason': '在走道停留／經過，位移很小'}
    if last['x'] <= cfg['stair_x'] and last['y'] >= cfg['stair_bottom'] and xs[0] > last['x']:
        return {'dir': 'down', 'conf': 0.6, 'reason': '最後出現在樓梯口區'}
    if len(det) >= 2 and xs[-1] - xs[0] >= cfg['up_dx']:
        return {'dir': 'up', 'conf': 0.55, 'reason': '整體往右移動'}
    return {'dir': 'unknown', 'conf': 0.0, 'reason': '看不出方向（偵測 %d 幀）' % len(det)}


def exit_zone(seg, cfg):
    """seg: 這一段的偵測（[{'t','p'}]，時間順序）。回傳 {'zone','dest','origin','reason'}；zone＝stairs／right_edge／door_mid／unknown"""
    first, last = seg[0]['p'], seg[-1]['p']
    dx = last['x'] - first['x']
    origin = 'stairs' if first['x'] <= cfg['exit_stairs_x'] else ('right_edge' if first['x'] >= cfg['exit_edge_x'] else 'door_mid')
    if last['x'] <= cfg['exit_stairs_x'] and last['y'] >= cfg['exit_stairs_y']:
        zone, dest = 'stairs', 'stairs'
    elif last['x'] >= cfg['exit_door_x']:
        # 書房門與臥室門在畫面裡都落在 x≈0.70～0.80（10/20～10/28 共 82 段錄影），位置分不出來，改看「從哪一側走過來」：
        # 從左側（樓梯側）往右走到門口消失＝臥室；從右邊緣往左走到門口消失＝書房；位移太小就不猜
        zone = 'right_edge' if last['x'] >= cfg['exit_edge_x'] else 'door_mid'
        dest = 'bedroom' if dx >= cfg['exit_dx'] else ('study' if dx <= -cfg['exit_dx'] else '')
    else:
        zone, dest = 'unknown', ''
    return {'zone': zone, 'dest': dest, 'origin': origin, 'dx': round(dx, 2), 'x': last['x'], 'y': last['y'], 'h': last['h'],
            'reason': '消失在 x %.2f y %.2f（起點 x %.2f，位移 %+.2f，共 %d 幀）→ %s' % (last['x'], last['y'], first['x'], dx, len(seg), dest or '看不出')}


class Tracker:
    def __init__(self, cfg, state=None):
        self.cfg = cfg
        s = state or {}
        self.frames = s.get('frames', [])
        self.fired = s.get('fired', [])
        self.t_last = s.get('t_last', 0)
        self.exit_mark = s.get('exit_mark', 0)      # 已經判過去向的最後一次偵測時間

    def dump(self):
        return {'frames': self.frames[-120:], 'fired': self.fired, 't_last': self.t_last, 'exit_mark': self.exit_mark}

    def exit_check(self, t, force=False):
        """人消失超過 exit_gap_s（force＝動靜結束時不等）就判斷最後去向；每一段只判一次"""
        det = [f for f in self.frames if f['p'] and f['t'] > self.exit_mark]
        if len(det) < self.cfg['exit_min_det']:
            return None
        if not force and t - det[-1]['t'] < self.cfg['exit_gap_s']:
            return None
        r = exit_zone(det, self.cfg)
        self.exit_mark = det[-1]['t']
        return r

    def add(self, t, persons):
        if self.t_last and t - self.t_last > self.cfg['idle_reset_s']:
            self.frames, self.fired, self.exit_mark = [], [], 0
        self.t_last = t
        p = main_person(persons, self.cfg)
        self.frames.append({'t': round(t, 2), 'p': p})
        n_all = len([x for x in (persons or []) if x.get('conf', 0) >= self.cfg['min_conf']])
        res = decide(self.frames, self.cfg)
        fire = ''
        # up / down 互斥：已經決定過其中一個就不再改口；none（沒人）只在 finalize 時判斷（動靜剛開始時人還沒走進畫面是正常的）
        if res['dir'] in self.cfg['fire_dirs'] and not ({'up', 'down'} & set(self.fired)):
            self.fired.append(res['dir'])
            fire = res['dir']
        out = {'persons': n_all, 'main': p, 'dir': res['dir'], 'conf': res['conf'], 'reason': res['reason'], 'fire': fire,
               'frames': len(self.frames), 'detected': len([f for f in self.frames if f['p']])}
        if p is None:
            ex = self.exit_check(t)
            if ex:
                out['exit'] = ex
        return out

    def finalize(self):
        decided = next((d for d in self.fired if d in ('up', 'down')), '')
        r = final_class(self.frames, self.cfg, decided)
        r['frames'] = len(self.frames)
        r['detected'] = len([f for f in self.frames if f['p']])
        r['already_fired'] = list(self.fired)
        ex = self.exit_check(self.t_last, force=True)       # 動靜結束時還沒判過去向的最後一段
        if ex:
            r['exit'] = ex
        return r


def vision_persons(url, jpg_path, timeout=20):
    data = open(jpg_path, 'rb').read()
    req = urllib.request.Request(url.rstrip('/') + '/analyze?slots=front=0,0,1,1&plate=0&persons_only=1', data=data,
                                 headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r).get('persons', [])


def cmd_frame(a):
    os.makedirs(a.dir, exist_ok=True)
    cfg = load_cfg(a.dir)
    sp = os.path.join(a.dir, 'track.json')
    state = {}
    if os.path.exists(sp) and not a.reset:
        try:
            state = json.load(open(sp, encoding='utf-8'))
        except Exception:  # noqa: BLE001
            state = {}
    t0 = time.time()
    try:
        persons = vision_persons(a.vision, a.frame)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({'error': str(e)[:120]}))
        return
    tr = Tracker(cfg, state)
    out = tr.add(a.t or time.time(), persons)
    json.dump(tr.dump(), open(sp, 'w', encoding='utf-8'))
    out['ms'] = int((time.time() - t0) * 1000)
    print(json.dumps(out, ensure_ascii=False))


def cmd_finalize(a):
    cfg = load_cfg(a.dir)
    sp = os.path.join(a.dir, 'track.json')
    state = json.load(open(sp, encoding='utf-8')) if os.path.exists(sp) else {}
    out = Tracker(cfg, state).finalize()
    json.dump({'frames': [], 'fired': [], 't_last': 0}, open(sp, 'w', encoding='utf-8'))
    print(json.dumps(out, ensure_ascii=False))


def replay_clip(clip, vision, cfg, fps=1.0, scale=640):
    d = tempfile.mkdtemp(prefix='tfr_')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', clip, '-vf', 'fps=%s,scale=%d:-1' % (fps, scale), os.path.join(d, 'f%04d.jpg')], check=True)
    tr = Tracker(cfg)
    rows = []
    for i, f in enumerate(sorted(glob.glob(os.path.join(d, '*.jpg')))):
        t = i / fps
        o = tr.add(t, vision_persons(vision, f))
        rows.append((round(t, 1), o['main'], o['dir'], o['fire']))
    fin = tr.finalize()
    for f in glob.glob(os.path.join(d, '*')):
        os.remove(f)
    os.rmdir(d)
    return rows, fin


def cmd_replay(a):
    cfg = load_cfg(a.dir)
    rows, fin = replay_clip(a.replay_clip, a.vision, cfg, a.fps)
    for r in rows:
        if r[1] or r[3]:
            print('%5.1fs' % r[0], r[1], r[2], ('FIRE ' + r[3]) if r[3] else '')
    print('FINAL', json.dumps(fin, ensure_ascii=False))


# 由 10/28 00:46（下樓）、00:49（上樓）兩段真實錄影，用 add-on 偵測出的人物框中心／腳底整理成的軌跡（每 0.5 秒一幀，None＝沒偵測到）
REAL_DOWN = [(0.73, 0.99), (0.705, 0.99), (0.675, 0.99), (0.69, 0.99), (0.695, 0.99), (0.75, 0.99), (0.785, 0.99), (0.78, 0.99),
             (0.705, 0.98), (0.615, 0.99), (0.475, 0.99), (0.405, 0.99), None, (0.32, 1.0), None, None, (0.335, 0.99), (0.34, 1.0)]
REAL_UP = [(0.615, 0.99), (0.70, 0.99), (0.755, 1.0), (0.745, 1.0), (0.73, 0.91)]


def _run_seq(seq, cfg, step=1):
    tr, fired = Tracker(cfg), []
    for i, p in enumerate(seq[::step]):
        h = p[2] if (p is not None and len(p) > 2) else 0.6
        persons = [] if p is None else [{'conf': 0.9, 'box': [p[0] - 0.1, p[1] - h, p[0] + 0.1, p[1]]}]
        o = tr.add(i * step * 0.5, persons)
        if o['fire']:
            fired.append((i * step * 0.5, o['fire']))
    return fired, tr.finalize()


def selftest():
    cfg = dict(DEFAULT_CFG)
    cfg['fire_dirs'] = ['up', 'down']      # 測試判斷規則本身；上線預設只發 up
    errors = []
    f, fin = _run_seq(REAL_DOWN, cfg)
    if not f or f[0][1] != 'down':
        errors.append('真實下樓軌跡沒有判成 down：%s %s' % (f, fin))
    f, fin = _run_seq(REAL_UP, cfg)
    if not f or f[0][1] != 'up':
        errors.append('真實上樓軌跡沒有判成 up：%s %s' % (f, fin))
    # 1 秒一幀（上線的實際節奏）也要判得出來
    f, _ = _run_seq(REAL_DOWN, cfg, step=2)
    if not f or f[0][1] != 'down':
        errors.append('1 秒一幀下樓判不出來：%s' % f)
    f, _ = _run_seq(REAL_UP, cfg, step=2)
    if not f or f[0][1] != 'up':
        errors.append('1 秒一幀上樓判不出來：%s' % f)
    # 爬樓梯上來：頭肩先從畫面底邊冒出來，框越來越高（10/23 00:44 錄影，x,腳底y,框高）
    f, fin = _run_seq([(0.64, 1.0, 0.21), (0.73, 0.99, 0.54), (0.70, 0.99, 0.78), (0.72, 0.87, 0.69)], cfg)
    if not f or f[0][1] != 'up':
        errors.append('爬樓梯上來沒判成 up：%s' % f)
    # 從房門走向樓梯（遠處走近）：10/23 22:07 錄影
    f, fin = _run_seq([(0.67, 0.78, 0.37), (0.69, 0.89, 0.70), (0.57, 0.99, 0.79), (0.69, 0.89, 0.73)], cfg)
    if not f or f[0][1] != 'down':
        errors.append('走向樓梯沒判成 down：%s' % f)
    # 最後去向：往右走到房門口消失＝臥室；從右邊緣往左走到房門口消失＝書房；往左下樓梯口消失＝下樓；位移太小不猜
    def exits(seq):
        tr, out = Tracker(cfg), []
        for i, p in enumerate(seq):
            h = 0.6
            persons = [] if p is None else [{'conf': 0.9, 'box': [p[0] - 0.1, p[1] - h, p[0] + 0.1, p[1]]}]
            o = tr.add(i * 0.5, persons)
            if o.get('exit'):
                out.append(o['exit']['dest'])
        return out, tr
    gone = [None] * 7
    for name, seq, want in (('往右走到門口', [(0.35, 0.99), (0.5, 0.99), (0.65, 0.99), (0.74, 0.99)], 'bedroom'),
                            ('從右邊緣往左走到門口', [(0.91, 0.99), (0.85, 0.99), (0.78, 0.99), (0.73, 0.99)], 'study'),
                            ('往左下樓梯口', [(0.8, 0.99), (0.6, 0.99), (0.42, 0.99), (0.35, 1.0)], 'stairs'),
                            ('原地不動', [(0.72, 0.99), (0.73, 0.99), (0.72, 0.99)], '')):
        got, _ = exits(seq + gone)
        if got != [want]:
            errors.append('去向 %s 應為 %r，實際 %r' % (name, want, got))
    got, _ = exits([(0.35, 0.99), (0.5, 0.99), (0.65, 0.99), (0.74, 0.99)] + [None] * 3)      # 消失還不到 2.5 秒：先不判
    if got:
        errors.append('消失不到 2.5 秒不該判去向：%r' % got)
    got, tr = exits([(0.35, 0.99), (0.5, 0.99), (0.65, 0.99), (0.74, 0.99)] + [None] * 3)
    if tr.finalize().get('exit', {}).get('dest') != 'bedroom':
        errors.append('動靜結束時要補判去向')
    # 沒人：只在 finalize 判
    f, fin = _run_seq([None] * 6, cfg)
    if f or fin['dir'] != 'none':
        errors.append('沒人沒判成 none：%s %s' % (f, fin))
    # 走道經過（位移小）
    f, fin = _run_seq([(0.55, 0.9), (0.56, 0.9), (0.55, 0.9), (0.57, 0.9), (0.56, 0.9)], cfg)
    if f or fin['dir'] != 'pass':
        errors.append('走道經過沒判成 pass：%s %s' % (f, fin))
    # 只看到一幀：不亂猜
    f, fin = _run_seq([(0.7, 0.9)], cfg)
    if f:
        errors.append('只有一幀不該提早決定：%s' % f)
    # 隔太久自動歸零
    tr = Tracker(cfg)
    tr.add(100, [{'conf': 0.9, 'box': [0.6, 0.3, 0.8, 0.99]}])
    tr.add(140, [])
    if len(tr.frames) != 1:
        errors.append('閒置後軌跡沒歸零：%d' % len(tr.frames))
    print(json.dumps({'selftest': 'PASS' if not errors else 'FAIL', 'errors': errors}, ensure_ascii=False))
    return 0 if not errors else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frame')
    ap.add_argument('--t', type=float)
    ap.add_argument('--vision', default='http://local-garage-vision:8099')
    ap.add_argument('--dir', default='/config/topfloor_ai')
    ap.add_argument('--reset', action='store_true')
    ap.add_argument('--finalize', action='store_true')
    ap.add_argument('--replay-clip')
    ap.add_argument('--fps', type=float, default=1.0)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.replay_clip:
        return cmd_replay(a)
    if a.finalize:
        return cmd_finalize(a)
    if a.frame:
        return cmd_frame(a)
    ap.print_help()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""車庫樓梯口人流記錄（V1.0.0，只記錄不控制）

流程：樓梯感應器或車庫攝影機有人時，每秒一張快照 → Garage Vision add-on（persons_only＋pose）→ 這支腳本把人物串成軌跡（多人各自追蹤），
軌跡結束時判斷每個人是「從樓梯口出來（down，下樓走進車庫）」「走進樓梯口（up，上樓）」「只經過（pass）」或「看不出（unknown）」，
寫到 /config/garage_stair/log.jsonl。樓梯口區域（畫面 x 範圍）預設值在 DEFAULT_CFG，可由 /config/garage_stair/roi.json 覆蓋。

用法（在 HA 容器內，路徑為容器路徑）：
  python3 garage_stair_track.py --frame /config/www/snap/gs_n0.jpg --t 1730000000 [--reset]     # 增量處理一幀，輸出 JSON
  python3 garage_stair_track.py --finalize                                                     # 動靜結束：結算所有軌跡並清掉
  python3 garage_stair_track.py --presence --frame /config/www/snap/gs_chk.jpg                  # 關燈前確認：這張快照裡有沒有人（輸出 persons 數）
  python3 garage_stair_track.py --selftest
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sys
import time
import urllib.request

DIR = '/config/garage_stair'
COLLECT_DIR = '/config/learn_collect/garage_stair'
COLLECT_KEEP_DAYS = 14

DEFAULT_CFG = {
    'roi_x0': 0.22,          # 樓梯口區域（畫面 x 比例）：10/31 樓梯口在車庫攝影機左側牆角，x 約 0.24～0.37
    'roi_x1': 0.38,
    'min_conf': 0.35,
    'match_d': 0.25,         # 同一人前後幀的最大距離（x、腳底 y 的城市距離）
    'lost_s': 3.0,           # 軌跡超過這麼久沒有新偵測就結算
    'idle_reset_s': 20.0,    # 整體超過這麼久沒有新幀，全部歸零
    'min_det': 3,            # 軌跡至少偵測到幾幀才判方向
    'move_dx': 0.08,         # 出入樓梯口至少要位移這麼多
}


def load_cfg(workdir=DIR):
    cfg = dict(DEFAULT_CFG)
    p = os.path.join(workdir, 'roi.json')
    if os.path.exists(p):
        try:
            cfg.update({k: v for k, v in json.load(open(p, encoding='utf-8')).items() if k in cfg})
        except Exception:  # noqa: BLE001
            pass
    return cfg


def pt_of(p):
    b = p['box']
    return {'x': round((b[0] + b[2]) / 2, 3), 'y': round(b[3], 3), 'h': round(b[3] - b[1], 3), 'c': round(p.get('conf', 0), 2)}


def in_roi(x, cfg):
    return cfg['roi_x0'] <= x <= cfg['roi_x1']


def classify(track, cfg):
    pts = track['pts']
    if len(pts) < cfg['min_det']:
        return {'dir': 'unknown', 'reason': '偵測不足 %d 幀' % len(pts)}
    x0, x1 = pts[0]['x'], pts[-1]['x']
    s_in, e_in = in_roi(x0, cfg), in_roi(x1, cfg)
    dx = x1 - x0
    h0, h1 = pts[0]['h'], pts[-1]['h']
    if s_in and not e_in and abs(dx) >= cfg['move_dx']:
        return {'dir': 'down', 'reason': '從樓梯口走出（x %.2f→%.2f，框高 %.2f→%.2f）' % (x0, x1, h0, h1)}
    if e_in and not s_in and abs(dx) >= cfg['move_dx']:
        return {'dir': 'up', 'reason': '走進樓梯口（x %.2f→%.2f，框高 %.2f→%.2f）' % (x0, x1, h0, h1)}
    if s_in and e_in:
        return {'dir': 'dwell', 'reason': '一直在樓梯口區（x %.2f→%.2f）' % (x0, x1)}
    return {'dir': 'pass', 'reason': '只在車庫經過（x %.2f→%.2f）' % (x0, x1)}


class Tracker:
    def __init__(self, cfg, state=None):
        self.cfg = cfg
        s = state or {}
        self.tracks = s.get('tracks', [])
        self.next_id = s.get('next_id', 1)
        self.t_last = s.get('t_last', 0)
        self.max_conc = s.get('max_conc', 0)
        self.done = []          # 這一次呼叫結算出的事件

    def dump(self):
        return {'tracks': self.tracks, 'next_id': self.next_id, 't_last': self.t_last, 'max_conc': self.max_conc}

    def _close(self, tr):
        r = classify(tr, self.cfg)
        r.update({'id': tr['id'], 't0': tr['pts'][0]['t'], 't1': tr['pts'][-1]['t'], 'det': len(tr['pts']),
                  'x0': tr['pts'][0]['x'], 'x1': tr['pts'][-1]['x']})
        self.done.append(r)

    def add(self, t, persons):
        cfg = self.cfg
        if self.t_last and t - self.t_last > cfg['idle_reset_s']:
            self.finalize()
            self.tracks, self.max_conc = [], 0
        self.t_last = t
        ps = [pt_of(p) for p in (persons or []) if p.get('conf', 0) >= cfg['min_conf']]
        used = set()
        # 大的（近的）人先配對
        for p in sorted(ps, key=lambda q: -q['h']):
            best, bd = None, cfg['match_d']
            for tr in self.tracks:
                if tr['id'] in used or t - tr['pts'][-1]['t'] > cfg['lost_s']:
                    continue
                q = tr['pts'][-1]
                d = abs(p['x'] - q['x']) + abs(p['y'] - q['y'])
                if d < bd:
                    best, bd = tr, d
            p = dict(p, t=round(t, 2))
            if best is None:
                best = {'id': self.next_id, 'pts': []}
                self.next_id += 1
                self.tracks.append(best)
            best['pts'].append(p)
            used.add(best['id'])
        # 結算消失太久的軌跡
        keep = []
        for tr in self.tracks:
            if t - tr['pts'][-1]['t'] > cfg['lost_s']:
                self._close(tr)
            else:
                keep.append(tr)
        self.tracks = keep
        self.max_conc = max(self.max_conc, len(ps))
        return {'persons': len(ps), 'tracks': len(self.tracks), 'closed': self.done}

    def finalize(self):
        for tr in self.tracks:
            self._close(tr)
        self.tracks = []
        return {'closed': self.done, 'max_conc': self.max_conc}


def vision_persons(url, jpg_path, timeout=20):
    data = open(jpg_path, 'rb').read()
    req = urllib.request.Request(url.rstrip('/') + '/analyze?slots=front=0,0,1,1&plate=0&persons_only=1&pose=1', data=data,
                                 headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r).get('persons', [])


def log_events(events, max_conc):
    if not events:
        return
    os.makedirs(DIR, exist_ok=True)
    with open(os.path.join(DIR, 'log.jsonl'), 'a', encoding='utf-8') as f:
        for e in events:
            e = dict(e, ts=dt.datetime.fromtimestamp(e['t1']).strftime('%Y-%m-%d %H:%M:%S'), max_conc=max_conc)
            f.write(json.dumps(e, ensure_ascii=False) + '\n')


def collect_frame(src, t, persons, out):
    """學習資料收集：每張分析過的快照＋人物框，存到 /config/learn_collect/garage_stair/<日期>/，保留 14 天（之後驗證方向規則用）"""
    day = dt.datetime.fromtimestamp(t).strftime('%Y%m%d')
    d = os.path.join(COLLECT_DIR, day)
    new_day = not os.path.isdir(d)
    os.makedirs(d, exist_ok=True)
    stamp = dt.datetime.fromtimestamp(t).strftime('%H%M%S_%f')[:10]
    shutil.copyfile(src, os.path.join(d, stamp + '.jpg'))
    rec = {'t': round(t, 2), 'file': stamp + '.jpg', 'persons': [{'c': p.get('conf'), 'b': p.get('box')} for p in (persons or [])],
           'closed': [c['dir'] for c in out.get('closed', [])]}
    with open(os.path.join(d, 'index.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    if new_day:
        cut = (dt.datetime.fromtimestamp(t) - dt.timedelta(days=COLLECT_KEEP_DAYS)).strftime('%Y%m%d')
        for n in os.listdir(COLLECT_DIR):
            if n.isdigit() and n < cut:
                shutil.rmtree(os.path.join(COLLECT_DIR, n), ignore_errors=True)


def cmd_frame(a):
    os.makedirs(DIR, exist_ok=True)
    cfg = load_cfg()
    sp = os.path.join(DIR, 'track.json')
    state = {}
    if os.path.exists(sp) and not a.reset:
        try:
            state = json.load(open(sp, encoding='utf-8'))
        except Exception:  # noqa: BLE001
            state = {}
    t = a.t or time.time()
    t0 = time.time()
    try:
        persons = vision_persons(a.vision, a.frame)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({'error': str(e)[:120]}))
        return
    tr = Tracker(cfg, state)
    out = tr.add(t, persons)
    json.dump(tr.dump(), open(sp, 'w', encoding='utf-8'))
    log_events(out['closed'], tr.max_conc)
    out['ms'] = int((time.time() - t0) * 1000)
    try:
        collect_frame(a.frame, t, persons, out)
    except Exception:  # noqa: BLE001
        pass
    print(json.dumps(out, ensure_ascii=False))


def cmd_finalize(a):
    cfg = load_cfg()
    sp = os.path.join(DIR, 'track.json')
    state = json.load(open(sp, encoding='utf-8')) if os.path.exists(sp) else {}
    tr = Tracker(cfg, state)
    out = tr.finalize()
    json.dump({'tracks': [], 'next_id': tr.next_id, 't_last': 0, 'max_conc': 0}, open(sp, 'w', encoding='utf-8'))
    log_events(out['closed'], out['max_conc'])
    print(json.dumps(out, ensure_ascii=False))


def cmd_presence(a):
    cfg = load_cfg()
    try:
        persons = [p for p in vision_persons(a.vision, a.frame) if p.get('conf', 0) >= cfg['min_conf']]
    except Exception as e:  # noqa: BLE001
        print(json.dumps({'persons': -1, 'error': str(e)[:120]}))
        return
    print(json.dumps({'persons': len(persons), 'xs': [pt_of(p)['x'] for p in persons]}))


def selftest():
    cfg = dict(DEFAULT_CFG)

    def box(x, y, h=0.4):
        return {'conf': 0.9, 'box': [x - 0.04, y - h, x + 0.04, y]}

    def run(seq):
        tr = Tracker(cfg)
        t = 1000.0
        for ps in seq:
            tr.add(t, ps)
            t += 1
        tr.add(t + 5, [])              # 之後沒人，軌跡結算
        tr.finalize()
        return [d['dir'] for d in tr.done]

    # 從樓梯口出來往右走 → down
    assert run([[box(0.30, 0.9)], [box(0.36, 0.9)], [box(0.45, 0.92)], [box(0.55, 0.95)]]) == ['down']
    # 從右邊走進樓梯口 → up
    assert run([[box(0.60, 0.9)], [box(0.50, 0.9)], [box(0.40, 0.9)], [box(0.31, 0.88)]]) == ['up']
    # 只經過 → pass
    assert run([[box(0.6, 0.9)], [box(0.7, 0.9)], [box(0.8, 0.9)]]) == ['pass']
    # 一人出一人進，同時 → 各自一條
    seq = [[box(0.30, 0.9), box(0.70, 0.95)], [box(0.36, 0.9), box(0.55, 0.95)], [box(0.46, 0.9), box(0.42, 0.95)], [box(0.58, 0.9), box(0.32, 0.95)]]
    assert sorted(run(seq)) == ['down', 'up'], run(seq)
    # 偵測太少 → unknown
    assert run([[box(0.3, 0.9)], [box(0.4, 0.9)]]) == ['unknown']
    print('selftest PASS')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frame')
    ap.add_argument('--t', type=float, default=0)
    ap.add_argument('--reset', action='store_true')
    ap.add_argument('--finalize', action='store_true')
    ap.add_argument('--presence', action='store_true')
    ap.add_argument('--vision', default='http://local-garage-vision:8099')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.presence and a.frame:
        cmd_presence(a)
    elif a.finalize:
        cmd_finalize(a)
    elif a.frame:
        cmd_frame(a)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

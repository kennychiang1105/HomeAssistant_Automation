#!/usr/bin/env python3
"""車庫車輛畫面分析（V4.2.5）

讀一張車庫快照，依 garage_roi.json 的「車位」區域算出每個車位：
  occupied   車位有沒有車（與「空車位基準」比對；沒學過空車位基準時為 null）
  identity   是哪輛車（與已學的樣板比對；學不到或不確定為 unknown）
  lights_on  車燈區域比滾動基準明顯變亮（以牆面參考區正規化，排除紅外線/開燈造成的整體亮度變化）
  moved      車身相對於滾動基準位移超過門檻（FFT 相位相關）
只用 Pillow + numpy（HA 容器內沒有 cv2）。不呼叫 HA、不發任何通知；結果以 JSON 印出。

用法（HA 容器內）：
  garage_car_watch.py --snapshot /config/www/snap/garage_cur.jpg            # 分析一張並更新滾動基準
  garage_car_watch.py --snapshot X --learn-empty front                      # 把這張當作「前位是空的」基準
  garage_car_watch.py --snapshot X --learn-sig front=luxgen_n7              # 把這張的前位當作 Luxgen 樣板（車頭朝鐵門）
  garage_car_watch.py --snapshot X --learn-sig front=luxgen_n7:inside       # 同一輛車但車頭朝內（倒車入庫）的樣板
  garage_car_watch.py --selftest                                            # 離線自我檢查（合成畫面），不寫任何狀態
"""
import argparse
import csv
import json
import os
import sys
import time

import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_ROI = os.path.join(ROOT, 'garage_roi.json')
DEFAULT_DIR = os.path.join(ROOT, 'garage_car')
WORK_W = 640                      # 分析時縮到這個寬度（原圖 2688 寬），位移像素以此為單位
HIST_KEEP = 40                    # 車燈亮度滾動歷史筆數


def load_img(path):
    im = Image.open(path).convert('RGB')
    h = int(im.height * WORK_W / im.width)
    return im.resize((WORK_W, h), Image.BILINEAR)


def crop(arr, box):
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = box
    return arr[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


def gray(rgb):
    return rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], dtype=np.float32)


def phase_shift(a, b):
    """兩張同大小灰階圖的位移（像素，回傳 (dx, dy, 峰值強度)）。"""
    if a.shape != b.shape or min(a.shape) < 16:
        return 0.0, 0.0, 0.0
    win = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1])).astype(np.float32)
    fa = np.fft.rfft2((a - a.mean()) * win)
    fb = np.fft.rfft2((b - b.mean()) * win)
    r = fa * np.conj(fb)
    r /= np.maximum(np.abs(r), 1e-9)
    c = np.fft.irfft2(r, s=a.shape)
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    peak = float(c[iy, ix])
    dy = iy if iy <= a.shape[0] // 2 else iy - a.shape[0]
    dx = ix if ix <= a.shape[1] // 2 else ix - a.shape[1]
    return float(dx), float(dy), peak


def signature(rgb):
    """車身區的樣板：4x4 區塊平均亮度（以整塊平均正規化）＋ 16 格亮度直方圖；另帶彩度判斷日夜（紅外線無彩度）。"""
    g = gray(rgb)
    h, w = g.shape
    grid = np.array([[g[i * h // 4:(i + 1) * h // 4, j * w // 4:(j + 1) * w // 4].mean() for j in range(4)] for i in range(4)])
    grid = grid / max(g.mean(), 1.0)
    hist, _ = np.histogram(g, bins=16, range=(0, 255))
    hist = hist / max(hist.sum(), 1)
    mx, mn = rgb.max(axis=2).astype(np.float32), rgb.min(axis=2).astype(np.float32)
    sat = float(((mx - mn) / np.maximum(mx, 1)).mean())
    return {'mode': 'ir' if sat < 0.04 else 'color', 'grid': grid.round(4).ravel().tolist(), 'hist': hist.round(4).tolist()}


def sig_dist(a, b):
    ga, gb = np.array(a['grid']), np.array(b['grid'])
    ha, hb = np.array(a['hist']), np.array(b['hist'])
    return float(np.abs(ga - gb).mean() + 0.5 * np.abs(ha - hb).sum() / 2)


def shape_type(bg, empty):
    """沒學過樣板的車（非 Luxgen／Tesla）：用「與空車位的差異區域」大小與長寬比粗分 motorcycle／suv／sedan。"""
    if bg.shape != empty.shape:
        return 'unknown'
    mask = np.abs(bg - empty) > 25
    area = float(mask.mean())
    if area < 0.04:
        return 'unknown'
    rows = np.where(mask.mean(axis=1) > 0.10)[0]
    cols = np.where(mask.mean(axis=0) > 0.10)[0]
    if len(rows) == 0 or len(cols) == 0:
        return 'unknown'
    hh, ww = rows[-1] - rows[0] + 1, cols[-1] - cols[0] + 1
    if area < 0.18:
        return 'motorcycle'
    return 'suv' if hh / max(ww, 1) > 0.62 else 'sedan'


def cable_sig(arr, box):
    """充電線區域的邊緣能量分布（12x8 格，總和正規化）：線的位置／走向不同，分布就不同。"""
    g = gray(crop(arr, box))
    gx = np.abs(np.diff(g, axis=1))[:-1, :]
    gy = np.abs(np.diff(g, axis=0))[:, :-1]
    e = np.minimum(gx + gy, 80.0)
    h, w = e.shape
    gh, gw = h // 8 * 8, w // 12 * 12
    e = e[:gh, :gw].reshape(8, gh // 8, 12, gw // 12).mean(axis=(1, 3))
    return (e / max(e.sum(), 1e-6)).round(5).ravel().tolist()


def cable_classify(sig, templates, thr, margin=0.04):
    best = None
    scored = []
    for label, t in (templates or {}).items():
        d = float(np.abs(np.array(sig) - np.array(t)).sum())
        scored.append((d, label))
    scored.sort()
    if not scored:
        return {'state': 'unknown', 'dist': None}
    d0, l0 = scored[0]
    ok = d0 <= thr and (len(scored) == 1 or scored[1][0] - d0 >= margin)
    return {'state': l0 if ok else 'unknown', 'dist': round(d0, 3), 'second': round(scored[1][0], 3) if len(scored) > 1 else None}


def cmd_learn_cable(img, roi, state, label):
    sig = cable_sig(np.asarray(img), roi['cable'])
    tpl = state.setdefault('cable_templates', {})
    old = tpl.get(label)
    tpl[label] = sig if not old else [round(0.7 * a + 0.3 * b, 5) for a, b in zip(old, sig)]
    return {'learned_cable': label}


def vision_call(url, path, query, jpg, timeout=20):
    req = urllib.request.Request(url.rstrip('/') + path + '?' + query, data=jpg, method='POST',
                                 headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def slots_query(roi):
    return 'slots=' + ';'.join('%s=%s' % (n, ','.join(str(x) for x in s['body'])) for n, s in roi['slots'].items())


def apply_vision(a, roi, state, out, jpg, now):
    """本機 YOLO＋CLIP（Garage Vision add-on）補強：框出車、認出是哪輛車與車頭朝向、粗分車型。
    平常 vision_every 秒一次；有車燈／位移證據或身分不明時馬上多問一次。add-on 連不上就略過（保持原本的分析）。"""
    v = state.setdefault('vision', {})
    thr = roi.get('thresholds', {})
    need = (now - v.get('ts', 0) > a.vision_every) or any(
        r['lights_on'] or r['moved'] or r['identity'] == 'unknown' for r in out['slots'].values())
    if not need:
        return {'skipped': True}
    try:
        res = vision_call(a.vision, '/analyze', slots_query(roi), jpg)
    except Exception as e:  # noqa: BLE001
        return {'error': str(e)[:120]}
    v['ts'] = now
    summary = {'ms': res.get('ms'), 'slots': {}}
    for name, vr in (res.get('slots') or {}).items():
        r = out['slots'].get(name)
        if r is None:
            continue
        d = vr.get('det')
        s = {'det': d['cls'] if d else None, 'conf': d['conf'] if d else None}
        if d and d['conf'] >= 0.5:
            r['present'] = True
            state.setdefault('slots', {}).setdefault(name, {})['present'] = True
            idr, typ = vr.get('id'), vr.get('type')
            if idr and idr.get('score', 0) >= thr.get('vision_id_score', 0.85) and \
                    (idr.get('second') is None or idr['score'] - idr['second'] >= thr.get('vision_id_margin', 0.02)):
                r['identity'] = idr['identity']
                r['identity_src'] = 'vision'
                if idr.get('facing') and idr.get('facing_margin', 1) >= thr.get('vision_face_margin', 0.01):
                    r['facing'] = idr['facing']
                    state.setdefault('slots', {}).setdefault(name, {})['facing'] = idr['facing']
                s['id'] = idr['identity']
                s['score'] = idr['score']
            if r['identity'] == 'unknown' and typ and typ.get('p', 0) >= 0.6:
                r['vehicle_type'] = {'truck': 'suv'}.get(typ['label'], typ['label'])
            elif r['identity'] == 'unknown' and d['cls'] == 'motorcycle':
                r['vehicle_type'] = 'motorcycle'
            s['type'] = typ
        summary['slots'][name] = s
    return summary


def load_json(path, default):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def analyse(img, roi, state, workdir, learn=True, now=None, gate_recent=False):
    """核心分析；state 會被就地更新（learn=True 時）。回傳結果 dict。"""
    now = now or time.time()
    arr = np.asarray(img)
    wall_g = gray(crop(arr, roi['wall']))
    wall_mean = float(wall_g.mean())
    wall_prev = state.get('wall_mean')
    exposure_changed = bool(wall_prev and abs(wall_mean - wall_prev) / max(wall_prev, 1) > roi.get('exposure_jump', 0.25))
    out = {'ts': int(now), 'wall_mean': round(wall_mean, 1), 'exposure_changed': exposure_changed, 'slots': {}}
    thr = roi.get('thresholds', {})
    t_light = thr.get('lights_delta', 0.35)
    t_move = thr.get('shift_px', 3.0)
    t_occ = thr.get('occupied_diff', 14.0)
    t_sig = thr.get('identity_dist', 0.25)
    for name, s in roi['slots'].items():
        st = state.setdefault('slots', {}).setdefault(name, {})
        body = crop(arr, s['body'])
        bg = gray(body)
        res = {'occupied': None, 'identity': 'unknown', 'lights_on': False, 'lights_delta': 0.0, 'moved': False, 'shift_px': 0.0,
               'lights_reliable': bool(s.get('lights_reliable', True))}
        # 有沒有車
        empty_path = os.path.join(workdir, 'empty_%s.npy' % name)
        if os.path.exists(empty_path):
            e = np.load(empty_path)
            if e.shape == bg.shape:
                diff = float(np.abs(bg - e).mean())
                res['occupied_diff'] = round(diff, 1)
                res['occupied'] = bool(diff > t_occ)
        ref_path = os.path.join(workdir, 'ref_%s.npy' % name)
        # 與滾動基準的差異（車子被開走時會突然變很大）
        ref_diff = None
        if os.path.exists(ref_path):
            rr = np.load(ref_path)
            if rr.shape == bg.shape:
                ref_diff = float(np.abs(bg - rr).mean())
                res['ref_diff'] = round(ref_diff, 1)
        big = bool(ref_diff is not None and ref_diff > 2 * t_occ and not exposure_changed)
        st['bigchg'] = (st.get('bigchg', 0) + 1) if big else 0
        present = res['occupied'] if res['occupied'] is not None else st.get('present', True)
        # 還沒學過空車位基準：鐵門剛開過、且車身區域連續 3 次大幅改變 → 視為車已開走，順便把現在畫面學成空車位基準
        if gate_recent and learn and res['occupied'] is None and present and st['bigchg'] >= 3:
            np.save(empty_path, bg)
            present = False
            res['auto_empty'] = True
        # 是哪輛車
        sig = signature(body)
        res['sig_mode'] = sig['mode']
        # 樣板鍵：<mode>＝車頭朝鐵門（door）、<mode>_inside＝車頭朝內（倒車入庫）
        per_car = {}
        for car, tpls in (state.get('templates', {}) or {}).items():
            for key, tpl in tpls.items():
                if key not in (sig['mode'], sig['mode'] + '_inside'):
                    continue
                d = sig_dist(sig, tpl)
                per_car.setdefault(car, []).append(('inside' if key.endswith('_inside') else 'door', d))
        ranked = sorted(((min(v, key=lambda x: x[1]), car, v) for car, v in per_car.items()), key=lambda z: z[0][1])
        res['facing'] = 'unknown'
        if ranked:
            (face, d), car, v = ranked[0]
            res['identity_dist'] = round(d, 3)
            other_car = ranked[1][0][1] if len(ranked) > 1 else None
            if d <= t_sig and (other_car is None or other_car - d > 0.03):
                res['identity'] = car
                other_face = [x[1] for x in v if x[0] != face]
                if not other_face or other_face[0] - d > 0.02:
                    res['facing'] = face
        res['vehicle_type'] = 'unknown'
        if os.path.exists(empty_path) and res.get('occupied'):
            res['vehicle_type'] = shape_type(bg, np.load(empty_path))
        # 車燈：車尾朝向攝影機（車頭朝鐵門，door）看尾燈／煞車燈／倒車燈；車頭朝向攝影機（inside）看頭燈。
        # 亮度（紅外線夜間）與「紅色程度」（白天煞車燈、倒車時的紅色尾燈）兩種訊號，任一明顯高於滾動基準就算亮起。
        which = 'inside' if st.get('facing') == 'inside' else 'door'
        lbox = s.get('lights_' + which) or s['lights']
        lrgb = crop(arr, lbox).astype(np.float32)
        lg = gray(lrgb)
        level = float(np.percentile(lg, 95)) / max(wall_mean, 1.0)
        redv = float(np.percentile(lrgb[..., 0] - np.maximum(lrgb[..., 1], lrgb[..., 2]), 95)) / 255.0
        hist = st.setdefault('lights_hist_' + which, [])
        rhist = st.setdefault('red_hist_' + which, [])
        base = float(np.median(hist)) if len(hist) >= 5 else None
        rbase = float(np.median(rhist)) if len(rhist) >= 5 else None
        res['lights_level'] = round(level, 3)
        res['lights_roi'] = which
        if base is not None and not exposure_changed:
            res['lights_delta'] = round(level - base, 3)
            res['lights_on'] = bool(res['lights_reliable'] and res['lights_delta'] > t_light)
        if rbase is not None and not exposure_changed:
            res['red_delta'] = round(redv - rbase, 3)
            if res['lights_reliable'] and res['red_delta'] > thr.get('red_delta', 0.12):
                res['lights_on'] = True
        # 位移
        if os.path.exists(ref_path) and not exposure_changed:
            ref = np.load(ref_path)
            dx, dy, peak = phase_shift(bg, ref)
            res['shift_px'] = round(float(np.hypot(dx, dy)), 2)
            res['shift_peak'] = round(peak, 3)
            res['moved'] = bool(res['shift_px'] >= t_move and (peak > 0.03 or res['shift_px'] >= 10))
        res['present'] = bool(present)
        if learn and res['facing'] != 'unknown':
            st['facing'] = res['facing']
        if learn:
            if present and st.get('present', True) is False and os.path.exists(ref_path):
                os.remove(ref_path)          # 車回來了：舊基準作廢，重新學
                st['arrived_ts'] = now
            if (not present) and st.get('present', True):
                st['left_ts'] = now
            st['present'] = bool(present)
        # 更新滾動基準（只在「看起來靜止」時；異常時凍結，避免把變化學進基準）
        quiet = not res['lights_on'] and not res['moved'] and bool(present) and not big
        if learn and quiet and not exposure_changed:
            hist.append(level)
            del hist[:-HIST_KEEP]
            rhist.append(redv)
            del rhist[:-HIST_KEEP]
            if (not os.path.exists(ref_path)) or now - st.get('ref_ts', 0) > roi.get('ref_refresh_sec', 300):
                np.save(ref_path, bg)
                st['ref_ts'] = now
        out['slots'][name] = res
    if roi.get('cable'):
        csig = cable_sig(arr, roi['cable'])
        out['cable'] = cable_classify(csig, state.get('cable_templates'), thr.get('cable_dist', 0.30))
    if learn and not exposure_changed:
        state['wall_mean'] = wall_mean
    return out


def cmd_learn_empty(img, roi, name, workdir):
    s = roi['slots'][name]
    np.save(os.path.join(workdir, 'empty_%s.npy' % name), gray(crop(np.asarray(img), s['body'])))
    return {'learned_empty': name}


def cmd_learn_sig(img, roi, state, name, car, workdir):
    facing = 'door'
    if ':' in car:
        car, facing = car.split(':', 1)
    sig = signature(crop(np.asarray(img), roi['slots'][name]['body']))
    key = sig['mode'] + ('_inside' if facing == 'inside' else '')
    state.setdefault('templates', {}).setdefault(car, {})[key] = sig
    return {'learned_sig': car, 'facing': facing, 'mode': sig['mode']}


def selftest():
    """合成畫面自我檢查：靜止 → 不誤判；加亮車燈 → lights_on；平移車身 → moved；整體變亮 → 排除。"""
    import tempfile
    rng = np.random.default_rng(1)
    base = (rng.random((360, 640, 3)) * 40 + 80).astype(np.uint8)
    base[40:140, 20:100] = 120                     # 牆面參考
    base[120:300, 330:610] = (rng.random((180, 280, 3)) * 30 + 170).astype(np.uint8)   # 車身（亮）
    base[200:230, 340:560] = 150                   # 車燈區（暗）
    roi = {'wall': [0.03, 0.11, 0.16, 0.39], 'slots': {'front': {'body': [0.5, 0.3, 0.95, 0.85], 'lights': [0.52, 0.55, 0.88, 0.64]}},
           'thresholds': {'lights_delta': 0.35, 'shift_px': 3.0}, 'ref_refresh_sec': 99999}
    errors = []
    with tempfile.TemporaryDirectory() as d:
        state = {}
        for i in range(8):
            r = analyse(Image.fromarray(base), roi, state, d, now=1000 + i)
        s = r['slots']['front']
        if s['lights_on'] or s['moved']:
            errors.append('靜止時誤判 %s' % s)
        lit = base.copy()
        lit[200:230, 340:560] = 255
        s = analyse(Image.fromarray(lit), roi, state, d, learn=False, now=1100)['slots']['front']
        if not s['lights_on']:
            errors.append('車燈變亮沒被偵測 %s' % s)
        moved = np.roll(base, 12, axis=1)
        s = analyse(Image.fromarray(moved), roi, state, d, learn=False, now=1200)['slots']['front']
        if not s['moved']:
            errors.append('車身位移沒被偵測 %s' % s)
        bright = np.clip(base.astype(np.int16) + 60, 0, 255).astype(np.uint8)
        r = analyse(Image.fromarray(bright), roi, state, d, learn=False, now=1300)
        if not r['exposure_changed'] or r['slots']['front']['lights_on']:
            errors.append('整體亮度變化未被排除 %s' % r)
        # 空位判斷與樣板
        cmd_learn_empty(Image.fromarray(np.where(np.arange(640)[None, :, None] > 300, 90, base).astype(np.uint8)), roi, 'front', d)
        r = analyse(Image.fromarray(base), roi, state, d, learn=False, now=1400)
        if r['slots']['front']['occupied'] is not True:
            errors.append('有車未判成 occupied %s' % r['slots']['front'])
        cmd_learn_sig(Image.fromarray(base), roi, state, 'front', 'luxgen_n7', d)
        r = analyse(Image.fromarray(base), roi, state, d, learn=False, now=1500)
        if r['slots']['front']['identity'] != 'luxgen_n7':
            errors.append('身分比對失敗 %s' % r['slots']['front'])
    # 沒學過空車位基準時：鐵門剛開過 + 車被開走（車身區域變成地板）連續 3 次 → 自動學成空車位；車回來 → present 回 True
    with tempfile.TemporaryDirectory() as d:
        state = {}
        for i in range(8):
            analyse(Image.fromarray(base), roi, state, d, now=2000 + i)
        gone = base.copy()
        gone[120:300, 330:610] = (rng.random((180, 280, 3)) * 20 + 60).astype(np.uint8)
        for i in range(4):
            r = analyse(Image.fromarray(gone), roi, state, d, now=2100 + i, gate_recent=True)
        s = r['slots']['front']
        if s['present'] is not False:
            errors.append('車開走沒判成 present=False %s' % s)
        for i in range(3):
            r = analyse(Image.fromarray(base), roi, state, d, now=2200 + i)
        if r['slots']['front']['present'] is not True:
            errors.append('車回來沒判成 present=True %s' % r['slots']['front'])
    # 鐵門沒開過：只是畫面大改變（例如有人搬東西）不可自動學成空車位
    with tempfile.TemporaryDirectory() as d:
        state = {}
        for i in range(8):
            analyse(Image.fromarray(base), roi, state, d, now=4000 + i)
        for i in range(4):
            r = analyse(Image.fromarray(gone), roi, state, d, now=4100 + i, gate_recent=False)
        if r['slots']['front']['present'] is not True:
            errors.append('鐵門沒開過卻把車位學成空 %s' % r['slots']['front'])
    # 紅色煞車燈（白天彩色畫面）：車燈區域變紅 → lights_on（亮度不一定變很多）
    colr = base.copy()
    colr[..., 2] = (colr[..., 2] * 0.6).astype(np.uint8)
    roi_r = dict(roi); roi_r['slots'] = {'front': dict(roi['slots']['front'], lights_door=[0.52, 0.55, 0.88, 0.64])}
    with tempfile.TemporaryDirectory() as d:
        state = {}
        for i in range(8):
            analyse(Image.fromarray(colr), roi_r, state, d, now=7000 + i)
        brake = colr.copy()
        brake[200:230, 340:560, 0] = 235
        brake[200:230, 340:560, 1] = 60
        brake[200:230, 340:560, 2] = 60
        s = analyse(Image.fromarray(brake), roi_r, state, d, learn=False, now=7100)['slots']['front']
        if not s['lights_on']:
            errors.append('紅色煞車燈沒被偵測 %s' % s)
    # 車型粗分：機車（小面積）、休旅車（高）、房車（扁長）
    e0 = np.full((100, 200), 60.0, dtype=np.float32)
    def veh(h, w):
        v = e0.copy()
        v[100 - h:, 100 - w // 2:100 + w // 2] = 200
        return v
    for want, (h, w) in {'motorcycle': (30, 40), 'suv': (90, 120), 'sedan': (45, 170)}.items():
        got = shape_type(veh(h, w), e0)
        if got != want:
            errors.append('車型 %s 判成 %s' % (want, got))
    # 車頭朝向：同一輛車左右鏡像的畫面要能分辨 door／inside
    grad = np.tile(np.linspace(120, 250, 280)[None, :, None], (180, 1, 3)).astype(np.uint8)
    face_door = base.copy()
    face_door[120:300, 330:610] = grad
    face_in = base.copy()
    face_in[120:300, 330:610] = grad[:, ::-1]
    with tempfile.TemporaryDirectory() as d:
        state = {}
        cmd_learn_sig(Image.fromarray(face_door), roi, state, 'front', 'luxgen_n7', d)
        cmd_learn_sig(Image.fromarray(face_in), roi, state, 'front', 'luxgen_n7:inside', d)
        s1 = analyse(Image.fromarray(face_door), roi, state, d, learn=False, now=5000)['slots']['front']
        s2 = analyse(Image.fromarray(face_in), roi, state, d, learn=False, now=5100)['slots']['front']
        if (s1['identity'], s1['facing']) != ('luxgen_n7', 'door'):
            errors.append('車頭朝鐵門沒判出 %s' % s1)
        if (s2['identity'], s2['facing']) != ('luxgen_n7', 'inside'):
            errors.append('車頭朝內沒判出 %s' % s2)
    # 充電線：垂掛／拉向前位車的邊緣分布不同 → 能分出 hanging、to_front；沒學過的畫面回 unknown
    roi_c = dict(roi, cable=[0.0, 0.1, 0.4, 0.7])
    hang = base.copy()
    hang[80:250, 40:44] = 20                 # 垂直線（垂掛）
    tofront = base.copy()
    for i in range(160):
        tofront[100 + i // 4:103 + i // 4, 20 + i:23 + i] = 20     # 斜線（拉向車）
    with tempfile.TemporaryDirectory() as d:
        state = {}
        cmd_learn_cable(Image.fromarray(hang), roi_c, state, 'hanging')
        cmd_learn_cable(Image.fromarray(tofront), roi_c, state, 'to_front')
        c1 = analyse(Image.fromarray(hang), roi_c, state, d, learn=False, now=6000)['cable']
        c2 = analyse(Image.fromarray(tofront), roi_c, state, d, learn=False, now=6100)['cable']
        if c1['state'] != 'hanging' or c2['state'] != 'to_front':
            errors.append('充電線分類失敗 %s %s' % (c1, c2))
    print(json.dumps({'selftest': 'FAIL' if errors else 'PASS', 'errors': errors}, ensure_ascii=False))
    return 1 if errors else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--snapshot')
    ap.add_argument('--roi', default=DEFAULT_ROI)
    ap.add_argument('--dir', default=DEFAULT_DIR)
    ap.add_argument('--learn-empty')
    ap.add_argument('--learn-sig')
    ap.add_argument('--learn-cable', help='hanging（沒接車，線垂掛）／to_front（接到前位車）／unseen（拍不到，接到後位車）')
    ap.add_argument('--no-learn', action='store_true', help='只分析，不更新滾動基準（除錯用）')
    ap.add_argument('--csv', action='store_true', help='附加一列指標到 metrics.csv（P0 資料收集）')
    ap.add_argument('--gate-recent', action='store_true', help='鐵門最近 10 分鐘內開過（啟用「車位自動學成空」）')
    ap.add_argument('--vision', help='Garage Vision add-on 網址，例如 http://local-garage-vision:8099（沒給就不用）')
    ap.add_argument('--vision-every', type=int, default=300, help='平常多久問一次 add-on（秒）')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.snapshot:
        ap.error('--snapshot required')
    os.makedirs(a.dir, exist_ok=True)
    roi = load_json(a.roi, None)
    if not roi:
        print(json.dumps({'error': 'roi not found: ' + a.roi}))
        sys.exit(2)
    state_path = os.path.join(a.dir, 'state.json')
    state = load_json(state_path, {})
    try:
        img = load_img(a.snapshot)
    except Exception as e:
        print(json.dumps({'error': 'snapshot: %s' % e}))
        sys.exit(3)
    if a.learn_empty:
        print(json.dumps(cmd_learn_empty(img, roi, a.learn_empty, a.dir)))
        return
    if a.learn_cable:
        if not roi.get('cable'):
            print(json.dumps({'error': 'roi has no cable box'}))
            sys.exit(4)
        res = cmd_learn_cable(img, roi, state, a.learn_cable)
        save_json(state_path, state)
        print(json.dumps(res))
        return
    if a.learn_sig:
        name, car = a.learn_sig.split('=', 1)
        res = cmd_learn_sig(img, roi, state, name, car, a.dir)
        if a.vision:
            try:
                lab = car if (':' in car or car in ('sedan', 'suv', 'motorcycle')) else car + ':door'
                rv = vision_call(a.vision, '/learn', 'slot=%s&label=%s&%s' % (name, lab, slots_query(roi)), open(a.snapshot, 'rb').read())
                res['vision'] = rv.get('learned')
            except Exception as e:  # noqa: BLE001
                res['vision_error'] = str(e)[:120]
        save_json(state_path, state)
        print(json.dumps(res))
        return
    out = analyse(img, roi, state, a.dir, learn=not a.no_learn, gate_recent=a.gate_recent)
    if a.vision:
        out['vision'] = apply_vision(a, roi, state, out, open(a.snapshot, 'rb').read(), time.time())
    if not a.no_learn:
        save_json(state_path, state)
    if a.csv:
        path = os.path.join(a.dir, 'metrics.csv')
        new = not os.path.exists(path)
        with open(path, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if new:
                w.writerow(['ts', 'wall_mean', 'exposure_changed', 'slot', 'present', 'identity', 'facing', 'lights_level', 'lights_delta', 'lights_on', 'shift_px', 'moved'])
            for n, r in out['slots'].items():
                w.writerow([out['ts'], out['wall_mean'], int(out['exposure_changed']), n, int(r['present']), r['identity'], r['facing'], r['lights_level'],
                            r['lights_delta'], int(r['lights_on']), r['shift_px'], int(r['moved'])])
        # 保留最近約 14 天（每分鐘 2 列）
        try:
            lines = open(path, encoding='utf-8').read().splitlines()
            if len(lines) > 60000:
                open(path, 'w', encoding='utf-8').write('\n'.join([lines[0]] + lines[-50000:]) + '\n')
        except Exception:
            pass
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()

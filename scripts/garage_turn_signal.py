#!/usr/bin/env python3
"""車尾左方向燈偵測（V4.3.0-beta 4）：看 3 秒短片，車尾左後角（車頭朝鐵門時＝畫面上車身的左側）的橘色像素比例隨時間一亮一滅＝打左方向燈。
用法：garage_turn_signal.py --clip /config/www/snap/x.mp4 --slot front [--vision http://local-garage-vision:8099] [--side left]
輸出 JSON：{blink, flashes, peak, floor, series, box, side}。--selftest 用合成序列驗證。只讀影片，不碰 HA。"""
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
REGION = {'left': (0.0, 0.22, 0.18, 0.56), 'right': (0.78, 1.0, 0.18, 0.56)}


def amber_frac(rgb):
    """橘黃色（色相約 20～48°、飽和度高、亮）像素比例；煞車燈的純紅（色相 <15°）不算。"""
    hsv = np.asarray(Image.fromarray(rgb).convert('HSV'), dtype=np.float32)
    h = hsv[..., 0] * 360.0 / 255.0
    s, v = hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    m = (h >= 20) & (h <= 48) & (s >= 0.55) & (v >= 0.70)
    return float(m.mean())


def decide(series, min_swing=0.004, min_flashes=3, max_run=8):
    """series：每幀橘色比例（10fps）。方向燈＝約 1～2Hz 短促亮暗交替：亮的區段 ≥min_flashes 次，且每段亮／暗都不超過 max_run 幀（0.8 秒）。
    車子移動、陽光反光造成的橘色是「慢慢升高再降低」的長區段，不算。"""
    base = {'blink': False, 'flashes': 0, 'peak': 0.0, 'floor': 0.0}
    if len(series) < 12:
        return base
    a = np.asarray(series, dtype=np.float32)
    hi, lo = float(np.percentile(a, 92)), float(np.percentile(a, 8))
    base.update({'peak': round(hi, 4), 'floor': round(lo, 4)})
    if hi - lo < min_swing or hi < 2.0 * lo + min_swing / 2:
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
    inner = runs[1:-1] if len(runs) > 2 else runs        # 頭尾區段被剪斷，不算
    flashes = sum(1 for st, ln in inner if st and 1 <= ln <= max_run)
    too_long = any(ln > max_run for st, ln in inner)
    base.update({'flashes': flashes, 'blink': bool(flashes >= min_flashes and not too_long)})
    return base


def vision_box(url, jpg, roi, slot):
    q = 'slots=' + ';'.join('%s=%s' % (n, ','.join(str(x) for x in s['body'])) for n, s in roi['slots'].items()) + '&plate=0'
    req = urllib.request.Request(url.rstrip('/') + '/analyze?' + q, data=jpg, method='POST', headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = ((json.loads(r.read().decode()).get('slots') or {}).get(slot) or {}).get('det')
    return d['box'] if d else None


def analyse_clip(clip, slot, side, vision):
    roi = json.load(open(ROI, encoding='utf-8'))
    tmp = tempfile.mkdtemp(prefix='turn_')
    try:
        r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-nostdin', '-i', clip, '-vf', 'fps=%d,scale=1344:-1' % FPS, '-q:v', '3', tmp + '/%04d.jpg'],
                           capture_output=True, text=True, timeout=60)
        frames = sorted(glob.glob(tmp + '/*.jpg'))
        if r.returncode != 0 or len(frames) < 8:
            return {'error': 'ffmpeg: %s frames=%d %s' % (r.returncode, len(frames), r.stderr[:100])}
        box = None
        if vision:
            try:
                box = vision_box(vision, open(frames[len(frames) // 2], 'rb').read(), roi, slot)
            except Exception:  # noqa: BLE001
                box = None
        if not box:
            box = roi['slots'][slot]['body']
        x0, x1, y0, y1 = REGION[side]
        bw, bh = box[2] - box[0], box[3] - box[1]
        series = []
        for f in frames:
            im = Image.open(f).convert('RGB')
            W, H = im.size
            c = im.crop((int((box[0] + bw * x0) * W), int((box[1] + bh * y0) * H), int((box[0] + bw * x1) * W), int((box[1] + bh * y1) * H)))
            series.append(round(amber_frac(np.asarray(c)), 4))
        out = decide(series)
        out.update({'side': side, 'slot': slot, 'box': [round(v, 3) for v in box], 'series': series})
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def selftest():
    err = []
    steady = [0.001] * 30
    if decide(steady)['blink']:
        err.append('常亮／無燈被判成閃爍')
    blink = ([0.02] * 3 + [0.001] * 4) * 5            # 約 1.4Hz 閃爍（10fps）
    if not decide(blink)['blink']:
        err.append('閃爍沒被偵測 %s' % decide(blink))
    one = [0.001] * 12 + [0.02] * 5 + [0.001] * 13     # 只亮一次（反光／路過）
    if decide(one)['blink']:
        err.append('只亮一次被判成閃爍')
    bump = [0.0] * 20 + [round(0.03 * (1 - abs(i - 20) / 20), 4) for i in range(40)] + [0.0] * 20       # 車子移動：橘色慢慢升高再降低
    if decide(bump)['blink']:
        err.append('慢速起伏被判成閃爍')
    weak = ([0.0035] * 3 + [0.001] * 4) * 5            # 幅度太小
    if decide(weak)['blink']:
        err.append('微弱變化被判成閃爍')
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    img[:10, :10] = (255, 170, 30)                     # 橘
    img[10:, :10] = (230, 20, 20)                      # 紅（煞車燈）
    f = amber_frac(img)
    if not 0.2 < f < 0.3:
        err.append('橘色比例不對 %s（紅色不該算）' % f)
    print(json.dumps({'selftest': 'PASS' if not err else 'FAIL', 'errors': err}, ensure_ascii=False))
    return 0 if not err else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clip')
    ap.add_argument('--slot', default='front')
    ap.add_argument('--side', default='left', choices=['left', 'right'])
    ap.add_argument('--vision')
    ap.add_argument('--delete', action='store_true', help='分析完刪掉短片')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.clip:
        ap.error('--clip required')
    try:
        print(json.dumps(analyse_clip(a.clip, a.slot, a.side, a.vision), ensure_ascii=False))
    finally:
        if a.delete:
            try:
                os.remove(a.clip)
            except OSError:
                pass


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""車庫出門影片掃描（開發用，只讀影片）：逐幀算「左後角橘色比例（左方向燈）」與「煞車燈區域亮度／紅色程度」，
輸出每秒摘要與滑動視窗的左方向燈判斷，用來對照真實出門影片、調整 garage_turn_signal.py／garage_car_watch.py 門檻。
用法（HA 容器內）：garage_exit_scan.py CLIP_MP4 [--slot front] [--fps 10] [--box x0,y0,x1,y1] [--json out.json]
車身框預設取 garage_roi.json 該車位的 body（影片裡車子不一定剛好在框內，--box 可覆蓋）。"""
import argparse
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

spec = importlib.util.spec_from_file_location('gts', '/config/scripts/garage_turn_signal.py')
gts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--slot', default='front')
    ap.add_argument('--fps', type=int, default=10)
    ap.add_argument('--box')
    ap.add_argument('--json')
    a = ap.parse_args()
    roi = json.load(open('/config/garage_roi.json', encoding='utf-8'))
    s = roi['slots'][a.slot]
    box = [float(v) for v in a.box.split(',')] if a.box else s['body']
    lbox = s.get('lights_door') or s['lights']
    wall = roi['wall']
    tmp = tempfile.mkdtemp(prefix='gscan_')
    try:
        r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-nostdin', '-i', a.clip, '-vf', 'fps=%d,scale=1344:-1' % a.fps, '-q:v', '3', tmp + '/%05d.jpg'],
                           capture_output=True, text=True)
        frames = sorted(glob.glob(tmp + '/*.jpg'))
        if not frames:
            print(json.dumps({'error': 'no frames', 'stderr': r.stderr[:200]}))
            return 1
        x0, x1, y0, y1 = gts.REGION['left']
        bw, bh = box[2] - box[0], box[3] - box[1]
        amber, red, lvl = [], [], []
        for f in frames:
            im = Image.open(f).convert('RGB')
            W, H = im.size
            arr = np.asarray(im)
            c = im.crop((int((box[0] + bw * x0) * W), int((box[1] + bh * y0) * H), int((box[0] + bw * x1) * W), int((box[1] + bh * y1) * H)))
            amber.append(round(gts.amber_frac(np.asarray(c)), 4))
            lr = arr[int(lbox[1] * H):int(lbox[3] * H), int(lbox[0] * W):int(lbox[2] * W)].astype(np.float32)
            wr = arr[int(wall[1] * H):int(wall[3] * H), int(wall[0] * W):int(wall[2] * W)].astype(np.float32)
            g = lr.mean(axis=2)
            wm = max(float(wr.mean()), 1.0)
            lvl.append(round(float(np.percentile(g, 95)) / wm, 3))
            red.append(round(float(np.percentile(lr[..., 0] - np.maximum(lr[..., 1], lr[..., 2]), 95)) / 255.0, 3))
        n = len(frames)
        fps = a.fps
        # 滑動視窗（3 秒、每 0.5 秒）左方向燈判斷
        wins = []
        win, step = 3 * fps, fps // 2 or 1
        for i in range(0, max(n - win, 0) + 1, step):
            d = gts._decide_window(np.asarray(amber[i:i + win], dtype=np.float32), 0.005, 3, 8)
            if d['blink']:
                wins.append({'t': round(i / fps, 1), 'flashes': d['flashes'], 'peak': d['peak'], 'floor': d['floor']})
        per_sec = []
        for k in range(0, n, fps):
            sl = slice(k, k + fps)
            per_sec.append({'t': k // fps, 'amber_max': max(amber[sl]), 'amber_min': min(amber[sl]), 'red': round(max(red[sl]), 3), 'lvl': round(max(lvl[sl]), 3)})
        out = {'clip': os.path.basename(a.clip), 'frames': n, 'fps': fps, 'box': box, 'blink_windows': wins, 'per_sec': per_sec}
        if a.json:
            json.dump(out, open(a.json, 'w'), ensure_ascii=False)
        print(json.dumps({'clip': out['clip'], 'frames': n, 'blink_windows': wins[:12], 'n_blink_windows': len(wins),
                          'red_max': max(red), 'lvl_max': max(lvl), 'amber_peak': max(amber)}, ensure_ascii=False))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

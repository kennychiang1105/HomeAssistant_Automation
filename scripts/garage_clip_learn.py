#!/usr/bin/env python3
"""用 UniFi Protect 存檔影片學習車庫出入（V4.2.5）：逐段影片取關鍵幀，跑與即時分析相同的畫面分析（garage_car_watch.analyse）
加上 Garage Vision add-on 的偵測／身分／朝向，把每個取樣點存成一行 JSON（/config/garage_car/learn/clip_frames.jsonl）。
之後由 garage_clip_report.py 統計「出門／回家事件」與事件前的訊號（車燈、位移）。

用法（HA 容器內）：garage_clip_learn.py CLIP_MP4 START_EPOCH [--name 顯示名稱] [--step 4]
處理完會刪掉 CLIP_MP4（影片只是暫存，不留）。只讀影片與呼叫 add-on 的 /analyze（不會改樣板庫、不碰 HA 任何實體）。
"""
import argparse
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

spec = importlib.util.spec_from_file_location('gcw', '/config/scripts/garage_car_watch.py')
gcw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gcw)

WORK = '/config/garage_car/learn'
OUT = WORK + '/clip_frames.jsonl'
VISION = 'http://local-garage-vision:8099'


def done_names():
    try:
        return {json.loads(l)['clip'] for l in open(OUT, encoding='utf-8') if l.strip()}
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('t0', type=float)
    ap.add_argument('--name', default='')
    ap.add_argument('--step', type=int, default=4)
    a = ap.parse_args()
    name = a.name or os.path.basename(a.clip)
    os.makedirs(WORK, exist_ok=True)
    if name in done_names():
        print('skip', name)
        try:
            os.remove(a.clip)
        except Exception:
            pass
        return
    roi = gcw.load_json('/config/garage_roi.json', None)
    state_path = WORK + '/state.json'
    state = gcw.load_json(state_path, {})
    tmp = WORK + '/frames'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-nostdin', '-threads', '2', '-skip_frame', 'nokey', '-i', a.clip,
                        '-vf', 'fps=1/%d,scale=1344:-1' % a.step, '-q:v', '4', tmp + '/%04d.jpg'], capture_output=True, text=True)
    frames = sorted(glob.glob(tmp + '/*.jpg'))
    if r.returncode != 0 or not frames:
        print('ffmpeg failed', name, r.stderr[:200])
        return
    sq = gcw.slots_query(roi)
    rec = {'clip': name, 't0': a.t0, 'step': a.step, 'frames': []}
    learned_n, last_learn, learned_labels = 0, {}, []
    for i, f in enumerate(frames):
        t = i * a.step
        try:
            img = gcw.load_img(f)
            out = gcw.analyse(img, roi, state, WORK, learn=True, now=a.t0 + t)
            jpg = open(f, 'rb').read()
            try:
                v = gcw.vision_call(VISION, '/analyze', sq, jpg, timeout=40)
            except Exception as e:  # noqa: BLE001
                v = {'slots': {}, 'error': str(e)[:80]}
        except Exception as e:  # noqa: BLE001
            print('frame error', name, t, e)
            continue
        fr = {'t': t, 'expo': int(out['exposure_changed']), 's': {}}
        for sn, r1 in out['slots'].items():
            vs = (v.get('slots') or {}).get(sn) or {}
            d = vs.get('det')
            idr = vs.get('id') or {}
            box = d['box'] if d else None
            fr['s'][sn] = {
                'p': 1 if d else 0,
                'cx': round((box[0] + box[2]) / 2, 3) if box else None, 'cy': round((box[1] + box[3]) / 2, 3) if box else None,
                'w': round(box[2] - box[0], 3) if box else None, 'cf': d['conf'] if d else None,
                'id': idr.get('identity'), 'sc': idr.get('score'), 'sec': idr.get('second'), 'face': idr.get('facing'),
                'ty': (vs.get('type') or {}).get('label'),
                'lo': int(r1['lights_on']), 'rd': r1.get('red_delta'), 'ld': r1.get('lights_delta'),
                'mv': int(r1['moved']), 'sh': r1['shift_px'],
                'pl': (vs.get('plate') or {}).get('text'), 'plc': (vs.get('plate') or {}).get('conf'),
            }
            if idr.get('facing'):
                state.setdefault('slots', {}).setdefault(sn, {})['facing'] = idr['facing']
            # 影像讀到家裡車牌（信心 >=0.9、完全相符）＝可靠標籤：影像樣板判錯或不夠有把握的畫面，存進 add-on 樣板庫（每段影片最多 4 張、至少隔 3 個取樣點）
            pl = vs.get('plate') or {}
            car = gcw.PLATES.get(pl.get('text')) if (pl and d and pl.get('conf', 0) >= 0.9) else None
            if car and idr.get('facing') and (idr.get('identity') != car or idr.get('score', 0) < 0.9) \
                    and learned_n < 4 and i - last_learn.get(sn, -9) >= 3:
                lab = car + (':inside' if idr['facing'] == 'inside' else '')
                try:
                    gcw.vision_call(VISION, '/learn', 'slot=%s&label=%s&%s' % (sn, lab, sq), jpg, timeout=40)
                    learned_n += 1
                    last_learn[sn] = i
                    learned_labels.append('%s:%s' % (sn, lab))
                except Exception:  # noqa: BLE001
                    pass
        rec['frames'].append(fr)
    gcw.save_json(state_path, state)
    rec['learned'] = learned_labels
    with open(OUT, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        os.remove(a.clip)
    except Exception:
        pass
    print('ok', name, len(rec['frames']), 'frames', 'plates:', sum(1 for fr in rec['frames'] for s in fr['s'].values() if s.get('pl')), 'learned:', learned_labels)


if __name__ == '__main__':
    main()

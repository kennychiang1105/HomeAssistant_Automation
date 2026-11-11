#!/usr/bin/env python3
"""車庫方向燈／雙黃燈「即時分析」（V4.4.1，2026-11-10）。
直接讀攝影機串流（HA 內建 go2rtc 轉送，常駐連線），每一幀算車尾左右角落的橘色比例，累積到規律閃爍就立刻回報；
車身框每秒向 Garage Vision add-on 更新一次並「跟著車子走」（車從後位開到前位途中也看得到，不依賴車位標籤）。
判斷沿用 garage_turn_signal.py 的 amber_frac／decide（單邊 3 秒內規律閃 ≥2 次、振幅 ≥0.005；雙黃燈左右各 ≥2 次、振幅 ≥0.003、且左右同步相關係數 ≥0.5）。
即時分析每 0.5 秒評估一次（機會比短片檢查多很多），所以改成「連續 3 輪（約 1.5 秒）都成立」才回報（2026-11-10 用 13 段影片量化校正：
真實出門 2 段都連續 4 輪；誤判 2～3 段只有 1～2 輪）。
V4.4.2（2026-11-11）：拿掉「整台車一起變色不算」——白色車身會被自己的方向燈照成橘色、整台車跟著燈一亮一暗，11-11 09:28 真的方向燈因此被擋掉、閃了 11 秒沒偵測到
（鐵門最後是車牌辨識開的）；這道防護在 13 段回放裡沒有擋下任何誤判（誤判都是「連續 3 輪」擋掉的）。參考區序列仍然記錄，只供診斷。
「車外還有人」不在這裡擋，交給 HA 開門前的 script.garage_board_check（人在車旁上車時方向燈也會亮，這裡擋掉會連真的出門一起漏掉）。

用法（HA shell_command，最長約 45 秒，偵測到就提早結束）：
  garage_turn_rt.py --url rtsp://127.0.0.1:18554/<stream> --vision http://local-garage-vision:8099 --max 45
回放驗證（整段影片跑完，列出所有偵測時間）：
  garage_turn_rt.py --clip x.mp4 --vision http://local-garage-vision:8099
輸出 JSON：{blink, kind, slot, people, flashes, peak, box, frames, elapsed, video_t, ...}。--selftest 用合成畫面驗證。只讀影像，不碰 HA。"""
import argparse
import io
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from garage_turn_signal import REGION, ROI, VEHICLE_CLS, amber_frac, decide, outside_people, vision_people  # noqa: E402

FPS = 10
W, H = 1344, 756
WIN = 30            # 雙黃燈評估視窗（幀）＝3 秒，與短片分析相同
WIN_S = 40          # 整車變色（參考區）檢查用的視窗（幀）＝4 秒
REF = (0.30, 0.70, 0.50, 0.80)   # 車身中央參考區（相對車身框 x0,x1,y0,y1）：真的車燈只有角落亮，這裡不會跟著閃
PERSON_GUARD = 0.25  # 只用來回報畫面上有沒有人（不再用來擋偵測）
MIN_LEN = 20        # 至少累積 2 秒才評估
EVAL_EVERY = 5      # 每 0.5 秒評估一次
CONFIRM = 3         # 連續幾次評估（每 0.5 秒）成立才回報
REFRESH = 20        # 每幾幀更新一次車身框（回放模式，約 2 秒，和即時模式實測的更新速度相當；即時模式由背景執行緒盡快更新）
KEEP = 90           # 每輛車保留的序列長度（幀）


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - ix * iy
    return ix * iy / u if u > 0 else 0.0


def overlap_frac(box, region):
    """box 有多少比例落在 region 內。"""
    ix = max(0.0, min(box[2], region[2]) - max(box[0], region[0]))
    iy = max(0.0, min(box[3], region[3]) - max(box[1], region[1]))
    a = max(1e-6, (box[2] - box[0]) * (box[3] - box[1]))
    return ix * iy / a


def slot_of(box, roi):
    """車身框屬於哪個車位（與車位範圍重疊最多；都沒重疊時取中心最近）。"""
    best, bv = None, 0.0
    for n, s in roi['slots'].items():
        v = overlap_frac(box, s['body'])
        if v > bv:
            best, bv = n, v
    if best:
        return best
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return min(roi['slots'], key=lambda n: (cx - (roi['slots'][n]['body'][0] + roi['slots'][n]['body'][2]) / 2) ** 2
               + (cy - (roi['slots'][n]['body'][1] + roi['slots'][n]['body'][3]) / 2) ** 2)


def vision_all(url, jpg, roi):
    """一次 add-on 呼叫：回傳 (車輛框清單 [(slot, box)], persons, 所有車輛框)。"""
    q = 'slots=' + ';'.join('%s=%s' % (n, ','.join(str(x) for x in s['body'])) for n, s in roi['slots'].items()) + '&plate=0'
    req = urllib.request.Request(url.rstrip('/') + '/analyze?' + q, data=jpg, method='POST', headers={'Content-Type': 'image/jpeg'})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode())
    out = []
    for n, s in (res.get('slots') or {}).items():
        if s.get('det') and s['det'].get('box'):
            out.append((n, s['det']['box']))
    for x in (res.get('dets') or []):
        if x.get('cls') in VEHICLE_CLS and x.get('conf', 0) >= 0.3 and x.get('box'):
            if not any(iou(x['box'], b) >= 0.6 for _, b in out):
                out.append((slot_of(x['box'], roi), x['box']))
    return out, (res.get('persons') or []), [b for _, b in out]


class Track:
    def __init__(self, slot, box):
        self.slot, self.box = slot, box
        self.sl, self.sr, self.ref = [], [], []
        self.rej = {'scene': 0, 'person': 0}
        self.miss = 0
        self.hits = 0
        self.last = None
        self.cool = 0


class Analyzer:
    def __init__(self):
        self.tracks = []
        self.people = None          # None＝還不知道（add-on 還沒回應或連不上）
        self.people_conf = []
        self.vboxes = []
        self.persons = []           # 最近一次看到的所有人框（信心 ≥ PERSON_GUARD），用來判斷有沒有人擋在車燈前
        self.lock = threading.Lock()
        self.vision_ok = 0
        self.vision_err = 0

    def refresh(self, dets, persons, vboxes):
        """用最新的車輛框更新追蹤（跟著車子走：框移動時沿用同一條序列）。"""
        with self.lock:
            used = set()
            for tr in self.tracks:
                best, bv = None, 0.3
                for i, (_, b) in enumerate(dets):
                    if i in used:
                        continue
                    v = iou(tr.box, b)
                    if v >= bv:
                        best, bv = i, v
                if best is None:
                    tr.miss += 1
                else:
                    used.add(best)
                    tr.slot, tr.box, tr.miss = dets[best][0], dets[best][1], 0
            self.tracks = [t for t in self.tracks if t.miss < 3]
            for i, (sl, b) in enumerate(dets):
                if i not in used:
                    self.tracks.append(Track(sl, b))
            self.vboxes = vboxes
            if persons is not None:
                self.persons = [q['box'] for q in persons if q.get('box') and q.get('conf', 0) >= PERSON_GUARD]
                ps = outside_people(persons, vboxes)
                self.people, self.people_conf = len(ps), [round(p.get('conf', 0), 2) for p in ps]
            self.vision_ok += 1

    def _crop(self, frame, box, reg):
        bw, bh = box[2] - box[0], box[3] - box[1]
        x0, x1, y0, y1 = reg
        ya, xa = int((box[1] + bh * y0) * H), int((box[0] + bw * x0) * W)
        return frame[ya:max(int((box[1] + bh * y1) * H), ya + 1), xa:max(int((box[0] + bw * x1) * W), xa + 1)]

    def _blocked(self, box, side):
        """有沒有人擋在這一側的車燈區域前（區域外擴 3% 畫面）。"""
        bw, bh = box[2] - box[0], box[3] - box[1]
        x0, x1, y0, y1 = REGION[side]
        r = (box[0] + bw * x0 - 0.03, box[1] + bh * y0 - 0.03, box[0] + bw * x1 + 0.03, box[1] + bh * y1 + 0.03)
        return any(min(r[2], q[2]) > max(r[0], q[0]) and min(r[3], q[3]) > max(r[1], q[1]) for q in self.persons)

    def _evaluate(self, tr):
        """回傳 (結果 dict 或 None)。結果含 kind／flashes／peak／floor／peak_left／peak_right。"""
        L, R = tr.sl[-WIN:], tr.sr[-WIN:]
        hl, hr = decide(L, min_swing=0.003), decide(R, min_swing=0.003)
        tr.last = {'peak_left': hl['peak'], 'peak_right': hr['peak']}
        out, sides = None, []
        if hl['blink'] and hr['blink']:
            a, b = np.asarray(L, dtype=np.float32), np.asarray(R, dtype=np.float32)
            cc = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0
            if cc >= 0.5:
                out, sides = dict(hl if hl['flashes'] >= hr['flashes'] else hr, kind='hazard', sync=round(cc, 2)), ['left', 'right']
        if out is None:
            rl, rr = decide(L), decide(R)
            if rl['blink'] != rr['blink']:
                out, sides = (dict(rl, kind='left'), ['left']) if rl['blink'] else (dict(rr, kind='right'), ['right'])
        if out is None:
            return None
        # 車身參考區的起伏只記錄不擋（白色車身會被方向燈照成橘色，V4.4.2）
        f = np.asarray(tr.ref[-WIN_S:], dtype=np.float32)
        out['body_swing'] = round(float(np.percentile(f, 92) - np.percentile(f, 8)), 3) if len(f) else 0.0
        out['peak_left'], out['peak_right'] = hl['peak'], hr['peak']
        return out

    def push(self, frame, n):
        """餵一幀（H×W×3 uint8）。回傳偵測結果 dict 或 None。"""
        hit = None
        with self.lock:
            for tr in self.tracks:
                for reg, ser in ((REGION['left'], tr.sl), (REGION['right'], tr.sr), (REF, tr.ref)):
                    c = self._crop(frame, tr.box, reg)
                    ser.append(round(amber_frac(c), 4) if c.size else 0.0)
                    if len(ser) > KEEP:
                        del ser[0]
                if tr.cool > 0:
                    tr.cool -= 1
                if n % EVAL_EVERY == 0 and len(tr.sl) >= MIN_LEN and tr.cool == 0:
                    r = self._evaluate(tr)
                    tr.hits = tr.hits + 1 if r else 0
                    if tr.hits >= CONFIRM and hit is None:
                        hit = dict(r, slot=tr.slot, box=[round(v, 3) for v in tr.box], series=tr.sl[-WIN_S:], series_right=tr.sr[-WIN_S:])
                        tr.hits, tr.cool = 0, 50
        return hit

    def summary(self):
        with self.lock:
            return [{'slot': t.slot, 'box': [round(v, 3) for v in t.box], 'n': len(t.sl),
                     'peak_left': (t.last or {}).get('peak_left', 0), 'peak_right': (t.last or {}).get('peak_right', 0), 'rejected': t.rej} for t in self.tracks]


def to_jpg(frame):
    b = io.BytesIO()
    Image.fromarray(frame).save(b, 'JPEG', quality=85)
    return b.getvalue()


def run(src, vision, max_s, live, stop_first):
    roi = json.load(open(ROI, encoding='utf-8'))
    cmd = ['ffmpeg', '-v', 'error', '-nostdin']
    if live:
        cmd += ['-rtsp_transport', 'tcp', '-fflags', 'nobuffer', '-flags', 'low_delay', '-probesize', '1000000', '-analyzeduration', '500000']
    cmd += ['-i', src, '-an', '-vf', 'fps=%d,scale=%d:%d' % (FPS, W, H), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    an = Analyzer()
    state = {'frame': None, 'stop': False}

    def do_refresh(frame):
        try:
            dets, persons, vboxes = vision_all(vision, to_jpg(frame), roi)
            an.refresh(dets, persons, vboxes)
        except Exception:  # noqa: BLE001
            an.vision_err += 1

    def worker():
        while not state['stop']:
            f = state['frame']
            if f is None:
                time.sleep(0.05)
                continue
            t = time.time()
            do_refresh(f)
            time.sleep(max(0.0, 0.7 - (time.time() - t)))      # 最快約每 0.7 秒更新一次車身框

    if live and vision:
        threading.Thread(target=worker, daemon=True).start()
    size, n, t0, dets_out = W * H * 3, 0, time.time(), []
    try:
        while True:
            buf = b''
            while len(buf) < size:
                chunk = proc.stdout.read(size - len(buf))
                if not chunk:
                    break
                buf += chunk
            if len(buf) < size:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3)
            n += 1
            if live:
                state['frame'] = frame
            elif vision and (n == 1 or n % REFRESH == 0):
                do_refresh(frame)
            hit = an.push(frame, n)
            if hit:
                people, pconf = an.people, an.people_conf
                if vision and live:
                    try:                      # 偵測到才補看現在這一幀，人數取較多者（和短片分析一致）
                        last = outside_people(vision_people(vision, to_jpg(frame)), an.vboxes)
                        if people is None or len(last) > people:
                            people, pconf = len(last), [round(p.get('conf', 0), 2) for p in last]
                    except Exception:  # noqa: BLE001
                        pass
                hit.update({'people': people if people is not None else -1, 'people_conf': pconf, 'frames': n,
                            'elapsed': round(time.time() - t0, 1), 'video_t': round(n / FPS, 1)})
                if stop_first:
                    return hit
                dets_out.append({k: hit[k] for k in ('video_t', 'slot', 'kind', 'flashes', 'peak_left', 'peak_right', 'people', 'box')})
            if live and time.time() - t0 > max_s:
                break
    finally:
        state['stop'] = True
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass
    out = {'blink': False, 'frames': n, 'elapsed': round(time.time() - t0, 1), 'tracks': an.summary(),
           'vision_ok': an.vision_ok, 'vision_err': an.vision_err}
    if not stop_first:
        out['detections'] = dets_out
        out['blink'] = bool(dets_out)
    if n == 0:
        out['error'] = 'no frames'
    return out


def selftest():
    err = []
    box = [0.50, 0.10, 0.96, 0.80]

    def frame(on_l, on_r, b=box, amber=(255, 170, 30), flood=False):
        f = np.zeros((H, W, 3), dtype=np.uint8)
        bw, bh = b[2] - b[0], b[3] - b[1]
        if flood:                                   # 整台車一起變色
            f[int(b[1] * H):int(b[3] * H), int(b[0] * W):int(b[2] * W)] = amber
        for side, on in (('left', on_l), ('right', on_r)):
            if on:
                x0, x1, y0, y1 = REGION[side]
                f[int((b[1] + bh * (y0 + 0.02)) * H):int((b[1] + bh * (y0 + 0.10)) * H), int((b[0] + bw * x0) * W):int((b[0] + bw * x1) * W)] = amber
        return f

    def play(seq, boxes=None, persons=None, flood=False):
        an = Analyzer()
        for i, (l, r) in enumerate(seq, 1):
            b = boxes[i - 1] if boxes else box
            if i == 1 or i % REFRESH == 0:
                an.refresh([('front', b)], persons or [], [b])
            h = an.push(frame(l, r, b, flood=flood and (l or r)), i)
            if h:
                return i, h
        return None, None

    blink = [(i % 9 < 4, i % 9 < 4) for i in range(60)]
    i, h = play(blink)
    if not h or h['kind'] != 'hazard' or i > 35:
        err.append('雙黃燈沒在 3.5 秒內偵測到 %s %s' % (i, h and h['kind']))
    i, h = play([(i % 9 < 4, i % 9 < 4) for i in range(60)], flood=True)
    if not h or h['kind'] != 'hazard':
        err.append('白色車身被方向燈照亮（整台車跟著閃）時應該照樣偵測到雙黃燈（11-11 09:28）')
    i, h = play([(i % 9 < 4, False) for i in range(60)], persons=[{'conf': 0.5, 'box': [0.44, 0.05, 0.56, 0.9]}])
    if not h or h['kind'] != 'left':
        err.append('人在車旁時方向燈不該被偵測層擋掉（交給開門前的車外有人確認）%s' % (h and h['kind']))
    i, h = play([(i in (10, 11, 12, 13, 22, 23, 24), False) for i in range(60)] + [(False, False)] * 20)
    if h is None or h['kind'] != 'left':
        pass     # 只閃 2 次的短暫訊號：偵測與否都可，但不能連續 3 輪都成立就一定會被回報；交給下面的單次測試
    an2 = Analyzer()
    an2.refresh([('front', box)], [], [box])
    seq = [(i in (10, 11, 12, 13), False) for i in range(25)] + [(False, False)] * 35     # 只亮一下（≈1 輪評估）
    got = None
    for i, (l, r) in enumerate(seq, 1):
        got = got or an2.push(frame(l, r), i)
    if got:
        err.append('只亮一下就被回報（應連續 3 輪才成立）')
    i, h = play([(i % 9 < 4, (i + 4) % 9 < 4) for i in range(60)])
    if h and h['kind'] == 'hazard':
        err.append('左右不同步被判成雙黃燈')
    i, h = play([(i % 9 < 4, False) for i in range(60)])
    if not h or h['kind'] != 'left':
        err.append('左方向燈 %s' % (h and h['kind']))
    i, h = play([(False, i % 9 < 4) for i in range(60)])
    if not h or h['kind'] != 'right':
        err.append('右方向燈 %s' % (h and h['kind']))
    i, h = play([(True, True)] * 60)
    if h:
        err.append('常亮被判成閃爍')
    i, h = play([(False, False)] * 60)
    if h:
        err.append('無燈被判成閃爍')
    i, h = play([(12 <= i < 17, 12 <= i < 17) for i in range(60)])
    if h:
        err.append('只亮一次被判成閃爍')
    # 車子往前開：框每秒移動一點，序列要接續（跟著車子走）
    mv = [[0.20 + 0.002 * k, 0.30 - 0.001 * k, 0.66 + 0.002 * k, 0.95 - 0.001 * k] for k in range(60)]
    i, h = play(blink, mv)
    if not h or h['kind'] != 'hazard':
        err.append('移動中的車沒偵測到雙黃燈 %s' % (h,))
    # 追蹤：框大幅跳到另一輛車時不沿用序列
    an = Analyzer()
    an.refresh([('front', box)], [], [box])
    an.refresh([('back', [0.0, 0.5, 0.45, 1.0])], [], [])
    if len(an.tracks) != 2 or an.tracks[0].miss != 1:
        err.append('不同車輛被併成同一條追蹤')
    if slot_of([0.5, 0.1, 0.95, 0.8], {'slots': {'front': {'body': [0.45, 0.0, 1.0, 0.85]}, 'back': {'body': [0.0, 0.3, 0.6, 1.0]}}}) != 'front':
        err.append('slot_of 判斷錯')
    print(json.dumps({'selftest': 'PASS' if not err else 'FAIL', 'errors': err}, ensure_ascii=False))
    return 0 if not err else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', help='即時串流（rtsp://…）')
    ap.add_argument('--clip', help='回放影片檔（整段跑完，列出所有偵測）')
    ap.add_argument('--vision')
    ap.add_argument('--max', type=float, default=45, help='即時模式最長秒數')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.url or a.clip):
        ap.error('--url or --clip required')
    try:
        out = run(a.url or a.clip, a.vision, a.max, live=bool(a.url), stop_first=bool(a.url))
    except Exception as e:  # noqa: BLE001
        out = {'blink': False, 'error': str(e)[:200]}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()

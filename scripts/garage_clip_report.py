#!/usr/bin/env python3
"""統計影片學習結果（garage_clip_learn.py 產生的 clip_frames.jsonl）：找出出門／回家事件、事件前的車燈與位移訊號領先時間、誤判率，
並輸出建議的門檻。只讀檔，不碰 HA。用法：garage_clip_report.py [--json 輸出檔]"""
import argparse
import datetime
import json
import statistics as st
from collections import Counter, defaultdict

SRC = '/config/garage_car/learn/clip_frames.jsonl'
ID_SCORE, ID_MARGIN = 0.85, 0.02
TZ = datetime.timezone(datetime.timedelta(hours=8))


def car_of(s):
    if s.get('id') and s.get('sc') is not None and s['sc'] >= ID_SCORE and (s.get('sec') is None or s['sc'] - s['sec'] >= ID_MARGIN):
        return s['id']
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json')
    a = ap.parse_args()
    clips = [json.loads(l) for l in open(SRC, encoding='utf-8') if l.strip()]
    clips = [c for c in clips if c['clip'] != 'test_first' or True]
    events, quiet_clips, sig_in_quiet = [], 0, 0
    for c in clips:
        fr = c['frames']
        if len(fr) < 4:
            continue
        had_event = False
        for sn in ('front', 'back'):
            ps = [f['s'][sn]['p'] for f in fr]
            if len(ps) < 4:
                continue
            first, last = ps[:2], ps[-2:]
            cars = Counter(car_of(f['s'][sn]) for f in fr if f['s'][sn]['p'] and car_of(f['s'][sn]))
            car = cars.most_common(1)[0][0] if cars else None
            faces = Counter(f['s'][sn].get('face') for f in fr if f['s'][sn]['p'] and f['s'][sn].get('face'))
            ev = None
            if all(first) and not any(last):
                ev = 'depart'
            elif not any(first) and all(last):
                ev = 'arrive'
            if not ev:
                continue
            had_event = True
            tz0 = c['t0']
            # 事件時間點：離開＝最後一次看到車；回家＝第一次看到車
            idx = max(i for i, p in enumerate(ps) if p) if ev == 'depart' else min(i for i, p in enumerate(ps) if p)
            t_ev = fr[idx]['t']
            # 前兆：車燈（亮度或紅色）、位移
            def firsts(key):
                for f in fr:
                    s = f['s'][sn]
                    if f['t'] > t_ev and ev == 'depart':
                        break
                    if key == 'lights' and (s['lo'] or (s.get('rd') or 0) > 0.12):
                        return f['t']
                    if key == 'moved' and s['mv']:
                        return f['t']
                return None
            cx0 = next((f['s'][sn]['cx'] for f in fr if f['s'][sn]['p']), None)
            t_shift = None
            for f in fr:
                s = f['s'][sn]
                if s['p'] and cx0 is not None and s['cx'] is not None and abs(s['cx'] - cx0) > 0.03:
                    t_shift = f['t']
                    break
            tl, tm = firsts('lights'), firsts('moved')
            events.append({'clip': c['clip'], 'time': datetime.datetime.fromtimestamp(tz0 + t_ev, TZ).strftime('%m-%d %H:%M:%S'),
                           'wd': datetime.datetime.fromtimestamp(tz0, TZ).weekday(), 'slot': sn, 'event': ev, 'car': car,
                           'face': faces.most_common(1)[0][0] if faces else None, 't_event': t_ev, 'dur': fr[-1]['t'],
                           'lights_t': tl, 'moved_t': tm, 'shift_t': t_shift,
                           'lead_lights': (t_ev - tl) if (ev == 'depart' and tl is not None) else None,
                           'lead_moved': (t_ev - tm) if (ev == 'depart' and tm is not None) else None,
                           'lead_shift': (t_ev - t_shift) if (ev == 'depart' and t_shift is not None) else None})
        if not had_event:
            quiet_clips += 1
            if any(f['s'][sn]['lo'] or f['s'][sn]['mv'] for f in fr for sn in ('front', 'back') if f['s'][sn]['p']):
                sig_in_quiet += 1
    dep = [e for e in events if e['event'] == 'depart']
    arr = [e for e in events if e['event'] == 'arrive']
    print('clips:', len(clips), '| 出門事件:', len(dep), '| 回家事件:', len(arr), '| 無事件的片段:', quiet_clips,
          '（其中有車燈／位移訊號:', sig_in_quiet, '）')
    for e in sorted(events, key=lambda x: x['time']):
        print('%s %-6s %-6s %-14s %-7s 車燈領先=%s 位移領先=%s 車身移動領先=%s' % (
            e['time'], e['event'], e['slot'], e['car'], e['face'], e['lead_lights'], e['lead_moved'], e['lead_shift']))
    for title, group in (('出門', dep), ('回家', arr)):
        by = defaultdict(list)
        for e in group:
            by[e['car']].append(e)
        for car, es in by.items():
            hrs = [int(e['time'][6:8]) for e in es]
            print('%s %s: %d 次，時段 %s，星期 %s' % (title, car, len(es), sorted(Counter(hrs).items()), sorted(Counter(e['wd'] for e in es).items())))
    ll = [e['lead_lights'] for e in dep if e['lead_lights'] is not None]
    lm = [e['lead_moved'] for e in dep if e['lead_moved'] is not None]
    ls = [e['lead_shift'] for e in dep if e['lead_shift'] is not None]
    n = max(1, len(dep))
    print('出門前兆：車燈訊號 %d/%d 次有（領先秒數 中位數 %s）；位移訊號 %d/%d（中位數 %s）；車身移動 %d/%d（中位數 %s）' % (
        len(ll), n, st.median(ll) if ll else None, len(lm), n, st.median(lm) if lm else None, len(ls), n, st.median(ls) if ls else None))
    if a.json:
        json.dump({'events': events, 'quiet_clips': quiet_clips, 'sig_in_quiet': sig_in_quiet}, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()

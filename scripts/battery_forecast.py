#!/usr/bin/env python3
"""
電池電量預估（V4.1.6，2026-10-17）
在 HA 容器內執行：python3 /config/scripts/battery_forecast.py   → 寫出 /config/battery_forecast.json
由 sensor.battery_forecast（command_line）讀取，00-2C 耗材通知與客廳門鎖預估天數共用。

做法（每台裝置）：
1. 讀長期統計（每小時平均，保留 1 年以上）＋最近 3 天的原始狀態，換算成「每日中位數」，再取 5 天移動中位數：
   一兩天的突波（例如 72→34→72）與 60/80 來回跳動都會被壓掉。同時算出裝置一次回報的「一格」大小（1～20）。
2. 換電池偵測：比目前最低點高 30 以上，或回到 95 以上（原本 ≤85）→ 新的一輪。
3. 這一輪只取「創新低」的時間點（下降點），當作電量包絡線。
4. 日耗電率 = 本輪平均（起始電量 − 目前電量 + 半格）÷ 本輪經過天數——包含最後一次下降後「一直沒掉」的時間，
   所以一次掉 20 格、之後幾個月不動的裝置不會被算成耗電很快；
   最近 60 天掉得比較快時往快的方向修正一半（電池後段通常加速）；
   有上一輪完整電池（≥60 天、掉 ≥20 格）或門鎖上一輪的日耗電率時，與之混合（本輪越久權重越高，最多 85%）。
5. 目前電量估計 = 最後一次下降後，依耗電率往下推，但不低於「最後讀數 − 一格」：
   所以就算裝置好幾天沒回報，剩餘天數也會每天遞減，不會一直卡在同一個數字。
6. 剩餘天數 = (估計電量 − 該裝置的沒電門檻) ÷ 日耗電率。
"""
import datetime, json, math, sqlite3, statistics, time

DB = 'file:/config/home-assistant_v2.db?mode=ro'
OUT = '/config/battery_forecast.json'
TZ = datetime.timezone(datetime.timedelta(hours=8))
DEVICES = [
    # k：短代碼（與 00-2C 相同）、e：電量感測器、empty：沒電門檻（%）
    {'k': 'gar', 'e': 'sensor.garage_battery', 'empty': 20, 'step': 20},   # 鐵門控制器一次只回報 20 格
    {'k': 'door', 'e': 'sensor.ke_ting_men_suo_dian_liang_guo_lu', 'empty': 10, 'prior_entity': 'input_number.doorlock_batt_drop_last_cycle'},
    {'k': 'study', 'e': 'sensor.shu_fang_gan_ying_kai_guan_battery', 'empty': 5},
    {'k': 'cube', 'e': 'sensor.0x158d00027d8a8e_battery', 'empty': 5},
    {'k': 'toiletm', 'e': 'sensor.e406bf25caa1_battery', 'empty': 5},
    {'k': 'kitchenm', 'e': 'sensor.08b95f06b466_battery', 'empty': 5},
    {'k': 'garstair', 'e': 'sensor.e406bf25cfea_battery', 'empty': 5},
    {'k': 'bell', 'e': 'sensor.0x00158d0002419b84_battery', 'empty': 5},
    {'k': 'kswitch', 'e': 'sensor.0x00158d00023cd3dc_battery', 'empty': 5},
]
DAY = 86400.0


def theil_sen(pts):
    """pts: [(t_days, v)] → slope (%/day), None if not enough"""
    sl = [(pts[j][1] - pts[i][1]) / (pts[j][0] - pts[i][0]) for i in range(len(pts)) for j in range(i + 1, len(pts)) if pts[j][0] - pts[i][0] > 0.5]
    return statistics.median(sl) if sl else None


def daily_series(c, entity):
    m = c.execute('select id from statistics_meta where statistic_id=?', (entity,)).fetchone()
    by_day = {}
    distinct = set()
    cutoff = time.time() - 180 * DAY
    if m:
        for ts, mean, mn, mx in c.execute('select start_ts, mean, min, max from statistics where metadata_id=? order by start_ts', (m[0],)):
            v = mean if mean is not None else mn
            if v is None or not (0 <= v <= 100):
                continue
            d = datetime.datetime.fromtimestamp(ts, TZ).date()
            by_day.setdefault(d, []).append(v)
            if ts >= cutoff:
                for x in (mn, mx):
                    if x is not None and 1 <= x <= 100:
                        distinct.add(round(x))
    # recent raw states (cover the hours not yet in long-term statistics)
    sm = c.execute('select metadata_id from states_meta where entity_id=?', (entity,)).fetchone()
    now_v, now_since = None, None
    if sm:
        rows = c.execute('select state, last_updated_ts from states where metadata_id=? and last_updated_ts > ? order by last_updated_ts', (sm[0], time.time() - 3 * DAY)).fetchall()
        for st, ts in rows:
            try:
                v = float(st)
            except (TypeError, ValueError):
                continue
            if 0 <= v <= 100:
                d = datetime.datetime.fromtimestamp(ts, TZ).date()
                by_day.setdefault(d, []).append(v)
                if v != now_v:
                    now_since = ts
                now_v = v
                if 1 <= v <= 100:
                    distinct.add(round(v))
    raw = []
    for d in sorted(by_day):
        noon = datetime.datetime(d.year, d.month, d.day, 12, tzinfo=TZ).timestamp() / DAY
        raw.append((noon, statistics.median(by_day[d])))
    # 5-day rolling median (trailing at the end): one- or two-day dips/flaps disappear
    out = []
    for i in range(len(raw)):
        win = [v for _, v in raw[max(0, i - 2):i + 3]]
        out.append((raw[i][0], statistics.median(win)))
    # reporting step ("one notch"): smallest gap between the distinct values reported in the last 180 days (1…20)
    dv = sorted(distinct)
    gaps = [dv[i + 1] - dv[i] for i in range(len(dv) - 1) if dv[i + 1] - dv[i] >= 1]
    step = float(max(1, min(20, min(gaps)))) if gaps else 1.0
    return out, (now_v, now_since), step


def segments(daily):
    segs, cur = [], None
    for t, v in daily:
        if cur is None:
            cur = {'start': t, 'v0': v, 'pts': [(t, v)], 'env': v, 'last': t}
            continue
        if v >= cur['env'] + 30 or (v >= 95 and cur['env'] <= 85):
            segs.append(cur)
            cur = {'start': t, 'v0': v, 'pts': [(t, v)], 'env': v, 'last': t}
            continue
        if v < cur['env'] - 0.5:
            cur['env'] = v
            cur['pts'].append((t, v))
        cur['last'] = t
    if cur:
        segs.append(cur)
    return segs


def prior_from(seg):
    # only a real previous battery (≥ 60 days, dropped ≥ 20 points) is trusted; short junk segments around a swap are ignored
    span = seg['last'] - seg['start']
    drop = seg['v0'] - seg['env']
    if len(seg['pts']) >= 3 and span >= 60 and drop >= 20:
        return drop / span
    return None


def env_at(pts, t):
    v = pts[0][1]
    for pt, pv in pts:
        if pt <= t:
            v = pv
    return v


def forecast(c, dev, now_d, states_now):
    daily, (now_v, now_since), step = daily_series(c, dev['e'])
    step = float(dev.get('step', step))
    if not daily:
        return {'status': 'nodata'}
    segs = segments(daily)
    cur = segs[-1]
    # the smoothed series lags 2 days; a fresh, plausible drop that has held for ≥ 6 h counts right away
    if now_v is not None and now_since and now_v < cur['env'] - 0.5 and cur['env'] - now_v <= max(3 * step, 10) \
            and time.time() - now_since >= 6 * 3600:
        cur['env'] = now_v
        cur['pts'].append((now_since / DAY, now_v))
    prior = prior_from(segs[-2]) if len(segs) >= 2 else None
    prior_src = 'last_cycle' if prior else None
    if prior is None and dev.get('prior_entity'):
        try:
            p = float(states_now.get(dev['prior_entity'], 'x'))
            if p > 0:
                prior, prior_src = p, dev['prior_entity']
        except ValueError:
            pass
    pts = cur['pts']
    span = now_d - cur['start']
    n_drops = len(pts) - 1
    level = cur['env']
    res = {'level': round(level, 1), 'reported': now_v, 'seg_start': datetime.datetime.fromtimestamp(cur['start'] * DAY, TZ).strftime('%Y-%m-%d'),
           'span_days': round(span, 1), 'drops': n_drops, 'empty': dev['empty']}
    if level <= dev['empty']:
        res.update({'status': 'empty', 'days': 0})
        return res
    if n_drops == 0:
        res.update({'status': 'stable' if span >= 30 else 'learning', 'days': None})
        return res
    q = step
    # whole-cycle average INCLUDING the quiet time since the last drop (half a step for the unseen part of the current step):
    # a device that dropped once and then stayed flat for months is not draining fast
    cur_rate = (cur['v0'] - level + q / 2) / max(span, 1.0)
    rate = cur_rate
    recent_rate = None
    if span >= 60:
        lvl60 = env_at(pts, now_d - 60)
        if lvl60 - level >= min(q, 3):
            recent_rate = (lvl60 - level + q / 2) / 60.0
            if recent_rate > rate:                       # batteries usually speed up near the end
                rate = (rate + recent_rate) / 2
    if prior:
        w = min(0.85, span / 180.0)
        rate = w * rate + (1 - w) * prior
    rate = max(rate, 0.01)
    t_last = pts[-1][0]
    est = max(level - rate * (now_d - t_last), level - q)
    days = min(max(0.0, (est - dev['empty']) / rate), 1095.0)      # cap at 3 years (shown as "3 年以上")
    conf = 'high' if n_drops >= 4 and span >= 30 else ('mid' if n_drops >= 2 and span >= 10 else 'low')
    res.update({'status': 'ok', 'rate': round(rate, 4), 'cur_rate': round(cur_rate, 4), 'recent_rate': round(recent_rate, 4) if recent_rate else None,
                'prior_rate': round(prior, 4) if prior else None, 'prior_src': prior_src, 'step': round(q, 1), 'est_level': round(est, 1),
                'days': round(days, 1), 'date': datetime.datetime.fromtimestamp((now_d + days) * DAY, TZ).strftime('%Y-%m-%d'), 'conf': conf})
    return res


def main():
    c = sqlite3.connect(DB, uri=True, timeout=30)
    now_d = time.time() / DAY
    states_now = {}
    for d in DEVICES:
        if d.get('prior_entity'):
            sm = c.execute('select metadata_id from states_meta where entity_id=?', (d['prior_entity'],)).fetchone()
            if sm:
                r = c.execute('select state from states where metadata_id=? order by last_updated_ts desc limit 1', (sm[0],)).fetchone()
                if r:
                    states_now[d['prior_entity']] = r[0]
    items = {}
    for d in DEVICES:
        try:
            items[d['k']] = dict(forecast(c, d, now_d, states_now), entity=d['e'])
        except Exception as e:  # one bad device must not break the others
            items[d['k']] = {'status': 'error', 'error': str(e)[:120], 'entity': d['e']}
    out = {'updated': datetime.datetime.now(TZ).strftime('%Y-%m-%d %H:%M'), 'items': items}
    with open(OUT + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    import os
    os.replace(OUT + '.tmp', OUT)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

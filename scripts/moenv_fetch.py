#!/usr/bin/env python3
"""
環境部開放資料（V4.1.6，2026-10-18）
在 HA 容器內執行：python3 /config/scripts/moenv_fetch.py   → 寫出 /config/moenv_air.json（由 sensor.moenv_air 讀取）
API 金鑰放在 /config/secrets.yaml 的 moenv_api_key（不進 git）。

資料：
- aqx_p_432  空氣品質指標（AQI）即時：取離家最近的測站（頭份，siteid 25；資料失效退回苗栗 26、竹東 23），含 PM2.5／PM10／O3／NO2／SO2／CO、風速風向、主要污染物。
- uv_s_01    紫外線指數（氣象署）：取後龍站最近一筆有效值（夜間為 -999，用最近一次有效值並註明時間）。
- aqf_p_01   空氣品質預報：竹苗空品區，今日～後天的預報 AQI 與主要污染物。
data.moenv.gov.tw 的憑證缺 Subject Key Identifier，Python 3.13+ 預設嚴格檢查會失敗；這裡只關掉 VERIFY_X509_STRICT，憑證鏈與主機名稱仍然驗證。
抓不到時保留上一次的資料並標示 stale。
"""
import datetime, json, os, ssl, time, urllib.request

OUT = '/config/moenv_air.json'
SECRETS = '/config/secrets.yaml'
TZ = datetime.timezone(datetime.timedelta(hours=8))
STATIONS = ['25', '26', '23']          # 頭份、苗栗、竹東（依距離）
UV_SITE = '後龍'
AREA = '竹苗'


def key():
    for l in open(SECRETS, encoding='utf-8'):
        if l.startswith('moenv_api_key'):
            return l.split(':', 1)[1].strip()
    raise RuntimeError('moenv_api_key not in secrets.yaml')


def api(ds, extra=''):
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    url = 'https://data.moenv.gov.tw/api/v2/%s?api_key=%s&format=json%s' % (ds, key(), extra)
    last = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (HomeAssistant)', 'Accept': 'application/json'})
            d = json.loads(urllib.request.urlopen(req, timeout=40, context=ctx).read().decode('utf-8'))
            return d if isinstance(d, list) else d.get('records', [])
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


def num(v):
    try:
        x = float(v)
        return None if x <= -900 else x
    except (TypeError, ValueError):
        return None


def aqi_level(a):
    if a is None:
        return None
    return 1 if a <= 50 else 2 if a <= 100 else 3 if a <= 150 else 4 if a <= 200 else 5 if a <= 300 else 6


def main():
    prev = {}
    if os.path.exists(OUT):
        try:
            prev = json.load(open(OUT, encoding='utf-8'))
        except Exception:
            prev = {}
    out = dict(prev)
    out['updated'] = datetime.datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    errs = []
    # ---- AQI ----
    try:
        recs = api('aqx_p_432', '&limit=100')
        by = {r.get('siteid'): r for r in recs}
        pick = None
        for sid in STATIONS:
            r = by.get(sid)
            if r and num(r.get('aqi')) is not None and num(r.get('pm2.5')) is not None:
                pick = r
                break
        if pick:
            a = num(pick.get('aqi'))
            out['aq'] = {'ok': True, 'station': pick.get('sitename'), 'county': pick.get('county'), 'aqi': a, 'level': aqi_level(a), 'status': pick.get('status'),
                         'pollutant': pick.get('pollutant') or '', 'pm25': num(pick.get('pm2.5')), 'pm10': num(pick.get('pm10')), 'pm25_avg': num(pick.get('pm2.5_avg')),
                         'pm10_avg': num(pick.get('pm10_avg')), 'o3': num(pick.get('o3')), 'no2': num(pick.get('no2')), 'so2': num(pick.get('so2')), 'co': num(pick.get('co')),
                         'wind_speed': num(pick.get('wind_speed')), 'wind_direc': num(pick.get('wind_direc')), 'time': pick.get('publishtime'), 'stale': False}
        else:
            errs.append('aqi: no station with data')
    except Exception as e:
        errs.append('aqi: %s %s' % (type(e).__name__, str(e)[:80]))
    # ---- UV ----
    try:
        recs = [r for r in api('uv_s_01', '&limit=300') if r.get('sitename') == UV_SITE]
        recs.sort(key=lambda r: r.get('datacreationdate', ''), reverse=True)
        good = [r for r in recs if num(r.get('uvi')) is not None]
        if good:
            out['uv'] = {'ok': True, 'site': UV_SITE, 'uvi': num(good[0]['uvi']), 'time': good[0].get('datacreationdate'), 'latest_time': recs[0].get('datacreationdate')}
    except Exception as e:
        errs.append('uv: %s %s' % (type(e).__name__, str(e)[:80]))
    # ---- forecast ----
    try:
        recs = [r for r in api('aqf_p_01', '&limit=300') if r.get('area') == AREA]
        latest = {}
        for r in recs:
            d = r.get('forecastdate')
            if d and (d not in latest or r.get('publishtime', '') > latest[d].get('publishtime', '')):
                latest[d] = r
        fc = []
        today = datetime.datetime.now(TZ).strftime('%Y-%m-%d')
        for d in [x for x in sorted(latest) if x >= today][:4]:
            r = latest[d]
            fc.append({'date': d, 'aqi': num(r.get('aqi')), 'major': r.get('majorpollutant') or '', 'minor': r.get('minorpollutant') or '', 'publish': r.get('publishtime')})
        if fc:
            out['forecast'] = fc
    except Exception as e:
        errs.append('forecast: %s %s' % (type(e).__name__, str(e)[:80]))
    out['errors'] = errs
    out['ok'] = bool(out.get('aq', {}).get('ok')) and not any(e.startswith('aqi') for e in errs)
    if errs and out.get('aq'):
        out['aq']['stale'] = any(e.startswith('aqi') for e in errs)
    with open(OUT + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    os.replace(OUT + '.tmp', OUT)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])


if __name__ == '__main__':
    main()

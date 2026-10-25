#!/usr/bin/env python3
"""查氣象署地震報告，挑出與預警時間最接近的一筆，並把報告圖與震度分布圖存到本機（SOP-24）。
資料集：E-A0015-001（顯著有感地震報告）、E-A0016-001（小區域有感地震報告）。授權碼放 /config/secrets.yaml 的 cwa_api_key。
用法：cwa_quake.py <預警時間 epoch> <容許分鐘> <圖片輸出資料夾> <圖片網址前綴>
輸出：一行 JSON；ok=true 時含 time／epicenter／lat／lon／mag／depth／max_int／areas／report_img／shake_img，否則 ok=false 與 reason。
"""
import sys, json, re, os, glob, time, random, datetime, ssl, struct, urllib.request, urllib.parse

SECRETS = '/config/secrets.yaml'
DATASETS = ['E-A0015-001', 'E-A0016-001']
TW = datetime.timezone(datetime.timedelta(hours=8))
# 氣象署憑證缺 Subject Key Identifier，Python 3.13 以後預設的嚴格檢查會拒絕；仍然驗證憑證鏈，只關掉 X509 嚴格模式
CTX = ssl.create_default_context()
CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT


def out(d):
    print(json.dumps(d, ensure_ascii=False))
    sys.exit(0)


def api_key():
    try:
        for line in open(SECRETS, encoding='utf-8'):
            m = re.match(r'\s*cwa_api_key\s*:\s*["\']?([^"\'#\s]+)', line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return ''


def fetch(ds, key):
    url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/%s?%s' % (
        ds, urllib.parse.urlencode({'Authorization': key, 'format': 'JSON', 'limit': 10}))
    with urllib.request.urlopen(url, timeout=20, context=CTX) as r:
        d = json.load(r)
    rec = d.get('records') or {}
    return rec.get('Earthquake') or []


def origin_epoch(e):
    t = ((e.get('EarthquakeInfo') or {}).get('OriginTime') or '').strip()
    try:
        d = datetime.datetime.fromisoformat(t.replace(' ', 'T'))
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=TW)).timestamp()


def rank(s):
    m = re.search(r'(\d)\s*(弱|強)?', str(s))
    return (int(m.group(1)) + (0.5 if m.group(2) == '強' else 0)) if m else -1


def png_ratio(path):
    try:
        with open(path, 'rb') as f:
            h = f.read(24)
        if h[:8] == b'\x89PNG\r\n\x1a\n':
            w, hh = struct.unpack('>II', h[16:24])
            return '%d:%d' % (w, hh) if w and hh and 1 / 3 <= w / hh <= 3 else ''
    except OSError:
        pass
    return ''


def download(url, outdir, prefix, tag):
    if not url:
        return ''
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    ext = ext if ext in ('.png', '.jpg', '.jpeg', '.gif') else '.png'
    name = 'snap_quake_%s_%s%s' % (tag, ''.join(random.choice('abcdef0123456789') for _ in range(16)), ext)
    try:
        with urllib.request.urlopen(url, timeout=25, context=CTX) as r, open(os.path.join(outdir, name), 'wb') as f:
            f.write(r.read())
    except Exception:
        return ''
    return prefix + name


def main():
    if len(sys.argv) < 5:
        out({'ok': False, 'reason': 'usage'})
    t0, win, outdir, prefix = float(sys.argv[1]), float(sys.argv[2]) * 60, sys.argv[3], sys.argv[4]
    key = api_key()
    if not key:
        out({'ok': False, 'reason': 'no_key'})
    best = None
    for ds in DATASETS:
        try:
            quakes = fetch(ds, key)
        except Exception as ex:
            out({'ok': False, 'reason': 'fetch_error', 'detail': str(ex)[:120]})
        for e in quakes:
            o = origin_epoch(e)
            if o is None or abs(t0 - o) > win:
                continue
            if best is None or abs(t0 - o) < abs(t0 - best[0]):
                best = (o, e)
    for old in glob.glob(os.path.join(outdir, 'snap_quake_*')):       # 3 天前的舊圖清掉
        try:
            if time.time() - os.path.getmtime(old) > 3 * 86400:
                os.remove(old)
        except OSError:
            pass
    if best is None:
        out({'ok': False, 'reason': 'no_match'})
    o, e = best
    info = e.get('EarthquakeInfo') or {}
    epi = info.get('Epicenter') or {}
    mag = (info.get('EarthquakeMagnitude') or {}).get('MagnitudeValue')
    cities = {}
    for a in ((e.get('Intensity') or {}).get('ShakingArea') or []):
        c, v = a.get('CountyName'), a.get('AreaIntensity')
        if c and '、' not in c and v is not None and rank(v) > rank(cities.get(c, '')):
            cities[c] = str(v)
    areas = sorted(cities.items(), key=lambda kv: -rank(kv[1]))
    tag = datetime.datetime.fromtimestamp(o, TW).strftime('%m%d%H%M')
    ri = download(e.get('ReportImageURI'), outdir, prefix, tag + 'r')
    si = download(e.get('ShakemapImageURI'), outdir, prefix, tag + 's')
    out({'ok': True,
         'time': datetime.datetime.fromtimestamp(o, TW).strftime('%m/%d %H:%M:%S'),
         'epicenter': re.sub(r'\s+', '', epi.get('Location') or epi.get('EpicenterLocation') or info.get('EpicenterLocation') or ''),
         'lat': epi.get('EpicenterLatitude'), 'lon': epi.get('EpicenterLongitude'),
         'mag': mag, 'depth': info.get('FocalDepth'),
         'max_int': areas[0][1] if areas else '',
         'areas': [{'county': c, 'int': v} for c, v in areas[:6]],
         'content': e.get('ReportContent') or '',
         'report_img': ri, 'report_ratio': png_ratio(os.path.join(outdir, ri.rsplit('/', 1)[-1])) if ri else '',
         'shake_img': si, 'shake_ratio': png_ratio(os.path.join(outdir, si.rsplit('/', 1)[-1])) if si else ''})


main()
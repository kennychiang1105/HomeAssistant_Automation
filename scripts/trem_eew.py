#!/usr/bin/env python3
"""TREM（ExpTech）即時預警客戶端（SOP-24）：連公開的 EEW 串流（不需金鑰），算出竹南的預估震度與抵達秒數，
有警報就呼叫 HA 區網 webhook（→ script.eq99，source=TREM；多來源去重由 eq99 處理）。
  串流：https://api.lb.exptech.dev/api/v2/eq/eew?sse=1（SSE，每個 data 是目前有效的預警陣列；失敗時退回每 2 秒輪詢同網址）
  每筆預警欄位：id、serial、status（1 警報、3 取消）、final、author、eq{lat,lon,depth,mag,max,time,loc}
  預估震度：CWA 近場衰減式 PGA=1.657·e^(1.533M)·R^-1.607（R＝震源距，公里；gal）再對照中央氣象署震度分級；S 波 3.5 km/s。
  常駐於 HA 容器（shell_command.trem_eew_start 啟動，看門狗每 5 分鐘確認心跳）。單一執行個體（pid 檔）。
"""
import json, math, os, re, socket, sys, time, urllib.request, urllib.error, datetime

SITE = (24.6856, 120.8794)          # 竹南鎮
MIN_LEVEL = 2                       # 低於此預估震度不通知（與地牛 add-on 門檻一致）
VS = 3.5                            # S 波速度 km/s
STREAM = 'https://api.lb.exptech.dev/api/v2/eq/eew'
SECRETS = '/config/secrets.yaml'
LOG = '/config/trem_eew.log'
PID = '/config/.trem_eew.pid'
HA = 'http://127.0.0.1:8125/api/webhook/'
GAL = [(800, 7), (440, 6), (250, 6), (140, 5), (80, 5), (25, 4), (8, 3), (2.5, 2), (0.8, 1)]


def log(msg):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > 300000:
            os.replace(LOG, LOG + '.1')
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write('%s %s\n' % (datetime.datetime.now().strftime('%F %T'), msg))
    except OSError:
        pass


def hook_id():
    for line in open(SECRETS, encoding='utf-8'):
        m = re.match(r'\s*eew_oxwu_alert_hook\s*:\s*(\S+)', line)
        if m:
            return m.group(1)
    raise SystemExit('secrets.yaml 缺 eew_oxwu_alert_hook')


def post(payload):
    req = urllib.request.Request(HA + hook_id(), data=json.dumps(payload, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=8).read()
        return True
    except Exception as e:
        log('post failed: %s' % e)
        return False


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def estimate(eq):
    d = hav(SITE[0], SITE[1], float(eq['lat']), float(eq['lon']))
    r = max(math.hypot(d, float(eq.get('depth') or 10)), 1.0)
    pga = 1.657 * math.exp(1.533 * float(eq['mag'])) * r ** -1.607
    lv = next((l for g, l in GAL if pga >= g), 0)
    t0 = float(eq['time']) / 1000.0
    return lv, t0 + r / VS, r


def alive():
    try:
        pid = int(open(PID).read().strip())
        os.kill(pid, 0)
        return pid != os.getpid() and 'trem_eew' in open('/proc/%d/cmdline' % pid).read()
    except (OSError, ValueError):
        return False


def handle(items, seen):
    now = time.time()
    for e in items or []:
        try:
            eid, eq = e['id'], e['eq']
            if e.get('status') == 3:
                continue
            lv, arrive, r = estimate(eq)
            sent = seen.get(eid, -1)
            if lv >= MIN_LEVEL and lv > sent:
                secs = max(0, int(arrive - now))
                ok = post({'source': 'TREM', 'level': str(lv), 'seconds': str(secs), 'timestamp': str(int(arrive)),
                           'loc': eq.get('loc', ''), 'mag': eq.get('mag'), 'depth': eq.get('depth'), 'lat': eq.get('lat'),
                           'lon': eq.get('lon'), 'id': eid, 'serial': e.get('serial')})
                log('EEW %s #%s M%s %s -> 竹南 預估%s級 %s秒 (R=%.0fkm) post=%s' % (eid, e.get('serial'), eq.get('mag'), eq.get('loc'), lv, secs, r, ok))
                seen[eid] = lv
            elif eid not in seen:
                seen[eid] = max(lv, 0) if lv < MIN_LEVEL else lv
                log('EEW %s #%s M%s %s 竹南預估%s級（低於門檻，不通知）' % (eid, e.get('serial'), eq.get('mag'), eq.get('loc'), lv))
        except Exception as ex:
            log('handle error: %s %s' % (type(ex).__name__, ex))
    for k in [k for k, _ in seen.items() if k not in {x.get('id') for x in items or []}]:
        if len(seen) > 50:
            seen.pop(k, None)


def run():
    seen, last_beat, fails, connected_once = {}, 0, 0, False
    while True:
        try:
            req = urllib.request.Request(STREAM + '?sse=1', headers={'Accept': 'text/event-stream', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req, timeout=40) as r:
                if fails or not connected_once:
                    log('SSE connected')
                fails, connected_once = 0, True
                ev = ''
                while True:
                    line = r.readline()
                    if not line:
                        break
                    s = line.decode('utf-8', 'ignore').rstrip('\r\n')
                    if s.startswith('event:'):
                        ev = s[6:].strip()
                    elif s.startswith('data:') and ev != 'info':
                        try:
                            data = json.loads(s[5:].strip())
                        except ValueError:
                            continue
                        handle(data if isinstance(data, list) else [data], seen)
                    elif s == '':
                        ev = ''
                    if time.time() - last_beat > 60:
                        post({'source': 'TREM', 'heartbeat': 1}); last_beat = time.time()
        except (TimeoutError, socket.timeout):          # 40 秒沒有任何資料只是閒置：立刻重連，不算錯誤
            if time.time() - last_beat > 60:
                post({'source': 'TREM', 'heartbeat': 1}); last_beat = time.time()
            continue
        except Exception as ex:
            fails += 1
            log('stream error (%d): %s' % (fails, ex))
        # 串流斷線：改輪詢同網址幾次再重連
        for _ in range(3 if fails < 5 else 10):
            try:
                with urllib.request.urlopen(STREAM, timeout=10) as r:
                    handle(json.loads(r.read().decode()), seen)
            except Exception as ex:
                log('poll error: %s' % ex)
            if time.time() - last_beat > 60:
                post({'source': 'TREM', 'heartbeat': 1}); last_beat = time.time()
            time.sleep(2)
        time.sleep(min(3 * fails, 30))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':          # 只計算、不通知：trem_eew.py --test 緯度 經度 規模 深度
        lat, lon, mag, dep = map(float, sys.argv[2:6])
        lv, arr, r = estimate({'lat': lat, 'lon': lon, 'mag': mag, 'depth': dep, 'time': time.time() * 1000})
        print(json.dumps({'level': lv, 'seconds': round(arr - time.time(), 1), 'R_km': round(r, 1)}))
        sys.exit(0)
    if alive():
        sys.exit(0)
    open(PID, 'w').write(str(os.getpid()))
    log('started pid %d' % os.getpid())
    run()
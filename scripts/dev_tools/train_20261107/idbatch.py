"""在 HA 容器內執行：把 /config/.idtest/*.jpg 逐張送 Garage Vision（含車牌、occ），結果寫 /config/.idtest/out.jsonl。每張之間休息 0.4 秒，避免拖慢即時分析。"""
import json, os, time, urllib.request, glob
roi = json.load(open('/config/garage_roi.json', encoding='utf-8'))
q = 'slots=' + ';'.join('%s=%s' % (n, ','.join(str(x) for x in s['body'])) for n, s in roi['slots'].items()) + '&occ=1'
D = '/config/.idtest'
outp = os.path.join(D, 'out.jsonl')
done = set()
if os.path.exists(outp):
    done = {json.loads(l)['name'] for l in open(outp) if l.strip()}
fs = sorted(glob.glob(D + '/g_*.jpg'))
with open(outp, 'a') as f:
    for i, p in enumerate(fs):
        n = os.path.basename(p)
        if n in done:
            continue
        try:
            req = urllib.request.Request('http://local-garage-vision:8099/analyze?' + q, data=open(p, 'rb').read(), method='POST', headers={'Content-Type': 'image/jpeg'})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
            slots = {k: {'det': v.get('det'), 'id': v.get('id'), 'occ': v.get('occ'), 'type': v.get('type')} for k, v in (d.get('slots') or {}).items()}
            f.write(json.dumps({'name': n, 'plates': d.get('plates'), 'slots': slots, 'persons': d.get('persons'), 'ms': d.get('ms')}) + '\n')
            f.flush()
        except Exception as e:  # noqa: BLE001
            f.write(json.dumps({'name': n, 'error': str(e)[:100]}) + '\n')
        time.sleep(0.4)
open(os.path.join(D, 'DONE'), 'w').write(str(len(fs)))

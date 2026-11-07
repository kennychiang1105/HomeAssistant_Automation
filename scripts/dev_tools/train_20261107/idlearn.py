"""在 HA 容器內：依 /config/.idtest/id_learn.json 把畫面送 add-on /learn 補學身分樣板。"""
import json, urllib.request
roi = json.load(open('/config/garage_roi.json', encoding='utf-8'))
sq = 'slots=' + ';'.join('%s=%s' % (n, ','.join(str(x) for x in s['body'])) for n, s in roi['slots'].items())
items = json.load(open('/config/.idtest/id_learn.json'))
for it in items:
    q = 'slot=%s&label=%s&%s' % (it['slot'], it['label'], sq)
    req = urllib.request.Request('http://local-garage-vision:8099/learn?' + q, data=open('/config/.idtest/' + it['name'], 'rb').read(), method='POST', headers={'Content-Type': 'image/jpeg'})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        print(it['name'], it['slot'], it['label'], '->', r.get('learned'), 'gallery', r.get('gallery'))
    except Exception as e:  # noqa: BLE001
        print(it['name'], it['slot'], it['label'], 'ERROR', str(e)[:100])

import json, cv2, numpy as np, sys
rows = {json.loads(l)['name']: json.loads(l) for l in open(r'C:\ai_lab\garage\id_out.jsonl', encoding='utf-8') if l.strip()}
names = sys.argv[2:]
tiles = []
for n in names:
    im = cv2.imread(r'C:\ai_lab\garage\frames3\%s' % n)
    H, W = im.shape[:2]
    r = rows.get(n, {})
    for k, v in (r.get('slots') or {}).items():
        d = v.get('det')
        if d:
            b = d['box']
            col = (0, 255, 0) if k == 'front' else (255, 128, 0)
            cv2.rectangle(im, (int(b[0] * W), int(b[1] * H)), (int(b[2] * W), int(b[3] * H)), col, 3)
            idr = v.get('id') or {}
            cv2.putText(im, '%s %s %.3f/%s' % (k, idr.get('label', ''), idr.get('score', 0), idr.get('second')), (int(b[0] * W) + 5, int(b[1] * H) + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, col, 2)
    for p in r.get('plates') or []:
        cv2.putText(im, p['text'], (int(p['cx'] * W) - 40, int(p['cy'] * H) - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    c = cv2.resize(im, (640, 360))
    cv2.putText(c, n[2:13], (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    tiles.append(c)
while len(tiles) % 3:
    tiles.append(np.zeros((360, 640, 3), np.uint8))
cv2.imwrite(sys.argv[1], np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 80])
print('ok', len(names))

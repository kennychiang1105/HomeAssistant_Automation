import json, cv2, numpy as np
rows = {json.loads(l)['name']: json.loads(l) for l in open(r'C:\ai_lab\garage\id_out.jsonl', encoding='utf-8') if l.strip()}
items = json.load(open(r'C:\ai_lab\garage\id_learn.json'))
tiles = []
for it in items:
    im = cv2.imread(r'C:\ai_lab\garage\frames3\%s' % it['name'])
    H, W = im.shape[:2]
    b = rows[it['name']]['slots'][it['slot']]['det']['box']
    cv2.rectangle(im, (int(b[0] * W), int(b[1] * H)), (int(b[2] * W), int(b[3] * H)), (0, 255, 0), 4)
    c = cv2.resize(im, (480, 270))
    cv2.rectangle(c, (0, 0), (480, 22), (0, 0, 0), -1)
    cv2.putText(c, '%s %s -> %s' % (it['name'][2:13], it['slot'], it['label']), (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    tiles.append(c)
cv2.imwrite(r'C:\ai_lab\garage\id_tpl.jpg', np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 80])
print('ok')

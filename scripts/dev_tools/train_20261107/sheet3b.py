"""依類別抽樣拼圖：sheet3b.py <slot> <cat> [n] [full]
cat：fp_empty（p<=0.1 但 YOLO 有車）、fn_occ（p>=0.9 但 YOLO 沒車）、unsure1（0.1~0.9 且 YOLO 有車）、unsure0（0.1~0.9 且 YOLO 沒車）
full：顯示整張畫面縮圖（框出車位），否則只裁車位"""
import json, cv2, numpy as np, sys
slot, cat = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 36
full = 'full' in sys.argv
rows = json.load(open(r'C:\ai_lab\garage\eval3.json'))
roi = json.load(open(r'C:\ai_lab\garage\garage_roi.json', encoding='utf-8'))
b = roi['slots'][slot]['body']
f = {'fp_empty': lambda p, y: p <= 0.1 and y, 'fn_occ': lambda p, y: p >= 0.9 and not y,
     'unsure1': lambda p, y: 0.1 < p < 0.9 and y, 'unsure0': lambda p, y: 0.1 < p < 0.9 and not y}[cat]
items = [r for r in rows if f(*r[slot])]
json.dump([r['name'] for r in items], open(r'C:\ai_lab\garage\cat_%s_%s.json' % (slot, cat), 'w'))
step = max(1, len(items) / n)
sel = [items[int(i * step)] for i in range(min(n, len(items)))]
tiles = []
for r in sel:
    im = cv2.imread(r'C:\ai_lab\garage\frames3\%s' % r['name'])
    H, W = im.shape[:2]
    if full:
        cv2.rectangle(im, (int(b[0] * W), int(b[1] * H)), (int(b[2] * W), int(b[3] * H)), (0, 255, 0), 3)
        c = cv2.resize(im, (320, 180))
    else:
        c = cv2.resize(im[int(b[1] * H):int(b[3] * H), int(b[0] * W):int(b[2] * W)], (300, 220))
    cv2.rectangle(c, (0, 0), (c.shape[1], 16), (0, 0, 0), -1)
    cv2.putText(c, '%s p=%.2f y=%d' % (r['name'][2:13], r[slot][0], int(r[slot][1])), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1)
    tiles.append(c)
h, w = tiles[0].shape[:2]
while len(tiles) % 6:
    tiles.append(np.zeros((h, w, 3), np.uint8))
out = r'C:\ai_lab\garage\sheet_%s_%s.jpg' % (slot, cat)
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 80])
print(cat, slot, 'total', len(items), 'shown', len(sel), out)

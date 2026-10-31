import json, cv2, numpy as np, sys
slot = sys.argv[1]
rows = json.load(open(r'C:\ai_lab\garage\new_eval.json'))
roi = json.load(open(r'C:\ai_lab\garage\garage_roi.json', encoding='utf-8'))
b = roi['slots'][slot]['body']
dis = [r for r in rows if (r[slot][0] > 0.5) != r[slot][1]]
step = max(1, len(dis) // 30)
sel = dis[::step][:30]
tiles = []
for r in sel:
    im = cv2.imread(r'C:\ai_lab\garage\frames2\%s' % r['name'])
    H, W = im.shape[:2]
    c = cv2.resize(im[int(b[1] * H):int(b[3] * H), int(b[0] * W):int(b[2] * W)], (260, 200))
    cv2.putText(c, '%s clf=%.2f yolo=%d' % (r['name'][2:11], r[slot][0], int(r[slot][1])), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    tiles.append(c)
while len(tiles) % 6:
    tiles.append(np.zeros((200, 260, 3), np.uint8))
rows_img = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
cv2.imwrite(r'C:\ai_lab\garage\dis_%s.jpg' % slot, np.vstack(rows_img), [cv2.IMWRITE_JPEG_QUALITY, 80])
print(len(dis), 'shown', len(sel))

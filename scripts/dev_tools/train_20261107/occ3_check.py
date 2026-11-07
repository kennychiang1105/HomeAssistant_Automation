"""未標註（模稜兩可）的新畫面：新模型（留一日）變得很有把握的，拼圖看合不合理。"""
import numpy as np, json, cv2
exec(open(r'C:\ai_lab\garage\occ3.py', encoding='utf-8').read().split("out = {}")[0])
for slot in ('front', 'back'):
    R = roi['slots'][slot]['body']
    lab = np.array(cl[slot]); y1 = np.full(len(lab), -1)
    for c in occ[slot]: y1[lab == c] = 1
    for c in emp[slot]: y1[lab == c] = 0
    X1, Y1 = d1[slot][y1 >= 0], y1[y1 >= 0]
    y2 = np.array([0 if rows2[n][slot][0] < 0.1 else 1 if rows2[n][slot][0] > 0.9 else (1 if 0.2 < rows2[n][slot][0] < 0.8 else -1) for n in d2['names']])
    X2, Y2 = d2[slot][y2 >= 0], y2[y2 >= 0]
    y3 = []
    for n in names3:
        p = rows3[n][slot][0]
        boxes = [x['box'] for x in P3[n].get('ft960', []) if x['cls'] == 'car' and x['conf'] >= 0.5]
        parked = any(R[0] <= (b[0] + b[2]) / 2 <= R[2] and R[1] <= (b[1] + b[3]) / 2 <= R[3] and cover(b, R) >= 0.5 for b in boxes)
        y3.append(1 if p >= 0.9 else 0 if p <= 0.1 else (1 if parked else -1))
    y3 = np.array(y3); X3 = d3[slot]
    pn = np.zeros(len(names3))
    for dday in sorted(set(days3)):
        te = days3 == dday
        tr3 = (~te) & (y3 >= 0)
        clf = LogisticRegression(C=10, max_iter=5000, class_weight='balanced').fit(np.vstack([X1, X2, X3[tr3]]), np.concatenate([Y1, Y2, y3[tr3]]))
        pn[te] = clf.predict_proba(X3[te])[:, 1]
    po = prob(old[slot], X3)
    un = np.where(y3 < 0)[0]
    ch = [i for i in un if (pn[i] >= 0.8 or pn[i] <= 0.2) and not (po[i] >= 0.8 or po[i] <= 0.2)]
    flip = [i for i in range(len(names3)) if (po[i] >= 0.8 and pn[i] <= 0.2) or (po[i] <= 0.2 and pn[i] >= 0.8)]
    print(slot, '未標', len(un), '新模型變得有把握', len(ch), '（判有車', sum(1 for i in ch if pn[i] >= 0.8), '判空', sum(1 for i in ch if pn[i] <= 0.2), '）新舊有把握但相反', len(flip))
    sel = (ch + flip)[:48] if len(ch + flip) <= 48 else [(ch + flip)[int(k * len(ch + flip) / 48)] for k in range(48)]
    tiles = []
    for i in sel:
        im = cv2.imread(r'C:\ai_lab\garage\frames3\%s' % names3[i]); H, W = im.shape[:2]
        cv2.rectangle(im, (int(R[0] * W), int(R[1] * H)), (int(R[2] * W), int(R[3] * H)), (0, 255, 0), 3)
        c = cv2.resize(im, (320, 180)); cv2.rectangle(c, (0, 0), (320, 16), (0, 0, 0), -1)
        cv2.putText(c, '%s old=%.2f new=%.2f%s' % (names3[i][2:13], po[i], pn[i], ' FLIP' if i in flip else ''), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1)
        tiles.append(c)
    if tiles:
        while len(tiles) % 6: tiles.append(np.zeros((180, 320, 3), np.uint8))
        cv2.imwrite(r'C:\ai_lab\garage\occ3_check_%s.jpg' % slot, np.vstack([np.hstack(tiles[k:k + 6]) for k in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 80])

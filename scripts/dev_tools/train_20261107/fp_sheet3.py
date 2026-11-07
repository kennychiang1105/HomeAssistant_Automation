import cv2, json, sys, numpy as np
cm = {m['clip']: m for m in json.load(open(r'C:\ai_lab\topfloor\clips3\clipmap.json', encoding='utf-8-sig'))}
clips = sys.argv[2:]
rows = []
for c in clips:
    cap = cv2.VideoCapture(cm[c]['path'])
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    tiles = []
    for k in range(6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((k + 0.5) * n / 6))
        ok, fr = cap.read()
        fr = cv2.resize(fr, (320, 180)) if ok else np.zeros((180, 320, 3), np.uint8)
        tiles.append(fr)
    row = np.hstack(tiles)
    cv2.putText(row, c[:16], (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    rows.append(row)
cv2.imwrite(sys.argv[1], np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 78])
print('ok')

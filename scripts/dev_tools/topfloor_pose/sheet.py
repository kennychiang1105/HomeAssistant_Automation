import cv2, sys, numpy as np
clips = sys.argv[2:]
rows = []
for c in clips:
    cap = cv2.VideoCapture(r'C:\ai_lab\topfloor\clips\%s' % c)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    tiles = []
    for k in range(6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((k + 0.5) * n / 6))
        ok, fr = cap.read()
        if not ok:
            fr = np.zeros((360, 640, 3), np.uint8)
        fr = cv2.resize(fr, (320, 180))
        tiles.append(fr)
    row = np.hstack(tiles)
    cv2.putText(row, c[:16], (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    rows.append(row)
cv2.imwrite(sys.argv[1], np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])

import json, numpy as np, sys
d = np.load(r'C:\ai_lab\garage\emb.npz')
names = list(d['names'])
sat = d['sat']
cl = json.load(open(r'C:\ai_lab\garage\clusters.json'))
roi = json.load(open(r'C:\ai_lab\garage\garage_roi.json', encoding='utf-8'))
occ = {'front': {1, 3, 5, 6, 7, 8, 9, 10, 11, 13}, 'back': {0, 2, 3, 4, 6, 9, 10, 12, 13}}
for tag in ('pseudo_m640', 'pseudo_x'):
    P = json.load(open(r'C:\ai_lab\garage\%s.json' % tag))
    for slot in ('front', 'back'):
        lab = np.array(cl[slot])
        box = roi['slots'][slot]['body']
        for mode, sel in (('IR', sat < 8), ('color', sat >= 8)):
            idx = [i for i in range(len(names)) if lab[i] in occ[slot] and sel[i]]
            if not idx:
                continue
            hit = 0
            for i in idx:
                ok = False
                for x in P[names[i]]:
                    if x['cls'] == 'car' and x['conf'] >= 0.3:
                        cx, cy = (x['box'][0] + x['box'][2]) / 2, (x['box'][1] + x['box'][3]) / 2
                        if box[0] <= cx <= box[2] and box[1] <= cy <= box[3]:
                            ok = True
                if ok:
                    hit += 1
            print(tag, slot, mode, 'occupied n', len(idx), 'detected %.1f%%' % (100 * hit / len(idx)))

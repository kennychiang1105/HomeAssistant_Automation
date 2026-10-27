#!/usr/bin/env python3
"""Garage Vision：YOLO11 偵測汽車／機車 ＋ CLIP 車種／車頭朝向辨識（本機 HTTP，埠 8099，只給 HA 內部用）。

POST /analyze?slots=front=x0,y0,x1,y1;back=...   body=JPEG  → 每個車位的偵測框、身分（樣板庫 kNN）、車型（零樣本）
     （V0.2.0）回傳多一個 plates（整張畫面讀到的車牌）與每車位的 plate（RapidOCR；plate=0 可關閉）
POST /learn?slot=front&label=luxgen_n7:inside&slots=...  body=JPEG → 把這個車位的車存進樣板庫
POST /forget?label=luxgen_n7:inside
GET  /health、GET /gallery
座標都用整張圖的比例 (0~1)。樣板庫存在 /data/gallery.json（add-on 重啟、更新後仍保留）。
"""
import io
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np
import onnxruntime as ort
from PIL import Image

MODELS, DATA = "/models", "/data"
GAL = os.path.join(DATA, "gallery.json")
so = ort.SessionOptions()
so.intra_op_num_threads = int(os.environ.get("THREADS", "3"))
yolo = ort.InferenceSession(f"{MODELS}/yolo11m.onnx", so, providers=["CPUExecutionProvider"])
clip = ort.InferenceSession(f"{MODELS}/clip_visual.onnx", so, providers=["CPUExecutionProvider"])
TEXT = np.load(f"{MODELS}/text_embeds.npy")
try:                                             # 車牌文字辨識（RapidOCR，onnx）；載入失敗就只停用車牌功能
    from rapidocr_onnxruntime import RapidOCR
    OCR = RapidOCR()
except Exception as _e:                          # noqa: BLE001
    OCR = None
    print("ocr disabled:", _e, flush=True)
PLATE_RE = [re.compile(r"([A-Z]{2,3})[-·.]?([0-9]{3,4})"), re.compile(r"([0-9]{3,4})[-·.]?([A-Z]{2,3})")]
TYPES = ["suv", "sedan", "motorcycle", "truck"]
VEH = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
LOCK = threading.Lock()
MAX_PER_LABEL = 40


def load_gallery():
    try:
        with open(GAL, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_gallery(g):
    os.makedirs(DATA, exist_ok=True)
    tmp = GAL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(g, f)
    os.replace(tmp, GAL)


PERSON_CONF = 0.30
LAST = {"persons": []}


def detect(img, conf=0.25, iou=0.5):
    W, H = img.size
    s = 640 / max(W, H)
    nw, nh = round(W * s), round(H * s)
    px, py = (640 - nw) // 2, (640 - nh) // 2
    canvas = Image.new("RGB", (640, 640), (114, 114, 114))
    canvas.paste(img.resize((nw, nh), Image.BILINEAR), (px, py))
    x = np.asarray(canvas, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
    out = yolo.run(None, {yolo.get_inputs()[0].name: x})[0][0]      # (84, N)
    boxes, scores = out[:4].T, out[4:].T
    cls, sc = scores.argmax(1), scores.max(1)
    idx = [i for i in np.where(sc > conf)[0] if int(cls[i]) in VEH]
    # 人（COCO 類別 0）：整個畫面都找，另外回傳（關門前確認淨空用）；門檻略低，夜間紅外線的人信心常偏低
    pidx = [i for i in np.where(sc > PERSON_CONF)[0] if int(cls[i]) == 0]
    persons = []
    for i in sorted(pidx, key=lambda k: -sc[k]):
        cx, cy, w, h = boxes[i]
        b = [(cx - w / 2 - px) / s / W, (cy - h / 2 - py) / s / H, (cx + w / 2 - px) / s / W, (cy + h / 2 - py) / s / H]
        b = [float(min(max(v, 0.0), 1.0)) for v in b]
        if any(iou_of(b, d["box"]) > iou for d in persons):
            continue
        persons.append({"conf": round(float(sc[i]), 3), "box": [round(v, 4) for v in b]})
    LAST["persons"] = persons
    dets = []
    for i in sorted(idx, key=lambda k: -sc[k]):
        cx, cy, w, h = boxes[i]
        b = [(cx - w / 2 - px) / s / W, (cy - h / 2 - py) / s / H, (cx + w / 2 - px) / s / W, (cy + h / 2 - py) / s / H]
        b = [float(min(max(v, 0.0), 1.0)) for v in b]
        if any(iou_of(b, d["box"]) > iou for d in dets if d["cls"] == VEH[int(cls[i])]):
            continue
        dets.append({"cls": VEH[int(cls[i])], "conf": round(float(sc[i]), 3), "box": [round(v, 4) for v in b]})
    return dets


def iou_of(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def embed(img):
    w, h = img.size
    s = 224 / max(w, h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    canvas = Image.new("RGB", (224, 224), (0, 0, 0))
    canvas.paste(img.resize((nw, nh), Image.BICUBIC), ((224 - nw) // 2, (224 - nh) // 2))
    a = ((np.asarray(canvas, dtype=np.float32) / 255.0 - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    e = clip.run(None, {clip.get_inputs()[0].name: a})[0][0]
    return e / np.linalg.norm(e)


def crop(img, box, pad=0.04):
    W, H = img.size
    w, h = box[2] - box[0], box[3] - box[1]
    return img.crop((max(0, int((box[0] - w * pad) * W)), max(0, int((box[1] - h * pad) * H)),
                     min(W, int((box[2] + w * pad) * W)), min(H, int((box[3] + h * pad) * H))))


def zero_shot(e):
    z = 100.0 * (TEXT @ e)
    p = np.exp(z - z.max())
    p /= p.sum()
    k = int(p.argmax())
    return {"label": TYPES[k], "p": round(float(p[k]), 3)}


def classify(e, gallery):
    """樣板庫 kNN：身分＝label 冒號前（luxgen_n7）、朝向＝冒號後（door／inside）。"""
    if not gallery:
        return None
    per = {}
    for g in gallery:
        per.setdefault(g["label"], []).append(float(np.dot(e, np.asarray(g["emb"], dtype=np.float32))))
    best = sorted(((max(v), l) for l, v in per.items()), reverse=True)     # 每個完整 label 取最像的一張
    base = {}
    for sim, l in best:
        b = l.split(":")[0]
        base.setdefault(b, []).append((sim, l))
    ranked = sorted(((v[0][0], b, v) for b, v in base.items()), reverse=True)
    top_sim, top_base, v = ranked[0]
    second = ranked[1][0] if len(ranked) > 1 else None
    res = {"identity": top_base, "score": round(top_sim, 3), "second": round(second, 3) if second is not None else None,
           "label": v[0][1]}
    if ":" in v[0][1]:
        res["facing"] = v[0][1].split(":")[1]
        if len(v) > 1:
            res["facing_margin"] = round(v[0][0] - v[1][0], 3)
    return res


def read_plates(img):
    """整張畫面找車牌文字（台灣車牌：英文＋數字）。回傳 [{text, conf, box(比例), cx, cy}]；OCR 沒載入就回空。"""
    if OCR is None:
        return []
    W, H = img.size
    res, _ = OCR(np.asarray(img)[:, :, ::-1])
    out = []
    for box, txt, conf in (res or []):
        t = re.sub(r"[\s·.\-_]", "", str(txt).upper())
        m = None
        for rx in PLATE_RE:
            m = rx.fullmatch(t)
            if m:
                break
        if not m or float(conf) < 0.5:
            continue
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        b = [min(xs) / W, min(ys) / H, max(xs) / W, max(ys) / H]
        out.append({"text": "".join(m.groups()), "conf": round(float(conf), 3), "box": [round(v, 4) for v in b],
                    "cx": round((b[0] + b[2]) / 2, 4), "cy": round((b[1] + b[3]) / 2, 4)})
    return sorted(out, key=lambda p: -p["conf"])


def parse_slots(q):
    out = {}
    for part in (q.get("slots", [""])[0]).split(";"):
        if "=" in part:
            name, box = part.split("=", 1)
            try:
                out[name] = [float(x) for x in box.split(",")]
            except ValueError:
                pass
    return out


def pick(dets, box):
    """取中心點落在車位框內、面積最大的偵測。"""
    best = None
    for d in dets:
        cx, cy = (d["box"][0] + d["box"][2]) / 2, (d["box"][1] + d["box"][3]) / 2
        if box[0] <= cx <= box[2] and box[1] <= cy <= box[3]:
            area = (d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1])
            if best is None or area > best[0]:
                best = (area, d)
    return best[1] if best else None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            return self._send(200, {"ok": True, "gallery": len(load_gallery())})
        if u.path == "/gallery":
            c = {}
            for g in load_gallery():
                c[g["label"]] = c.get(g["label"], 0) + 1
            return self._send(200, c)
        self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        n = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(n) if n else b""
        t0 = time.time()
        try:
            if u.path == "/forget":
                lab = q.get("label", [""])[0]
                with LOCK:
                    g = [x for x in load_gallery() if x["label"] != lab]
                    save_gallery(g)
                return self._send(200, {"forgot": lab, "gallery": len(g)})
            img = Image.open(io.BytesIO(body)).convert("RGB")
            slots = parse_slots(q)
            with LOCK:
                dets = detect(img)
                if u.path == "/learn":
                    slot, label = q.get("slot", [""])[0], q.get("label", [""])[0]
                    d = pick(dets, slots[slot]) if slot in slots else None
                    if not d or not label:
                        return self._send(404, {"error": "no vehicle in slot", "dets": dets})
                    e = embed(crop(img, d["box"]))
                    g = load_gallery()
                    mine = [x for x in g if x["label"] == label]
                    if len(mine) >= MAX_PER_LABEL:
                        oldest = min(mine, key=lambda x: x["ts"])
                        g.remove(oldest)
                    g.append({"label": label, "emb": [round(float(v), 5) for v in e], "ts": time.time()})
                    save_gallery(g)
                    return self._send(200, {"learned": label, "slot": slot, "det": d, "gallery": len(g)})
                if u.path == "/analyze":
                    gal = load_gallery()
                    res = {"ts": int(time.time()), "size": list(img.size), "dets": dets, "slots": {}}
                    res["persons"] = LAST.get("persons", [])
                    plates = read_plates(img) if q.get("plate", ["1"])[0] != "0" else []
                    res["plates"] = plates
                    for name, box in slots.items():
                        d = pick(dets, box)
                        r = {"det": d}
                        if d:
                            e = embed(crop(img, d["box"]))
                            r["type"] = zero_shot(e)
                            r["id"] = classify(e, gal)
                        # 車牌屬於這個車位：車牌中心落在該車位的偵測框內（沒偵測到車就看車位框）
                        area = d["box"] if d else box
                        r["_area"] = area
                        res["slots"][name] = r
                    # 一塊車牌只屬於一個車位：包含它的框中面積最小的那個（前景大車的框常蓋住後方車的車牌）
                    for p in plates:
                        own = [(( r["_area"][2] - r["_area"][0]) * (r["_area"][3] - r["_area"][1]), n) for n, r in res["slots"].items()
                               if r["_area"][0] <= p["cx"] <= r["_area"][2] and r["_area"][1] <= p["cy"] <= r["_area"][3]]
                        if own:
                            n = min(own)[1]
                            if "plate" not in res["slots"][n]:
                                res["slots"][n]["plate"] = {"text": p["text"], "conf": p["conf"]}
                    for r in res["slots"].values():
                        r.pop("_area", None)
                    res["ms"] = int((time.time() - t0) * 1000)
                    return self._send(200, res)
            self._send(404, {"error": "not found"})
        except Exception as ex:  # noqa: BLE001
            self._send(500, {"error": str(ex)})


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    print("garage_vision ready", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8099), H).serve_forever()

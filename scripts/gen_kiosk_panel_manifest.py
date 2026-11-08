#!/usr/bin/env python3
"""由「自動化管理」面板（automation-panel.yaml）產生 Kiosk 用的清單 www/automation-panel.json。

Kiosk（NAS，8130 埠）的「自動化管理」頁不自己維護分類與卡片：它讀這份清單，所以面板怎麼分、Kiosk 就怎麼分。
  views[].sections[].items[] 每一項是下列其中一種：
    {"e": "entity_id", "n": "顯示名稱"}                      一般列（開關、數值、選項、文字、日期、按鈕、唯讀值）
    {"bc": {...}}                                           特殊卡片（custom:button-card 的 JS 樣板原封不動帶過去，
                                                            Kiosk 用同一份程式產生畫面，所以兩邊長得一樣）
  views[].sections[].title 和面板的標題完全相同（含「（10）」這類數量）
  actions：特殊卡片上的按鈕（呼叫腳本）清單，Kiosk 後端只允許執行這裡列出的動作
用法：python3 scripts/gen_kiosk_panel_manifest.py        （generate_automation_panel.py 執行後會自動呼叫）
"""
import json
import pathlib
import re
import sys
import time

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "automation-panel.yaml"
OUT = ROOT / "www" / "automation-panel.json"
SKIP_DOMAINS = {"script", "scene", "camera"}
EID = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")


def key_title(t):
    t = re.sub(r"[（(]\s*\d+\s*[）)]\s*$", "", str(t or "")).strip()
    return re.sub(r"（續）$", "", t).strip()


def css_of(lst):
    """button-card 的 styles（[{prop: value}, ...]）轉成 CSS 字串。"""
    out = []
    for d in lst or []:
        if isinstance(d, dict):
            for k, v in d.items():
                out.append("%s:%s" % (k, v))
    return ";".join(out)


def js_body(s):
    s = str(s).strip()
    if s.startswith("[[[") and s.endswith("]]]"):
        return s[3:-3]
    return None


def build(doc):
    views, actions = [], {}
    for vi, v in enumerate(doc.get("views", [])):
        if v.get("path") == "back-3d":
            continue
        sections, state = [], {"key": None, "title": "", "icon": "", "desc": ""}
        seen = set()

        def sec():
            k = state["key"] or ""
            for s in sections:
                if s["_k"] == k:
                    return s
            s = {"_k": k, "title": state["title"], "icon": state["icon"], "items": []}
            sections.append(s)
            return s

        def add(eid, name):
            if not isinstance(eid, str) or not EID.match(eid) or eid.split(".")[0] in SKIP_DOMAINS or eid in seen:
                return
            seen.add(eid)
            sec()["items"].append({"e": eid, "n": str(name or "").strip()})

        def add_bc(c):
            st = c.get("styles") or {}
            fields = []
            for fname, val in (c.get("custom_fields") or {}).items():
                b = js_body(val) if isinstance(val, str) else None
                if b is not None:
                    fields.append({"name": fname, "js": b, "css": css_of((st.get("custom_fields") or {}).get(fname))})
            bc = {"e": c.get("entity") or "", "card": css_of(st.get("card")), "fields": fields}
            src = " ".join(f["js"] for f in fields) + " " + " ".join(str(c.get(k) or "") for k in ("name", "label"))
            bc["refs"] = sorted(set(re.findall(r"\b((?:sensor|binary_sensor|input_[a-z]+|script|automation|switch|light|device_tracker|person|weather)\.[a-z0-9_]+)\b", src)))
            for k in ("name", "label", "icon"):
                if isinstance(c.get(k), str):
                    b = js_body(c[k])
                    bc[k + "_js" if b is not None else k] = b if b is not None else c[k]
            tap = c.get("tap_action") or {}
            if tap.get("action") in ("call-service", "perform-action"):
                svc = tap.get("service") or tap.get("perform_action") or ""
                if re.match(r"^(script|input_button)\.[a-z0-9_]+$", svc):
                    aid = "v%d_%d" % (vi, len(actions))
                    actions[aid] = {"service": svc, "data": tap.get("data") or tap.get("service_data") or {}}
                    bc["tap"] = aid
            if bc["e"]:
                seen.add(bc["e"])
            sec()["items"].append({"bc": bc})

        def walk(c):
            if isinstance(c, list):
                for x in c:
                    walk(x)
                return
            if not isinstance(c, dict):
                return
            t = c.get("type")
            if t == "heading":
                state["key"] = key_title(c.get("heading"))
                if not any(s["_k"] == state["key"] for s in sections):
                    state["title"] = str(c.get("heading") or "")
                    state["icon"] = str(c.get("icon") or "")
            if t == "markdown" and not state["desc"] and str(c.get("content", "")).startswith("**"):
                state["desc"] = re.sub(r"\*\*", "", str(c.get("content"))).strip()
            if t == "custom:button-card" and c.get("template") != "prows":
                if any(isinstance(x, str) and "[[[" in x for x in (c.get("custom_fields") or {}).values()) or (c.get("tap_action") or {}).get("action") in ("call-service", "perform-action"):
                    add_bc(c)
                    return
            if t == "entities" or "entities" in c:
                for r in c.get("entities") or []:
                    if isinstance(r, str):
                        add(r, "")
                    elif isinstance(r, dict):
                        add(r.get("entity"), r.get("name"))
            elif "entity" in c and t != "heading":
                add(c.get("entity"), c.get("name"))
            items = (c.get("variables") or {}).get("items") if isinstance(c.get("variables"), dict) else None
            if isinstance(items, list):                    # 開關列樣板（template: prows）
                for x in items:
                    if isinstance(x, list) and x:
                        add(x[0], x[1] if len(x) > 1 else "")
            for k in ("cards", "card"):
                if k in c:
                    walk(c[k])

        walk(v.get("cards", []))
        sections = [{k: s[k] for k in ("title", "icon", "items")} for s in sections if s["items"]]
        if sections:
            views.append({"key": str(v.get("path") or v.get("title")), "title": str(v.get("title", "")), "icon": str(v.get("icon", "")),
                          "desc": state["desc"], "sections": sections})
    return {"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "views": views, "actions": actions}


def main():
    doc = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    m = build(doc)
    OUT.write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n = sum(len(s["items"]) for v in m["views"] for s in v["sections"])
    nb = sum(1 for v in m["views"] for s in v["sections"] for i in s["items"] if "bc" in i)
    print("wrote", OUT, len(m["views"]), "views", n, "items (", nb, "special cards,", len(m["actions"]), "actions )")
    return m


if __name__ == "__main__":
    m = main()
    if "-v" in sys.argv:
        for v in m["views"]:
            print(v["key"], [(s["title"], len(s["items"])) for s in v["sections"]])
        print(m["actions"])

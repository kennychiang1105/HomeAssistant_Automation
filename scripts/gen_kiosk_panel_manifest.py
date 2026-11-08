#!/usr/bin/env python3
"""由「自動化管理」面板（automation-panel.yaml）產生 Kiosk 用的清單 www/automation-panel.json。

Kiosk（NAS，8130 埠）的「自動化管理」頁不自己維護分類：它讀這份清單，所以面板怎麼分、Kiosk 就怎麼分。
清單格式：{"updated": "...", "views": [{"key","title","sections":[{"title","items":[{"e":"entity_id","n":"顯示名稱"}]}]}]}
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


def clean_title(t):
    t = re.sub(r"[（(]\s*\d+\s*[）)]\s*$", "", str(t or "")).strip()
    t = re.sub(r"（續）$", "", t).strip()
    return t


def build(doc):
    views = []
    for v in doc.get("views", []):
        sections, state = [], {"cur": None, "icon": "", "desc": ""}
        seen = set()

        def sec(title):
            for s in sections:
                if s["title"] == title:
                    return s
            s = {"title": title, "icon": state.get("icon", ""), "items": []}
            sections.append(s)
            return s

        def add(eid, name):
            if not isinstance(eid, str) or not EID.match(eid) or eid.split(".")[0] in SKIP_DOMAINS or eid in seen:
                return
            seen.add(eid)
            sec(state["cur"] or "").get("items").append({"e": eid, "n": str(name or "").strip()})

        def walk(c):
            if isinstance(c, list):
                for x in c:
                    walk(x)
                return
            if not isinstance(c, dict):
                return
            t = c.get("type")
            if t == "heading":
                state["cur"] = clean_title(c.get("heading"))
                state["icon"] = str(c.get("icon") or "")
            if t == "markdown" and not state["desc"] and str(c.get("content", "")).startswith("**"):
                state["desc"] = re.sub(r"\*\*", "", str(c.get("content"))).strip()
            if t == "entities" or "entities" in c:
                for r in c.get("entities") or []:
                    if isinstance(r, str):
                        add(r, "")
                    elif isinstance(r, dict):
                        add(r.get("entity"), r.get("name"))
            elif "entity" in c and t not in ("heading",):
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
        sections = [s for s in sections if s["items"]]
        if sections:
            views.append({"key": str(v.get("path") or v.get("title")), "title": str(v.get("title", "")), "icon": str(v.get("icon", "")), "desc": state["desc"], "sections": sections})
    return {"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "views": views}


def main():
    doc = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    m = build(doc)
    OUT.write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n = sum(len(s["items"]) for v in m["views"] for s in v["sections"])
    print("wrote", OUT, len(m["views"]), "views", n, "entities")
    return m


if __name__ == "__main__":
    m = main()
    if "-v" in sys.argv:
        for v in m["views"]:
            print(v["key"], v["title"], [(s["title"], len(s["items"])) for s in v["sections"]])

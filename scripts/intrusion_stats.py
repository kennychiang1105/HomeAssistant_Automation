#!/usr/bin/env python3
"""離家入侵偵測：感應器穩定度統計（V4.1.6）。

每週（08-7D 自動化）或手動執行：用資料庫紀錄統計「全員離家且網關離家」期間各感應器的表現，
  · 不穩的（離線比例過高、離家時一直自己亂跳）→ 排除
  · 穩定的（觀察時數夠、沒有誤觸、有在回報資料）→ 納入監控
結果寫到 /config/intrusion_sensors.json（HA 的 sensor.intrusion_sensor_lists 讀它），
並重新產生訊號收集自動化（08-7C，所有候選感應器的觸發清單，新裝的感應器下次統計後自動加入）。

統計的「離家期間」＝ binary_sensor.at_home_nobody_home 開滿 10 分鐘 且 input_boolean.aqara_li_jia 開滿 20 分鐘 之後（與正式監控的啟動條件一致）。
事件型感應器（客廳門鎖：有人開門才會回報）不看離線比例，只看離家時有沒有亂報。
輸出（stdout）：第一行 OK 或 CHANGED，之後是人看得懂的差異；結尾若收集自動化有更新會印 RELOAD。
"""
import datetime
import glob
import json
import os
import re
import sqlite3
import sys
import time

CFG = "/config" if os.path.isdir("/config/.storage") else "/homeassistant"
OUT = CFG + "/intrusion_sensors.json"
COLLECTOR_DIR = CFG + "/configuration/Automations" if os.path.isdir(CFG + "/configuration/Automations") else CFG + "/Automations"
COLLECTOR = COLLECTOR_DIR + "/08-7C入侵偵測訊號收集AI.yaml"

LOOKBACK_DAYS = 28
ARM_NOBODY_S = 10 * 60
ARM_AWAY_S = 20 * 60
MIN_WINDOW_S = 5 * 60
MIN_HOURS = 24            # 納入前至少要有的離家觀察時數
MAX_UNAVAIL = 0.10        # 離家期間離線比例上限（事件型感應器不看）
MAX_RATE = 0.5            # 離家時每小時「觸發」次數上限（真入侵很少，常常跳就是不穩）
DEAD_DAYS = 7             # 這麼多天完全沒有任何有效回報 → 視為沒資料
BAD = ("unavailable", "unknown", "", None)

# 固定角色（入口類）；其他的由探索找出來當 interior（室內動作）
FIXED = {
    "cover.garage": "garage",
    "input_boolean.er_lou_men_suo_tong_bu_kai_guan": "er_lou",
}
LOCK_DEVICE_MODEL = re.compile(r"aqara\.lock", re.I)
LOCK_SUFFIX = ("door_state", "latch_state", "lock_by_handle")
INTERIOR_ID = re.compile(r"(motion|person_detected|occupancy|presence|zhan_kong)")
IGNORE_ID = re.compile(r"(^binary_sensor\.at_home_|homekit|charging|men_ling|wa_fi|ping_mu|scene_|_anyone_|_nobody_|template_|vehicle_connected|contactor)")


def jload(path):
    try:
        return json.load(open(path))
    except Exception:
        return {}


def main():
    now = time.time()
    since = now - LOOKBACK_DAYS * 86400
    reg = jload(CFG + "/.storage/core.entity_registry").get("data", {}).get("entities", [])
    dev = {d["id"]: d for d in jload(CFG + "/.storage/core.device_registry").get("data", {}).get("devices", [])}
    rs = {x["state"]["entity_id"]: x["state"] for x in jload(CFG + "/.storage/core.restore_state").get("data", [])}

    # ---- 候選感應器 ----
    cand = {}
    for e in reg:
        eid = e["entity_id"]
        if e.get("disabled_by"):
            continue
        d = dev.get(e.get("device_id"), {})
        if eid in FIXED:
            cand[eid] = FIXED[eid]
        elif eid.startswith("binary_sensor.") and LOCK_DEVICE_MODEL.search(d.get("model") or "") and eid.endswith(LOCK_SUFFIX):
            cand[eid] = "lock"
        elif eid.startswith("binary_sensor.") and e.get("platform") not in ("template", "homekit", "group") and not IGNORE_ID.search(eid):
            dc = e.get("device_class") or e.get("original_device_class") or (rs.get(eid, {}).get("attributes") or {}).get("device_class")
            if dc in ("motion", "occupancy", "presence") or INTERIOR_ID.search(eid):
                cand[eid] = "interior"
    names = {}
    for eid in cand:
        e = next((x for x in reg if x["entity_id"] == eid), {})
        fn = ((rs.get(eid, {}).get("attributes") or {}).get("friendly_name") or e.get("name") or e.get("original_name") or eid)
        dn = (dev.get(e.get("device_id"), {}).get("name_by_user") or dev.get(e.get("device_id"), {}).get("name") or "")
        names[eid] = fn if (not dn or dn in fn) else "%s %s" % (dn, fn)

    db = sqlite3.connect("file:%s/home-assistant_v2.db?mode=ro" % CFG, uri=True, timeout=60)

    def history(eid, lo, hi):
        """(ts,state) rows; includes the last row before lo as the starting state."""
        rows = db.execute(
            "select s.last_updated_ts,s.state from states s join states_meta m using(metadata_id) "
            "where m.entity_id=? and s.last_updated_ts>=? and s.last_updated_ts<? order by s.last_updated_ts", (eid, lo, hi)).fetchall()
        first = db.execute(
            "select s.last_updated_ts,s.state from states s join states_meta m using(metadata_id) "
            "where m.entity_id=? and s.last_updated_ts<? order by s.last_updated_ts desc limit 1", (eid, lo)).fetchone()
        if first:
            rows.insert(0, (lo, first[1]))
        return rows

    def intervals(eid, on_vals):
        out, st = [], None
        for t, s in history(eid, since, now):
            if s in on_vals and st is None:
                st = t
            elif s not in on_vals and st is not None:
                out.append((st, t))
                st = None
        if st is not None:
            out.append((st, now))
        return out

    # ---- 離家期間（與正式監控啟動條件一致）----
    nob = intervals("binary_sensor.at_home_nobody_home", ("on",))
    away = intervals("input_boolean.aqara_li_jia", ("on",))
    windows = []
    for ns_, ne_ in nob:
        for as_, ae_ in away:
            s = max(ns_ + ARM_NOBODY_S, as_ + ARM_AWAY_S)
            e = min(ne_, ae_)
            if e - s >= MIN_WINDOW_S:
                windows.append((s, e))
    windows.sort()
    hours = sum(b - a for a, b in windows) / 3600.0

    def in_win(t):
        return any(a <= t < b for a, b in windows)

    prev_out = jload(OUT)
    stats, monitored, excluded, insufficient = {}, {}, {}, {}
    for eid, role in sorted(cand.items()):
        rows = history(eid, since, now)
        sig = 0
        unav = 0.0
        prev = None
        for i, (t, s) in enumerate(rows):
            if prev is not None and in_win(t):
                if role == "interior" and s == "on" and prev != "on":
                    sig += 1
                elif role == "lock" and s not in BAD and prev not in BAD and s != prev:
                    sig += 1
                elif role == "garage" and s in ("open", "opening") and prev in ("closed", "closing"):
                    sig += 1
                elif role == "er_lou" and s == "on" and prev != "on":
                    sig += 1
            if s in ("unavailable", "unknown"):
                end = rows[i + 1][0] if i + 1 < len(rows) else now
                for a, b in windows:
                    lo, hi = max(a, t), min(b, end)
                    if hi > lo:
                        unav += hi - lo
            prev = s
        total = hours * 3600.0
        unav_pct = (unav / total) if total else 0.0
        rate = (sig / hours) if hours else 0.0
        # 活著嗎：最近 DEAD_DAYS 天（任何時段）有沒有非離線的回報；事件型看 28 天內有沒有任何紀錄
        recent = [s for t, s in rows if t >= now - DEAD_DAYS * 86400 and s not in BAD]
        live = bool(recent) if role != "lock" else any(s not in BAD for t, s in rows)
        stats[eid] = {"role": role, "signals": sig, "rate_per_h": round(rate, 3), "unavail_pct": round(unav_pct * 100, 1), "live": live}
        if hours < MIN_HOURS:
            insufficient[eid] = "離家觀察時數不足（%.1f 小時）" % hours
        elif role == "lock":
            if rate > MAX_RATE:
                excluded[eid] = "離家時每小時 %.2f 次回報（疑似誤報）" % rate
            elif not live:
                excluded[eid] = "28 天內沒有任何回報"
            else:
                monitored[eid] = role
        else:
            if role == "interior" and unav_pct > MAX_UNAVAIL:
                excluded[eid] = "離家期間離線 %.0f%%" % (unav_pct * 100)
            elif rate > MAX_RATE:
                excluded[eid] = "離家時每小時亂跳 %.2f 次" % rate
            elif not live:
                excluded[eid] = "%d 天內沒有任何有效回報" % DEAD_DAYS
            else:
                monitored[eid] = role

    data = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "hours": round(hours, 1),
        "windows": len(windows),
        "monitored": monitored,
        "excluded": excluded,
        "insufficient": insufficient,
        "names": names,
        "stats": stats,
    }
    open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))

    # ---- 與上次比較 ----
    pm, pe = prev_out.get("monitored", {}), prev_out.get("excluded", {})
    lines = []
    for e in sorted(set(monitored) - set(pm)):
        lines.append("＋納入：%s" % names.get(e, e))
    for e in sorted(set(pm) - set(monitored)):
        lines.append("－移出監控：%s（%s）" % (names.get(e, e), excluded.get(e) or insufficient.get(e) or "已不存在"))
    for e in sorted(set(excluded) - set(pe)):
        if e not in pm:
            lines.append("✕新排除：%s（%s）" % (names.get(e, e), excluded[e]))
    print("CHANGED" if lines else "OK")
    print("離家觀察 %.1f 小時（%d 段）｜監控 %d 個、排除 %d 個、觀察不足 %d 個" % (hours, len(windows), len(monitored), len(excluded), len(insufficient)))
    for l in lines:
        print(l)

    # ---- 收集自動化（所有候選的觸發清單）----
    interior = sorted(e for e, r in cand.items() if r == "interior")
    locks = sorted(e for e, r in cand.items() if r == "lock")
    roles = {e: r for e, r in cand.items()}
    def yl(items, ind):
        return "\n".join("%s- %s" % (" " * ind, i) for i in items)
    yaml_text = """# ──────────────────────────────────────────────
# 08-7C入侵偵測訊號收集AI (V4.1.6)  ※ 由 scripts/intrusion_stats.py 自動產生，請勿手改（下次統計會覆蓋）
# 更新紀錄：
# - V4.1.6（2026-10-12）：新增。把所有「候選」感應器（室內動作、客廳門鎖、車庫鐵門、二樓門鎖）的觸發統一轉成 intrusion_signal 事件，
#   給 08-7離家入侵偵測AI 判斷；是否監控由 sensor.intrusion_sensor_lists／手動覆寫決定（不穩的在那邊被排除）。
# 產生時間：%s
# ──────────────────────────────────────────────
- id: ai_08_7c_intrusion_signal_collector
  alias: 08-7C入侵偵測訊號收集AI (V4.1.6)
  description: 把候選感應器的觸發轉成 intrusion_signal 事件（自動產生）。
  mode: queued
  max: 30
  max_exceeded: silent
  variables:
    roles: %s
  triggers:
    - trigger: state
      id: interior
      entity_id:
%s
      to: "on"
%s    - trigger: state
      id: garage
      entity_id: cover.garage
      from:
        - closed
        - closing
      to:
        - open
        - opening
    - trigger: state
      id: er_lou
      entity_id: input_boolean.er_lou_men_suo_tong_bu_kai_guan
      to: "on"
  conditions:
    - alias: "客廳門鎖：只算真的有變化（不算離線／重新連線）"
      condition: template
      value_template: >-
        {{ trigger.id != 'lock' or (trigger.from_state is not none and trigger.to_state is not none
           and trigger.from_state.state not in ['unavailable', 'unknown']
           and trigger.to_state.state not in ['unavailable', 'unknown']
           and trigger.from_state.state != trigger.to_state.state) }}
  actions:
    - event: intrusion_signal
      event_data:
        entity_id: "{{ trigger.entity_id }}"
        role: "{{ roles.get(trigger.entity_id, trigger.id) }}"
        state: "{{ trigger.to_state.state }}"
        via_ha: "{{ trigger.to_state.context.user_id is not none or trigger.to_state.context.parent_id is not none }}"
""" % (data["updated"], json.dumps(roles, ensure_ascii=False),
       yl(interior, 8),
       ("    - trigger: state\n      id: lock\n      entity_id:\n%s\n" % yl(locks, 8)) if locks else "")
    old = open(COLLECTOR, encoding="utf-8").read() if os.path.exists(COLLECTOR) else ""
    body = lambda s: re.sub(r"# 產生時間：.*\n", "", s)
    if body(old) != body(yaml_text):
        open(COLLECTOR, "w", encoding="utf-8").write(yaml_text)
        print("RELOAD")


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:           # 出錯時讓呼叫端看得到
        print("ERROR %s" % ex)
        sys.exit(1)


#!/usr/bin/env python3
"""產生「自動化管理」側邊欄面板（/homeassistant/automation-panel.yaml）。

用法（在專案資料夾執行）：
    python3 scripts/generate_automation_panel.py            # 產生 www/automation-panel.yaml（本機）
    python3 scripts/generate_automation_panel.py --deploy   # 產生並上傳到 HA 主機（需再重啟 HA 才會載入新設定；只改面板內容不用重啟，重新整理即可）

資料來源：透過 SSH 讀取 HA 的 core.restore_state，取得目前存在（非 unavailable）的 automation / input_* / timer / counter / script（紀錄庫已排除 automation／script，不能再用）。
新增自動化或 helper 之後，重新執行本程式即可更新面板（面板是 YAML 模式，儲存檔案後在瀏覽器重新整理）。
分類規則在下方 AUTO_RULES / HELPER_RULES，可自行調整。
"""
import json, re, subprocess, sys, pathlib

HOST = "kenny1105@192.168.68.97"
OUT = pathlib.Path(__file__).resolve().parent.parent / "www" / "automation-panel.yaml"

QUERY = r'''
import json
# 讀 HA 的 core.restore_state（每 15 分鐘與停止時寫入）取得「現在確實存在」的實體：
# 紀錄庫已把 automation／script 排除，改查紀錄庫會讀到已刪除自動化的舊狀態（面板出現「找不到實體」）。
d=json.load(open("/homeassistant/.storage/core.restore_state"))["data"]
doms=("automation","input_boolean","input_number","input_select","input_text","input_datetime","input_button","timer","counter","script")
out=[]
# restore_state 會保留已刪除實體最多 7 天；現存實體的 last_seen 都是最近一次寫入時間，只收這一批
from datetime import datetime
ts=lambda x: datetime.fromisoformat(x["last_seen"].replace("Z","+00:00")).timestamp()
newest=max(ts(x) for x in d)
for x in d:
    if ts(x) < newest - 120: continue
    s=x["state"]; eid=s["entity_id"]
    if eid.split(".")[0] in doms:
        out.append((eid,s["state"],(s.get("attributes") or {}).get("friendly_name","")))
print(json.dumps(out,ensure_ascii=False))
'''

# 分類：(key, 標題, icon, 說明)
CATS = [
    ("overview", "總覽", "mdi:view-dashboard-outline", ""),
    ("notify", "通知與廣播", "mdi:bell-ring-outline", "通知分級（資訊/一般/重要/緊急）、LINE、廣播音量、氣氛燈提醒、機台氣氛燈、LINE Bot。"),
    ("scene", "情境", "mdi:home-automation", "早安／晚安／離家／到家情境、網關模式、HomeKit／Google 情境按鈕、漸進燈光。"),
    ("switch", "開關按鈕", "mdi:light-switch", "Terncy／小米／Aqara 實體開關的單擊、雙擊、長按動作（800 系列）。"),
    ("lighting", "照明與感應燈", "mdi:lightbulb-on-outline", "樓梯燈、廚房／廁所感應燈、客廳／車庫燈、車庫鐵門感應燈。"),
    ("topfloor", "頂樓", "mdi:stairs-up", "五樓保全、樓梯感應燈、書房燈、上下樓情境、深夜熟睡鎖與頂樓感應參數。"),
    ("security", "保全與門鎖", "mdi:shield-home-outline", "離家保全、鐵門／車牌辨識、門鈴、門鎖電量、網關。"),
    ("emergency", "緊急與災防", "mdi:alert-octagon-outline", "緊急模式 05A~05E、地震／天氣／疏散警報。"),
    ("air_fan", "空氣與風扇", "mdi:fan", "空氣清淨機、客廳／頂樓風扇、空調溫度門檻、夏季模式。"),
    ("system", "系統維護", "mdi:cog-outline", "穩定重啟、看門狗、更新紀錄／版本、耗材電量、Tesla、測試與初始化、定位追蹤。"),
    ("internal", "內部狀態（勿動）", "mdi:lock-outline", "由自動化自動維護的旗標、紀錄、計時器與計數器，一般不用修改；手動改動可能讓自動化判斷錯誤。"),
    ("other", "其他", "mdi:dots-horizontal-circle-outline", "尚未歸類的項目（可在 generate_automation_panel.py 調整分類規則）。"),
]

# 自動化分類規則：依 friendly_name，由上而下第一個符合者
AUTO_RULES = [
    ("scene", r"^(100晚安|101早安|102離家|103到家|100A|100B|100C ?GoogleHome|08-7A|105門鎖|106-1|HomeKit情境|AI離家版本|800-開關系列-(0B?|1B?)(?![0-9A-Za-z]))"),
    ("topfloor", r"^(08-5[A-K]|800-開關系列-(11|12)[A-D]?)"),
    ("emergency", r"^(05[A-E]|01地震|02地震|03E|03苗栗|04苗栗|00-2廣播系統測試)"),
    ("air_fan", r"^(07|06空氣|21[AB]|22頂樓)"),
    ("lighting", r"^(800-開關系列-(9[ABC]|10)|08-4|08-8|104-1|801-)"),
    ("security", r"^(08-[236]|08鐵門|104|105大門|106B|100C[123]|100C客廳|08-3)"),
    ("switch", r"^800-"),
    ("notify", r"^(00-2[AB]|00-2[CDEFGHIJK]通知|00-2D(通知|氣氛燈|情境廣播|廣播音量)|LINE通知標題|00-2D)"),
    ("system", r"^(00-|09|106|107|14|版本快照)"),
]

# helper 分類規則：依 entity_id（含 friendly_name），由上而下第一個符合者
HELPER_RULES = [
    ("lighting", r"toilet_light|garage_light|light_cooldown|light_manual"),
    ("security", r"wu_lou_bao_quan|lpr_|allowed_plates|doorlock|er_lou_men_suo|gateway_|garagejudge|五樓保全"),
    ("topfloor", r"topfloor|sleep_silent|ding_lou_(shang|xia|ye|yue|si_lou)|debug_topfloor|pan_duan_ding_lou|wu_lou_she_ying_ji_kai_guan"),
    ("emergency", r"jin_ji|disaster|eq99|di_zhen|tian_qi|line_eew"),
    ("scene", r"aqara_|google_scene|hk_scene|scene_origin|input_button\.(night|li_jia|morning|dao_jia)|collection_of_homekit"),
    ("notify", r"notify_|announce_|line_bot|mood_|ambient_|scene_announce|notif_title|garage_arrival"),
    ("air_fan", r"fan|feng_shan|summer_mode|^input_number\.(ac_|enter_|night_cold|morning_reopen)|effective_apparent|living_room"),
    ("system", r"supply_|system_stability|ai_00_01|tesla|at_home|tracker|ai_version|ai_manual|automation_(package|framework)|homekit_framework|ai_leave_version|floorplan|battery_system|collection|last_disaster"),
]
# 「內部狀態」：由自動化自動維護，不是給人調整的（旗標、時間戳、紀錄、計時器、計數器、記憶值…）
INTERNAL_RE = re.compile(
    r"^timer\.|^counter\."
    r"|^input_datetime\.(?!system_stability_restart_time|supply_battery_report_time)"
    r"|^input_boolean\.(topfloor_(0fb7|13b8|kandeng|study)_auto|topfloor_stairs_keep_on|topfloor_stairs_night_used|mood_alert_active|line_bot_quota_exhausted_notified|tesla_charger_session_charged"
    r"|aqara_|hk_scene_|google_scene_|jin_ji_mo_shi_pan_duan_|ding_lou_(shang|xia)_lou_qing_jing|ding_lou_ye_deng_qing_jing|ding_lou_yue_du_qing_jing"
    r"|ding_lou_fan_(system_action_guard|manual_hold|manual_off_hold|cold_off_memory|manual_speed_snooze)|living_room_fan_manual_speed_snooze"
    r"|collection_of_homekit_sensors|garagejudge|pan_duan_|er_lou_men_suo_tong_bu_kai_guan|ke_ting_dian_feng_shan_control)"
    r"|^input_text\.(.*_init$|.*_flag$|.*_last($|_)|.*decision|.*last_path|ambient_scene_state|mood_mem_|.*notice_key|.*monthly_history|doorlock_batt_last_stage"
    r"|doorlock_batt_model_last_cycle|ai_leave_version_text|scene_origin_device|line_eew_remote_|notif_title_|.*last_message|.*debug_last|ai_00_01_)"
    r"|^input_number\.(supply_batt_lowest_|doorlock_batt_drop_last_cycle|.*effective_apparent_temperature)"
    r"|^input_select\.(lpr_last_plate|floorplan_active_floor)"
)

# 各分類內的功能小組（依序比對，先符合者先分；沒符合的依元件種類分組）
SUBGROUPS = {
    "notify": [
        ("LINE 通知開關", r"notify_line_|notify_supply_extra_line|notify_tesla_charge_extra_line"),
        ("HA 通知開關", r"notify_ha_|garage_arrival_ha_notify|notify_tesla_charge_extra_system"),
        ("廣播音量與情境廣播", r"announce_volume|scene_announce"),
        ("氣氛燈與機台氣氛燈", r"mood_alert|ambient_"),
        ("通知測試按鈕", r"notify_test|tesla_charger_notify_test"),
    ],
    "topfloor": [
        ("感應燈與書房燈參數", r"topfloor_(evidence|line_debounce|arrive|down_4f|vacancy|study|stairs_night|stairs_day)|topfloor_motion_pause"),
        ("上下樓情境判斷參數", r"_kenny|topfloor_webhook_mode|topfloor_ap_macs"),
        ("睡眠靜默與熟睡鎖", r"sleep_silent"),
    ],
    "air_fan": [
        ("溫度門檻與冷氣", r"ac_|enter_|night_cold|morning_reopen|summer_mode"),
        ("客廳風扇", r"living_room_fan|ke_ting_dian_feng"),
        ("頂樓風扇", r"ding_lou_fan|top_floor_fan"),
    ],
    "security": [
        ("車牌辨識（LPR）", r"lpr_|allowed_plates"),
        ("門鎖與電池", r"doorlock|er_lou_men_suo"),
        ("五樓保全", r"wu_lou_bao_quan"),
        ("網關", r"gateway_"),
    ],
    "system": [
        ("耗材電量回報", r"supply_battery|battery_system_test"),
        ("系統穩定自動重啟", r"system_stability"),
        ("版本與更新紀錄", r"version|ai_manual|ai_version|ai_leave"),
        ("家人定位追蹤", r"at_home|tracker"),
        ("Tesla 充電", r"tesla"),
    ],
}

TYPE_LABEL = [
    ("input_boolean", "其他開關"), ("input_number", "其他數值參數"), ("input_select", "選項"),
    ("input_text", "文字"), ("input_datetime", "日期時間"), ("input_button", "操作按鈕"),
    ("timer", "計時器"), ("counter", "計數器"),
]


def classify(rules, text):
    for key, pat in rules:
        if re.search(pat, text):
            return key
    return "other"


def fetch():
    r = subprocess.run(["ssh", HOST, "sudo python3 -"], input=QUERY, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def q(s):
    return json.dumps(s, ensure_ascii=False)


def entity_rows(ids, names=None):
    return [f"          - entity: {i}" for i in ids]


def short_name(n):
    """列內名稱去掉「預設…」等細節，避免太長被切斷（單位保留）。"""
    n = re.sub(r"[，,；;]\s*預設[^）)]*", "", n)
    n = re.sub(r"[（(]\s*預設[^）)]*[）)]", "", n)
    n = re.sub(r"[（(]\s*[）)]", "", n)
    return n.strip()


# 每種列元件裡的 hui-generic-entity-row 預設會把名稱切成「…」；用 card-mod 讓它換行顯示
ROW_TYPES = ["toggle", "input-number", "input-select", "input-text", "input-datetime", "button",
             "simple", "timer", "select", "number", "text", "sensor"]


_CM_DONE = [False]


def card_mod_wrap():
    """第一次輸出完整內容並設錨點 &cm，之後用 *cm 重複使用，避免檔案過大。"""
    if _CM_DONE[0]:
        return ["        card_mod: *cm"]
    _CM_DONE[0] = True
    L = ["        card_mod: &cm", "          style:", "            .: |", "              ha-card { overflow: hidden !important; }"]
    css = ".info, .info > * { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.35; }"
    for t in ROW_TYPES:
        L.append(f"            hui-{t}-entity-row:")
        L.append("              $:")
        L.append("                hui-generic-entity-row:")
        L.append("                  $: |")
        L.append(f"                    {css}")
    return L


def entities_card(rows, title=None):
    L = ["      - type: entities"]
    if title:
        L.append(f"        title: {q(title)}")
    L += ["        show_header_toggle: false", "        state_color: true", "        entities:"]
    for r in rows:
        if isinstance(r, tuple):
            eid, name = r
            L.append(f"          - entity: {eid}")
            L.append(f"            name: {q(name)}")
        else:
            L.append(f"          - {r}")
    L += card_mod_wrap()
    return L


def heading(text, icon=None):
    L = ["      - type: heading", f"        heading: {q(text)}", "        heading_style: title"]
    if icon:
        L.append(f"        icon: {icon}")
    return L


def section(cards_lines, span=None):
    L = ["    - type: grid"]
    if span:
        L.append(f"      column_span: {span}")
    L.append("      cards:")
    L += cards_lines
    return L


BOT_JS = """[[[
  const e = entity;
  const u = Number(e.attributes.usage || 0), lim = Number(e.attributes.limit || 200);
  const r = Math.max(lim - u, 0), p = Math.min(100, Math.round(u / lim * 100));
  const sw = Number((states['sensor.line_bot_in_use'].attributes || {}).rotation_switch_limit || 196);
  const cur = Number((states['sensor.line_bot_in_use'].attributes || {}).target_index) === __IDX__;
  const color = u >= sw ? '#EB5757' : (p >= 70 ? '#F2994A' : '#27AE60');
  const chip = cur ? '使用中' : (u >= sw ? '已達切換門檻' : '待命');
  const chipBg = cur ? 'rgba(39,174,96,.18)' : (u >= sw ? 'rgba(235,87,87,.18)' : 'rgba(128,128,128,.18)');
  const chipFg = cur ? '#1E8E4E' : (u >= sw ? '#C0392B' : 'inherit');
  return `
   <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
     <div style="font-weight:600;font-size:15px;line-height:1.35;white-space:normal;text-align:left">${e.attributes.friendly_name}</div>
     <div style="font-size:12px;padding:3px 10px;border-radius:999px;background:${chipBg};color:${chipFg};white-space:nowrap">${chip}</div>
   </div>
   <div style="display:flex;align-items:baseline;gap:6px;margin:12px 0 8px">
     <span style="font-size:34px;font-weight:700;line-height:1;color:${color}">${r}</span>
     <span style="opacity:.65;font-size:13px">則剩餘</span>
   </div>
   <div style="height:12px;border-radius:7px;background:rgba(128,128,128,.22);overflow:hidden">
     <div style="width:${p}%;height:100%;background:${color};border-radius:7px"></div>
   </div>
   <div style="display:flex;justify-content:space-between;font-size:12px;opacity:.7;margin-top:7px">
     <span>已用 ${u} / ${lim}</span><span>${p}%</span>
   </div>`;
]]]"""


def quota_section():
    """LINE Bot 額度：4 張卡片（剩餘數字＋進度條＋狀態），用 auto-fit 格線，直向 1~2 欄、橫向 4 欄，不會左右滑動。"""
    L = []
    L += heading("LINE Bot 額度", "mdi:message-text-outline")
    L.append("      - type: custom:layout-card")
    L.append("        layout_type: custom:grid-layout")
    L.append("        layout:")
    L.append("          grid-template-columns: repeat(auto-fit, minmax(230px, 1fr))")
    L.append("          grid-gap: 12px")
    L.append("          margin: 0")
    L.append("        cards:")
    for i in range(4):
        L.append("          - type: custom:button-card")
        L.append(f"            entity: sensor.bot_msg_remaining{i}")
        L.append("            show_name: false")
        L.append("            show_icon: false")
        L.append("            show_state: false")
        L.append("            tap_action:")
        L.append("              action: none")
        L.append("            styles:")
        L.append("              card:")
        L.append("                - height: auto")
        L.append("                - padding: 16px")
        L.append("                - border-radius: 18px")
        L.append("              grid:")
        L.append("                - grid-template-areas: '\"body\"'")
        L.append("                - grid-template-columns: 1fr")
        L.append("            custom_fields:")
        L.append("              body: |")
        for ln in BOT_JS.replace("__IDX__", str(i)).splitlines():
            L.append("                " + ln)
    md = ("目前使用：**{{ states('sensor.line_bot_in_use') }}**　下一個：Bot{{ state_attr('sensor.line_bot_rotation_target','next_bot') }}\n\n"
          "已用達 {{ state_attr('sensor.line_bot_in_use','rotation_switch_limit') }} 則（剩餘不到 5）自動切換下一個 Bot；群組訊息一次約耗 5 個額度；月初沿用上月最後使用的 Bot。")
    L.append("      - type: markdown")
    L.append("        content: " + q(md))
    return L


def quota_settings():
    rows = [("input_select.line_bot_mode", "LINE Bot 模式"), ("input_number.line_bot_sticky", "主用 Bot（Auto 沿用）"),
            ("input_boolean.line_bot_test_mode", "測試模式"), ("input_boolean.line_bot_custom_user_enable", "自訂目標 ID 啟用"),
            ("input_text.line_bot_custom_user_id", "自訂目標 ID")]
    return heading("LINE Bot 設定", "mdi:robot-outline") + entities_card(rows)


def overview_sections(autos, stale):
    total = sum(len(v) for v in autos.values())
    intro = (f"啟用中的自動化 **{total}** 支（另有 {stale} 筆已失效的舊自動化殘留，可到「設定 → 自動化」清理）。"
             "上方分頁依功能分類，每頁有該類自動化的開關與可調整的參數。")
    quick = [("input_boolean.notify_line_general_enable", "LINE 通知｜一般"), ("input_boolean.notify_line_important_enable", "LINE 通知｜重要"),
             ("input_boolean.notify_line_emergency_enable", "LINE 通知｜緊急"), ("input_boolean.notify_line_doorbell_enable", "LINE 通知｜大門門鈴"),
             ("input_boolean.notify_ha_info_enable", "HA 通知｜資訊級"), ("input_boolean.notify_ha_general_enable", "HA 通知｜一般級"),
             ("input_boolean.notify_ha_important_enable", "HA 通知｜重要級"), ("input_boolean.garage_arrival_ha_notify", "104-4 車庫回家｜HA 通知"),
             ("input_boolean.mood_alert_enable", "氣氛燈提醒｜總開關"), ("input_boolean.mood_alert_important_enable", "氣氛燈提醒｜重要級"),
             ("input_boolean.mood_alert_emergency_enable", "氣氛燈提醒｜緊急級"), ("input_boolean.mood_alert_ap_off", "機台氣氛燈｜停用通知閃爍"),
             ("input_boolean.ambient_scene_off", "機台氣氛燈｜停用情境色"), ("input_boolean.scene_announce_enable", "情境執行廣播"),
             ("input_number.announce_volume_general", "廣播音量｜一般"), ("input_number.announce_volume_important", "廣播音量｜重要"),
             ("input_number.announce_volume_emergency", "廣播音量｜緊急")]
    top = [("input_boolean.topfloor_motion_pause", "頂樓感應暫停"), ("input_boolean.sleep_silent_active", "頂樓深夜熟睡手動鎖"),
           ("input_select.topfloor_webhook_mode", "頂樓 Webhook 判斷模式"), ("input_boolean.topfloor_stairs_keep_on", "樓梯燈常開（9A）"),
           ("input_boolean.wu_lou_bao_quan_xi_tong_kai_guan", "五樓保全系統開關"), ("input_boolean.debug_topfloor_kenny", "頂樓自動化 Debug 模式")]
    off_md = ("{% set off = states.automation | selectattr('state','eq','off') | map(attribute='name') | sort | list %}"
              "{% if off | length == 0 %}沒有停用中的自動化。{% else %}{% for n in off %}- {{ n }}\n{% endfor %}{% endif %}")
    recent_md = ("{% set ns = namespace(items=[]) %}"
                 "{% for a in states.automation if a.attributes.get('last_triggered') is not none and (now() - a.attributes.get('last_triggered')).total_seconds() < 86400 %}"
                 "{% set ns.items = ns.items + [(a.name, a.attributes.get('last_triggered'))] %}{% endfor %}"
                 "{% for n, t in (ns.items | sort(attribute='1', reverse=true))[:12] %}- {{ n }}（{{ relative_time(t) }}前）\n{% endfor %}")
    S = []
    S += section(["      - type: markdown", "        content: " + q(intro)], span=3)
    S += section(quota_section(), span=3)
    S += section(quota_settings())
    S += section(heading("常用總開關", "mdi:toggle-switch-outline") + entities_card(quick))
    S += section(heading("頂樓常用", "mdi:stairs-up") + entities_card(top))
    S += section(heading("目前停用的自動化", "mdi:pause-circle-outline") + ["      - type: markdown", "        content: " + q(off_md)])
    S += section(heading("最近 24 小時觸發", "mdi:history") + ["      - type: markdown", "        content: " + q(recent_md)])
    return S


def build(data):
    _CM_DONE[0] = False
    autos = {k: [] for k, *_ in CATS}
    settings = {k: [] for k, *_ in CATS}      # (dom, 名稱, eid)
    internal = {k: [] for k, *_ in CATS}
    stale = 0
    for eid, st, fn in data:
        dom = eid.split(".")[0]
        if st in ("unavailable", "None") or (dom == "automation" and not fn):
            if dom == "automation":
                stale += 1
            continue
        if dom == "automation":
            autos[classify(AUTO_RULES, fn)].append((fn, eid))
        elif dom == "script":
            continue
        else:
            cat = classify(HELPER_RULES, f"{eid} {fn}")
            if re.search(r"^input_(select|number|boolean|text)\.line_bot_(mode|sticky|test_mode|custom_user_enable|custom_user_id)$", eid):
                continue   # LINE Bot 模式與設定只放在「總覽」，避免重複
            if INTERNAL_RE.search(eid):
                internal[cat].append((dom, fn or eid, eid))
            else:
                settings[cat].append((dom, fn or eid, eid))

    L = ["# 自動化管理面板（由 scripts/generate_automation_panel.py 產生，請勿直接手改；重新執行程式即可更新）",
         "title: 自動化管理", "views:"]
    for key, title, icon, desc in CATS:
        L += [f"  - title: {q(title)}", f"    path: {key}", f"    icon: {icon}", "    type: sections", "    max_columns: 4", "    sections:"]
        if key == "overview":
            L += overview_sections(autos, stale)
            continue
        if key == "other" and not autos[key] and not settings[key]:
            L = L[:-6]   # 沒有未分類項目就不顯示「其他」分頁
            continue
        if key == "internal":
            L += section(["      - type: markdown", "        content: " + q(f"**{title}**　{desc}")], span=3)
            for ck, ctitle, *_ in CATS:
                items = internal.get(ck)
                if items:
                    rows = [(eid, short_name(fn)) for dom, fn, eid in sorted(items, key=lambda x: (x[0], x[1]))]
                    L += section(heading(f"{ctitle}（{len(rows)}）") + entities_card(rows))
            continue
        n_auto = len(autos[key]); n_set = len(settings[key])
        L += section(["      - type: markdown", "        content: " + q(f"**{title}**　{desc}　自動化 {n_auto} 支、可調整項目 {n_set} 個")], span=3)
        if autos[key]:
            rows = [(eid, fn) for fn, eid in sorted(autos[key])]
            L += section(heading(f"自動化開關（{n_auto}）", "mdi:robot") + entities_card(rows))
        # 功能小組
        left = list(settings[key])
        for label, pat in SUBGROUPS.get(key, []):
            grp = [x for x in left if re.search(pat, x[2] + " " + x[1])]
            if grp:
                left = [x for x in left if x not in grp]
                rows = [(eid, short_name(fn)) for dom, fn, eid in sorted(grp, key=lambda x: (x[0], x[1]))]
                L += section(heading(f"{label}（{len(rows)}）") + entities_card(rows))
        # 其餘依元件種類（同分類已有功能小組時，這些標為「其他…」）
        had_groups = len(left) != len(settings[key])
        for dom, label in TYPE_LABEL:
            grp = [x for x in left if x[0] == dom]
            if grp:
                label = label.replace("其他", "")
                label = ("其他" + label) if had_groups else label
                rows = [(eid, short_name(fn)) for d, fn, eid in sorted(grp, key=lambda x: x[1])]
                L += section(heading(f"{label}（{len(rows)}）") + entities_card(rows))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    data = fetch()
    text = build(data)
    import yaml
    yaml.safe_load(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT, len(text.splitlines()), "lines")
    if "--deploy" in sys.argv:
        subprocess.run(["ssh", HOST, "sudo tee /homeassistant/automation-panel.yaml >/dev/null"], input=text, text=True, check=True)
        print("deployed to /homeassistant/automation-panel.yaml")

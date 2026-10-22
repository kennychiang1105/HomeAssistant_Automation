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
GONE={"input_boolean.door_light_auto",
      # 2026-10-11 105門鎖自動判斷到家已併入 100A
      "automation.automation_26",
      # 2026-10-12 入侵偵測的收集／統計自動化改名（08-7A→08-7C、08-7S→08-7D）
      "automation.08_7aru_qin_zhen_ce_xun_hao_shou_ji_ai_v4_1_6","automation.08_7sru_qin_zhen_ce_gan_ying_qi_tong_ji_ai_v4_1_6",
      # 2026-10-11 在家判斷改只讀 person.*，移除追蹤裝置清單 input_text
      "input_text.at_home_kenny_trackers","input_text.at_home_kenny_ipad_trackers","input_text.at_home_elay_trackers","input_text.at_home_jerry_trackers","input_text.at_home_iris_trackers",
      # 2026-10-11 已刪除的舊 07 系列與舊 100A（restore_state 還會保留一陣子）
      "automation.kong_qi_qing_jing_ji_zi_dong_qi_dong","automation.10kong_qi_yan_zhong_tong_zhi",
      "automation.11kong_qi_yan_zhong_tong_zhi_yan_zhong","automation.07kong_qi_qing_jing_ji_zi_dong_qi_dong",
      "automation.07_4kong_qi_qing_jing_ji_zi_dong_guan_bi","automation.100zi_dong_qi_dong_dao_jia_zao_an_qing_jing"}
# restore_state 會保留已刪除實體最多 7 天；現存實體的 last_seen 都是最近一次寫入時間，只收這一批
from datetime import datetime
ts=lambda x: datetime.fromisoformat(x["last_seen"].replace("Z","+00:00")).timestamp()
newest=max(ts(x) for x in d)
for x in d:
    if ts(x) < newest - 120: continue
    s=x["state"]; eid=s["entity_id"]
    if eid in GONE: continue                     # 已刪除但 restore_state 還留著的實體
    if eid.split(".")[0] in doms:
        out.append((eid,s["state"],(s.get("attributes") or {}).get("friendly_name","")))
print(json.dumps(out,ensure_ascii=False))
'''

# 分類：(key, 標題, icon, 說明)
CATS = [
    ("overview", "總覽", "mdi:view-dashboard-outline", ""),
    ("supply", "耗材與額度", "mdi:battery-charging-medium", "設備電池預估、空氣清淨機濾網壽命、LINE Bot 額度消耗與月底全月預測。"),
    ("notify", "通知與廣播", "mdi:bell-ring-outline", "通知分級（資訊/一般/重要/緊急）、LINE、廣播音量、氣氛燈提醒、機台氣氛燈。"),
    ("scene", "情境", "mdi:home-automation", "早安／晚安／離家／到家情境、網關模式、HomeKit／Google 情境按鈕、漸進燈光。"),
    ("switch", "開關按鈕", "mdi:light-switch", "Terncy／小米／Aqara 實體開關的單擊、雙擊、長按動作（800 系列），以及 Terncy 無線開關單擊切換（08-9）。"),
    ("lighting", "照明與感應燈", "mdi:lightbulb-on-outline", "樓梯燈、廚房／廁所感應燈、客廳／車庫燈、車庫鐵門感應燈。"),
    ("topfloor", "頂樓", "mdi:stairs-up", "五樓保全、樓梯感應燈、書房燈、上下樓情境、深夜熟睡鎖與頂樓感應參數。"),
    ("security", "保全與門鎖", "mdi:shield-home-outline", "離家保全、鐵門／車牌辨識、門鈴、門鎖電量、網關。"),
    ("emergency", "緊急與災防", "mdi:alert-octagon-outline", "緊急模式 05A~05G（含連點三下維修暫停）、地震／天氣／疏散警報。"),
    ("air_fan", "空氣與風扇", "mdi:fan", "空氣清淨機、客廳／頂樓風扇、空調溫度門檻、夏季模式。"),
    ("system", "系統維護", "mdi:cog-outline", "穩定重啟、看門狗、更新紀錄／版本、Tesla、測試與初始化、定位追蹤。"),
    ("internal", "內部狀態（勿動）", "mdi:lock-outline", "由自動化自動維護的旗標、紀錄、計時器與計數器，一般不用修改；手動改動可能讓自動化判斷錯誤。"),
    ("other", "其他", "mdi:dots-horizontal-circle-outline", "尚未歸類的項目（可在 generate_automation_panel.py 調整分類規則）。"),
]

# 自動化分類規則：依 friendly_name，由上而下第一個符合者
AUTO_RULES = [
    ("supply", r"^(00-2C|耗材|電池)"),
    ("scene", r"^(100晚安|101早安|102離家|103到家|100A|100B|100C ?GoogleHome|08-7A|105門鎖|106-1|HomeKit情境|AI離家版本|800-開關系列-(0B?|1B?)(?![0-9A-Za-z]))"),
    ("topfloor", r"^(08-5[A-K]|800-開關系列-(11|12)[A-D]?)"),
    ("emergency", r"^(05[A-G]|01地震|02地震|03E|03苗栗|04苗栗|00-2廣播系統測試)"),
    ("air_fan", r"^(07|06空氣|06環境異常|21[AB]|22頂樓)"),
    ("lighting", r"^(800-開關系列-(9[ABC]|10)|08-4|08-8|104-1|801-)"),
    ("security", r"^(08-[236]|08-7離家入侵|08-7[CD]|08鐵門|104|105大門|106B|106C|100C[123]|100C客廳|08-3)"),
    ("switch", r"^(800-|08-9|Terncy)"),
    ("notify", r"^(00-2[AB]|00-2[CDEFGHIJK]通知|00-2D(通知|氣氛燈|情境廣播|廣播音量)|LINE通知標題|00-2D)"),
    ("system", r"^(00-|09|106|107|14|版本快照)"),
]

# helper 分類規則：依 entity_id（含 friendly_name），由上而下第一個符合者
HELPER_RULES = [
    ("supply", r"supply_|battery_system|doorlock_batt|line_bot_forecast"),
    ("switch", r"terncy_btn|stairs_si_lou_hold"),
    ("lighting", r"toilet_light|garage_light|light_cooldown|light_manual|light_anim"),
    ("security", r"intrusion_|wu_lou_bao_quan|lpr_|allowed_plates|doorlock|er_lou_men_suo|gateway_|garagejudge|五樓保全|wang_guan|jie_chu_wang_guan|54ef44cf58f9_alarm|解除網關"),
    ("topfloor", r"topfloor|sleep_silent|sleep_holiday|ding_lou_(shang|xia|ye|yue|si_lou)|debug_topfloor|pan_duan_ding_lou|wu_lou_she_ying_ji_kai_guan"),
    ("emergency", r"jin_ji|emergency_|disaster|eq99|di_zhen|tian_qi|line_eew"),
    ("scene", r"auto_scene_|scene_window_|scene_sunrise|scene_sunset|aqara_|google_scene|hk_scene|scene_origin|input_button\.(night|li_jia|morning|dao_jia)|collection_of_homekit"),
    ("notify", r"notify_|announce_|line_bot|mood_|ambient_|scene_announce|notif_title|garage_arrival|garage_away"),
    ("air_fan", r"air_ai|air_pm|air_manual|env_alert|env_co|env_temp|fan|feng_shan|summer_|^input_number\.(ac_|enter_|night_cold|morning_reopen)|effective_apparent|living_room"),
    ("system", r"tv_ir_power|tv_keepalive|maintenance_until|v41_phone|tw_makeup|system_stability|ai_00_01|tesla|at_home|tracker|ai_version|ai_manual|automation_(package|framework)|homekit_framework|ai_leave_version|floorplan|collection|last_disaster"),
]
# 「內部狀態」：由自動化自動維護，不是給人調整的（旗標、時間戳、紀錄、計時器、計數器、記憶值…）
INTERNAL_RE = re.compile(
    r"^timer\.|^counter\."
    r"|^input_datetime\.(?!system_stability_restart_time|supply_battery_report_time|maintenance_until)"
    r"|^input_boolean\.(emergency_snapshot_valid|stairs_si_lou_hold|topfloor_(0fb7|13b8|kandeng|study)_auto|topfloor_stairs_keep_on|topfloor_stairs_night_used|mood_alert_active|light_anim_active|line_bot_quota_exhausted_notified|tesla_charger_session_charged"
    r"|aqara_|hk_scene_|google_scene_|jin_ji_mo_shi_pan_duan_|ding_lou_(shang|xia)_lou_qing_jing|ding_lou_ye_deng_qing_jing|ding_lou_yue_du_qing_jing"
    r"|ding_lou_fan_(system_action_guard|manual_hold|manual_off_hold|cold_off_memory|manual_speed_snooze)|living_room_fan_manual_speed_snooze"
    r"|collection_of_homekit_sensors|collection_of_homepod_sensors|garagejudge|pan_duan_|er_lou_men_suo_tong_bu_kai_guan|ke_ting_dian_feng_shan_control)"
    r"|^input_text\.(intrusion_recent|emergency_(trigger_source|garage_prev)|air_ai_state|env_alert_cd|.*_init$|.*_flag$|.*_last($|_)|.*decision|.*last_path|ambient_scene_state|announce_manual_result|notify_manual_result|mood_mem_|.*notice_key|.*monthly_history|doorlock_batt_last_stage"
    r"|doorlock_batt_model_last_cycle|ai_leave_version_text|scene_origin_device|line_eew_remote_|notif_title_|.*last_message|.*debug_last|ai_00_01_)"
    r"|^input_number\.(v41_phone_match_|supply_batt_lowest_|doorlock_batt_drop_last_cycle|.*effective_apparent_temperature)"
    r"|^input_select\.(lpr_last_plate)"
)

# 各分類內的功能小組（依序比對，先符合者先分；沒符合的依元件種類分組）
SUBGROUPS = {
    "supply": [
        ("LINE Bot 模式與設定", r"line_bot_mode|line_bot_sticky|line_bot_test_mode|line_bot_custom"),
        ("耗材通知與報告設定", r"supply_battery_report_time|notify_supply_extra_line|supply_filter_notified"),
        ("耗材測試按鈕", r"battery_system_test"),
    ],
    "notify": [
        ("LINE 通知開關", r"notify_line_|notify_tesla_charge_extra_line"),
        ("HA 通知開關", r"notify_ha_|garage_arrival_ha_notify|garage_away_off_ha_notify|notify_tesla_charge_extra_system"),
        ("災害訊息廣播開關", r"announce_disaster_"),
        ("手動廣播與手動通知", r"announce_manual|notify_manual"),
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
        ("溫度門檻與冷氣", r"ac_|enter_|night_cold|morning_reopen|summer_"),
        ("客廳風扇", r"living_room_fan|ke_ting_dian_feng"),
        ("頂樓風扇", r"ding_lou_fan|top_floor_fan"),
    ],
    "emergency": [
        ("維修暫停（連點三下）", r"emergency_triple_press"),
    ],
    "security": [
        ("離家入侵偵測", r"intrusion_"),
        ("車牌辨識（LPR）", r"lpr_|allowed_plates"),
        ("門鎖與電池", r"doorlock|er_lou_men_suo"),
        ("五樓保全", r"wu_lou_bao_quan"),
        ("網關與警報", r"gateway_|wang_guan|jie_chu_wang_guan|網關|54ef44cf58f9_alarm"),
    ],
    "system": [
        ("系統穩定自動重啟", r"system_stability"),
        ("版本與更新紀錄", r"version|ai_manual|ai_version|ai_leave"),
        ("家人定位追蹤", r"at_home|tracker"),
        ("Tesla 充電", r"tesla"),
        ("電視待機保持連線", r"tv_ir_power|tv_keepalive"),
        ("維護模式（更新期間略過通知）", r"maintenance_until"),
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
    local_storage = pathlib.Path("/homeassistant/.storage/core.restore_state")
    if not local_storage.exists():
        local_storage = pathlib.Path("/config/.storage/core.restore_state")
    if local_storage.exists():
        r = subprocess.run(["python3", "-"], input=QUERY, capture_output=True, text=True, check=True)
        return json.loads(r.stdout)
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


IOS_CARD_CSS = (
    # iOS 分組清單：圓角卡片、細分隔線、綠色開關、藍色按鈕、圓角輸入框；顏色跟隨 HA 主題（深色／淺色都可）
    "ha-card { overflow: hidden !important; border-radius: 18px !important; border: none !important;"
    " box-shadow: 0 1px 2px rgba(0,0,0,.18) !important; padding: 2px 0 !important;"
    " --switch-checked-color: #34C759; --switch-checked-button-color: #ffffff; --switch-checked-track-color: #34C759;"
    " --switch-unchecked-button-color: #ffffff; --switch-unchecked-track-color: rgba(120,120,128,.32);"
    " --mdc-theme-primary: #0A84FF; --primary-color: #0A84FF;"
    " --mdc-text-field-fill-color: rgba(120,120,128,.14); --mdc-text-field-idle-line-color: transparent;"
    " --mdc-text-field-hover-line-color: transparent; --mdc-text-field-disabled-line-color: transparent;"
    " --mdc-shape-small: 10px; --mdc-select-fill-color: rgba(120,120,128,.14); --mdc-select-idle-line-color: transparent;"
    " --mdc-select-hover-line-color: transparent; --mdc-text-field-label-ink-color: var(--secondary-text-color); }"
    " #states { padding: 4px 16px !important; }"
    " #states > * { margin: 0 !important; padding: 9px 0 !important; }"
    " #states > * + * { border-top: 0.5px solid rgba(128,128,128,.28); }"
)
ROW_CSS = (
    ".info, .info > * { white-space: normal !important; overflow: visible !important; text-overflow: clip !important;"
    " line-height: 1.35; font-size: 15px; }"
    " state-badge { width: 32px; height: 32px; min-width: 32px; border-radius: 9px; margin-right: 4px;"
    " background: rgba(10,132,255,.14); color: #0A84FF; --mdc-icon-size: 19px; display: flex; align-items: center; justify-content: center; }"
    " mwc-button, ha-button { --mdc-theme-primary: #0A84FF; font-weight: 600; }"
)


def card_mod_wrap():
    """第一次輸出完整內容並設錨點 &cm，之後用 *cm 重複使用，避免檔案過大。"""
    if _CM_DONE[0]:
        return ["        card_mod: *cm"]
    _CM_DONE[0] = True
    L = ["        card_mod: &cm", "          style:", "            .: |", f"              {IOS_CARD_CSS}"]
    for t in ROW_TYPES:
        L.append(f"            hui-{t}-entity-row:")
        L.append("              $:")
        L.append("                hui-generic-entity-row:")
        L.append("                  $: |")
        L.append(f"                    {ROW_CSS}")
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
    # iOS 分組標題：小一點、次要文字色、與卡片左緣對齊
    L += ["        card_mod:", "          style: |",
          "            .container { padding: 14px 6px 4px !important; }",
          "            .title { font-size: 13px !important; font-weight: 600 !important; letter-spacing: .3px; color: var(--secondary-text-color) !important; }"]
    return L


MD_CSS = ["        card_mod:", "          style: |",
          "            ha-card { border-radius: 18px !important; border: none !important; box-shadow: 0 1px 2px rgba(0,0,0,.18) !important; padding: 2px 4px !important; font-size: 14px; line-height: 1.55; }"]


MASONRY = False   # build() 內全部分頁都設為 True（masonry：卡片依高度自動分欄，不留空白）


def section(cards_lines, span=None):
    if MASONRY:
        L = ["    - type: vertical-stack", "      cards:"]
        L += cards_lines
        return L
    L = ["    - type: grid"]
    if span:
        L.append(f"      column_span: {span}")
    L.append("      cards:")
    L += cards_lines
    return L


def list_blocks(title, rows, icon=None, max_rows=10):
    """長清單切成多張連續卡片（每張最多 max_rows 列），第二張起標題加「（續）」；
    寬螢幕可分散到不同欄、手機上仍是連續順序。"""
    n = len(rows)
    parts = max(1, -(-n // max_rows))
    size = -(-n // parts)
    out = []
    for i in range(parts):
        chunk = rows[i * size:(i + 1) * size]
        t = title if i == 0 else re.sub(r"（\d+）$", "", title) + "（續）"
        out.append(section(heading(t, icon) + entities_card(chunk)))
    return out


def list_section(head_lines, rows, min_split=12):
    """項目很多（>min_split）時，拆成左右兩欄並佔兩個欄位寬，避免一欄拉很長、旁邊留一大片空白。"""
    if MASONRY or len(rows) <= min_split:
        return section(head_lines + entities_card(rows))
    half = (len(rows) + 1) // 2
    inner = []
    for part in (rows[:half], rows[half:]):
        inner += ["    " + ln for ln in entities_card(part)]
    return section(head_lines + ["      - type: grid", "        columns: 2", "        square: false", "        cards:"] + inner, span=2)


BOT_JS = r"""[[[
  const e = entity;
  const u = Number(e.attributes.usage || 0), lim = Number(e.attributes.limit || 200);
  const r = Math.max(lim - u, 0), p = Math.min(100, Math.round(u / lim * 100));
  const sw = Number((states['sensor.line_bot_in_use'].attributes || {}).rotation_switch_limit || 196);
  const cur = Number((states['sensor.line_bot_in_use'].attributes || {}).target_index) === __IDX__;
  const color = u >= sw ? '#FF453A' : (p >= 70 ? '#FF9F0A' : '#30D158');
  const chip = cur ? '使用中' : (u >= sw ? '已達門檻' : '待命');
  const chipBg = cur ? 'rgba(48,209,88,.18)' : (u >= sw ? 'rgba(255,69,58,.18)' : 'rgba(120,120,128,.18)');
  const chipFg = cur ? '#30D158' : (u >= sw ? '#FF453A' : 'var(--secondary-text-color)');
  const full = String(e.attributes.friendly_name || '');
  const name = full.replace(/^ChiangFamily\s*/i, '') || full;
  const letter = (name.trim().slice(-1) || '?').toUpperCase();
  return `
   <div style="display:flex;align-items:center;gap:12px;text-align:left">
     <div style="flex:none;width:40px;height:40px;border-radius:11px;background:${color}26;color:${color};
                 display:flex;align-items:center;justify-content:center;font-weight:700;font-size:17px">${letter}</div>
     <div style="flex:1;min-width:0">
       <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
         <span style="font-weight:600;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${name}</span>
         <span style="flex:none;font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;background:${chipBg};color:${chipFg}">${chip}</span>
       </div>
       <div style="height:6px;border-radius:4px;background:rgba(120,120,128,.24);margin:9px 0 6px;overflow:hidden">
         <div style="width:${p}%;height:100%;background:${color};border-radius:4px"></div>
       </div>
       <div style="display:flex;justify-content:space-between;align-items:baseline;font-size:12px;color:var(--secondary-text-color)">
         <span>剩餘 <b style="font-size:16px;color:${color}">${r}</b> 則</span><span>已用 ${u} / ${lim}（${p}%）</span>
       </div>
     </div>
   </div>`;
]]]"""


def quota_section():
    """LINE Bot 額度：4 張卡片（剩餘數字＋進度條＋狀態），用 auto-fit 格線，直向 1~2 欄、橫向 4 欄，不會左右滑動。"""
    L = []
    L += heading("LINE Bot 額度", "mdi:message-text-outline")
    L.append("      - type: custom:layout-card")
    L.append("        layout_type: custom:grid-layout")
    L.append("        layout:")
    L.append("          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr))")
    L.append("          grid-gap: 8px")
    L.append("          margin: 0")
    L.append("        cards:")
    for i in range(4):
        L.append("          - type: custom:button-card")
        L.append(f"            entity: sensor.bot_msg_remaining{i}")
        L.append("            show_name: false")
        L.append("            show_icon: false")
        L.append("            show_state: false")
        L.append("            tap_action:")
        L.append("              action: more-info")           # 點額度卡片 → 跳出該 Bot 剩餘額度的詳細視窗（歷史圖表）
        L.append("            hold_action:")
        L.append("              action: more-info")
        L.append("            styles:")
        L.append("              card:")
        L.append("                - cursor: pointer")
        L.append("                - height: auto")
        L.append("                - padding: 12px 14px")
        L.append("                - border-radius: 18px")
        L.append("                - box-shadow: 0 1px 2px rgba(0,0,0,.18)")
        L.append("                - border: none")
        L.append("              grid:")
        L.append("                - grid-template-areas: '\"body\"'")
        L.append("                - grid-template-columns: 1fr")
        L.append("            custom_fields:")
        L.append("              body: |")
        for ln in BOT_JS.replace("__IDX__", str(i)).splitlines():
            L.append("                " + ln)

    status_js = """[[[
  const curInUse = states['sensor.line_bot_in_use'] ? states['sensor.line_bot_in_use'].state : '智慧家庭 D';
  const targetObj = states['sensor.line_bot_rotation_target'];
  const nextIdx = targetObj?.attributes?.next_bot;
  const botNames = { 0: '智慧家庭 A（緊急Bot）', 1: '智慧家庭 B', 2: '智慧家庭 C', 3: '智慧家庭 D' };
  const nextName = nextIdx != null ? (botNames[nextIdx] || ('Bot ' + nextIdx)) : '--';

  const f = states['sensor.line_bot_forecast'];
  const st = f ? f.state : 'safe';
  const a = f?.attributes || {};
  const normalDate = a.normal_exhaust_date ? a.normal_exhaust_date.slice(5).replace('-', '/') : '--';
  const totalDate = a.total_exhaust_date ? a.total_exhaust_date.slice(5).replace('-', '/') : '--';

  let statusColor, statusBg, statusBorder, statusLabel, statusIcon, desc1, desc2;
  if (st === 'safe') {
    statusColor = '#30D158';
    statusBg = 'rgba(48,209,88,.12)';
    statusBorder = 'rgba(48,209,88,.25)';
    statusLabel = '額度安全充裕';
    statusIcon = 'mdi:check-circle';
    desc1 = `本月一般 Bot 額度充裕（可用至 ${normalDate}）`;
    desc2 = '運作平穩，本月無需動用緊急 Bot。';
  } else if (st === 'need_emergency') {
    statusColor = '#FF9F0A';
    statusBg = 'rgba(255,159,10,.14)';
    statusBorder = 'rgba(255,159,10,.3)';
    statusLabel = '預備動用緊急 Bot';
    statusIcon = 'mdi:alert-circle';
    desc1 = `一般 Bot 預估於 ${normalDate}（約 ${a.normal_days_left || 0} 天後）用盡，將切換緊急 Bot`;
    desc2 = '動用智慧家庭 A 後，預估可順利撐至月底重置。';
  } else {
    statusColor = '#FF453A';
    statusBg = 'rgba(255,69,58,.14)';
    statusBorder = 'rgba(255,69,58,.3)';
    statusLabel = '額度告急';
    statusIcon = 'mdi:alert-octagon';
    desc1 = `日均消耗偏高（${a.daily_rate || 0} 則/天），預估於 ${normalDate} 動用緊急 Bot`;
    desc2 = `預估將於 ${totalDate} 前耗盡，請留意推播發送量！`;
  }

  return `
    <div style="background:var(--card-background-color);border-radius:18px;padding:14px 16px;box-shadow:0 1px 2px rgba(0,0,0,.18);display:flex;flex-direction:column;gap:10px;min-width:0;width:100%;box-sizing:border-box">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:13px">
        <div style="display:flex;align-items:center;gap:6px">
          <ha-icon icon="mdi:robot" style="color:#0A84FF;--mdc-icon-size:20px"></ha-icon>
          <span style="color:var(--secondary-text-color)">目前使用：</span>
          <strong style="color:var(--primary-text-color)">${curInUse.replace('ChiangFamily ', '')}</strong>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <span style="color:var(--secondary-text-color)">下一輪替：</span>
          <span style="font-weight:600;color:var(--primary-text-color);background:rgba(120,120,128,.15);padding:2px 8px;border-radius:6px">${nextName}</span>
        </div>
      </div>

      <div style="background:${statusBg};border:1px solid ${statusBorder};border-radius:12px;padding:11px 13px;display:flex;align-items:flex-start;gap:10px;min-width:0;box-sizing:border-box">
        <ha-icon icon="${statusIcon}" style="color:${statusColor};--mdc-icon-size:22px;flex-shrink:0;margin-top:1px"></ha-icon>
        <div style="flex:1;min-width:0;white-space:normal !important">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:5px;flex-wrap:wrap">
            <span style="font-size:12.5px;font-weight:700;color:${statusColor};white-space:nowrap">預估 Bot 使用狀況</span>
            <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;background:${statusColor};color:#fff;white-space:nowrap;flex-shrink:0">${statusLabel}</span>
          </div>
          <div style="font-size:12.5px;line-height:1.55;color:var(--primary-text-color);white-space:normal !important;word-break:break-word;overflow-wrap:anywhere">
            <div style="font-weight:600;white-space:normal !important">${desc1}</div>
            ${desc2 ? `<div style="font-size:12px;color:var(--secondary-text-color);margin-top:3px;white-space:normal !important">${desc2}</div>` : ''}
          </div>
        </div>
      </div>

      <div style="font-size:11.5px;color:var(--secondary-text-color);line-height:1.4;display:flex;align-items:center;gap:5px;flex-wrap:wrap">
        <ha-icon icon="mdi:information-outline" style="--mdc-icon-size:14px;flex-shrink:0"></ha-icon>
        <span>已達 196 則自動切換下個 Bot · 群組每則約耗 5 額度 · 每月 1 日重置</span>
      </div>
    </div>
  `;
]]]"""
    L.append("      - type: custom:button-card")
    L.append("        entity: sensor.line_bot_in_use")
    L.append("        show_name: false")
    L.append("        show_icon: false")
    L.append("        show_state: false")
    L.append("        styles:")
    L.append("          card:")
    L.append("            - border-radius: 18px")
    L.append("            - border: none")
    L.append("            - box-shadow: 0 1px 2px rgba(0,0,0,.18)")
    L.append("            - padding: 0")
    L.append("            - white-space: normal")
    L.append("          grid:")
    L.append("            - grid-template-areas: '\"body\"'")
    L.append("            - grid-template-columns: 1fr")
    L.append("          custom_fields:")
    L.append("            body:")
    L.append("              - width: 100%")
    L.append("              - min-width: 0")
    L.append("              - text-align: left")
    L.append("              - white-space: normal")
    L.append("        custom_fields:")
    L.append("          body: |")
    for ln in status_js.splitlines():
        L.append("            " + ln)
    return L


def quota_settings():
    rows = [("input_select.line_bot_mode", "LINE Bot 模式"), ("input_number.line_bot_sticky", "主用 Bot（Auto 沿用）"),
            ("input_boolean.line_bot_test_mode", "測試模式"), ("input_boolean.line_bot_custom_user_enable", "自訂目標 ID 啟用"),
            ("input_text.line_bot_custom_user_id", "自訂目標 ID")]
    return heading("LINE Bot 設定", "mdi:robot-outline") + entities_card(rows)


def linebot_forecast_banner():
    """LINE Bot 全月預測診斷卡片：顯示日發送率、一般 Bot 耗盡日、緊急 Bot 狀態、重置倒數與診斷。"""
    js = """[[[
  const f = states['sensor.line_bot_forecast'];
  if (!f || !f.attributes) return '<div style="padding:14px;text-align:center">LINE Bot 預測載入中...</div>';
  const a = f.attributes;
  const st = f.state;
  
  let bgGradient, statusTitle, statusBadge, badgeBg, badgeFg, iconName, iconColor;
  if (st === 'safe') {
    bgGradient = 'linear-gradient(135deg, rgba(48,209,88,.14) 0%, rgba(48,209,88,.04) 100%)';
    statusTitle = '本月額度充裕（無需動用緊急Bot）';
    statusBadge = '安全充裕';
    badgeBg = 'rgba(48,209,88,.2)';
    badgeFg = '#30D158';
    iconName = 'mdi:check-circle';
    iconColor = '#30D158';
  } else if (st === 'need_emergency') {
    bgGradient = 'linear-gradient(135deg, rgba(255,159,10,.16) 0%, rgba(255,159,10,.04) 100%)';
    statusTitle = `預估 ${a.normal_exhaust_day || '中旬'} 號動用緊急Bot（可撐至月底）`;
    statusBadge = '備援預備';
    badgeBg = 'rgba(255,159,10,.2)';
    badgeFg = '#FF9F0A';
    iconName = 'mdi:alert-circle';
    iconColor = '#FF9F0A';
  } else {
    bgGradient = 'linear-gradient(135deg, rgba(255,69,58,.16) 0%, rgba(255,69,58,.04) 100%)';
    statusTitle = `額度告急（預估 ${a.total_exhaust_date ? a.total_exhaust_date.slice(5).replace('-', '/') : '月底前'} 耗盡）`;
    statusBadge = '額度告急';
    badgeBg = 'rgba(255,69,58,.2)';
    badgeFg = '#FF453A';
    iconName = 'mdi:alert-octagon';
    iconColor = '#FF453A';
  }

  const normalDate = a.normal_exhaust_date ? a.normal_exhaust_date.slice(5).replace('-', '/') : '--';

  const rawSummary = a.summary || '';
  const parts = rawSummary.split(/[；;]/);
  const part1 = parts[0] ? parts[0].trim() : '';
  const part2 = parts[1] ? parts.slice(1).join('；').trim() : '';

  return `
    <div style="background:${bgGradient};border-radius:18px;padding:16px;box-shadow:0 1px 2px rgba(0,0,0,.18);min-width:0;width:100%;box-sizing:border-box">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:12px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:8px;min-width:0;flex:1">
          <ha-icon icon="${iconName}" style="color:${iconColor};--mdc-icon-size:22px;flex-shrink:0"></ha-icon>
          <span style="font-size:15px;font-weight:700;line-height:1.35;word-break:break-word;white-space:normal !important">${statusTitle}</span>
        </div>
        <span style="font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:999px;background:${badgeBg};color:${badgeFg};white-space:nowrap;flex-shrink:0">${statusBadge}</span>
      </div>
      
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(125px, 1fr));gap:8px;margin:12px 0;padding:10px 12px;background:rgba(120,120,128,.1);border-radius:12px">
        <div>
          <div style="font-size:11px;color:var(--secondary-text-color)">日均消耗率</div>
          <div style="font-size:16px;font-weight:700;color:var(--primary-text-color)">${a.daily_rate || 0} <span style="font-size:12px;font-weight:normal">則/天</span></div>
        </div>
        <div>
          <div style="font-size:11px;color:var(--secondary-text-color)">一般 Bot 預估至</div>
          <div style="font-size:16px;font-weight:700;color:${a.need_emergency ? '#FF9F0A' : '#30D158'}">${normalDate} <span style="font-size:12px;font-weight:normal">(${a.normal_days_left || 0}天)</span></div>
        </div>
        <div>
          <div style="font-size:11px;color:var(--secondary-text-color)">緊急 Bot (智慧家庭A)</div>
          <div style="font-size:16px;font-weight:700;color:var(--primary-text-color)">剩餘 ${a.emergency_remaining || 0} <span style="font-size:12px;font-weight:normal">則備援</span></div>
        </div>
        <div>
          <div style="font-size:11px;color:var(--secondary-text-color)">每月 1 日重置倒數</div>
          <div style="font-size:16px;font-weight:700;color:var(--primary-text-color)">${a.days_left_in_month || 0} <span style="font-size:12px;font-weight:normal">天</span></div>
        </div>
      </div>

      <div style="margin-top:10px;padding:10px 12px;background:rgba(120,120,128,.12);border-radius:12px;display:flex;align-items:flex-start;gap:8px;min-width:0;box-sizing:border-box">
        <span style="font-size:15px;flex-shrink:0;line-height:1.2;margin-top:1px">💡</span>
        <div style="flex:1;min-width:0;white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;line-height:1.5">
          <div style="font-size:13px;font-weight:600;color:var(--primary-text-color);white-space:normal !important">${part1}</div>
          ${part2 ? `<div style="font-size:12px;color:var(--secondary-text-color);margin-top:3px;white-space:normal !important">${part2}</div>` : ''}
        </div>
      </div>
    </div>
  `;
]]]"""
    L = ["      - type: custom:button-card",
         "        entity: sensor.line_bot_forecast",
         "        show_name: false", "        show_icon: false", "        show_state: false",
         "        styles:", "          card:", "            - border-radius: 18px", "            - border: none",
         "            - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "            - padding: 0",
         "            - white-space: normal",
         "          grid:", "            - grid-template-areas: '\"body\"'", "            - grid-template-columns: 1fr",
         "          custom_fields:", "            body:", "              - width: 100%",
         "              - min-width: 0", "              - text-align: left", "              - white-space: normal",
         "        custom_fields:", "          body: |"]
    for ln in js.splitlines():
        L.append("            " + ln)
    return L


def filter_life_section():
    """空氣清淨機濾網壽命卡片（高階 iOS 風格 custom:button-card）。"""
    js = """[[[
  const s = states['sensor.kong_qi_qing_jing_ji_filter_life_remaining'];
  const lvl = s ? parseInt(s.state, 10) || 0 : 0;
  const notified = states['input_boolean.supply_filter_notified']?.state === 'on';
  
  let color, bgGradient, statusDesc;
  if (lvl <= 5) {
    color = '#FF453A';
    bgGradient = 'linear-gradient(135deg, rgba(255,69,58,.16) 0%, rgba(255,69,58,.04) 100%)';
    statusDesc = '已達臨界壽命，請立即更換濾網';
  } else if (lvl <= 10) {
    color = '#FF9F0A';
    bgGradient = 'linear-gradient(135deg, rgba(255,159,10,.16) 0%, rgba(255,159,10,.04) 100%)';
    statusDesc = '濾網壽命偏低，請準備備用濾芯';
  } else {
    color = '#30D158';
    bgGradient = 'linear-gradient(135deg, rgba(48,209,88,.14) 0%, rgba(48,209,88,.04) 100%)';
    statusDesc = '濾網狀態良好，壽命充足';
  }

  return `
    <div style="background:${bgGradient};border-radius:18px;padding:16px;box-shadow:0 1px 2px rgba(0,0,0,.18)">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:42px;height:42px;border-radius:12px;background:${color}22;color:${color};display:flex;align-items:center;justify-content:center;flex:none">
            <ha-icon icon="mdi:air-filter" style="--mdc-icon-size:24px"></ha-icon>
          </div>
          <div>
            <div style="font-weight:700;font-size:16px;color:var(--primary-text-color)">空氣清淨機濾網壽命</div>
            <div style="font-size:12.5px;color:${color};font-weight:600;margin-top:2px">${statusDesc}</div>
          </div>
        </div>
        <div style="text-align:right">
          <span style="font-size:26px;font-weight:800;color:${color}">${lvl}<small style="font-size:16px">%</small></span>
        </div>
      </div>

      <div style="height:8px;border-radius:999px;background:rgba(120,120,128,.18);margin:14px 0 10px;overflow:hidden">
        <div style="width:${Math.max(lvl, 2)}%;height:100%;background:${color};border-radius:999px;box-shadow:0 0 8px ${color}66;transition:width 0.4s"></div>
      </div>

      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:11.5px;color:var(--secondary-text-color)">
        <span style="padding:2px 8px;border-radius:6px;background:rgba(120,120,128,.1)">門檻：≤10% 提醒備品 · ≤5% 請更換</span>
        <span style="padding:2px 8px;border-radius:6px;background:${notified ? 'rgba(255,159,10,.2)' : 'rgba(120,120,128,.1)'};color:${notified ? '#FF9F0A' : 'inherit'};font-weight:${notified ? '600' : 'normal'}">
          ${notified ? '⚠️ 已發出更換通知' : '尚未發送通知'}
        </span>
      </div>
    </div>
  `;
]]]"""
    card = [
        "      - type: custom:button-card",
        "        entity: sensor.kong_qi_qing_jing_ji_filter_life_remaining",
        "        show_name: false", "        show_icon: false", "        show_state: false",
        "        styles:", "          card:", "            - border-radius: 18px", "            - border: none",
        "            - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "            - padding: 0",
        "          grid:", "            - grid-template-areas: '\"body\"'", "            - grid-template-columns: 1fr",
        "        custom_fields:", "          body: |",
    ]
    for ln in js.splitlines():
        card.append("            " + ln)
    rows = [
        ("input_boolean.supply_filter_notified", "濾網更換已通知旗標"),
    ]
    return heading("空氣清淨機濾網", "mdi:air-filter") + card + entities_card(rows)


def battery_forecast_section():
    """9 大感測器電池壽命預估清單卡片（高階 iOS 風格搭配色彩與進度指標，清楚換行排版）。"""
    js = """[[[
  const f = states['sensor.battery_forecast'];
  if (!f || !f.attributes || !f.attributes.items) {
    return '<div style="padding:16px;text-align:center;color:var(--secondary-text-color)">尚無電池預測數據，請點擊下方測試按鈕或等待系統每日 03:50 自動計算。</div>';
  }
  const items = f.attributes.items;
  const names = {
    'gar': '鐵門感應器', 'door': '客廳門鎖', 'study': '書房感應開關',
    'cube': '客廳魔方', 'toiletm': '二樓廁所感應', 'kitchenm': '廚房人體感應',
    'nightl': '廁所夜燈', 'bell': '二樓門口電鈴', 'kswitch': '廚房無線開關'
  };

  const getBatteryIcon = (lvl) => {
    if (lvl <= 5) return 'mdi:battery-alert';
    if (lvl <= 15) return 'mdi:battery-10';
    if (lvl <= 35) return 'mdi:battery-30';
    if (lvl <= 65) return 'mdi:battery-50';
    if (lvl <= 85) return 'mdi:battery-70';
    return 'mdi:battery';
  };

  let rowsHtml = '';
  for (const [k, d] of Object.entries(items)) {
    const name = names[k] || k;
    const lvl = Math.round(d.level || 0);
    const emptyLvl = d.empty || 10;
    const isEmpty = d.status === 'empty' || lvl <= emptyLvl;
    const isStable = d.status === 'stable';
    
    let color, rowBg, tagText, tagBg, tagFg;
    if (isEmpty) {
      color = '#FF453A';
      rowBg = 'rgba(255,69,58,.12);border:1px solid rgba(255,69,58,.3)';
      tagText = '更換門檻';
      tagBg = 'rgba(255,69,58,.22)';
      tagFg = '#FF453A';
    } else if (lvl <= 35) {
      color = '#FF9F0A';
      rowBg = 'rgba(255,159,10,.1);border:1px solid rgba(255,159,10,.25)';
      tagText = '偏低';
      tagBg = 'rgba(255,159,10,.2)';
      tagFg = '#FF9F0A';
    } else if (isStable) {
      color = '#0A84FF';
      rowBg = 'rgba(120,120,128,.08);border:1px solid rgba(120,120,128,.14)';
      tagText = '平穩';
      tagBg = 'rgba(10,132,255,.18)';
      tagFg = '#0A84FF';
    } else {
      color = '#30D158';
      rowBg = 'rgba(120,120,128,.08);border:1px solid rgba(120,120,128,.14)';
      tagText = '正常';
      tagBg = 'rgba(48,209,88,.18)';
      tagFg = '#30D158';
    }

    let line1 = '', line2 = '';
    if (isEmpty) {
      line1 = `<span style="color:#FF453A;font-weight:700">⚠️ 已達更換門檻（≤ ${emptyLvl}%）</span>`;
      line2 = '<span style="color:#FF453A">請儘速更換電池以確保穩定運作</span>';
    } else if (d.days != null && d.days > 0) {
      line1 = `預估可用 <b style="font-size:13.5px;color:var(--primary-text-color)">${Math.round(d.days)}</b> 天`;
      line2 = `至 ${d.date} · 日耗 ${d.rate}%/天`;
    } else if (isStable) {
      line1 = '<span style="color:#0A84FF;font-weight:600">滿電平穩 · 壽命充足</span>';
      line2 = `持續運作 ${Math.round(d.span_days || 0)} 天無掉格`;
    } else {
      line1 = '壽命評估中';
      line2 = '持續收集放電曲線數據';
    }

    const icon = getBatteryIcon(lvl);

    rowsHtml += `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:14px;background:${rowBg};gap:10px;min-width:0;box-sizing:border-box">
        <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
          <div style="width:36px;height:36px;border-radius:10px;background:${color}22;color:${color};display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <ha-icon icon="${icon}" style="--mdc-icon-size:22px"></ha-icon>
          </div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
              <span style="font-weight:700;font-size:14.5px;color:var(--primary-text-color)">${name}</span>
              <span style="font-size:11px;font-weight:700;padding:1px 7px;border-radius:6px;background:${tagBg};color:${tagFg};white-space:nowrap">${tagText}</span>
            </div>
            <div style="font-size:12.5px;margin-top:3px;line-height:1.35;white-space:normal !important;word-break:break-word">
              ${line1}
            </div>
            <div style="font-size:11.5px;color:var(--secondary-text-color);margin-top:2px;line-height:1.35;white-space:normal !important;word-break:break-word">
              ${line2}
            </div>
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div style="font-size:18px;font-weight:800;color:${color}">${lvl}<small style="font-size:12px">%</small></div>
          <div style="width:42px;height:5px;border-radius:999px;background:rgba(120,120,128,.2);margin-top:4px;overflow:hidden">
            <div style="width:${Math.max(lvl, 2)}%;height:100%;background:${color};border-radius:999px"></div>
          </div>
        </div>
      </div>
    `;
  }

  return `
    <div style="background:var(--card-background-color,#1c1c1e);border-radius:18px;padding:14px;box-shadow:0 1px 2px rgba(0,0,0,.18);min-width:0;box-sizing:border-box">
      <div style="display:flex;flex-direction:column;gap:8px">
        ${rowsHtml}
      </div>
    </div>
  `;
]]]"""
    card = [
        "      - type: custom:button-card",
        "        entity: sensor.battery_forecast",
        "        show_name: false", "        show_icon: false", "        show_state: false",
        "        styles:", "          card:", "            - border-radius: 18px", "            - border: none",
        "            - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "            - padding: 0",
        "            - white-space: normal",
        "          grid:", "            - grid-template-areas: '\"body\"'", "            - grid-template-columns: 1fr",
        "          custom_fields:", "            body:", "              - width: 100%",
        "              - min-width: 0", "              - text-align: left", "              - white-space: normal",
        "        custom_fields:", "          body: |",
    ]
    for ln in js.splitlines():
        card.append("            " + ln)
    return heading("9 大感測器電池壽命預估", "mdi:battery-clock-outline") + card


def supply_control_section():
    """耗材監控設定與操作按鈕。"""
    rows = [
        ("input_boolean.notify_supply_extra_line_enable", "耗材更換額外 LINE 推播"),
        ("input_datetime.supply_battery_report_time", "耗材定期摘要時間"),
        ("input_button.battery_system_test_trigger", "測試耗材電量系統"),
    ]
    return heading("耗材監控設定與操作", "mdi:tune-variant") + entities_card(rows)


def supply_view(title, path, icon, autos):
    """耗材與額度分頁（依裝置尺寸響應式排版）：
    - 三欄（橫向寬螢幕）：Col 1 LINE Bot 全套、Col 2 電池壽命+耗材設定、Col 3 清淨機濾網+自動化（三欄維持不變）
    - 雙欄（iPad 直向/中寬度）：Col 1 LINE Bot 全套、Col 2 電池壽命 ➔ 清淨機濾網（在上）➔ 耗材設定（在下）➔ 自動化
    - 單欄（手機/窄視窗）：LINE Bot 全套 ➔ 電池壽命 ➔ 清淨機濾網（在上）➔ 耗材設定（在下）➔ 自動化
    採用 custom:grid-layout 搭配 mediaquery 精準達成各裝置尺寸響應排版。
    """
    auto_rows = [(eid, fn) for fn, eid in sorted(autos.get("supply", []))]
    has_auto = bool(auto_rows)

    col1_cards = (
        heading("LINE Bot 全月預測診斷", "mdi:chart-timeline-variant")
        + linebot_forecast_banner()
        + quota_section()
        + quota_settings()
    )
    battery_cards = battery_forecast_section()
    filter_cards = filter_life_section()
    settings_cards = supply_control_section()
    auto_cards = heading("耗材相關自動化", "mdi:robot") + entities_card(auto_rows) if has_auto else []

    if has_auto:
        areas_3col = '        "col1 battery filter"\n        "col1 settings auto"'
        areas_2col = '            "col1 battery"\n            "col1 filter"\n            "col1 settings"\n            "col1 auto"'
        areas_1col = '            "col1"\n            "battery"\n            "filter"\n            "settings"\n            "auto"'
    else:
        areas_3col = '        "col1 battery filter"\n        "col1 settings ."'
        areas_2col = '            "col1 battery"\n            "col1 filter"\n            "col1 settings"'
        areas_1col = '            "col1"\n            "battery"\n            "filter"\n            "settings"'

    L = [
        f"  - title: {q(title)}",
        f"    path: {path}",
        f"    icon: {icon}",
        "    type: custom:grid-layout",
        "    layout:",
        "      grid-template-columns: repeat(3, minmax(280px, 1fr))",
        "      grid-gap: 8px",
        "      margin: 0",
        "      align-items: start",
        "      grid-template-areas: |",
        areas_3col,
        "      mediaquery:",
        '        "(max-width: 768px)":',
        "          grid-template-columns: minmax(0, 1fr)",
        "          grid-template-areas: |",
        areas_1col,
        '        "(max-width: 1024px)":',
        "          grid-template-columns: repeat(2, minmax(280px, 1fr))",
        "          grid-template-areas: |",
        areas_2col,
        "    cards:",
    ]

    def _grid_stack(area, cards_lines):
        out = [
            "      - type: vertical-stack",
            "        view_layout:",
            f"          grid-area: {area}",
            "        cards:",
        ]
        for ln in cards_lines:
            out.append("  " + ln)
        return out

    L += _grid_stack("col1", col1_cards)
    L += _grid_stack("battery", battery_cards)
    L += _grid_stack("filter", filter_cards)
    L += _grid_stack("settings", settings_cards)
    if has_auto:
        L += _grid_stack("auto", auto_cards)

    return L


def _text_card(entity, js):
    """通用 button-card 外殼：無邊框圓角、文字一律自動換行不溢出。"""
    L = ["      - type: custom:button-card", f"        entity: {entity}",
         "        show_name: false", "        show_icon: false", "        show_state: false",
         "        styles:", "          card:", "            - border-radius: 18px", "            - border: none",
         "            - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "            - padding: 0",
         "            - white-space: normal", "            - overflow: hidden",
         "          grid:", "            - grid-template-areas: '\"body\"'", "            - grid-template-columns: minmax(0, 1fr)",
         "          custom_fields:", "            body:", "              - width: 100%",
         "              - min-width: 0", "              - text-align: left", "              - white-space: normal",
         "        custom_fields:", "          body: |"]
    for ln in js.splitlines():
        L.append("            " + ln)
    return L


DISASTER_JS = r"""[[[
  const raw = (entity && entity.state) || '';
  const bad = ['', 'unknown', 'unavailable', 'None', 'none'];
  const s = bad.includes(raw) ? '' : String(raw).trim();
  const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const calm = !s || /^(無|目前無|沒有|正常)/.test(s);
  const lamps = { '紅色': ['#FF453A', 'rgba(255,69,58,.16)'], '橙色': ['#FF9F0A', 'rgba(255,159,10,.16)'], '黃色': ['#FFD60A', 'rgba(255,214,10,.16)'] };
  const re = /([^，。()（）]*?局部地區)有([^()（）]*?)[(（](紅色|橙色|黃色)燈號[)）]/g;
  const items = [];
  let m;
  while ((m = re.exec(s)) !== null) items.push({ region: m[1].trim(), cond: m[2].trim(), lamp: m[3] });
  let top = null;
  for (const k of ['紅色', '橙色', '黃色']) { if (s.includes(k)) { top = k; break; } }
  let color, bg, label, icon;
  if (calm) { color = '#30D158'; bg = 'linear-gradient(135deg, rgba(48,209,88,.14) 0%, rgba(48,209,88,.04) 100%)'; label = '目前無警報'; icon = 'mdi:shield-check'; }
  else if (top) { color = lamps[top][0]; bg = `linear-gradient(135deg, ${lamps[top][1]} 0%, rgba(120,120,128,.04) 100%)`; label = top + '燈號'; icon = 'mdi:alert-octagon'; }
  else { color = '#FF9F0A'; bg = 'linear-gradient(135deg, rgba(255,159,10,.16) 0%, rgba(255,159,10,.04) 100%)'; label = '災防通知'; icon = 'mdi:alert-circle'; }
  const lead = items.length ? s.split('，')[0] : '';
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  let body = '';
  if (calm) {
    body = `<div style="font-size:13.5px;color:var(--primary-text-color);${wrap}">${s ? esc(s) : '目前沒有任何災害防護告警訊息。'}</div>`;
  } else if (items.length) {
    body = (lead ? `<div style="font-size:13px;font-weight:600;line-height:1.5;margin-bottom:8px;color:var(--primary-text-color);${wrap}">${esc(lead)}</div>` : '') +
      items.map(it => {
        const c = lamps[it.lamp];
        return `<div style="display:flex;gap:10px;align-items:flex-start;padding:10px 12px;margin-top:6px;border-radius:12px;background:${c[1]};border:1px solid ${c[0]}55;min-width:0;box-sizing:border-box">
          <span style="flex-shrink:0;margin-top:4px;width:10px;height:10px;border-radius:50%;background:${c[0]};box-shadow:0 0 6px ${c[0]}"></span>
          <div style="flex:1;min-width:0;${wrap}">
            <div style="font-size:12px;font-weight:700;color:${c[0]};margin-bottom:2px">${it.lamp}燈號</div>
            <div style="font-size:13px;line-height:1.5;color:var(--primary-text-color);${wrap}">${esc(it.region)}</div>
            <div style="font-size:12px;line-height:1.45;color:var(--secondary-text-color);margin-top:2px;${wrap}">${esc(it.cond)}</div>
          </div></div>`;
      }).join('') +
      `<details style="margin-top:10px"><summary style="font-size:12px;color:var(--secondary-text-color);cursor:pointer">查看完整內容</summary><div style="font-size:12.5px;line-height:1.55;margin-top:6px;color:var(--secondary-text-color);${wrap}">${esc(s)}</div></details>`;
  } else {
    body = `<div style="font-size:13.5px;line-height:1.6;color:var(--primary-text-color);${wrap}">${esc(s)}</div>`;
  }
  const upd = entity && entity.last_changed ? new Date(entity.last_changed) : null;
  const updTxt = upd ? `${upd.getMonth() + 1}/${upd.getDate()} ${String(upd.getHours()).padStart(2, '0')}:${String(upd.getMinutes()).padStart(2, '0')}` : '--';
  return `
    <div style="background:${bg};border-radius:18px;padding:16px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:10px">
        <div style="display:flex;align-items:center;gap:8px;min-width:0;flex:1">
          <div style="width:36px;height:36px;border-radius:10px;background:${color}26;color:${color};display:flex;align-items:center;justify-content:center;flex-shrink:0"><ha-icon icon="${icon}" style="--mdc-icon-size:22px"></ha-icon></div>
          <span style="font-size:15px;font-weight:700;color:var(--primary-text-color)">氣象與災害告警</span>
        </div>
        <span style="font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:999px;background:${color};color:#fff;white-space:nowrap;flex-shrink:0">${label}</span>
      </div>
      ${body}
      <div style="font-size:11px;color:var(--secondary-text-color);margin-top:10px">更新於 ${updTxt}</div>
    </div>`;
]]]"""

EARTHQUAKE_JS = r"""[[[
  const raw = (entity && entity.state) || '';
  const bad = ['', 'unknown', 'unavailable', 'None', 'none'];
  const s = bad.includes(raw) ? '' : String(raw).trim();
  const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const mm = s.match(/^(\d{1,2}\/\d{1,2})\s*(\d{1,2}:\d{2})\s*(.*?)發生規模\s*([\d.]+)\s*(有感)?地震[，,]?\s*(.*?)。?$/);
  const mag = mm ? parseFloat(mm[4]) : NaN;
  let color = '#30D158';
  if (!isNaN(mag)) color = mag >= 6 ? '#FF453A' : (mag >= 5 ? '#FF9F0A' : (mag >= 4 ? '#FFD60A' : '#30D158'));
  const bg = `linear-gradient(135deg, ${color}2b 0%, rgba(120,120,128,.04) 100%)`;
  let body = '';
  if (mm) {
    const intens = mm[6] ? mm[6].replace(/^最大震度/, '') : '';
    const im = intens.match(/^(.*?)(\d+[弱強]?級?)$/);
    const place = im ? im[1].trim() : intens;
    const lvl = im ? im[2] : '';
    const cell = (k, v, big) => `<div style="min-width:0;${wrap}"><div style="font-size:11px;color:var(--secondary-text-color)">${k}</div><div style="font-size:${big ? 22 : 14}px;font-weight:${big ? 800 : 700};color:${big ? color : 'var(--primary-text-color)'};line-height:1.3;${wrap}">${v}</div></div>`;
    body = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;padding:12px;background:rgba(120,120,128,.1);border-radius:12px">
      ${cell('規模', 'M ' + esc(mm[4]), true)}
      ${cell('最大震度', esc((place ? place + ' ' : '') + lvl) || '--', false)}
      ${cell('發生時間', esc(mm[1] + ' ' + mm[2]), false)}
      ${cell('震央位置', esc(mm[3].trim() || '--'), false)}
    </div>`;
  } else if (s) {
    body = `<div style="font-size:13.5px;line-height:1.6;color:var(--primary-text-color);${wrap}">${esc(s)}</div>`;
  } else {
    body = `<div style="font-size:13.5px;color:var(--primary-text-color)">目前沒有地震速報資料。</div>`;
  }
  const label = isNaN(mag) ? '地震速報' : (mag >= 6 ? '強震' : (mag >= 5 ? '中強震' : (mag >= 4 ? '有感地震' : '小區域地震')));
  return `
    <div style="background:${bg};border-radius:18px;padding:16px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:10px">
        <div style="display:flex;align-items:center;gap:8px;min-width:0;flex:1">
          <div style="width:36px;height:36px;border-radius:10px;background:${color}26;color:${color};display:flex;align-items:center;justify-content:center;flex-shrink:0"><ha-icon icon="mdi:pulse" style="--mdc-icon-size:22px"></ha-icon></div>
          <span style="font-size:15px;font-weight:700;color:var(--primary-text-color)">最新地震報告</span>
        </div>
        <span style="font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:999px;background:${color};color:#fff;white-space:nowrap;flex-shrink:0">${label}</span>
      </div>
      ${body}
    </div>`;
]]]"""


def disaster_blocks():
    return [section(heading("氣象與災害告警", "mdi:weather-hurricane") + _text_card("sensor.disaster", DISASTER_JS)),
            section(heading("最新地震報告", "mdi:pulse") + _text_card("sensor.earthquake", EARTHQUAKE_JS))]


def family_tracking_blocks():
    """系統維護 > 家人裝置追蹤：每位家人的主要裝置選單，加上 person.* 目前實際參考哪個裝置（00-2S／packages/v41_person_main_device.yaml）。"""
    md = (
        "{% set P = [('kenny','Kenny'),('iris','Iris'),('jerry','Jerry'),('elay','Elay')] %}"
        "| 家人 | person 狀態 | person 目前參考的裝置 | 該裝置狀態 |\n|---|---|---|---|\n"
        "{% for k, n in P %}{% set sn = 'sensor.person_' ~ k ~ '_source_device' %}"
        "| **{{ n }}** | {{ '在家' if is_state('person.' ~ k, 'home') else ('離家' if is_state('person.' ~ k, 'not_home') else states('person.' ~ k)) }} "
        "| {{ states(sn) }}<br><sub>{{ state_attr(sn, 'source_entity') }}</sub> "
        "| {{ '在家' if state_attr(sn, 'source_state') == 'home' else ('離家' if state_attr(sn, 'source_state') == 'not_home' else state_attr(sn, 'source_state')) }} |\n"
        "{% endfor %}"
        "\n<sub>person.* 是 YAML 定義，在不在家都由它參考的裝置決定。在下面選「主要裝置」會改寫 persons.yaml 並重新載入 person；"
        "為避免切換後在家狀態突然改變而誤觸發離家／到家情境，選的裝置目前的在家狀態必須和該家人目前一致，否則會退回原選項並發 HA 通知。</sub>"
    )
    rows = [(f"input_select.person_main_device_{k}", f"{n} 的主要裝置") for k, n in
            (("kenny", "Kenny"), ("iris", "Iris"), ("jerry", "Jerry"), ("elay", "Elay"))]
    return [
        section(heading("家人裝置追蹤", "mdi:account-switch-outline") + ["      - type: markdown", "        content: " + q(md)] + MD_CSS),
        section(heading("家人主要裝置選擇", "mdi:cellphone-check") + entities_card(rows)),
    ]


def manual_button(script, result_entity, name, icon):
    """按鈕：點一下呼叫 script；腳本結束後 15 秒內，按鈕下方顯示「✓ …已送出」或「⚠ 原因」（結果存在 result_entity：訊息|時間戳）。"""
    return ["      - type: custom:button-card", f"        entity: {result_entity}", f"        name: {name}",
            f"        icon: {icon}", "        show_state: false", "        show_label: true", "        triggers_update: all", "        haptic: success",
            "        tap_action:", "          action: call-service", f"          service: {script}",
            "        label: |", "          [[[",
            f"            if (states['{script}'] && states['{script}'].state === 'on') return '處理中…';",
            "            const v = (entity && entity.state) || ''; const k = v.lastIndexOf('|');",
            "            if (k < 0) return '';",
            "            const age = Date.now() / 1000 - parseInt(v.slice(k + 1), 10);",
            "            return age >= 0 && age < 15 ? v.slice(0, k) : '';",
            "          ]]]",
            "        styles:", "          card:", "            - border-radius: 14px", "            - border: 1.5px solid #0A84FF", "            - padding: 12px", "            - background: transparent",
            "          grid:", "            - grid-template-areas: '\"i n\" \"i l\"'", "            - grid-template-columns: 40px 1fr", "            - text-align: left",
            "          icon:", "            - color: '#0A84FF'", "            - width: 26px",
            "          name:", "            - color: '#0A84FF'", "            - font-weight: 700", "            - font-size: 15px", "            - justify-self: start",
            "          label:", "            - font-size: 12px", "            - justify-self: start", "            - color: '#34C759'", "            - font-weight: 600"]


def manual_notify_section():
    """總覽首頁的「手動通知」：輸入內容、勾選 HA／LINE、選擇重要性，標題固定「系統通知訊息」。"""
    rows = ["{entity: input_text.notify_manual_text, name: \"通知內容\", icon: \"mdi:message-text-outline\"}",
            ("input_select.notify_manual_level", "重要性（資訊／一般／重要／緊急）"),
            ("input_boolean.notify_manual_ha", "HA 通知"), ("input_boolean.notify_manual_line", "LINE"),
            ("input_boolean.notify_manual_clear", "發送後清除內容")]
    return heading("手動通知（標題：系統通知訊息）", "mdi:message-alert-outline") + entities_card(rows) + manual_button("script.notify_manual", "input_text.notify_manual_result", "傳送通知", "mdi:send")


def manual_broadcast_section():
    """總覽首頁的「手動廣播」：輸入文字、勾選喇叭、選擇重要性，按下按鈕呼叫 script.announce_manual。"""
    rows = ["{entity: input_text.announce_manual_text, name: \"廣播內容\", icon: \"mdi:message-text-outline\"}", ("input_select.announce_manual_level", "重要性（一般／重要／緊急）"),
            ("input_boolean.announce_manual_ke_ting_homepod", "客廳 HomePod"), ("input_boolean.announce_manual_ding_lou_homepod", "頂樓 HomePod"),
            ("input_boolean.announce_manual_si_lou_homepod", "四樓 HomePod mini"), ("input_boolean.announce_manual_che_ku_speaker", "車庫攝影機喇叭"),
            ("input_boolean.announce_manual_wu_lou_speaker", "頂樓攝影機喇叭"), ("input_boolean.announce_manual_clear", "發送後清除內容")]
    btn = manual_button("script.announce_manual", "input_text.announce_manual_result", "發送廣播", "mdi:bullhorn")
    return heading("手動廣播", "mdi:bullhorn-outline") + entities_card(rows) + btn


def overview_sections(autos, stale):
    def _auto_eid(prefix, default):
        """依自動化名稱開頭找實體 ID（版號改了、實體 ID 後綴會跟著不同，不寫死）。"""
        for v in autos.values():
            for fn, eid in v:
                if fn.startswith(prefix):
                    return eid
        return default
    total = sum(len(v) for v in autos.values())
    intro = (f"啟用中的自動化 **{total}** 支（另有 {stale} 筆已失效的舊自動化殘留，可到「設定 → 自動化」清理）。"
             "上方分頁依功能分類，每頁有該類自動化的開關與可調整的參數。")
    quick = [("input_boolean.notify_line_general_enable", "LINE 通知｜一般"), ("input_boolean.notify_line_important_enable", "LINE 通知｜重要"),
             ("input_boolean.notify_line_emergency_enable", "LINE 通知｜緊急"), ("input_boolean.notify_line_doorbell_enable", "LINE 通知｜大門門鈴"),
             ("input_boolean.notify_ha_info_enable", "HA 通知｜資訊級"), ("input_boolean.notify_ha_general_enable", "HA 通知｜一般級"),
             ("input_boolean.notify_ha_important_enable", "HA 通知｜重要級"),
             ("input_boolean.mood_alert_enable", "氣氛燈提醒｜總開關"), ("input_boolean.mood_alert_important_enable", "氣氛燈提醒｜重要級"),
             ("input_boolean.mood_alert_emergency_enable", "氣氛燈提醒｜緊急級"), ("input_boolean.mood_alert_ap_off", "機台氣氛燈｜停用通知閃爍"),
             ("input_boolean.ambient_scene_off", "機台氣氛燈｜停用情境色"), ("input_boolean.scene_announce_enable", "情境執行廣播"),
             ("input_number.announce_volume_general", "廣播音量｜一般"), ("input_number.announce_volume_important", "廣播音量｜重要"),
             ("input_number.announce_volume_emergency", "廣播音量｜緊急")]
    gateways = [("input_boolean.jie_chu_wang_guan_jing_bao", "解除網關警報"),
                ("alarm_control_panel.54ef44cf58f9_alarm", "Aqara 網關警報"),
                ("input_boolean.aqara_zai_jia", "Aqara 在家"),
                ("input_boolean.aqara_li_jia", "Aqara 離家"),
                ("input_boolean.aqara_wan_an", "Aqara 晚安"),
                ("switch.smartpower_strip_2f_asussi_fu_qi", "Asus 伺服器電源"),
                ("switch.smartpower_strip_2f_udmse", "UDM-SE 電源"),
                ("switch.smartpower_strip_2f_tbcwang_lu_he", "TBC 網路盒電源"),
                ("switch.xiao_yan_wang_guan_cha_zuo", "小燕網關插座"),
                (_auto_eid("106C", "automation.106c_jie_chu_wang_guan_jing_bao_zheng_he_ai_v4_1_0"), "106C_解除網關警報整合AI"),
                ("automation.ai_gateway_anomaly_guard", "106網關系統AI"),
                ("automation.ai_00_01_xiaoyan_gateway_watchdog", "小燕網關看門狗")]
    top = [("input_boolean.topfloor_motion_pause", "頂樓感應暫停"), ("input_boolean.sleep_silent_active", "頂樓深夜熟睡手動鎖"),
           ("input_select.topfloor_webhook_mode", "頂樓 Webhook 判斷模式"), ("input_boolean.topfloor_stairs_keep_on", "樓梯燈常開（9A）"),
           ("input_boolean.wu_lou_bao_quan_xi_tong_kai_guan", "五樓保全系統開關"), ("input_boolean.debug_topfloor_kenny", "頂樓自動化 Debug 模式")]
    off_md = ("{% set off = states.automation | selectattr('state','eq','off') | map(attribute='name') | sort | list %}"
              "{% if off | length == 0 %}沒有停用中的自動化。{% else %}{% for n in off %}- {{ n }}\n{% endfor %}{% endif %}")
    recent_md = ("{% set ns = namespace(items=[]) %}"
                 "{% for a in states.automation if a.attributes.get('last_triggered') is not none and (now() - a.attributes.get('last_triggered')).total_seconds() < 86400 %}"
                 "{% set ns.items = ns.items + [(a.name, a.attributes.get('last_triggered'))] %}{% endfor %}"
                 "{% for n, t in (ns.items | sort(attribute='1', reverse=true))[:12] %}- {{ n }}（{{ relative_time(t) }}前）\n{% endfor %}")
    S = []                                   # 依閱讀順序：LINE Bot 額度與設定 → 說明 → 手動廣播／通知 → 災防與地震 → 常用總開關 → 網關與伺服器 → 頂樓 → 停用／最近觸發
    S.append(section(quota_section()))                # LINE Bot 額度與設定放最上面
    S.append(section(quota_settings()))
    S.append(section(["      - type: markdown", "        content: " + q(intro)] + MD_CSS))
    S.append(section(manual_broadcast_section()))
    S.append(section(manual_notify_section()))
    S.extend(disaster_blocks())
    S.append(section(heading("常用總開關", "mdi:toggle-switch-outline") + entities_card(quick)))
    S.append(section(heading("網關、伺服器與警報", "mdi:router-wireless") + entities_card(gateways)))
    S.append(section(heading("頂樓常用", "mdi:stairs-up") + entities_card(top)))
    S.append(section(heading("目前停用的自動化", "mdi:pause-circle-outline") + ["      - type: markdown", "        content: " + q(off_md)] + MD_CSS))
    S.append(section(heading("最近 24 小時觸發", "mdi:history") + ["      - type: markdown", "        content: " + q(recent_md)] + MD_CSS))
    return S


COLS = 4            # 最多 4 欄（橫向桌機／iPad 橫放）；layout-card 依螢幕寬度自動減少欄數：iPad 直放 2 欄、手機 1 欄
COL_WIDTH = 340     # 每欄最小寬度（px）


def est_height(lines):
    """粗估一張卡片的高度（px），只用來把卡片平均分到各欄。"""
    h = 24
    for ln in lines:
        t = ln.strip()
        if t.startswith("- entity:"):
            h += 48
        elif t == "- type: heading":
            h += 46
        elif t == "- type: custom:button-card":
            h += 92               # 額度卡片一列一張（窄欄）
        elif t.startswith("content:"):
            h += 40 + 22 * max(1, len(t) // 34)
    return h


def partition(heights, k):
    """把依序排列的卡片切成最多 k 段連續區塊，讓最高的一欄盡量矮（保留分類順序）。"""
    n = len(heights)
    k = max(1, min(k, n))
    pre = [0]
    for x in heights:
        pre.append(pre[-1] + x)
    INF = float("inf")
    best = [[INF] * (n + 1) for _ in range(k + 1)]
    cut = [[0] * (n + 1) for _ in range(k + 1)]
    best[0][0] = 0
    for j in range(1, k + 1):
        for i in range(1, n + 1):
            for m in range(j - 1, i):
                v = max(best[j - 1][m], pre[i] - pre[m])
                if v < best[j][i]:
                    best[j][i], cut[j][i] = v, m
    j = min(range(1, k + 1), key=lambda jj: (best[jj][n], -jj))
    bounds, i = [], n
    while j > 0:
        m = cut[j][i]
        bounds.append((m, i))
        i, j = m, j - 1
    return list(reversed(bounds))


def view(title, path, icon, blocks):
    """vertical-layout：依序排卡片，欄與欄之間放 layout-break；欄數不夠時依序往下接（手機就是單欄、順序不變）。"""
    L = [f"  - title: {q(title)}", f"    path: {path}", f"    icon: {icon}", "    type: custom:vertical-layout",
         "    layout:", f"      max_cols: {COLS}", f"      width: {COL_WIDTH}", "    cards:"]
    units = [[b] for b in blocks]
    if len(units) > 1:                     # 開頭的說明卡永遠跟下一張卡片放在同一欄，不會自己佔一欄
        units = [units[0] + units[1]] + units[2:]
    parts = partition([sum(est_height(b) for b in u) for u in units], COLS)
    for n, (a, b) in enumerate(parts):
        if n:
            L.append("    - type: custom:layout-break")
        for u in units[a:b]:
            for blk in u:
                L += blk
    return L


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
            if re.search(r"^input_select\.person_main_device_|^input_boolean\.person_main_device_busy$", eid):
                continue   # 家人主要裝置選單放在「系統維護」的家人裝置追蹤區，自己畫（busy 旗標不顯示）
            if INTERNAL_RE.search(eid):
                internal[cat].append((dom, fn or eid, eid))
            else:
                settings[cat].append((dom, fn or eid, eid))

    L = ["# 自動化管理面板（由 scripts/generate_automation_panel.py 產生，請勿直接手改；重新執行程式即可更新）",
         "title: 自動化管理", "views:"]
    global MASONRY
    MASONRY = True      # section() 輸出 vertical-stack 卡片，交給 vertical-layout 分欄
    for key, title, icon, desc in CATS:
        if key == "overview":
            L += view(title, key, icon, overview_sections(autos, stale))
            continue
        if key == "supply":
            L += supply_view(title, key, icon, autos)
            continue
        if key == "other" and not autos[key] and not settings[key]:
            continue   # 沒有未分類項目就不顯示「其他」分頁
        B = []
        if key == "internal":
            B.append(section(["      - type: markdown", "        content: " + q(f"**{title}**　{desc}")] + MD_CSS))
            homepod_rows = [
                ("sensor.5f_homepodmini_temperature", "5F HomePod mini 溫度"),
                ("sensor.5f_homepodmini_humidity", "5F HomePod mini 濕度"),
                ("sensor.livingroom_homepodmini_temperature", "客廳 HomePod mini 溫度"),
                ("sensor.livingroom_homepodmini_humidity", "客廳 HomePod mini 濕度"),
                ("input_boolean.collection_of_homepod_sensors", "HomePod 感測器收集開關"),
            ]
            B.append(section(heading("HomePod 偵測溫度", "mdi:homepod") + entities_card(homepod_rows)))
            for ck, ctitle, *_ in CATS:
                items = [x for x in internal.get(ck, []) if x[2] != "input_boolean.collection_of_homepod_sensors"]
                if items:
                    rows = [(eid, short_name(fn)) for dom, fn, eid in sorted(items, key=lambda x: (x[0], x[1]))]
                    B.extend(list_blocks(f"{ctitle}（{len(rows)}）", rows))
            L += view(title, key, icon, B)
            continue
        n_auto = len(autos[key]); n_set = len(settings[key])
        B.append(section(["      - type: markdown", "        content: " + q(f"**{title}**　{desc}　自動化 {n_auto} 支、可調整項目 {n_set} 個")] + MD_CSS))
        if key == "system":
            B.extend(family_tracking_blocks())      # 家人主要裝置選擇＋person 目前參考的裝置
        if key == "emergency":
            B.extend(disaster_blocks())      # 災防告警 sensor.disaster / 地震 sensor.earthquake 卡片
        if autos[key]:
            rows = [(eid, fn) for fn, eid in sorted(autos[key])]
            B.extend(list_blocks(f"自動化開關（{n_auto}）", rows, "mdi:robot"))
        # 功能小組（依 SUBGROUPS 的順序）
        left = list(settings[key])
        for label, pat in SUBGROUPS.get(key, []):
            grp = [x for x in left if re.search(pat, x[2] + " " + x[1])]
            if grp:
                left = [x for x in left if x not in grp]
                rows = [(eid, short_name(fn)) for dom, fn, eid in sorted(grp, key=lambda x: (x[0], x[1]))]
                B.extend(list_blocks(f"{label}（{len(rows)}）", rows))
        # 其餘依元件種類（同分類已有功能小組時，這些標為「其他…」）
        had_groups = len(left) != len(settings[key])
        for dom, label in TYPE_LABEL:
            grp = [x for x in left if x[0] == dom]
            if grp:
                label = label.replace("其他", "")
                label = ("其他" + label) if had_groups else label
                rows = [(eid, short_name(fn)) for d, fn, eid in sorted(grp, key=lambda x: x[1])]
                B.extend(list_blocks(f"{label}（{len(rows)}）", rows))
        L += view(title, key, icon, B)
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    data = fetch()
    text = build(data)
    import yaml
    yaml.safe_load(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT, len(text.splitlines()), "lines")

    # Always ensure root automation-panel.yaml is updated in sync
    root_panel = pathlib.Path(__file__).resolve().parent.parent / "automation-panel.yaml"
    ha_panel = pathlib.Path("/homeassistant/automation-panel.yaml")
    if ha_panel.parent.exists():
        ha_panel.write_text(text, encoding="utf-8")
        print("deployed to", ha_panel)
    elif root_panel.exists():
        root_panel.write_text(text, encoding="utf-8")
        print("deployed to", root_panel)

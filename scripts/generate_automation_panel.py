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
      # 2026-10-26 充電判斷改成機率模型，不再用最大電流換算
      "input_number.garage_charger_max_a",
      # 2026-10-26 104-2 改用 lpr_close_buffer_sec（秒）
      "input_number.lpr_auto_close_delay_min",
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
    ("scene", r"^(100晚安|101早安|102離家|103到家|100A|100B|100C ?GoogleHome|08-7[ABE]|105門鎖|106-1|HomeKit情境|AI離家版本|800-開關系列-(0B?|1B?)(?![0-9A-Za-z]))"),
    ("topfloor", r"^(08-5[A-M]|800-開關系列-(11|12)[A-D]?)"),
    ("emergency", r"^(05[A-G]|01地震|02地震|03E|03苗栗|04苗栗|00-2廣播系統測試|TREM 預警|地牛 add-on)"),
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
    ("security", r"intrusion_|wu_lou_bao_quan|garage_depart|garage_turn_|garage_board|garage_id_fix|garage_plate|garage_lamp|garage_slot|garage_facing|garage_learn|garage_ev_|garage_charg|garage_cable|garage_gate|garage_vehicle|lpr_|allowed_plates|doorlock|er_lou_men_suo|gateway_|garagejudge|五樓保全|wang_guan|jie_chu_wang_guan|54ef44cf58f9_alarm|解除網關"),
    ("topfloor", r"topfloor|sleep_silent|sleep_holiday|sleep_5h_|sleep_unlock_|ding_lou_(shang|xia|ye|yue|si_lou)|debug_topfloor|pan_duan_ding_lou|wu_lou_she_ying_ji_kai_guan"),
    ("emergency", r"jin_ji|emergency_|disaster|eq99|di_zhen|tian_qi|line_eew"),
    ("scene", r"leave_notice|anti_down_|noise_warning|auto_scene_|scene_morning_|scene_verify|scene_window_|scene_sunrise|scene_sunset|weather_sun_|aqara_|google_scene|hk_scene|scene_origin|input_button\.(night|li_jia|morning|dao_jia)|collection_of_homekit"),
    ("notify", r"notify_|announce_|eew_|disaster_item_memory|line_bot|mood_|ambient_|scene_announce|notif_title|garage_arrival|garage_away"),
    ("air_fan", r"air_ai|air_pm|air_door|air_manual|env_alert|env_co|env_temp|fan|feng_shan|summer_|^input_number\.(ac_|enter_|night_cold|morning_reopen)|effective_apparent|living_room"),
    ("system", r"tv_ir_power|tv_keepalive|maintenance_until|v41_phone|tw_makeup|system_stability|ai_00_01|tesla|at_home|tracker|ai_version|ai_manual|automation_(package|framework)|homekit_framework|ai_leave_version|floorplan|collection|last_disaster"),
]
# 「內部狀態」：由自動化自動維護，不是給人調整的（旗標、時間戳、紀錄、計時器、計數器、記憶值…）
INTERNAL_RE = re.compile(
    r"^timer\.|^counter\."
    r"|^input_datetime\.(?!system_stability_restart_time|supply_battery_report_time|maintenance_until|scene_morning_|sleep_5h_|sleep_unlock_|anti_down_start|anti_down_cutoff)"
    r"|^input_boolean\.(garage_vehicle_confirmed|garage_depart_candidate|garage_turn_detected|garage_lamp_(front|back)|leave_notice_sent|emergency_snapshot_valid|stairs_si_lou_hold|topfloor_(0fb7|13b8|kandeng|study)_auto|topfloor_stairs_keep_on|topfloor_stairs_night_used|mood_alert_active|light_anim_active|line_bot_quota_exhausted_notified|tesla_charger_session_charged"
    r"|aqara_|hk_scene_|google_scene_|jin_ji_mo_shi_pan_duan_|ding_lou_(shang|xia)_lou_qing_jing|ding_lou_ye_deng_qing_jing|ding_lou_yue_du_qing_jing"
    r"|ding_lou_fan_(system_action_guard|manual_hold|manual_off_hold|cold_off_memory|manual_speed_snooze)|living_room_fan_manual_speed_snooze"
    r"|collection_of_homekit_sensors|collection_of_homepod_sensors|garagejudge|pan_duan_|er_lou_men_suo_tong_bu_kai_guan|ke_ting_dian_feng_shan_control)"
    r"|^input_text\.(garage_depart_car|garage_id_fix_log|garage_plate_seen|intrusion_recent|emergency_(trigger_source|garage_prev)|air_ai_state|env_alert_cd|.*_init$|.*_flag$|.*_last($|_)|.*decision|.*last_path|ambient_scene_state|announce_manual_result|notify_manual_result|mood_mem_|.*notice_key|.*monthly_history|doorlock_batt_last_stage"
    r"|doorlock_batt_model_last_cycle|ai_leave_version_text|scene_origin_device|line_eew_remote_|disaster_seen_items|notif_title_|.*last_message|.*debug_last|ai_00_01_)"
    r"|^input_number\.(garage_ev_|v41_phone_match_|supply_batt_lowest_|doorlock_batt_drop_last_cycle|.*effective_apparent_temperature)"
    r"|^input_select\.(lpr_last_plate|garage_vehicle_latch|garage_vehicle_last)"
    r"|^input_datetime\.(garage_cable_learn_last|garage_id_fix_last|garage_turn_last|garage_gate_opened_at|scene_verify_skip_alarm_until)$"
)

# 各分類內的功能小組（依序比對，先符合者先分；沒符合的依元件種類分組）
SUBGROUPS = {
    "supply": [
        ("LINE Bot 模式與設定", r"line_bot_mode|line_bot_sticky|line_bot_test_mode|line_bot_custom"),
        ("耗材通知與報告設定", r"supply_battery_report_time|notify_supply_extra_line|supply_filter_notified"),
        ("耗材測試按鈕", r"battery_system_test"),
    ],
    "notify": [
        ("地震預警與空氣通知", r"地震預警|空氣通知|eew_|air_notify"),
        ("LINE 通知開關", r"notify_line_|notify_tesla_charge_extra_line"),
        ("HA 通知開關", r"notify_ha_|garage_arrival_ha_notify|garage_away_off_ha_notify|notify_tesla_charge_extra_system"),
        ("災害訊息廣播開關", r"announce_disaster_"),
        ("手動廣播與手動通知", r"announce_manual|notify_manual"),
        ("廣播音量與情境廣播", r"announce_volume|scene_announce|announce_end_chime|announce_demo"),
        ("氣氛燈與機台氣氛燈", r"mood_alert|ambient_"),
        ("通知測試按鈕", r"notify_test|tesla_charger_notify_test"),
    ],
    "topfloor": [
        ("感應燈與書房燈參數", r"topfloor_(evidence|line_debounce|arrive|down_4f|vacancy|study|stairs_night|stairs_day)|topfloor_motion_pause"),
        ("上下樓情境判斷參數", r"_kenny|topfloor_webhook_mode|topfloor_ap_macs"),
        ("睡眠靜默與熟睡鎖", r"sleep_silent|sleep_holiday|sleep_5h_|sleep_unlock_"),
        ("頂樓情境廣播", r"topfloor_scene_announce|頂樓情境廣播"),
        ("攝影機與模型判斷", r"頂樓模型|頂樓攝影機|五樓攝影機|頂樓四樓樓梯燈校正|頂樓樓梯燈｜自動關燈前"),
    ],
    "air_fan": [
        ("空氣清淨機（PM2.5）", r"air_"),
        ("環境異常（CO／溫度）", r"env_"),
        ("溫度門檻與冷氣", r"ac_|enter_|night_cold|morning_reopen|summer_"),
        ("客廳風扇", r"living_room_fan|ke_ting_dian_feng"),
        ("頂樓風扇", r"ding_lou_fan|top_floor_fan"),
    ],
    "emergency": [
        ("維修暫停（連點三下）", r"emergency_triple_press"),
        ("災害訊息通知與廣播", r"災害訊息|氣氛燈提醒_緊急|LINE通知啟用_緊急|地震系統廣播|天氣警訊廣播|地震預警"),
        ("緊急模式", r"緊急模式"),
    ],
    "security": [
        ("車庫車輛出門偵測", r"garage_depart_(watch|notify|auto_open|likelihood)|garage_turn_(signal|wait_board)"),
        ("離家入侵偵測", r"intrusion_"),
        ("車輛動態辨識（LPR）", r"lpr_|allowed_plates"),
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


DEFAULTS_QUERY = r"""
import json, sqlite3, sys, time
eids = json.loads(sys.stdin.readline())
now = time.time(); since = now - 14 * 86400
c = sqlite3.connect("file:/homeassistant/home-assistant_v2.db?mode=ro", uri=True, timeout=20)
meta = dict(c.execute("select entity_id, metadata_id from states_meta").fetchall())
out = {}
for e in eids:
    mid = meta.get(e)
    if mid is None:
        continue
    prev = c.execute("select state from states where metadata_id=? and last_updated_ts<=? order by last_updated_ts desc limit 1", (mid, since)).fetchone()
    rows = c.execute("select state, last_updated_ts from states where metadata_id=? and last_updated_ts>? order by last_updated_ts", (mid, since)).fetchall()
    cur, t0, on, tot, flips = (prev[0] if prev else None), since, 0.0, 0.0, 0
    if cur is None and rows:
        cur, t0 = rows[0][0], rows[0][1]
    for st, ts in rows:
        if cur in ("on", "off"):
            tot += ts - t0
            on += (ts - t0) if cur == "on" else 0
            if st in ("on", "off") and st != cur:
                flips += 1
        cur, t0 = st, ts
    if cur in ("on", "off"):
        tot += now - t0
        on += (now - t0) if cur == "on" else 0
    if tot > 3600:
        r = on / tot
        out[e] = "auto" if flips >= 8 and 0.05 < r < 0.95 else ("on" if r >= 0.5 else "off")
print(json.dumps(out))
"""
DEFAULTS = {}          # entity_id -> "on" / "off"（平常狀態）／"auto"（會自動切換：不分常開常關、不標示）
DEFAULTS_ON = [True]   # 內部狀態分頁不標「不是平常狀態」


def fetch_defaults(eids):
    """平常狀態：過去 14 天大部分時間的狀態；常常來回切換的是 "auto"；scripts/panel_defaults.json 可覆寫（{"entity_id": "on"／"off"／"auto"}）。"""
    out = {}
    try:
        r = subprocess.run(["python3", "-"], input=DEFAULTS_QUERY.lstrip("\n").replace("sys.stdin.readline()", repr(json.dumps(eids))),
                           capture_output=True, text=True, timeout=120)
        out = json.loads(r.stdout or "{}")
    except Exception as e:  # noqa: BLE001
        print("defaults query failed:", e)
    f = pathlib.Path(__file__).resolve().parent / "panel_defaults.json"
    if f.exists():
        try:
            out.update({k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items() if v in ("on", "off", "auto")})
        except Exception as e:  # noqa: BLE001
            print("panel_defaults.json error:", e)
    return out


def clean_name(n):
    """開關列名稱：去掉結尾的版本號「 (V4.3.0)」，比較好掃讀（版本號在詳細資訊裡看得到）。"""
    return re.sub(r"\s*[（(]\s*V\d[^）)]*[）)]\s*$", "", str(n or "")).strip() or str(n or "")


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


TOGGLE_DOMAINS = ("automation", "input_boolean", "switch", "light", "fan")
STATE = {}


def toggle_rows_card(rows):
    """一組開關列（和 Kiosk「自動化管理」同一套樣式）：圖示＋名稱＋右側 iOS 開關；點名稱開詳細資訊。"""
    items = []
    for r in rows:
        eid, name = r[0], clean_name(r[1])
        d = (r[2] if len(r) > 2 else DEFAULTS.get(eid)) if DEFAULTS_ON[0] else None
        d = d if d in ("on", "off") else None
        items.append([eid, name, d] if d else [eid, name])
    return ["      - type: custom:button-card", "        template: prows",
            "        variables:", "          items: " + json.dumps(items, ensure_ascii=False),
            "        triggers_update: " + json.dumps([x[0] for x in items])]


def entities_card(rows, title=None):
    """連續的開關列改用 toggle_rows_card；其餘（數值、選項、文字…）維持原生 entities 卡片。"""
    if not title and rows and any(isinstance(r, tuple) and r[0].split(".")[0] in TOGGLE_DOMAINS for r in rows):
        out, buf, kind = [], [], None
        for r in rows:
            k = isinstance(r, tuple) and r[0].split(".")[0] in TOGGLE_DOMAINS
            if buf and k != kind:
                out += toggle_rows_card(buf) if kind else _entities_card_native(buf)
                buf = []
            buf.append(r)
            kind = k
        if buf:
            out += toggle_rows_card(buf) if kind else _entities_card_native(buf)
        return out
    return _entities_card_native(rows, title)


def _entities_card_native(rows, title=None):
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
        L = ["    - type: vertical-stack",
             "      card_mod:", "        style: |",
             "          ha-card { background: rgba(120,120,128,.10) !important; border-radius: 22px !important; box-shadow: none !important; border: none !important; padding: 0 10px 12px !important; }",
             "      cards:"]
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


QUOTA_JS = r"""[[[
  const ids = ['sensor.bot_msg_remaining0', 'sensor.bot_msg_remaining1', 'sensor.bot_msg_remaining2', 'sensor.bot_msg_remaining3'];
  const inUse = states['sensor.line_bot_in_use'];
  const ia = (inUse && inUse.attributes) || {};
  const target = Number(ia.target_index);
  const sw = Number(ia.rotation_switch_limit || 196);
  const curName = inUse ? String(inUse.state).replace('ChiangFamily ', '') : '--';
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const head = (icon, color, title, chip) => `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <div style="flex:none;width:42px;height:42px;border-radius:13px;background:${color}1a;color:${color};display:flex;align-items:center;justify-content:center"><ha-icon icon="${icon}" style="--mdc-icon-size:24px"></ha-icon></div>
      <div style="flex:1;min-width:0;font-size:16px;font-weight:700;color:var(--primary-text-color);${wrap}">${title}</div>
      <span style="flex:none;font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;background:${color}1f;color:${color};white-space:nowrap">${chip}</span></div>`;
  const shell = (color, inner) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:16px 16px 16px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">${inner}</div>`;

  const rot = states['sensor.line_bot_rotation_target'];
  const nextIdx = rot && rot.attributes ? rot.attributes.next_bot : null;
  const botNames = { 0: '智慧家庭 A（緊急 Bot）', 1: '智慧家庭 B', 2: '智慧家庭 C', 3: '智慧家庭 D' };
  const nextName = nextIdx != null ? (botNames[nextIdx] || ('Bot ' + nextIdx)) : '--';
  const f = states['sensor.line_bot_forecast'];
  const st = f ? f.state : 'safe';
  const a = (f && f.attributes) || {};
  const md = (d) => d ? String(d).slice(5).replace('-', '/') : '--';
  let color, label, d1, d2;
  if (st === 'safe') { color = '#28A745'; label = '額度充裕'; d1 = `本月一般 Bot 額度充裕，可用至 ${md(a.normal_exhaust_date)}`; d2 = '運作平穩，本月不需動用緊急 Bot。'; }
  else if (st === 'need_emergency') { color = '#D97706'; label = '預備動用緊急 Bot'; d1 = `一般 Bot 預估 ${md(a.normal_exhaust_date)}（約 ${a.normal_days_left || 0} 天後）用盡，將切換緊急 Bot`; d2 = '動用智慧家庭 A 後，預估可順利撐至月底重置。'; }
  else { color = '#E5372C'; label = '額度告急'; d1 = `日均消耗偏高（${a.daily_rate || 0} 則/天），預估 ${md(a.normal_exhaust_date)} 動用緊急 Bot`; d2 = `預估 ${md(a.total_exhaust_date)} 前耗盡，請留意發送量。`; }
  const rows = ids.map((id, i) => {
    const e = states[id]; if (!e) return '';
    const u = Number(e.attributes.usage || 0), lim = Number(e.attributes.limit || 200);
    const r = Math.max(lim - u, 0), p = Math.min(100, Math.round(u / lim * 100));
    const c = u >= sw ? '#E5372C' : (p >= 70 ? '#D97706' : '#28A745');
    const cur = target === i;
    const chip = cur ? '使用中' : (u >= sw ? '已達門檻' : '待命');
    const chipBg = cur ? 'rgba(40,167,69,.14)' : (u >= sw ? 'rgba(229,55,44,.12)' : 'rgba(120,120,128,.14)');
    const chipFg = cur ? '#28A745' : (u >= sw ? '#E5372C' : 'var(--secondary-text-color)');
    return `<div style="display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:12px;background:rgba(120,120,128,.08)">
      <div style="flex:none;width:38px;height:38px;border-radius:11px;background:${c}1a;color:${c};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:16px">${'ABCD'[i]}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px"><span style="font-weight:600;font-size:14.5px;color:var(--primary-text-color)">智慧家庭 ${'ABCD'[i]}</span><span style="flex:none;font-size:11.5px;font-weight:700;padding:2px 9px;border-radius:999px;background:${chipBg};color:${chipFg}">${chip}</span></div>
        <div style="height:6px;border-radius:4px;background:rgba(120,120,128,.20);margin:8px 0 5px;overflow:hidden"><div style="width:${p}%;height:100%;background:${c};border-radius:4px"></div></div>
        <div style="display:flex;justify-content:space-between;align-items:baseline;font-size:12px;color:var(--secondary-text-color)"><span>剩餘 <b style="font-size:16px;color:${c}">${r}</b> 則</span><span>已用 ${u} / ${lim}（${p}%）</span></div>
      </div></div>`;
  }).join('');
  return shell(color, head('mdi:message-text-outline', color, 'LINE Bot 額度', '使用中：' + curName) +
    `<div style="display:flex;flex-direction:column;gap:8px">${rows}</div>` +
    `<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--secondary-text-color)"><span>下一輪替</span><span style="font-weight:700;color:var(--primary-text-color);padding:3px 10px;border-radius:8px;background:rgba(120,120,128,.12)">${nextName}</span></div>` +
    `<div style="margin-top:10px;padding:11px 14px;border-radius:12px;background:rgba(120,120,128,.08);${wrap}"><div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:4px"><span style="font-size:12.5px;font-weight:700;color:var(--primary-text-color)">預估 Bot 使用狀況</span><span style="flex:none;font-size:11.5px;font-weight:700;padding:2px 9px;border-radius:999px;background:${color}1f;color:${color}">${label}</span></div><div style="font-size:13.5px;font-weight:600;line-height:1.55;color:var(--primary-text-color)">${esc(d1)}</div><div style="font-size:12.5px;line-height:1.5;color:var(--secondary-text-color);margin-top:3px">${esc(d2)}</div></div>` +
    `<div style="margin-top:10px;font-size:11.5px;color:var(--secondary-text-color);line-height:1.5">已達 ${sw} 則自動切換下個 Bot · 群組每則約耗 5 額度 · 每月 1 日重置</div>`);
]]]"""


def quota_section():
    """LINE Bot 額度：4 個 Bot、輪替狀態與預估合成一張卡片（和「氣象與災害告警」同一種樣式）。"""
    L = []
    L += heading("LINE Bot 額度", "mdi:message-text-outline")
    L += ["      - type: custom:button-card",
          "        entity: sensor.bot_msg_remaining0",
          "        triggers_update:", "          - sensor.bot_msg_remaining0", "          - sensor.bot_msg_remaining1",
          "          - sensor.bot_msg_remaining2", "          - sensor.bot_msg_remaining3",
          "          - sensor.line_bot_in_use", "          - sensor.line_bot_forecast", "          - sensor.line_bot_rotation_target",
          "        show_name: false", "        show_icon: false", "        show_state: false",
          "        styles:", "          card:", "            - border-radius: 18px", "            - border: none",
          "            - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "            - padding: 0", "            - white-space: normal",
          "          grid:", "            - grid-template-areas: '\"body\"'", "            - grid-template-columns: 1fr",
          "          custom_fields:", "            body:", "              - width: 100%", "              - min-width: 0",
          "              - text-align: left", "              - white-space: normal",
          "        custom_fields:", "          body: |"]
    for ln in QUOTA_JS.splitlines():
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
  if (!f || !f.attributes) return '<div style="padding:16px;text-align:center;color:var(--secondary-text-color)">LINE Bot 預測載入中...</div>';
  const a = f.attributes;
  const st = f.state;
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const head = (icon, color, title, chip) => `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <div style="flex:none;width:42px;height:42px;border-radius:13px;background:${color}1a;color:${color};display:flex;align-items:center;justify-content:center"><ha-icon icon="${icon}" style="--mdc-icon-size:24px"></ha-icon></div>
      <div style="flex:1;min-width:0;font-size:16px;font-weight:700;color:var(--primary-text-color);${wrap}">${title}</div>
      <span style="flex:none;font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;background:${color}1f;color:${color};white-space:nowrap">${chip}</span></div>`;
  const tile = (k, v, c) => `<div style="min-width:0;padding:10px 12px;border-radius:12px;background:rgba(120,120,128,.08)"><div style="font-size:11.5px;color:var(--secondary-text-color);margin-bottom:3px">${k}</div><div style="font-size:17px;font-weight:700;line-height:1.25;color:${c || 'var(--primary-text-color)'};${wrap}">${v}</div></div>`;
  const shell = (color, inner) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:16px 16px 16px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">${inner}</div>`;

  const md = (d) => d ? String(d).slice(5).replace('-', '/') : '--';
  let color, title, chip, icon;
  if (st === 'safe') { color = '#28A745'; title = '本月額度充裕，不需動用緊急 Bot'; chip = '安全充裕'; icon = 'mdi:check-circle'; }
  else if (st === 'need_emergency') { color = '#D97706'; title = `預估 ${a.normal_exhaust_day || '中旬'} 號動用緊急 Bot，可撐至月底`; chip = '備援預備'; icon = 'mdi:alert-circle'; }
  else { color = '#E5372C'; title = `額度告急，預估 ${md(a.total_exhaust_date)} 耗盡`; chip = '額度告急'; icon = 'mdi:alert-octagon'; }
  const parts = String(a.summary || '').split(/[；;]/);
  const part1 = parts[0] ? parts[0].trim() : '';
  const part2 = parts.length > 1 ? parts.slice(1).join('；').trim() : '';
  const unit = (t) => `<span style="font-size:12px;font-weight:500;color:var(--secondary-text-color)"> ${t}</span>`;
  return shell(color, head(icon, color, '本月 LINE Bot 預測', chip) +
    `<div style="font-size:15px;font-weight:700;line-height:1.5;margin:-4px 0 12px;color:var(--primary-text-color);${wrap}">${esc(title)}</div>` +
    `<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px">` +
      tile('日均消耗', `${esc(a.daily_rate || 0)}${unit('則/天')}`) +
      tile('一般 Bot 預估至', `${md(a.normal_exhaust_date)}${unit(`（${esc(a.normal_days_left || 0)} 天）`)}`, a.need_emergency ? color : '') +
      tile('緊急 Bot 剩餘', `${esc(a.emergency_remaining || 0)}${unit('則')}`) +
      tile('距離月初重置', `${esc(a.days_left_in_month || 0)}${unit('天')}`) +
    `</div>` +
    (part1 ? `<div style="margin-top:12px;padding:11px 14px;border-radius:12px;background:rgba(120,120,128,.08);${wrap}"><div style="font-size:13.5px;font-weight:600;line-height:1.55;color:var(--primary-text-color)">${esc(part1)}</div>${part2 ? `<div style="font-size:12.5px;line-height:1.5;color:var(--secondary-text-color);margin-top:3px">${esc(part2)}</div>` : ''}</div>` : ''));
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
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const head = (icon, color, title, chip) => `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <div style="flex:none;width:42px;height:42px;border-radius:13px;background:${color}1a;color:${color};display:flex;align-items:center;justify-content:center"><ha-icon icon="${icon}" style="--mdc-icon-size:24px"></ha-icon></div>
      <div style="flex:1;min-width:0;font-size:16px;font-weight:700;color:var(--primary-text-color);${wrap}">${title}</div>
      <span style="flex:none;font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;background:${color}1f;color:${color};white-space:nowrap">${chip}</span></div>`;
  const tile = (k, v, c) => `<div style="min-width:0;padding:10px 12px;border-radius:12px;background:rgba(120,120,128,.08)"><div style="font-size:11.5px;color:var(--secondary-text-color);margin-bottom:3px">${k}</div><div style="font-size:17px;font-weight:700;line-height:1.25;color:${c || 'var(--primary-text-color)'};${wrap}">${v}</div></div>`;
  const shell = (color, inner) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:16px 16px 16px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">${inner}</div>`;

  let color, chip, desc;
  if (lvl <= 5) { color = '#E5372C'; chip = '請更換'; desc = '已達臨界壽命，請立即更換濾網'; }
  else if (lvl <= 10) { color = '#D97706'; chip = '備品'; desc = '濾網壽命偏低，請準備備用濾芯'; }
  else { color = '#28A745'; chip = '良好'; desc = '濾網狀態良好，壽命充足'; }
  const pct = Math.max(0, Math.min(100, lvl));
  return shell(color, head('mdi:air-filter', color, '空氣清淨機濾網', chip) +
    `<div style="display:flex;align-items:center;gap:18px">
      <div style="flex:none;width:92px;height:92px;border-radius:50%;background:conic-gradient(${color} ${pct * 3.6}deg, rgba(120,120,128,.18) 0);display:flex;align-items:center;justify-content:center">
        <div style="width:72px;height:72px;border-radius:50%;background:var(--card-background-color);display:flex;align-items:center;justify-content:center"><span style="font-size:24px;font-weight:800;color:${color}">${lvl}<small style="font-size:13px">%</small></span></div>
      </div>
      <div style="flex:1;min-width:0">
        <div style="font-size:14.5px;font-weight:700;line-height:1.5;color:var(--primary-text-color);${wrap}">${desc}</div>
        <div style="font-size:12.5px;line-height:1.6;color:var(--secondary-text-color);margin-top:4px">壽命 ≤10% 提醒備品　≤5% 請更換</div>
        <div style="display:inline-block;margin-top:8px;font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;background:${notified ? color + '1f' : 'rgba(120,120,128,.12)'};color:${notified ? color : 'var(--secondary-text-color)'}">${notified ? '已發出更換通知' : '尚未發送通知'}</div>
      </div></div>`);
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
    'cube': '客廳魔方', 'toiletm': '二樓廁所感應', 'kitchenm': '廚房人體感應', 'garstair': '車庫樓梯人體感應',
    'bell': '二樓門口電鈴', 'kswitch': '廚房無線開關'
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
    """耗材與額度分頁：和其他分頁一樣用 view()（custom:vertical-layout）排版，欄寬、置中、分區底色區塊完全一致。"""
    auto_rows = [(eid, fn) for fn, eid in sorted(autos.get("supply", []))]
    desc = next((d for k, t, ic, d in CATS if k == "supply"), "")
    B = [section(["      - type: markdown", "        content: " + q(f"**{title}**　{desc}")] + MD_CSS),
         section(heading("LINE Bot 全月預測診斷", "mdi:chart-timeline-variant") + linebot_forecast_banner()),
         section(quota_section()),
         section(quota_settings()),
         section(battery_forecast_section()),
         section(filter_life_section()),
         section(supply_control_section())]
    if auto_rows:
        B.append(section(heading("耗材相關自動化", "mdi:robot") + entities_card(auto_rows)))
    return view(title, path, icon, B)


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
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const head = (icon, color, title, chip) => `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <div style="flex:none;width:42px;height:42px;border-radius:13px;background:${color}1a;color:${color};display:flex;align-items:center;justify-content:center"><ha-icon icon="${icon}" style="--mdc-icon-size:24px"></ha-icon></div>
      <div style="flex:1;min-width:0;font-size:16px;font-weight:700;color:var(--primary-text-color);${wrap}">${title}</div>
      <span style="flex:none;font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;background:${color}1f;color:${color};white-space:nowrap">${chip}</span></div>`;
  const tile = (k, v, c) => `<div style="min-width:0;padding:10px 12px;border-radius:12px;background:rgba(120,120,128,.08)"><div style="font-size:11.5px;color:var(--secondary-text-color);margin-bottom:3px">${k}</div><div style="font-size:17px;font-weight:700;line-height:1.25;color:${c || 'var(--primary-text-color)'};${wrap}">${v}</div></div>`;
  const shell = (color, inner) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:16px 16px 16px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">${inner}</div>`;

  const lamps = { '紅色': '#E5372C', '橙色': '#D97706', '黃色': '#B88600' };
  const calm = !s || /^(無|目前無|沒有|正常)/.test(s);
  const re = /([^，。()（）]*?局部地區)有([^()（）]*?)[(（](紅色|橙色|黃色)燈號[)）]/g;
  const items = [];
  let m;
  while ((m = re.exec(s)) !== null) items.push({ region: m[1].replace(/^[、，,\s]+/, '').trim(), cond: m[2].trim(), lamp: m[3] });
  let top = null;
  for (const k of ['紅色', '橙色', '黃色']) { if (s.includes(k)) { top = k; break; } }
  let color, label, icon;
  if (calm) { color = '#28A745'; label = '目前無警報'; icon = 'mdi:shield-check'; }
  else if (top) { color = lamps[top]; label = top + '燈號'; icon = 'mdi:alert-octagon'; }
  else { color = '#D97706'; label = '災防通知'; icon = 'mdi:alert-circle'; }
  const lead = items.length ? s.split('，')[0] : '';
  let body = '';
  if (calm) {
    body = `<div style="font-size:14px;line-height:1.6;color:var(--secondary-text-color);${wrap}">${s ? esc(s) : '目前沒有任何災害防護告警訊息。'}</div>`;
  } else if (items.length) {
    body = (lead ? `<div style="font-size:15px;font-weight:700;margin-bottom:10px;color:var(--primary-text-color);${wrap}">${esc(lead)}</div>` : '') +
      `<div style="display:flex;flex-direction:column;gap:8px">` + items.map(it => {
        const c = lamps[it.lamp];
        return `<div style="display:flex;gap:10px;align-items:flex-start;padding:11px 12px;border-radius:12px;background:rgba(120,120,128,.08)">
          <span style="flex:none;margin-top:5px;width:10px;height:10px;border-radius:50%;background:${c}"></span>
          <div style="flex:1;min-width:0;${wrap}">
            <div style="font-size:12px;font-weight:700;color:${c}">${it.lamp}燈號</div>
            <div style="font-size:14px;font-weight:600;line-height:1.5;color:var(--primary-text-color);margin-top:1px;${wrap}">${esc(it.region)}</div>
            <div style="font-size:12.5px;line-height:1.5;color:var(--secondary-text-color);margin-top:2px;${wrap}">${esc(it.cond)}</div>
          </div></div>`;
      }).join('') + `</div>` +
      `<details style="margin-top:10px"><summary style="font-size:12.5px;color:var(--secondary-text-color);cursor:pointer">查看完整內容</summary><div style="font-size:13px;line-height:1.6;margin-top:6px;color:var(--secondary-text-color);${wrap}">${esc(s)}</div></details>`;
  } else {
    body = `<div style="font-size:14px;line-height:1.6;color:var(--primary-text-color);${wrap}">${esc(s)}</div>`;
  }
  const upd = entity && entity.last_changed ? new Date(entity.last_changed) : null;
  const updTxt = upd ? `${upd.getMonth() + 1}/${upd.getDate()} ${String(upd.getHours()).padStart(2, '0')}:${String(upd.getMinutes()).padStart(2, '0')}` : '';
  return shell(color, head(icon, color, '氣象與災害告警', label) + body + (updTxt ? `<div style="font-size:11.5px;color:var(--secondary-text-color);margin-top:12px">更新於 ${updTxt}</div>` : ''));
]]]"""

EARTHQUAKE_JS = r"""[[[
  const raw = (entity && entity.state) || '';
  const bad = ['', 'unknown', 'unavailable', 'None', 'none'];
  const s = bad.includes(raw) ? '' : String(raw).trim();
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const head = (icon, color, title, chip) => `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
      <div style="flex:none;width:42px;height:42px;border-radius:13px;background:${color}1a;color:${color};display:flex;align-items:center;justify-content:center"><ha-icon icon="${icon}" style="--mdc-icon-size:24px"></ha-icon></div>
      <div style="flex:1;min-width:0;font-size:16px;font-weight:700;color:var(--primary-text-color);${wrap}">${title}</div>
      <span style="flex:none;font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;background:${color}1f;color:${color};white-space:nowrap">${chip}</span></div>`;
  const tile = (k, v, c) => `<div style="min-width:0;padding:10px 12px;border-radius:12px;background:rgba(120,120,128,.08)"><div style="font-size:11.5px;color:var(--secondary-text-color);margin-bottom:3px">${k}</div><div style="font-size:17px;font-weight:700;line-height:1.25;color:${c || 'var(--primary-text-color)'};${wrap}">${v}</div></div>`;
  const shell = (color, inner) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:16px 16px 16px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">${inner}</div>`;

  const mm = s.match(/^(\d{1,2}\/\d{1,2})\s*(\d{1,2}:\d{2})\s*(.*?)發生規模\s*([\d.]+)\s*(有感)?地震[，,]?\s*(.*?)。?$/);
  const mag = mm ? parseFloat(mm[4]) : NaN;
  let color = '#28A745';
  if (!isNaN(mag)) color = mag >= 6 ? '#E5372C' : (mag >= 5 ? '#D97706' : (mag >= 4 ? '#B88600' : '#28A745'));
  const label = isNaN(mag) ? '地震速報' : (mag >= 6 ? '強震' : (mag >= 5 ? '中強震' : (mag >= 4 ? '有感地震' : '小區域地震')));
  let body = '';
  if (mm) {
    const intens = mm[6] ? mm[6].replace(/^最大震度/, '') : '';
    const im = intens.match(/^(.*?)(\d+[弱強]?級?)$/);
    const place = im ? im[1].trim() : intens;
    const lvl = im ? im[2] : '';
    const row = (icon, k, v) => `<div style="display:flex;align-items:center;gap:10px;min-width:0"><ha-icon icon="${icon}" style="flex:none;color:var(--secondary-text-color);--mdc-icon-size:18px"></ha-icon><span style="flex:none;font-size:12.5px;color:var(--secondary-text-color);width:58px">${k}</span><span style="flex:1;min-width:0;font-size:14px;font-weight:600;color:var(--primary-text-color);${wrap}">${v}</span></div>`;
    body = `<div style="display:flex;align-items:stretch;gap:14px">
      <div style="flex:none;min-width:104px;padding:12px 14px;border-radius:14px;background:${color}14;display:flex;flex-direction:column;justify-content:center;align-items:center">
        <div style="font-size:11.5px;color:var(--secondary-text-color)">規模</div>
        <div style="font-size:30px;font-weight:800;line-height:1.1;color:${color}">${esc(mm[4])}</div>
        ${lvl ? `<div style="font-size:12px;font-weight:700;color:${color};margin-top:3px">震度 ${esc(lvl)}</div>` : ''}
      </div>
      <div style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:9px">
        ${row('mdi:map-marker-outline', '震央', esc(mm[3].trim() || '--'))}
        ${row('mdi:home-alert-outline', '最大震度', esc((place ? place + ' ' : '') + lvl) || '--')}
        ${row('mdi:clock-outline', '時間', esc(mm[1] + ' ' + mm[2]))}
      </div></div>`;
  } else if (s) {
    body = `<div style="font-size:14px;line-height:1.6;color:var(--primary-text-color);${wrap}">${esc(s)}</div>`;
  } else {
    body = `<div style="font-size:14px;color:var(--secondary-text-color)">目前沒有地震速報資料。</div>`;
  }
  return shell(color, head('mdi:pulse', color, '最新地震報告', label) + body);
]]]"""


def disaster_blocks():
    return [section(heading("氣象與災害告警", "mdi:weather-hurricane") + _text_card("sensor.disaster", DISASTER_JS)),
            section(heading("最新地震報告", "mdi:pulse") + _text_card("sensor.earthquake", EARTHQUAKE_JS))]


FAMILY_OTHER = "其他（自訂，在下方欄位輸入 device_tracker）"   # 必須和 scripts/gen_person_main_device.py 的 OTHER 一樣

FAMILY_JS = r"""[[[
  const k = '__K__', n = '__N__';
  const st = (id) => (states[id] ? states[id].state : undefined);
  const label = (s) => s === 'home' ? '在家' : (s === 'not_home' ? '離家' : (s || '--'));
  const col = (s) => s === 'home' ? '#30D158' : (s === 'not_home' ? '#8E8E93' : '#FF9F0A');
  const chip = (s) => `<span style="flex:none;font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;background:${col(s)}26;color:${col(s)}">${label(s)}</span>`;
  const ps = st('person.' + k);
  const sn = states['sensor.person_' + k + '_source_device'];
  const dev = sn ? sn.state : '--', ent = sn ? (sn.attributes.source_entity || '') : '', dst = sn ? sn.attributes.source_state : undefined;
  let watch = '';
  if (__W__) {
    const we = st('input_text.watch_tracker_entity_kenny') || '';
    const wo = states[we];
    const wn = wo ? String(wo.attributes.friendly_name || we).replace(/^(.{3,}?)\s+\1$/, '$1') : (we || '未設定');
    watch = `<div style="margin-top:10px;padding-top:9px;border-top:1px solid rgba(120,120,128,.24)">
      <div style="font-size:12px;color:var(--secondary-text-color)">⌚ 手錶追蹤裝置</div>
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:3px">
        <span style="font-weight:600;font-size:14px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${wn}</span>${wo ? chip(wo.state) : ''}</div>
      <div style="font-size:11px;opacity:.65;word-break:break-all;margin-top:1px">${we}</div></div>`;
  }
  return `
   <div style="display:flex;align-items:center;gap:12px;text-align:left">
     <div style="flex:none;width:46px;height:46px;border-radius:13px;background:${col(ps)}26;color:${col(ps)};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:19px">${n.slice(0, 1)}</div>
     <div style="flex:1;min-width:0">
       <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
         <span style="font-weight:700;font-size:17px">${n}</span>${chip(ps)}
       </div>
       <div style="font-size:12px;color:var(--secondary-text-color);margin-top:8px">person.${k} 目前參考的裝置</div>
       <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:3px">
         <span style="font-weight:600;font-size:14px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${dev}</span>${chip(dst)}
       </div>
       <div style="font-size:11px;opacity:.65;word-break:break-all;margin-top:1px">${ent}</div>
       ${watch}
     </div>
   </div>`;
]]]"""


def _shift(lines, delta):
    """把一段 YAML 行整體右移（delta>0）或左移（delta<0）。"""
    out = []
    for ln in lines:
        out.append((" " * delta + ln) if delta >= 0 else ln[min(-delta, len(ln) - len(ln.lstrip())):])
    return out


def _ents_map(rows, indent):
    """entities 卡片（mapping 形式，keys 位於 indent 欄），用於 vertical-stack／conditional 內。"""
    pad = " " * indent
    L = [f"{pad}type: entities", f"{pad}show_header_toggle: false", f"{pad}state_color: true", f"{pad}entities:"]
    for eid, name in rows:
        L += [f"{pad}  - entity: {eid}", f"{pad}    name: {q(name)}"]
    L += _shift(card_mod_wrap(), indent - 8)      # card_mod_wrap 以 list-item 縮排 8 欄輸出
    return L


def weather_sun_blocks():
    """V4.2.3（SOP-22）：「早安／到家」分頁的「日出日落的天氣調整」卡片：目前天氣與套用的分鐘、早安時間窗的實際起訖、各級調整分鐘與總開關。"""
    rows = [("weather.homeweather_zhu_nan_zhen", "目前天氣"),
            ("sensor.weather_sun_shift_min", "目前套用的天氣調整（分鐘）"), ("sensor.weather_dark_deg", "等效太陽仰角偏移（度）"),
            ("binary_sensor.weather_cloudy_sustained", "陰天（持續中）"), ("binary_sensor.weather_rainy_sustained", "下雨（持續中）"),
            ("binary_sensor.weather_heavy_sustained", "大雨雷雨（持續中）"),
            ("binary_sensor.scene_morning_window", "早安時段（含天氣調整）"),
            ("sensor.scene_morning_start", "早安起點（含天氣調整）"), ("sensor.scene_morning_end", "早安終點（含天氣調整）"),
            ("input_boolean.weather_sun_adjust_off", "關閉日出日落的天氣調整"),
            ("input_number.weather_sun_shift_cloudy_min", "調整分鐘｜陰天"), ("input_number.weather_sun_shift_rainy_min", "調整分鐘｜下雨"),
            ("input_number.weather_sun_shift_heavy_min", "調整分鐘｜大雨雷雨")]
    md = ["      - type: markdown",
          "        content: " + q("陰雨天天色提早變暗、早上更晚亮：早安起點往後延、終點往前提，100A 最早啟動、燈組動畫傍晚色調、大門開光自動開燈也一併調整。**調整分鐘＝目前天氣的級別**（陰 1、雨 2、大雨 3），天氣要持續 10 分鐘才套用、結束 20 分鐘後才取消。")] + MD_CSS
    return [section(heading("日出日落的天氣調整", "mdi:weather-sunset") + md + entities_card(rows))]


def garage_cars_blocks():
    """保全分頁：車庫車輛位置（前／後位、車種、車頭朝向）、出去可能性、樣板學習（packages/v42_garage_cars.yaml）。"""
    status = [
        ("sensor.garage_car_luxgen_n7", "Luxgen N7"),
        ("sensor.garage_car_tesla_model3", "Tesla Model 3"),
        ("input_select.garage_slot_front", "前位（靠鐵門）"),
        ("input_select.garage_facing_front", "前位車頭朝向"),
        ("input_select.garage_slot_back", "後位（內側）"),
        ("input_select.garage_facing_back", "後位車頭朝向"),
        ("sensor.garage_depart_likelihood", "出去可能性"),
        "{type: attribute, entity: sensor.garage_depart_likelihood, attribute: reasons, name: 可能性依據}",
        ("input_select.garage_charging_car", "現在充電的車"),
        ("input_select.garage_charging_slot", "現在充電的車位"),
        ("input_text.garage_charge_log", "充電紀錄（最近一次）"),
        ("input_text.garage_id_fix_log", "身分校正紀錄（車牌／排除法，最近一次）"),
        ("input_text.garage_plate_seen", "攝影機讀到的車牌（影像文字辨識，最近一次）"),
        ("input_boolean.garage_depart_candidate", "準備出門中"),
        ("input_text.garage_depart_last", "最近一次判斷"),
    ]
    learn = [
        ("input_select.garage_learn_slot", "車位"),
        ("input_select.garage_learn_car", "這個車位現在是"),
        ("input_select.garage_learn_facing", "車頭朝向（door＝朝鐵門／inside＝朝內）"),
        ("input_button.garage_learn_do", "用現在的畫面學習"),
    ]
    hint = ("車庫攝影機每分鐘（車庫有人／鐵門沒關／可能性高時每 15 秒）分析一次畫面，判斷前／後位是哪輛車、車頭朝向、車燈與位移，"
            "3D 平面圖同步顯示。車輛換位置或第一次使用時，請讓車停好，選好車位／車種／車頭朝向後按「用現在的畫面學習」；"
            "車位是空的就選「empty」。充電中的車會依功率（100%／20%＝Tesla、80%＝Luxgen）與充電線（拍到接到前位、拍不到＝後方車輛）自動記錄並補強辨識。自動開鐵門預設關閉，在「車庫車輛出門偵測」小組設定。")
    return [section(heading("車庫車輛位置", "mdi:car-multiple") + entities_card(status)),
            section(heading("車輛樣板學習", "mdi:school") + ["      - type: markdown", "        content: " + q("<sub>" + hint + "</sub>")] + MD_CSS + entities_card(learn))]


def family_tracking_blocks():
    """系統維護 > 家人裝置追蹤：每位家人一張現代化卡片（頭像＋在家狀態＋person 目前參考的裝置），
    下面是主要裝置選單；選到「其他」才出現自訂裝置輸入欄（00-2S／packages/v41_person_main_device.yaml）。"""
    people = (("kenny", "Kenny"), ("iris", "Iris"), ("jerry", "Jerry"), ("elay", "Elay"))
    L = heading("家人裝置追蹤", "mdi:account-switch-outline")
    L += ["      - type: custom:layout-card", "        layout_type: custom:grid-layout", "        layout:",
          "          grid-template-columns: repeat(auto-fit, minmax(290px, 1fr))", "          grid-gap: 10px", "          margin: 0", "        cards:"]
    for k, n in people:
        L += ["          - type: vertical-stack", "            cards:",
              "              - type: custom:button-card",
              f"                entity: sensor.person_{k}_source_device",
              "                show_name: false", "                show_icon: false", "                show_state: false",
              "                triggers_update: all",
              "                tap_action:", "                  action: more-info",
              "                styles:", "                  card:", "                    - cursor: pointer", "                    - height: auto",
              "                    - padding: 14px 16px", "                    - border-radius: 18px",
              "                    - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "                    - border: none",
              "                  grid:", "                    - grid-template-areas: '\"body\"'", "                    - grid-template-columns: 1fr",
              "                custom_fields:", "                  body: |"]
        js = FAMILY_JS.replace("__K__", k).replace("__N__", n).replace("__W__", "true" if k == "kenny" else "false")
        L += ["                    " + ln for ln in js.splitlines()]
        rows = [(f"input_select.person_main_device_{k}", "主要裝置")]
        if k == "kenny":
            rows.append(("input_text.watch_tracker_entity_kenny", "手錶追蹤裝置（entity）"))
        m1 = _ents_map(rows, 16)
        L += ["              - " + m1[0].strip()] + m1[1:]
        m2 = _ents_map([(f"input_text.person_main_device_custom_{k}", "自訂裝置（device_tracker.xxx）")], 18)
        L += ["              - type: conditional", "                conditions:", "                  - condition: state",
              f"                    entity: input_select.person_main_device_{k}", f"                    state: {q(FAMILY_OTHER)}",
              "                card:"] + m2
    hint = ("person.* 是 YAML 定義，在不在家都由它參考的裝置決定。選「主要裝置」會改寫 persons.yaml 並重新載入 person；"
            "為避免切換後在家狀態突然改變而誤觸發離家／到家情境，選的裝置目前的在家狀態必須和該家人目前一致，否則會退回原選項並發 HA 通知。"
            "清單沒有的裝置選「其他」，再輸入 device_tracker.xxx（小寫英數底線，可到 設定 > 裝置與服務 > 實體 搜尋 device_tracker）。")
    return [section(L), section(["      - type: markdown", "        content: " + q("<sub>" + hint + "</sub>")] + MD_CSS)]


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
    # V4.2.3（SOP-21）：廣播音效——結束音總開關、試聽類別與試聽按鈕（只播頂樓 HomePod、音量 0.3）
    snd_rows = [("input_boolean.announce_end_chime_off", "關閉廣播結束音效"), ("input_select.announce_demo_kind", "音效試聽類別（只播頂樓 HomePod）")]
    snd_btn = manual_button("script.announce_sound_demo", "input_select.announce_demo_kind", "播放廣播音效試聽", "mdi:music-note")
    return (heading("手動廣播", "mdi:bullhorn-outline") + entities_card(rows) + btn
            + heading("廣播音效", "mdi:music-note") + entities_card(snd_rows) + snd_btn)


LISTCARD_RECENT = r"""[[[
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const autos = Object.values(states).filter((s) => s.entity_id.indexOf('automation.') === 0);
  const wrapBox = (color, title, chip, rows, empty) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:14px 4px 6px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">
    <div style="display:flex;align-items:center;gap:10px;margin:0 16px 8px 0"><span style="flex:1;font-size:15px;font-weight:700;color:var(--primary-text-color)">${title}</span><span style="flex:none;font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;background:${color}1f;color:${color}">${chip}</span></div>
    <div style="max-height:340px;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding-right:12px">${rows || `<div style="padding:14px 4px;font-size:14px;color:var(--secondary-text-color)">${empty}</div>`}</div></div>`;
  const rowH = (dot, name, right) => `<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-top:.5px solid rgba(128,128,128,.28)"><span style="flex:none;width:8px;height:8px;border-radius:50%;background:${dot}"></span><span style="flex:1;min-width:0;font-size:14px;line-height:1.4;color:var(--primary-text-color);${wrap}">${esc(name)}</span><span style="flex:none;font-size:12.5px;color:var(--secondary-text-color);white-space:nowrap">${right}</span></div>`;

  const now = Date.now();
  const items = autos.filter((s) => s.attributes && s.attributes.last_triggered)
    .map((s) => ({ n: s.attributes.friendly_name || s.entity_id, t: new Date(s.attributes.last_triggered).getTime() }))
    .filter((x) => !isNaN(x.t) && now - x.t < 86400000 && now - x.t > -60000).sort((a, b) => b.t - a.t);
  const rel = (ms) => { const m = Math.max(0, Math.round(ms / 60000)); return m < 1 ? '剛剛' : m < 60 ? `${m} 分鐘前` : `${Math.floor(m / 60)} 小時前`; };
  const hm = (t) => { const d = new Date(t); return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); };
  return wrapBox('#0A84FF', '最近 24 小時觸發', `${items.length} 筆`, items.map((x) => rowH('#0A84FF', x.n, `${hm(x.t)}・${rel(now - x.t)}`)).join(''), '最近 24 小時沒有自動化被觸發。');
]]]"""
LISTCARD_OFF = r"""[[[
  const esc = (t) => String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const wrap = 'white-space:normal !important;word-break:break-word;overflow-wrap:anywhere;min-width:0';
  const autos = Object.values(states).filter((s) => s.entity_id.indexOf('automation.') === 0);
  const wrapBox = (color, title, chip, rows, empty) => `<div style="background:var(--card-background-color);box-shadow:inset 4px 0 0 ${color};border-radius:18px;padding:14px 4px 6px 20px;min-width:0;width:100%;box-sizing:border-box;overflow:hidden">
    <div style="display:flex;align-items:center;gap:10px;margin:0 16px 8px 0"><span style="flex:1;font-size:15px;font-weight:700;color:var(--primary-text-color)">${title}</span><span style="flex:none;font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;background:${color}1f;color:${color}">${chip}</span></div>
    <div style="max-height:340px;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding-right:12px">${rows || `<div style="padding:14px 4px;font-size:14px;color:var(--secondary-text-color)">${empty}</div>`}</div></div>`;
  const rowH = (dot, name, right) => `<div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-top:.5px solid rgba(128,128,128,.28)"><span style="flex:none;width:8px;height:8px;border-radius:50%;background:${dot}"></span><span style="flex:1;min-width:0;font-size:14px;line-height:1.4;color:var(--primary-text-color);${wrap}">${esc(name)}</span><span style="flex:none;font-size:12.5px;color:var(--secondary-text-color);white-space:nowrap">${right}</span></div>`;

  const off = autos.filter((s) => s.state === 'off').map((s) => s.attributes.friendly_name || s.entity_id).sort();
  return wrapBox(off.length ? '#D97706' : '#28A745', '目前停用的自動化', off.length ? `${off.length} 支` : '全部啟用', off.map((n) => rowH('#D97706', n, '已停用')).join(''), '沒有停用中的自動化。');
]]]"""


def list_js_card(js):
    """用 button-card 樣板做的清單卡片（可滑動）；Kiosk 讀得到同一份樣板。"""
    L = ["      - type: custom:button-card", "        triggers_update: all",
         "        show_name: false", "        show_icon: false", "        show_state: false",
         "        styles:", "          card:", "            - border-radius: 18px", "            - border: none",
         "            - box-shadow: 0 1px 2px rgba(0,0,0,.18)", "            - padding: 0", "            - white-space: normal",
         "          grid:", "            - grid-template-areas: '\"body\"'", "            - grid-template-columns: 1fr",
         "          custom_fields:", "            body:", "              - width: 100%", "              - min-width: 0",
         "              - text-align: left", "              - white-space: normal",
         "        custom_fields:", "          body: |"]
    for ln in js.splitlines():
        L.append("            " + ln)
    return L


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
             ("sensor.weather_sun_shift_min", "日出日落天氣調整｜目前分鐘"), ("input_boolean.weather_sun_adjust_off", "日出日落天氣調整｜關閉"),
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
    S.append(section(heading("目前停用的自動化", "mdi:pause-circle-outline") + list_js_card(LISTCARD_OFF)))
    S.append(section(heading("最近 24 小時觸發", "mdi:history") + list_js_card(LISTCARD_RECENT)))
    return S


COLS = 2            # 最多 2 欄（iPad 橫放／電腦）；layout-card 依螢幕寬度自動減少欄數：手機、iPad 直放 1 欄
COL_WIDTH = 340     # 每欄最小寬度（px）：窄螢幕（手機、iPad 分割畫面）也放得下，不會左右被切掉


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


def back_3d_block():
    """快捷按鈕：回到「智慧家庭」儀表板的 3D 介面（/lovelace-smart/home）。"""
    return [
        "    - type: button",
        '      name: "返回 3D 介面"',
        "      icon: mdi:cube-scan",
        "      show_state: false",
        "      icon_height: 26px",
        "      tap_action:",
        "        action: navigate",
        "        navigation_path: /lovelace-smart/home",
        "      card_mod:",
        "        style: |",
        "          ha-card { border-radius: 18px !important; border: none !important; box-shadow: 0 1px 2px rgba(0,0,0,.18) !important; background: #FFB900 !important; color: #111 !important; --primary-text-color: #111; --paper-item-icon-color: #111; font-weight: 700; }",
    ]


def view(title, path, icon, blocks):
    """vertical-layout：依序排卡片，欄與欄之間放 layout-break；欄數不夠時依序往下接（手機就是單欄、順序不變）。"""
    L = [f"  - title: {q(title)}", f"    path: {path}", f"    icon: {icon}", "    type: custom:vertical-layout",
         "    layout:", f"      max_cols: {COLS}", f"      width: {COL_WIDTH}",
         "      mediaquery:", "        '(min-width: 1000px)':", "          width: 460", "    cards:"]
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


PANEL_ROOT = [
"button_card_templates:",
"  prows:",
"    show_name: false",
"    show_icon: false",
"    show_state: false",
"    tap_action:",
"      action: none",
"    hold_action:",
"      action: none",
"    styles:",
"      card:",
"        - padding: 0",
"        - border-radius: 18px",
"        - border: none",
"        - box-shadow: 0 1px 2px rgba(0,0,0,.18)",
"        - overflow: hidden",
"      grid:",
"        - grid-template-areas: '\"rows\"'",
"        - grid-template-columns: 1fr",
"      custom_fields:",
"        rows:",
"          - width: 100%",
"          - min-width: 0",
"    custom_fields:",
"      rows: |",
"        [[[",
"        if (!window.__tabPtr) { window.__tabPtr = 1; document.addEventListener('pointerdown', (ev) => { if (ev.composedPath().some((el) => el && el.tagName && /TAB(?!LE)/.test(el.tagName))) window.__tabT = Date.now(); }, true); }",
"        const it = variables.items || [];",
"        const esc = (t) => String(t == null ? '' : t).replace(/[&<>\"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));",
"        const DI = {automation: 'mdi:robot-outline', input_boolean: 'mdi:toggle-switch-outline', switch: 'mdi:power-socket', light: 'mdi:lightbulb-outline', fan: 'mdi:fan'};",
"        const css = '<style>.r{display:flex;align-items:center;gap:12px;padding:10px 16px;min-height:50px;box-sizing:border-box}.r+.r{border-top:.5px solid rgba(128,128,128,.28)}'",
"          + '.ic{flex:none;width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center;background:rgba(10,132,255,.14);color:#0A84FF;--mdc-icon-size:19px;transition:background .15s,color .15s}'",
"          + '.r.on .ic{background:rgba(255,185,0,.2);color:#E09B00}'",
"          + '.n{flex:1;min-width:0;text-align:left;font-size:15px;line-height:1.35;white-space:normal;word-break:break-word;color:var(--primary-text-color);cursor:pointer}'",
"          + '.sw{position:relative;flex:none;width:51px;height:31px;border-radius:16px;border:0;padding:0;background:rgba(120,120,128,.32);cursor:pointer;transition:background .18s;-webkit-tap-highlight-color:transparent}'",
"          + '.sw::after{content:\"\";position:absolute;top:2px;left:2px;width:27px;height:27px;border-radius:50%;background:#fff;box-shadow:0 2px 4px rgba(0,0,0,.3);transition:left .18s}'",
"          + '.sw.on{background:#34C759}.sw.on::after{left:22px}.sw:disabled{opacity:.35;cursor:default}.na .n{opacity:.5}'",
"          + '.dv{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;font-size:11.5px;font-weight:700;vertical-align:1px;background:rgba(255,159,10,.18);color:#E08600}'",
"          + '.r.dev{background:rgba(255,159,10,.06)}</style>';",
"        return css + it.map(([e, n, d]) => {",
"          const s = states[e]; const st = s ? s.state : 'unavailable';",
"          const on = st === 'on'; const na = !s || st === 'unavailable'; const dev = !!d && !na && st !== d;",
"          const ic = (s && s.attributes.icon) || DI[e.split('.')[0]] || 'mdi:toggle-switch-outline';",
"          const nm = n || (s && s.attributes.friendly_name) || e;",
"          return `<div class=\"r ${on ? 'on' : ''} ${na ? 'na' : ''} ${dev ? 'dev' : ''}\"><span class=\"ic\"><ha-icon icon=\"${esc(ic)}\"></ha-icon></span>`",
"            + `<span class=\"n\" onclick=\"event.stopPropagation();this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:'${e}'},bubbles:true,composed:true}))\">${esc(nm)}${dev ? `<span class=\"dv\">平常${d === 'on' ? '開' : '關'}</span>` : ''}</span>`",
"            + `<button class=\"sw ${on ? 'on' : ''}\" ${na ? 'disabled' : ''} aria-label=\"切換\" onclick=\"event.stopPropagation();this.classList.toggle('on');this.parentNode.classList.toggle('on');document.querySelector('home-assistant').hass.callService('homeassistant','toggle',{entity_id:'${e}'})\"></button></div>`;",
"        }).join('');",
"        ]]]"
]
BACK_VIEW = [
"  - title: \"返回 3D\"",
"    path: back-3d",
"    icon: mdi:cube-scan",
"    cards:",
"    - type: custom:button-card",
"      show_name: false",
"      show_icon: false",
"      show_state: false",
"      tap_action:",
"        action: navigate",
"        navigation_path: /lovelace-smart/home",
"      styles:",
"        card:",
"          - border-radius: 18px",
"        grid:",
"          - grid-template-areas: '\"go\"'",
"      custom_fields:",
"        go: |",
"          [[[",
"          if (!window.__tabPtr) { window.__tabPtr = 1; document.addEventListener('pointerdown', (ev) => { if (ev.composedPath().some((el) => el && el.tagName && /TAB(?!LE)/.test(el.tagName))) window.__tabT = Date.now(); }, true); }",
"          if (location.pathname.endsWith('/back-3d') && (!window.__back3d || Date.now() - window.__back3d > 1500)) {",
"            window.__back3d = Date.now();",
"            const dest = window.__tabT && Date.now() - window.__tabT < 3000 ? '/lovelace-smart/home' : '/lovelace-automation/overview'; setTimeout(() => { history.replaceState(null, '', dest); window.dispatchEvent(new CustomEvent('location-changed', {detail: {replace: true}})); }, 0);",
"          }",
"          return '<div style=\"padding:28px 8px;text-align:center;font-size:15px;color:var(--secondary-text-color)\">正在返回 3D 介面…（沒有跳轉請點這裡）</div>';",
"          ]]]"
]


def build(data):
    _CM_DONE[0] = False
    global STATE
    STATE = {eid: st for eid, st, fn in data}
    DEFAULTS.clear()
    DEFAULTS.update(fetch_defaults([eid for eid, st, fn in data if eid.split(".")[0] in TOGGLE_DOMAINS]))
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
            if re.search(r"^input_select\.person_main_device_|^input_text\.person_main_device_custom_|^input_boolean\.person_main_device_busy$|^input_text\.watch_tracker_entity_kenny$", eid):
                continue   # 家人主要裝置選單放在「系統維護」的家人裝置追蹤區，自己畫（busy 旗標不顯示）
            if re.search(r"^input_select\.garage_(slot|facing|learn|charging)_|^input_button\.garage_learn_do$|^input_text\.garage_(depart_last|charge_log)$", eid):
                continue   # 車庫車輛位置與樣板學習放在「保全」分頁的專屬區塊（garage_cars_blocks），自己畫
            if INTERNAL_RE.search(eid):
                internal[cat].append((dom, fn or eid, eid))
            else:
                settings[cat].append((dom, fn or eid, eid))

    L = ["# 自動化管理面板（由 scripts/generate_automation_panel.py 產生，請勿直接手改；重新執行程式即可更新）",
         "title: 自動化管理"] + PANEL_ROOT + ["views:"]
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
        DEFAULTS_ON[0] = key != "internal"
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
        B.append(section(["      - type: markdown", "        content: " + q(f"**{title}**　{desc}")] + MD_CSS))
        if key == "system":
            B.extend(family_tracking_blocks())      # 家人主要裝置選擇＋person 目前參考的裝置
        if key == "scene":
            B.extend(weather_sun_blocks())      # 日出日落的天氣調整（SOP-22）
        if key == "security":
            B.extend(garage_cars_blocks())      # 車庫前／後位車輛、車頭朝向、出去可能性、樣板學習
        if key == "emergency":
            B.extend(disaster_blocks())      # 災防告警 sensor.disaster / 地震 sensor.earthquake 卡片
        # 開關：自動化＋輸入開關集中，依平常狀態分兩區（掃一眼：開著區有關掉的、關著區有打開的，就是和平常不同）
        tog = [(eid, fn) for fn, eid in autos[key]] + [(eid, short_name(fn)) for dom, fn, eid in settings[key] if dom in TOGGLE_DOMAINS]
        tog.sort(key=lambda r: (0 if r[0].startswith("automation.") else 1, clean_name(r[1])))
        auto_rows = [r for r in tog if DEFAULTS.get(r[0]) == "auto"]
        on_rows = [r for r in tog if r not in auto_rows and DEFAULTS.get(r[0], STATE.get(r[0])) == "on"]
        off_rows = [r for r in tog if r not in auto_rows and r not in on_rows]
        if on_rows:
            B.extend(list_blocks(f"平常開著（{len(on_rows)}）", on_rows, "mdi:toggle-switch", max_rows=60))
        if off_rows:
            B.extend(list_blocks(f"平常關著（{len(off_rows)}）", off_rows, "mdi:toggle-switch-off-outline", max_rows=60))
        if auto_rows:
            B.extend(list_blocks(f"會自動切換（{len(auto_rows)}）", auto_rows, "mdi:swap-horizontal", max_rows=60))
        # 其他設定：功能小組（依 SUBGROUPS 的順序），標題不再加數量
        left = [x for x in settings[key] if x[0] not in TOGGLE_DOMAINS]
        for label, pat in SUBGROUPS.get(key, []):
            grp = [x for x in left if re.search(pat, x[2] + " " + x[1])]
            if grp:
                left = [x for x in left if x not in grp]
                rows = [(eid, short_name(fn)) for dom, fn, eid in sorted(grp, key=lambda x: (x[0], x[1]))]
                B.extend(list_blocks(label, rows, max_rows=60))
        # 其餘依元件種類（同分類已有功能小組時，這些標為「其他…」）
        had_groups = len(left) != len([x for x in settings[key] if x[0] not in TOGGLE_DOMAINS])
        for dom, label in TYPE_LABEL:
            grp = [x for x in left if x[0] == dom]
            if grp:
                label = label.replace("其他", "")
                label = ("其他" + label) if had_groups else label
                rows = [(eid, short_name(fn)) for d, fn, eid in sorted(grp, key=lambda x: x[1])]
                B.extend(list_blocks(label, rows, max_rows=60))
        L += view(title, key, icon, B)
    i0 = L.index("views:") + 1
    L[i0:i0] = BACK_VIEW    # 分頁列最前面：返回 3D 介面（和 Kiosk 一樣）
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

    # Kiosk（NAS 8130 埠）的「自動化管理」頁讀這份清單
    try:
        subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve().parent / "gen_kiosk_panel_manifest.py")], check=True)
    except Exception as e:  # noqa: BLE001
        print("kiosk manifest failed:", e)

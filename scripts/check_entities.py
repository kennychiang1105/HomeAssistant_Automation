#!/usr/bin/env python3
"""實體引用檢查：掃描自動化／腳本／package，找出「引用了但系統裡不存在」的實體（改名、裝置淘汰最常見）。

用法：python3 check_entities.py [--json]
輸出：每行「實體｜引用它的檔案」；沒有問題時輸出 OK。
判斷「存在」：實體註冊表、資料庫 states_meta（曾經有過狀態）、YAML 裡自己定義的（helper、template 名稱）都算存在。
不會誤判：服務名稱（light.turn_on 之類）、屬性名稱（light.brightness）、以 _ 結尾的前綴樣板。
"""
import glob, json, os, re, sqlite3, sys

CFG = "/config" if os.path.isdir("/config/.storage") else "/homeassistant"
DOMAINS = ("light|switch|sensor|binary_sensor|input_boolean|input_number|input_text|input_select|input_datetime|"
           "input_button|device_tracker|media_player|fan|climate|cover|lock|camera|script|automation|timer|counter|"
           "scene|person|button|number|select|event|alarm_control_panel|humidifier|update|vacuum|weather|zone|group")
SERVICES = {"turn_on","turn_off","toggle","set_value","reload","trigger","start","cancel","finish","pause","increment",
            "decrement","reset","create","write","volume_set","play_media","media_stop","open_cover","close_cover",
            "set_percentage","set_datetime","select_option","snapshot","record","alarm_arm_away","alarm_arm_home",
            "alarm_arm_night","alarm_disarm","alarm_trigger","time_fired","data","brightness","color_temperature",
            "finished","mode","is_on","is_off","last_changed","speak","press","send_message"}
IGNORE = {"binary_sensor.template_sidebar_update_color"}  # themes.yaml 的樣式變數，不是實體
pat = re.compile(r"\b(%s)\.([a-z0-9_]+)\b" % DOMAINS)

files = (glob.glob(f"{CFG}/configuration/Automations/*.yaml") + glob.glob(f"{CFG}/Automations/*.yaml")
         + glob.glob(f"{CFG}/configuration/Scripts/*.yaml") + glob.glob(f"{CFG}/packages/*.yaml")
         + [f"{CFG}/automations.yaml"])
seen_files = set()
refs = {}
defined_text = ""
for f in files:
    real = os.path.realpath(f)
    if real in seen_files or not os.path.exists(f):
        continue
    seen_files.add(real)
    t = "\n".join(l for l in open(f, errors="ignore").read().split("\n") if not l.lstrip().startswith("#"))
    defined_text += t
    for m in pat.finditer(t):
        e = m.group(0)
        if e.endswith("_") or m.group(2) in SERVICES:
            continue
        refs.setdefault(e, set()).add(os.path.basename(f)[:24])

known = set()
try:
    known |= {e["entity_id"] for e in json.load(open(f"{CFG}/.storage/core.entity_registry"))["data"]["entities"]}
except Exception:
    pass
try:
    known |= {x["state"]["entity_id"] for x in json.load(open(f"{CFG}/.storage/core.restore_state"))["data"]}
except Exception:
    pass
try:
    db = sqlite3.connect(f"file:{CFG}/home-assistant_v2.db?mode=ro", uri=True, timeout=30)
    known |= {r[0] for r in db.execute("select entity_id from states_meta")}
except Exception as ex:
    print("資料庫讀取失敗：", ex, file=sys.stderr)

# YAML 自己定義的 helper／template：名稱（name:）轉成 entity_id 太複雜，改成「定義檔裡出現 'key:' 縮排行」的粗略判斷
def defined_in_yaml(e):
    obj = e.split(".", 1)[1]
    return re.search(r"^\s{2,4}%s:\s*$" % re.escape(obj), defined_text, re.M) is not None or ("unique_id: " + obj) in defined_text

missing = sorted((e, sorted(fs)[:3]) for e, fs in refs.items() if e not in known and e not in IGNORE and not defined_in_yaml(e))
if "--json" in sys.argv:
    print(json.dumps(missing, ensure_ascii=False))
elif not missing:
    print("OK")
else:
    print(f"發現 {len(missing)} 個可能不存在的實體：")
    for e, fs in missing:
        print(f"{e}｜{'、'.join(fs)}")

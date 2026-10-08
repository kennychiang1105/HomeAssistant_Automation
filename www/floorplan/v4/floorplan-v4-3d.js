/* Floorplan V4.0-beta 1 - real 3D view
 * custom:floorplan-v4-3d       three.js scene extruded from the 2D plan SVGs (walls/furniture),
 *                              orbit/pinch/pan, per-light glow that follows the light colour,
 *                              stairs / windows / doors / furniture heights, roller door that follows the cover,
 *                              HTML hotspots with names (tap = toggle, hold = more-info, ✎ = drag to fix position;
 *                              positions are saved per HA user under frontend user data "floorplan_v4_positions")
 * custom:floorplan-v4-sidebar  clock + floor navigation + people at home (landscape layout)
 *
 * The selected floor is shared with floorplan-v4-controls through localStorage + a window event.
 */
const KEY = "floorplan_v4_floor";
const EVT = "floorplan-v4-floor";
const LIB = new URL("./lib/", import.meta.url).href;
let threePromise = null;
const loadThree = () => {
  threePromise = threePromise || Promise.all([
    import(LIB + "three.module.js"),
    import(LIB + "OrbitControls.js"),
    import(LIB + "SVGLoader.js"),
  ]).then(([THREE, oc, sl]) => ({ THREE, OrbitControls: oc.OrbitControls, SVGLoader: sl.SVGLoader }));
  return threePromise;
};
const getFloor = (cfg) => {
  let f = null;
  try { f = localStorage.getItem(KEY); } catch (e) { /* ignore */ }
  return f && (cfg.floors[f] || f === "全棟") ? f : cfg.default || Object.keys(cfg.floors)[0];
};
const setFloor = (f) => {
  try { localStorage.setItem(KEY, f); } catch (e) { /* ignore */ }
  window.dispatchEvent(new CustomEvent(EVT, { detail: f }));
};

const FLOOR_GAP = 150;
const DEFAULT_PEOPLE = [
  { id: "kenny", name: "Kenny", color: "#4fc3f7" },
  { id: "elay", name: "Elay", color: "#f48fb1" },
  { id: "jerry", name: "Jerry", color: "#a5d6a7" },
  { id: "iris", name: "Iris", color: "#ffcc80" },
];
const PEOPLE_CSS = `
  .row { display:flex; align-items:center; gap:10px; padding:6px 4px; }
  .av { flex:none; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center;
        color:#111; font:700 14px sans-serif; border:2px solid transparent; }
  .av.off { filter:grayscale(1); opacity:.45; }
  .av.on { border-color:#43a047; }
  .nm { font:600 14px sans-serif; color:var(--primary-text-color); }
  .lc { font:12px sans-serif; color:var(--secondary-text-color); }`;
const peopleHtml = (h, people) => people.map((p) => {
  const home = h.states[`binary_sensor.at_home_${p.id}`]?.state === "on";
  let loc = h.states[`sensor.at_home_${p.id}_location`]?.state;
  if (!home) loc = "離家";
  else if (!loc || ["unknown", "unavailable"].includes(loc)) loc = "在家";
  return `<div class="row"><div class="av ${home ? "on" : "off"}" style="background:${p.color}">${p.name.slice(0, 1)}</div>
    <div><div class="nm">${p.name}</div><div class="lc">${loc}</div></div></div>`;
}).join("");

class FloorplanV4People extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(cfg) {
    this._cfg = cfg;
    this.shadowRoot.innerHTML = `<style>:host{display:block} .box{background:var(--card-background-color,#1c1c1e);
      border-radius:16px;padding:10px 12px;display:grid;grid-template-columns:repeat(2,1fr);gap:0 8px} ${PEOPLE_CSS}</style>
      <div class="box"></div>`;
  }
  set hass(h) {
    this.shadowRoot.querySelector(".box").innerHTML = peopleHtml(h, this._cfg.people || DEFAULT_PEOPLE);
  }
  getCardSize() { return 3; }
}

// friendly name -> icon (keywords from the Chinese entity names), then fallback by kind
const NAME_ICONS = [
  [/崁燈/, "mdi:light-recessed"], [/壁燈/, "mdi:wall-sconce-flat"], [/檯燈/, "mdi:desk-lamp"],
  [/床頭燈/, "mdi:lamp"], [/樓梯燈/, "mdi:stairs"], [/燈組/, "mdi:ceiling-light"], [/路燈|陽台燈/, "mdi:outdoor-lamp"],
  [/門口燈/, "mdi:coach-lamp"], [/環繞燈/, "mdi:led-strip-variant"], [/小燈/, "mdi:lamp"], [/捕蚊/, "mdi:bug"],
  [/印表機/, "mdi:printer"], [/Workstation|工作站/i, "mdi:desktop-tower"], [/網關/, "mdi:router-wireless"],
  [/homepod/i, "mdi:speaker"], [/電視/, "mdi:television"], [/空氣清淨/, "mdi:air-purifier"], [/電風扇|風扇/, "mdi:fan"],
  [/空調|冷氣/, "mdi:air-conditioner"], [/Garage|鐵門/i, "mdi:garage-variant"], [/攝影機.*人員/, "mdi:account-search"],
  [/一氧化碳/, "mdi:molecule-co"], [/甲醛/, "mdi:flask-outline"], [/空氣品質/, "mdi:air-filter"],
  [/燈/, "mdi:lightbulb"], [/插座|Plug/i, "mdi:power-socket-eu"],
];
const KIND_ICONS = {
  light: "mdi:lightbulb", switch: "mdi:lightbulb", plug: "mdi:power-socket-eu", fan: "mdi:fan",
  cover: "mdi:garage-variant", lock: "mdi:lock", climate: "mdi:air-conditioner", camera: "mdi:cctv",
  media_player: "mdi:speaker", motion: "mdi:motion-sensor", person: "mdi:account-search",
  safety: "mdi:alert-circle-outline", doorlock: "mdi:door", ap: "mdi:wifi", printer: "mdi:printer",
};
const VALUE_KINDS = ["temp", "hum", "value"];
const TOGGLE_KINDS = ["light", "switch", "plug", "fan", "cover"];
// Taiwan comfort bands (CWA-style, shifted +2 °C for indoor sensors): temperature °C and relative humidity %
const tempColor = (t) => (t < 16 ? "#4f8fff" : t < 20 ? "#4fc3f7" : t < 24 ? "#4dd0b4" : t < 28 ? "#66bb6a"
  : t < 30 ? "#ffd54f" : t < 32 ? "#ffa726" : t < 35 ? "#ff7043" : "#e53935");
const humColor = (h) => (h < 40 ? "#ffb74d" : h < 60 ? "#66bb6a" : h < 70 ? "#4fc3f7" : h < 80 ? "#5c8dff" : "#7e57c2");
const NAME_OVERRIDE = {
  "sensor.tesla_charger_homekit_status": "Tesla充電樁",
  "input_boolean.er_lou_men_suo_tong_bu_kai_guan": "二樓門鎖",
  "cover.garage": "車庫鐵門",
  "switch.tp_link_power_strip_028a": "小燕網關",
  "switch.xiao_yan_wang_guan_cha_zuo": "小燕網關",
  "switch.ding_lou_homepodcha_zuo": "頂樓HomePod插座",
  "sensor.udmse_kenny_state": "UDM SE 主機",
  "sensor.switch_lite_8_poe_state": "Switch Lite",
  "sensor.ricoh_sp_c261sfnw": "RICOH 印表機",
  "sensor.u6_pro_2f_state": "U6-Pro",
  "sensor.u6_mesh_1f_state": "U6 Mesh",
  "sensor.u6_lite_3f_state": "U6-Lite",
  "sensor.u6_extender_4f_elay_state": "U6 Extender",
  "sensor.u6_iw_4f_jerry_state": "U6-IW",
  "sensor.u6_iw_5f_kenny_state": "U6-IW",
};
const cleanName = (s, d) => {
  if (NAME_OVERRIDE[d.entity]) return NAME_OVERRIDE[d.entity];
  let n = s?.attributes?.friendly_name || d.entity.split(".")[1];
  n = n.replace(/iSmartgate Garage door|Garage door/i, "車庫鐵門").replace(/\s*(High|Medium) resolution channel/i, "").replace(/\s*(灯|Plug|狀態)$/i, "")
    .replace(/^TP-LINK_Power Strip_\w+\s*/i, "").replace(/^TP-LINK_\S+\s*/, "").replace(/\s*小米智能變頻電風扇.*$/, "").replace(/小米|傳感器|感測器|環境/g, "")
    .replace(/\(Homepod\)/i, " HomePod").replace(/AsusWorkstation/i, "ASUS").replace(/Tesla Wall Connector/i, "Tesla")
    .replace(/\s*偵測到人員$/, " 人體").replace(/\s*Motion Left$/i, " 左").replace(/\s*Motion Right$/i, " 右")
    .replace(/\s*(Motion|動作)$/i, " 動作").replace(/危險$/, "");
  if (VALUE_KINDS.includes(d.kind)) n = n.replace(/溫度|濕度|有效/g, "");
  n = n.replace(/^(\S+)\s+\1/, "$1").replace(/\s+/g, " ").trim();
  return n || (s?.attributes?.friendly_name || d.entity);
};
// the floor is already selected, so "頂樓 / 五樓 …" prefixes are dropped when that keeps names unique
const stripFloor = (n) => {
  const m = n.replace(/^(頂樓|一樓|二樓|三樓|四樓|五樓|車庫|廚房|客廳|餐廳)\s*(?=\S{2,})/, "");
  return m.length >= 2 ? m : n;
};
const clip = (n, max = 8) => ([...n].length > max ? [...n].slice(0, max).join("") + "…" : n);
const iconFor = (s, d) => {
  const n = s?.attributes?.friendly_name || "";
  if (d.kind === "motion") return "mdi:motion-sensor";
  if (d.kind === "camera") return "mdi:cctv";
  if (d.kind === "person") return "mdi:account-search";
  for (const [re, ic] of NAME_ICONS) if (re.test(n)) return ic;
  return KIND_ICONS[d.kind] || "mdi:circle-small";
};
const POS_KEY = "floorplan_v4_positions";
const CATS = [["light", "燈光"], ["device", "設備"], ["sensor", "感測"], ["camera", "攝影機"], ["env", "環境"],
  ["stair", "樓梯"], ["people", "成員"]];
const PRESETS = [["all", "全部"], ["light", "燈光"], ["device", "設備"], ["detect", "偵測"], ["custom", "自訂"]];
const PRESET_CATS = { all: CATS.map((c) => c[0]), light: ["light", "stair"], device: ["device", "stair"],
  detect: ["sensor", "camera", "env", "stair", "people"] };
const BUSY_FLOOR = 14;                       // floors with more lights/devices than this start in 偵測顯示
const catOf = (d) => (d.kind === "light" || d.kind === "switch" ? "light"
  : ["motion", "person", "safety", "ap"].includes(d.kind) ? "sensor"
  : d.kind === "camera" ? "camera" : VALUE_KINDS.includes(d.kind) ? "env" : d.kind === "stair" ? "stair" : "device");
// one charger = sensor.tesla_charger_homekit_status (text) + sensor.tesla_wall_connector_total_power (kW)
const chargerInfo = (st) => {
  const t = String(st["sensor.tesla_charger_homekit_status"]?.state || "");
  const raw = String(st["sensor.tesla_wall_connector_status"]?.state || "");
  const plugged = st["binary_sensor.tesla_wall_connector_vehicle_connected"]?.state === "on";
  const pw = st["sensor.tesla_wall_connector_total_power"];
  let kw = parseFloat(pw?.state);
  if (!isNaN(kw) && /^w$/i.test(pw?.attributes?.unit_of_measurement || "")) kw /= 1000;
  let key = "unplugged", label = t.replace(/^無充電$/, "未插線") || "未知";
  if (/error|fault/i.test(raw)) { key = "error"; label = "異常"; }
  else if (/充電中/.test(t)) { key = "charging"; label = t.replace("充電中", " 充電中").trim(); }   // "Tesla 充電中" / "Luxgen 充電中"
  else if (/充電完成/.test(t)) { key = "done"; label = "充電完成"; }
  else if (/已連接|準備/.test(t)) { key = "plugged"; label = "已插線 · 待充電"; }
  else if (/無充電/.test(t)) { key = "unplugged"; label = "未插線"; }
  const power = key === "charging" && !isNaN(kw) ? ` · ${kw.toFixed(1)} kW` : "";
  return { key, label, power, plugged: plugged && key !== "unplugged", kw };
};
const CHARGER_TXT = { charging: "充電中", charging_reduced: "降功率充電", charging_finished: "充電完成", ready: "就緒",
  connected: "已插線", negotiating: "協商中", waiting_car: "等待車輛", not_connected: "未插線", booting: "開機中", error: "異常" };
const typeText = (s, d) => {
  const st = s.state, on = st === "on";
  const pct = s.attributes.brightness != null && on ? ` ${Math.round(s.attributes.brightness / 2.55)}%` : "";
  switch (d.kind) {
    case "light": case "switch": return `燈 · ${on ? "開" + pct : "關"}`;
    case "plug": return `插座 · ${on ? "開" : "關"}`;
    case "fan": return `風扇 · ${on ? "運轉" : "關"}`;
    case "climate": return `空調 · ${st === "off" ? "關" : st}`;
    case "media_player": return `喇叭 · ${({ playing: "播放中", paused: "暫停", idle: "閒置", off: "關" })[st] || st}`;
    case "cover": return `鐵門 · ${({ open: "開", closed: "關", opening: "開啟中", closing: "關閉中" })[st] || st}`;
    case "doorlock": return `門鎖 · ${on ? "已開鎖" : "已上鎖"}`;
    case "lock": return `門鎖 · ${st === "locked" ? "上鎖" : "解鎖"}`;
    case "motion": return `動作感測 · ${on ? "有動作" : "無"}`;
    case "person": return `人體偵測 · ${on ? "偵測到人" : "無"}`;
    case "safety": return `安全 · ${on ? "危險" : "正常"}`;
    case "camera": return `攝影機 · ${({ recording: "錄影中", streaming: "串流中", idle: "待命" })[st] || st}`;
    case "charger": return "";                                       // filled from chargerInfo() in _sync
    default: return "";
  }
};

class FloorplanV43D extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._groups = {};
    this._spots = [];
    this._ready = false;
    this._labels = true;
    this._edit = false;
    this._ovr = {};
  }
  setConfig(cfg) {
    if (!cfg.floors) throw new Error("floors is required");
    this._cfg = JSON.parse(JSON.stringify(cfg));     // own copy: positions can be edited
    this._floor = getFloor(cfg);
    try { this._labels = localStorage.getItem("floorplan_v4_labels") !== "0"; } catch (e) { /* ignore */ }
    const order = [...Object.keys(cfg.floors), "全棟"];
    const tabs = cfg.tabs
      ? `<div class="tabs">${order.map((k) => `<button data-f="${k}">${k}</button>`).join("")}</div>` : "";
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .tabs { display:grid; grid-template-columns:repeat(${order.length},1fr); gap:6px; margin-bottom:8px; }
        .tabs button { border:0; border-radius:12px; padding:10px 2px; font:600 14px sans-serif;
                       background:rgba(120,120,128,.16); color:var(--primary-text-color); cursor:pointer; }
        .tabs button.on { background:#FFB900; color:#111; }
        .wrap { position:relative; height:${(cfg.height || "70vh").replace(/dvh/g, "vh")}; height:${cfg.height || "70vh"}; border-radius:16px; overflow:hidden;
                background:radial-gradient(ellipse at 50% 35%, #2a2f3a 0%, #14161b 70%); }
        canvas { width:100%; height:100%; display:block; touch-action:none; outline:none; }
        .spots { position:absolute; inset:0; pointer-events:none; overflow:hidden; }
        .pin { position:absolute; left:0; top:0; width:0; height:0; pointer-events:none; --off:24px; }
        .pin.hide, .pin.missing { display:none !important; }
        .dot { position:absolute; left:-5px; top:-5px; width:10px; height:10px; border-radius:50%;
               background:#fff; box-shadow:0 0 0 2px rgba(0,0,0,.55); pointer-events:auto; }
        .links { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; }
        .links polyline { fill:none; stroke:rgba(255,255,255,.78); stroke-width:1.5; stroke-linejoin:round; }
        .tag { position:absolute; left:0; top:0; display:flex; align-items:center;
               gap:6px; padding:3px 9px 3px 3px; border-radius:20px; white-space:nowrap; pointer-events:auto; cursor:pointer;
               background:rgba(20,21,25,.88); border:1px solid rgba(255,255,255,.28); color:#fff;
               user-select:none; -webkit-user-select:none; touch-action:none; box-shadow:0 2px 8px rgba(0,0,0,.4); }
        .ic { width:30px; height:30px; flex:none; border-radius:50%; display:flex; align-items:center; justify-content:center;
              background:#3a3d45; --mdc-icon-size:18px; transition:background .2s; }
        .tx { display:flex; flex-direction:column; line-height:1.15; }
        .nm { font:700 12px sans-serif; }
        .ty { font:500 10.5px sans-serif; color:rgba(255,255,255,.7); }
        .sm .ic { width:26px; height:26px; --mdc-icon-size:16px; } .sm .nm { font-size:11px; } .sm .ty { font-size:9.5px; }
        .sm .tag { gap:5px; padding:2px 7px 2px 2px; } .sm .seg button { padding:7px 8px; font-size:11.5px; }
        .sm .tools button, .sm .zones button { padding:6px 8px; font-size:11px; } .sm .scn button { padding:8px 4px; font-size:12px; }
        .nolabels .tx, .pin.compact .tx { display:none; }
        .pin.compact .tag { padding:3px; }
        .scn { position:absolute; left:8px; right:8px; bottom:56px; display:flex; gap:8px; z-index:4; justify-content:center; }
        .scn button { flex:1; max-width:120px; border:0; border-radius:14px; padding:10px 6px; cursor:pointer;
                      display:flex; align-items:center; justify-content:center; gap:6px; --mdc-icon-size:20px;
                      background:rgba(20,21,25,.9); color:#fff; font:700 13px sans-serif; box-shadow:0 2px 8px rgba(0,0,0,.4); }
        .scn button.on { background:#FFB900; color:#111; }
        .zones { position:absolute; left:8px; top:8px; display:flex; gap:6px; z-index:3; flex-wrap:wrap; max-width:60%; }
        .zones button { border:0; border-radius:10px; padding:7px 11px; font:600 12px sans-serif; cursor:pointer;
                        background:rgba(30,30,32,.8); color:#fff; }
        .zones button.on { background:#4fc3f7; color:#0b1a24; }
        .nolabels .tag { padding:3px; }
        .pin.on .ic { background:#FFB900; color:#111; } .pin.on .dot { background:#FFB900; }
        .pin.trig .ic { background:#ff7043; color:#111; } .pin.trig .dot { background:#ff7043; }
        .pin.alert .ic { background:#e53935; } .pin.alert .dot { background:#e53935; }
        .pin.env .ic { background:#2c4a5c; color:#9fdcff; } .pin.env.temp .ic { background:#5a3a32; color:#ffbca8; }
        .pin.floorbadge .nm { font-size:15px; } .pin.floorbadge .tag { padding:4px 12px 4px 4px; }
        .pin.stair .ic { background:#5b4a1d; color:#ffe08a; } .pin.stair .tag { border-color:rgba(255,224,138,.6); }
        .pin.person .ic { color:#111; font:700 13px sans-serif; }
        .pin.cam .ic { background:#1f4f6b; color:#bfe9ff; }
        .editing .tag { outline:2px dashed #FFB900; outline-offset:2px; cursor:move; }
        .tools { position:absolute; right:8px; top:8px; display:flex; gap:6px; z-index:3; }
        .tools button, .chips button { border:0; border-radius:10px; padding:7px 10px; font:600 12px sans-serif; cursor:pointer;
                        background:rgba(30,30,32,.78); color:#fff; flex:none; }
        .tools button.on, .chips button.on { background:#FFB900; color:#111; }
        .filter { position:absolute; left:8px; right:8px; bottom:12px; display:flex; gap:6px; align-items:flex-end; z-index:4; }
        .seg { display:flex; gap:2px; padding:3px; border-radius:12px; background:rgba(20,21,25,.88); flex:none;
               box-shadow:0 2px 8px rgba(0,0,0,.4); }
        .seg button { border:0; border-radius:9px; padding:8px 11px; font:700 12.5px sans-serif; cursor:pointer;
                      background:transparent; color:#fff; }
        .seg button.on { background:#FFB900; color:#111; }
        .chips { display:none; gap:6px; overflow-x:auto; scrollbar-width:none; }
        .chips.show { display:flex; }
        .chips::-webkit-scrollbar { display:none; }
        .hint { position:absolute; left:10px; top:12px; right:200px; font:11px sans-serif; color:rgba(255,255,255,.5);
                pointer-events:none; }
        .ver { position:absolute; right:10px; bottom:5px; font:600 10.5px sans-serif; letter-spacing:.3px;
               color:rgba(255,255,255,.45); pointer-events:none; z-index:3; }
        .msg { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
               font:14px sans-serif; color:#aaa; text-align:center; padding:20px; }
      </style>
      ${tabs}
      <div class="wrap"><canvas></canvas><div class="spots"></div>
        <div class="tools"><button data-t="labels">名稱</button><button data-t="edit">✎ 調整位置</button>
          <button data-t="reset" style="display:none">重設</button></div>
        <div class="filter"><div class="seg">${PRESETS.map(([k, n]) => `<button data-p="${k}">${n}</button>`).join("")}</div>
          <div class="chips">${CATS.map(([k, n]) => `<button data-c="${k}">${n}</button>`).join("")}</div></div>
        <div class="hint"></div><div class="zones"></div><div class="scn"></div>
        <div class="ver">UI4.0</div>
        <div class="msg">載入 3D…</div></div>`;
    this._onTabs();
    this._onTools();
    this._init();
  }
  set hass(h) {
    const first = !this._hass;
    this._hass = h;
    if (first) this._loadOverrides();
    if (!this._ready) return;
    const now = Date.now();                       // HA pushes every state change: sync at most ~3 times a second
    if (now - (this._lastSync || 0) > 350) { this._lastSync = now; clearTimeout(this._syncT); this._sync(); }
    else { clearTimeout(this._syncT); this._syncT = setTimeout(() => { this._lastSync = Date.now(); this._sync(); }, 350); }
  }
  getCardSize() { return 8; }
  connectedCallback() {
    this._evt = (e) => {
      if (e.detail !== this._floor) { this._floor = e.detail; this._applyFloor(); }
    };
    window.addEventListener(EVT, this._evt);
    this._ro = new ResizeObserver(() => this._resize());
    this._ro.observe(this);
    // 斷線後馬上重新接上（HA 重新排版／條件卡片切換）時，上一輪的「停止」旗標還在，渲染迴圈會在下一幀自己結束，
    // 之後切樓層圖釘就不會再被定位（全部擠在左上角、3D 畫面停住）。所以重接時一定先取消停止並重新量測。
    this._stop = false;
    if (this._ready) { this._loop(); this._resize(); this._barDirty = true; this._dirty = true; }
  }
  disconnectedCallback() {
    window.removeEventListener(EVT, this._evt);
    this._ro?.disconnect();
    this._stop = true;
  }
  _onTabs() {
    this.shadowRoot.querySelector(".tabs")?.addEventListener("click", (e) => {
      const f = e.target.closest("button")?.dataset.f;
      if (f) { this._floor = f; setFloor(f); this._applyFloor(); }
    });
  }
  _onTools() {
    const root = this.shadowRoot;
    const sync = () => {
      root.querySelector('[data-t="labels"]').classList.toggle("on", this._labels);
      root.querySelector('[data-t="edit"]').classList.toggle("on", this._edit);
      root.querySelector('[data-t="reset"]').style.display = this._edit ? "" : "none";
      root.querySelector(".spots").classList.toggle("nolabels", !this._labels);
      root.querySelector(".spots").classList.toggle("editing", this._edit);
      const preset = this._presetFor(this._floor);
      this._cats = new Set(preset === "custom" ? [...this._custom] : PRESET_CATS[preset]);
      root.querySelectorAll(".seg button").forEach((b) => b.classList.toggle("on", b.dataset.p === preset));
      root.querySelector(".chips").classList.toggle("show", preset === "custom");
      root.querySelectorAll(".chips button").forEach((b) => b.classList.toggle("on", this._custom.has(b.dataset.c)));
      this._applyCats?.();
      root.querySelector(".hint").textContent = this._edit ? "調整位置：拖曳圓點到正確位置，放開即儲存" : "";
      this._barDirty = true;
    };
    const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (err) { return d; } };
    const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (err) { /* ignore */ } };
    this._custom = new Set(load("floorplan_v4_custom", CATS.map((c) => c[0])));
    this._presets = load("floorplan_v4_presets", {});           // chosen preset per floor
    this._syncTools = sync;
    root.querySelector(".seg").addEventListener("click", (e) => {
      const p = e.target.closest("button")?.dataset.p;
      if (!p) return;
      this._presets[this._floor] = p;
      save("floorplan_v4_presets", this._presets);
      sync();
      this._dirty = true;
    });
    root.querySelector(".chips").addEventListener("click", (e) => {
      const c = e.target.closest("button")?.dataset.c;
      if (!c) return;
      if (this._custom.has(c)) this._custom.delete(c); else this._custom.add(c);
      save("floorplan_v4_custom", [...this._custom]);
      sync();
      this._dirty = true;
    });
    root.querySelector(".tools").addEventListener("click", (e) => {
      const t = e.target.closest("button")?.dataset.t;
      if (t === "labels") {
        this._labels = !this._labels;
        try { localStorage.setItem("floorplan_v4_labels", this._labels ? "1" : "0"); } catch (err) { /* ignore */ }
      } else if (t === "edit") this._edit = !this._edit;
      else if (t === "reset" && confirm("清除所有自訂位置，回到平面圖原始位置？")) {
        this._ovr = {};
        this._saveOverrides();
        this._applyOverrides(true);
      }
      sync();
      this._dirty = true;
    });
    sync();
  }

  _presetFor(floor) {
    if (this._presets?.[floor]) return this._presets[floor];
    const fls = floor === "全棟" ? Object.values(this._cfg.floors) : [this._cfg.floors[floor]].filter(Boolean);
    const busy = fls.reduce((n, fl) => n + fl.devices.filter((d) => ["light", "device"].includes(catOf(d))).length, 0);
    return busy > BUSY_FLOOR ? "detect" : "all";
  }

  // ---- position overrides (saved per HA user with frontend/set_user_data) ----
  async _loadOverrides() {
    try {
      const r = await this._hass.callWS({ type: "frontend/get_user_data", key: POS_KEY });
      this._ovr = r?.value || {};
    } catch (e) { this._ovr = {}; }
    this._applyOverrides(false);
  }
  _saveOverrides() {
    this._hass?.callWS({ type: "frontend/set_user_data", key: POS_KEY, value: this._ovr }).catch((e) => console.error(e));
  }
  _applyOverrides(resetFirst) {
    for (const [n, fl] of Object.entries(this._cfg.floors)) {
      for (const d of fl.devices) {
        if (resetFirst && d._x0 != null) { d.x = d._x0; d.y = d._y0; }
        if (d._x0 == null) { d._x0 = d.x; d._y0 = d.y; }
        const o = this._ovr[`${n}|${d.entity}`];
        if (o) { d.x = o[0]; d.y = o[1]; }
        this._moveDecal(n, d);
      }
    }
    this._dirty = true;
  }
  _moveDecal(floor, d) {
    const m = this._groups[floor]?.decals[d.entity];
    if (m) m.position.set(d.x, 4.5, d.y);
  }

  async _init() {
    const say = (t) => { const m = this.shadowRoot.querySelector(".msg"); if (m) m.textContent = t; };
    try { await this._init2(say); } catch (e) {
      console.error("floorplan-v4-3d", e);
      say("3D 錯誤：" + (e && (e.stack || e.message) || e).toString().slice(0, 300));
    }
  }

  async _init2(say) {
    say("載入 three.js…");
    const lib = await loadThree();
    say("建立場景…");
    const { THREE, OrbitControls, SVGLoader } = lib;
    this._T = THREE;
    this._SVG = SVGLoader;
    const root = this.shadowRoot;
    const canvas = root.querySelector("canvas");
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.localClippingEnabled = true;
    this._renderer = renderer;
    const scene = new THREE.Scene();
    this._scene = scene;
    scene.add(new THREE.HemisphereLight(0xe6edff, 0x2a2e38, 1.05));
    const sun = new THREE.DirectionalLight(0xffffff, 1.25);
    sun.position.set(-300, 650, 420);
    scene.add(sun);
    const fill = new THREE.DirectionalLight(0xbfd4ff, 0.35);
    fill.position.set(400, 300, -300);
    scene.add(fill);
    const cam = new THREE.PerspectiveCamera(38, 1, 5, 6000);
    this._cam = cam;
    const controls = new OrbitControls(cam, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.12;
    controls.maxPolarAngle = Math.PI * 0.47;
    controls.minPolarAngle = 0.12;
    controls.screenSpacePanning = true;
    controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
    controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN
    };
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    controls.addEventListener("change", () => { this._dirty = true; });
    this._controls = controls;
    this._ray = new THREE.Raycaster();

    const c = document.createElement("canvas");
    c.width = c.height = 128;
    const g = c.getContext("2d");
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, "rgba(255,255,255,1)");
    grad.addColorStop(0.45, "rgba(255,255,255,.45)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
    this._glowTex = new THREE.CanvasTexture(c);

    const loader = new SVGLoader();
    say("載入平面圖…");
    const names = Object.keys(this._cfg.floors);
    await Promise.all(names.map(async (n, idx) => {
      const fl = this._cfg.floors[n];
      const text = await (await fetch(fl.plan)).text();
      this._groups[n] = this._buildFloor(THREE, loader, text, fl, idx);
      scene.add(this._groups[n].group);
    }));
    say("組裝 3D…");
    root.querySelector(".msg")?.remove();
    this._ready = true;
    this._applyOverrides(false);
    this._applyFloor();
    this._resize();
    if (this._hass) this._sync();
    this._loop();
  }

  _buildFloor(THREE, loader, svgText, fl, idx) {
    const group = new THREE.Group();
    const inner = new THREE.Group();            // plan space: x -> x, svg y -> z, height -> y
    inner.position.set(-fl.width / 2, 0, -fl.height / 2);
    group.add(inner);
    const lam = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, side: THREE.DoubleSide, ...extra });
    const matCache = {};
    const M = (c) => (matCache[c] = matCache[c] || lam(c));
    const edgeMat = new THREE.LineBasicMaterial({ color: 0x1b1d22, transparent: true, opacity: 0.5 });
    const edges = (mesh, parent = inner) => {
      const e = new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry, 30), edgeMat);
      e.position.copy(mesh.position); e.rotation.copy(mesh.rotation); e.scale.copy(mesh.scale);
      parent.add(e);
    };
    // box in plan coordinates: x0,y0 = north-west corner, w along x, d along y, z0..z0+h height
    const box = (x0, y0, w, d, z0, h, mat, parent = inner, outline = true) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(Math.max(w, 0.5), Math.max(h, 0.3), Math.max(d, 0.5)), mat);
      m.position.set(x0 + w / 2, z0 + h / 2, y0 + d / 2);
      parent.add(m);
      if (outline) edges(m, parent);
      return m;
    };
    const cyl = (cx, cy, rx, ry, z0, h, mat, parent = inner) => {
      const m = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, h, 28), mat);
      m.scale.set(rx, 1, ry);
      m.position.set(cx, z0 + h / 2, cy);
      parent.add(m);
      return m;
    };
    const furnitureBoxes = (fl.furniture || []).map((f) => ({ x: f.x, y: f.y, w: f.w, h: f.h }));

    // walls are cut open wherever a door sits (roller door, hinged doors) so nothing overlaps the door
    const cuts = [];                                        // plan-space boxes
    const gd = fl.garage_door;
    if (gd) cuts.push({ x0: gd.x - 12, x1: gd.x + gd.w + 12, y0: gd.y, y1: gd.y + gd.h });       // whole wall thickness + margin
    for (const dr of fl.doors || []) {
      const c = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] }[dr.closed];
      const L = Math.max(dr.w, dr.h), t = 16;               // cut the whole door width and the full wall thickness (+margin)
      const ex = dr.hinge[0] + c[0] * L, ey = dr.hinge[1] + c[1] * L;
      cuts.push({ x0: Math.min(dr.hinge[0], ex) - (c[0] ? 0 : t), x1: Math.max(dr.hinge[0], ex) + (c[0] ? 0 : t),
        y0: Math.min(dr.hinge[1], ey) - (c[1] ? 0 : t), y1: Math.max(dr.hinge[1], ey) + (c[1] ? 0 : t) });
    }
    const wallHex = fl.wall_color ? parseInt(String(fl.wall_color).replace("#", ""), 16) : 0xe3e7ee;
    const wallMats = new Map();
    let brickTex = null;
    const brick = () => {
      if (brickTex) return brickTex;
      const cv = document.createElement("canvas"); cv.width = 128; cv.height = 128;
      const g2 = cv.getContext && cv.getContext("2d");
      if (!g2) return null;
      g2.fillStyle = "#6b3a22"; g2.fillRect(0, 0, 128, 128);
      for (let r = 0; r < 8; r++) for (let c = -1; c < 4; c++) {
        g2.fillStyle = ["#c8743c", "#bf6b35", "#d07f45"][(r + c + 3) % 3];
        g2.fillRect(c * 40 + (r % 2) * 20 + 1, r * 16 + 1, 38, 14);
      }
      brickTex = new THREE.CanvasTexture(cv); brickTex.wrapS = brickTex.wrapT = THREE.RepeatWrapping; brickTex.repeat.set(0.08, 0.08);
      return brickTex;
    };
    const zoneWall = (b) => (fl.wall_colors || []).find((q) => (b.x0 + b.x1) / 2 >= q.x && (b.x0 + b.x1) / 2 <= q.x + q.w && (b.y0 + b.y1) / 2 >= q.y && (b.y0 + b.y1) / 2 <= q.y + q.h);
    const wallMatFor = (b) => {                              // clipping is per material, so each wall uses the box it touches
      const zw = zoneWall(b);
      if (zw) {
        const key = "z" + zw.color + (zw.texture || "");
        if (!wallMats.has(key)) wallMats.set(key, zw.texture === "brick" && brick()
          ? new THREE.MeshLambertMaterial({ map: brick(), side: THREE.DoubleSide }) : lam(parseInt(String(zw.color).replace("#", ""), 16)));
        return wallMats.get(key);
      }
      const i = cuts.findIndex((q) => b.x0 < q.x1 && b.x1 > q.x0 && b.y0 < q.y1 && b.y1 > q.y0);
      if (i < 0) return wallMats.get(-1) || (wallMats.set(-1, lam(wallHex)), wallMats.get(-1));
      if (!wallMats.has(i)) {
        const q = cuts[i], X = fl.width / 2, Z = fl.height / 2;
        wallMats.set(i, lam(wallHex, { clipIntersection: true, clippingPlanes: [
          new THREE.Plane(new THREE.Vector3(-1, 0, 0), q.x0 - X), new THREE.Plane(new THREE.Vector3(1, 0, 0), -(q.x1 - X)),
          new THREE.Plane(new THREE.Vector3(0, 0, -1), q.y0 - Z), new THREE.Plane(new THREE.Vector3(0, 0, 1), -(q.y1 - Z))] }));
      }
      return wallMats.get(i);
    };

    const plan = new THREE.Group();
    plan.scale.set(1, -1, 1);
    plan.rotation.x = -Math.PI / 2;
    inner.add(plan);

    // floor slab, with openings where a staircase goes down
    const slabShape = new THREE.Shape();
    slabShape.moveTo(0, 0); slabShape.lineTo(fl.width, 0); slabShape.lineTo(fl.width, fl.height);
    slabShape.lineTo(0, fl.height); slabShape.lineTo(0, 0);
    for (const st of fl.stairs || []) {
      if (st.h1 >= 0) continue;
      const hole = new THREE.Path();
      hole.moveTo(st.x, st.y); hole.lineTo(st.x, st.y + st.h); hole.lineTo(st.x + st.w, st.y + st.h);
      hole.lineTo(st.x + st.w, st.y); hole.lineTo(st.x, st.y);
      slabShape.holes.push(hole);
    }
    const slab = new THREE.Mesh(new THREE.ExtrudeGeometry(slabShape, { depth: 4, bevelEnabled: false }), lam(fl.floor_color ? parseInt(String(fl.floor_color).replace("#", ""), 16) : 0x353b48));
    slab.position.z = -4;
    plan.add(slab);

    // plan geometry: walls from black fills; anything inside a modelled item / stair is replaced by the model
    const inRect = (b, r, pad = 3) => b.x0 >= r.x - pad && b.x1 <= r.x + r.w + pad && b.y0 >= r.y - pad && b.y1 <= r.y + r.h + pad;
    const covered = (b) => furnitureBoxes.some((r) => inRect(b, r)) || (fl.stairs || []).some((r) => inRect(b, r));
    const data = loader.parse(svgText);
    const walls = [];
    for (const path of data.paths) {
      const fill = (path.userData?.style?.fill || "#000").toLowerCase();
      if (fill === "none") continue;
      for (const shape of this._SVG.createShapes(path)) {
        const b = { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity };
        for (const pt of shape.getPoints()) {
          b.x0 = Math.min(b.x0, pt.x); b.x1 = Math.max(b.x1, pt.x); b.y0 = Math.min(b.y0, pt.y); b.y1 = Math.max(b.y1, pt.y);
        }
        const w = b.x1 - b.x0, h = b.y1 - b.y0;
        const isBlack = fill === "#000" || fill === "#000000" || fill === "black";
        const pts = shape.getPoints();
        let area = 0, per = 0;
        for (let i = 0; i < pts.length; i++) {
          const a = pts[i], c = pts[(i + 1) % pts.length];
          area += a.x * c.y - c.x * a.y; per += Math.hypot(c.x - a.x, c.y - a.y);
        }
        for (const hole of shape.holes) for (const p2 of [hole.getPoints()]) {
          let ha = 0;
          for (let i = 0; i < p2.length; i++) { const a = p2[i], c = p2[(i + 1) % p2.length]; ha += a.x * c.y - c.x * a.y; per += Math.hypot(c.x - a.x, c.y - a.y); }
          area = Math.abs(area) - Math.abs(ha);
        }
        const thick = per ? Math.abs(area) / per : 0;                // shoelace sum = 2A, so 2A/P ~ wall thickness
        // walls are long and thin; small black blobs (toilet bowl, faucet, drain) are plan symbols, not walls
        const isWall = isBlack && ((thick <= 11.5 && (Math.max(w, h) >= 24 || pts.length <= 8)) || w * h > 60000);   // straight stubs stay walls, round blobs do not
        if (isWall) walls.push(b);
        if (!isWall && covered(b)) continue;
        const isWhite = fill === "#fff" || fill === "#ffffff" || fill === "white";
        if (isWhite && Math.min(w, h) <= 6) continue;      // door / window rects are modelled separately
        let depth = 0.6, mat = M(0x434a58);                   // unmodelled plan detail = flat floor marking
        if (isWall) { depth = 34; mat = wallMatFor({ x0: b.x0, x1: b.x1, y0: b.y0, y1: b.y1 }); }
        else if (isBlack) { depth = 0.6; mat = M(0x2a2e36); }          // small black plan details (toilet bowl, faucet, drain, car icon) stay flat, never poles
        else if (fill === "#0d9a48") { depth = 10; mat = M(0x2f8f5b); }
        const mesh = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false }), mat);
        mesh.position.z = 0.2;
        plan.add(mesh);
      }
    }

    // which side of a box faces into the room: the side farthest from the nearest wall
    const facing = (x, y, w, h) => {
      const cx = x + w / 2, cy = y + h / 2;
      const dist = { N: Infinity, S: Infinity, W: Infinity, E: Infinity };
      for (const b of walls) {
        if (cx >= b.x0 - 4 && cx <= b.x1 + 4) {
          if (b.y1 <= cy) dist.N = Math.min(dist.N, y - b.y1); else if (b.y0 >= cy) dist.S = Math.min(dist.S, b.y0 - (y + h));
        }
        if (cy >= b.y0 - 4 && cy <= b.y1 + 4) {
          if (b.x1 <= cx) dist.W = Math.min(dist.W, x - b.x1); else if (b.x0 >= cx) dist.E = Math.min(dist.E, b.x0 - (x + w));
        }
      }
      const back = Object.entries(dist).sort((a, b2) => a[1] - b2[1])[0][0];
      return { N: "S", S: "N", W: "E", E: "W" }[back];
    };
    this._facing = facing;

    // window runs: overlapping sliding panes merged into one span; the room side is the side towards the floor's middle
    // (facing() is unreliable here because the window sits between collinear pieces of its own wall)
    const spans = [];
    for (const o of fl.openings || []) {
      if (o.kind !== "window") continue;
      const hz = o.w >= o.h, line = hz ? o.y + o.h / 2 : o.x + o.w / 2, a = hz ? o.x : o.y, b = hz ? o.x + o.w : o.y + o.h;
      const s = spans.find((q) => q.hz === hz && Math.abs(q.line - line) < 3 && a <= q.b + 2 && b >= q.a - 2);
      if (s) { s.a = Math.min(s.a, a); s.b = Math.max(s.b, b); } else spans.push({ hz, line, a, b });
    }
    for (const s of spans) {
      s.sgn = (s.line < (s.hz ? fl.height : fl.width) / 2) ? 1 : -1;            // +1: room is on the +x / +y side
      const cl = (fl.furniture || []).find((q) => q.type === "curtain_line" && (q.w >= q.h) === s.hz
        && Math.abs((s.hz ? q.y + q.h / 2 : q.x + q.w / 2) - s.line) < 15
        && (s.hz ? q.x : q.y) <= s.a + 2 && (s.hz ? q.x + q.w : q.y + q.h) >= s.b - 2);
      s.covered = !!cl;                                                       // a hand-placed full-length curtain already covers it
      const mid = (s.a + s.b) / 2, cx = s.hz ? mid : s.line + 9 * s.sgn, cy = s.hz ? s.line + 9 * s.sgn : mid;
      const inRect = (q) => cx >= q.x && cx <= q.x + q.w && cy >= q.y && cy <= q.y + q.h;
      s.curtain = !!fl.curtains && !cl && (!(fl.curtain_colors || []).length || fl.curtain_colors.some(inRect))
        && !(fl.stairs || []).some(inRect);                                   // no curtain hanging over a stairwell
      s.clear = cl ? Math.abs((s.hz ? cl.y + cl.h / 2 : cl.x + cl.w / 2) - s.line) + 2.5 : s.curtain ? 12.5 : 6.5;
    }
    this._winSpans = spans;
    // keep furniture out of the glass (and the curtain behind it) so no window is blocked, inside or out
    const WALLMOUNT = new Set(["floor_patch", "rug", "deck", "curtain_line", "computer", "printer", "lamp", "whiteboard", "ac_unit", "wall_shelf", "mirror", "tv_wall"]);
    const clearOf = (f) => {
      if (WALLMOUNT.has(f.type) || f.x == null || f.w * f.h > 40000) return f;
      let { x, y } = f; const { w, h } = f;
      for (const s of spans) {
        const lo = s.hz ? x : y, hi = s.hz ? x + w : y + h;
        if (Math.min(hi, s.b) - Math.max(lo, s.a) < 6) continue;              // corner touch only
        const near = s.hz ? y : x, far = s.hz ? y + h : x + w, inside = ((near + far) / 2 - s.line) * s.sgn >= 0;
        let d = 0;
        if (inside) { if (s.sgn > 0 && near < s.line + s.clear) d = s.line + s.clear - near; if (s.sgn < 0 && far > s.line - s.clear) d = s.line - s.clear - far; }
        else { if (s.sgn > 0 && far > s.line - 6.5) d = s.line - 6.5 - far; if (s.sgn < 0 && near < s.line + 6.5) d = s.line + 6.5 - near; }
        if (s.hz) y += d; else x += d;
      }
      return x === f.x && y === f.y ? f : { ...f, x, y };
    };

    // modelled furniture
    for (const f of fl.furniture || []) this._furniture(THREE, clearOf(f), fl, { box, cyl, M, lam, inner, edges, facing });

    // light fixtures by name: recessed / ceiling panel / wall sconce / desk lamp / bedside lamp / floor lamp
    const fixtures = {};
    const TOP = { wardrobe: 33, cabinet: 15, counter: 19.5, desk: 20, table: 20, coffee: 12, bed: 19, sofa: 21, toilet: 18,
      sink: 16.5, shower: 32, bathtub: 13, car: 21, washer: 22, appliance: 14.5, stove: 19, shelf: 29, tv_unit: 44, plant: 30,
      chair: 24, computer: 34, printer: 28 };
    const under = (x, y) => (fl.furniture || []).filter((f) => x >= f.x && x <= f.x + f.w && y >= f.y && y <= f.y + f.h)
      .reduce((m, f) => Math.max(m, TOP[f.type] ?? 10), 0);
    for (const d of fl.devices) {
      if (!(d.kind === "light" || d.light)) continue;
      let n = d.name || "";
      const top = under(d.x, d.y);
      // a floor lamp standing in furniture becomes a lamp on top of it; anything above tall furniture goes flush to the ceiling
      if (/小燈/.test(n) && top > 0) n = "床頭燈";
      if (top > 24 && !/崁燈|壁燈|樓梯燈|陽台燈|門口燈|路燈|環繞燈/.test(n)) n = "崁燈";
      const glow = new THREE.MeshLambertMaterial({ color: 0xf4f1e8, emissive: 0x000000 });
      const metal = M(0x9aa3b0);
      const g = new THREE.Group();
      g.position.set(d.x, 0, d.y);
      inner.add(g);
      const add = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); g.add(m); return m; };
      if (/崁燈/.test(n)) {
        add(new THREE.CylinderGeometry(5, 5, 1.2, 20), glow, 0, 33.5, 0);
      } else if (/客廳燈組\s*1$|客廳燈組1/.test(n)) {          // living room: flower chandelier (photo)
        const dark = M(0x2b2b2e);
        add(new THREE.CylinderGeometry(3, 3, 0.8, 16), dark, 0, 33.6, 0);                       // ceiling cup
        add(new THREE.CylinderGeometry(0.4, 0.4, 5, 6), dark, 0, 31, 0);
        add(new THREE.SphereGeometry(2, 12, 8), dark, 0, 28.3, 0);
        for (let i = 0; i < 7; i++) {
          const a = (i / 7) * Math.PI * 2, r = 9;
          const arm = add(new THREE.CylinderGeometry(0.3, 0.3, r, 6), dark, Math.cos(a) * r / 2, 28.3, Math.sin(a) * r / 2);
          arm.rotation.z = Math.PI / 2; arm.rotation.y = -a;
          add(new THREE.CylinderGeometry(0.3, 0.3, 2.5, 6), dark, Math.cos(a) * r, 29.4, Math.sin(a) * r);
          const shade = add(new THREE.SphereGeometry(2.8, 12, 8, 0, Math.PI * 2, Math.PI * 0.35, Math.PI * 0.65), glow,
            Math.cos(a) * r, 31.8, Math.sin(a) * r);                                           // frosted tulip, opening upward
          shade.rotation.x = Math.PI;
        }
      } else if (/客廳燈組/.test(n)) {                            // other living-room groups: recessed downlights
        add(new THREE.CylinderGeometry(3.5, 3.5, 1, 16), glow, 0, 33.6, 0);
      } else if (/餐廳燈組/.test(n)) {                            // dining: bar with three cylinder pendants (photo)
        add(new THREE.BoxGeometry(30, 1, 6), metal, 0, 33.5, 0);
        for (const ox of [-10, 0, 10]) {
          add(new THREE.CylinderGeometry(0.15, 0.15, 9, 4), metal, ox, 29, 0);
          add(new THREE.CylinderGeometry(3.4, 3.4, 7, 16, 1, true), glow, ox, 21.5, 0);
        }
      } else if (/書房燈/.test(n)) {                             // 5F study: black ring frame with two white cone shades
        const blk = M(0x1b1c1f);
        add(new THREE.CylinderGeometry(3.5, 3.5, 0.8, 18), blk, 0, 33.6, 0);
        for (const ox of [-2, 2]) add(new THREE.CylinderGeometry(0.15, 0.15, 8, 4), blk, ox, 29.5, 0);
        add(new THREE.TorusGeometry(5, 0.35, 6, 24), blk, 0, 25, 0).rotation.x = Math.PI / 2;
        for (const ox of [-1.8, 1.8]) add(new THREE.ConeGeometry(2.2, 6, 14, 1, true), glow, ox, 23, 0);
      } else if (/頂樓燈組/.test(n)) {                            // 5F room: slotted metal cylinder pendants
        for (const [ox, len] of [[-3, 10], [3, 14]]) {
          add(new THREE.CylinderGeometry(0.12, 0.12, len, 4), metal, ox, 34 - len / 2, 0);
          add(new THREE.CylinderGeometry(2.6, 2.6, 7, 16, 1, true), M(0xb8bcc2), ox, 34 - len - 3.5, 0);
          add(new THREE.CylinderGeometry(2.2, 2.2, 6, 12), glow, ox, 34 - len - 3.5, 0);
        }
      } else if (/燈組|頂樓燈|主燈/.test(n)) {
        add(new THREE.CylinderGeometry(0.4, 0.4, 6, 6), metal, 0, 31, 0);
        add(new THREE.CylinderGeometry(10, 12, 2.5, 24), glow, 0, 27.5, 0);
      } else if (/壁燈|樓梯燈|陽台燈|門口燈|路燈|環繞燈/.test(n)) {
        const f = facing(d.x - 2, d.y - 2, 4, 4);                // mount on the nearest wall, shine into the room
        const off = { N: [0, 4], S: [0, -4], E: [-4, 0], W: [4, 0] }[f] || [0, 0];
        add(new THREE.BoxGeometry(5, 6, 5), metal, off[0], 24, off[1]);
        add(new THREE.SphereGeometry(3.2, 14, 10), glow, off[0] * 0.2, 24, off[1] * 0.2);
      } else if (/檯燈/.test(n)) {
        const b0 = top || 0;
        add(new THREE.CylinderGeometry(3, 3.5, 1, 16), metal, 0, b0 + 0.5, 0);
        add(new THREE.CylinderGeometry(0.5, 0.5, 10, 8), metal, 0, b0 + 6, 0);
        add(new THREE.ConeGeometry(4.5, 5, 16, 1, true), glow, 2, b0 + 11, 0).rotation.z = 0.5;
      } else if (/床頭燈|小燈/.test(n)) {
        const base = /床頭/.test(n) ? (top || 15) : 0;
        add(new THREE.CylinderGeometry(3, 3.5, base ? 1 : 1.5, 16), metal, 0, base + 0.5, 0);
        add(new THREE.CylinderGeometry(0.6, 0.6, base ? 7 : 26, 8), metal, 0, base + (base ? 4 : 13), 0);
        add(new THREE.CylinderGeometry(4, 6, 6, 18, 1, true), glow, 0, base + (base ? 10 : 28), 0);
      } else {
        add(new THREE.SphereGeometry(4, 16, 12), glow, 0, 30, 0);
      }
      fixtures[d.entity] = glow;
    }

    // stairs
    const tile = fl.stair_style === "tile";                     // photos: white tiled treads, dark wood rail
    const treadA = lam(tile ? 0xeceae4 : 0xf2dcae), treadB = lam(tile ? 0xd9d5cd : 0xc99e62), railMat = new THREE.MeshBasicMaterial({ color: 0x9fe0ff, transparent: true, opacity: 0.35, depthWrite: false });
    for (const st of fl.stairs || []) {
      const n = Math.max(3, st.steps);
      const along = st.axis === "x";
      const run = along ? st.w : st.h;
      const tread = run / n;
      const down = st.h1 < 0;
      for (let i = 0; i < n; i++) {
        const top = st.h1 * (i + 1) / n;                 // up: 34/n .. 34, down: -34/n .. -34
        const k = st.dir > 0 ? i : n - 1 - i;
        const z0 = down ? -40 : 0, hh = (down ? top : top) - z0;
        const sx = along ? st.x + tread * k : st.x, sy = along ? st.y : st.y + tread * k;
        box(sx, sy, along ? tread : st.w, along ? st.h : tread, z0, hh, i % 2 ? treadB : treadA);
      }
      // direction arrows on the treads: yellow = up, blue = down (pointing up the flight)
      const tri = new THREE.Shape();
      const as = Math.min(along ? st.h : st.w, 40) * 0.45;
      tri.moveTo(as * 0.6, 0); tri.lineTo(-as * 0.4, as * 0.45); tri.lineTo(-as * 0.15, 0); tri.lineTo(-as * 0.4, -as * 0.45); tri.lineTo(as * 0.6, 0);
      const arrowMat = new THREE.MeshBasicMaterial({ color: down ? 0x4fc3f7 : 0xffb900, side: THREE.DoubleSide });
      const upDir = down ? -st.dir : st.dir;                // walking-up direction along the run axis
      for (const fr of [0.25, 0.5, 0.75]) {
        const i = Math.min(n - 1, Math.floor(fr * n));
        const k = st.dir > 0 ? i : n - 1 - i;
        const top = st.h1 * (i + 1) / n;
        const a = new THREE.Mesh(new THREE.ShapeGeometry(tri), arrowMat);
        a.rotation.x = -Math.PI / 2;
        a.rotation.z = along ? (upDir > 0 ? 0 : Math.PI) : (upDir > 0 ? -Math.PI / 2 : Math.PI / 2);
        a.position.set(along ? st.x + tread * (k + 0.5) : st.x + st.w / 2, top + 0.25, along ? st.y + st.h / 2 : st.y + tread * (k + 0.5));
        inner.add(a);
      }
      // side rails (glass) along both long edges, rising with the flight
      const railH = 10;
      for (const side of [0, 1]) {
        const g = new THREE.Group();
        const len = run, w = 1.5;
        const rail = new THREE.Mesh(tile ? new THREE.BoxGeometry(along ? len : 1.6, 1.4, along ? 1.6 : len)
          : new THREE.BoxGeometry(along ? len : w, railH, along ? w : len), tile ? M(0x3b2416) : railMat);
        const slope = Math.atan2(st.h1, run) * (st.dir > 0 ? 1 : -1);
        if (along) rail.rotation.z = slope; else rail.rotation.x = -slope;
        g.add(rail);
        g.position.set(along ? st.x + st.w / 2 : (side ? st.x + st.w : st.x),
          st.h1 / 2 + railH / 2 + 2, along ? (side ? st.y + st.h : st.y) : st.y + st.h / 2);
        inner.add(g);
      }
      if (down) {                                         // guard rail around the opening, open at the entry end
        const entryAtMax = st.dir < 0;                    // the top step sits at the arrow end
        const segs = along
          ? [[st.x, st.y, st.w, 1.5], [st.x, st.y + st.h - 1.5, st.w, 1.5], [entryAtMax ? st.x : st.x + st.w - 1.5, st.y, 1.5, st.h]]
          : [[st.x, st.y, 1.5, st.h], [st.x + st.w - 1.5, st.y, 1.5, st.h], [st.x, entryAtMax ? st.y : st.y + st.h - 1.5, st.w, 1.5]];
        for (const s of segs) {
          if (tile) {                                       // white half wall + dark wood cap rail (photo 10)
            box(s[0], s[1], s[2], s[3], 0, 13, M(0xf1ede4), inner, false);
            box(s[0] - 0.5, s[1] - 0.5, s[2] + 1, s[3] + 1, 13, 1.6, M(0x3b2416), inner, false);
          } else box(s[0], s[1], s[2], s[3], 0, 14, railMat, inner, false);
        }
        if (tile) {                                         // newel post with a ball top at the stair head
          const nx = along ? (entryAtMax ? st.x + st.w : st.x) : st.x + st.w, nz = along ? st.y + st.h : (entryAtMax ? st.y + st.h : st.y);
          box(nx - 2, nz - 2, 4, 4, 0, 16, M(0x3b2416));
          cyl(nx, nz, 2.4, 2.4, 16, 2.6, M(0x3b2416));
        }
      }
    }

    // windows: bright glass band with a white frame; doors: wooden leaf
    let lattice = null;
    const glass = new THREE.MeshBasicMaterial({ color: 0x6fd3ff, transparent: true, opacity: 0.6, depthWrite: false });
    const frameMat = new THREE.LineBasicMaterial({ color: fl.window_frame ? parseInt(String(fl.window_frame).replace("#", ""), 16) : 0xffffff });
    for (const o of fl.openings || []) {
      const win = o.kind === "window";
      const horizontal = o.w >= o.h;
      const th = win ? 11 : 6;                                              // glass flush with the ~10-wide walls
      const gw = horizontal ? o.w : th, gdp = horizontal ? th : o.h;
      const hgt = win ? 24 : 30;
      const grille = win && (fl.window_grille || []).find((q) => o.x + o.w / 2 >= q.x && o.x + o.w / 2 <= q.x + q.w && o.y + o.h / 2 >= q.y && o.y + o.h / 2 <= q.y + q.h);
      if (grille && !lattice) {
        const cv = document.createElement("canvas"); cv.width = 64; cv.height = 64;
        const g2 = cv.getContext && cv.getContext("2d");
        if (g2) {
          g2.fillStyle = "#16303a"; g2.fillRect(0, 0, 64, 64);
          g2.strokeStyle = "#0b1114"; g2.lineWidth = 3;
          for (let k = -64; k < 128; k += 12) { g2.beginPath(); g2.moveTo(k, 0); g2.lineTo(k + 64, 64); g2.stroke(); g2.beginPath(); g2.moveTo(k + 64, 0); g2.lineTo(k, 64); g2.stroke(); }
          lattice = new THREE.CanvasTexture(cv); lattice.wrapS = lattice.wrapT = THREE.RepeatWrapping;
        }
      }
      const gmat = grille && lattice ? (() => { const t = lattice.clone(); t.needsUpdate = true; t.repeat.set(Math.max(o.w, o.h) / 16, 2); return new THREE.MeshBasicMaterial({ map: t }); })() : glass;
      const m = box(o.x + o.w / 2 - gw / 2, o.y + o.h / 2 - gdp / 2, gw, gdp, win ? 7 : 0, hgt, win ? gmat : M(0x9a6b43), inner, false);
      const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry), win ? frameMat : edgeMat);
      e.position.copy(m.position);
      inner.add(e);
    }

    // curtains (top floor): pleated fabric on the room side of every window
    if (fl.curtains) {
      const clothFor = (px, py) => { const c = (fl.curtain_colors || []).find((q) => px >= q.x && px <= q.x + q.w && py >= q.y && py <= q.y + q.h); return M(c ? parseInt(String(c.color).replace("#", ""), 16) : 0xd9ccb6); };
      for (const s of spans) {
        if (!s.curtain) continue;
        const horizontal = s.hz, len = s.b - s.a, mid = (s.a + s.b) / 2;
        const off = horizontal ? [0, 9 * s.sgn] : [9 * s.sgn, 0];             // always on the room side of the glass
        const cloth = horizontal ? clothFor(mid, s.line) : clothFor(s.line, mid);
        const folds = Math.max(3, Math.round(len / 7));
        for (let i = 0; i < folds; i++) {
          const t = (i + 0.5) / folds, z = i % 2 ? 1.6 : -1.6;
          const px = horizontal ? s.a + len * t : s.line + z, py = horizontal ? s.line + z : s.a + len * t;
          const m = new THREE.Mesh(new THREE.BoxGeometry(horizontal ? len / folds + 0.6 : 1.4, 29, horizontal ? 1.4 : len / folds + 0.6), cloth);
          m.position.set(px + off[0], 4 + 14.5, py + off[1]);
          inner.add(m);
        }
        box((horizontal ? mid : s.line) + off[0] - (horizontal ? len / 2 : 0.6), (horizontal ? s.line : mid) + off[1] - (horizontal ? 0.6 : len / 2),
          horizontal ? len : 1.2, horizontal ? 1.2 : len, 33.5, 1, M(0x8c96a4), inner, false);     // rail
      }
    }

    // hinged doors (e.g. 2F front door): frame + leaf + handle, leaf swings with the lock/cover state
    const hinged = {};
    for (const dr of fl.doors || []) {
      const vec = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] };
      const c = vec[dr.closed], o = vec[dr.open];
      const len = Math.hypot(dr.w >= dr.h ? dr.w : dr.h, 0);
      const pivot = new THREE.Group();
      pivot.position.set(dr.hinge[0], 0, dr.hinge[1]);
      inner.add(pivot);
      const leaf = new THREE.Group();
      pivot.add(leaf);
      const along = c[0] !== 0;                                  // leaf runs along x or z
      const L = Math.max(dr.w, dr.h);
      // photo: active leaf = wood outside / dark charcoal steel inside with a smart lock,
      // next to it a fixed side-light with tall wrought-iron decorative glass in a dark wood frame
      const La = L * 0.6, Ls = L - La;
      const wood = lam(0x8a4f2a), steel = new THREE.MeshStandardMaterial({ color: 0x3a3d42, roughness: 0.5, metalness: 0.3 });
      const inside = dr.inside ? vec[dr.inside] : [-o[0], -o[1]];   // room side
      const faces = wood;                                        // photo: the swinging leaf is wood on both faces
      if (dr.outer) {                                            // charcoal outer (security) door in the opening, seen when open
        const ox = dr.hinge[0] - inside[0] * 3 + c[0] * La / 2, oz = dr.hinge[1] - inside[1] * 3 + c[1] * La / 2;
        const od = new THREE.Mesh(new THREE.BoxGeometry(along ? La : 2, 30, along ? 2 : La), steel);
        od.position.set(ox, 15, oz); inner.add(od);
      }
      const door = new THREE.Mesh(new THREE.BoxGeometry(along ? La : 4, 30, along ? 4 : La), faces);
      door.position.set(c[0] * La / 2, 15, c[1] * La / 2);
      leaf.add(door); edges(door, leaf);
      const lock = new THREE.Mesh(new THREE.BoxGeometry(along ? 2.5 : 1.2, 7, along ? 1.2 : 2.5), M(0x111214));   // smart lock (room side)
      lock.position.set(c[0] * (La - 5) + inside[0] * 2.6, 15, c[1] * (La - 5) + inside[1] * 2.6);
      leaf.add(lock);
      const knob = new THREE.Mesh(new THREE.BoxGeometry(along ? 4 : 1, 1, along ? 1 : 4), M(0xc9a14a));          // lever handle
      knob.position.set(c[0] * (La - 6) - inside[0] * 2.6, 13, c[1] * (La - 6) - inside[1] * 2.6);
      leaf.add(knob);
      // fixed side-light: dark wood frame + decorative glass (scroll pattern texture)
      const cv = document.createElement("canvas"); cv.width = 64; cv.height = 256;
      const cx2 = cv.getContext("2d");
      if (cx2) {
        cx2.fillStyle = "#1f2a33"; cx2.fillRect(0, 0, 64, 256);
        cx2.strokeStyle = "#c9a35a"; cx2.lineWidth = 2;
        for (let yy = 16; yy < 256; yy += 40) {
          cx2.beginPath(); cx2.arc(20, yy, 10, 0.2, Math.PI * 1.6); cx2.stroke();
          cx2.beginPath(); cx2.arc(44, yy + 20, 10, Math.PI, Math.PI * 2.6); cx2.stroke();
        }
        cx2.beginPath(); cx2.moveTo(32, 0); cx2.lineTo(32, 256); cx2.stroke();
      }
      const glassTex = cx2 ? new THREE.CanvasTexture(cv) : null;
      const sx = dr.hinge[0] + c[0] * (La + Ls / 2), sz = dr.hinge[1] + c[1] * (La + Ls / 2);
      const sframe = new THREE.Mesh(new THREE.BoxGeometry(along ? Ls : 4, 30, along ? 4 : Ls), M(0x4a2e1c));
      sframe.position.set(sx, 15, sz); inner.add(sframe);
      for (const side of [1, -1]) {                               // glass visible from both sides
        const gp = new THREE.Mesh(new THREE.PlaneGeometry(Ls * 0.55, 24),
          new THREE.MeshBasicMaterial({ map: glassTex, color: glassTex ? 0xffffff : 0x2a3540 }));
        gp.position.set(sx + (along ? 0 : side * 2.1), 16, sz + (along ? side * 2.1 : 0));
        gp.rotation.y = along ? (side > 0 ? 0 : Math.PI) : (side > 0 ? Math.PI / 2 : -Math.PI / 2);
        inner.add(gp);
      }
      const post = (px, pz) => { const m = new THREE.Mesh(new THREE.BoxGeometry(6, 32, 6), M(0x4e3420)); m.position.set(px, 16, pz); inner.add(m); };
      post(dr.hinge[0], dr.hinge[1]); post(dr.hinge[0] + c[0] * L, dr.hinge[1] + c[1] * L);
      const lintel = new THREE.Mesh(new THREE.BoxGeometry(along ? L : 6, 4, along ? 6 : L), M(0x4a2e1c));
      lintel.position.set(dr.hinge[0] + c[0] * L / 2, 33, dr.hinge[1] + c[1] * L / 2); inner.add(lintel);
      const theta = Math.atan2(c[1] * o[0] - c[0] * o[1], c[0] * o[0] + c[1] * o[1]);
      const arc = new THREE.Mesh(new THREE.RingGeometry(La - 1, La, 40, 1, 0, Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false }));
      arc.rotation.x = -Math.PI / 2;
      // ring sector from the closed direction c to the open direction o (angle measured in the plan x/z plane)
      arc.rotation.z = 0;
      const a0 = Math.atan2(-c[1], c[0]), a1 = Math.atan2(-o[1], o[0]);
      const start = ((a1 - a0 + Math.PI * 3) % (Math.PI * 2)) - Math.PI < 0 ? a1 : a0;
      arc.geometry.dispose();
      arc.geometry = new THREE.RingGeometry(La - 1, La, 40, 1, start, Math.PI / 2);
      arc.position.set(dr.hinge[0], 0.9, dr.hinge[1]);
      inner.add(arc);
      hinged[dr.entity] = { leaf, theta, cur: 0, target: 0, when: dr.open_when || "on" };
    }

    // roller garage door: follows the cover state (closed = full height, open = rolled up)
    const doors = {};
    const cover = fl.devices.find((d) => d.kind === "cover");
    if (gd && cover) {
      const along = gd.h >= gd.w;
      const door = new THREE.Mesh(new THREE.BoxGeometry(along ? 5 : gd.w, 34, along ? gd.h : 5), lam(0xb6bfcc));
      door.geometry.translate(0, -17, 0);
      door.position.set(gd.x + gd.w / 2, 34, gd.y + gd.h / 2);
      inner.add(door);
      edges(door);
      for (let i = 1; i < 8; i++) {                         // slats
        const s = box(gd.x + gd.w / 2 - 3, gd.y, 6, gd.h, 0, 0.5, M(0x8c96a4), door, false);
        s.position.set(0, -i * 4.2, 0);
      }
      box(gd.x + gd.w / 2 - 6, gd.y, 12, gd.h, 32, 5, M(0x5d6572));    // roller housing
      doors[cover.entity] = door;
    }

    // cameras and motion sensors: device model + coverage fan in the direction of the plan arrow
    const sensors = {};
    for (const d of fl.devices) {
      if (d.kind !== "camera" && d.kind !== "motion") continue;
      let arrowMat = null;
      const g = new THREE.Group();
      g.position.set(d.x, d.kind === "camera" ? 30 : 26, d.y);
      inner.add(g);
      const yaw = (d.yaw ?? 90) * Math.PI / 180;
      if (d.kind === "camera") {
        const body = new THREE.Mesh(new THREE.BoxGeometry(12, 6, 6), lam(0xf4f6f8));
        body.position.x = 4;
        const lens = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 2, 16), lam(0x111418));
        lens.rotation.z = Math.PI / 2; lens.position.x = 11;
        const arm = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 6, 8), lam(0x9aa3b0));
        arm.position.set(-2, 3, 0);
        const head = new THREE.Group();
        head.add(body, lens, arm);
        head.rotation.y = -yaw;
        g.add(head);
      } else {
        const dome = new THREE.Mesh(new THREE.SphereGeometry(4, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), lam(0xf4f6f8));
        dome.rotation.x = Math.PI;
        g.add(dome);
        if (d.yaw != null) {
          const arrow = new THREE.Mesh(new THREE.ConeGeometry(2.6, 8, 12), (arrowMat = lam(0x8a8f98)));
          arrow.rotation.z = -Math.PI / 2;
          const holder = new THREE.Group();
          holder.add(arrow); arrow.position.x = 7;
          holder.rotation.y = -yaw;
          g.add(holder);
        }
      }
      let fan = null;
      if (d.yaw != null) {
        const fov = (d.kind === "camera" ? d.fov || 100 : 70) * Math.PI / 180;
        const radius = d.kind === "camera" ? 150 : 80;
        fan = new THREE.Mesh(new THREE.CircleGeometry(radius, 32, -(yaw + fov / 2), fov),
          new THREE.MeshBasicMaterial({ color: d.kind === "camera" ? 0x4fc3f7 : 0x8a8f98, transparent: true,
            opacity: d.kind === "camera" ? 0.16 : 0.1, depthWrite: false, side: THREE.DoubleSide }));
        fan.rotation.x = -Math.PI / 2;
        fan.position.set(d.x, 1.2, d.y);
        inner.add(fan);
      }
      sensors[d.entity] = { g, fan, d, arrowMat };
    }

    // EV charger (wall box with status LED + coiled cable), mounted on the nearest wall
    const chargers = {};
    for (const d of fl.devices) {
      if (d.kind !== "charger") continue;
      const f = facing(d.x - 3, d.y - 3, 6, 6);
      const rot = { S: 0, N: Math.PI, E: Math.PI / 2, W: -Math.PI / 2 }[f] ?? 0;
      const g = new THREE.Group();
      g.position.set(d.x, 0, d.y);
      g.rotation.y = rot;
      inner.add(g);
      const body = new THREE.Mesh(new THREE.BoxGeometry(11, 17, 4), M(0xeceff2));
      body.position.set(0, 18, 0); g.add(body); edges(body, g);
      const glassM = new THREE.Mesh(new THREE.BoxGeometry(9, 15, 0.6), M(0x2a2f36));
      glassM.position.set(0, 18, 2.2); g.add(glassM);
      const led = new THREE.MeshBasicMaterial({ color: 0x4caf50 });
      const bar = new THREE.Mesh(new THREE.BoxGeometry(1.2, 9, 0.5), led);
      bar.position.set(0, 19, 2.6); g.add(bar);
      const coil = new THREE.Mesh(new THREE.TorusGeometry(4.5, 0.7, 8, 24), M(0x1b1d22));
      coil.position.set(0, 7, 2.5); g.add(coil);
      const plug = new THREE.Mesh(new THREE.BoxGeometry(2.5, 4, 2.5), M(0x1b1d22));
      plug.position.set(5, 13, 2.6); g.add(plug);
      // cable to the car (Tesla charge port = left rear light) or hanging from the box when unplugged
      const cars = (fl.furniture || []).filter((c) => c.type === "car");
      let car = cars.sort((a, b) => Math.hypot(a.x + a.w / 2 - d.x, a.y + a.h / 2 - d.y) - Math.hypot(b.x + b.w / 2 - d.x, b.y + b.h / 2 - d.y))[0];
      const inward = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] }[f] || [0, -1];   // from the wall into the room (same side the box faces)
      const start = new THREE.Vector3(d.x + inward[0] * 6 + (inward[1] ? 5 : 0), 13, d.y + inward[1] * 6 + (inward[0] ? 5 : 0));
      let plugged = null;
      if (car) {
        const alongX = (car.axis || "x") === "x";
        const L = (alongX ? car.w : car.h) * 0.92, Wd = (alongX ? car.h : car.w) * 0.62;
        const fv = { E: [1, 0], W: [-1, 0], S: [0, 1], N: [0, -1] }[car.front || (alongX ? "E" : "S")];
        const rv = [-fv[1], fv[0]];                          // car's right-hand side (facing along fv)
        const cxm = car.x + car.w / 2, cym = car.y + car.h / 2;
        const P = (a, b, y) => new THREE.Vector3(cxm + fv[0] * a + rv[0] * b, y, cym + fv[1] * a + rv[1] * b);
        // charge port: front-right of the car; the cable goes around the front end along the near (left) side
        const port = P(L * 0.36, Wd * 0.47, 10);
        const pts = [start, new THREE.Vector3(start.x + inward[0] * 12, 2, start.z + inward[1] * 12),
          P(L * 0.05, -(Wd / 2 + 16), 1.8), P(L * 0.5 + 16, -(Wd / 2 + 14), 1.8), P(L * 0.5 + 18, Wd * 0.25, 1.8),
          P(L * 0.36 + 8, Wd * 0.58, 3), port];
        plugged = new THREE.CatmullRomCurve3(pts, false, "catmullrom", 0.4);
      }
      const hang = new THREE.CatmullRomCurve3([start, new THREE.Vector3(start.x + inward[0] * 6, 7, start.z + inward[1] * 6),
        new THREE.Vector3(start.x + inward[0] * 14, 2, start.z + inward[1] * 14 + 6),
        new THREE.Vector3(start.x + inward[0] * 24, 1.6, start.z + inward[1] * 24 + 10)]);
      const cableMat = new THREE.MeshBasicMaterial({ color: 0x777c85 });
      const tube = (curve) => { const m = new THREE.Mesh(new THREE.TubeGeometry(curve, 64, 1.3, 8, false), cableMat); inner.add(m); return m; };
      const cabPlug = plugged ? tube(plugged) : null, cabHang = tube(hang);
      const pulseMat = new THREE.MeshBasicMaterial({ color: 0xbfe3ff });
      const pulses = [];
      if (plugged) for (let i = 0; i < 6; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(2.3, 10, 8), pulseMat); m.visible = false; inner.add(m); pulses.push(m); }
      const portDot = plugged ? new THREE.Mesh(new THREE.SphereGeometry(2.6, 10, 8), cableMat) : null;
      if (portDot) { portDot.position.copy(plugged.getPoint(1)); inner.add(portDot); }
      chargers[d.entity] = { led, cableMat, pulseMat, cabPlug, cabHang, pulses, curve: plugged, portDot };
    }

    // UniFi network gear, modelled by product name: UDM SE (main gateway, 1U box), U6-Pro/Lite (ceiling disc),
    // U6-IW (in-wall plate), U6 Extender (plug-in), U6 Mesh (small tower); status LED + wifi rings follow *_state
    const aps = {};
    for (const d of fl.devices) {
      if (d.kind !== "ap") continue;
      const id = d.entity, white = M(0xf4f5f7);
      const led = new THREE.MeshBasicMaterial({ color: 0x3d9bff });
      const g = new THREE.Group();
      g.position.set(d.x, 0, d.y);
      inner.add(g);
      let top = 20;
      if (/switch/.test(id)) {                                                 // Switch Lite 8 PoE: small white 8-port box on a shelf
        g.position.y = 6.5;                                                  // sits on the 3F desk (top at 20) rather than a shelf
        const sh = new THREE.Mesh(new THREE.BoxGeometry(20, 1, 12), M(0x6b4a30)); sh.position.set(0, 13.5, 0); g.add(sh);
        const body = new THREE.Mesh(new THREE.BoxGeometry(18, 2.4, 9), white); body.position.set(0, 15.2, 0); g.add(body);
        const ports = new THREE.Mesh(new THREE.PlaneGeometry(14, 0.9), M(0x2a2e35)); ports.position.set(0, 15.2, 4.55); g.add(ports);
        const bar = new THREE.Mesh(new THREE.BoxGeometry(18, 0.3, 0.3), led); bar.position.set(0, 16.5, 4.4); g.add(bar);
        top = 17;
      } else if (/udm/.test(id)) {                                                    // UDM SE on a shelf: silver 1U chassis, touch display, port row
        const sh = new THREE.Mesh(new THREE.BoxGeometry(26, 1, 14), M(0x6b4a30)); sh.position.set(0, 13.5, 0); g.add(sh);
        const body = new THREE.Mesh(new THREE.BoxGeometry(24, 2.6, 12), M(0xd6d9de)); body.position.set(0, 15.3, 0); g.add(body);
        const scr = new THREE.Mesh(new THREE.PlaneGeometry(4, 1.6), new THREE.MeshBasicMaterial({ color: 0x5ab0ff })); scr.position.set(-8, 15.3, 6.05); g.add(scr);
        const ports = new THREE.Mesh(new THREE.PlaneGeometry(13, 1), M(0x2a2e35)); ports.position.set(3, 15.3, 6.05); g.add(ports);
        const bar = new THREE.Mesh(new THREE.BoxGeometry(24, 0.3, 0.3), led); bar.position.set(0, 16.7, 6); g.add(bar);
        top = 17;
      } else if (/iw/.test(id) || /extender/.test(id)) {                      // wall unit facing into the room
        const f = facing(d.x - 3, d.y - 3, 6, 6);
        g.rotation.y = { S: 0, N: Math.PI, E: Math.PI / 2, W: -Math.PI / 2 }[f] ?? 0;
        const iw = /iw/.test(id), z0 = iw ? 9 : 4;
        const body = new THREE.Mesh(new THREE.BoxGeometry(iw ? 6 : 5, iw ? 9 : 7, iw ? 1.6 : 3), white); body.position.set(0, z0 + (iw ? 4.5 : 3.5), 1); g.add(body);
        const dot = new THREE.Mesh(new THREE.BoxGeometry(iw ? 3 : 1.2, 0.5, 0.3), led); dot.position.set(0, z0 + (iw ? 8 : 6), iw ? 1.9 : 2.6); g.add(dot);
        top = z0 + 10;
      } else if (/mesh/.test(id)) {                                            // U6 Mesh: slim white tower on a stand
        const body = new THREE.Mesh(new THREE.CylinderGeometry(1.8, 1.8, 9, 16), white); body.position.set(0, 4.5 + 13, 0); g.add(body);
        const base = new THREE.Mesh(new THREE.CylinderGeometry(2.6, 2.6, 0.6, 16), white); base.position.set(0, 13.3, 0); g.add(base);
        const ring = new THREE.Mesh(new THREE.TorusGeometry(1.85, 0.25, 6, 20), led); ring.rotation.x = Math.PI / 2; ring.position.set(0, 21.5, 0); g.add(ring);
        const post = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 13, 8), M(0x9aa0a8)); post.position.set(0, 6.5, 0); g.add(post);
        top = 23;
      } else {                                                                 // ceiling disc (U6-Pro larger than U6-Lite)
        const r = /pro/.test(id) ? 6.5 : 5;
        const disc = new THREE.Mesh(new THREE.CylinderGeometry(r, r * 0.92, 1.4, 28), white); disc.position.set(0, 33.2, 0); g.add(disc);
        const ring = new THREE.Mesh(new THREE.TorusGeometry(r * 0.55, 0.3, 6, 24), led); ring.rotation.x = Math.PI / 2; ring.position.set(0, 32.45, 0); g.add(ring);
        top = 31;
      }
      // wifi symbol: three arcs above the unit, shown while connected
      const wifi = new THREE.Group();
      const wmat = new THREE.MeshBasicMaterial({ color: 0x3d9bff, transparent: true, opacity: 0.9, depthWrite: false });
      for (const [k, rad] of [[0, 2], [1, 4], [2, 6]]) {
        const arc = new THREE.Mesh(new THREE.TorusGeometry(rad, 0.45, 6, 20, Math.PI / 2), wmat);
        arc.rotation.z = Math.PI / 4; arc.userData.k = k; wifi.add(arc);
      }
      const dotw = new THREE.Mesh(new THREE.SphereGeometry(0.8, 10, 8), wmat); wifi.add(dotw);
      wifi.position.set(0, /udm|mesh|switch/.test(id) ? top + 3 : top - (/iw|extender/.test(id) ? -2 : 8), 0);
      if (!/udm|mesh|switch/.test(id) && !/iw|extender/.test(id)) wifi.rotation.z = Math.PI;   // under a ceiling disc: arcs point down
      g.add(wifi);
      aps[id] = { led, wifi, wmat };
    }

    // light glow on the floor (colour + brightness follow the light)
    const decals = {};
    for (const d of fl.devices) {
      if (d.kind === "light" || d.light) {
        const m = new THREE.Mesh(
          new THREE.PlaneGeometry(130, 130),
          new THREE.MeshBasicMaterial({ map: this._glowTex, transparent: true, depthWrite: false,
            blending: THREE.AdditiveBlending, color: 0xffd9a0, opacity: 0 }));
        m.rotation.x = -Math.PI / 2;
        m.position.set(d.x, 4.5, d.y);
        inner.add(m);
        decals[d.entity] = m;
      }
    }
    // everything except the plan shell (slab, walls) and the light glow is "detail" and is hidden in the whole-house view
    const keep = new Set([plan, ...Object.values(decals)]);
    const detail = inner.children.filter((c) => !keep.has(c));
    return { group, decals, doors, hinged, sensors, fixtures, chargers, aps, detail, fl, inner };
  }

  // parametric furniture in plan coordinates (x/y = north-west corner, w along x, h along y)
  _furniture(THREE, f, fl, { box, cyl, M, lam, inner, edges, facing }) {
    const { x, y, w, h } = f;
    const onDesk = (fl.furniture || []).some((o) => ["desk", "table"].includes(o.type) && o !== f &&
      x >= o.x - 2 && y >= o.y - 2 && x + w <= o.x + o.w + 2 && y + h <= o.y + o.h + 2);
    const z = onDesk ? 19 : 0;
    const wood = M(0xa47b52), woodDark = M(0x6e4f33), white = M(0xf3f5f8), fabric = M(0x8d97a8);
    const side = (dir) => ({ N: [x, y, w, 0], S: [x, y + h, w, 0], W: [x, y, 0, h], E: [x + w, y, 0, h] }[dir]);
    const legs = (top, t = 3) => {
      for (const [lx, ly] of [[x, y], [x + w - t, y], [x, y + h - t], [x + w - t, y + h - t]]) box(lx, ly, t, t, z, top, woodDark, inner, false);
    };
    switch (f.type) {
      case "bed": {
        const head = f.head || "N", vert = head === "N" || head === "S";
        box(x, y, w, h, 0, 8, woodDark);                                       // frame
        box(x + 2, y + 2, w - 4, h - 4, 8, 7, white);                           // mattress
        const L = vert ? h : w, W = vert ? w : h;
        const blanket = L * 0.62;                                              // blanket at the foot end
        if (head === "N") box(x + 1, y + h - blanket, w - 2, blanket - 1, 15, 1.6, M(0x6f8fc4));
        if (head === "S") box(x + 1, y + 1, w - 2, blanket - 1, 15, 1.6, M(0x6f8fc4));
        if (head === "W") box(x + w - blanket, y + 1, blanket - 1, h - 2, 15, 1.6, M(0x6f8fc4));
        if (head === "E") box(x + 1, y + 1, blanket - 1, h - 2, 15, 1.6, M(0x6f8fc4));
        const fold = 6;                                                        // folded duvet edge
        if (head === "N") box(x + 1, y + h - blanket, w - 2, fold, 16.6, 1.4, M(0xe9eef7));
        if (head === "S") box(x + 1, y + blanket - fold, w - 2, fold, 16.6, 1.4, M(0xe9eef7));
        if (head === "W") box(x + w - blanket, y + 1, fold, h - 2, 16.6, 1.4, M(0xe9eef7));
        if (head === "E") box(x + blanket - fold, y + 1, fold, h - 2, 16.6, 1.4, M(0xe9eef7));
        const pw = (W - 12) / 2, pd = Math.min(28, L * 0.14);
        for (const i of [0, 1]) {                                             // pillows
          const off = 4 + i * (pw + 4);
          if (head === "N") box(x + off, y + 5, pw, pd, 15, 4, white);
          if (head === "S") box(x + off, y + h - 5 - pd, pw, pd, 15, 4, white);
          if (head === "W") box(x + 5, y + off, pd, pw, 15, 4, white);
          if (head === "E") box(x + w - 5 - pd, y + off, pd, pw, 15, 4, white);
        }
        const [hx, hy, hw, hh] = side(head);                                   // headboard
        box(head === "E" ? hx - 5 : hx, head === "S" ? hy - 5 : hy, hw || 5, hh || 5, 0, 26, woodDark);
        break;
      }
      case "desk": case "table": case "coffee": {
        const top = f.type === "coffee" ? 10 : 18;
        if (f.round) {
          cyl(x + w / 2, y + h / 2, w / 2, h / 2, top, 2, wood);
          cyl(x + w / 2, y + h / 2, 2, 2, 0, top, woodDark);
        } else if (f.style === "marble") {                          // solid wood box base + beige marble top (photo)
          box(x + 3, y + 3, w - 6, h - 6, 0, top, M(0x5a3a26));
          box(x, y, w, h, top, 2.2, M(0xe9dcc6));
        } else if (f.style === "light") {                           // light oak desk top on dark legs (5F photos)
          box(x, y, w, h, top, 2, M(0xc79a63));
          legs(top);
        } else if (f.style === "wood") {
          box(x, y, w, h, top, 2, M(0x8a5530));
          for (const [lx, ly] of [[x + 2, y + 2], [x + w - 6, y + 2], [x + 2, y + h - 6], [x + w - 6, y + h - 6]]) box(lx, ly, 4, 4, 0, top, M(0x6b3f22), inner, false);
        } else {
          box(x, y, w, h, top, 2, wood);
          legs(top);
        }
        break;
      }
      case "chair": {
        const face = f.face || "N";
        if (f.style === "office") {                                 // black office chair on a 5-star base
          const blk = M(0x1e1f22);
          cyl(x + w / 2, y + h / 2, w / 2 - 2, h / 2 - 2, 10, 2.5, blk);
          cyl(x + w / 2, y + h / 2, 0.8, 0.8, 2, 8, M(0x6b6f76));
          cyl(x + w / 2, y + h / 2, w / 2 - 4, h / 2 - 4, 0.6, 1.4, blk);
          const bk = { N: [x + 4, y + h - 4, w - 8, 2.5], S: [x + 4, y + 1.5, w - 8, 2.5], E: [x + 1.5, y + 4, 2.5, h - 8], W: [x + w - 4, y + 4, 2.5, h - 8] }[face];
          box(bk[0], bk[1], bk[2], bk[3], 12.5, 12, blk);
          break;
        }
        if (f.style === "wood") {                                   // wooden dining chair with slatted back (photo)
          const wd = M(0x8a5530);
          box(x + 1, y + 1, w - 2, h - 2, 9, 2, wd);
          for (const [lx, ly] of [[x + 2, y + 2], [x + w - 4, y + 2], [x + 2, y + h - 4], [x + w - 4, y + h - 4]]) box(lx, ly, 2, 2, 0, 9, wd, inner, false);
          const bx = { N: [x + 1, y + h - 3, w - 2, 2], S: [x + 1, y + 1, w - 2, 2], E: [x + 1, y + 1, 2, h - 2], W: [x + w - 3, y + 1, 2, h - 2] }[face];
          for (const hz of [14, 18, 22]) box(bx[0], bx[1], bx[2], bx[3], hz, 1.6, wd, inner, false);
          for (const k of [0, 1]) {
            const px = face === "N" || face === "S" ? (k ? bx[0] + bx[2] - 2 : bx[0]) : bx[0];
            const py = face === "E" || face === "W" ? (k ? bx[1] + bx[3] - 2 : bx[1]) : bx[1];
            box(px, py, 2, 2, 11, 13, wd, inner, false);
          }
          break;
        }
        box(x + 2, y + 2, w - 4, h - 4, 9, 3, fabric);
        for (const [lx, ly] of [[x + 3, y + 3], [x + w - 5, y + 3], [x + 3, y + h - 5], [x + w - 5, y + h - 5]]) box(lx, ly, 2, 2, 0, 9, woodDark, inner, false);
        const t = 3;
        const back = { N: [x + 2, y + h - t - 1, w - 4, t], S: [x + 2, y + 1, w - 4, t], E: [x + 1, y + 2, t, h - 4], W: [x + w - t - 1, y + 2, t, h - 4] }[face];
        box(back[0], back[1], back[2], back[3], 12, 12, fabric);
        break;
      }
      case "sofa": {
        const b = f.back || "N", t = 10;
        const beige = f.style === "beige";
        const base = beige ? M(0x5a3a26) : fabric, cush = beige ? M(0xe0d4bd) : M(0xaab3c2);
        box(x, y, w, h, 0, 9, base);                                            // wooden base (photo: dark wood)
        box(x + 2, y + 2, w - 4, h - 4, 9, 3, cush);                            // seat cushions
        const bk = { N: [x, y, w, t], S: [x, y + h - t, w, t], W: [x, y, t, h], E: [x + w - t, y, t, h] }[b];
        box(bk[0], bk[1], bk[2], bk[3], 0, 12, base);
        box(bk[0], bk[1], bk[2], bk[3], 12, 9, cush);                           // back cushions
        const arms = b === "N" || b === "S" ? [[x, y, 7, h], [x + w - 7, y, 7, h]] : [[x, y, w, 7], [x, y + h - 7, w, 7]];
        for (const a of arms) box(a[0], a[1], a[2], a[3], 0, 14, base);
        break;
      }
      case "wardrobe": case "cabinet": case "counter": {
        const H = f.height || (f.type === "wardrobe" ? 33 : f.type === "counter" ? 18 : 15);
        const long = Math.max(w, h), along = w >= h;
        const n = Math.max(1, Math.round(long / 48));
        for (let i = 0; i < n; i++) {                                           // doors / modules
          const s = long / n;
          box(along ? x + i * s + 0.4 : x, along ? y : y + i * s + 0.4, along ? s - 0.8 : w, along ? h : s - 0.8, 0, H,
            f.color ? M(parseInt(String(f.color).replace("#", ""), 16)) : f.type === "wardrobe" ? M(0x8b6a4b) : wood);
        }
        if (f.type === "counter") box(x, y, w, h, H, 1.5, f.top ? M(parseInt(String(f.top).replace("#", ""), 16)) : M(0xe9ecef));        // worktop
        const front = f.face || facing(x, y, w, h);                             // doors open towards the room
        for (let i = 0; i < n; i++) {
          const s2 = long / n, c = (i + 0.5) * s2;
          const hx = along ? x + c - 0.6 : front === "E" ? x + w : x - 1.2;
          const hy = along ? (front === "S" ? y + h : y - 1.2) : y + c - 0.6;
          if ((along && (front === "N" || front === "S")) || (!along && (front === "E" || front === "W")))
            box(hx, hy, along ? 1.2 : 1.2, along ? 1.2 : 1.2, H * 0.35, H * 0.4, M(0xd8dde4), inner, false);
        }
        break;
      }
      case "shelf": {
        box(x, y, w, h, 0, 1.5, wood, inner, false);
        for (const hz of [9, 18, 27]) box(x, y, w, h, hz, 1.5, wood);
        for (const [lx, ly] of [[x, y], [x + w - 2, y], [x, y + h - 2], [x + w - 2, y + h - 2]]) box(lx, ly, 2, 2, 0, 29, woodDark, inner, false);
        for (let i = 0; i < 6; i++) box(x + 3 + (i * (w - 6)) / 6, y + 3, (w - 6) / 6 - 1, h - 6, 1.5, 6 + (i % 3) * 1.5, M([0xd35f5f, 0x5f8fd3, 0xe0b04a][i % 3]), inner, false);
        break;
      }
      case "toilet": {
        const tank = f.tank || "N", tankD = 0.3;
        const tb = { N: [x, y, w, h * tankD], S: [x, y + h * (1 - tankD), w, h * tankD], W: [x, y, w * tankD, h], E: [x + w * (1 - tankD), y, w * tankD, h] }[tank];
        box(tb[0], tb[1], tb[2], tb[3], 0, 18, white);
        const bx = tank === "W" ? x + w * tankD : x, by = tank === "N" ? y + h * tankD : y;
        const bw = tank === "W" || tank === "E" ? w * (1 - tankD) : w, bh = tank === "N" || tank === "S" ? h * (1 - tankD) : h;
        cyl(bx + bw / 2, by + bh / 2, bw / 2 - 1, bh / 2 - 1, 0, 10, white);
        cyl(bx + bw / 2, by + bh / 2, bw / 2 - 4, bh / 2 - 4, 10, 0.4, M(0x9fc9e6));
        if (f.bidet) {                                                       // washlet seat + side control arm (photo)
          cyl(bx + bw / 2, by + bh / 2, bw / 2 + 0.5, bh / 2 + 0.5, 10, 1.6, white);
          box(bx + bw / 2 - 2, by - 3, 6, 3, 9, 3, M(0xe8e4dc), inner, false);
        }
        cyl(bx + bw / 2, by + bh / 2, bw / 2 - 0.6, bh / 2 - 0.6, 10.1, 0.8, M(0xe6e9ee)).material = new THREE.MeshLambertMaterial({ color: 0xe6e9ee, transparent: true, opacity: 0.55 }); // seat ring
        break;
      }
      case "sink": {
        if (f.style === "round") {                                            // round stainless basin set into a wooden desk (5F study photo)
          cyl(x + w / 2, y + h / 2, Math.min(w, h) / 2 - 2, Math.min(w, h) / 2 - 2, 18.6, 0.6, new THREE.MeshStandardMaterial({ color: 0xc9ced6, roughness: 0.2, metalness: 0.8 }));
          cyl(x + 3, y + h / 2, 0.7, 0.7, 19, 5, M(0xc9ced6));
          break;
        }
        box(x, y, w, h, 0, 15, wood);
        box(x, y, w, h, 15, 1.5, white);
        box(x + w * 0.18, y + h * 0.18, w * 0.64, h * 0.64, 15.6, 1, M(0xb8c6d6), inner, false);
        cyl(x + w / 2, y + 3, 1, 1, 16.5, 5, M(0xc9ced6));
        break;
      }
      case "shower": {
        box(x, y, w, h, 0, 1.8, white);
        const g = new THREE.MeshBasicMaterial({ color: 0xbfe9ff, transparent: true, opacity: 0.28, depthWrite: false, side: THREE.DoubleSide });
        for (const s of [[x, y, w, 0.8], [x, y + h - 0.8, w, 0.8], [x, y, 0.8, h], [x + w - 0.8, y, 0.8, h]]) box(s[0], s[1], s[2], s[3], 1.8, 30, g, inner, true);
        cyl(x + 4, y + 4, 0.7, 0.7, 0, 30, M(0xc9ced6));                       // wall pipe in the corner
        cyl(x + 7, y + 7, 4, 4, 29.5, 0.8, M(0xc9ced6));
        cyl(x + w * 0.5, y + h * 0.5, 2, 2, 1.85, 0.3, M(0x6b7380));            // drain
        break;
      }
      case "bathtub": {
        box(x, y, w, h, 0, 13, white);
        box(x + 5, y + 5, w - 10, h - 10, 9, 3.5, M(0x8fc9e8), inner, false);
        cyl(x + w / 2, y + 6, 1.2, 1.2, 13, 5, M(0xc9ced6));
        break;
      }
      case "car": {
        // soft white "Tesla screen" style car: smooth rounded body, grey glasshouse, front towards f.front
        const alongX = (f.axis || "x") === "x";
        const L = (alongX ? w : h) * 0.92, W = (alongX ? h : w) * 0.62;
        const g = new THREE.Group();
        g.position.set(x + w / 2, 0, y + h / 2);
        const yaw = { E: 0, W: Math.PI, S: -Math.PI / 2, N: Math.PI / 2 }[f.front || (alongX ? "E" : "S")];
        g.rotation.y = yaw;
        inner.add(g);
        const paint = new THREE.MeshStandardMaterial({ color: 0xeceef1, roughness: 0.55, metalness: 0.05 });
        const glassM = new THREE.MeshStandardMaterial({ color: 0x9aa1ab, roughness: 0.3, metalness: 0.1 });
        const ext = (draw, depth, mat, bevel) => {
          const sh = new THREE.Shape(); draw(sh);
          const geo = new THREE.ExtrudeGeometry(sh, { depth, bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 5, curveSegments: 10 });
          geo.translate(0, 0, -depth / 2);
          const m = new THREE.Mesh(geo, mat); g.add(m); return m;
        };
        const X = (t) => t * L;
        ext((sh) => {                                           // body: low nose, smooth hood, tall tail
          sh.moveTo(X(-0.48), 4.5); sh.lineTo(X(0.47), 4.5);
          sh.quadraticCurveTo(X(0.52), 8, X(0.46), 10.5);
          sh.quadraticCurveTo(X(0.32), 12.4, X(0.16), 12.8);
          sh.lineTo(X(-0.4), 13.6);
          sh.quadraticCurveTo(X(-0.51), 12.5, X(-0.48), 4.5);
        }, W - 6, paint, 3);
        ext((sh) => {                                           // glasshouse with raked windscreen and fastback
          sh.moveTo(X(0.17), 12.6);
          sh.quadraticCurveTo(X(0.06), 20.5, X(-0.1), 20.6);
          sh.quadraticCurveTo(X(-0.3), 20.2, X(-0.43), 13.3);
          sh.lineTo(X(0.17), 12.6);
        }, W - 14, glassM, 2.2);
        const tyreM = new THREE.MeshStandardMaterial({ color: 0x5d6168, roughness: 0.8 });
        for (const fx of [-0.31, 0.32]) for (const side of [-1, 1]) {
          const t = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 4, 24), tyreM);
          t.rotation.x = Math.PI / 2;
          t.position.set(X(fx), 6, side * (W / 2 - 0.5));
          g.add(t);
        }
        break;
      }
      case "washer": {
        box(x + 1, y + 1, w - 2, h - 2, 0, 22, white);
        cyl(x + w / 2, y + h / 2, Math.min(w, h) * 0.32, Math.min(w, h) * 0.32, 22, 0.6, M(0x5e7a96));
        break;
      }
      case "appliance": box(x, y, w, h, 0, 14, M(0xd8dde4)); box(x + 2, y + 2, w - 4, h - 4, 14, 0.5, M(0x2b2f36), inner, false); break;
      case "stove": {
        box(x, y, w, h, 0, 18, wood);
        box(x + 2, y + 2, w - 4, h - 4, 18, 0.8, M(0x1d2026));
        for (const [fx, fy] of [[0.3, 0.25], [0.7, 0.25], [0.3, 0.75], [0.7, 0.75]]) cyl(x + w * fx, y + h * fy, 5, 5, 18.8, 0.4, M(0x9b3b2f));
        break;
      }
      case "computer": {
        const back = f.back || "N";
        const g = new THREE.Group();
        g.position.set(x + w / 2, z, y + h / 2);
        inner.add(g);
        const span = (back === "N" || back === "S" ? w : h) * 0.9, depth = back === "N" || back === "S" ? h : w;
        const n = f.dual ? 2 : 1, mw = f.dual ? span / 2 - 1 : Math.max(w, h) * 0.85;
        for (let i = 0; i < n; i++) {                                          // dual: two widescreens side by side, toed in slightly
          const sx = n === 1 ? 0 : (i ? 1 : -1) * (mw / 2 + 0.6);
          const unit = new THREE.Group();
          unit.position.set(sx, 0, -depth * 0.25);
          if (n === 2) unit.rotation.y = (i ? -1 : 1) * 0.22;
          const mon = new THREE.Mesh(new THREE.BoxGeometry(mw, 13, 1.5), M(0x16181c));
          const screen = new THREE.Mesh(new THREE.PlaneGeometry(mw - 2, 11), new THREE.MeshBasicMaterial({ color: 0x3d8bff }));
          const stand = new THREE.Mesh(new THREE.BoxGeometry(3, 4, 3), M(0x3a3f47));
          mon.position.set(0, 4 + 6.5, 0); screen.position.set(0, 4 + 6.5, 0.8); stand.position.set(0, 2, 0);
          unit.add(mon, screen, stand);
          g.add(unit);
        }
        const kw = f.dual ? Math.min(mw * 0.9, 34) : mw * 0.8;
        const kb = new THREE.Mesh(new THREE.BoxGeometry(kw, 0.8, 6), M(0x2f343c));
        kb.position.set(0, 0.4, depth * 0.18);
        g.add(kb);
        const mouse = new THREE.Mesh(new THREE.BoxGeometry(2, 0.8, 3), M(0x2f343c));
        mouse.position.set(kw * 0.5 + 4, 0.4, depth * 0.18);
        g.add(mouse);
        g.rotation.y = ({ N: 0, S: Math.PI, E: -Math.PI / 2, W: Math.PI / 2 }[back]) - ((f.rot || 0) * Math.PI) / 180;
        if (z > 0) {                                                            // PC tower under the desk
          const tower = new THREE.Mesh(new THREE.BoxGeometry(7, 16, 15), M(0x1f2329));
          tower.position.set(x + w + 4, 8, y + h / 2);
          inner.add(tower);
          edges(tower);
        }
        break;
      }
      case "printer": {
        box(x + 2, y + 2, w - 4, h - 4, z, 9, M(0xe4e7eb));
        box(x + 6, y + 4, w - 12, 3, z + 9, 0.5, M(0x2b2f36), inner, false);
        box(x + 5, y + h - 8, w - 10, 6, z + 9, 1.2, white, inner, false);
        break;
      }
      case "plant": {
        const r = Math.min(Math.min(w, h) / 2, 24);
        cyl(x + w / 2, y + h / 2, r * 0.45, r * 0.45, z, f.small ? 3 : 8, M(0x8a5a3c));
        const leaves = new THREE.Mesh(new THREE.IcosahedronGeometry(r * (f.small ? 0.7 : 0.85), 1), M(0x3f9d5c));
        leaves.position.set(x + w / 2, z + (f.small ? 3 : 8) + r * 0.7, y + h / 2);
        inner.add(leaves);
        break;
      }
      case "tv_unit": {
        box(x, y + h * 0.35, w, h * 0.65, 0, 10, woodDark);
        const tvw = w * 0.62;
        box(x + w / 2 - 6, y + h * 0.18 - 1, 12, 6, 10, 4, M(0x1d2026));               // stand
        box(x + (w - tvw) / 2, y + h * 0.18, tvw, 2, 14, 30, M(0x111317));            // TV stands taller than the cabinets
        const scr = new THREE.Mesh(new THREE.PlaneGeometry(tvw - 2, 28), new THREE.MeshBasicMaterial({ color: 0x2a3d5c }));
        scr.position.set(x + w / 2, 29, y + h * 0.18 + 2.1);
        inner.add(scr);
        break;
      }
      case "tv_wall": {                       // photo 1: low dark-wood media console, big TV hung on the wall above it, split AC higher up
        const dw = M(0x4a3020), dark = M(0x2a1a10);
        const depth = Math.min(h * 0.28, 20);                                   // shallow console against the wall
        box(x, y, w, depth, 0, 9, dw);                                          // console body
        box(x - 1, y - 0.5, w + 2, depth + 1, 9, 1.2, M(0x5a3a24));             // console top
        for (const dx of [0.33, 0.66]) box(x + w * dx, y + depth - 0.6, 0.8, 0.8, 1, 9, dark, inner, false);   // open-shelf dividers
        for (let i = 0; i < 4; i++) {                                           // gear on the shelves: AV boxes
          box(x + w * (0.08 + i * 0.24), y + depth - 3, w * 0.14, 3, 2.5, 3, M(i % 2 ? 0x1c1d21 : 0x6d717a), inner, false);
        }
        const pw = Math.min(w * 0.86, 190);                                     // dark wood frame on the wall (outline only)
        const px = x + (w - pw) / 2;
        for (const fx of [px, px + pw - 2]) box(fx, y - 0.2, 2, 1, 12, 17, dark, inner, false);   // frame sides
        box(px, y - 0.2, pw, 1, 28.5, 1.8, dark, inner, false);                            // frame top
        const tvw = pw * 0.34;                                                  // TV well inside the frame (photo)                                                  // big TV hung high, clear above the console
        box(x + (w - tvw) / 2, y + 1.5, tvw, 2.5, 13.5, 13, M(0x232529));
        const scr = new THREE.Mesh(new THREE.PlaneGeometry(tvw - 2, 11), new THREE.MeshBasicMaterial({ color: 0x2c4a73 }));
        scr.position.set(x + w / 2, 20, y + 4.1);
        inner.add(scr);
        const glare = new THREE.Mesh(new THREE.PlaneGeometry(tvw * 0.3, 11), new THREE.MeshBasicMaterial({ color: 0x4b6c99, transparent: true, opacity: 0.5 }));
        glare.position.set(x + w / 2 - tvw * 0.25, 20, y + 4.15);
        inner.add(glare);
        if (f.ac) box(x + w / 2 - 15, y + 0.6, 50, 6, 30.4, 3.4, M(0xf4f2ee));  // split AC just above the frame, over the right half of the TV (photo)
        break;
      }
      case "floor_patch": {                   // tiled / timber floor area (5F roof terrace photo: beige tiles)
        box(x, y, w, h, 0, 0.5, M(parseInt(String(f.color || "#d8cfb8").replace("#", ""), 16)), inner, false);
        if (f.grid) for (let gx = x + f.grid; gx < x + w; gx += f.grid) box(gx - 0.25, y, 0.5, h, 0.5, 0.15, M(0x8f8676), inner, false);
        if (f.grid) for (let gy = y + f.grid; gy < y + h; gy += f.grid) box(x, gy - 0.25, w, 0.5, 0.5, 0.15, M(0x8f8676), inner, false);
        break;
      }
      case "pots": {                          // row of terracotta planter troughs with shrubs (roof terrace)
        const along = w >= h, n = Math.max(1, Math.round((along ? w : h) / 22));
        for (let i = 0; i < n; i++) {
          const L = (along ? w : h) / n;
          const px = along ? x + i * L + 1 : x, py = along ? y : y + i * L + 1;
          box(px, py, along ? L - 2 : w, along ? h : L - 2, 0, 6, M(0xb5583c));
          const bush = new THREE.Mesh(new THREE.IcosahedronGeometry(Math.min(along ? L : w, along ? h : L) * 0.45, 0), M(i % 2 ? 0x7a6b45 : 0x5e6b3a));
          bush.position.set(px + (along ? L / 2 : w / 2), 9, py + (along ? h / 2 : L / 2)); inner.add(bush);
        }
        break;
      }
      case "curtain_line": {                  // free-standing curtain on a ceiling track (sheer room divider / partition)
        const along = w >= h, len = along ? w : h, folds = Math.max(4, Math.round(len / 6));
        const mat = new THREE.MeshLambertMaterial({ color: parseInt(String(f.color || "#e9dfcc").replace("#", ""), 16), transparent: true, opacity: f.sheer ? 0.45 : 0.95, side: THREE.DoubleSide, depthWrite: !f.sheer });
        for (let i = 0; i < folds; i++) {
          const t = (i + 0.5) / folds, z = i % 2 ? 1.2 : -1.2;
          const m = new THREE.Mesh(new THREE.BoxGeometry(along ? len / folds + 0.4 : 0.8, 31, along ? 0.8 : len / folds + 0.4), mat);
          m.position.set(along ? x + w * t : x + w / 2 + z, 16, along ? y + h / 2 + z : y + h * t);
          inner.add(m);
        }
        box(x, y, w, h, 33.4, 0.8, M(0xe8e8e8), inner, false);
        break;
      }
      case "wall_shelf": {                    // open cubby shelf hung on the wall
        const along = w >= h, n = Math.max(2, Math.round((along ? w : h) / 14));
        box(x, y, w, h, 20, 0.8, wood); box(x, y, w, h, 26, 0.8, wood); box(x, y, w, h, 32, 0.8, wood);
        for (let i = 0; i <= n; i++) {
          const t = i / n;
          box(along ? x + w * t - 0.4 : x, along ? y : y + h * t - 0.4, along ? 0.8 : w, along ? h : 0.8, 20, 12, wood, inner, false);
        }
        break;
      }
      case "metal_cabinet": box(x, y, w, h, 0, 17, M(0x2f5a45)); for (const hz of [6, 11.5]) box(x, y - 0.4, w, 0.6, hz, 0.5, M(0xb0b4b8), inner, false); break;
      case "chest": {                         // white drawer chest on wooden legs (5F room photo)
        box(x, y, w, h, 3, 17, M(0xf2efe8));
        box(x - 0.5, y - 0.5, w + 1, h + 1, 20, 1, wood);
        for (const hz of [7, 11, 15]) box(x + 1, y - 0.4, w - 2, 0.5, hz, 0.4, M(0xc9bfae), inner, false);
        for (const [lx, ly] of [[x + 1, y + 1], [x + w - 2, y + 1], [x + 1, y + h - 2], [x + w - 2, y + h - 2]]) box(lx, ly, 1, 1, 0, 3, wood, inner, false);
        break;
      }
      case "cube_shelf": {                    // white cube bookshelf
        box(x, y, w, h, 0, 22, M(0xf4f2ee));
        for (const hz of [7.5, 15]) box(x, y - 0.3, w, 0.6, hz, 0.8, M(0xd8d4cc), inner, false);
        break;
      }
      case "ac_unit": box(x, y, w, h, 28, 4, M(0xf4f2ee)); break;
      case "whiteboard": box(x, y, w, h, 14, 11, new THREE.MeshStandardMaterial({ color: 0xdfe8e4, roughness: 0.1, metalness: 0.2 })); break;
      case "deck": {                          // timber deck boards (front balcony photo)
        const n = Math.max(4, Math.round(w / 9));
        for (let i = 0; i < n; i++) box(x + (i * w) / n + 0.3, y, w / n - 0.6, h, 0, 1.2, M(i % 2 ? 0x6b4a2e : 0x765233), inner, false);
        break;
      }
      case "garden_table": {                  // white cast-iron bistro table
        const wt = M(0xf4f4f2);
        cyl(x + w / 2, y + h / 2, w / 2, h / 2, 16, 1.2, wt);
        cyl(x + w / 2, y + h / 2, 1, 1, 0, 16, wt);
        for (let i = 0; i < 3; i++) { const a = (i / 3) * Math.PI * 2; box(x + w / 2 + Math.cos(a) * 6 - 0.6, y + h / 2 + Math.sin(a) * 6 - 0.6, 1.2, 1.2, 0, 3, wt, inner, false); }
        break;
      }
      case "garden_chair": {                  // white cast-iron chair with round lattice back
        const wt = M(0xf4f4f2), face = f.face || "N";
        cyl(x + w / 2, y + h / 2, w / 2 - 1, h / 2 - 1, 9, 1, wt);
        for (const [lx, ly] of [[x + 3, y + 3], [x + w - 4, y + 3], [x + 3, y + h - 4], [x + w - 4, y + h - 4]]) box(lx, ly, 1, 1, 0, 9, wt, inner, false);
        const back = { N: [x + 2, y + h - 2, w - 4, 1], S: [x + 2, y + 1, w - 4, 1], E: [x + 1, y + 2, 1, h - 4], W: [x + w - 2, y + 2, 1, h - 4] }[face];
        box(back[0], back[1], back[2], back[3], 10, 13, new THREE.MeshLambertMaterial({ color: 0xf4f4f2, transparent: true, opacity: 0.85 }));
        break;
      }
      case "planter": {                       // raised stone planter with a tree
        box(x, y, w, h, 0, 14, M(0xb9b2a5));
        box(x + 2, y + 2, w - 4, h - 4, 14, 0.6, M(0x4a3626), inner, false);
        cyl(x + w / 2, y + h / 2, 1.5, 1.5, 14, 14, M(0x6b4f35));
        const crown = new THREE.Mesh(new THREE.IcosahedronGeometry(Math.min(w, h) * 0.5, 1), M(0x3f8a4f));
        crown.position.set(x + w / 2, 34, y + h / 2); inner.add(crown);
        break;
      }
      case "purifier": box(x + 2, y + 2, w - 4, h - 4, 0, 18, M(0xf5f5f3)); cyl(x + w / 2, y + h / 2, w / 2 - 4, h / 2 - 4, 18, 0.5, M(0x9aa0a8)); break;
      case "kitchen_run": {                   // glossy black base units, white worktop, wine-red uppers on the wall side (photos)
        const along = w >= h;
        const blk = new THREE.MeshStandardMaterial({ color: 0x1c1416, roughness: 0.25, metalness: 0.1 });
        const red = new THREE.MeshStandardMaterial({ color: 0x7a1f2b, roughness: 0.25, metalness: 0.1 });
        box(x, y, w, h, 0, 17, blk);
        box(x, y, w, h, 17, 1.5, M(0xf3f3f1));
        const L = along ? w : h, n = Math.max(2, Math.round(L / 30));
        for (let i = 0; i < n; i++) {                                         // drawer handles on the room side
          const c = (i + 0.5) / n;
          if (along) box(x + w * c - 6, y + h, 12, 0.8, 13, 0.8, M(0xc9ced6), inner, false);
          else box(x - 0.8, y + h * c - 6, 0.8, 12, 13, 0.8, M(0xc9ced6), inner, false);
        }
        const ud = Math.min(along ? h : w, 14);                               // upper cabinets against the wall, left open where a window is
        const wallAt = along ? y : x + w;
        let segs = [[along ? x : y, along ? x + w : y + h]];
        for (const s of this._winSpans || []) {
          if (s.hz !== along || Math.abs(s.line - wallAt) > 20) continue;
          segs = segs.flatMap(([a, b]) => (s.b + 2 <= a || s.a - 2 >= b ? [[a, b]] : [[a, s.a - 2], [s.b + 2, b]]).filter(([p, q]) => q - p > 4));
        }
        for (const [a, b] of segs) { if (along) box(a, y, b - a, ud, 25, 9, red); else box(x + w - ud, a, ud, b - a, 25, 9, red); }
        if (f.sink_at != null) {
          const c = f.sink_at, sw = 22;
          const sx = along ? x + w * c - sw / 2 : x + 4, sy = along ? y + 4 : y + h * c - sw / 2;
          box(sx, sy, along ? sw : w - 8, along ? h - 8 : sw, 17.8, 0.8, M(0x9aa2ac), inner, false);
          cyl(along ? x + w * c : x + w - 5, along ? y + 5 : y + h * c, 0.8, 0.8, 18.5, 6, M(0xc9ced6));
        }
        if (f.cooktop_at != null) {
          const c = f.cooktop_at, cw = 30;
          const cx0 = along ? x + w * c - cw / 2 : x + 3, cy0 = along ? y + 3 : y + h * c - cw / 2;
          box(cx0, cy0, along ? cw : w - 6, along ? h - 6 : cw, 18.6, 0.5, M(0x111214), inner, false);
          if (f.hood) {
            const hm = new THREE.MeshStandardMaterial({ color: 0xc4c9cf, roughness: 0.3, metalness: 0.7 });
            box(along ? cx0 : x + w - 18, along ? y : cy0, along ? cw : 18, along ? 18 : cw, 26, 2, hm);
            box(along ? cx0 + cw / 2 - 4 : x + w - 10, along ? y + 2 : cy0 + cw / 2 - 4, 8, 8, 28, 6, hm);
          }
        }
        break;
      }
      case "hutch": {                         // dark wood hutch: base + worktop + frosted sliding glass upper (photo 3)
        box(x, y, w, h, 0, 17, M(0x3b2618));
        box(x, y, w, h, 17, 1.2, M(0xf3f3f1));
        box(x, y, w, h * 0.6, 24, 10, M(0x3b2618));
        box(x + 2, y + h * 0.6, w - 4, 0.6, 25, 8, new THREE.MeshLambertMaterial({ color: 0xdfe6ea, transparent: true, opacity: 0.8 }), inner, false);
        break;
      }
      case "fridge": {                        // photo 4: big black French-door fridge, a little lower than the tall pantry behind it
        const m = new THREE.MeshStandardMaterial({ color: 0x1a1214, roughness: 0.2, metalness: 0.2 });
        const H = 30;
        box(x, y, w, h, 0, H, m);
        const line = M(0x55595f), front = f.front || "N", ns = front === "N" || front === "S";
        const L = ns ? w : h;                                                        // door width
        const fx = front === "E" ? x + w - 0.2 : x - 0.4, fy = front === "S" ? y + h - 0.2 : y - 0.4;
        const slab = (off, len, z0, hz, th = 0.6) => ns
          ? box(x + off, fy, len, th, z0, hz, line, inner, false)
          : box(fx, y + off, th, len, z0, hz, line, inner, false);
        slab(L / 2 - 0.2, 0.4, 14, 15);                                              // French-door split
        slab(1, L - 2, 13.5, 0.4);                                                   // freezer / fridge split
        for (const hz of [6, 10]) slab(1, L - 2, hz, 0.4);                           // drawer lines
        for (const ho of [L / 2 - 3, L / 2 + 2]) slab(ho, 1, 15, 10, 0.9);           // handles
        slab(4, L * 0.35, 22, 5, 0.5);                                               // calendar magnets on the door
        break;
      }
      case "pantry": {                        // tall black cabinet reaching the ceiling, behind the fridge
        const m = new THREE.MeshStandardMaterial({ color: 0x1c1416, roughness: 0.25 });
        box(x, y, w, h, 0, 34, m);
        for (const hz of [11, 22]) box(x + 1, y + h - 0.3, w - 2, 0.6, hz, 0.4, M(0x55595f), inner, false);
        break;
      }
      case "pedestal_sink": {                 // white pedestal basin + glass shelf (photo 5)
        cyl(x + w / 2, y + h / 2, 3, 3, 0, 13, white);
        cyl(x + w / 2, y + h / 2, w / 2 - 2, h / 2 - 3, 13, 3, white);
        cyl(x + w / 2, y + h / 2, w / 2 - 6, h / 2 - 7, 15.6, 0.5, M(0xb8c6d6));
        break;
      }
      case "mirror": box(x, y, w, h, 18, 12, new THREE.MeshStandardMaterial({ color: 0xcfe3ec, roughness: 0.05, metalness: 0.9 })); break;
      default: box(x, y, w, h, 0, 10, M(0x8a93a3));
    }
  }

  _applyFloor() {
    if (!this._ready) return;
    const T = this._T;
    const all = this._floor === "全棟";
    const names = Object.keys(this._cfg.floors).filter((n) => this._groups[n]);
    names.forEach((n, i) => {
      const g = this._groups[n].group;
      g.visible = all || n === this._floor;
      g.position.y = all ? i * FLOOR_GAP : 0;
      for (const c of this._groups[n].detail || []) c.visible = !all;       // whole-house = light shell only
    });
    this._rebuildSpots();
    this._syncTools?.();
    this.shadowRoot.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.f === this._floor));
    this._zone = null;
    const whole = this._floor === "全棟";
    for (const q of [".filter", ".zones", ".scn", ".tools"]) { const e = this.shadowRoot.querySelector(q); if (e) e.style.visibility = whole ? "hidden" : ""; }
    this._renderer?.setPixelRatio(Math.min(window.devicePixelRatio || 1, whole ? 1.25 : 2));
    this._renderScenes();
    this._expanded = null;
    this._focus = null;
    this._renderZones();
    this._frame();
    this._sync();
    this._dirty = true;
  }

  _makePin(cat, extra = "") {
    const el = document.createElement("div");
    el.className = `pin ${cat} ${extra}`;
    el.dataset.cat = cat;
    el.innerHTML = `<div class="dot"></div>
      <div class="tag"><span class="ic"><ha-icon></ha-icon></span><span class="tx"><b class="nm"></b><small class="ty"></small></span></div>`;
    return el;
  }
  _inZone(x, y) {
    const z = this._zone;
    return !z || (x >= z.x && x <= z.x + z.w && y >= z.y && y <= z.y + z.h);
  }
  _applyCats() {
    for (const sp of this._spots || []) {
      if (sp.badge || sp.always) { sp.el.classList.remove("hide"); continue; }
      const grouped = sp.group ? this._expanded === sp.group : (sp.d._group && this._expanded !== sp.d._group && !sp.d._alert);
      sp.el.classList.toggle("hide", !this._cats.has(sp.cat) || !this._inZone(sp.d.x, sp.d.y) || !!grouped);
    }
    for (const pr of this._persons || []) pr.el.classList.toggle("hide", !this._cats.has("people"));
  }
  _renderScenes() {
    const host = this.shadowRoot.querySelector(".scn");
    const sc = this._cfg.floors[this._floor]?.scenes || [];
    host.innerHTML = sc.map((x, i) => `<button data-i="${i}"><ha-icon icon="${x.icon}"></ha-icon>${x.name}</button>`).join("");
    host.onclick = (e) => {
      const b = e.target.closest("button");
      if (!b || !this._hass) return;
      const x = sc[+b.dataset.i];
      this._hass.callService("input_boolean", "turn_on", { entity_id: x.entity });   // scene triggers reset themselves
    };
    this._syncScenes();
  }
  _syncScenes() {
    const st = this._hass?.states;
    const sc = this._cfg.floors[this._floor]?.scenes || [];
    this.shadowRoot.querySelectorAll(".scn button").forEach((b) => b.classList.toggle("on", st?.[sc[+b.dataset.i]?.entity]?.state === "on"));
  }
  _renderZones() {
    this._barDirty = true;
    const host = this.shadowRoot.querySelector(".zones");
    const zones = this._cfg.floors[this._floor]?.zones || [];
    this.shadowRoot.querySelector(".hint").style.display = zones.length || this._expanded ? "none" : "";
    host.innerHTML = (zones.length ? [`<button data-z="">整層</button>`, ...zones.map((z, i) => `<button data-z="${i}">${z.name}</button>`)] : [])
      .concat(this._expanded ? [`<button data-z="collapse">← 收合群組</button>`] : []).join("");
    host.querySelectorAll("button").forEach((b) => b.classList.toggle("on", (b.dataset.z === "" && !this._zone) || zones[b.dataset.z] === this._zone));
    host.onclick = (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.z === "collapse") { this._expanded = null; this._focus = null; }
      else { this._zone = b.dataset.z === "" ? null : zones[+b.dataset.z]; this._expanded = null; this._focus = null; }
      this._frame();
      this._applyCats();
      this._renderZones();
      this._dirty = true;
    };
  }
  _frame() {
    const names = Object.keys(this._cfg.floors).filter((n) => this._groups[n]);
    const all = this._floor === "全棟";
    const span = all ? (names.length - 1) * FLOOR_GAP : 0;
    const ref = this._groups[all ? names[0] : this._floor]?.fl || { width: 900, height: 560 };
    if (this._focus && !all) { const f = this._focus; return this._frameRect(f.x, f.y, f.w, f.h, ref, 0); }
    if (this._zone && !all) { const z = this._zone; return this._frameRect(z.x, z.y, z.w, z.h, ref, 0); }
    this._frameRect(0, 0, ref.width, ref.height, ref, span);
  }
  // place the camera so a plan rectangle fills the view between the top and bottom button bars
  _frameRect(x, y, w, h, ref, span) {
    const T = this._T;
    const wrap = this.shadowRoot.querySelector(".wrap");
    const aspect = (wrap.clientWidth || 800) / (wrap.clientHeight || 600);
    const vf = (this._cam.fov * Math.PI) / 360;                 // half vertical fov
    const hf = Math.atan(Math.tan(vf) * aspect);
    const usable = 0.8;                                         // leave room for the button bars
    // tall (phone) view: turn the plan so its long side runs up the screen and fill the height
    const turn = aspect < 0.95 && w > h * 1.15;
    const ew = turn ? h : w, eh = turn ? w : h;                 // extents along screen x / screen y
    const distW = (ew / 2) / Math.tan(hf) * 1.06;
    const distH = ((eh * (turn ? 0.78 : 0.62) + span) / 2) / (Math.tan(vf) * usable) * 1.06;
    let dist = Math.max(distW, distH, 160);
    const cx = x + w / 2 - ref.width / 2, cz = y + h / 2 - ref.height / 2;
    const dir = (turn ? new T.Vector3(0.95, 1.05, 0.12) : new T.Vector3(0.3, 0.86, 0.75)).normalize();
    this._controls.target.copy(new T.Vector3(cx, span / 2, cz + (turn ? 0 : h * 0.04)));
    this._cam.position.copy(this._controls.target).addScaledVector(dir, dist);
    // refine numerically: project the box corners, then scale/shift until they fill the usable area
    const W = wrap.clientWidth || 800, H = wrap.clientHeight || 600;
    const corners = [];
    for (const px of [x, x + w]) for (const pz of [y, y + h]) for (const py of [0, 38]) {
      corners.push(new T.Vector3(px - ref.width / 2, py + span * 0 , pz - ref.height / 2));
    }
    if (span) for (const c of [...corners]) corners.push(new T.Vector3(c.x, c.y + span, c.z));
    const top = (aspect < 0.95 ? 0.2 : 0.14) * H, bottom = 0.86 * H, usableH = bottom - top, usableW = 0.94 * W;
    for (let it = 0; it < 8; it++) {
      this._cam.lookAt(this._controls.target);
      this._cam.updateMatrixWorld(); this._cam.updateProjectionMatrix();
      let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
      for (const c of corners) {
        const v = c.clone().project(this._cam);
        const sx = ((v.x + 1) / 2) * W, sy = ((1 - v.y) / 2) * H;
        x0 = Math.min(x0, sx); x1 = Math.max(x1, sx); y0 = Math.min(y0, sy); y1 = Math.max(y1, sy);
      }
      const scale = Math.max((x1 - x0) / usableW, (y1 - y0) / usableH);
      const cxs = (x0 + x1) / 2, cys = (y0 + y1) / 2;
      const dx = (cxs - W / 2) / W, dy = (cys - (top + bottom) / 2) / H;   // how far the box is off-centre
      const d0 = this._cam.position.distanceTo(this._controls.target);
      const right = new T.Vector3().setFromMatrixColumn(this._cam.matrixWorld, 0);
      const up = new T.Vector3().setFromMatrixColumn(this._cam.matrixWorld, 1);
      const unit = 2 * d0 * Math.tan(vf);                                   // world height seen at the target
      this._controls.target.addScaledVector(right, dx * unit * aspect).addScaledVector(up, -dy * unit);
      this._cam.position.copy(this._controls.target).addScaledVector(dir, d0 * Math.min(2, Math.max(0.5, scale)));
      dist = d0 * scale;
    }
    this._controls.minDistance = dist * 0.25;
    this._controls.maxDistance = dist * 2.8;
    this._controls.update();
    this._dirty = true;
  }
  _rebuildSpots() {
    const host = this.shadowRoot.querySelector(".spots");
    host.replaceChildren();
    this._links = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this._links.setAttribute("class", "links");
    host.appendChild(this._links);
    this._spots = [];
    const all = this._floor === "全棟";
    const order = Object.keys(this._cfg.floors);
    const stairSeen = new Set();                         // whole-house: each stair light once (shared lights sit on two floors)
    Object.entries(this._groups).forEach(([n, g]) => {
      if (!all && n !== this._floor) return;
      if (all) {                                           // whole-house view: one badge per floor, tap = open that floor
        const el = this._makePin("stair", "floorbadge");
        el.querySelector("ha-icon").setAttribute("icon", "mdi:layers-outline");
        el.querySelector(".nm").textContent = n;
        const tag = el.querySelector(".tag");
        tag.addEventListener("pointerdown", (e) => e.stopPropagation());
        tag.addEventListener("pointerup", (e) => { e.stopPropagation(); this._floor = n; setFloor(n); this._applyFloor(); });
        host.appendChild(el);
        this._spots.push({ el, ic: el.querySelector("ha-icon"), nm: el.querySelector(".nm"), ty: el.querySelector(".ty"), tag,
          d: { x: g.fl.width / 2, y: g.fl.height / 2, z: 36, kind: "badge" }, floor: n, g, cat: "badge", badge: n });
        for (const d of g.fl.devices) {                  // stair lights stay visible and tappable in the whole-house view
          if (catOf(d) !== "light" || !/樓梯燈/.test(d.name || "") || stairSeen.has(d.entity)) continue;
          stairSeen.add(d.entity);
          const sel = this._makePin("light", d.kind);
          this._bindSpot(sel, d, n);
          host.appendChild(sel);
          this._spots.push({ el: sel, ic: sel.querySelector("ha-icon"), nm: sel.querySelector(".nm"), ty: sel.querySelector(".ty"),
            tag: sel.querySelector(".tag"), d, floor: n, g, cat: "light", always: true });
        }
        return;
      }
      for (const d of g.fl.devices) {
        const cat = catOf(d);
        const el = this._makePin(cat, `${d.kind}${d.kind === "camera" ? " cam" : ""}`);
        this._bindSpot(el, d, n);
        host.appendChild(el);
        this._spots.push({ el, ic: el.querySelector("ha-icon"), nm: el.querySelector(".nm"), ty: el.querySelector(".ty"),
          tag: el.querySelector(".tag"), d, floor: n, g, cat });
      }
      // cluster lights of one room that are close together
      const lights = g.fl.devices.filter((d) => catOf(d) === "light");
      const clusters = [];
      for (const d of lights) {
        const c = clusters.find((k) => k.room === (d.zone || d.room || "") && k.items.some((o) => Math.hypot(o.x - d.x, o.y - d.y) < 110));
        if (c) c.items.push(d); else clusters.push({ room: d.zone || d.room || "", items: [d] });
      }
      clusters.filter((c) => c.items.length >= 2).forEach((c, ci) => {
        const key = `${n}|${ci}`;
        const xs = c.items.map((d) => d.x), ys = c.items.map((d) => d.y);
        const box = { x: Math.min(...xs) - 70, y: Math.min(...ys) - 70, w: Math.max(...xs) - Math.min(...xs) + 140, h: Math.max(...ys) - Math.min(...ys) + 140 };
        for (const d of c.items) d._group = key;
        const el = this._makePin("light", "group");
        const tag = el.querySelector(".tag");
        let timer = null, held = false;
        tag.addEventListener("pointerdown", (e) => {
          e.stopPropagation(); held = false;
          timer = setTimeout(() => {                         // long press: all on / all off
            held = true;
            const anyOn = c.items.some((d) => this._hass?.states[d.entity]?.state === "on");
            this._hass?.callService("homeassistant", anyOn ? "turn_off" : "turn_on", { entity_id: c.items.map((d) => d.entity) });
          }, 500);
        });
        tag.addEventListener("pointerup", (e) => {
          e.stopPropagation(); clearTimeout(timer);
          if (held) return;
          this._expanded = key; this._focus = box;           // tap: zoom in and show every light
          this._frame(); this._applyCats(); this._renderZones();
        });
        host.appendChild(el);
        const d = { x: xs.reduce((a, b) => a + b, 0) / xs.length, y: ys.reduce((a, b) => a + b, 0) / ys.length, kind: "group", z: 6 };
        this._spots.push({ el, ic: el.querySelector("ha-icon"), nm: el.querySelector(".nm"), ty: el.querySelector(".ty"),
          tag, d, floor: n, g, cat: "light", group: key, items: c.items, room: c.room });
      });
      // multi-sensor devices: group by device name prefix ("廚房環境感測器 廚房 CO2" -> 廚房環境感測器)
      const sgroups = {};
      for (const d of g.fl.devices) {
        if (!["temp", "hum", "value", "safety"].includes(d.kind)) continue;
        const nm = this._hass?.states[d.entity]?.attributes?.friendly_name || d.name || "";
        const prefix = nm.includes(" ") ? nm.split(" ")[0] : "";
        if (prefix.length >= 2) (sgroups[prefix] = sgroups[prefix] || []).push(d);
      }
      Object.entries(sgroups).filter(([, items]) => items.length >= 2).forEach(([prefix, items]) => {
        const key = `${n}|s|${prefix}`;
        const xs = items.map((d) => d.x), ys = items.map((d) => d.y);
        const box = { x: Math.min(...xs) - 60, y: Math.min(...ys) - 60, w: Math.max(...xs) - Math.min(...xs) + 120, h: Math.max(...ys) - Math.min(...ys) + 120 };
        for (const d of items) d._group = key;
        const el = this._makePin("env", "group sgroup");
        const tag = el.querySelector(".tag");
        tag.addEventListener("pointerdown", (e) => e.stopPropagation());
        tag.addEventListener("pointerup", (e) => {
          e.stopPropagation();
          this._expanded = key; this._focus = box;           // tap: zoom in and list every reading
          this._frame(); this._applyCats(); this._renderZones();
        });
        host.appendChild(el);
        const d = { x: xs.reduce((a, b) => a + b, 0) / xs.length, y: ys.reduce((a, b) => a + b, 0) / ys.length, kind: "sgroup", z: 6 };
        this._spots.push({ el, ic: el.querySelector("ha-icon"), nm: el.querySelector(".nm"), ty: el.querySelector(".ty"),
          tag, d, floor: n, g, cat: "env", group: key, items, sname: prefix.replace(/感測器|傳感器/, "") });
      });
      for (const st of g.fl.stairs || []) {               // stair badges: tap to go to the connected floor
        const target = order[order.indexOf(n) + (st.h1 > 0 ? 1 : -1)];
        if (!target || st.badge === false) continue;
        const el = this._makePin("stair");
        el.querySelector("ha-icon").setAttribute("icon", st.h1 > 0 ? "mdi:stairs-up" : "mdi:stairs-down");
        el.querySelector(".nm").textContent = `${st.h1 > 0 ? "上" : "下"} ${target}`;
        el.querySelector(".ty").remove();
        el.querySelector(".tag").addEventListener("pointerdown", (e) => e.stopPropagation());
        el.querySelector(".tag").addEventListener("pointerup", (e) => { e.stopPropagation(); this._floor = target; setFloor(target); this._applyFloor(); });
        host.appendChild(el);
        // anchor at the top step (up) or the entry (down)
        const top = st.dir > 0 ? 0.85 : 0.15;
        const d = { x: st.axis === "x" ? st.x + st.w * top : st.x + st.w / 2, y: st.axis === "y" ? st.y + st.h * top : st.y + st.h / 2,
          z: st.h1 > 0 ? 30 : 2, kind: "stair" };
        this._spots.push({ el, tag: el.querySelector(".tag"), d, floor: n, g, stair: true, cat: "stair" });
      }
    });
    this._persons = (all ? [] : this._cfg.people || []).map((p, i) => {
      const el = this._makePin("people", "person");
      el.querySelector(".ic").textContent = p.name.slice(0, 1);
      el.querySelector(".ic").style.background = p.color;
      el.querySelector(".nm").textContent = p.name;
      el.style.display = "none";
      host.appendChild(el);
      return { el, p, i, cur: null, tag: el.querySelector(".tag") };
    });
    this._applyCats();
  }

  _bindSpot(el, d, floor) {
    let timer = null, held = false, drag = false;
    el.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      if (this._edit) {
        drag = true;
        this._controls.enabled = false;
        e.target.setPointerCapture?.(e.pointerId);
        return;
      }
      held = false;
      timer = setTimeout(() => { held = true; this._moreInfo(d.entity); }, 500);
    });
    el.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const p = this._planPoint(e, floor);
      if (p) { d.x = Math.round(p.x * 10) / 10; d.y = Math.round(p.y * 10) / 10; this._moveDecal(floor, d); this._dirty = true; }
    });
    const end = (e) => {
      clearTimeout(timer);
      e.stopPropagation();
      if (drag) {
        drag = false;
        this._controls.enabled = true;
        this._ovr[`${floor}|${d.entity}`] = [d.x, d.y];
        this._saveOverrides();
        return;
      }
      if (e.type === "pointerup" && !held) this._tap(d);
    };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener("pointerleave", () => clearTimeout(timer));
  }
  _planPoint(e, floor) {
    const T = this._T, g = this._groups[floor];
    const r = this.shadowRoot.querySelector(".wrap").getBoundingClientRect();
    const ndc = new T.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    this._ray.setFromCamera(ndc, this._cam);
    const plane = new T.Plane(new T.Vector3(0, 1, 0), -(g.group.position.y + 8));
    const hit = new T.Vector3();
    if (!this._ray.ray.intersectPlane(plane, hit)) return null;
    return { x: hit.x + g.fl.width / 2, y: hit.z + g.fl.height / 2 };
  }
  _tap(d) {
    if (!this._hass) return;
    if (d.kind === "doorlock") return this._moreInfo(d.entity);       // never toggle a door lock by accident
    if (TOGGLE_KINDS.includes(d.kind)) this._hass.callService("homeassistant", "toggle", { entity_id: d.entity });
    else this._moreInfo(d.entity);
  }
  _moreInfo(entityId) {
    this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId } }));
  }

  _sync() {
    const T = this._T, st = this._hass?.states;
    if (!st) return;
    let alertChanged = false;
    for (const sp of this._spots.filter((x) => x.group && x.d.kind === "sgroup")) {
      const val = (k) => sp.items.filter((d) => d.kind === k).map((d) => parseFloat(st[d.entity]?.state)).filter((v) => !isNaN(v));
      const parts = [];
      const t = val("temp"), hm = val("hum");
      if (t.length) parts.push(`${t[0].toFixed(1)}°`);
      if (hm.length) parts.push(`${Math.round(hm[0])}%`);
      for (const d of sp.items.filter((x) => x.kind === "value")) {
        const s = st[d.entity];
        if (s && !isNaN(parseFloat(s.state))) parts.push(`${(s.attributes.friendly_name || "").split(" ").pop()} ${Math.round(parseFloat(s.state))}`);
      }
      const alerts = sp.items.filter((d) => d.kind === "safety" && st[d.entity]?.state === "on");
      for (const d of sp.items) {
        const a = alerts.includes(d);
        if (!!d._alert !== a) { d._alert = a; alertChanged = true; }   // an abnormal reading is shown on its own
      }
      const type = alerts.length ? `⚠ 異常 ${alerts.length} 項` : `正常 · ${parts.slice(0, 3).join(" · ")}`;
      if (sp._type !== type) { sp.nm.textContent = sp.sname; sp.ty.textContent = type; sp._type = type; sp.tw = 0; }
      if (!sp._icon) { sp.ic.setAttribute("icon", "mdi:air-filter"); sp._icon = 1; }
      sp.el.classList.toggle("alert", alerts.length > 0);
      if (!alerts.length && t.length) { const col = tempColor(t[0]); if (sp._col !== col) { sp.el.querySelector(".ic").style.background = col; sp.el.querySelector(".ic").style.color = "#111"; sp._col = col; } }
    }
    if (alertChanged) this._applyCats();
    for (const sp of this._spots.filter((x) => x.group && x.d.kind !== "sgroup")) {
      const on = sp.items.filter((d) => st[d.entity]?.state === "on").length;
      const name = `${sp.room || ""}燈光`, type = `${sp.items.length} 盞 · 開 ${on}`;
      if (sp._type !== type) { sp.nm.textContent = name; sp.ty.textContent = type; sp._type = type; sp.tw = 0; }
      if (!sp._icon) { sp.ic.setAttribute("icon", "mdi:lightbulb-group"); sp._icon = 1; }
      sp.el.classList.toggle("on", on > 0);
    }
    this._syncScenes?.();
    for (const sp of this._spots.filter((x) => x.badge)) {
      const fl = sp.g.fl;
      const lights = fl.devices.filter((d) => d.kind === "light" || (d.kind === "switch" && d.light));
      const on = lights.filter((d) => st[d.entity]?.state === "on").length;
      const trig = fl.devices.filter((d) => ["motion", "person"].includes(d.kind) && st[d.entity]?.state === "on").length;
      const people = (this._cfg.people || []).filter((p) => {
        const m = st[`binary_sensor.at_home_${p.id}`]?.state === "on" && this._cfg.locations?.[st[`sensor.at_home_${p.id}_location`]?.state];
        return m && m.floor === sp.badge;
      }).map((p) => p.name.slice(0, 1));
      const type = `燈 ${on}/${lights.length}${people.length ? " · " + people.join("") : ""}${trig ? " · 偵測 " + trig : ""}`;
      if (sp._type !== type) { sp.ty.textContent = type; sp._type = type; sp.tw = 0; }
      sp.el.classList.toggle("on", on > 0);
      sp.el.classList.toggle("trig", trig > 0);
    }
    const cand = this._spots.filter((sp) => !sp.stair && !sp.group && !sp.badge && st[sp.d.entity]).map((sp) => {
      const base = cleanName(st[sp.d.entity], sp.d);
      return { sp, base, short: stripFloor(base) };
    });
    const count = (key) => cand.reduce((m, c) => (m[c[key]] = (m[c[key]] || 0) + 1, m), {});
    const shortN = count("short");
    for (const c of cand) c.final = shortN[c.short] > 1 ? c.base : c.short;
    const finalN = count("final");
    for (const c of cand) {
      if (finalN[c.final] > 1 && c.sp.d.room && !c.final.includes(c.sp.d.room)) c.final = `${c.sp.d.room}${c.final}`;
      c.sp._label = clip(c.final);
    }
    for (const sp of this._spots) {
      const { el, ic, d, stair } = sp;
      if (stair || sp.group || sp.badge) continue;
      const s = st[d.entity];
      el.classList.toggle("missing", !s);
      if (!s) continue;
      const name = sp._label || cleanName(s, d);
      let type = typeText(s, d);
      let icon = iconFor(s, d);
      if (VALUE_KINDS.includes(d.kind)) {
        const v = parseFloat(s.state);
        const unit = d.kind === "temp" ? "°C" : d.kind === "hum" ? "%" : ` ${s.attributes.unit_of_measurement || ""}`;
        const label = d.kind === "temp" ? "溫度" : d.kind === "hum" ? "濕度" : "數值";
        type = `${label} ${isNaN(v) ? "--" : (d.kind === "temp" ? v.toFixed(1) : Math.round(v))}${unit}`;
        icon = d.kind === "hum" ? "mdi:water-percent" : d.kind === "temp" ? "mdi:thermometer" : (icon === "mdi:circle-small" ? "mdi:molecule" : icon);
        if (!isNaN(v) && (d.kind === "temp" || d.kind === "hum")) {          // colour by comfort band
          const col = d.kind === "temp" ? tempColor(v) : humColor(v);
          if (sp._col !== col) { sp.el.querySelector(".ic").style.background = col; sp.el.querySelector(".ic").style.color = "#111"; sp.ty.style.color = col; sp._col = col; }
        }
      }
      if (d.kind === "doorlock") icon = s.state === "on" ? "mdi:lock-open-variant" : "mdi:lock";
      if (d.kind === "printer") {
        const ink = ["black", "cyan", "magenta", "yellow"].map((c, i) => `${"KCMY"[i]}${Math.round(parseFloat(st[`${d.entity}_${c}`]?.state) || 0)}`).join(" ");
        type = `${({ idle: "待機", printing: "列印中", unavailable: "離線", unknown: "未知" })[s.state] || s.state} · ${ink}%`;
        icon = "mdi:printer";
      }
      if (d.kind === "ap") {
        const up = s.state === "connected";
        icon = /switch/.test(d.entity) ? (up ? "mdi:switch" : "mdi:lan-disconnect") : up ? "mdi:wifi" : "mdi:wifi-off";
        const col = up ? "#2f8cff" : "#ff5a4f";                              // blue wifi badge, red when down
        if (sp._col !== col) { const ic0 = sp.el.querySelector(".ic"); ic0.style.background = col; ic0.style.color = "#fff"; sp._col = col; }
        type = `${/udm/.test(d.entity) ? "主機" : /switch/.test(d.entity) ? "交換器" : "分享器"} · ${up ? "已連線" : ({ disconnected: "離線", heartbeat_missed: "失聯", upgrading: "更新中" })[s.state] || s.state}`;
      }
      if (d.kind === "charger") {
        icon = "mdi:ev-station";
        const ci = chargerInfo(st);
        type = `充電樁 · ${ci.label}${ci.power}`;
      }
      if (sp._name !== name || sp._type !== type) { sp.nm.textContent = name; sp.ty.textContent = type; sp._name = name; sp._type = type; sp.tw = 0; }
      if (sp._icon !== icon) { ic.setAttribute("icon", icon); sp._icon = icon; }
      const on = d.kind === "charger" ? ["charging", "done", "plugged"].includes(chargerInfo(st).key)
        : d.kind === "ap" ? s.state === "connected"
        : ["on", "open", "opening", "unlocked", "heat", "cool", "playing"].includes(s.state);
      const sensorKind = ["motion", "person", "safety", "doorlock", "ap"].includes(d.kind);
      el.classList.toggle("on", on && !sensorKind);
      el.classList.toggle("trig", on && (d.kind === "motion" || d.kind === "person" || d.kind === "doorlock"));
      el.classList.toggle("alert", on && d.kind === "safety");
    }
    Object.values(this._groups).forEach((g) => {
      for (const [eid, door] of Object.entries(g.doors || {})) {
        const s = st[eid];
        const pos = s?.attributes?.current_position;
        const open = pos != null ? pos / 100 : ["open", "opening"].includes(s?.state) ? 1 : 0;
        door.userData.target = Math.max(0.1, 1 - open * 0.9);          // animated in _tickFlow
        if (door.userData.cur == null) door.userData.cur = door.scale.y = door.userData.target;
      }
      for (const [eid, h] of Object.entries(g.hinged || {})) {
        h.target = st[eid]?.state === h.when ? h.theta * 0.94 : 0;
      }
      for (const [eid, sn] of Object.entries(g.sensors || {})) {
        const on = st[eid]?.state === "on" || st[eid]?.state === "recording";
        sn.g.visible = !!st[eid];
        if (sn.fan) {
          sn.fan.visible = !!st[eid];
          if (sn.d.kind === "motion") {                      // grey while nothing is detected, red only when triggered
            sn.fan.material.color.setHex(on ? 0xff3b30 : 0x8a8f98);
            sn.fan.material.opacity = on ? 0.38 : 0.1;
            sn.arrowMat?.color.setHex(on ? 0xff3b30 : 0x8a8f98);
          }
        }
      }
      for (const [eid, ap] of Object.entries(g.aps || {})) {
        const up = st[eid]?.state === "connected";
        ap.up = up;
        ap.led.color.setHex(up ? 0x3d9bff : 0xff3b30);
        ap.wifi.visible = up;
      }
      for (const [eid, ch] of Object.entries(g.chargers || {})) {
        const ci = chargerInfo(st);
        const color = ci.key === "error" ? 0xe53935 : ci.key === "done" ? 0x4caf50 : ci.key === "charging" ? 0x2f9bff
          : ci.key === "plugged" ? 0x5ec8e8 : 0x777c85;                      // red / green / blue / light blue / grey
        ch.cableMat.color.setHex(color);
        ch.led.color.setHex(color);
        const plugged = ci.plugged || ci.key === "charging" || ci.key === "done" || ci.key === "plugged";
        const show = plugged || ci.key === "error";
        if (ch.cabPlug) ch.cabPlug.visible = show && !!ch.curve;
        if (ch.portDot) ch.portDot.visible = show;
        ch.cabHang.visible = !show || !ch.curve;
        ch.flowing = ci.key === "charging" && !!ch.curve;
        for (const p of ch.pulses) p.visible = ch.flowing;
      }
      for (const [eid, mat] of Object.entries(g.fixtures || {})) {
        const s = st[eid], on = s?.state === "on", a = s?.attributes || {};
        let hex = 0xffd9a0;
        if (on && a.rgb_color) hex = (a.rgb_color[0] << 16) | (a.rgb_color[1] << 8) | a.rgb_color[2];
        mat.emissive.setHex(on ? hex : 0x000000);
        mat.color.setHex(on ? 0xffffff : 0x9aa0a8);
      }
      for (const [eid, mesh] of Object.entries(g.decals)) {
        const s = st[eid];
        const on = s && s.state === "on";
        const a = s?.attributes || {};
        let hex = 0xffd9a0, op = on ? 0.85 : 0;
        if (on && a.rgb_color) hex = (a.rgb_color[0] << 16) | (a.rgb_color[1] << 8) | a.rgb_color[2];
        else if (on && a.hs_color) {
          const c = new T.Color(); c.setHSL(a.hs_color[0] / 360, 1, 1 - a.hs_color[1] / 200); hex = c.getHex();
        }
        if (on && a.brightness != null) op = 0.25 + 0.75 * (a.brightness / 255);
        mesh.material.color.setHex(hex);
        mesh.material.opacity = op;
      }
    });
    for (const pr of this._persons || []) {
      const home = st[`binary_sensor.at_home_${pr.p.id}`]?.state === "on";
      const loc = st[`sensor.at_home_${pr.p.id}_location`]?.state;
      const m = home && this._cfg.locations?.[loc];
      pr.cur = m ? { floor: m.floor, x: m.x + (pr.i - 1.5) * 26, y: m.y + (pr.i % 2) * 20 } : null;
      const t = home ? (loc && !["unknown", "unavailable"].includes(loc) ? loc : "在家") : "離家";
      if (pr._t !== t) { pr.el.querySelector(".ty").textContent = t; pr._t = t; pr.tw = 0; }
    }
    this._dirty = true;
  }

  _tickFlow() {
    const t = performance.now() / 1000;
    const dt = Math.min(0.1, t - (this._tPrev || t)); this._tPrev = t;
    for (const g of Object.values(this._groups)) {
      if (!g.group.visible) continue;
      for (const door of Object.values(g.doors || {})) {            // roller door rolls up / down over ~1.5 s
        const u = door.userData;
        if (u.target == null || Math.abs(u.cur - u.target) < 0.002) continue;
        u.cur += Math.sign(u.target - u.cur) * Math.min(Math.abs(u.target - u.cur), dt * 0.6);
        door.scale.y = u.cur; this._dirty = true;
      }
      for (const h of Object.values(g.hinged || {})) {              // front door swings
        if (Math.abs(h.cur - h.target) < 0.002) continue;
        h.cur += (h.target - h.cur) * Math.min(1, dt * 3.2);
        h.leaf.rotation.y = h.cur; this._dirty = true;
      }
    }
    for (const g of Object.values(this._groups)) {
      if (!g.group.visible) continue;
      for (const ch of Object.values(g.chargers || {})) {
        if (!ch.flowing) continue;
        ch.pulses.forEach((p, i) => p.position.copy(ch.curve.getPoint((t * 0.4 + i / ch.pulses.length) % 1)));
        this._dirty = true;
      }
    }
  }

  _resize() {
    if (!this._ready) return;
    const wrap = this.shadowRoot.querySelector(".wrap");
    const w = wrap.clientWidth, h = wrap.clientHeight;
    if (!w || !h) return;
    const small = w < 900;                                   // e.g. iPad mini landscape: smaller labels and buttons
    if (small !== this._small) {
      this._small = small;
      wrap.classList.toggle("sm", small);
      for (const sp of this._spots || []) sp.tw = 0;
      for (const pr of this._persons || []) pr.tw = 0;
      this._barDirty = true;
    }
    this._renderer.setSize(w, h, false);
    this._cam.aspect = w / h;
    this._cam.updateProjectionMatrix();
    this._dirty = true;
  }

  _loop() {
    if (this._looping) { this._stop = false; return; }     // 迴圈還在跑：只取消待處理的停止
    this._looping = true;
    this._stop = false;
    const v = new this._T.Vector3();
    const tick = () => {
      if (this._stop) { this._looping = false; return; }
      requestAnimationFrame(tick);
      this._controls.update();
      this._tickFlow();
      if (!this._dirty) return;
      this._dirty = false;
      this._renderer.render(this._scene, this._cam);
      const wrap = this.shadowRoot.querySelector(".wrap");
      const w = wrap.clientWidth, h = wrap.clientHeight;
      if (!this._topBar || this._barDirty) {
        const bars = [".tools", ".zones"].map((q) => this.shadowRoot.querySelector(q)).filter((e) => e && e.style.visibility !== "hidden" && e.offsetHeight);
        const wr = wrap.getBoundingClientRect();
        this._topBar = Math.max(54, ...bars.map((e) => e.getBoundingClientRect().bottom - wr.top + 8));
        this._barDirty = false;
      }
      const items = [];
      for (const sp of this._spots) {
        if (sp.el.classList.contains("hide") || sp.el.classList.contains("missing")) continue;
        const hz = sp.d.z ?? (sp.d.kind === "camera" ? 34 : sp.d.kind === "motion" && sp.d.yaw != null ? 28 : 4);
        v.set(sp.d.x - sp.g.fl.width / 2, hz, sp.d.y - sp.g.fl.height / 2).add(sp.g.group.position).project(this._cam);
        if (v.z >= 1) { sp.el.style.display = "none"; continue; }
        sp.el.style.display = "";
        items.push({ sp, x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h });
      }
      const allFloors = this._floor === "全棟";
      for (const pr of this._persons || []) {
        const g = pr.cur && this._groups[pr.cur.floor];
        if (!g || !(allFloors || pr.cur.floor === this._floor) || pr.el.classList.contains("hide") ||
          !this._inZone(pr.cur.x, pr.cur.y)) { pr.el.style.display = "none"; continue; }
        v.set(pr.cur.x - g.fl.width / 2, 20, pr.cur.y - g.fl.height / 2).add(g.group.position).project(this._cam);
        pr.el.style.display = v.z < 1 ? "" : "none";
        if (v.z < 1) items.push({ sp: pr, x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h });
      }
      // place each label near its point: try short heights first, then slide sideways (elbow line)
      items.sort((a, b) => b.y - a.y);
      const placed = [];
      const hit = (r) => placed.some((p) => r.x < p.x + p.w && r.x + r.w > p.x && r.y < p.y + p.h && r.y + r.h > p.y);
      const lines = [];
      const topLimit = this._topBar || 54;                    // keep labels clear of the tool/zone buttons
      if (allFloors) {                                        // whole house: floor badges in a column on the left, stair lights on the right
        const cols = { L: items.filter((it) => it.sp.badge), R: items.filter((it) => it.sp.always) };
        for (const [side, col] of Object.entries(cols)) {
          // fixed top-to-bottom order: stair lights from the roof down to the garage, floors 5F..1F
          const STAIR_ORDER = [/頂樓/, /^四樓/, /三四樓/, /^三樓/, /二三樓/, /車庫/];
          const rank = (it) => side === "L" ? -Object.keys(this._cfg.floors).indexOf(it.sp.badge)
            : (((i) => (i < 0 ? 99 : i))(STAIR_ORDER.findIndex((re) => re.test(it.sp.d.name || ""))));
          col.sort((a, b) => rank(a) - rank(b) || a.y - b.y);
          const boxes = col.map((it) => {
            const sp = it.sp;
            if (!sp.tw) { sp.el.classList.remove("compact"); sp.tw = sp.tag.offsetWidth || 90; sp.th = sp.tag.offsetHeight || 36; }
            const compact = !this._labels;
            if (sp.el.classList.contains("compact") !== compact) sp.el.classList.toggle("compact", compact);
            return { it, tw: compact ? 36 : sp.tw, th: compact ? 36 : sp.th };
          });
          let y = topLimit;
          for (const b of boxes) { b.y = Math.max(y, b.it.y - b.th / 2); y = b.y + b.th + 6; }
          const over = y - 6 - (h - 8);                       // ran off the bottom: slide the column up (not past the top bar)
          if (over > 0) for (const b of boxes) b.y = Math.max(topLimit, b.y - over);
          for (const b of boxes) {
            const { it, tw, th } = b, sp = it.sp;
            const lx = side === "L" ? 8 : w - tw - 8;
            placed.push({ x: lx - 3, y: b.y - 3, w: tw + 6, h: th + 6 });
            sp.el.style.transform = `translate(${it.x}px, ${it.y}px)`;
            sp.tag.style.transform = `translate(${lx - it.x}px, ${b.y - it.y}px)`;
            const ly = b.y + th / 2, ex = side === "L" ? lx + tw : lx, mx = (it.x + ex) / 2;
            lines.push(`<polyline points="${it.x},${it.y} ${mx},${it.y} ${mx},${ly} ${ex},${ly}"/>`);
          }
        }
        for (let i = items.length - 1; i >= 0; i--) if (items[i].sp.badge || items[i].sp.always) items.splice(i, 1);
      }
      for (const it of items) {
        const sp = it.sp;
        if (!sp.tw) { sp.el.classList.remove("compact"); sp.tw = sp.tag.offsetWidth || 90; sp.th = sp.tag.offsetHeight || 36; }
        const tryPlace = (tw, th, levels) => {
          const step = tw * 0.5 + 10;
          for (const lvl of levels) for (const k of [0, 1, -1, 2, -2, 3, -3]) {
            const dy = 16 + lvl * 24, dx = k * step;
            const r = { x: it.x + dx - tw / 2 - 3, y: it.y - dy - th - 3, w: tw + 6, h: th + 6 };
            if (r.x < 2 || r.x + r.w > w - 2 || r.y < topLimit) continue;
            if (!hit(r)) return { dx, dy, r };
          }
          return null;
        };
        const labelsOn = this._labels;
        let best = labelsOn ? tryPlace(sp.tw, sp.th, [0, 1, 2, 3]) : null;
        let compact = !best;
        if (!best) best = tryPlace(36, 36, [0, 1, 2, 3, 4]);           // crowded: icon-only bubble
        if (!best) {                                                   // no room above: hang the bubble below the point
          const dy = -(36 + 8);
          best = { dx: 0, dy, r: { x: it.x - 18, y: it.y + 8, w: 36, h: 36 } };
          compact = true;
        }
        if (sp.el.classList.contains("compact") !== compact) sp.el.classList.toggle("compact", compact);
        const tw = compact ? 36 : sp.tw, th = compact ? 36 : sp.th;
        placed.push(best.r);
        sp.el.style.transform = `translate(${it.x}px, ${it.y}px)`;
        sp.tag.style.transform = `translate(${best.dx - tw / 2}px, ${-best.dy - th}px)`;
        const ly = it.y - best.dy - th / 2;                     // connector: up, then across to the label edge
        const pts = best.dx === 0 ? `${it.x},${it.y} ${it.x},${it.y - best.dy}`
          : `${it.x},${it.y} ${it.x},${ly} ${it.x + best.dx + (best.dx > 0 ? -tw / 2 : tw / 2)},${ly}`;
        lines.push(`<polyline points="${pts}"/>`);
      }
      if (this._links) this._links.innerHTML = lines.join("");
    };
    tick();
  }
}

class FloorplanV4Sidebar extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(cfg) {
    this._cfg = cfg;
    this._floor = getFloor({ floors: Object.fromEntries((cfg.floors || ["1F", "2F", "3F", "4F", "5F"]).map((f) => [f, 1])), default: cfg.default || "2F" });
    const floors = [...(cfg.floors || ["1F", "2F", "3F", "4F", "5F"]), "全棟"];
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .box { background:var(--card-background-color,#1c1c1e); border-radius:16px; padding:12px; box-sizing:border-box;
               height:calc(100vh - 88px); height:${cfg.height || "calc(100dvh - 88px)"}; display:flex; flex-direction:column; overflow:hidden; }
        .top { display:flex; align-items:baseline; gap:10px; }
        .time { font:300 34px sans-serif; color:var(--primary-text-color); letter-spacing:1px; }
        .date { font:12px sans-serif; color:var(--secondary-text-color); margin:0 0 8px; }
        .nav { display:grid; grid-template-columns:repeat(3,1fr); gap:6px; }
        .nav button { border:0; border-radius:10px; padding:9px 4px; background:rgba(120,120,128,.14);
                      color:var(--primary-text-color); font:600 14px sans-serif; cursor:pointer; }
        .nav button.on { background:rgba(255,185,0,.2); color:#FFB900; }
        .h { font:12px sans-serif; color:var(--secondary-text-color); margin:10px 4px 5px; }
        .narrow .time { font-size:26px; } .narrow .date { display:none; }
        .narrow .box { padding:8px; } .narrow .wx { padding:6px 8px; gap:8px; --mdc-icon-size:24px; }
        .narrow .wx .t { font-size:20px; } .narrow .wx .c { font-size:10.5px; margin-top:2px; }
        .narrow .h { margin:7px 2px 4px; font-size:11px; }
        .narrow .row2 { padding:5px 8px; gap:6px; --mdc-icon-size:18px; } .narrow .row2 .n { font-size:12px; } .narrow .row2 .v { font-size:10.5px; }
        .narrow .nav { gap:4px; margin-top:6px; } .narrow .nav button { padding:7px 2px; font-size:12px; border-radius:8px; }
        .narrow .ppl { grid-template-columns:1fr; gap:0; } .narrow .ppl .row { padding:2px 2px; }
        .wx { display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:12px; background:rgba(79,195,247,.1);
              cursor:pointer; --mdc-icon-size:30px; color:#ffd36b; }
        .wx .t { font:300 24px sans-serif; color:var(--primary-text-color); line-height:1; }
        .wx .c { font:12px sans-serif; color:var(--secondary-text-color); margin-top:4px; }
        .sec { display:flex; flex-direction:column; gap:5px; }
        .box > * { flex-shrink:0; } .box > .ppl { flex:0 1 auto; }
        .nav { margin-top:10px; }
        .row2 { display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:10px; cursor:pointer;
                background:rgba(120,120,128,.14); --mdc-icon-size:20px; }
        .row2 .n { flex:1; font:600 13px sans-serif; color:var(--primary-text-color); }
        .row2 .v { font:600 12px sans-serif; color:var(--secondary-text-color); }
        .row2.ok ha-icon { color:#43a047; } .row2.warn ha-icon { color:#FFB900; } .row2.bad { background:rgba(229,57,53,.25); }
        .row2.bad ha-icon { color:#e53935; }
        .ppl { display:grid; grid-template-columns:1fr 1fr; gap:2px 6px; align-content:start; min-height:0; overflow:hidden; }
        .ppl .row { padding:3px 2px; gap:7px; } .ppl .av { width:28px; height:28px; font-size:12px; }
        .ppl .nm { font-size:13px; } .ppl .lc { font-size:11px; }
        ${PEOPLE_CSS}
      </style>
      <div class="box"><div class="top"><div class="time"></div></div><div class="date"></div>
        <div class="wx"></div>
        <div class="h">保全狀態</div><div class="sec"></div>
        <div class="nav">${floors.map((f) => `<button data-f="${f}">${f === "全棟" ? "全棟" : f}</button>`).join("")}</div>
        <div class="h">在家成員</div><div class="ppl"></div></div>`;
    this.shadowRoot.querySelector(".nav").addEventListener("click", (e) => {
      const f = e.target.closest("button")?.dataset.f;
      if (f) { this._floor = f; setFloor(f); this._mark(); }
    });
    this._mark();
    this._clock();
  }
  set hass(h) {
    this._hass = h;
    const host = this.shadowRoot.querySelector(".ppl");
    if (host) host.innerHTML = peopleHtml(h, this._cfg.people || DEFAULT_PEOPLE);
    const root = this.shadowRoot;
    const wxId = this._cfg.weather || "weather.homeweather_zhu_nan_zhen";
    const wx = h.states[wxId];
    const WX = { sunny: ["mdi:weather-sunny", "晴"], "clear-night": ["mdi:weather-night", "晴朗夜"], cloudy: ["mdi:weather-cloudy", "多雲"],
      partlycloudy: ["mdi:weather-partly-cloudy", "晴時多雲"], rainy: ["mdi:weather-rainy", "雨"], pouring: ["mdi:weather-pouring", "大雨"],
      "lightning-rainy": ["mdi:weather-lightning-rainy", "雷雨"], lightning: ["mdi:weather-lightning", "雷"], fog: ["mdi:weather-fog", "霧"],
      windy: ["mdi:weather-windy", "強風"], snowy: ["mdi:weather-snowy", "雪"] };
    const box = root.querySelector(".wx");
    if (box && wx) {
      const [ic, txt] = WX[wx.state] || ["mdi:weather-partly-cloudy", wx.state];
      const a = wx.attributes;
      box.innerHTML = `<ha-icon icon="${ic}"></ha-icon><div><div class="t">${a.temperature ?? "--"}°</div>
        <div class="c">${txt} · 濕度 ${a.humidity ?? "--"}%</div></div>`;
      box.onclick = () => this._more(wxId);
    }
    const sec = root.querySelector(".sec");
    if (sec) {
      const AL = { disarmed: ["已解除", "warn"], armed_home: ["在家警戒", "ok"], armed_away: ["離家警戒", "ok"], armed_night: ["夜間警戒", "ok"],
        armed_vacation: ["度假警戒", "ok"], arming: ["啟動中", "warn"], pending: ["倒數中", "warn"], triggered: ["警報中！", "bad"] };
      const rows = [];
      const al = h.states[this._cfg.alarm || "alarm_control_panel.54ef44cf58f9_alarm"];
      if (al) { const [t, c] = AL[al.state] || [al.state, "warn"]; rows.push([al.entity_id, "mdi:shield-home", "保全系統", t, c]); }
      for (const [id, icon, name] of this._cfg.security || [["input_boolean.er_lou_men_suo_tong_bu_kai_guan", "mdi:lock", "二樓門鎖"],
        ["cover.garage", "mdi:garage-variant", "車庫鐵門"], ["input_boolean.5f_security_temp_disable", "mdi:shield-off", "五樓保全暫解"]]) {
        const st = h.states[id];
        if (!st) continue;
        const isDoor = id === "input_boolean.er_lou_men_suo_tong_bu_kai_guan";
        const txt = isDoor ? (st.state === "on" ? "已開鎖" : "已上鎖")
          : { locked: "已上鎖", unlocked: "未上鎖", open: "開啟", closed: "關閉", opening: "開啟中", closing: "關閉中", on: "啟用", off: "未啟用" }[st.state] || st.state;
        const cls = isDoor ? (st.state === "on" ? "bad" : "ok") : ["unlocked", "open", "opening"].includes(st.state) ? "bad" : st.state === "on" ? "warn" : "ok";
        rows.push([id, isDoor ? (st.state === "on" ? "mdi:lock-open-variant" : "mdi:lock") : st.state === "unlocked" ? "mdi:lock-open-variant" : icon, name, txt, cls]);
      }
      sec.innerHTML = rows.map(([id, ic, n, v, c]) => `<div class="row2 ${c}" data-id="${id}"><ha-icon icon="${ic}"></ha-icon>
        <span class="n">${n}</span><span class="v">${v}</span></div>`).join("");
      sec.onclick = (e) => { const r = e.target.closest(".row2"); if (r) this._more(r.dataset.id); };
    }
  }
  _more(entityId) {
    this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId } }));
  }
  _mark() {
    this.shadowRoot.querySelectorAll(".nav button").forEach((b) => b.classList.toggle("on", b.dataset.f === this._floor));
  }
  _clock() {
    const t = this.shadowRoot.querySelector(".time"), d = this.shadowRoot.querySelector(".date");
    const upd = () => {
      const n = new Date();
      t.textContent = n.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false });
      d.textContent = n.toLocaleDateString("zh-TW", { month: "long", day: "numeric", weekday: "long" });
    };
    upd();
    clearInterval(this._iv);
    clearTimeout(this._ivAlign);
    // tick exactly on the minute boundary, then every minute
    this._ivAlign = setTimeout(() => { upd(); this._iv = setInterval(upd, 60000); }, 60000 - (Date.now() % 60000) + 50);
  }
  connectedCallback() {
    this._evt = (e) => { this._floor = e.detail; this._mark(); };
    window.addEventListener(EVT, this._evt);
    if (this.shadowRoot.querySelector(".time")) this._clock();          // HA detaches cards on view switch: restart the clock
    this._vis = () => { if (!document.hidden) this._clock(); };
    document.addEventListener("visibilitychange", this._vis);
    this._ro = new ResizeObserver(() => this.shadowRoot.querySelector(".box")?.classList.toggle("narrow", this.clientWidth < 250));
    this._ro.observe(this);
  }
  disconnectedCallback() {
    window.removeEventListener(EVT, this._evt); clearInterval(this._iv); this._ro?.disconnect();
    document.removeEventListener("visibilitychange", this._vis);
  }
  getCardSize() { return 6; }
}

if (!customElements.get("floorplan-v4-3d")) {
  customElements.define("floorplan-v4-3d", FloorplanV43D);
  customElements.define("floorplan-v4-sidebar", FloorplanV4Sidebar);
  customElements.define("floorplan-v4-people", FloorplanV4People);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: "floorplan-v4-3d", name: "Floorplan V4 3D" });
  window.customCards.push({ type: "floorplan-v4-sidebar", name: "Floorplan V4 sidebar" });
}

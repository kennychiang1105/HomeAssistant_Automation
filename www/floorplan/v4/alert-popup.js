/* Smart Home Global Alert Popup (V4.2.0 / UI4.0-beta8)
 * Modern responsive modal for:
 *   1. Earthquake Early Warning (EEW: input_text.line_eew_remote_level / seconds)
 *   2. Local Disaster Alerts (sensor.disaster - filtered to 竹南/苗栗/新竹 or national emergency)
 *   3. Felt Earthquake Reports (sensor.earthquake)
 * Features:
 *   - Active across all views of the Smart Home dashboard (/lovelace-smart/*)
 *   - Color-coded region badges: 竹南 (Red), 苗栗 (Blue), 新竹 (Green) + collapsed other counties
 *   - Strict anti-overflow CSS (min-width:0, overflow-wrap:anywhere, dedicated wrapped time row)
 *   - 30s auto-close countdown progress bar + manual close (✕, button, backdrop, Esc)
 *   - beta8: only local orange/red lamps, evacuation, tsunami, national alarms (water repair etc. no longer pop);
 *            content older than 1 hour and unread is not shown (initial load and live changes); dedupe by hash of the full text;
 *            a new EEW replaces the one on screen; also runs on the standalone kiosk page (window.__kioskHass)
 */
(() => {
  if (window.__smartAlertPopupV420) return;
  window.__smartAlertPopupV420 = true;

  const STORAGE_KEY = "smart_alert_popup_seen_v420";
  const AUTO_CLOSE_SEC = 30;
  const FRESH_MS = 3600 * 1000;                  // beta8: older than 1 hr and unread -> no popup (initial load and live changes)
  const EEW_LOAD_WINDOW_MS = 90 * 1000;          // 90 sec on initial load for EEW

  const loadSeen = () => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") || {};
    } catch (e) {
      return {};
    }
  };
  const markSeen = (key) => {
    try {
      const seen = loadSeen();
      seen[key] = Date.now();
      // Keep only last 60 entries to avoid bloat
      const entries = Object.entries(seen).sort((a, b) => b[1] - a[1]).slice(0, 60);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(entries)));
    } catch (e) { /* ignore */ }
  };
  const isSeen = (key) => !!loadSeen()[key];

  // beta8: dedupe by a hash of the whole text (the old first-120-characters key hid later changes of the same message)
  const hashStr = (str) => {
    let h1 = 5381, h2 = 52711;
    const t = String(str ?? "");
    for (let i = 0; i < t.length; i++) {
      const c = t.charCodeAt(i);
      h1 = ((h1 * 33) ^ c) >>> 0;
      h2 = ((h2 * 31) + c) >>> 0;
    }
    return `${h1.toString(36)}${h2.toString(36)}${t.length}`;
  };
  // V4.2.2：災害訊息的「在地內容簽章」（燈號＋竹南／苗栗／新竹地區＋條件），和 03 自動化的 disaster_sig 一致；其他縣市或時段文字變動不算新訊息
  const disasterSig = (raw) => {
    const s0 = String(raw ?? "").trim();
    const re = /([^，。()（）\n]*?局部地區)有([^()（）\n]*?)[(（](紅色|橙色|黃色)燈號[)）]/g;
    const sig = [];
    let m;
    while ((m = re.exec(s0)) !== null) {
      const p = parseAlertRegion(m[1]);
      if (p.targets.length) sig.push(`${m[3]}:${p.targets.map((t) => t.name).sort().join("/")}:${m[2].trim()}`);
    }
    return sig.length ? sig.sort().join("|") : s0.replace(/\s+/g, "").slice(0, 240);
  };
  const getHass = () => window.__kioskHass || document.querySelector("home-assistant")?.hass;
  const isFresh = (age) => Number.isFinite(age) && age <= FRESH_MS && age > -5 * 60 * 1000;
  // age of the disaster notice: sensor.disaster_last_valid_update (stable across reloads), else the entity's own update time
  const disasterAgeMs = (hass, disSt, now) => {
    const raw = hass.states["sensor.disaster_last_valid_update"]?.state;
    const t = raw && !["unknown", "unavailable", "none", "None"].includes(raw) ? new Date(raw).getTime() : NaN;
    if (Number.isFinite(t)) return now - t;
    const u = disSt?.last_updated ? new Date(disSt.last_updated).getTime() : NaN;
    return Number.isFinite(u) ? now - u : Infinity;
  };
  // age of an earthquake report from the time written in the report itself (last_updated resets on every HA reload)
  const eqReportAgeMs = (eqSt, now) => {
    const s = String(eqSt?.state ?? "").replace(/^.*收到以下中央氣象(?:局|署)訊息[:：]\s*/, "").trim();
    const m = s.match(/^(\d{1,2})\/(\d{1,2})\s*(\d{1,2}):(\d{2})/);
    if (!m) return Infinity;
    const d0 = new Date(now);
    let t = new Date(d0.getFullYear(), parseInt(m[1], 10) - 1, parseInt(m[2], 10), parseInt(m[3], 10), parseInt(m[4], 10)).getTime();
    if (t - now > 24 * 3600 * 1000) t = new Date(d0.getFullYear() - 1, parseInt(m[1], 10) - 1, parseInt(m[2], 10), parseInt(m[3], 10), parseInt(m[4], 10)).getTime();
    return now - t;
  };

  const isSmartDashboard = () => {
    if (window.__kioskHass) return true;
    const p = location.pathname || "";
    if (p.startsWith("/lovelace-smart")) return true;
    return !!document.querySelector("floorplan-v4-3d, floorplan-v4-sidebar, floorplan-v4-card");
  };

  const escHtml = (s) =>
    String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

  // Parse a lamp region string into { time, targets: [{name, col, bg, bd, dot}], others: [] }
  const parseAlertRegion = (reg) => {
    const r0 = String(reg || "").replace(/局部地區$/, "").trim();
    const parts = r0.split("、");
    let timePrefix = "";
    const targets = [];
    const others = [];
    for (const raw of parts) {
      let item = raw.trim();
      const mTime = item.match(/^(.*(?:上午|下午|晚上|中午|晨|夜))\s*(.*)$/);
      if (mTime) {
        if (!timePrefix) timePrefix = mTime[1].trim();
        item = mTime[2].trim();
      }
      if (!item) continue;
      if (item.includes("竹南")) {
        targets.push({ name: item, col: "#DC2626", bg: "#FEE2E2", bd: "#FCA5A5", dot: "🔴" });
      } else if (item.includes("苗栗")) {
        targets.push({ name: item, col: "#2F80ED", bg: "#EFF6FF", bd: "#BFDBFE", dot: "🔵" });
      } else if (item.includes("新竹")) {
        targets.push({ name: item, col: "#16A34A", bg: "#F0FDF4", bd: "#BBF7D0", dot: "🟢" });
      } else {
        others.push(item);
      }
    }
    return { time: timePrefix, targets, others };
  };

  // Parse sensor.disaster and check if it affects 竹南 / 苗栗 / 新竹 (or is national emergency)
  const parseDisasterAlert = (rawMsg) => {
    if (!rawMsg || ["unknown", "unavailable", "none", "None"].includes(rawMsg)) return null;
    const s0 = String(rawMsg)
      .replace(/^(?:天氣告知系統)?收到以下政府災害訊息[:：]?\s*/, "")
      .replace(/^政府發布(?:緊急)?疏散避難警報[:：]?\s*/, "")
      .trim();
    if (!s0 || /演練|演習|模擬/.test(s0)) return null;
    if (/地震/.test(s0) && !/海嘯/.test(s0)) return null;

    const parts = s0.split("二、注意");
    const sMain = (parts[0] || "").replace(/^[一1]、(?:概述)?[:：\s]*/, "").trim();
    const sNote = parts.length > 1
      ? parts[1].replace(/^[(（]警戒[)）]事項[：:\s]*/, "").replace(/^事項[：:\s]*/, "").trim()
      : "";

    const lampRe = /([^，。()（）\n]*?局部地區)有([^()（）\n]*?)[(（](紅色|橙色|黃色)燈號[)）]/g;
    const items = [];
    let m;
    while ((m = lampRe.exec(sMain)) !== null) {
      const parsed = parseAlertRegion(m[1]);
      items.push({ reg: m[1].trim(), cond: m[2].trim(), lamp: m[3].trim(), parsed });
    }

    // beta8: only local orange/red lamps, evacuation, tsunami, debris flow, typhoon warning, extreme rain and national alarms pop up
    //        (yellow lamps, water repair and other notices that merely mention the area do not)
    let hasLocal = false;
    if (items.length > 0) {
      hasLocal = items.some((it) => (it.lamp === "紅色" || it.lamp === "橙色") && it.parsed.targets.length > 0);
    } else {
      const national = /國家級警報|空襲|飛彈/.test(sMain);
      const severe = /疏散|撤離|海嘯|土石流|堰塞|颱風(?:海上|陸上)?警報|大豪雨|超大豪雨/.test(sMain);
      hasLocal = national || (severe && /竹南|苗栗|新竹/.test(sMain));
    }
    if (!hasLocal) return null;

    let cardTitle = "氣象與災害告警";
    let badge = "災防通知";
    let themeColor = "#F59E0B";
    let headerBg = "linear-gradient(135deg, #EA580C, #D97706)";
    let icon = "mdi:weather-Pouring";

    if (/疏散|撤離/.test(s0)) {
      cardTitle = "緊急疏散避難警報"; badge = "疏散警報"; themeColor = "#DC2626";
      headerBg = "linear-gradient(135deg, #DC2626, #B91C1C)"; icon = "mdi:bullhorn-outline";
    } else if (/海嘯/.test(s0)) {
      cardTitle = "海嘯警報"; badge = "海嘯警報"; themeColor = "#DC2626";
      headerBg = "linear-gradient(135deg, #DC2626, #B91C1C)"; icon = "mdi:tsunami";
    } else if (/土石流|堰塞/.test(s0)) {
      cardTitle = "土石流災害警戒"; badge = "土石流警戒"; themeColor = "#DC2626";
      headerBg = "linear-gradient(135deg, #DC2626, #B91C1C)"; icon = "mdi:landslide-outline";
    } else if (/紅色/.test(s0)) {
      cardTitle = "氣象與災害告警"; badge = "紅色燈號"; themeColor = "#DC2626";
      headerBg = "linear-gradient(135deg, #DC2626, #B91C1C)"; icon = "mdi:weather-hurricane";
    } else if (/橙色/.test(s0)) {
      cardTitle = "氣象與災害告警"; badge = "橙色燈號"; themeColor = "#EA580C";
      headerBg = "linear-gradient(135deg, #EA580C, #D97706)"; icon = "mdi:weather-windy";
    } else if (/黃色/.test(s0)) {
      cardTitle = "氣象與災害告警"; badge = "黃色燈號"; themeColor = "#D97706";
      headerBg = "linear-gradient(135deg, #D97706, #CA8A04)"; icon = "mdi:weather-windy";
    } else if (/颱風/.test(s0)) {
      cardTitle = "氣象與災害告警"; badge = "颱風警報"; themeColor = "#EA580C";
      headerBg = "linear-gradient(135deg, #EA580C, #B91C1C)"; icon = "mdi:weather-hurricane";
    } else if (/豪雨|大雨/.test(s0)) {
      cardTitle = "氣象與災害告警"; badge = "豪雨特報"; themeColor = "#EA580C";
      headerBg = "linear-gradient(135deg, #2563EB, #1D4ED8)"; icon = "mdi:weather-pouring";
    } else if (/淹水|洩洪|放水/.test(s0)) {
      cardTitle = "淹水與放水警戒"; badge = "淹水警戒"; themeColor = "#EA580C";
      headerBg = "linear-gradient(135deg, #0284C7, #0369A1)"; icon = "mdi:home-flood";
    } else if (/停水|停電/.test(s0)) {
      cardTitle = "民生停供通知"; badge = "民生停供"; themeColor = "#EA580C";
      headerBg = "linear-gradient(135deg, #D97706, #B45309)"; icon = "mdi:water-off-outline";
    }

    const lead = items.length > 0 ? (sMain.split("，")[0] || "").trim() : "";
    return {
      kind: "disaster",
      cardTitle,
      badge,
      themeColor,
      headerBg,
      icon,
      lead,
      items,
      sMain,
      sNote,
      isEvac: /疏散|撤離/.test(s0),
    };
  };

  // Parse sensor.earthquake
  const parseEarthquakeReport = (rawEq) => {
    if (!rawEq || ["unknown", "unavailable", "none", "None"].includes(rawEq)) return null;
    const s = String(rawEq).replace(/^.*收到以下中央氣象(?:局|署)訊息[:：]\s*/, "").trim();
    const m = s.match(/^(\d{1,2}\/\d{1,2})\s*(\d{1,2}:\d{2})\s*(.*?)發生規模\s*([\d.]+)\s*(?:有感|小區域)?地震[，,]?\s*(.*?)。?$/);
    if (!m) return null;
    const mag = parseFloat(m[4]) || 0;
    const isMajor = mag >= 5;
    const badge = mag >= 6 ? "強震報告" : mag >= 5 ? "中強震" : mag >= 4 ? "有感地震" : "小區域地震";
    const themeColor = mag >= 6 ? "#DC2626" : mag >= 5 ? "#EA580C" : mag >= 4 ? "#D97706" : "#16A34A";
    const headerBg = mag >= 5
      ? "linear-gradient(135deg, #DC2626, #B91C1C)"
      : "linear-gradient(135deg, #EA580C, #D97706)";
    const maxInt = (m[5] || "").replace(/^最大震度/, "").trim() || "--";
    return {
      kind: "earthquake",
      cardTitle: "最新地震報告",
      badge,
      themeColor,
      headerBg,
      icon: "mdi:pulse",
      dateStr: `${m[1]} ${m[2]}`,
      location: (m[3] || "").trim(),
      mag: m[4],
      magNum: mag,
      maxInt,
      needGuide: isMajor,
    };
  };

  // Build EEW payload
  const parseEEW = (lvRaw, secRaw) => {
    const lvStr = String(lvRaw ?? "").trim();
    const secStr = String(secRaw ?? "").trim();
    if (!lvStr || ["unknown", "unavailable", "none", "None"].includes(lvStr)) return null;
    const lvNum = parseInt((lvStr.match(/\d+/) || ["0"])[0], 10) || 0;
    const secNum = parseInt((secStr.match(/\d+/) || ["0"])[0], 10) || 0;
    const lvDisp = lvStr.includes("級") ? lvStr : `${lvStr} 級`;
    const isUrgent = lvNum >= 4;
    return {
      kind: "eew",
      cardTitle: "地震預警速報",
      badge: isUrgent ? "緊急避難" : lvNum === 3 ? "有感警戒" : "輕微有感",
      themeColor: isUrgent ? "#DC2626" : "#EA580C",
      headerBg: isUrgent
        ? "linear-gradient(135deg, #DC2626, #991B1B)"
        : "linear-gradient(135deg, #EA580C, #C2410C)",
      icon: "mdi:alert-octagram",
      lvNum,
      lvDisp,
      secNum,
      actTitle: isUrgent
        ? "已啟動緊急模式與全宅廣播"
        : lvNum === 3
        ? "已啟動全宅語音廣播提醒"
        : "預警通知（未達廣播與緊急模式門檻）",
      actDesc: isUrgent
        ? "預估震度達 4 級以上，系統自動開啟全室照明並關閉危險電源。"
        : lvNum === 3
        ? "預估震度 3 級，本次啟動語音廣播提醒。"
        : "預估震度較小，請留意後續搖晃。",
      guide: "請保持冷靜，立即就地趴下、掩護、穩住並抓住桌腳，保護頭頸部！",
    };
  };

  class SmartAlertPopupHost extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._queue = [];
      this._current = null;
      this._timer = null;
      this._eewTimer = null;
      this._onKeyDown = (e) => {
        if (e.key === "Escape" && this._current) this.dismiss();
      };
    }

    connectedCallback() {
      window.addEventListener("keydown", this._onKeyDown);
    }

    disconnectedCallback() {
      window.removeEventListener("keydown", this._onKeyDown);
    }

    enqueue(item, urgent = false) {
      if (!isSmartDashboard()) return;
      if (this._current && this._current.key === item.key) return;
      if (this._queue.some((q) => q.key === item.key)) return;
      if (urgent) {
        if (this._current) {
          if (this._current.data.kind !== "eew") this._queue.unshift(this._current);   // an older EEW is simply replaced
          this._show(item);
          return;
        }
        this._queue.unshift(item);
      } else {
        this._queue.push(item);
      }
      if (!this._current) {
        this._next();
      }
    }

    _next() {
      this._clearTimers();
      if (this._queue.length === 0) {
        this._current = null;
        this.shadowRoot.innerHTML = "";
        return;
      }
      const nextItem = this._queue.shift();
      this._show(nextItem);
    }

    dismiss() {
      if (this._current) {
        markSeen(this._current.key);
      }
      this._next();
    }

    _clearTimers() {
      if (this._timer) { clearInterval(this._timer); this._timer = null; }
      if (this._eewTimer) { clearInterval(this._eewTimer); this._eewTimer = null; }
    }

    _renderBodyHtml(d) {
      if (d.kind === "eew") {
        const initSec = d.secNum > 0 ? `${d.secNum} 秒後` : "即將抵達";
        return `
          <div class="grid2">
            <div class="stat-box" style="background:#FEF2F2;border-color:#FCA5A5">
              <div class="stat-label">預估震度</div>
              <div class="stat-val" style="color:${d.themeColor}">${escHtml(d.lvDisp)}</div>
            </div>
            <div class="stat-box" style="background:#FEF2F2;border-color:#FCA5A5">
              <div class="stat-label">預計抵達</div>
              <div class="stat-val eew-sec" style="color:#111827">${escHtml(initSec)}</div>
            </div>
          </div>
          <div class="info-box">
            <div class="info-title" style="color:${d.themeColor}">🛡️ ${escHtml(d.actTitle)}</div>
            <div class="info-desc">${escHtml(d.actDesc)}</div>
          </div>
          <div class="warn-box">
            <span class="warn-ic">⚠️</span>
            <div class="warn-txt">${escHtml(d.guide)}</div>
          </div>
        `;
      }

      if (d.kind === "earthquake") {
        return `
          <div class="grid2">
            <div class="stat-box" style="background:#FFF7ED;border-color:#FDBA74">
              <div class="stat-label">地震規模</div>
              <div class="stat-val" style="color:${d.themeColor}">M ${escHtml(d.mag)}</div>
            </div>
            <div class="stat-box" style="background:#FFF7ED;border-color:#FDBA74">
              <div class="stat-label">最大震度</div>
              <div class="stat-val" style="color:#111827">${escHtml(d.maxInt)}</div>
            </div>
          </div>
          <div class="meta-list">
            <div class="meta-row">
              <span class="meta-k">發生時間</span>
              <span class="meta-v">${escHtml(d.dateStr)}</span>
            </div>
            <div class="meta-row">
              <span class="meta-k">震央位置</span>
              <span class="meta-v">${escHtml(d.location)}</span>
            </div>
          </div>
          ${d.needGuide ? `
            <div class="warn-box">
              <span class="warn-ic">⚠️</span>
              <div class="warn-txt">發生有感地震，請保持冷靜，立即就地趴下、掩護、穩住並保護頭頸部。</div>
            </div>
          ` : ""}
        `;
      }

      // kind === 'disaster'
      const lampPalette = {
        "紅色": { col: "#DC2626", bg: "#FEF2F2", bd: "#FCA5A5", dot: "🔴" },
        "橙色": { col: "#EA580C", bg: "#FFF7ED", bd: "#FDBA74", dot: "🟠" },
        "黃色": { col: "#CA8A04", bg: "#FEFCE8", bd: "#FDE047", dot: "🟡" },
      };

      let mainHtml = "";
      if (d.items && d.items.length > 0) {
        // Prioritize blocks that have local targets first
        const sorted = [...d.items].sort((a, b) => (b.parsed.targets.length > 0 ? 1 : 0) - (a.parsed.targets.length > 0 ? 1 : 0));
        mainHtml = `
          ${d.lead ? `<div class="lead-txt">${escHtml(d.lead)}</div>` : ""}
          ${sorted.map((it) => {
            const lc = lampPalette[it.lamp] || lampPalette["黃色"];
            const p = it.parsed;
            const hasTargets = p.targets.length > 0;
            const tagsHtml = hasTargets
              ? `<div class="tag-row">${p.targets.map((t) =>
                  `<span class="region-pill" style="background:${t.bg};border-color:${t.bd};color:${t.col}">${t.dot} ${escHtml(t.name)}</span>`
                ).join("")}</div>`
              : "";
            const othersHtml = p.others.length > 0
              ? `<div class="others-txt">${hasTargets ? "其他縣市：" : "涵蓋地區："}${escHtml(p.others.join("、"))}</div>`
              : "";
            return `
              <div class="lamp-box" style="background:${lc.bg};border-color:${lc.bd}">
                <div class="lamp-hdr" style="color:${lc.col}">${lc.dot} ${escHtml(it.lamp)}燈號${!hasTargets ? "（其他縣市）" : ""}</div>
                ${p.time ? `<div class="lamp-time">⏱️ ${escHtml(p.time)}</div>` : ""}
                ${tagsHtml}
                <div class="lamp-cond">有${escHtml(it.cond)}</div>
                ${othersHtml}
              </div>
            `;
          }).join("")}
        `;
      } else {
        // Non-lamp disaster alert: highlight 竹南/苗栗/新竹 pills at top if mentioned
        const pills = [];
        if (d.sMain.includes("竹南")) pills.push({ name: "竹南", col: "#DC2626", bg: "#FEE2E2", bd: "#FCA5A5", dot: "🔴" });
        if (d.sMain.includes("苗栗")) pills.push({ name: "苗栗縣", col: "#2F80ED", bg: "#EFF6FF", bd: "#BFDBFE", dot: "🔵" });
        if (d.sMain.includes("新竹")) pills.push({ name: "新竹縣市", col: "#16A34A", bg: "#F0FDF4", bd: "#BBF7D0", dot: "🟢" });
        const paras = d.sMain.split("\n").map((s) => s.trim()).filter(Boolean);
        mainHtml = `
          <div class="lamp-box" style="background:#FFF7ED;border-color:#FDBA74">
            ${pills.length ? `<div class="tag-row">${pills.map((t) =>
              `<span class="region-pill" style="background:${t.bg};border-color:${t.bd};color:${t.col}">${t.dot} ${escHtml(t.name)}</span>`
            ).join("")}</div>` : ""}
            ${paras.map((p, i) => `<div class="para-txt" style="${i === 0 ? "font-weight:700" : ""}">${escHtml(p)}</div>`).join("")}
          </div>
        `;
      }

      const noteHtml = d.sNote
        ? `<div class="note-box"><div class="note-hdr">注意（警戒）事項</div><div class="note-txt">${escHtml(d.sNote)}</div></div>`
        : "";
      const evacHtml = d.isEvac
        ? `<div class="warn-box"><span class="warn-ic">🚨</span><div class="warn-txt">已觸發緊急疏散警報，請立即留意政府廣播與周遭環境，迅速配合疏散避難！</div></div>`
        : "";

      return mainHtml + noteHtml + evacHtml;
    }

    _show(item) {
      this._clearTimers();
      this._current = item;
      markSeen(item.key);
      const d = item.data;
      const nowStr = new Date().toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false });

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            all: initial;
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
            -webkit-font-smoothing: antialiased;
          }
          .backdrop {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.62);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
            animation: fadeIn 0.2s ease-out;
          }
          .card {
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 440px;
            max-height: min(86dvh, 720px);
            background: #FFFFFF;
            color: #111827;
            border-radius: 20px;
            box-shadow: 0 22px 48px -12px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(0, 0, 0, 0.08);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-sizing: border-box;
            animation: popUp 0.24s cubic-bezier(0.16, 1, 0.3, 1);
          }
          @media (max-width: 520px) {
            :host {
              align-items: flex-end;
              padding: 10px 10px calc(10px + env(safe-area-inset-bottom, 0px)) 10px;
            }
            .card {
              max-width: 100%;
              max-height: 85dvh;
              border-radius: 22px;
            }
          }
          @media (prefers-reduced-motion: reduce) {
            .backdrop, .card { animation: none !important; }
          }
          @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
          @keyframes popUp {
            from { opacity: 0; transform: translateY(18px) scale(0.97); }
            to { opacity: 1; transform: translateY(0) scale(1); }
          }

          .hdr {
            background: ${d.headerBg};
            color: #FFFFFF;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-shrink: 0;
            min-width: 0;
          }
          .hdr-ic {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
          }
          .hdr-ic ha-icon {
            --mdc-icon-size: 21px;
            color: #FFFFFF;
          }
          .hdr-main {
            flex: 1;
            min-width: 0;
          }
          .hdr-title {
            font-size: 16px;
            font-weight: 800;
            line-height: 1.25;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .hdr-sub {
            font-size: 11.5px;
            opacity: 0.9;
            margin-top: 2px;
          }
          .hdr-badge {
            background: rgba(255, 255, 255, 0.22);
            border: 1px solid rgba(255, 255, 255, 0.38);
            color: #FFFFFF;
            font-size: 11.5px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 99px;
            flex-shrink: 0;
            white-space: nowrap;
          }
          .close-x {
            appearance: none;
            border: none;
            background: rgba(0, 0, 0, 0.18);
            color: #FFFFFF;
            width: 32px;
            height: 32px;
            border-radius: 99px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: background 0.15s;
          }
          .close-x:hover { background: rgba(0, 0, 0, 0.32); }

          .body {
            padding: 14px 16px;
            overflow-y: auto;
            overscroll-behavior: contain;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-width: 0;
          }
          .lead-txt {
            font-size: 14px;
            font-weight: 700;
            color: #111827;
            line-height: 1.45;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .grid2 {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
          }
          .stat-box {
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 10px 12px;
            min-width: 0;
          }
          .stat-label {
            font-size: 11.5px;
            color: #6B7280;
            font-weight: 600;
          }
          .stat-val {
            font-size: 21px;
            font-weight: 800;
            margin-top: 3px;
            line-height: 1.2;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .meta-list {
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
          }
          .meta-row {
            display: flex;
            align-items: baseline;
            gap: 8px;
            font-size: 13px;
            min-width: 0;
          }
          .meta-k {
            color: #6B7280;
            flex-shrink: 0;
            font-size: 12px;
          }
          .meta-v {
            color: #111827;
            font-weight: 700;
            flex: 1;
            min-width: 0;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .info-box {
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 10px 12px;
          }
          .info-title {
            font-size: 13px;
            font-weight: 700;
            line-height: 1.4;
          }
          .info-desc {
            font-size: 12px;
            color: #4B5563;
            margin-top: 3px;
            line-height: 1.45;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .lamp-box {
            border: 1px solid #FDBA74;
            border-radius: 14px;
            padding: 11px 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            min-width: 0;
          }
          .lamp-hdr {
            font-size: 13.5px;
            font-weight: 800;
            line-height: 1.3;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .lamp-time {
            font-size: 12px;
            color: #4B5563;
            font-weight: 600;
            line-height: 1.4;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
          }
          .region-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: 8px;
            border: 1px solid transparent;
            font-size: 13px;
            font-weight: 800;
            line-height: 1.3;
            max-width: 100%;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .lamp-cond {
            font-size: 13px;
            color: #111827;
            font-weight: 600;
            line-height: 1.45;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .others-txt {
            font-size: 11.5px;
            color: #6B7280;
            line-height: 1.45;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .para-txt {
            font-size: 13px;
            color: #111827;
            line-height: 1.5;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .note-box {
            background: #F3F4F6;
            border-radius: 12px;
            padding: 9px 12px;
          }
          .note-hdr {
            font-size: 11.5px;
            font-weight: 700;
            color: #4B5563;
          }
          .note-txt {
            font-size: 12px;
            color: #374151;
            margin-top: 3px;
            line-height: 1.45;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .warn-box {
            background: #FEF2F2;
            border: 1px solid #FCA5A5;
            border-radius: 12px;
            padding: 10px 12px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
          }
          .warn-ic {
            font-size: 16px;
            line-height: 1.3;
            flex-shrink: 0;
          }
          .warn-txt {
            font-size: 12.5px;
            font-weight: 700;
            color: #B91C1C;
            line-height: 1.45;
            flex: 1;
            min-width: 0;
            overflow-wrap: anywhere;
            word-break: break-word;
          }

          .ftr {
            padding: 10px 16px 14px 16px;
            background: #F9FAFB;
            border-top: 1px solid #E5E7EB;
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-shrink: 0;
          }
          .ftr-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
          }
          .countdown-txt {
            font-size: 12px;
            color: #6B7280;
            font-weight: 600;
          }
          .ok-btn {
            appearance: none;
            border: none;
            background: #111827;
            color: #FFFFFF;
            font-size: 13.5px;
            font-weight: 700;
            padding: 9px 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: opacity 0.15s;
          }
          .ok-btn:hover { opacity: 0.88; }
          .bar-wrap {
            width: 100%;
            height: 4px;
            background: #E5E7EB;
            border-radius: 99px;
            overflow: hidden;
          }
          .bar-fill {
            height: 100%;
            width: 100%;
            background: ${d.themeColor};
            transform-origin: left center;
            transition: width 0.25s linear;
          }
        </style>
        <div class="backdrop"></div>
        <div class="card" role="dialog" aria-modal="true" aria-label="${escHtml(d.cardTitle)}">
          <div class="hdr">
            <div class="hdr-ic"><ha-icon icon="${escHtml(d.icon)}"></ha-icon></div>
            <div class="hdr-main">
              <div class="hdr-title">${escHtml(d.cardTitle)}</div>
              <div class="hdr-sub">智慧家庭即時推播 ・ ${escHtml(nowStr)}</div>
            </div>
            <div class="hdr-badge">${escHtml(d.badge)}</div>
            <button class="close-x" title="關閉" aria-label="關閉">✕</button>
          </div>
          <div class="body">
            ${this._renderBodyHtml(d)}
          </div>
          <div class="ftr">
            <div class="ftr-row">
              <div class="countdown-txt">將於 <span class="cd-num">${AUTO_CLOSE_SEC}</span> 秒後自動關閉</div>
              <button class="ok-btn">我知道了</button>
            </div>
            <div class="bar-wrap"><div class="bar-fill"></div></div>
          </div>
        </div>
      `;

      this.shadowRoot.querySelector(".backdrop")?.addEventListener("click", () => this.dismiss());
      this.shadowRoot.querySelector(".close-x")?.addEventListener("click", () => this.dismiss());
      this.shadowRoot.querySelector(".ok-btn")?.addEventListener("click", () => this.dismiss());

      // EEW arrival countdown if applicable
      let eewRem = d.kind === "eew" && d.secNum > 0 ? d.secNum : 0;
      if (eewRem > 0) {
        const secEl = this.shadowRoot.querySelector(".eew-sec");
        this._eewTimer = setInterval(() => {
          eewRem -= 1;
          if (!secEl) return;
          if (eewRem > 0) {
            secEl.textContent = `${eewRem} 秒後`;
          } else {
            secEl.textContent = "地震波已抵達";
            clearInterval(this._eewTimer);
            this._eewTimer = null;
          }
        }, 1000);
      }

      // 30s auto-close countdown
      const totalMs = AUTO_CLOSE_SEC * 1000;
      const startTs = Date.now();
      const cdEl = this.shadowRoot.querySelector(".cd-num");
      const barEl = this.shadowRoot.querySelector(".bar-fill");
      this._timer = setInterval(() => {
        const elapsed = Date.now() - startTs;
        const leftMs = Math.max(0, totalMs - elapsed);
        const leftSec = Math.ceil(leftMs / 1000);
        if (cdEl) cdEl.textContent = String(leftSec);
        if (barEl) barEl.style.width = `${(leftMs / totalMs) * 100}%`;
        if (leftMs <= 0) {
          this.dismiss();
        }
      }, 250);
    }
  }

  if (!customElements.get("smart-alert-popup-host")) {
    customElements.define("smart-alert-popup-host", SmartAlertPopupHost);
  }

  const ensureHost = () => {
    let el = document.querySelector("smart-alert-popup-host");
    if (!el && document.body) {
      el = document.createElement("smart-alert-popup-host");
      document.body.appendChild(el);
    }
    return el;
  };

  // State watcher
  let initialized = false;
  let lastDisasterVal = null;
  let lastEqVal = null;
  let lastEewStamp = null;
  let pendingDis = null;

  const checkStates = () => {
    if (!isSmartDashboard()) return;
    const hass = getHass();
    if (!hass || !hass.states) return;

    const now = Date.now();
    const disSt = hass.states["sensor.disaster"];
    const eqSt = hass.states["sensor.earthquake"];
    const eewLvSt = hass.states["input_text.line_eew_remote_level"];
    const eewSecSt = hass.states["input_text.line_eew_remote_seconds"];

    if (!initialized) {
      initialized = true;
      lastDisasterVal = disSt?.state ?? null;
      lastEqVal = eqSt?.state ?? null;
      lastEewStamp = eewLvSt ? `${eewLvSt.last_updated}|${eewLvSt.state}|${eewSecSt?.state}` : null;

      // On initial load, only pop if updated very recently and not yet seen
      if (eewLvSt && eewLvSt.last_updated) {
        const age = now - new Date(eewLvSt.last_updated).getTime();
        const key = `eew:${lastEewStamp}`;
        if (age >= 0 && age <= EEW_LOAD_WINDOW_MS && !isSeen(key)) {
          const parsed = parseEEW(eewLvSt.state, eewSecSt?.state);
          if (parsed) ensureHost()?.enqueue({ key, data: parsed }, true);
        }
      }
      if (disSt && disSt.state) {
        const age = disasterAgeMs(hass, disSt, now);
        const key = `dis:${hashStr(disasterSig(disSt.state))}`;
        if (isFresh(age) && !isSeen(key)) {
          const parsed = parseDisasterAlert(disSt.state);
          if (parsed) ensureHost()?.enqueue({ key, data: parsed }, false);
        }
      }
      if (eqSt && eqSt.state) {
        const age = eqReportAgeMs(eqSt, now);
        const key = `eq:${hashStr(eqSt.state)}`;
        if (isFresh(age) && !isSeen(key)) {
          const parsed = parseEarthquakeReport(eqSt.state);
          if (parsed) ensureHost()?.enqueue({ key, data: parsed }, false);
        }
      }
      return;
    }

    // 1. Live EEW change
    if (eewLvSt) {
      const curStamp = `${eewLvSt.last_updated}|${eewLvSt.state}|${eewSecSt?.state}`;
      if (curStamp !== lastEewStamp) {
        lastEewStamp = curStamp;
        const key = `eew:${curStamp}`;
        if (!isSeen(key)) {
          const parsed = parseEEW(eewLvSt.state, eewSecSt?.state);
          if (parsed) ensureHost()?.enqueue({ key, data: parsed }, true);
        }
      }
    }

    // 2. Live Disaster change (beta8: an old notice that comes back, e.g. after the sensor was unavailable, does not pop up;
    //    sensor.disaster_last_valid_update may lag the state by a moment, so a change is re-checked for up to 4 s)
    if (disSt && disSt.state !== lastDisasterVal) {
      lastDisasterVal = disSt.state;
      pendingDis = { state: disSt.state, since: now };
    }
    if (pendingDis) {
      if (disSt && disSt.state === pendingDis.state) {
        if (isFresh(disasterAgeMs(hass, disSt, now))) {
          const key = `dis:${hashStr(disasterSig(disSt.state))}`;
          pendingDis = null;
          if (!isSeen(key)) {
            const parsed = parseDisasterAlert(disSt.state);
            if (parsed) ensureHost()?.enqueue({ key, data: parsed }, false);
          }
        } else if (now - pendingDis.since > 4000) {
          pendingDis = null;
        }
      } else {
        pendingDis = null;
      }
    }

    // 3. Live Earthquake report change (age comes from the time written in the report)
    if (eqSt && eqSt.state !== lastEqVal) {
      lastEqVal = eqSt.state;
      const key = `eq:${hashStr(eqSt.state)}`;
      if (!isSeen(key) && isFresh(eqReportAgeMs(eqSt, now))) {
        const parsed = parseEarthquakeReport(eqSt.state);
        if (parsed) ensureHost()?.enqueue({ key, data: parsed }, false);
      }
    }
  };

  setInterval(checkStates, 750);

  // Manual preview helper for testing on any open dashboard
  window.showSmartAlertPopup = (type = "disaster", customText = null) => {
    const hass = getHass();
    const host = ensureHost();
    if (!host) return false;
    if (type === "eew") {
      const parsed = parseEEW(
        customText?.level || hass?.states?.["input_text.line_eew_remote_level"]?.state || "4",
        customText?.seconds || hass?.states?.["input_text.line_eew_remote_seconds"]?.state || "15"
      );
      if (parsed) host.enqueue({ key: `test:eew:${Date.now()}`, data: parsed }, true);
      return !!parsed;
    }
    if (type === "earthquake") {
      const raw = customText || hass?.states?.["sensor.earthquake"]?.state ||
        "10/22 10:15 花蓮縣政府南南西方 15.2 公里(位於花蓮縣壽豐鄉)發生規模 5.2 有感地震，最大震度花蓮縣 4 級。";
      const parsed = parseEarthquakeReport(raw);
      if (parsed) host.enqueue({ key: `test:eq:${Date.now()}`, data: parsed }, false);
      return !!parsed;
    }
    const raw = customText || hass?.states?.["sensor.disaster"]?.state || "";
    const parsed = parseDisasterAlert(raw);
    if (parsed) host.enqueue({ key: `test:dis:${Date.now()}`, data: parsed }, false);
    return !!parsed;
  };
})();

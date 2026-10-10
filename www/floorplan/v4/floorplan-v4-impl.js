import("/local/floorplan/v4/floorplan-v4-3d.js?t=" + Date.now()).catch((e) => console.error("floorplan-v4-3d failed", e));
/* Floorplan V4.0-beta6
 * custom:floorplan-v4-card      floor tabs + pan/zoom map (pinch, wheel, drag, double-tap reset)
 * custom:floorplan-v4-controls  per-floor control card that follows the floor chosen in the map card
 *
 * config:
 *   default: 2F
 *   floors: { "1F": {label: "1F", card: <any card config>}, ... }
 * The selected floor is kept client-side (sessionStorage, shared with floorplan-v4-3d.js), not in an input_select.
 */
(() => {
  if (customElements.get("floorplan-v4-card")) return;
  const KEY = "floorplan_v4_floor";
  const EVT = "floorplan-v4-floor";
  const getFloor = (cfg) => {
    let f = null;
    try { f = sessionStorage.getItem(KEY); } catch (e) { /* ignore */ }   // same store as floorplan-v4-3d.js
    return f && cfg.floors[f] ? f : cfg.default || Object.keys(cfg.floors)[0];
  };
  const setFloor = (f) => {
    try { sessionStorage.setItem(KEY, f); localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
    window.dispatchEvent(new CustomEvent(EVT, { detail: f }));
  };

  class Base extends HTMLElement {
    constructor() {
      super();
      this._els = {};
      this.attachShadow({ mode: "open" });
    }
    setConfig(cfg) {
      if (!cfg.floors) throw new Error("floors is required");
      this._cfg = cfg;
      this._floor = getFloor(cfg);
      this._build();
    }
    set hass(h) {
      this._hass = h;
      Object.values(this._els).forEach((el) => { el.hass = h; });
    }
    getCardSize() { return 6; }
    async _card(floor) {
      if (!this._els[floor]) {
        const helpers = await window.loadCardHelpers();
        const el = await helpers.createCardElement(this._cfg.floors[floor].card);
        if (this._hass) el.hass = this._hass;
        this._els[floor] = el;
      }
      return this._els[floor];
    }
  }

  class FloorplanV4Card extends Base {
    _build() {
      this._scale = 1; this._x = 0; this._y = 0;
      const tabs = Object.entries(this._cfg.floors)
        .map(([k, v]) => `<button data-f="${k}">${v.label || k}</button>`).join("");
      this.shadowRoot.innerHTML = `
        <style>
          :host { display:block; }
          .tabs { display:grid; grid-template-columns:repeat(${Object.keys(this._cfg.floors).length},1fr);
                  gap:8px; margin-bottom:10px; }
          .tabs button { border:0; border-radius:14px; padding:12px 4px; font:600 15px sans-serif;
                  background:rgba(120,120,128,.16); color:var(--primary-text-color); cursor:pointer; }
          .tabs button.on { background:#FFB900; color:#111; }
          .vp { position:relative; overflow:hidden; border-radius:16px; touch-action:none;
                background:var(--card-background-color,#fff); user-select:none; -webkit-user-select:none; }
          .inner { transform-origin:0 0; will-change:transform; }
          .zoom { position:absolute; right:8px; bottom:8px; display:flex; flex-direction:column; gap:6px; z-index:5; }
          .zoom button { width:38px; height:38px; border-radius:50%; border:0; font:700 20px sans-serif;
                  background:rgba(30,30,30,.7); color:#fff; cursor:pointer; }
        </style>
        <div class="tabs">${tabs}</div>
        <div class="vp"><div class="inner"></div>
          <div class="zoom"><button data-z="in">+</button><button data-z="out">&minus;</button><button data-z="reset">&#8634;</button></div>
        </div>`;
      const root = this.shadowRoot;
      root.querySelector(".tabs").addEventListener("click", (e) => {
        const f = e.target.closest("button")?.dataset.f;
        if (f) { this._floor = f; setFloor(f); this._show(); }
      });
      root.querySelector(".zoom").addEventListener("click", (e) => {
        const z = e.target.closest("button")?.dataset.z;
        if (!z) return;
        const vp = root.querySelector(".vp").getBoundingClientRect();
        if (z === "reset") this._reset();
        else this._zoomAt(z === "in" ? 1.4 : 1 / 1.4, vp.width / 2, vp.height / 2);
      });
      this._gestures(root.querySelector(".vp"));
      this._show();
    }
    async _show() {
      const root = this.shadowRoot;
      root.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.f === this._floor));
      const inner = root.querySelector(".inner");
      const el = await this._card(this._floor);
      inner.replaceChildren(el);
      this._reset();
    }
    connectedCallback() {
      this._on = (e) => {
        if (e.detail !== this._floor && this._cfg.floors[e.detail]) { this._floor = e.detail; this._show(); }
      };
      window.addEventListener(EVT, this._on);
    }
    disconnectedCallback() { window.removeEventListener(EVT, this._on); }

    _apply() {
      const vp = this.shadowRoot.querySelector(".vp");
      const inner = this.shadowRoot.querySelector(".inner");
      const r = vp.getBoundingClientRect();
      // keep the map overlapping the viewport
      const minX = r.width - r.width * this._scale, minY = r.height - inner.offsetHeight * this._scale;
      this._x = Math.min(0, Math.max(minX, this._x));
      this._y = Math.min(0, Math.max(Math.min(0, minY), this._y));
      inner.style.transform = `translate(${this._x}px,${this._y}px) scale(${this._scale})`;
    }
    _reset() { this._scale = 1; this._x = 0; this._y = 0; this._apply(); }
    _zoomAt(f, cx, cy) {
      const s = Math.min(5, Math.max(1, this._scale * f));
      const k = s / this._scale;
      this._x = cx - (cx - this._x) * k;
      this._y = cy - (cy - this._y) * k;
      this._scale = s;
      this._apply();
    }
    _gestures(vp) {
      const ptrs = new Map();
      let last = null, moved = false, lastTap = 0;
      const dist = () => { const [a, b] = [...ptrs.values()]; return Math.hypot(a.x - b.x, a.y - b.y); };
      const mid = () => { const [a, b] = [...ptrs.values()]; return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; };
      vp.addEventListener("pointerdown", (e) => {
        ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
        moved = false;
        last = ptrs.size === 2 ? { d: dist(), m: mid() } : { x: e.clientX, y: e.clientY };
      });
      vp.addEventListener("pointermove", (e) => {
        if (!ptrs.has(e.pointerId)) return;
        ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
        const r = vp.getBoundingClientRect();
        if (ptrs.size === 2) {
          const d = dist(), m = mid();
          this._zoomAt(d / last.d, m.x - r.left, m.y - r.top);
          this._x += m.x - last.m.x; this._y += m.y - last.m.y; this._apply();
          last = { d, m }; moved = true;
        } else if (this._scale > 1.01) {
          const dx = e.clientX - last.x, dy = e.clientY - last.y;
          if (moved || Math.hypot(dx, dy) > 6) {
            moved = true;
            vp.setPointerCapture?.(e.pointerId);
            this._x += dx; this._y += dy; this._apply();
            last = { x: e.clientX, y: e.clientY };
          }
        }
      });
      const up = (e) => {
        ptrs.delete(e.pointerId);
        if (ptrs.size === 1) { const p = [...ptrs.values()][0]; last = { x: p.x, y: p.y }; }
        if (!moved && ptrs.size === 0 && e.target === vp) lastTap = 0;
      };
      vp.addEventListener("pointerup", up);
      vp.addEventListener("pointercancel", up);
      // a drag must not trigger the hotspot underneath
      vp.addEventListener("click", (e) => { if (moved) { e.stopPropagation(); e.preventDefault(); moved = false; } }, true);
      vp.addEventListener("dblclick", (e) => { e.preventDefault(); this._reset(); });
      vp.addEventListener("wheel", (e) => {
        e.preventDefault();
        const r = vp.getBoundingClientRect();
        this._zoomAt(e.deltaY < 0 ? 1.15 : 1 / 1.15, e.clientX - r.left, e.clientY - r.top);
      }, { passive: false });
    }
  }

  class FloorplanV4Controls extends Base {
    _build() {
      this.shadowRoot.innerHTML = `<div class="c"></div>`;
      this._show();
    }
    async _show() {
      const el = await this._card(this._floor);
      this.shadowRoot.querySelector(".c").replaceChildren(el);
    }
    connectedCallback() {
      this._on = (e) => {
        if (this._cfg && this._cfg.floors[e.detail]) { this._floor = e.detail; this._show(); }
      };
      window.addEventListener(EVT, this._on);
    }
    disconnectedCallback() { window.removeEventListener(EVT, this._on); }
  }

  customElements.define("floorplan-v4-card", FloorplanV4Card);
  customElements.define("floorplan-v4-controls", FloorplanV4Controls);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: "floorplan-v4-card", name: "Floorplan V4 map" });
  window.customCards.push({ type: "floorplan-v4-controls", name: "Floorplan V4 controls" });
})();

// ── kiosk mode: open any dashboard URL with ?kiosk to hide HA's sidebar and the menu / search / ⋮ buttons but keep the view tabs (cosmetic only; ?kiosk=0 turns it off) ──
(() => {
  try {
    if (/[?&]kiosk=0\b/.test(location.search)) {
      sessionStorage.removeItem("fp4_kiosk");
      setTimeout(() => document.querySelector("home-assistant")?.dispatchEvent(new CustomEvent("hass-dock-sidebar", { detail: { dock: "docked" } })), 1500);   // give the sidebar back
    }
    else if (/[?&]kiosk(=|&|$)/.test(location.search)) sessionStorage.setItem("fp4_kiosk", "1");
    if (sessionStorage.getItem("fp4_kiosk") !== "1") return;
  } catch (e) { return; }
  const put = (root, id, css) => {
    if (!root || root.querySelector("#" + id)) return;
    const st = document.createElement("style"); st.id = id; st.textContent = css; root.appendChild(st);
  };
  let docked = false;
  const apply = () => {
    const ha = document.querySelector("home-assistant");
    if (!docked && ha?.hass) { docked = true; ha.dispatchEvent(new CustomEvent("hass-dock-sidebar", { detail: { dock: "always_hidden" } })); }   // HA's own setting: no reserved column
    const main = document.querySelector("home-assistant")?.shadowRoot?.querySelector("home-assistant-main");
    put(main?.shadowRoot, "fp4k-main", "ha-sidebar{display:none!important} ha-drawer{--mdc-drawer-width:0px!important} :host{--mdc-drawer-width:0px!important}");
    const drawer = main?.shadowRoot?.querySelector("ha-drawer");
    put(drawer?.shadowRoot, "fp4k-drawer", ".mdc-drawer{display:none!important;width:0!important} .mdc-drawer-app-content{margin-left:0!important;margin-right:0!important;margin-inline-start:0!important;padding-left:0!important} :host{--mdc-drawer-width:0px!important}");
    put(main?.shadowRoot, "fp4k-main2", "partial-panel-resolver,ha-panel-lovelace{margin-left:0!important;padding-left:0!important;width:100%!important} .mdc-drawer-app-content{margin-left:0!important}");
    const root = main?.shadowRoot?.querySelector("ha-panel-lovelace")?.shadowRoot?.querySelector("hui-root");
    put(root?.shadowRoot, "fp4k-root", "ha-menu-button,.action-items,.edit-mode,ha-button-menu,ha-icon-button-arrow-prev{display:none!important} .toolbar{padding-inline-start:12px!important}");
  };
  setInterval(apply, 700);
  apply();
})();

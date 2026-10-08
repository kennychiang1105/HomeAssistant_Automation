import json

with open('www/floorplan/3d/floorplan_3d_coordinates.json', 'r', encoding='utf-8') as f:
    floor_coords = json.load(f)

# Filter entities for clean interactive display (filter out infra/redundant sensors)
clean_data = {}
for fl, d in floor_coords.items():
    clean_ents = {}
    for ent_id, ent in d['entities'].items():
        cat = ent.get('category', 'other')
        if cat in ['infra']:
            continue
        clean_ents[ent_id] = ent
    clean_data[fl] = {
        "floor": fl,
        "name": d['name'],
        "viewbox": d['viewbox'],
        "svg_url": f"/local/floorplan/3d/floor_{fl.lower()}_3d.svg",
        "entities": clean_ents
    }

card_js = f"""// ─────────────────────────────────────────────────────────────
// Chiang Family 3D Floorplan Interactive Card
// Supports 3D Rotation, Pinch-to-Zoom, Pan & Live HA States
// ─────────────────────────────────────────────────────────────

const FLOOR_DATA = {json.dumps(clean_data, ensure_ascii=False, indent=2)};

class Card3DFloorplan extends HTMLElement {{
  constructor() {{
    super();
    this.attachShadow({{ mode: 'open' }});
    this.currentFloor = '2F';
    this.activeFilter = 'all';
    
    // 3D Transform States
    this.pitch = 50;  // rotateX (tilt)
    this.yaw = 0;     // rotateZ (orbit)
    this.zoom = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.is2D = false;

    // Pointer / Touch tracking
    this.isDragging = false;
    this.pointers = new Map();
    this.prevPinchDist = 0;
    this.startX = 0;
    this.startY = 0;
    this.startPanX = 0;
    this.startPanY = 0;
    this.startPitch = 0;
    this.startYaw = 0;
    this._hass = null;
  }}

  setConfig(config) {{
    this._config = config || {{}};
    this.render();
  }}

  set hass(hass) {{
    this._hass = hass;
    // Check if HA active floor helper changed
    const helperState = hass.states['input_select.floorplan_active_floor'];
    if (helperState) {{
      const stateVal = helperState.state;
      let targetFloor = '2F';
      if (stateVal.includes('1F')) targetFloor = '1F';
      else if (stateVal.includes('2F')) targetFloor = '2F';
      else if (stateVal.includes('3F')) targetFloor = '3F';
      else if (stateVal.includes('4F')) targetFloor = '4F';
      else if (stateVal.includes('5F')) targetFloor = '5F';
      else if (stateVal.includes('全棟')) targetFloor = 'ALL';
      
      if (this.currentFloor !== targetFloor && !this.userSwitching) {{
        this.currentFloor = targetFloor;
        this.updateFloorView();
      }}
    }}
    this.updateEntityPins();
  }}

  render() {{
    this.shadowRoot.innerHTML = `
      <style>
        :host {{
          display: block;
          position: relative;
          width: 100%;
          border-radius: 18px;
          overflow: hidden;
          background: #f8fafc;
          box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
          user-select: none;
          -webkit-user-select: none;
        }}

        /* Top Sticky Floor Navigation */
        .floor-nav {{
          display: flex;
          align-items: center;
          justify-content: flex-start;
          gap: 6px;
          padding: 10px 14px;
          background: rgba(255, 255, 255, 0.85);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-bottom: 1px solid rgba(226, 232, 240, 0.8);
          overflow-x: auto;
          scrollbar-width: none;
          z-index: 10;
          position: relative;
        }}
        .floor-nav::-webkit-scrollbar {{ display: none; }}

        .pill-btn {{
          padding: 6px 14px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 600;
          border: 1px solid #e2e8f0;
          background: rgba(255, 255, 255, 0.9);
          color: #475569;
          cursor: pointer;
          white-space: nowrap;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 4px;
          touch-action: manipulation;
        }}
        .pill-btn.active {{
          background: #0f172a;
          color: #ffffff;
          border-color: #0f172a;
          box-shadow: 0 4px 10px rgba(15, 23, 42, 0.2);
        }}

        /* Secondary Category Filter */
        .filter-nav {{
          display: flex;
          gap: 6px;
          padding: 6px 14px;
          background: rgba(248, 250, 252, 0.7);
          border-bottom: 1px solid rgba(226, 232, 240, 0.5);
          overflow-x: auto;
          scrollbar-width: none;
          z-index: 9;
        }}
        .filter-nav::-webkit-scrollbar {{ display: none; }}
        .filter-btn {{
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 600;
          border: 1px solid #cbd5e1;
          background: rgba(255,255,255,0.7);
          color: #64748b;
          cursor: pointer;
        }}
        .filter-btn.active {{
          background: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }}

        /* 3D Viewport Stage */
        .stage-3d {{
          position: relative;
          width: 100%;
          height: 480px;
          overflow: hidden;
          perspective: 1200px;
          touch-action: none;
          cursor: grab;
          background: radial-gradient(circle at center, #ffffff 0%, #f1f5f9 100%);
        }}
        .stage-3d:active {{
          cursor: grabbing;
        }}

        /* 3D Transformed Plane */
        .canvas-3d {{
          position: absolute;
          top: 50%;
          left: 50%;
          width: 600px;
          height: 380px;
          margin-top: -190px;
          margin-left: -300px;
          transform-style: preserve-3d;
          transform-origin: 50% 50%;
          will-change: transform;
          transition: transform 0.05s linear;
        }}

        .floor-svg-layer {{
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          user-select: none;
        }}

        /* Interactive Pin Badges */
        .pin-layer {{
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          transform-style: preserve-3d;
        }}

        .pin {{
          position: absolute;
          pointer-events: auto;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.88);
          border: 1.2px solid rgba(203, 213, 225, 0.9);
          box-shadow: 0 4px 10px rgba(15, 23, 42, 0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 15px;
          cursor: pointer;
          transform-style: preserve-3d;
          transition: transform 0.15s ease, background 0.2s, box-shadow 0.2s;
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          touch-action: manipulation;
        }}
        .pin:active {{
          transform: scale(1.25) !important;
        }}

        .pin.light-on {{
          background: #fef3c7;
          border-color: #f59e0b;
          color: #d97706;
          box-shadow: 0 0 12px rgba(245, 158, 11, 0.8), 0 2px 6px rgba(0,0,0,0.1);
        }}
        .pin.cover-open {{
          background: #ecfdf5;
          border-color: #10b981;
          color: #059669;
          box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
        }}
        .pin.motion-on {{
          background: #ecfeff;
          border-color: #06b6d4;
          color: #0891b2;
          animation: pulse 1.6s infinite ease-out;
        }}
        .pin.camera {{
          background: #eff6ff;
          border-color: #3b82f6;
          color: #2563eb;
        }}

        @keyframes pulse {{
          0% {{ box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.7); }}
          70% {{ box-shadow: 0 0 0 12px rgba(6, 182, 212, 0); }}
          100% {{ box-shadow: 0 0 0 0 rgba(6, 182, 212, 0); }}
        }}

        /* Floating Viewport Controls */
        .controls-overlay {{
          position: absolute;
          bottom: 14px;
          right: 14px;
          display: flex;
          flex-direction: column;
          gap: 6px;
          z-index: 10;
        }}
        .ctrl-btn {{
          width: 38px;
          height: 38px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.88);
          border: 1px solid rgba(226, 232, 240, 0.8);
          box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          color: #334155;
          cursor: pointer;
          touch-action: manipulation;
          transition: all 0.15s ease;
        }}
        .ctrl-btn:active {{
          transform: scale(0.92);
          background: #e2e8f0;
        }}

        /* Gesture Hint Badge */
        .hint-badge {{
          position: absolute;
          bottom: 14px;
          left: 14px;
          padding: 6px 12px;
          border-radius: 14px;
          background: rgba(255, 255, 255, 0.75);
          backdrop-filter: blur(8px);
          font-size: 11px;
          font-weight: 500;
          color: #64748b;
          border: 1px solid rgba(226, 232, 240, 0.6);
          pointer-events: none;
        }}
      </style>

      <!-- Floor Selector -->
      <div class="floor-nav">
        <button class="pill-btn" data-floor="1F">1F 車庫</button>
        <button class="pill-btn active" data-floor="2F">2F 客廳餐廳</button>
        <button class="pill-btn" data-floor="3F">3F 主臥室</button>
        <button class="pill-btn" data-floor="4F">4F 次臥</button>
        <button class="pill-btn" data-floor="5F">5F 頂樓</button>
        <button class="pill-btn" data-floor="ALL">🏛️ 全棟透視</button>
      </div>

      <!-- Filter Selector -->
      <div class="filter-nav">
        <button class="filter-btn active" data-filter="all">全部實體</button>
        <button class="filter-btn" data-filter="light">💡 燈光開關</button>
        <button class="filter-btn" data-filter="climate">❄️ 空調風扇</button>
        <button class="filter-btn" data-filter="cover">🚪 車庫鐵門</button>
        <button class="filter-btn" data-filter="camera">📹 監控鏡頭</button>
      </div>

      <!-- 3D Interactive Stage -->
      <div class="stage-3d" id="stage">
        <div class="canvas-3d" id="canvas">
          <img class="floor-svg-layer" id="floorImg" src="/local/floorplan/3d/floor_2f_3d.svg" alt="3D Floor" />
          <div class="pin-layer" id="pinLayer"></div>
        </div>

        <!-- Floating Controls -->
        <div class="controls-overlay">
          <button class="ctrl-btn" id="btnRotate" title="旋轉 45 度">🔄</button>
          <button class="ctrl-btn" id="btnZoomIn" title="放大">➕</button>
          <button class="ctrl-btn" id="btnZoomOut" title="縮小">➖</button>
          <button class="ctrl-btn" id="btn2D3D" title="2D/3D 切換">📐</button>
          <button class="ctrl-btn" id="btnReset" title="復位">🎯</button>
        </div>

        <div class="hint-badge">
          👆 單指拖曳旋轉 · 雙指縮放平移
        </div>
      </div>
    `;

    this.bindEvents();
    this.updateFloorView();
  }}

  bindEvents() {{
    const root = this.shadowRoot;
    const stage = root.getElementById('stage');
    
    // Floor pills
    root.querySelectorAll('.floor-nav .pill-btn').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        const fl = e.currentTarget.dataset.floor;
        this.selectFloor(fl);
      }});
    }});

    // Filter buttons
    root.querySelectorAll('.filter-nav .filter-btn').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        root.querySelectorAll('.filter-nav .filter-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.activeFilter = e.currentTarget.dataset.filter;
        this.renderPins();
      }});
    }});

    // Control buttons
    root.getElementById('btnRotate').addEventListener('click', () => {{
      this.yaw = (this.yaw + 45) % 360;
      this.applyTransform();
    }});
    root.getElementById('btnZoomIn').addEventListener('click', () => {{
      this.zoom = Math.min(2.8, this.zoom * 1.25);
      this.applyTransform();
    }});
    root.getElementById('btnZoomOut').addEventListener('click', () => {{
      this.zoom = Math.max(0.6, this.zoom * 0.8);
      this.applyTransform();
    }});
    root.getElementById('btn2D3D').addEventListener('click', () => {{
      this.is2D = !this.is2D;
      if (this.is2D) {{
        this.pitch = 0;
        this.yaw = 0;
      }} else {{
        this.pitch = 50;
        this.yaw = 0;
      }}
      this.applyTransform();
    }});
    root.getElementById('btnReset').addEventListener('click', () => {{
      this.pitch = 50;
      this.yaw = 0;
      this.zoom = 1.0;
      this.panX = 0;
      this.panY = 0;
      this.is2D = false;
      this.applyTransform();
    }});

    // Gesture Handlers (Pointer Events)
    stage.addEventListener('pointerdown', (e) => this.onPointerDown(e));
    window.addEventListener('pointermove', (e) => this.onPointerMove(e));
    window.addEventListener('pointerup', (e) => this.onPointerUp(e));
    window.addEventListener('pointercancel', (e) => this.onPointerUp(e));

    // Mouse wheel zoom
    stage.addEventListener('wheel', (e) => {{
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      this.zoom = Math.min(2.8, Math.max(0.6, this.zoom * delta));
      this.applyTransform();
    }}, {{ passive: false }});
  }}

  onPointerDown(e) {{
    this.pointers.set(e.pointerId, e);
    if (this.pointers.size === 1) {{
      this.isDragging = true;
      this.startX = e.clientX;
      this.startY = e.clientY;
      this.startPitch = this.pitch;
      this.startYaw = this.yaw;
      this.startPanX = this.panX;
      this.startPanY = this.panY;
    }} else if (this.pointers.size === 2) {{
      const pts = Array.from(this.pointers.values());
      this.prevPinchDist = Math.hypot(pts[0].clientX - pts[1].clientX, pts[0].clientY - pts[1].clientY);
      this.startPanX = this.panX;
      this.startPanY = this.panY;
      this.startX = (pts[0].clientX + pts[1].clientX) / 2;
      this.startY = (pts[0].clientY + pts[1].clientY) / 2;
    }}
  }}

  onPointerMove(e) {{
    if (!this.pointers.has(e.pointerId)) return;
    this.pointers.set(e.pointerId, e);

    if (this.pointers.size === 1 && this.isDragging) {{
      const dx = e.clientX - this.startX;
      const dy = e.clientY - this.startY;

      if (e.shiftKey || this.is2D) {{
        // Pan
        this.panX = this.startPanX + dx;
        this.panY = this.startPanY + dy;
      }} else {{
        // Orbit Rotate (Yaw & Pitch)
        this.yaw = (this.startYaw + dx * 0.45) % 360;
        this.pitch = Math.min(85, Math.max(15, this.startPitch - dy * 0.35));
      }}
      this.applyTransform();
    }} else if (this.pointers.size === 2) {{
      // Pinch to zoom and 2-finger pan
      const pts = Array.from(this.pointers.values());
      const dist = Math.hypot(pts[0].clientX - pts[1].clientX, pts[0].clientY - pts[1].clientY);
      if (this.prevPinchDist > 0) {{
        const factor = dist / this.prevPinchDist;
        this.zoom = Math.min(2.8, Math.max(0.6, this.zoom * factor));
      }}
      this.prevPinchDist = dist;

      const midX = (pts[0].clientX + pts[1].clientX) / 2;
      const midY = (pts[0].clientY + pts[1].clientY) / 2;
      this.panX = this.startPanX + (midX - this.startX);
      this.panY = this.startPanY + (midY - this.startY);

      this.applyTransform();
    }}
  }}

  onPointerUp(e) {{
    this.pointers.delete(e.pointerId);
    if (this.pointers.size < 2) {{
      this.prevPinchDist = 0;
    }}
    if (this.pointers.size === 0) {{
      this.isDragging = false;
    }}
  }}

  applyTransform() {{
    const canvas = this.shadowRoot.getElementById('canvas');
    if (!canvas) return;
    
    // Apply pan, zoom, pitch, yaw
    canvas.style.transform = `translate(${{this.panX}}px, ${{this.panY}}px) scale(${{this.zoom}}) rotateX(${{this.pitch}}deg) rotateZ(${{this.yaw}}deg)`;

    // Billboard effect: Counter-rotate pins so they stand facing the camera
    const pins = this.shadowRoot.querySelectorAll('.pin');
    pins.forEach(pin => {{
      pin.style.transform = `translate(-50%, -50%) rotateZ(${{-this.yaw}}deg) rotateX(${{-this.pitch}}deg)`;
    }});
  }}

  selectFloor(fl) {{
    this.currentFloor = fl;
    this.userSwitching = true;

    // Update HA input_select helper
    if (this._hass) {{
      const floorMap = {{
        '1F': '1F 車庫',
        '2F': '2F 客廳餐廳',
        '3F': '3F 主臥室',
        '4F': '4F 次臥',
        '5F': '5F 頂樓',
        'ALL': '全棟立體透視'
      }};
      if (floorMap[fl]) {{
        this._hass.callService('input_select', 'select_option', {{
          entity_id: 'input_select.floorplan_active_floor',
          option: floorMap[fl]
        }});
      }}
    }}

    setTimeout(() => {{ this.userSwitching = false; }}, 500);
    this.updateFloorView();
  }}

  updateFloorView() {{
    const root = this.shadowRoot;
    if (!root) return;

    // Update active pill
    root.querySelectorAll('.floor-nav .pill-btn').forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.floor === this.currentFloor);
    }});

    const floorImg = root.getElementById('floorImg');
    if (this.currentFloor === 'ALL') {{
      floorImg.src = '/local/floorplan/3d/floor_all_3d.svg';
    }} else {{
      floorImg.src = `/local/floorplan/3d/floor_${{this.currentFloor.toLowerCase()}}_3d.svg`;
    }}

    // Reset center on floor switch
    this.panX = 0;
    this.panY = 0;
    this.zoom = this.currentFloor === 'ALL' ? 0.65 : 1.0;
    this.renderPins();
    this.applyTransform();
  }}

  renderPins() {{
    const pinLayer = this.shadowRoot.getElementById('pinLayer');
    if (!pinLayer) return;
    pinLayer.innerHTML = '';

    if (this.currentFloor === 'ALL') return;

    const flData = FLOOR_DATA[this.currentFloor];
    if (!flData) return;

    const ents = flData.entities;
    for (const entId in ents) {{
      const ent = ents[entId];
      const cat = ent.category;

      // Filter check
      if (this.activeFilter !== 'all') {{
        if (this.activeFilter === 'light' && cat !== 'light') continue;
        if (this.activeFilter === 'climate' && !['climate', 'fan'].includes(cat)) continue;
        if (this.activeFilter === 'cover' && cat !== 'cover') continue;
        if (this.activeFilter === 'camera' && cat !== 'camera') continue;
      }}

      const pin = document.createElement('div');
      pin.className = 'pin';
      pin.dataset.entityId = entId;
      pin.dataset.domain = ent.domain;
      pin.dataset.category = cat;
      pin.style.left = `${{ent.pct_left}}%`;
      pin.style.top = `${{ent.pct_top}}%`;

      // Icon determination
      let icon = '💡';
      if (cat === 'camera') icon = '📹';
      else if (cat === 'cover') icon = '🚪';
      else if (cat === 'climate') icon = '❄️';
      else if (cat === 'fan') icon = '🌀';
      else if (cat === 'motion') icon = '📡';
      else if (cat === 'switch') icon = '🔌';
      pin.textContent = icon;

      // Tap action
      pin.addEventListener('click', (e) => {{
        e.stopPropagation();
        this.handlePinClick(entId, ent.domain);
      }});

      pinLayer.appendChild(pin);
    }}

    this.updateEntityPins();
    this.applyTransform();
  }}

  updateEntityPins() {{
    if (!this._hass) return;
    const pins = this.shadowRoot.querySelectorAll('.pin');
    pins.forEach(pin => {{
      const entId = pin.dataset.entityId;
      const stateObj = this._hass.states[entId];
      if (!stateObj) return;

      const state = stateObj.state;
      const cat = pin.dataset.category;

      if (cat === 'light' || cat === 'switch') {{
        pin.classList.toggle('light-on', state === 'on');
      }} else if (cat === 'cover') {{
        pin.classList.toggle('cover-open', state === 'open');
      }} else if (cat === 'motion') {{
        pin.classList.toggle('motion-on', state === 'on');
      }}
    }});
  }}

  handlePinClick(entId, domain) {{
    if (!this._hass) return;
    if (domain === 'camera') {{
      const event = new CustomEvent('hass-more-info', {{
        bubbles: true,
        composed: true,
        detail: {{ entityId: entId }}
      }});
      this.dispatchEvent(event);
    }} else {{
      // Toggle
      this._hass.callService(domain === 'cover' ? 'cover' : 'homeassistant', 'toggle', {{
        entity_id: entId
      }});
    }}
  }}

  getCardSize() {{
    return 7;
  }}
}}

customElements.define('card-3d-floorplan', Card3DFloorplan);
console.info('%c CARD-3D-FLOORPLAN %c v2.0 Loaded ', 'background:#0284c7;color:#fff;font-weight:bold;', 'background:#f8fafc;color:#0f172a;');
"""

with open('www/floorplan/3d/card-3d-floorplan.js', 'w', encoding='utf-8') as f:
    f.write(card_js)

print("Generated www/floorplan/3d/card-3d-floorplan.js successfully!")

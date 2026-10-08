import os
import math
import json
import html
import xml.etree.ElementTree as ET

# Load spatial scene graph
with open('spatial_scene_graph.json', 'r', encoding='utf-8') as f:
    scene_graph = json.load(f)

os.makedirs('www/floorplan/3d', exist_ok=True)

cos30 = math.cos(math.radians(30))  # ~0.866025
sin30 = math.sin(math.radians(30))  # 0.5

coord_export = {}

floor_order = ["1F", "2F", "3F", "4F", "5F"]

# Entity categorization helper
def categorize_entity(ent_id, domain):
    if 'u6_' in ent_id or 'switch_lite' in ent_id or 'udm' in ent_id:
        return 'infra'
    if 'tong_bu_kai_guan' in ent_id:
        return 'infra'
    if 'alarm' in ent_id or 'aqaradang_qian_qing_jing' in ent_id:
        return 'security'
    if domain == 'camera':
        return 'camera'
    if domain == 'climate':
        return 'climate'
    if domain == 'fan':
        return 'fan'
    if domain == 'cover':
        return 'cover'
    if domain == 'light':
        return 'light'
    if domain == 'switch':
        if any(kw in ent_id for kw in ['deng', 'light', 'kan_deng', 'bi_deng', 'lu_deng']):
            return 'light'
        return 'switch'
    if domain == 'binary_sensor':
        if any(kw in ent_id for kw in ['motion', 'zhan_kong', 'person']):
            return 'motion'
        return 'infra'
    if domain == 'sensor':
        if any(kw in ent_id for kw in ['parkinggrid', 'temperature', 'humidity', 'pm2_5']):
            return 'sensor'
        return 'infra'
    return 'other'

for floor_key in floor_order:
    floor_data = scene_graph['floors'][floor_key]
    svg_filename = floor_data['svg_file']
    w_orig, h_orig = floor_data['viewbox'][2], floor_data['viewbox'][3]
    
    c_top = (0.0, 0.0)
    c_right = (w_orig * cos30, w_orig * sin30)
    c_bottom = ((w_orig - h_orig) * cos30, (w_orig + h_orig) * sin30)
    c_left = (-h_orig * cos30, h_orig * sin30)
    
    all_x = [c_top[0], c_right[0], c_bottom[0], c_left[0]]
    all_y = [c_top[1], c_right[1], c_bottom[1], c_left[1]]
    
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)
    
    margin_x = 50.0
    margin_y = 50.0
    slab_depth = 28.0
    shadow_depth = 18.0
    
    tx = -min_x + margin_x
    ty = -min_y + margin_y
    
    p_top = (c_top[0] + tx, c_top[1] + ty)
    p_right = (c_right[0] + tx, c_right[1] + ty)
    p_bottom = (c_bottom[0] + tx, c_bottom[1] + ty)
    p_left = (c_left[0] + tx, c_left[1] + ty)
    
    viewbox_w = max_x - min_x + margin_x * 2
    viewbox_h = max_y - min_y + margin_y * 2 + slab_depth + shadow_depth
    
    tree = ET.parse(svg_filename)
    root = tree.getroot()
    
    defs_el = root.find('{http://www.w3.org/2000/svg}defs')
    style_content = ""
    if defs_el is not None:
        style_el = defs_el.find('{http://www.w3.org/2000/svg}style')
        if style_el is not None and style_el.text:
            style_content = style_el.text
            
    arch_group = None
    for child in root:
        if child.attrib.get('id') in ['Layer_11', 'Layer_1'] or child.attrib.get('data-name') == 'Layer_1':
            arch_group = child
            break
            
    arch_xml = ""
    if arch_group is not None:
        for el in arch_group:
            arch_xml += ET.tostring(el, encoding='unicode')
    else:
        for el in root:
            tag = el.tag.split('}')[-1]
            if tag not in ['defs'] and el.attrib.get('id') != 'HA實體專用圖層':
                arch_xml += ET.tostring(el, encoding='unicode')
                
    entity_decals = []
    floor_coords = {}
    
    for ent in floor_data['entities']:
        orig_x = ent['coordinates']['x']
        orig_y = ent['coordinates']['y']
        
        iso_x = (orig_x - orig_y) * cos30 + tx
        iso_y = (orig_x + orig_y) * sin30 + ty
        
        pct_left = round((iso_x / viewbox_w) * 100, 2)
        pct_top = round((iso_y / viewbox_h) * 100, 2)
        
        ent_id = ent['entity_id']
        category = categorize_entity(ent_id, ent['domain'])
        
        floor_coords[ent_id] = {
            "entity_id": ent_id,
            "domain": ent['domain'],
            "category": category,
            "room": ent['room'],
            "pct_left": pct_left,
            "pct_top": pct_top,
            "iso_x": round(iso_x, 1),
            "iso_y": round(iso_y, 1)
        }
        
        # Only add floor decals for visible interactive devices
        if category in ['light', 'switch', 'cover', 'climate', 'camera']:
            decal_svg = f'''
        <g class="floor-anchor" id="anchor_{ent_id}" transform="translate({iso_x:.1f}, {iso_y:.1f})">
          <ellipse cx="0" cy="0" rx="10" ry="5.5" fill="rgba(37, 99, 235, 0.04)" stroke="rgba(59, 130, 246, 0.2)" stroke-width="0.8" stroke-dasharray="2,2" />
        </g>'''
            entity_decals.append(decal_svg)
        
    # Also add camera decals
    if floor_key == '1F':
        cam_id = 'camera.g6_instant_high_resolution_channel'
        c_orig_x, c_orig_y = 387.95, 29.42
        c_iso_x = (c_orig_x - c_orig_y) * cos30 + tx
        c_iso_y = (c_orig_x + c_orig_y) * sin30 + ty
        floor_coords[cam_id] = {
            "entity_id": cam_id,
            "domain": "camera",
            "category": "camera",
            "room": "1F 車庫監控",
            "pct_left": round((c_iso_x / viewbox_w) * 100, 2),
            "pct_top": round((c_iso_y / viewbox_h) * 100, 2),
            "iso_x": round(c_iso_x, 1),
            "iso_y": round(c_iso_y, 1)
        }
    elif floor_key == '5F':
        cam_id = 'camera.wu_lou_she_ying_ji_high'
        c_orig_x, c_orig_y = 696.64, 466.07
        c_iso_x = (c_orig_x - c_orig_y) * cos30 + tx
        c_iso_y = (c_orig_x + c_orig_y) * sin30 + ty
        floor_coords[cam_id] = {
            "entity_id": cam_id,
            "domain": "camera",
            "category": "camera",
            "room": "5F 頂樓監控",
            "pct_left": round((c_iso_x / viewbox_w) * 100, 2),
            "pct_top": round((c_iso_y / viewbox_h) * 100, 2),
            "iso_x": round(c_iso_x, 1),
            "iso_y": round(c_iso_y, 1)
        }
        
    coord_export[floor_key] = {
        "floor": floor_key,
        "name": floor_data['name'],
        "viewbox": [0, 0, round(viewbox_w, 1), round(viewbox_h, 1)],
        "entities": floor_coords
    }
    
    escaped_floor_name = html.escape(floor_data['name'])
    
    out_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {viewbox_w:.1f} {viewbox_h:.1f}" width="100%" height="100%">
  <defs>
    <filter id="ambientShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#0f172a" flood-opacity="0.12" />
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.06" />
    </filter>
    <linearGradient id="slabLeftEdge" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#e2e8f0" />
      <stop offset="100%" stop-color="#cbd5e1" />
    </linearGradient>
    <linearGradient id="slabRightEdge" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#cbd5e1" />
      <stop offset="100%" stop-color="#94a3b8" />
    </linearGradient>
    <linearGradient id="topPlateGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="60%" stop-color="#f8fafc" />
      <stop offset="100%" stop-color="#f1f5f9" />
    </linearGradient>
    <style>
      {style_content}
      .arch-layer path, .arch-layer rect, .arch-layer polygon {{
        vector-effect: non-scaling-stroke;
      }}
      .floor-title-badge {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
        font-size: 15px;
        font-weight: 700;
        fill: #334155;
        letter-spacing: 0.5px;
      }}
    </style>
  </defs>

  <polygon points="{p_top[0]:.1f},{p_top[1]+shadow_depth:.1f} {p_right[0]:.1f},{p_right[1]+shadow_depth:.1f} {p_bottom[0]:.1f},{p_bottom[1]+shadow_depth+slab_depth:.1f} {p_left[0]:.1f},{p_left[1]+shadow_depth+slab_depth:.1f}" 
           fill="#64748b" opacity="0.20" filter="url(#ambientShadow)" />

  <polygon points="{p_left[0]:.1f},{p_left[1]:.1f} {p_bottom[0]:.1f},{p_bottom[1]:.1f} {p_bottom[0]:.1f},{p_bottom[1]+slab_depth:.1f} {p_left[0]:.1f},{p_left[1]+slab_depth:.1f}" 
           fill="url(#slabLeftEdge)" stroke="#94a3b8" stroke-width="0.8" />
  
  <polygon points="{p_bottom[0]:.1f},{p_bottom[1]:.1f} {p_right[0]:.1f},{p_right[1]:.1f} {p_right[0]:.1f},{p_right[1]+slab_depth:.1f} {p_bottom[0]:.1f},{p_bottom[1]+slab_depth:.1f}" 
           fill="url(#slabRightEdge)" stroke="#64748b" stroke-width="0.8" />

  <polygon points="{p_top[0]:.1f},{p_top[1]:.1f} {p_right[0]:.1f},{p_right[1]:.1f} {p_bottom[0]:.1f},{p_bottom[1]:.1f} {p_left[0]:.1f},{p_left[1]:.1f}" 
           fill="url(#topPlateGradient)" stroke="#cbd5e1" stroke-width="1.5" />

  <g class="arch-layer" transform="matrix({cos30:.6f} {sin30:.6f} {-cos30:.6f} {sin30:.6f} {tx:.2f} {ty:.2f})">
    {arch_xml}
  </g>

  <g class="entity-decals">
    {''.join(entity_decals)}
  </g>

  <g transform="translate(45, 45)">
    <rect x="-10" y="-18" width="140" height="36" rx="8" ry="8" fill="rgba(255,255,255,0.9)" stroke="#e2e8f0" stroke-width="1" />
    <text x="0" y="4" class="floor-title-badge">{escaped_floor_name}</text>
  </g>
</svg>'''

    out_file = f'www/floorplan/3d/floor_{floor_key.lower()}_3d.svg'
    with open(out_file, 'w', encoding='utf-8') as fp:
        fp.write(out_svg)
    print(f"Generated {out_file} (ViewBox: 0 0 {viewbox_w:.1f} {viewbox_h:.1f})")

# Save coordinates json
with open('www/floorplan/3d/floorplan_3d_coordinates.json', 'w', encoding='utf-8') as fp:
    json.dump(coord_export, fp, indent=2, ensure_ascii=False)

print("Coordinate export saved to www/floorplan/3d/floorplan_3d_coordinates.json")

# Generate Stacked Multi-Floor Overview (floor_all_3d.svg)
print("Generating stacked overview floor_all_3d.svg...")
stacked_elements = []
offsets = {
    "1F": 1500,
    "2F": 1150,
    "3F": 800,
    "4F": 450,
    "5F": 100
}

for fl in ["1F", "2F", "3F", "4F", "5F"]:
    fl_svg_path = f'www/floorplan/3d/floor_{fl.lower()}_3d.svg'
    with open(fl_svg_path, 'r', encoding='utf-8') as f:
        svg_txt = f.read()
    
    start_tag = svg_txt.find('>', svg_txt.find('<svg')) + 1
    end_tag = svg_txt.rfind('</svg>')
    inner = svg_txt[start_tag:end_tag]
    
    y_off = offsets[fl]
    stacked_elements.append(f'''
    <!-- {fl} Stack Layer -->
    <g id="stack_{fl}" transform="translate(100, {y_off}) scale(0.85)">
      {inner}
    </g>
    ''')

stacked_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 2400" width="100%" height="100%">
  <defs>
    <filter id="ambientShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#0f172a" flood-opacity="0.12" />
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.06" />
    </filter>
    <linearGradient id="slabLeftEdge" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#e2e8f0" />
      <stop offset="100%" stop-color="#cbd5e1" />
    </linearGradient>
    <linearGradient id="slabRightEdge" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#cbd5e1" />
      <stop offset="100%" stop-color="#94a3b8" />
    </linearGradient>
    <linearGradient id="topPlateGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="60%" stop-color="#f8fafc" />
      <stop offset="100%" stop-color="#f1f5f9" />
    </linearGradient>
  </defs>
  
  <text x="80" y="80" font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif" font-size="28" font-weight="700" fill="#1e293b">
    CHIANG FAMILY 3D 全棟立體透視
  </text>
  <text x="80" y="115" font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif" font-size="14" font-weight="500" fill="#64748b">
    5 階立體垂直拓撲展開 · 智慧空間總覽
  </text>

  {''.join(stacked_elements)}
</svg>'''

with open('www/floorplan/3d/floor_all_3d.svg', 'w', encoding='utf-8') as f:
    f.write(stacked_svg)

print("Generated www/floorplan/3d/floor_all_3d.svg successfully!")

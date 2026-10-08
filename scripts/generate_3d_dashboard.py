import json

dashboard_yaml = """title: 3D 智慧家庭
views:
  # ══════════════════════════════════════════════════════════════
  # 1. iPad / 平板雙欄駕駛艙視圖 (Tablet Cockpit)
  # ══════════════════════════════════════════════════════════════
  - title: 3D 控制中心 (iPad)
    path: tablet
    icon: mdi:tablet-dashboard
    type: custom:grid-layout
    layout:
      grid-template-columns: 1fr 380px
      grid-template-areas: |
        "main sidebar"
      mediaquery:
        "(max-width: 960px)":
          grid-template-columns: 100%
          grid-template-areas: |
            "main"
            "sidebar"
    cards:
      # ── [左側舞台：3D 可旋轉/縮放互動畫布] ──
      - type: vertical-stack
        view_layout:
          grid-area: main
        cards:
          - type: custom:card-3d-floorplan

      # ── [右側側邊欄：環境概況、即時設備控制、監控與情境] ──
      - type: vertical-stack
        view_layout:
          grid-area: sidebar
        cards:
          - type: markdown
            content: >
              ## 🏠 當前樓層狀態

              **目前選擇：{{ states('input_select.floorplan_active_floor') }}**


              {% set active_fl = states('input_select.floorplan_active_floor') %}

              {% if '1F' in active_fl %}
                - 🚗 車位狀態：**{% if is_state('sensor.parkinggrid1','on') %}車位一佔用{% else %}車位一空置{% endif %}**
                - 🚪 車庫鐵門：**{{ states('cover.garage') }}**
                - 💡 車庫主燈：**{{ states('switch.che_ku_zhu_deng') }}**
                - 🔌 特斯拉充電：**{{ states('sensor.tesla_wall_connector_status') }}**
              {% elif '2F' in active_fl %}
                - 🌡️ 室內溫度：**{{ states('sensor.kong_qi_qing_jing_ji_temperature') }}°C**
                - 💧 室內濕度：**{{ states('sensor.kong_qi_qing_jing_ji_humidity') }}%**
                - 🍃 空氣清淨機：**{{ states('fan.kong_qi_qing_jing_ji') }} (PM2.5: {{ states('sensor.kong_qi_qing_jing_ji_pm2_5') }})**
                - 🔒 二樓正門：**{{ states('lock.er_lou_men_suo') }}**
              {% elif '3F' in active_fl %}
                - 💡 主臥走廊：**{{ states('switch.er_san_lou_lou_ti_deng') }}**
                - 🛋️ 主臥燈光：**{{ states('switch.san_lou_lou_ti_deng') }}**
              {% elif '4F' in active_fl %}
                - 💡 前臥室燈：**{{ states('switch.qian_wo_shi_deng') }}**
                - 💡 後臥室燈：**{{ states('switch.hou_wo_shi_deng') }}**
                - 🪜 四樓梯廳：**{{ states('switch.san_si_lou_lou_ti_deng') }}**
              {% elif '5F' in active_fl %}
                - 🌡️ 頂樓溫度：**{{ states('sensor.5f_homepodmini_temperature') }}°C**
                - ❄️ 頂樓空調：**{{ states('climate.ding_lou_kong_diao') }}**
                - 💻 書房主機：**{{ states('switch.asusworkstationcha_zuo') }}**
                - 💡 頂樓主燈：**{{ states('light.ding_lou_deng_zu_1') }}**
              {% else %}
                - 💡 全屋亮燈數：**{{ states('sensor.all_light_count') }} 盞**
                - 🚨 災防/地震：**{{ states('sensor.earthquake') }}**
              {% endif %}

          # 快捷情境操作
          - type: grid
            title: 常用情境快捷
            columns: 2
            square: false
            cards:
              - type: button
                entity: input_boolean.google_scene_dao_jia_trigger
                name: 回家模式
                icon: mdi:home-import-outline
                tap_action:
                  action: toggle
              - type: button
                entity: input_boolean.google_scene_chu_men_trigger
                name: 離家模式
                icon: mdi:home-export-outline
                tap_action:
                  action: toggle
              - type: button
                entity: input_boolean.google_scene_zao_an_trigger
                name: 早安情境
                icon: mdi:weather-sunny
                tap_action:
                  action: toggle
              - type: button
                entity: input_boolean.google_scene_wan_an_trigger
                name: 晚安休眠
                icon: mdi:weather-night
                tap_action:
                  action: toggle

          # 即時攝影機監視小窗
          - type: conditional
            conditions:
              - entity: input_select.floorplan_active_floor
                state: "1F 車庫"
            card:
              type: picture-entity
              entity: camera.g6_instant_high_resolution_channel
              name: 1F 車庫即時監視
              camera_view: live

          - type: conditional
            conditions:
              - entity: input_select.floorplan_active_floor
                state: "5F 頂樓"
            card:
              type: picture-entity
              entity: camera.wu_lou_she_ying_ji_high
              name: 5F 梯廳即時監視
              camera_view: live

  # ══════════════════════════════════════════════════════════════
  # 2. 手機版便攜直向視圖 (Mobile Optimized)
  # ══════════════════════════════════════════════════════════════
  - title: 3D 便攜版 (手機)
    path: mobile
    icon: mdi:cellphone
    cards:
      # 手機版 3D 互動畫布 (支援單指旋轉、雙指縮放平移、分類篩選)
      - type: custom:card-3d-floorplan

      # 當前樓層狀態摘要卡片
      - type: markdown
        content: >
          ### 📱 當前樓層：{{ states('input_select.floorplan_active_floor') }}

          - 👆 **操作指引**：可單指滑動旋轉角度、雙指縮放平移；點選下方篩選標籤可快速切換設備。

      # 底部單手常用快捷大按鈕
      - type: grid
        title: 當前常用控制
        columns: 3
        square: true
        cards:
          - type: button
            entity: switch.che_ku_zhu_deng
            name: 車庫主燈
            icon: mdi:lightbulb
            tap_action:
              action: toggle
          - type: button
            entity: switch.chu_fang_deng
            name: 廚房燈
            icon: mdi:ceiling-light
            tap_action:
              action: toggle
          - type: button
            entity: cover.garage
            name: 車庫鐵門
            icon: mdi:garage
            tap_action:
              action: toggle

  # ══════════════════════════════════════════════════════════════
  # 3. 全棟立體透視視圖 (Building Isometric Overview)
  # ══════════════════════════════════════════════════════════════
  - title: 全棟立體透視
    path: overview
    icon: mdi:office-building
    cards:
      - type: picture-elements
        image: /local/floorplan/3d/floor_all_3d.svg
        elements: []
"""

with open('3d-floorplan.yaml', 'w', encoding='utf-8') as f:
    f.write(dashboard_yaml)

print("Generated 3d-floorplan.yaml successfully!")

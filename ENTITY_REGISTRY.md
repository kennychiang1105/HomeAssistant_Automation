# Home Assistant 常用實體分類總表與 AI 開發調用清單 (ENTITY_REGISTRY)

> **版本**：V1.0  
> **建立日期**：2026-09-23  
> **適用架構**：Home Assistant 2026.8+ / AI Program 架構  
> **用途**：集中記錄全戶自動化、腳本、Helper 及硬體整合之所有核心實體。提供「分區」與「領域功能」雙向檢索，並收錄重大開發避坑經驗與硬體特性，供 AI 與開發者精準調用。

---

> **位置資料**：每個實體在 1F~5F 平面圖與 3D 場景中的座標、區域、燈群組，見 [ENTITY_POSITIONS.md](ENTITY_POSITIONS.md)（機器可讀：`entity_positions.yaml` / `entity_positions.json`）。

## 快速導覽目錄
1. [AI 開發核心規範與避坑指南（AI Essential Rules）](#一-ai-開發核心規範與避坑指南ai-essential-rules)
2. [分區檢索清單（Area Registry）](#二-分區檢索清單area-registry)
   - [1F 車庫區域 (Garage)](#1-1f-車庫區域-garage)
   - [2F 客廳區域 (Living Room)](#2-2f-客廳區域-living-room)
   - [2F 餐廳與廚房區域 (Dining & Kitchen)](#3-2f-餐廳與廚房區域-dining--kitchen)
   - [2F 廁所區域 (Bathroom)](#4-2f-廁所區域-bathroom)
   - [3F 臥室區域 (3F Bedroom)](#5-3f-臥室區域-3f-bedroom)
   - [4F 臥室區域 (4F Bedrooms - Jerry & Elay)](#6-4f-臥室區域-4f-bedrooms)
   - [5F 頂樓與書房區域 (5F Rooftop & Study)](#7-5f-頂樓與書房區域-rooftop--study)
   - [全棟樓梯間 (Staircases)](#8-全棟樓梯間-staircases)
   - [全戶系統、保全與車輛 (System, Security & Vehicles)](#9-全戶系統保全與車輛-system-security--vehicles)
3. [領域功能分類清單（Domain Registry）](#三-領域功能分類清單domain-registry)
   - [燈光與開關 (Lights & Switches)](#1-燈光與開關-lights--switches)
   - [動態、人體與占用感應器 (Motion, Occupancy & Presence)](#2-動態人體與占用感應器-motion-occupancy--presence)
   - [環境與電量感測器 (Sensors & Battery)](#3-環境與電量感測器-sensors--battery)
   - [門窗、鐵門與門鎖 (Covers & Locks)](#4-門窗鐵門與門鎖-covers--locks)
   - [保全與攝影機 (Security & Cameras)](#5-保全與攝影機-security--cameras)
   - [家電設備 (Appliances - Fan / TV / AC)](#6-家電設備-appliances)
   - [Helper 輔助實體 (Inputs, Timers, Buttons)](#7-helper-輔助實體-helpers)

---

## 一、 AI 開發核心規範與避坑指南（AI Essential Rules）

在開發或修改任何自動化與腳本時，AI 必須優先遵循以下硬體特性與經驗法則：

### 1. 車庫主燈 5 秒硬體防切小燈規則 ⚠️
* **硬體特性**：車庫主燈（`switch.che_ku_zhu_deng`）驅動器具備多段切換功能。若電源剛關閉後於 5 秒內再次通電，硬體會自動切換為「小燈/夜燈模式」。
* **防呆規範**：
  1. 自動化開燈時，若目前狀態為 `off`，必須檢查距離上次狀態變更時間是否滿 5 秒：
     ```jinja2
     {% set elapsed = as_timestamp(now()) - as_timestamp(states.switch.che_ku_zhu_deng.last_changed, 0) %}
     {% if elapsed < 5 %}需 delay (5.1 - elapsed) 秒後再開燈{% endif %}
     ```
  2. 若車庫主燈目前已為 `on`，嚴禁重複發送 `switch.turn_on`，避免無效指令。

### 2. UniFi Protect 原生實體 vs Scrypted 橋接實體 📷
* **選用原則**：**一律優先使用 UniFi Protect 原生實體**，避免使用 Scrypted 橋接產生的重複命名實體。
* **對照表**：
  * 車庫動態感測：使用 `binary_sensor.g6_instant_motion`（**禁止**使用 `binary_sensor.che_ku_che_ku_she_ying_ji_motion`）。
  * 頂樓動態感測：使用 `binary_sensor.ding_lou_she_ying_ji_motion`。
  * 人車 AI 物件偵測：`binary_sensor.che_ku_she_ying_ji_person_detected`、`binary_sensor.che_ku_she_ying_ji_vehicle_detected`。

### 3. 全戶實體開關「三擊（Triple Press）」絕對專用 🚨
* 全戶所有小燕科技（Terncy）開關及小米無線開關的「三擊」，**100% 專屬於 `05E緊急實體按鈕`（`1744040282451`）**。
* **嚴禁**在任何自動化中將實體開關三擊指定給區域自訂功能。

### 4. Wi-Fi AP MAC 區域定位防抖規範 📶
* 手機連接 Wi-Fi AP 判定所在樓層（`che_ku_wa_fi_gan_ying_zong_he_pan_duan`、`er_lou_ping_mu_gan_ying_zong_he_pan_duan`）：
  * **必須配置 30 秒 `delay_off`**，防止手機螢幕鎖定節能休眠或 AP 快速漫遊時出現短暫掉線。
  * 模板在展開追蹤器時，需透過 `selectattr('attributes.ap_mac', 'defined')` 確保僅讀取具備 AP MAC 屬性之實體。

### 5. LINE 推播標準規範 💬
* **唯一管道**：一律呼叫 `script.send_line_to_user`。
* **分級開關**：一般通知（`notify_line_general_enable` 🪧）、重要通知（`notify_line_important_enable` ⚠️）、緊急通知（`notify_line_emergency_enable` 🚨）。
* **文案規範**：純口語說明事件與動作，**嚴禁**暴露內部 entity/service 名稱。

---

## 二、 分區檢索清單（Area Registry）

### 1. 1F 車庫區域 (Garage)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `cover.garage` | Cover | iSmartgate Pro | 車庫鐵門（開啟/關閉/開門中） |
| `switch.che_ku_zhu_deng` | Switch | Terncy 車庫主燈開關 | 車庫主燈（含 5 秒防切小燈保護） |
| `switch.che_ku_deng_cha_zuo` | Switch | Terncy 車庫主開關3 | 車庫燈插座開關 |
| `binary_sensor.g6_instant_motion` | Binary Sensor | UniFi Protect | 車庫攝影機動態感測（原生） |
| `binary_sensor.che_ku_she_ying_ji_person_detected` | Binary Sensor | UniFi Protect | 車庫人員 AI 偵測 |
| `binary_sensor.che_ku_she_ying_ji_vehicle_detected` | Binary Sensor | UniFi Protect | 車庫車輛 AI 偵測 |
| `binary_sensor.che_ku_wa_fi_gan_ying_zong_he_pan_duan` | Binary Sensor | Template Helper | 車庫 Wi-Fi 手機綜合感應（U6 Mesh 1F） |
| `timer.garage_light_manual_off_cooldown` | Timer | Helper | 車庫燈手動關閉冷卻計時器 |
| `input_number.garage_light_cooldown_sec` | Input Number | Helper | 車庫燈冷卻秒數設定（預設 30 秒） |
| `input_boolean.garagejudge` | Input Boolean | Helper | 車庫狀態判定輔助旗標 |
| `sensor.che_ku_tesla_wall_connector_vehicle_current` | Sensor | Tesla Wall Connector | 特斯拉充電樁車輛電流 |
| `sensor.che_ku_tesla_wall_connector_wifi_rssi` | Sensor | Tesla Wall Connector | 特斯拉充電樁 Wi-Fi 訊號 |
| `input_number.supply_batt_lowest_garage` | Input Number | Helper | 車庫感測器最低電量記錄 |

### 2. 2F 客廳區域 (Living Room)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `switch.ke_ting_kan_deng` | Switch | Terncy 客廳開關 | 客廳崁燈 |
| `switch.ke_ting_bi_deng` | Switch | Terncy 客廳開關 | 客廳壁燈 |
| `switch.ke_ting_huan_rao_deng` | Switch | Terncy 客廳開關 | 客廳環繞燈 |
| `switch.ke_ting_xiao_deng` | Switch | Terncy 客廳開關 | 客廳小燈 |
| `fan.ke_ting_dian_feng_shan` | Fan | Xiaomi Miio Fan | 客廳小米電風扇 |
| `lock.ke_ting_men_suo` | Lock | Aqara Lock (ZNMS02ES) | 客廳大門電子門鎖 |
| `sensor.ke_ting_men_suo_battery` | Sensor | Aqara Lock | 客廳門鎖剩餘電量 |
| `media_player.hisense_vision_55e7k_2fke_ting` | Media Player | Hisense TV | 客廳海信電視 |
| `media_player.ke_ting_de_dian_shi` | Media Player | Google Cast | 客廳電視 Cast 播放器 |
| `binary_sensor.er_lou_ping_mu_gan_ying_zong_he_pan_duan` | Binary Sensor | Template Helper | 二樓 Wi-Fi 綜合感應（U6-Pro 2F） |
| `sensor.ke_ting_wen_du_chuan_gan_qi_temperature` | Sensor | Aqara Temperature | 客廳溫度感測 |
| `sensor.ke_ting_wen_du_chuan_gan_qi_humidity` | Sensor | Aqara Humidity | 客廳濕度感測 |
| `input_number.living_room_effective_apparent_temperature` | Input Number | Helper | 客廳體感有效溫度 |

### 3. 2F 餐廳與廚房區域 (Dining & Kitchen)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `switch.chu_fang_deng` | Switch | Terncy 廚房開關 | 廚房主燈 |
| `switch.can_ting_kan_deng` | Switch | Terncy 廚房開關2 | 餐廳崁燈 |
| `switch.can_ting_bi_deng` | Switch | Terncy 廚房開關2 | 餐廳壁燈 |
| `binary_sensor.chu_fang_xiao_mi_ren_ti_chuan_gan_qi_motion` | Binary Sensor | BLE Monitor (PIR1G) | 廚房小米人體動態感應器 |
| `binary_sensor.xiaomi_front_door_doorbell` | Binary Sensor | Xiaomi Switch / Doorbell | 二樓大門門鈴（單擊觸發） |
| `media_player.can_ting_homepod` | Media Player | Apple HomePod | 餐廳 HomePod |
| `switch.zhi_hui_cha_zuo_p125_can_ting_homepod` | Switch | TP-Link Tapo P125 | 餐廳 HomePod 智慧插座 |
| `switch.zhi_hui_cha_zuo_p125_bu_wen_deng` | Switch | TP-Link Tapo P125 | 捕蚊燈智慧插座 |

### 4. 2F 廁所區域 (Bathroom)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `switch.ce_suo_deng` | Switch | Terncy 廁所開關 | 二樓廁所燈 |
| `binary_sensor.ce_suo_xiao_mi_ren_ti_chuan_gan_qi_motion` | Binary Sensor | BLE Monitor (PIR1G) | 廁所小米人體動態感應器 |
| `input_boolean.toilet_light_manual_mode` | Input Boolean | Helper | 廁所感應燈手動鎖定模式 |
| `input_number.toilet_light_auto_off_delay` | Input Number | Helper | 廁所燈自動關閉延遲（秒） |

### 5. 3F 臥室區域 (3F Bedroom)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `media_player.san_lou_wo_shi_homepod` | Media Player | Apple HomePod | 三樓臥室 HomePod |
| `device_tracker.u6_lite_3f` | Device Tracker | UniFi Network | U6-Lite (3F) 無線基地台 |

### 6. 4F 臥室區域 (4F Bedrooms)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `device_tracker.u6_iw_4f` | Device Tracker | UniFi Network | U6-IW (4F Jerry) 基地台 |
| `device_tracker.u6_extender` | Device Tracker | UniFi Network | U6 Extender (4F Elay) 延伸器 |
| `device_tracker.iphone_16_jerry` | Device Tracker | UniFi Network | Jerry iPhone 16 追蹤器 |
| `device_tracker.unifi_16_cc_a1_4d_4f_42_default` | Device Tracker | UniFi Network | Elay iPhone 16 Pro Max 追蹤器 |

### 7. 5F 頂樓與書房區域 (5F Rooftop & Study)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `switch.shu_fang_deng` | Switch | Terncy 書房開關 | 五樓書房燈 |
| `switch.yang_tai_deng` | Switch | Terncy 頂樓開關 | 頂樓陽台燈 |
| `switch.ding_lou_chuang_tou_deng` | Switch | Smart Plug / Switch | 頂樓床頭燈 |
| `switch.ding_lou_tai_deng_pro` | Switch | Smart Plug / Switch | 頂樓檯燈 Pro |
| `fan.ding_lou_dian_feng_shan` | Fan | Xiaomi Fan Pro | 頂樓小米電風扇 2 Pro |
| `climate.ding_lou_ri_li_leng_qi` | Climate | JCI Hitachi TW | 頂樓日立冷氣 |
| `binary_sensor.ding_lou_she_ying_ji_motion` | Binary Sensor | UniFi Protect | 頂樓攝影機動態感測（原生） |
| `media_player.ding_lou_homepod` | Media Player | Apple HomePod | 頂樓 HomePod |
| `device_tracker.u6_iw_5f` | Device Tracker | UniFi Network | U6-IW (5F Kenny) 基地台 |
| `input_number.rooftop_effective_apparent_temperature` | Input Number | Helper | 頂樓體感有效溫度 |

### 8. 全棟樓梯間 (Staircases)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `switch.lou_ti_deng` | Switch | Terncy 一二樓樓梯開關 | 一至二樓樓梯燈 |
| `switch.er_san_lou_lou_ti_deng` | Switch | Terncy 二三樓樓梯開關 | 二至三樓樓梯燈 |
| `switch.san_si_lou_lou_ti_deng` | Switch | Terncy 三四樓樓梯開關 | 三至四樓樓梯燈 |
| `switch.ding_lou_lou_ti_deng` | Switch | Terncy 四五樓樓梯開關 | 頂樓樓梯燈 |
| `light.ding_lou_lou_ti_deng_yeelink` | Light | Yeelight Color 5 | 頂樓樓梯彩色氣氛燈 |
| `input_button.ding_lou_si_lou_lou_ti_deng_xiao_zheng` | Input Button | Helper | 頂樓四樓樓梯燈校正按鈕 |

### 9. 全戶系統、保全與車輛 (System, Security & Vehicles)
| 實體 ID (Entity ID) | 類型 | 設備 / 整合名稱 | 功能說明 |
|---|---|---|---|
| `binary_sensor.at_home_kenny` | Binary Sensor | Template Presence | Kenny 在家狀態 |
| `binary_sensor.at_home_elay` | Binary Sensor | Template Presence | Elay 在家狀態 |
| `binary_sensor.at_home_jerry` | Binary Sensor | Template Presence | Jerry 在家狀態 |
| `binary_sensor.at_home_iris` | Binary Sensor | Template Presence | Iris 在家狀態 |
| `binary_sensor.at_home_anyone_home` | Binary Sensor | Template Occupancy | 全家是否有人在家 |
| `binary_sensor.at_home_nobody_home` | Binary Sensor | Template Occupancy | 全家是否全員離家 |
| `sensor.at_home_count` | Sensor | Template Sensor | 在家總人數 |
| `sensor.at_home_who_home` | Sensor | Template Sensor | 在家成員名單 |
| `alarm_control_panel.udmse_kenny_alarm_manager` | Alarm Panel | UniFi Protect | UDM-SE 保全告警管理器 |
| `sensor.lpr_recognized_plate` | Sensor | UniFi / LPR AI | 車牌辨識結果 |
| `sensor.line_bot_target_user_id` | Sensor | Line Bot | 預設 LINE 推播目標 User ID |

---

## 三、 領域功能分類清單（Domain Registry）

### 1. 燈光與開關 (Lights & Switches)
* `switch.che_ku_zhu_deng`（車庫主燈）
* `switch.lou_ti_deng`（一二樓樓梯燈）
* `switch.er_san_lou_lou_ti_deng`（二三樓樓梯燈）
* `switch.san_si_lou_lou_ti_deng`（三四樓樓梯燈）
* `switch.ding_lou_lou_ti_deng`（頂樓樓梯燈）
* `switch.ke_ting_kan_deng`（客廳崁燈）
* `switch.ke_ting_bi_deng`（客廳壁燈）
* `switch.ke_ting_huan_rao_deng`（客廳環繞燈）
* `switch.ke_ting_xiao_deng`（客廳小燈）
* `switch.chu_fang_deng`（廚房主燈）
* `switch.can_ting_kan_deng`（餐廳崁燈）
* `switch.can_ting_bi_deng`（餐廳壁燈）
* `switch.ce_suo_deng`（廁所燈）
* `switch.shu_fang_deng`（書房燈）
* `switch.yang_tai_deng`（陽台燈）
* `switch.men_kou_deng`（門口燈）
* `switch.lu_deng`（路燈）
* `light.ding_lou_lou_ti_deng_yeelink`（頂樓樓梯彩色氣氛燈）

### 2. 動態、人體與占用感應器 (Motion, Occupancy & Presence)
* `binary_sensor.g6_instant_motion`（車庫 G6 Instant 攝影機動態 - UniFi 原生）
* `binary_sensor.ding_lou_she_ying_ji_motion`（頂樓攝影機動態 - UniFi 原生）
* `binary_sensor.che_ku_she_ying_ji_person_detected`（車庫人員偵測）
* `binary_sensor.che_ku_she_ying_ji_vehicle_detected`（車庫車輛偵測）
* `binary_sensor.chu_fang_xiao_mi_ren_ti_chuan_gan_qi_motion`（廚房動態感應）
* `binary_sensor.ce_suo_xiao_mi_ren_ti_chuan_gan_qi_motion`（廁所動態感應）
* `binary_sensor.che_ku_wa_fi_gan_ying_zong_he_pan_duan`（車庫 Wi-Fi 人員感應，含 30s delay_off）
* `binary_sensor.er_lou_ping_mu_gan_ying_zong_he_pan_duan`（二樓 Wi-Fi 人員感應，含 30s delay_off）
* `binary_sensor.at_home_kenny` / `at_home_elay` / `at_home_jerry` / `at_home_iris`（人員在家庭狀態）
* `binary_sensor.at_home_anyone_home` / `at_home_nobody_home`（全戶在離家綜合判定）

### 3. 環境與電量感測器 (Sensors & Battery)
* `sensor.ke_ting_wen_du_chuan_gan_qi_temperature`（客廳溫度）
* `sensor.ke_ting_wen_du_chuan_gan_qi_humidity`（客廳濕度）
* `sensor.ke_ting_men_suo_battery`（客廳門鎖電量）
* `sensor.0x00158d0002419b84_battery`（二樓門鈴電量）
* `sensor.at_home_kenny_ap_mac` / `sensor.at_home_kenny_location`（Kenny AP MAC 與中文樓層定位）
* `sensor.at_home_elay_ap_mac` / `sensor.at_home_elay_location`（Elay AP MAC 與中文樓層定位）
* `sensor.at_home_jerry_ap_mac` / `sensor.at_home_jerry_location`（Jerry AP MAC 與中文樓層定位）
* `sensor.at_home_iris_ap_mac` / `sensor.at_home_iris_location`（Iris AP MAC 與中文樓層定位）
* `sensor.at_home_kenny_ipad_ap_mac` / `sensor.at_home_kenny_ipad_location`（Kenny iPad AP MAC 與樓層定位）

### 4. 門窗、鐵門與門鎖 (Covers & Locks)
* `cover.garage`（1F 車庫鐵門）
* `lock.ke_ting_men_suo`（2F 客廳電子門鎖）

### 5. 保全與攝影機 (Security & Cameras)
* `camera.che_ku_she_ying_ji_medium_resolution_channel`（車庫攝影機 RTSP 串流）
* `alarm_control_panel.udmse_kenny_alarm_manager`（保全告警管理器）
* `binary_sensor.xiaomi_front_door_doorbell`（大門門鈴 HomeKit 橋接）

### 6. 家電設備 (Appliances)
* `fan.ke_ting_dian_feng_shan`（客廳小米電風扇）
* `fan.ding_lou_dian_feng_shan`（頂樓小米電風扇 2 Pro）
* `climate.ding_lou_ri_li_leng_qi`（頂樓日立冷氣）
* `media_player.hisense_vision_55e7k_2fke_ting`（客廳海信電視）
* `media_player.can_ting_homepod`（餐廳 HomePod）
* `media_player.san_lou_wo_shi_homepod`（三樓臥室 HomePod）
* `media_player.ding_lou_homepod`（頂樓 HomePod）

### 7. Helper 輔助實體 (Helpers)
* **通知開關 (Notification Booleans)**：
  * `input_boolean.notify_line_general_enable`（LINE 一般通知開關 🪧）
  * `input_boolean.notify_line_important_enable`（LINE 重要通知開關 ⚠️）
  * `input_boolean.notify_line_emergency_enable`（LINE 緊急通知開關 🚨）
  * `input_boolean.line_bot_quota_exhausted_notified`（LINE 配額用盡去重開關）
* **情境與模式開關 (Scene & Mode Booleans)**：
  * `input_boolean.aqara_zai_jia` / `aqara_li_jia` / `aqara_wan_an` / `aqara_zao_an`（情境橋接開關）
  * `input_boolean.emergency_mode_switch`（05E 緊急模式旗標）
  * `input_boolean.toilet_light_manual_mode`（廁所燈手動常亮旗標）
* **數值與設定 (Input Numbers)**：
  * `input_number.garage_light_cooldown_sec`（車庫燈手動關閉冷卻秒數，預設 30s）
  * `input_number.living_room_effective_apparent_temperature`（客廳體感溫度）
  * `input_number.rooftop_effective_apparent_temperature`（頂樓體感溫度）
  * `input_number.supply_batt_lowest_*`（全戶各感測器最低電量歷史記錄）
* **計時器 (Timers)**：
  * `timer.garage_light_manual_off_cooldown`（車庫燈手動關閉冷卻計時）
  * `timer.fan_auto_off_timer`（電風扇自動關閉計時）
* **按鈕與文字 (Buttons & Texts)**：
  * `input_button.ding_lou_si_lou_lou_ti_deng_xiao_zheng`（樓梯燈校正按鈕）
  * `input_button.ai_version_snapshot_clear`（快照清除按鈕）
  * `input_text.at_home_*_trackers`（各成員追蹤裝置清單）
  * `input_text.automation_package_version_manual`（更新包版本字串）
  * `input_text.automation_framework_version_manual`（自動化架構版本字串）

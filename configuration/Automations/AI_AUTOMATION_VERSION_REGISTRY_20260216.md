# AI 自動化版本與 ID 總表（2026-02-16）

> 用途：集中管理 `configuration/Automations/*AI.yaml` 的標準欄位，作為後續優化/比對基準。

## 統一規範（已套用）
- 每份 AI 自動化檔案皆具備：
  - `alias`
  - `id`
  - `description`
  - `mode`
  - `variables.automation_version`
- 版本字串統一使用：
  - 穩定版：`Vx.y.z`
  - 測試版：`Vx.y.z-beta.n`

## 依賴版本
- Helper 套件版本（`packages/helper.yaml`）：`V3.1`

## 現況總表

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Automations/00-2BLINE推播AI.yaml` | `00-2BLINE推播AI (V3.0)` | `ai_line_bot_quota_guard` | `V3.0` |
| `configuration/Automations/03苗栗天氣告知系統AI.yaml` | `03苗栗天氣告知系統AI (V3.0)` | `ai_miaoli_weather_disaster_notify` | `V3.0` |
| `configuration/Automations/08-5F頂樓自動上下樓情境AI.yaml` | `08-5F頂樓自動上下樓情境AI (V3.0)` | `ai_topfloor_stairs_scene` | `V3.0` |
| `configuration/Automations/08-5G書房燈感應AI.yaml` | `08-5G 書房燈感應AI (V3.1)` | `ai_08_5g_study_motion_light` | `V3.1` |
| `configuration/Automations/08-6離家保全系統AI.yaml` | `08-6離家保全系統AI (V3.0)` | `ai_away_security_system` | `V3.0` |
| `configuration/Automations/08-8A廚房感應燈AI.yaml` | `08-8A 廚房感應燈AI (V3.0)` | `ai_08_8a_kitchen_motion_light` | `V3.0` |
| `configuration/Automations/100B自動離家AI.yaml` | `100B自動離家AI (V3.0)` | `ai_auto_leave_system` | `V3.0` |
| `configuration/Automations/100C1客廳門鎖電量分級通知AI.yaml` | `100C1客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_stage_notify` | `V3.0` |
| `configuration/Automations/100C2客廳門鎖電量分級通知AI.yaml` | `100C2客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_cycle_calibration` | `V3.0` |
| `configuration/Automations/104-1車庫鐵門感應燈AI.yaml` | `104-1車庫鐵門感應燈AI (V3.1)` | `ai_104_1_garage_gate_motion_light` | `V3.1` |
| `configuration/Automations/104-2車牌辨識AI.yaml` | `104-2車牌辨識AI (V3.0 Beta2)` | `ai_lpr_recognition` | `V3.1-beta.1` |
| `configuration/Automations/104-3鐵門判斷未關提醒及作動AI.yaml` | `104-3鐵門判斷未關提醒及作動AI (V3.1)` | `ai_104_3_garage_gate_open_guard_and_autoclose` | `V3.1` |
| `configuration/Automations/106B網關異常警告AI.yaml` | `106B網關異常警告AI (V3.0)` | `ai_gateway_anomaly_guard` | `V3.0` |
| `configuration/Automations/21A_客廳電風扇整合控制AI.yaml` | `21A_客廳電風扇整合控制AI (V3.0)` | `ai_living_room_fan_integrated_control` | `V3.0` |
| `configuration/Automations/21B_客廳電風扇異常告警AI.yaml` | `21B_客廳電風扇異常告警AI (V3.0)` | `ai_living_room_fan_anomaly_alert` | `V3.0` |
| `configuration/Automations/22頂樓電風扇自動化AI.yaml` | `22頂樓電風扇自動化AI (V3.1)` | `ai_topfloor_fan_automation` | `V3.1` |

## 維護約定
- 調整邏輯時：
  1. 先更新檔內 `variables.automation_version`。
  2. 再同步本總表。
  3. 若有跨檔引用，優先保持 `id` 不變；若必須改 `id`，要全域搜尋後一併更新。


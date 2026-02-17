# AI 自動化版本與 ID 總表（2026-02-16）

> 用途：集中管理 `Automation/*AI.yaml` 的標準欄位，作為後續優化/比對基準。

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

## 現況總表

| File | Alias | id | automation_version |
|---|---|---|---|
| `Automation/00-2BLINE推播AI.yaml` | `00-2BLINE推播AI (V1.3)` | `line_bot_quota_guard` | `V1.3.0` |
| `Automation/03苗栗天氣告知系統AI.yaml` | `03苗栗天氣告知系統AI (V1.7)` | `ai_03_miaoli_weather_disaster_notify` | `V1.7.0` |
| `Automation/08-5F頂樓自動上下樓情境AI.yaml` | `08-5F頂樓自動上下樓情境AI (V2.0)` | `ai_08_5f_stairs_scene` | `V2.0.0` |
| `Automation/08-6離家保全系統AI.yaml` | `08-6離家保全系統AI (V1.6)` | `ai_08_6_away_security_system` | `V1.6.0` |
| `Automation/100B自動離家AI.yaml` | `100B自動離家AI (V2.8)` | `ai_leave_100b_v1beta9` | `V2.8.0` |
| `Automation/100C1客廳門鎖電量分級通知AI.yaml` | `100C1客廳門鎖電量分級通知AI (V2.3)` | `ai_100c1_doorlock_battery_stage_notify` | `V2.3.0` |
| `Automation/100C2客廳門鎖電量分級通知AI.yaml` | `100C2客廳門鎖電量分級通知AI (V2.4)` | `ai_100c2_doorlock_battery_cycle_calibration` | `V2.4.0` |
| `Automation/104-2車牌辨識AI.yaml` | `104-2車牌辨識AI (V1 Beta 4)` | `lpr_ai_beta_104_2` | `V1.4.0-beta.4` |
| `Automation/106B網關異常警告AI.yaml` | `106B網關異常警告AI (V1.6)` | `gateway_anomaly_guard_ai` | `V1.6.0` |
| `Automation/21A_客廳電風扇整合控制AI.yaml` | `21A_客廳電風扇整合控制AI (V2.2)` | `ai_21a_living_room_fan_integrated_control` | `V2.2.0` |
| `Automation/21B_客廳電風扇異常告警AI.yaml` | `21B_客廳電風扇異常告警AI (V2 Beta 4)` | `ai_21b_living_room_fan_anomaly_alert` | `V2.0.0-beta.4` |
| `Automation/22頂樓電風扇自動化AI.yaml` | `22頂樓電風扇自動化AI (V2.3)` | `ding_lou_dian_feng_shan_zi_dong_hua_ai_22` | `V2.3.0` |

## 維護約定
- 調整邏輯時：
  1. 先更新檔內 `variables.automation_version`。
  2. 再同步本總表。
  3. 若有跨檔引用，優先保持 `id` 不變；若必須改 `id`，要全域搜尋後一併更新。


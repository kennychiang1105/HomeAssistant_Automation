# AI 版本與 ID 總表（Automation + Script）

> 用途：集中管理 `configuration/Automations/*AI.yaml` 與 `configuration/Scripts/*AI.yaml` 的標準欄位，作為後續優化/比對基準。

## 統一規範（已套用）
- Automation 與 Script 皆需維持可追溯版本欄位（`variables.automation_version`）。
- 每份 AI 自動化檔案皆具備：
  - `alias`
  - `id`
  - `description`
  - `mode`
  - `variables.automation_version`
- 版本字串統一使用：
  - 穩定版：`Vx.y.z`
  - 測試版：`Vx.y.z (Beta n)`
  - 候選版：`Vx.y.z (RCn)`

## 依賴版本
- Helper 套件版本（`packages/helper.yaml`）：`V3.5`

## 現況總表（Automations）

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Automations/00-2BLINE推播AI.yaml` | `00-2BLINE推播AI (V3.2)` | `ai_line_bot_quota_guard` | `V3.2` |
| `configuration/Automations/00-2A更新紀錄推播AI.yaml` | `00-2A更新紀錄推播AI (V3.0)` | `ai_00_2a_release_note_push` | `V3.0` |
| `configuration/Automations/03苗栗天氣告知系統AI.yaml` | `03苗栗天氣告知系統AI (V3.0)` | `ai_miaoli_weather_disaster_notify` | `V3.0` |
| `configuration/Automations/05B緊急模式通知AI.yaml` | `05B緊急模式通知AI (V3.0)` | `ai_05b_emergency_mode_notify_v3` | `V3.0` |
| `configuration/Automations/05C按鈕自動復位AI.yaml` | `05C按鈕自動復位AI (V3.0)` | `ai_05c_emergency_button_auto_reset_v3` | `V3.0` |
| `configuration/Automations/05D緊急模式虛擬按鈕AI.yaml` | `05D緊急模式虛擬按鈕AI (V3.0)` | `ai_05d_emergency_virtual_button_bridge_v3` | `V3.0` |
| `configuration/Automations/08-5F頂樓自動上下樓情境AI.yaml` | `08-5F頂樓自動上下樓情境AI (V3.1)` | `ai_topfloor_stairs_scene` | `V3.1` |
| `configuration/Automations/08-5G書房燈感應AI.yaml` | `08-5G 書房燈感應AI (V3.1)` | `ai_08_5g_study_motion_light` | `V3.1` |
| `configuration/Automations/08-6離家保全系統AI.yaml` | `08-6離家保全系統AI (V3.0)` | `ai_away_security_system` | `V3.0` |
| `configuration/Automations/08-8A廚房感應燈AI.yaml` | `08-8A 廚房感應燈AI (V3.1)` | `ai_08_8a_kitchen_motion_light` | `V3.1` |
| `configuration/Automations/100B自動離家AI.yaml` | `100B自動離家AI (V3.1)` | `ai_auto_leave_system` | `V3.1` |
| `configuration/Automations/100C1客廳門鎖電量分級通知AI.yaml` | `100C1客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_stage_notify` | `V3.0` |
| `configuration/Automations/100C2客廳門鎖電量分級通知AI.yaml` | `100C2客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_cycle_calibration` | `V3.0` |
| `configuration/Automations/104-1車庫鐵門感應燈AI.yaml` | `104-1車庫鐵門感應燈AI (V3.2)` | `ai_104_1_garage_gate_motion_light` | `V3.2` |
| `configuration/Automations/104-2車牌辨識AI.yaml` | `104-2車牌辨識AI (V3.0 RC2)` | `ai_lpr_recognition` | `V3.0 (RC2)` |
| `configuration/Automations/104-3鐵門判斷未關提醒及作動AI.yaml` | `104-3鐵門判斷未關提醒及作動AI (V3.2)` | `ai_104_3_garage_gate_open_guard_and_autoclose` | `V3.2` |
| `configuration/Automations/106B網關異常警告AI.yaml` | `106B網關異常警告AI (V3.0)` | `ai_gateway_anomaly_guard` | `V3.0` |
| `configuration/Automations/21A_客廳電風扇整合控制AI.yaml` | `21A_客廳電風扇整合控制AI (V3.0)` | `ai_living_room_fan_integrated_control` | `V3.0` |
| `configuration/Automations/21B_客廳電風扇異常告警AI.yaml` | `21B_客廳電風扇異常告警AI (V3.0)` | `ai_living_room_fan_anomaly_alert` | `V3.0` |
| `configuration/Automations/22頂樓電風扇自動化AI.yaml` | `22頂樓電風扇自動化AI (V3.1)` | `ai_topfloor_fan_automation` | `V3.1` |

## 維護約定
- 調整邏輯時：
  1. 先更新檔內 `variables.automation_version`。
  2. 再同步本總表。
  3. 若有跨檔引用，優先保持 `id` 不變；若必須改 `id`，要全域搜尋後一併更新。


## AI 更新步驟與注意事項（SOP）

### SOP-1：LINE 通知文案原則（易懂優先）
1. LINE 通知內容要**口語且易懂**，優先描述「發生什麼事、系統做了什麼、使用者要知道什麼」。
2. 避免在 LINE 內容暴露技術參數或內部 entity/service 名稱（例如 `automation.xxx`、helper 參數細節）。
3. 技術細節保留在註解、版本紀錄或 persistent notification 即可。

### SOP-2：LINE 分級開關與標題格式（每次更新必做）
1. 一般通知：必須檢查 `input_boolean.notify_line_general_enable`，標題格式建議為 `【系統名稱】一般 General 🪧`。
2. 重要通知：必須檢查 `input_boolean.notify_line_important_enable`，標題格式建議為 `【系統名稱】重要 Important ⚠️`。
3. 緊急通知：必須檢查 `input_boolean.notify_line_emergency_enable`，標題格式建議為 `【系統名稱】緊急 Emergency 🚨` 或 `緊急 Urgent ‼️`（同系統內需一致）。
4. 不可跳過分級判斷直接送 LINE（除非明確有例外需求並在更新註解說明）。
5. 若原有獨立開關已被統一分級取代，需同步移除舊 helper 與引用，避免殭屍開關。
6. 通知內容需維持易懂：標題先顯示等級，再描述事件重點、系統動作與目前狀態。

### SOP-3：Helper 相容性檢查與註記（每次更新必做）
1. 調整自動化前，先確認使用到的 helper/sensor/input_* 是否存在且型別相容。
2. 若有新增或調整 helper，需同步更新 `packages/helper.yaml` 版本與說明。
3. 每一支受影響自動化檔案頂部註解需標示「相容版本：Helpers Vx.y（已確認）」。

### SOP-4：版本三方同步（通知 / Helper / Registry）
1. 任何影響通知或 helper 相依邏輯的更新，需同步檢查並更新：
   - 自動化檔案內 `automation_version` 與 alias 版本。
   - `packages/helper.yaml` 版本與更新紀錄。
   - `AI_VERSION_REGISTRY.md` 的依賴版本與現況總表。
2. 三方版本必須一致可追溯，避免「自動化已升版、Helper/Registry 未同步」。

### SOP-5：更新資訊連結（建議）
1. 與版本、配額或維運相關通知，建議附上更新紀錄網址：`https://github.com/kennychiang1105/HomeAssistant_Automation/releases/`。
2. 若通知字數有限，至少保留可追溯版本資訊（系統名 + 版本）。

### SOP-6：避免重複通知
1. 同一事件流若會觸發多段通知，需加上流程控制（`choose` / `stop` / 去重旗標）避免重複推播。
2. 「狀態說明通知」與「自動化結果通知」若可合併，優先合併為單一通知。
3. 通知需包含當前關鍵情境（例如目前情境狀態），降低使用者二次查詢成本。


### SOP-7：更新紀錄推播（00-2A）運作原理與更新點（每次改版必做）
1. **運作原理（變更才推播）**：
   - 00-2A 會讀取 `input_text.ai_version_snapshot_compact` 作為「上次版本快照」。
   - 將目前 HA 版本與 AI 元件版本組成新快照，比對後僅輸出有差異項目。
   - 若是新建立項目，舊版視為 `V0.0`，通知顯示 `V0.0 -> 新版本`。
2. **後續改版需要更新的地方**：
   - `configuration/Automations/00-2A更新紀錄推播AI.yaml`
     - `variables.ai_components`：新增/刪除/改版 AI 自動化與腳本時必須同步。
     - `variables.automation_version` 與 alias 版本。
   - `configuration/AI_VERSION_REGISTRY.md`
     - Automations/Scripts 現況總表版本號。
     - 「本次調整」條目（描述此次升版重點）。
   - `packages/helper.yaml`
     - 若 00-2A 依賴 helper 有增減，需同步版本與註記。
3. **驗證建議**：
   - 檢查 `ai_components` 與 registry 項目是否一致。
   - 檢查 `input_text.ai_version_snapshot_compact` 存在且可寫入。

## 現況總表（Scripts）

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Scripts/地震預警系統遠端AI.yaml` | `地震預警系統(遠端)AI (V3.2)` | `99999999999999` | `V3.2` |

## 本次調整（2026-03）
- 05 系列中 `05B/05C/05D` 已拆分為 AI 管理檔案（`configuration/Automations/*AI.yaml`），`05A` 保留於 `configuration/automations.yaml` 手動流程。
- 地震遠端腳本 `script.99999999999999` 已拆分至 `configuration/Scripts/地震預警系統遠端AI.yaml`，並由 `configuration/configuration.yaml` 新增 AI script include 載入。

- 版本總表更名為 `configuration/AI_VERSION_REGISTRY.md`，改為 Automation/Script 共用維護。
- 05B/05C/05D 緊急模式 AI 自動化統一升級為 `V3.0`，並同步更新 ID：`ai_05b_emergency_mode_notify_v3` / `ai_05c_emergency_button_auto_reset_v3` / `ai_05d_emergency_virtual_button_bridge_v3`。
- 地震遠端 Script AI（`script.99999999999999`）版本升級為 `V3.2`：震度分級調整為「2級以下僅通知、3級廣播不啟動緊急模式、4級以上維持緊急模式」，並同步分級通知（2級以下重要、3級以上緊急）。
- 已全域檢查 05B-05D 與地震 Script 的 ID/實體引用，未發現殘留舊 ID 參照。
- Helper 相容性檢查完成：本次流程依賴的 `notify_line_*` 與 `input_text.line_eew_remote_*` 已於 `packages/helper.yaml` 定義，維持 `Helpers V3.5`。

- 新增 `00-2A更新紀錄推播AI (V1.0)`：每日 18:00 推播 HA/AI 版本摘要到 HA 與 LINE（一般通知），並附更新紀錄網址。

- 00-2A更新紀錄推播AI 升級至 `V3.0`：納入全部 AI 自動化/腳本版本比對，僅在與上次版本快照不同時推播；新建項目以 `V0.0 -> 新版本` 顯示。

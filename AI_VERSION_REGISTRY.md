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
- Helper 套件版本（`packages/helper.yaml`）：`V3.14.1`
- configuration 套件版本（`packages/configuration.yaml`）：`V3.0`

## 現況總表（Automations）

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Automations/00-2BLINE推播AI.yaml` | `00-2BLINE推播AI (V3.3)` | `ai_line_bot_quota_guard` | `V3.3` |
| `configuration/Automations/00-01系統回應穩定自動化AI.yaml` | `00-01系統回應穩定自動化AI (V3.0.2)` | `ai_00_01_system_stability_auto_restart` / `ai_00_01_xiaoyan_gateway_watchdog` / `ai_00_01_unifi_protect_watchdog` | `V3.0.2` |
| `configuration/Automations/00-2A更新紀錄推播AI.yaml` | `00-2A更新紀錄推播AI (V3.3)` | `ai_00_2a_release_note_push` | `V3.3` |
| `configuration/Automations/00-2C耗材更換AI通知.yaml` | `00-2C耗材更換AI通知 (V3.0.3)` | `ai_00_2c_supply_battery_notify` | `V3.0.3` |
| `configuration/Automations/03苗栗天氣告知系統AI.yaml` | `03苗栗天氣告知系統AI (V3.0)` | `ai_miaoli_weather_disaster_notify` | `V3.0` |
| `configuration/Automations/05B緊急模式通知AI.yaml` | `05B緊急模式通知AI (V3.1)` | `ai_05b_emergency_mode_notify_v3` | `V3.1` |
| `configuration/Automations/05C按鈕自動復位AI.yaml` | `05C按鈕自動復位AI (V3.0)` | `ai_05c_emergency_button_auto_reset_v3` | `V3.0` |
| `configuration/Automations/05D緊急模式虛擬按鈕AI.yaml` | `05D緊急模式虛擬按鈕AI (V3.0)` | `ai_05d_emergency_virtual_button_bridge_v3` | `V3.0` |
| `configuration/Automations/100C_GoogleHome情境虛擬按鈕橋接AI.yaml` | `100C GoogleHome情境虛擬按鈕橋接AI (V3.0)` | `ai_100c_googlehome_scene_virtual_button_bridge` | `V3.0` |
| `configuration/Automations/08-5A五樓保全系統AI.yaml` | `08-5A五樓保全系統AI (V3.3.1)` | `ai_08_5a_5f_security_webhook_guard` | `V3.3.1` |
| `configuration/Automations/08-5F頂樓自動上下樓情境AI.yaml` | `08-5F頂樓自動上下樓情境AI (V3.3.1)` | `ai_topfloor_stairs_scene` | `V3.3.1` |
| `configuration/Automations/08-5C頂樓樓梯感應燈AI.yaml` | `08-5C頂樓樓梯感應燈AI (V3.4.0)` | `ai_08_5c_topfloor_stairs_motion_light` / `ai_08_5c_topfloor_stairs_motion_light_auto_off` | `V3.4.0` |
| `configuration/Automations/08-5G書房燈感應AI.yaml` | `08-5G 書房燈感應AI (V3.3.1)` | `ai_08_5g_study_motion_light` | `V3.3.1` |
| `configuration/Automations/08-6離家保全系統AI.yaml` | `08-6離家保全系統AI (V3.1)` | `ai_away_security_system` | `V3.1` |
| `configuration/Automations/08-8A廚房感應燈AI.yaml` | `08-8A 廚房感應燈AI (V3.1)` | `ai_08_8a_kitchen_motion_light` | `V3.1` |
| `configuration/Automations/100B自動離家AI.yaml` | `100B自動離家AI (V3.3.1)` | `ai_auto_leave_system` | `V3.3.1` |
| `configuration/Automations/100C1客廳門鎖電量分級通知AI.yaml` | `100C1客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_stage_notify` | `V3.0` |
| `configuration/Automations/100C2客廳門鎖電量分級通知AI.yaml` | `100C2客廳門鎖電量分級通知AI (V3.1)` | `ai_doorlock_battery_cycle_calibration` | `V3.1` |
| `configuration/Automations/100C3客廳門鎖電量下降時間紀錄AI.yaml` | `100C3客廳門鎖電量下降時間紀錄AI (V3.0)` | `ai_doorlock_battery_drop_timestamp_recorder` | `V3.0` |
| `configuration/Automations/104-1車庫鐵門感應燈AI.yaml` | `104-1車庫鐵門感應燈AI (V3.2)` | `ai_104_1_garage_gate_motion_light` | `V3.2` |
| `configuration/Automations/104-2車牌辨識AI.yaml` | `104-2車牌辨識AI (V3.0)` | `ai_lpr_recognition` | `V3.0` |
| `configuration/Automations/104-3鐵門判斷未關提醒及作動AI.yaml` | `104-3鐵門判斷未關提醒及作動AI (V3.3.1)` | `ai_104_3_garage_gate_open_guard_and_autoclose` | `V3.3.1` |
| `configuration/Automations/106網關系統AI.yaml` | `106網關系統AI (V3.1.1)` | `ai_gateway_anomaly_guard` | `V3.1.1` |
| `configuration/Automations/21A_客廳電風扇整合控制AI.yaml` | `21A_客廳電風扇整合控制AI (V3.1)` | `ai_living_room_fan_integrated_control` | `V3.1` |
| `configuration/Automations/21B_客廳電風扇異常告警AI.yaml` | `21B_客廳電風扇異常告警AI (V3.1)` | `ai_living_room_fan_anomaly_alert` | `V3.1` |
| `configuration/Automations/22頂樓電風扇自動化AI.yaml` | `22頂樓電風扇自動化AI (V3.2.1)` | `ai_topfloor_fan_automation` | `V3.2.1` |
| `configuration/Automations/107Tesla充電器狀態與通知AI.yaml` | `107Tesla充電器狀態與通知AI (V3.2.2)` | `ai_107_tesla_charger_status_notify` | `V3.2.2` |
| `configuration/Automations/08-5H頂樓深夜熟睡情境AI.yaml` | `08-5H頂樓深夜熟睡情境AI (V3.0.1)` | `ai_08_5h_topfloor_deep_sleep_scene_guard` | `V3.0.1` |
| `configuration/Automations/08-7A自動晚安情境AI.yaml` | `08-7A自動晚安情境AI (V3.0.2)` | `ai_08_7a_auto_goodnight_scene` | `V3.0.2` |

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
   - 00-2A 會讀取 `sensor.ai_version_registry_dynamic` 的 `versions` 屬性作為「目前版本快照」。
   - 00-2A 會讀取 `sensor.ai_version_snapshot_history` 的 `versions` 屬性作為「上次版本快照」。
   - 以 JSON 字典（Dictionary）逐鍵比對版本，僅輸出有差異項目（新增/升版/移除）。
   - 若是新建立項目，舊版視為 `V0.0`，通知顯示 `V0.0 -> 新版本`。
2. **後續改版需要更新的地方**：
   - `configuration/Automations/00-2A更新紀錄推播AI.yaml`
     - `variables.automation_version` 與 alias 版本。
   - `packages/helper.yaml`
     - `command_line.ai_version_registry_dynamic`：掃描路徑異動時需同步。
     - `template.ai_version_snapshot_history`：快照事件結構異動時需同步。
   - `configuration/AI_VERSION_REGISTRY.md`
     - Automations/Scripts 現況總表版本號。
     - 「本次調整」條目（描述此次升版重點）。
   - `packages/helper.yaml`
     - 若 00-2A 依賴 helper 有增減，需同步版本與註記。
3. **驗證建議**：
   - 檢查 `sensor.ai_version_registry_dynamic` 的 `versions` 屬性是否可正常產生。
   - 檢查 18:00 後 `sensor.ai_version_snapshot_history` 屬性是否已更新為最新 JSON。

### SOP-8：各獨立 AI 檔案頂部更新紀錄格式（每次更新必做）
1. 每個 `*AI.yaml` 檔案最上方需採用與 `100B自動離家AI.yaml` 一致的區塊格式：
   - 分隔線（`# ─────────────────────────────────────────────────────────────`）
   - 第一行：`# 檔名 (Vx.y.z)`
   - 第二行：`# 相容版本：Helpers Vx.y（已確認）`
   - 第三行：`# 更新紀錄（統一格式）：`
   - 後續以 `# - Vx.y.z：...` 由新到舊條列變更內容。
2. 同檔版本升級時，必須同步更新：
   - 頂部區塊版本。
   - `alias` 版本。
   - `variables.automation_version`。
3. 若同檔含多個 automation 區塊，版本號需一致，避免 registry 與通知版本不一致。

### SOP-9：版本號進位判斷規則（每次改版必做）
1. 穩定版版本號一律使用 `Vx.y.z`（語意化管理）。
2. **功能新增 / 行為擴充 / 流程重構**：升級次版本（`y + 1`，`z` 歸零），例如 `V3.3.1 -> V3.4.0`（可簡寫為 `V3.4`）。
3. **Bug 修復 / 小幅校正 / 文案或同步修正**：升級修補版（`z + 1`），例如 `V3.3 -> V3.3.1`、`V3.0 -> V3.0.1`。
4. 每次改版需在更新紀錄註明本次屬於「功能版」或「修補版」，並同步更新 alias、`variables.automation_version`、Registry 條目。(Helper與configuration套件版本每次確認之)
5. 同一個PR或Codex同一次僅需更新一次版本號

### SOP-10：LINE 發送可靠性防呆（每次涉及通知必做）
1. **LINE 一律使用 `script.send_line_to_user`**（避免直接呼叫 `notify.line_*` 造成 DNS/整合暫時失效時中斷流程）。
2. 發送前必做三項檢查：
   - 目標 `user_id` 不可為 `unknown/unavailable/none/空字串`。
   - 對應分級開關（一般/重要/緊急）必須為 `on`。
   - 若有子系統額外開關（如 Tesla/耗材額外 LINE 開關）也必須為 `on`。
3. payload 格式統一為 JSON message array（多則訊息），至少包含：
   - 第 1 則：版本標題（例：`【系統名稱AI (Vx.y.z)】` + 等級行）。
   - 第 2 則：事件主訊息（發生什麼事 + 關鍵時間/狀態）。
   - 需要時第 3 則：補充資訊（溫度、電量、附註）。
4. 任何一項檢查不通過時：
   - 不可硬送 LINE。
   - 必須留下 `persistent_notification` 或 logbook 記錄「未發送原因」（例：user_id 無效 / 開關關閉）。
5. 新增或修改通知時，PR 必須附「最小驗證清單」：
   - 一般/重要/緊急各至少 1 條 payload 範例。
   - 開關關閉時不發送的驗證結果。
   - `user_id` 無效時 fallback 記錄結果。

## 現況總表（Scripts）

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Scripts/地震預警系統遠端AI.yaml` | `地震預警系統(遠端)AI (V3.4)` | `eq99` | `V3.4` |

## 本次調整（2026-05-30 Tesla 完成通知與網關重啟靜音）
- `107Tesla充電器狀態與通知AI` 修補版升級至 `V3.2.2`：充電完成通知於用電量上方新增「充電用時 X時X分鐘」；一般 LINE 仍使用 `script.send_line_to_user`，並保留一般分級開關、Tesla 額外 LINE 開關與 user_id 有效性檢查，不通過時留下 `persistent_notification` 未發送原因，符合 SOP-10。
- `106網關系統AI` 修補版升級至 `V3.1.1`：HA 重開機觸發時只執行情境/網關同步，不發送 persistent notification 或 LINE；非 HA 重啟的異常攔截 LINE 仍走 `script.send_line_to_user` 並保留緊急分級開關、user_id 防呆與未發送 fallback，符合 SOP-10。

## 本次調整（2026-05-30 樓梯燈與晚安情境調整）
- `08-5C頂樓樓梯感應燈AI` 功能版升級至 `V3.4.0`：輔助關燈改依主流程最近來源分流；書房線/樓梯線直接放行，臥室線/攝影機 2.5 秒內攔截、2.5～10 秒放行，超過 10 秒一律放行。
- `08-7A自動晚安情境AI` 修補版升級至 `V3.0.2`：移除 night_check 定時觸發，二樓無人等待改為 30 秒，並取消執行訊息通知。
- LINE 通知檢查：本次兩份自動化皆未新增或修改 LINE 發送；08-7A 反而移除執行訊息通知，因此 SOP-10 無需新增 payload，且不會出現繞過 `script.send_line_to_user` 的 LINE 呼叫。

## 本次調整（2026-05-30 Tesla 充電記憶修補）
- `107Tesla充電器狀態與通知AI` 升級至 `V3.2.1`：修補版。插槍後若直接進入 `charging` / `charging_reduced`，`charge_done` 的當次已充電記憶重設流程會排除充電中狀態，避免 `input_boolean.tesla_charger_session_charged` 先開啟又瞬間關閉；LINE 發送維持 `script.send_line_to_user`，補齊 user_id 有效性檢查、一般/重要分級開關與 Tesla 額外開關判斷，以及未發送原因 `persistent_notification` fallback，符合 SOP-10。

## 本次調整（2026-05-30 樓梯燈防呆邏輯修補）
- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.3.4`：修正輔助關燈 8～180 秒防呆取值方式，改從主流程與備援舊 ID 的 `last_triggered` 中取最新時間，避免 `or` 只取第一個非空時間而忽略近期備援點燈紀錄；本次未新增或修改 LINE 發送流程，SOP-10 不適用但已確認 08-5C 無直接 `notify.line_*` 呼叫。

## 本次調整（2026-05-30 樓梯燈誤關修補）
- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.3.3`：重新啟用輔助關燈時間差防呆，主流程點燈後 8 秒內禁止書房左側感應器觸發輔助關燈，避免剛出房間關門或路過造成樓梯燈誤關；本次未新增或修改 LINE 發送流程，SOP-10 不適用但已確認無直接 `notify.line_*` 呼叫。

## 本次調整（2026-05-30 深夜補強）
- Helper 套件修補版升級至 `V3.14.1`：新增 `binary_sensor.che_ku_wa_fi_gan_ying_zong_he_pan_duan` 與 `binary_sensor.er_lou_ping_mu_gan_ying_zong_he_pan_duan`，沿用 AtHome AP MAC 區域判斷邏輯，補齊 104-3 與 08-7A 依賴實體。
- `104-3鐵門判斷未關提醒及作動AI` 升級至 `V3.3.1`：同步 Helper 相容版本，LINE 標題補版本字串，並明確記錄分級開關關閉或 user_id 無效時的未發送原因，符合 SOP-10。
- `08-7A自動晚安情境AI` 升級至 `V3.0.1`：同步 Helper 相容版本，確認二樓無人判斷 helper 已由 Helper 套件建立。

## 本次調整（2026-05-30 晚間追加）
- `106網關系統AI` 升級至 `V3.1`：正式改名並接管舊版 106 網關同步邏輯，移除舊自動化 ID `1690898378439`，以異常攔截 / 常規同步 / 解除歸位 / 無情境歸位分流避免 Race Condition，LINE 緊急通知依 SOP-10 走 `script.send_line_to_user` 並保留未發送 fallback。
- 新增 `08-7A自動晚安情境AI (V3.0)`：於 21:00 後或 03:00 前，二樓 AP/人員綜合判定無人且晚安情境尚未啟用時自動執行晚安情境。
- `104-3鐵門判斷未關提醒及作動AI` 升級至 `V3.3`：自動關門前新增車庫 AP 人員綜合判定，偵測有人時取消關門且不影響逾時未關提醒；車庫主燈變化排除 unknown/unavailable 抖動，AP 攔截補 LINE 結果通知。
- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.3.2`：攝影機防呆冷卻由 15 秒縮短至 10 秒，燈具實體狀態防呆由 5 秒縮短至 2 秒。

## 本次調整（2026-05-30 追加修補）
- `08-5A` / `08-5C` / `08-5F` / `08-5G` 修補版升級至 `V3.3.1`：補強手動執行時 `trigger` 未定義防呆，修正 08-5F 下樓 3 分鐘保護窗後 AP 複檢改用即時狀態，並修復 08-5A LINE user_id 為 unknown 時 fallback 失效。

## 本次調整（2026-05-30 追加）
- `08-5A五樓保全系統AI` 升級至 `V3.3`：威脅判斷改為只使用 `5fbedroomline` / `5fstudyroomline` / `5fstairsline` 的 Webhook 時間鏈，避免原感應器造成保全誤報。
- `08-5C` / `08-5F` / `08-5G` 升級至 `V3.3`：新增 `input_select.topfloor_webhook_mode` 統一模式選擇，可切換「綜合模式」（Webhook + 原本）、「Webhook模式」（只用 Webhook）、「原本模式」（回到原本判斷）。
- Helper 套件功能版升級至 `V3.14`：新增 `input_select.topfloor_webhook_mode` 供頂樓 Webhook 判斷模式統一切換。

- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.2`：新增三條跨線 Webhook 補燈與樓梯提前亮燈，房門/書房門補燈直接繞過冷卻防呆並以 `mode: restart` 刷新 2 分 30 秒倒數。
- `08-5F頂樓自動上下樓情境AI` 升級至 `V3.2`：完整保留原攝影機、AP、光源、保護窗與 Debug 判定流程，額外新增跨線時間鏈作為上/下樓秒級加速選項。
- `08-5G書房燈感應AI` 升級至 `V3.2`：完整保留原實體動態感應、AP 與攝影機延長判定，額外新增進書房秒開燈、靜坐防熄滅攔截、離開書房回房秒關與下樓 3 分鐘守候模式。
- 新增 `08-5A五樓保全系統AI (V3.2)`：將 `configuration/automations.yaml` 內原兩個 `08-5A 五樓保全系統`（含 Auto Beta）與 Webhook 加速補強獨立拆分至 AI 管理檔案，原手動/自動保全邏輯保留。
- Helper 套件功能版升級至 `V3.13`：新增五樓跨線最後觸發時間、書房進出推理時間與五樓保全手動解除開關；LINE 重要通知沿用 `input_boolean.notify_line_important_enable`，Kenny 在家判斷沿用既有 `binary_sensor.at_home_kenny`。

## 本次調整（2026-05-29）
- `107Tesla充電器狀態與通知AI` 升級至 `V3.2.0`：充電完成改以 charging/charging_reduced 離開至未連接或等待/準備狀態判斷，並結合當次插槍已充電記憶避免午夜與 6 小時未充電誤報。
- Helper 套件升級至 `V3.12.2`：新增 `input_boolean.tesla_charger_session_charged`，記錄當次插槍期間是否已開始充電。

## 本次調整（2026-05-28）
- `00-2C耗材更換AI通知` 升級至 `V3.0.3`：修復濾芯壽命重複通知問題（避免 unknown/unavailable 抖動），並在推播中明確標示為「空氣清淨機濾芯壽命」。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.1.4`：修復充電狀態因為 unknown 而導致的多次重複開始通知與完成時間錯誤；移除冗餘的額外系統通知，使 HA 通知與 LINE 通知數量與資訊保持一致。
- `00-01系統回應穩定自動化AI` 維持 `V3.0.2`：確認週期重啟維持 `hassio.host_reboot` 全機重啟，而非單純重載。
- Helper 套件：新增 `input_datetime.tesla_charger_start_time` 供 107Tesla 精準記錄開始時間。

## 本次調整（2026-05-23）
- `107Tesla充電器狀態與通知AI` 升級至 `V3.1.3`：開始通知調整為非充電狀態進入 charging/charging_reduced 即通知，移除對來源狀態過度限制；6 小時未充電維持待充狀態判斷；重要 LINE 通知標題統一含版本並新增測試通知按鈕。
- Helper 套件升級至 `V3.12.1`：新增 `input_button.tesla_charger_notify_test` 供 Tesla 充電通知測試。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.1.2`：開始通知改為僅在 idle/未連接→charging(Tesla) 或 charging_reduced(Luxgen) 觸發；完成通知僅在 charging*→未連接/完成 觸發；移除車種互轉觸發並修正 6 小時未充電誤報。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.1.1`：修正 Tesla/Luxgen 互轉時開始/完成通知邏輯，並將「連接 6 小時未充電」限制在待充且無充電能量時才通知，避免誤報。
- `00-01系統回應穩定自動化AI` 升級至 `V3.0.2`：固定主機重啟改為獨立時刻觸發，避免受小燕/攝影機看門狗重載影響重新計時。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.1.0`：通知格式統一為分段多訊息（含版本、emoji、換行），並補上 `kWh（度）` 單位。
- `00-2C耗材更換AI通知` 升級至 `V3.0.2`：修復 unknown/浮動造成重複電量提醒，LINE 發送方式統一為 `script.send_line_to_user`。
- Helper 套件升級至 `V3.12.0`：AtHome location 新增 unknown 2 分鐘緩衝，先顯示「離家確認中」再切換「離家」。
- 同次更新增補（版本號不變）：`00-01` 固定重啟時刻改為可調整兩個 helper 時間；`00-2C` 改為各裝置最低電量記錄（需 >=90% 才重設）；AtHome unknown 超過 10 分鐘顯示「異常」。
- 同次更新增補（版本號不變）：新增 SOP-10「LINE 發送可靠性防呆」，明確規範 `script.send_line_to_user`、payload 格式與未發送 fallback 記錄。
- 同次更新增補（版本號不變）：修正 `00-2C` 電池更換判斷，新增「較最低值回升 30% 以上視為更換」重設條件，並改為 `automation_version` 動態帶入標題。

## 本次調整（2026-05-18）
- `107Tesla充電器狀態與通知AI` 升級至 `V3.0.5`：00:02 僅在「準備充電/等待汽車」通知；充電完成狀態不通知。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.0.4`：修正 `session_energy` 不會即時歸零問題，00:02 改以「今日 00:00 後是否有充電能量更新」判斷。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.0.3`：恢復 00:02 未充電提醒，但僅在尚無充電完成紀錄（session_energy=0）時通知，避免充電完成後誤報。
- `107Tesla充電器狀態與通知AI` 升級至 `V3.0.2`：移除 00:02 未充電提醒避免充電完成後誤報，並新增 booting/ready/negotiating/error 未充電狀態（error 立即重要通知）。

## 本次調整（2026-05-17）
- `107Tesla充電器狀態與通知AI` 升級至 `V3.0.1`：充電完成但用電量為 0 不通知，LINE 改走 `script.send_line_to_user` 以避免 notify_line DNS 錯誤中斷。
- 新增 `00-2C耗材更換AI通知 (V3.0.1)`：整合空氣清淨機濾芯與多裝置電量分級通知，含定期摘要。
- `00-2A更新紀錄推播AI` 升級至 `V3.3`：新增手動輸入更新說明欄位並附加於推播。
- `00-2BLINE推播AI` 升級至 `V3.3`：低額度預警改為僅 Bot0，例行摘要改每月 1 日與 15 日。
- Helper 套件修補版升級至 `V3.11.1`：新增 `input_datetime.supply_battery_last_report_time` 供 00-2C 定期摘要獨立計時。

- 新增 `107Tesla充電器狀態與通知AI (V3.0)`：加入 Tesla/Luxgen 充電開始與完成通知、00:02 與連接 6 小時未充電的重要提醒，並整合系統通知與 LINE 分級推播。
- Helper 套件功能版升級至 `V3.10`：新增 Tesla 充電器 HomeKit helper（充電樁狀態 / Luxgen充電 / Tesla充電）與 Tesla 充電通知額外開關。

- Helper 套件修補版升級至 `V3.9.5`：AtHome AP MAC 感測器在離家時由 `unknown` 改為 `離家`，並同步讓位置感測器顯示 `離家`。
- `00-01系統回應穩定自動化AI` 修補版升級至 `V3.0.1`：補上完整 logbook（含主機重啟/小燕重載/Unifi Protect 監測結果）、恢復小燕網關看門狗，並移除依賴 initial 的 helper 設計。
- AtHome helpers 已整合至 `packages/helper.yaml`，不再需要獨立 `packages/AtHome.yaml`。
- 新增 `00-01系統回應穩定自動化AI (V3.0.1)`：合併原 `00-1` 與 `00-1B`，並加入 AtHome/鐵門觸發後 1 小時無相機狀態更新即重載 Unifi Protect integration 的看門狗。
- 原 `configuration/automations.yaml` 中 `00-1`、`00-1B` 已移除，改由 AI managed 檔案接管。

## 本次調整（2026-04-18）
- Helper 套件修補版升級至 `V3.9.4`：修復 `sensor.ai_li_jia_ban_ben_template` 被 `homeassistant.update_entity` 強制更新時觸發 `NotImplementedError`；`AI離家版本同步器` 升級為 `v3.2` 並移除該強制更新動作，改由 trigger-based template 自然更新。
- Helper 套件修補版升級至 `V3.9.3`：補上遺失的 `sensor.ai_li_jia_ban_ben_template` template 宣告，修復 `AI離家版本同步器` 強制更新時的 `Entity ... not found` 警告；同步將 `AI離家版本同步器` 升級為 `v3.1` 並新增 `variables.automation_version` 以符合 SOP。

## 本次調整（2026-04-10）
- Helper 套件修補版升級至 `V3.9.2`：優化版本快照基準模板 `current_versions` 的初始化，改為直接使用 `registry_versions` mapping，移除迴圈逐筆複製以降低模板計算成本。
- `22頂樓電風扇自動化AI` 修補版升級至 `V3.2.1`：修復 `t_eff` 在感測器暫時失效時（`none/unavailable`）造成 `float` 轉型錯誤，補強 `t_eff_valid` 判斷並加入安全預設值，避免自動化中斷。
- Helper 套件修補版升級至 `V3.9.1`：將版本比對模板中的 `dict.update()` 全數改為安全的 `dict(...)` 重新指派寫法，修復新版 Jinja2 的 `SecurityError` 限制。
- `08-5C頂樓樓梯感應燈AI` 修補版升級至 `V3.0.1`：主流程防呆由 8 秒調整為 15 秒，降低關燈後感測延遲造成誤重開。
- `08-5H頂樓深夜熟睡情境AI` 修補版升級至 `V3.0.1`：改為下樓情境執行後 1 分鐘檢查床頭燈（`light.yeelink_bslamp2_4329_light`）是否關閉；若失敗自動重跑一次下樓流程，僅在確認成功後才恢復風扇狀態。
- `100B自動離家AI` 修補版升級至 `V3.3.1`：LINE 通知標題統一移除「100B」編號顯示，並改以 `automation_version` 動態帶入版本，避免版本號未同步更新。
- 新增 SOP-8：後續每個獨立 `*AI.yaml` 檔案頂部更新紀錄格式需參照 `100B自動離家AI.yaml`。
- 新增 SOP-9：依「功能版 / 修補版」判斷版本進位，明確區分 `V3.4` 與 `V3.3.1` 類型升版。

## 本次調整（2026-03）
- 05 系列中 `05B/05C/05D` 已拆分為 AI 管理檔案（`configuration/Automations/*AI.yaml`），`05A` 保留於 `configuration/automations.yaml` 手動流程。
- 地震遠端腳本 `script.99999999999999` 已拆分至 `configuration/Scripts/地震預警系統遠端AI.yaml`，並由 `configuration/configuration.yaml` 新增 AI script include 載入。

- 版本總表更名為 `configuration/AI_VERSION_REGISTRY.md`，改為 Automation/Script 共用維護。
- 05B/05C/05D 緊急模式 AI 自動化統一升級為 `V3.0`，並同步更新 ID：`ai_05b_emergency_mode_notify_v3` / `ai_05c_emergency_button_auto_reset_v3` / `ai_05d_emergency_virtual_button_bridge_v3`。
- 地震遠端 Script AI（`script.99999999999999`）版本升級為 `V3.3`：震度解析改為正則擷取數字，`5- / 5+ / 6- / 6+ / 7` 均可正確判定分級。
- 已全域檢查 05B-05D 與地震 Script 的 ID/實體引用，未發現殘留舊 ID 參照。
- Helper 相容性檢查完成：本次流程依賴的 `notify_line_*` 與 `input_text.line_eew_remote_*` 已於 `packages/helper.yaml` 定義，維持 `Helpers V3.5`。

- 00-2A更新紀錄推播AI 版本演進：`V1.0`（建立每日 18:00 更新推播）→ `V3.0`（變更才推播）→ `V3.1`（改為 key-based 版本快照比對，避免元件順序異動造成誤判）→ `V3.2`（改為動態掃描版本 + trigger-based template snapshot，並修正 event JSON 型別保存）。

- 08-5C 頂樓樓梯感應燈（含自動關閉）已由 `configuration/automations.yaml` 拆分為 `configuration/Automations/08-5C頂樓樓梯感應燈AI.yaml`，並改用標準 ID：`ai_08_5c_topfloor_stairs_motion_light` / `ai_08_5c_topfloor_stairs_motion_light_auto_off`；已同步修正 `1747324079989` 的跨檔 automation 參照。
- 104-2 車牌辨識AI 由 `V3.0 (RC2)` 轉為正式 `V3.0`，車輛駛出安全緩衝由 90 秒調整為 45 秒。



- 08-5C頂樓樓梯感應燈AI 維持 `V3.0`：同次改版內完成左側感應關燈邏輯優化（精簡流程並避免分支衝突造成漏關燈），並在主流程新增 8 秒防呆避免關燈後攝影機延遲訊號立刻重開。

- 22頂樓電風扇自動化AI 升級至 `V3.2`：
  - 修正「手動開啟」會強制清除 `input_boolean.ding_lou_fan_cold_off_memory`，避免後續誤觸回溫再開。
  - 修正「手動關機」改為不受溫度限制；HomeKit 手動操作亦視為手動，但可透過系統保護窗排除情境腳本造成的關機。
  - 新增手動調速防護罩（頂樓/客廳），人為調速後跳過 AI 自動調速，並於風扇下次開機時自動解除。
- 新增 `08-5H頂樓深夜熟睡情境AI (V3.0)`：平日 `03:00`、假日 `05:00` 自動執行下樓情境，並在 HomeKit 外部關閉風扇時做風扇救援，維持 AI 溫控軌道。
- `configuration/automations.yaml` 已移除過時 UI 自動化 `12客廳電視自動化` 與 `13遙控器轉台`，並備份至 `deprecated_automations_backup/12_13_legacy_tv_remote_automations.yaml`。
- Helper 相容性檢查完成：本次新增頂樓/客廳手動調速防護罩 helper，`packages/helper.yaml` 版本同步升級至 `V3.6`。
- 100B自動離家AI 升級至 `V3.3`：維持切換成功後續行完整通知，並在完整通知中新增「本次已自動切換為離家情境（切換成功）」提示（僅原先非離家且切換成功時顯示）。
- 新增 `100C3客廳門鎖電量下降時間紀錄AI (V3.0)`：僅在門鎖電量有效下降時寫入 `input_datetime.doorlock_batt_last_drop_time`。
- 100C2客廳門鎖電量分級通知AI 升級至 `V3.1`：換電池校正時同步重設 `input_datetime.doorlock_batt_last_drop_time`，避免跨循環舊時間戳導致剩餘天數短暫顯示 0。
- Helper 升級至 `V3.7`：新增 `input_datetime.doorlock_batt_last_drop_time`，並修正剩餘天數估算改採 helper 時間戳，避免 HA 重啟重置 `last_changed` 造成天數反彈。

- 21A_客廳電風扇整合控制AI 升級至 `V3.1`：導入手動調速防護罩（下次開機解除）、manual actor 判斷與 null-safe 條件，避免 AI 與手動調速互搶。
- 廣播設備清理（2026-04）：已移除 `media_player.sony_bravia_tv` 相關音量/切源/狀態判斷流程，避免已下線設備造成自動化錯誤。
- 廣播設備清理延伸修正（2026-04-08）：05B / 08-6 / 21B 與地震遠端 Script 移除已下線 TV remote 實體引用（`61eaa5fb8386221ba077bcb884e74573`），避免 `Unknown entity` 導致自動化與腳本設定失敗；版本升級為 05B V3.1、08-6 V3.1、21B V3.1、EQ Script V3.4。
- 後續廣播更新約定：原 Sony TV 控制位置已統一改以 `# TVSPEAKERTODO:` 註記；未來導入新設備時，優先搜尋 `TVSPEAKERTODO` 後補上新設備音量與播放指令即可。

- Google Home 情境觸發橋接（2026-04）：新增 `100C_GoogleHome情境虛擬按鈕橋接AI`，以 `input_boolean.google_scene_*` 觸發 `100/101/102/103` 情境自動化，並在觸發後自動復位。
- Helper 升級至 `V3.9`：新增 Google Home 情境虛擬按鈕 helpers（早安/晚安/到家/出門）。

# Home Assistant 自動化整理基線（2026-02-16）

> 目的：先建立**現況盤點**，作為下一階段「優化與冗餘清理」的共同基準。  
> 範圍：`FullHistory/full_automations_20260307.yaml`、各 `*AI.yaml`、`packages/helper.yaml`。

---

## 1) 檔案分層現況

### A. 歷史完整快照（Monolith）
- `configuration/Automations/FullHistory/full_automations_20260307.yaml`
- 內容：完整自動化清單（109 筆 alias）。
- 角色：**凍結參考**（來源真相 / 回溯用），不建議直接當日常維護主檔。

### B. AI 可維護拆分檔（Modular）
目前獨立維護的自動化如下（12 份）：

| 檔案 | Alias | id | 與 full_automations_20260307 對照 |
|---|---|---|---|
| `configuration/Automations/00-2BLINE推播AI.yaml` | `00-2BLINE推播AI (V3.0)` | `ai_line_bot_quota_guard` | ✅ 可對上 |
| `configuration/Automations/03苗栗天氣告知系統AI.yaml` | `03苗栗天氣告知系統AI (V3.0)` | `ai_miaoli_weather_disaster_notify` | ✅ 可對上 |
| `configuration/Automations/08-5F頂樓自動上下樓情境AI.yaml` | `08-5F頂樓自動上下樓情境AI (V3.0)` | `ai_topfloor_stairs_scene` | ✅ 可對上 |
| `configuration/Automations/08-6離家保全系統AI.yaml` | `08-6離家保全系統AI (V3.0)` | `ai_away_security_system` | ✅ 可對上 |
| `configuration/Automations/100B自動離家AI.yaml` | `100B自動離家AI (V3.0)` | `ai_auto_leave_system` | ⚠️ Alias 版本字串未直接對上（疑似版本漂移） |
| `configuration/Automations/100C1客廳門鎖電量分級通知AI.yaml` | `100C1客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_stage_notify` | ✅ 可對上 |
| `configuration/Automations/100C2客廳門鎖電量分級通知AI.yaml` | `100C2客廳門鎖電量分級通知AI (V3.0)` | `ai_doorlock_battery_cycle_calibration` | ✅ 可對上 |
| `configuration/Automations/104-2車牌辨識AI.yaml` | `104-2車牌辨識AI (V3.0 Beta 1)` | `ai_lpr_recognition` | ✅ 可對上 |
| `configuration/Automations/106B網關異常警告AI.yaml` | `106B網關異常警告AI (V3.0)` | `ai_gateway_anomaly_guard` | ✅ 可對上 |
| `configuration/Automations/21A_客廳電風扇整合控制AI.yaml` | `21A_客廳電風扇整合控制AI (V3.0)` | `ai_living_room_fan_integrated_control` | ✅ 可對上 |
| `configuration/Automations/21B_客廳電風扇異常告警AI.yaml` | `21B_客廳電風扇異常告警AI (V3.0)` | `ai_living_room_fan_anomaly_alert` | ✅ 可對上 |
| `configuration/Automations/22頂樓電風扇自動化AI.yaml` | `22頂樓電風扇自動化AI (V3.0)` | `ai_topfloor_fan_automation` | ✅ 可對上 |

### C. 全局 helper 套件
- `packages/helper.yaml`
- 角色：提供跨自動化可重用實體（`input_boolean` / `input_number` / `timer` / `input_datetime` / template 等）。
- 特性：版本日誌詳細、覆蓋範圍廣，是目前「共用能力核心」。

---

## 2) 目前可見風險與冗餘熱點

### 2.1 單一來源（Source of Truth）尚未明確
- 同時存在「完整快照」與「拆分檔」兩種版本來源。
- 風險：修 A 忘記回寫 B，造成行為/版本註解不一致。

### 2.2 命名與 id 一致性不足
- 部分拆分檔未宣告 `id`，不利於後續重構追蹤。
- 版本字串格式混用（`V2.8`、`V1 Beta 4`、帶引號與不帶引號）。

### 2.3 通知邏輯跨檔重複傾向
- 多檔自動化重複使用 LINE 通知判斷（一般/重要/緊急、quota guard）。
- 建議再抽象為 script/template（若尚未全抽）。

### 2.4 風扇/保全/門鎖是高耦合區
- `21A/21B/22/08-5F/08-6/100B/100C1/100C2/106B` 彼此透過 helpers 互相影響。
- 優化時需先鎖定共用實體契約，避免「修一壞三」。

---

## 3) 建議的清理策略（建議先後順序）

> 執行狀態（2026-02-16）：
> - Phase 0：✅ 已完成（主維護來源與雙軌方式已定義）。
> - Phase 1：🟡 進行中（欄位/版本/ID 已統一，註解模板待最後定稿）。
> - Phase 2：🟡 進行中（已完成 08-5G 模組拆分、08-8A 開關邏輯合併）。
> - Phase 3：⬜ 尚未開始。

### Phase 0（先做，不改行為）
1. 固定「主維護來源」：
   - 建議以 **拆分 `*AI.yaml` + `packages/helper.yaml`** 為主。
   - `FullAutomationHistory/*` 保持只讀快照。
2. 制定欄位標準：每個自動化至少有
   - `alias`
   - `id`
   - `description`
   - `mode`
   - `variables.automation_version`

### Phase 1（低風險整潔）
1. 版本與命名正規化：
   - 例如統一 `Vx.y.z` 格式。
2. 補齊缺失 `id`。
3. 建立共用註解模板（檔頭 changelog 格式統一）。

### Phase 2（中風險，減冗餘）
1. 已完成：`08-5G 書房燈感應` 拆分為獨立 AI 模組，避免 UI/AI 雙源維護。
2. 已完成：`08-8A 廚房感應燈開/關` 合併為單一自動化，透過 `trigger id` 分流開關動作。
3. 抽離重複通知片段為 script（尤其 LINE 推播 payload/標題組合）。
4. 抽離共用條件模板（如在家/離家、緊急開關 gating）。
5. 針對 `100C1 + 100C2` 進行「單一門鎖電量框架」評估（分級通知 + 週期模型可同檔不同分支）。
6. 已完成：`800-開關系列` 的防連點 template 改為 `state_attr(...) | default(0)` 容錯寫法，降低 `last_triggered` 為空時模板錯誤風險。
7. 已完成：將重複的開關閃爍提示序列改為 `repeat`（2/4 次），減少 YAML 冗餘並簡化後續維護。

### Phase 3（高風險，行為優化）
1. 風扇三件組（21A/21B/22）做狀態機化（明確 state + cooldown + override）。
2. 保全鏈路（08-6/100B/106B）做事件流整理（trigger → 判斷 → 通知）。
3. 建立回歸測試清單（手動測試腳本 + 觸發矩陣）。

---

## 4) 下一步可直接執行的 TODO（建議）

- [ ] 先決定「FullAutomation20260215 只讀」是否正式定案。  
- [ ] 我可協助產出 `configuration/Automations/INDEX.md`（每個自動化：用途、觸發、依賴 helper、對外通知）。  
- [ ] 我可協助做「重複區塊盤點清單」（先只列，不改邏輯）。  
- [ ] 我可協助批次補 `id` 與統一版本字串。  
- [ ] 最後再進入功能優化（避免一開始就混改）。

---

## 5) 本基線結論

你目前的架構其實已經有良好方向：
- `FullAutomation20260215` 可當「歷史凍結基準」；
- `個別 *AI.yaml` 當「可維護主體」；
- `packages/helper.yaml` 當「共用能力層」。

接下來只要完成：**來源定版 + 命名/ID 正規化 + 通知邏輯抽象化**，就能進入安全的優化與冗餘清理節奏。

---

## 6) 已採納：UI + AI 雙軌載入模式

### 6.1 設定方式
- `automation: !include automations.yaml`（UI 維護路徑）。
- `automation ai_managed: !include_dir_merge_list Automations`（AI 模組化路徑）。

### 6.2 檔案歸屬
- `configuration/Automations/*.yaml`：
  - 每個檔案即為可直接載入的自動化定義（不再使用 include stub）。
  - 為目前實際載入來源（AI 管理主路徑）。
- `configuration/automations.yaml`：
  - 保留為 UI 可執行路徑（非 AI 管理自動化）。

### 6.3 管理約定（建議）
- 新增 AI 自動化時：
  1. 在 `configuration/Automations/` 建立（或更新）`XXX_AI.yaml`。
  2. 直接在 `configuration/Automations/` 內編輯或新增自動化檔。
  3. 確認同名 alias 已從 `configuration/automations.yaml` 移除，避免重複載入。
- 若需讓某自動化回到 UI 維護：
  - 自 `Automations` 移除 include，並把該自動化貼回 `automations.yaml`。

---

## 7) 怎麼「丟進 HA」：實際導入步驟（可直接照做）

以下流程假設你的 HA 設定根目錄是 `/config`。

### Step 1：放置檔案到 HA 設定目錄
- 將本 repo 的 `configuration/` 內容同步到 HA 的 `/config/`：
  - `configuration/configuration.yaml` → `/config/configuration.yaml`
  - `configuration/automations.yaml` → `/config/automations.yaml`
  - `configuration/Automations/*.yaml` → `/config/Automations/*.yaml`
- `configuration/Automations/*.yaml` 即為直接執行來源，不需額外 `Automation/` 轉接路徑。

### Step 2：先做語法檢查（強烈建議）
- 進入 HA：
  - **開發者工具 → YAML → 檢查設定**（Check Configuration）。
- 若有錯誤，先修正再重載/重啟，避免自動化整體載入失敗。

### Step 3：重載或重啟
- 你可以二選一：
  1. **開發者工具 → YAML → 重新載入 Automations**（優先，停機影響小）。
  2. 直接重啟 Home Assistant（若同時動到多個核心設定）。

### Step 4：確認載入是否生效
- 在 HA 的自動化頁面確認：
  - UI 自動化（`automations.yaml`）可正常執行。
  - AI 自動化（`configuration/Automations/*AI.yaml`）可正常執行。
- 避免 UI 與 AI 兩邊出現同名 alias。

### Step 5：後續維護規則（實務）
- **UI 維護來源** → `/config/automations.yaml`。
- **AI 維護來源** → `/config/Automations/*AI.yaml`。
- 每次搬移自動化前後，都建議執行一次「檢查設定 + 重新載入 Automations」。

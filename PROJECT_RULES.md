# Home Assistant GitOps & AI 開發升級標準作業程序 (PROJECT_RULES)

## 一、 連線與系統環境資訊（Connection & Environment Profile）

* **SSH 遠端連線**：`kenny1105@192.168.68.97:22` (`homeassistant.local`)
  * **認證方式**：ED25519 SSH 金鑰免密碼連線
  * **權限模式**：`sudo NOPASSWD: ALL`
* **HA 主機設定路徑**：`/config`（即 `/homeassistant`）
* **GitHub 遠端倉庫**：`https://github.com/kennychiang1105/HomeAssistant_Automation`
  * **存取 Token**：`[SECRET_GITHUB_PAT]` (Stored securely in local environment / git credentials)
  * **Git 使用者**：`kennychiang1105` (`kennychiang1105@users.noreply.github.com`)
* **本機歷史備份路徑**：`/Users/kenny/Library/Mobile Documents/com~apple~CloudDocs/Files/01_Documents/02家庭相關/03智慧家庭/AI Program`

---

## 二、 GitOps 標準開發與升級工作流程（GitOps Upgrade Workflow）

每次進行自動化開發、邏輯修改或版本升級時，AI 與開發者必須嚴格遵循以下 7 大步驟：

```mermaid
flowchart TD
    A["1. 確認目標版本號 (如 V3.6.8)"] --> B["2. SSH 連線 HA 主機並切換/建立 release 分支"]
    B --> C["3. 於 HA /config 直接進行修改 (遵循 18 項 SOP)"]
    C --> D["4. 執行 Pre-flight 語法檢驗 (Python YAML / HA CLI)"]
    D --> E["5. 自動重載生效 (Reload) 並提供測試指引"]
    E --> F["6. 🛑 使用者實體操作驗證確認 (User Sign-off)"]
    F -- 驗證成功 --> G["7. Git Commit & Push，自動建立 GitHub PR 並發布 Release"]
    G --> H["8. 更新推播系統儀表板實體同步 (保留差異供 00-2A 自動推播)"]
    F -- 發現異常 --> C
```

### 步驟 1：主動確認目標版本號
在進行任何程式碼修改或功能升級前，**若使用者尚未指定新版本號，AI 必須主動向使用者詢問預計開發的目標版本號**（例如 `V3.6.8`、`V3.7.0`）。

### 步驟 2：SSH 連線 HA 主機並建立 Git 分支
1. 透過 SSH 登入 HA 主機：
   ```bash
   ssh -p 22 kenny1105@192.168.68.97
   ```
2. 進入設定目錄並同步最新遠端主分支：
   ```bash
   cd /homeassistant
   sudo git fetch origin main
   sudo git checkout -b release/<目標版號>
   ```

### 步驟 3：直接於 HA 主機進行開發與修改
所有後續的：
* YAML 自動化修訂（`Automations/*AI.yaml`、`automations.yaml`）
* 腳本修訂（`Scripts/*AI.yaml`）
* Helper 套件變更（`packages/helper.yaml`）
* 主設定檔維護（`configuration.yaml`）
* 版本總表與開關指令對照表更新（`AI_VERSION_REGISTRY.md`、`SwitchCommand.md`）

皆**限定在 HA 主機 `/homeassistant` 的 release 分支中執行**，並嚴格遵循**第三章之 13 項核心 SOP 規範**。

### 步驟 4：即時語法檢驗與相容性檢查（Pre-flight Check）
在重載或重啟前，必須在 HA 主機上執行 YAML 語法檢驗：
```bash
python3 -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('Automations/*.yaml') + glob.glob('Scripts/*.yaml') + ['configuration.yaml', 'automations.yaml', 'packages/helper.yaml']]; print('ALL YAML SYNTAX OK')"
```

### 步驟 5：重載生效與提供驗證指引
語法檢驗 100% 通過後，重載 Home Assistant 設定使變更立即生效：
1. 重載自動化與腳本。
2. 檢查最新 50 行日誌確認無報錯或崩潰：
   ```bash
   tail -n 50 /homeassistant/home-assistant.log
   ```
3. **同步更新「自動化管理」面板**（SOP-14）：`python3 scripts/generate_automation_panel.py --deploy`。
4. **主動整理並提供「實體測試指引清單」**，明確列出受影響之實體開關手勢、情境觸發條件或 LINE 推播驗證點。

### 步驟 6：使用者實體操作驗證（User Physical Verification Gate）⚠️ 關鍵卡點
1. **必須由使用者親自在家庭實體環境中進行操作與驗證**（例如：實際按壓實體開關測試單擊/雙擊/長按、觸發情境確認燈光與設備作動、確認 LINE 推播內容符合 SOP 等）。
2. **AI 必須明確等待使用者回報「測試成功 / 驗證通過」**，嚴禁在使用者確認前擅自判定完成或提前 Commit/發佈。
3. **若使用者回報異常**：AI 需根據問題描述立即於主機進行微調修復，重新執行步驟 4 與步驟 5 再次交由使用者驗證；若有必要則執行第五章秒級回滾。

### 步驟 7：使用者確認後 Commit、Push 與自動建立 GitHub Release PR
獲得使用者明確確認驗證成功後，執行版本封裝：
1. **檢查變更狀態並 Commit**：
   ```bash
   sudo git add .
   sudo git commit -m "feat: Upgrade to <目標版號>"
   ```
2. **推送至 GitHub 遠端**：
   ```bash
   sudo git push -u origin release/<目標版號>
   ```
3. **透過 GitHub REST API 自動創建 PR 並發布 Release**：
   * 呼叫 GitHub API 建立 Pull Request。
   * PR 合併後依標準發布格式（包含 Known Bugs、Next Version 與系統日誌）發布 GitHub Release。

### 步驟 8：GitHub Release 發布後之儀表板實體同步（Post-Release Dashboard Sync）
在 GitHub Release 發布完成後，AI 必須立即透過 Home Assistant 服務調用同步「更新推播系統」儀表板手動版本實體（**注意：嚴禁主動按下「目前版本設為比對基準」**，以保留版本差異供每日 18:00 的 `00-2A更新紀錄推播AI` 自動偵測並推播通知）：

1. **更新手動版本 Helper 實體**（`input_text.set_value`）。**沿用歷史寫法**（見資料庫歷史）：
   * `input_text.automation_package_version_manual`：更新包版本，格式 `Vx.y.z`（例：`V3.6.9`、`V4.0`；修補版可加 `Patch (a)`，測試期 `V4.0-beta 8`）。
   * `input_text.automation_framework_version_manual`：架構版本，格式 `AIx.y`（例：`AI3.6`、`AI4.0`；測試期 `AI4.0 Beta 8`）。
   * `input_text.ai_manual_update_note`：**單行**簡明更新重點（≤255 字），開頭寫版本，重點以頓號分隔、結尾可帶一句總結，ASCII 與中文之間不加空格，例：`V4.0：通知分級與統一廣播(合成音檔快取)、氣氛燈情境、…，AI 4.0正式版`。不要用換行或模板。
   * **沒有 API 權杖時的寫入方式（一次性自動化）**：在 `/homeassistant/configuration/Automations/` 新增 `00-2Z發布後同步一次性.yaml`，觸發為 `homeassistant: start`、`delay 00:01:00` 後依序 `input_text.set_value` 上述三個實體；通過 `check_config` 後重啟 HA（先告知使用者），用資料庫確認三個值已更新，再**刪除該檔**（不納入 commit）。
   * 同步時一併處理：頂樓感應週報計數（`counter.topfloor_path_events`／`ghost_line`／`miss_line`／`fallback_off`／`study_max_off`）若累積了測試資料，在同一支一次性自動化內 `counter.reset`。
2. **比對基準設定規則（保留供 00-2A 自動寫入）**：
   * **嚴禁主動按下** `input_button.ai_version_snapshot_set_baseline`（目前版本設為比對基準）。
   * 每日 18:00 `00-2A更新紀錄推播AI` 觸發時，會自動偵測版本差異、發送 LINE 與 HA 系統更新推播，並在推播完成後**自動觸發事件將最新版本寫入快照基準**。
   * （僅在使用者明確要求「靜音/跳過本次更新通知」時，才依指令手動按下設為基準）。


---

## 三、 開發與修改 18 項核心標準作業程序（Core SOPs）

| SOP 編號 | 規範項目 | 核心要求與防呆機制 |
|---|---|---|
| **SOP-1** | LINE 文案原則 | 內容口語易懂，說明事件、系統動作與狀態；**禁止**暴露內部 entity/service 名稱。 |
| **SOP-2** | LINE 分級開關 | 必須經過分級開關判斷（一般 🪧 / 重要 ⚠️ / 緊急 🚨），不可跳過分級直發。 |
| **SOP-3** | Helper 相容性 | 修改前先確認 Helper 存在且型別相容；檔案頂部註記「相容版本：Helpers Vx.y（已確認）」。 |
| **SOP-4** | 版本三方同步 | 每次改動需**同步更新三處**：自動化檔案（`automation_version` / `alias`）、`packages/helper.yaml`、`AI_VERSION_REGISTRY.md`。 |
| **SOP-5** | 更新連結 | 版本與維運通知附上 GitHub Release 網址或可追溯版號。 |
| **SOP-6** | 避免重複通知 | 多段事件流需加去重/合併；除錯通知由 Debug Helper 控管，不額外新增 LINE 發送路徑。 |
| **SOP-7** | 更新紀錄推播 (00-2A) | 00-2A 透過動態快照差異比對僅推播變更項目；改版時需維護快照與對應 Registry。 |
| **SOP-8** | 頂部更新紀錄格式 | 每個 `*AI.yaml` 頂部需維持標準註解區塊（檔名、相容版本、更新紀錄列表）。 |
| **SOP-9** | 版號進位原則 | 功能新增/重構升次版本（`y+1`，如 `V3.3.1 -> V3.4.0`）；修復/微調升修補版（`z+1`，如 `V3.3 -> V3.3.1`）。 |
| **SOP-10** | LINE 發送可靠性 | **一律使用 `script.send_line_to_user`**；發送前必檢 `user_id` 有效性與開關狀態，失敗需 fallback 記錄；PR 需附最小驗證清單。 |
| **SOP-11** | TTS 廣播音量恢復 | 播音前讀取並保存音量（含 fallback）；播音後延遲 2 秒並以 `wait_template`（timeout 12s + `continue_on_timeout: true`）**確保一定恢復原始音量**。合成失敗時**重試最多 3 次，仍失敗只播提示音並發 HA 資訊級通知，不退回即時語音**（`merge_audio: false` 的呼叫除外）。 |
| **SOP-12** | 實體開關維護規範 | 查閱 `SwitchCommand.md` 防衝突；**三擊（Triple Press）全戶 100% 絕對專用於緊急模式（05E）**；單擊標配 500ms 長按防呆與 0.5s 消抖延遲；同步維護指令表。 |
| **SOP-13** | 主設定檔規範 | `configuration.yaml` 頂部標準化註解；檢查 HA 版本棄用整合；保護 include 結構；YAML 語法檢查與雙向同步。 |
| **SOP-14** | 自動化管理面板同步 | 側邊欄「自動化管理」面板（`/homeassistant/automation-panel.yaml`，由 `scripts/generate_automation_panel.py` 產生）。**新增／刪除／改名任何 automation、`input_*`（boolean／number／select／text／datetime／button）、`timer`、`counter` 後，必須重新產生並部署面板**：`python3 scripts/generate_automation_panel.py --deploy`（只改面板內容不需重啟 HA，瀏覽器重新整理即可）；新項目若被分到「其他」或分類不對，請調整腳本內 `AUTO_RULES`／`HELPER_RULES`。面板檔屬產生物，**禁止手改**。詳見下方〈面板更新流程〉。 |
| **SOP-15** | 通知內文排版與圖示 | LINE 卡片與 HA 通知的**內文**由 `custom_templates/notify_body.jinja`（本機副本 `www/custom_templates/`）統一產生，所有 LINE 路徑（`notify_dispatch`、舊格式純文字經 `send_line_to_user` 轉換、LINE Bot 額度通知）都用同一個範本。規則：①主要內容（標題）行單行、前面放依內容挑選的圖示（「…通知」用鈴鐺，預設公告），開頭的 `[離家]` 這類重複標籤與所有 emoji 一律移除；②下面的行與主要內容文字對齊，圖示只給「小標題（冒號結尾）」「名稱：數值」與警告行，一般句子不放圖示，小標題下的項目再縮排一層且圖示較小；③「名稱：數值」拆成灰色名稱＋粗體數值（沒有冒號但名稱以時間／溫度／狀態／車輛…結尾的舊式行也會自動辨識）；④句尾「請注意」後接橘色注意符號 ⚠︎（無圓圈）；⑤過長句子在「，」處逐子句斷行，避免孤字；⑥圖示顏色同一則以標題重要度為準（紅=緊急、橘=警告、綠=完成、藍=一般），只有警告／緊急行保留自己的顏色，另挑最多 3 個重點行（開始時間、用電量、狀態…）用對比色（綠／紫）。**圖示檔**：`www/icons/b2/<名稱>_<n|g|o|r|p>.png`（96px 圓形平面圖示，圖案置中，共 70+ 款，由 MDI 向量圖產生）；新增圖示請改 `pick` 巨集的關鍵字表並補齊五種顏色，上傳主機 `/homeassistant/www/icons/b2/` 後執行 `homeassistant.reload_custom_templates`（不需重啟）。標題色塊的白色圖示（`www/icons/*.png`）是另一套，不要混用。　**V4.2.0 新格式規定（所有 LINE 卡片一律適用，由 `flex_rows` 統一處理，不要各自手刻）**：①標題下方一條淺灰橫線，卡片內容上緣留白 20px；②每個小段落（以冒號結尾的小標題行或【段落】）上方一條淺灰橫線；③同一主題的多個重點自成小段落：「主題：」小標題＋每個重點一行（縮排），不要擠在同一行；④提醒／備註一律用 `※` 開頭：小字（xxs）、縮排對齊上一列的圖示、上方一條橫線延伸到右邊（連續的備註只在第一行上方加），不縮排的圖例說明用 `※※`；⑤顏色只標重點（紅／橙色燈號的地區、提醒裡的重點動作），其餘一般色，紫外線最多橘色；⑥新增通知時照上面寫文字（`名稱：數值`、`※ 提醒`、`行末⟦o⟧` 標色），由範本產生版面。 |
| **SOP-16** | 固定廣播句快取暖機 | 一律走 `script.announce`（合成音檔），**不要直接用 `tts.speak`**。分秒必爭的廣播（地震預警等）或需斷網也能播的固定句，要加進 `scripts/warm_announce.py` 的 `build_list()`（提示音檔名＋文字必須與 announce 實際傳入的完全相同，才會命中同一個快取檔），由 `00-2L廣播快取暖機AI` 開機後與每日 03:30 預先合成（即時合成約 1.7 秒、快取約 0.6 秒）。動態秒數／震度類廣播以「預估值 − 已經過時間 − 念到數字前的時間」挑句子。本機副本在 `scripts/`，主機在 `/homeassistant/scripts/`。 |
| **SOP-17** | 實際載入的檔案 | ⚠ **UI 自動化（舊的手動維護自動化）實際載入的是主機 `/homeassistant/automations.yaml`（根目錄）**，不是 `/homeassistant/configuration/automations.yaml`（那份是沒被載入的舊副本，兩者內容不同）。同理主要設定檔是 `/homeassistant/configuration.yaml`（根目錄），不是 `configuration/configuration.yaml`。AI 管理的檔案在 `/homeassistant/Automations/`、`Scripts/`（symlink 到 `configuration/`，這兩個是真的有載入）與 `/homeassistant/packages/`。修改前先 `grep` 確認：`automation: !include automations.yaml` 指向哪一份，改完用 HA 狀態確認別名（含版本）真的變了。 |
| **SOP-18** | Terncy 裝置 id | 自動化裡 Terncy 開關的 `device_id` **以事件（`terncy_pressed`／`terncy_long_press`）實際送出的為準**（舊 id，與 HA 裝置註冊表不同）。HA 啟動日誌的 `was split … can no longer fire` 警告不代表壞掉，**不要**依警告替換 id。改任何 device_id 前先查資料庫 `events` 的 `shared_data.device_id` 確認，改完要實際按開關驗證。 |
| **SOP-19** | 客廳／餐廳開燈動畫 | 客廳小燈、客廳燈組一／二／三／全、餐廳燈組開燈要走 `script.light_group_on`（動畫＋回到記憶的色溫亮度）。**入口一律用「（動畫）」template light**（`light.ke_ting_xiao_deng_dong_hua`、`…_deng_zu_yi/er/san_dong_hua`、`…_deng_zu_quan_dong_hua`、`light.can_ting_deng_zu_dong_hua`、`light.ke_ting_can_ting_quan_bu_dong_hua`），新增按鈕、情境、儀表板、Google／HomeKit 暴露時不要直接開原燈組 helper；動畫風格：氣氛（色調依太陽位置分黎明／白天／黃昏／夜晚）、依序、快速（魔方轉動）、滑動（魔方滑動），魔方轉動／滑動開燈改呼叫 `script.light_group_on`（style 快速／滑動）。**例外**：緊急模式（05A）與緊急模式快照還原必須瞬間全亮，維持呼叫原燈組。關燈永遠瞬間。燈況記憶看燈泡自己的 `light.mode`（2＝色溫）、`light.color_temperature`、`light.brightness`，不要用 HA 的 `color_mode`（對這些 Yeelink 燈會誤報 rgb）。 |
| **SOP-20** | 重啟接續（計畫重啟與意外重啟都要能接續功能） | Home Assistant 隨時可能重啟（更新、當機、斷電、人為），**所有有「等待狀態」的自動化／腳本，重啟後都必須能自己接續，不能假設不會重啟**。「等待狀態」包含 `delay`、`wait_for_trigger`、`wait_template`、`for:` 持續條件、`timer`、`mode: restart` 的倒數、`input_boolean` 旗標暫停中——這些在重啟時會消失或失去計時。規則：①新增或修改這類自動化時，必須加「HA 啟動」觸發（`platform: homeassistant, event: start`），啟動後（等實體載入約 1 分鐘）依**目前實際狀態**判斷要不要補做（燈還亮著就重新倒數關燈、風扇保留期還沒到就補回保留、暫停旗標已過期就解除），而不是依賴重啟前的記憶；②變數樣板碰到 `trigger.to_state`、`trigger.entity_id` 時要加 `trigger.to_state is defined` 保護，避免 HA 啟動觸發時樣板出錯；③`timer` 要靠 `restore: true` 或啟動時依 `input_datetime` 重算剩餘時間；④重啟前（計畫性）仍要確認沒有進行中的緊急模式、入侵倒數、情境逐環動作，並盡量挑沒人使用的時段，更新優先用 `automation.reload`、`script.reload`、`homeassistant.reload_custom_templates` 等重新載入（不要用 `template.reload`，會讓在家感測器抖動而誤觸離家／到家）；⑤驗收方式：用狀態確認，並實際想一次「倒數中途重啟會怎樣」。範例：104-1 在 HA 啟動 1 分鐘後，若車庫主燈或樓梯燈還亮著，重新進入關燈流程。2026-10-23 11:29 HA 重啟時剛好在車庫燈 5 分鐘關燈倒數，重啟後燈一直亮著，因此訂定。 |
| **SOP-21** | 廣播音效分類（開始音＋配對結束音） | 所有廣播走 `script.announce`，**依「類別 kind」決定開始音與配對的結束音**（不再只看等級）；結束音是同一組旋律反向下行、較短、較輕，由合成流程直接接在語音後面（`scripts/mk_announce.py` 第 3 參數，快取鍵含結束音）。**類別對照**（`announce` 的 `kinds` 表）：`quake` 地震預警（CWBEEW＋`cwb_end`）、`quake_report` 地震報告（兩組雙音嗶聲＋`quake_end`）、`evac` 疏散／海嘯／土石流／國家級警報（CWBEEW＋`cwb_end`）、`emergency` 緊急模式（銅管重擊）、`security` 保全（小調叮咚）、`weather` 天氣災害、`visitor` 訪客門鈴、`scene` 情境廣播、`notice_general`／`notice_important` 一般與重要生活通知（廣播前音樂風格）。**選類別**：呼叫 `script.announce` 時帶 `kind:`；沒帶就依等級（一般→notice_general、重要→notice_important、緊急→emergency）；經 `notify_dispatch` 的語音用 `voice_kind`；03 天氣災害與手動廣播用 `custom_templates/notify_body.jinja` 的 `broadcast_kind(msg, 預設類別)`（**只有「疏散／撤離」字樣＝evac**；颱風、豪雨、燈號、海嘯、土石流等一般災害廣播＝普通提示音，依等級）。**CWBEEW 只用在地震預警與疏散警告**。**不加音效的短句**（地震預警第一句倒數、車庫鐵門即將開啟／關閉）維持 `chime: false`，開始與結束音都不播。**總開關**：`input_boolean.announce_end_chime_off`（開＝不播結束音）。**產生與調整音效**：音效檔在 `/media/*_start.mp3`／`*_end.mp3`，由 `scripts/make_chimes.py` 的 SPECS 表格合成（音符、音色、迴響、目標響度都在表裡），要調整只改表格再在 HA 容器內重跑（`shell_command.make_chimes`），再依 `--json` 的長度更新 `announce` 的 `kinds` 表。**試聽**：面板「廣播音效」或 `script.announce_sound_demo`（只播頂樓 HomePod、音量 0.3，不觸發氣氛燈、不發通知）。新增廣播時：先決定類別，固定句要加進 `scripts/warm_announce.py` 的 `build_list()`（開始音、結束音、文字都要與實際呼叫相同，快取才會命中）。 |
| **SOP-22** | 日出日落判斷要考慮天氣 | 陰天、下雨時天色提早變暗、早上也更晚亮，所以**所有「依日出日落」的判斷都要依天氣前後調整**（早上「天亮」往後延、傍晚「天黑」往前提）。天氣調整層在 `packages/v42_weather_sun_adjust.yaml`：`sensor.weather_sun_shift_min`（目前套用的分鐘；陰 20／雨 40／大雨 60，可在面板調，`input_boolean.weather_sun_adjust_off` 整體關閉）與 `sensor.weather_dark_deg`（分鐘 × 0.25°，給用「太陽仰角」判斷的地方）；有防抖動（陰／雨持續 10 分鐘、大雨 5 分鐘才套用，結束後 20 分鐘才取消）。**新增任何依日出日落的判斷時，不要直接讀 `sun.sun`**：用早安到家時間窗（`binary_sensor.scene_morning_window`，起點加、終點減天氣分鐘）、或「仰角 < `sensor.weather_dark_deg`」代表天黑、或「仰角 − `sensor.weather_dark_deg`」當有效仰角。目前套用處：早安到家時間窗（`v41_scene_period.yaml`）、100A 自動情境最早啟動、燈組動畫氣氛色調、08-4 大門開光自動開燈。 |
| **SOP-23** | 熟睡不吵醒與災害通知去重 | ①**晚安情境（`input_boolean.aqara_wan_an`＝on）或頂樓熟睡中（`input_boolean.sleep_silent_active`＝on）時，非緊急（一般／重要）廣播所有喇叭都不播**：`script.announce` 整則略過；緊急等級照常；情境廣播（`kind: scene`，含晚安情境完成播報）不受影響；其他需要例外的呼叫帶 `force: true`（目前：手動廣播、車庫鐵門動作前的安全警語）。**新增廣播一律走 `script.announce`**，不要直接對喇叭 `play_media`／`tts.speak`。②**地震報告不是緊急**：01 地震災害系統只有規模 6 以上才用緊急等級，其餘用重要等級＋`quake_report` 音，且只在 07:00–22:00 廣播（LINE／HA 通知照發）；報告要和地震預警（eq99）是同一場（預警觸發時間 − 報告發生時間在 −5～＋5 分鐘）才當成「有預警的地震報告」，否則只發 HA 資訊通知。③**災害訊息以「單一項目」去重**（03）：訊息拆成燈號／降雨等級＋在地地區的項目（`disaster_sig` 每一段），`input_text.disaster_seen_items` 記住 `input_number.disaster_item_memory_hr`（預設 12）小時內已通知過的項目；項目全部通知過就不再發 LINE、HA 通知與廣播，出現新項目（升級、新增地區…）才發；僅重要類，緊急類不受影響。NCDR 會輪流發風力版／降雨版／合併版，不要再用「整段文字」或「嚴重度數字」判斷重複。 |
| **SOP-24** | 地震預警多來源去重、截圖與震央詳情 | ①**所有地震預警來源（地牛、TREM、氣象署 PWS…）一律呼叫 `script.eq99` 並帶 `source:`**；eq99 開頭用 `input_datetime.eew_last_event`／`input_text.eew_last_info` 判斷是不是同一場（合併時間 `input_number.eew_dedupe_window_sec`，預設 150 秒）：**最快到的先處理**，後到的只在紀錄寫「某來源比某來源慢幾秒」就略過；預估震度比先到的高 2 級以上（且達 3 級）才算升級、重新警報。新增來源只要呼叫 eq99，不要自己另做警報。②預警一收到，eq99 不阻塞啟動 `script.eew_detail_followup`：每 60 秒用 `scripts/cwa_quake.py` 查氣象署 E-A0015-001／E-A0016-001（最多 10 分鐘），找到發生時間相差 ±5 分鐘的那筆，補發震央、規模、深度、各縣市震度與報告圖；授權碼放 `secrets.yaml` 的 `cwa_api_key`（不進 git，沒有就只是不補發）。③**地牛 add-on**（`c370257c_oxwu`，竹南鎮 townID 1000504，警報門檻 2 級，VNC 埠 6901 不對外開放）的連動腳本是 `/config/oxwu/notify.sh`（設定 `/config/oxwu/settings.json`，兩者與 webhook ID 都不進 git）：警報時先呼叫區網 webhook（ID 在 secrets.yaml：`eew_oxwu_alert_hook`／`eew_oxwu_shot_hook`）→ `automation 地牛 add-on 預警接收AI` → 不阻塞啟動 `script.eq99`（`source: 地牛(HA)`），再等 3 秒用 `import` 截虛擬桌面存 `/config/www/snap/snap_eew_*.jpg`（`www/snap` 為 1777 讓 add-on 能寫）→ 呼叫 `script.eew_screenshot_ready`（eq99 3 分鐘內才附圖）；圖檔 3 天後由 `shell_command.clean_snaps` 清除。地牛傳給連動腳本的參數目前只確認有「預估震度、秒數」，其餘參數記在 `/config/oxwu/args.log`。截圖用 `import -crop 1008x684+0+42` 裁掉最上面的視窗標題列（關閉／縮小／設定按鈕）。⑤**TREM（ExpTech）即時預警**：`scripts/trem_eew.py` 常駐在 HA 容器，連公開的 `https://api.lb.exptech.dev/api/v2/eq/eew?sse=1`（不需金鑰；斷線退回輪詢），用 CWA 近場衰減式估竹南的預估震度與 S 波抵達秒數，≥2 級才透過同一個預警 webhook 呼叫 eq99（`source: TREM`，另帶震央地名、規模、深度，會附在截圖卡）；`automation TREM 預警客戶端看門狗AI` 每 5 分鐘看 `input_datetime.eew_trem_alive`（客戶端每分鐘心跳），沒心跳就用 `shell_command.trem_eew_start` 重啟，HA 啟動後 30 秒也會啟動（SOP-20）；紀錄在 `/config/trem_eew.log`。預估震度是近似值（沒有場址放大），與地牛不同時由 eq99 的去重／升級規則處理。**Windows 電腦的地牛連動與 add-on 並行時由 eq99 去重，確認穩定後再關掉電腦那邊。**⑤**測試守則**：不可用真實資料呼叫 `script.eq99`、預警 webhook 或 add-on 的 `notify.sh`（會真的廣播、開緊急模式、發 LINE）；一律用純模板驗證與靜態檢查，要端到端測試先問使用者並約時間。HA 模板條件必須回真正的布林（`1` 或非空字串會被當成假，要用 `> 0`、`| length > 0`、`| bool`）。⑥**按解除網關警報（106C）的順序**：先停緊急動作 → 還原 → 氣氛燈改回目前情境色 → 小音量廣播。④**LINE 額度保護**：預估震度低於 `input_number.eew_line_min_level`（預設 3）只發 HA 通知、不發 LINE；`input_boolean.eew_extra_enable` 關閉則截圖與詳情都不做。 |

### 〈面板更新流程〉（SOP-14 細則）
1. **何時更新**：新增／刪除／改名自動化、新增 helper（含新 package 的 helper）、新增分類時；每次發布版本（步驟 7）前再跑一次確認無遺漏。
2. **如何更新**：在專案資料夾執行 `python3 scripts/generate_automation_panel.py --deploy`。腳本會 SSH 唯讀查詢 HA 紀錄庫目前存在（非 `unavailable`）的實體，依規則分類後產生 YAML 並上傳；本機副本在 `www/automation-panel.yaml`。
3. **新實體要等 HA 已載入**：腳本讀的是「已載入的實體」，所以要先完成步驟 5（重載／重啟）讓新自動化與 helper 出現，再更新面板。
4. **分類規則**：自動化依名稱（`AUTO_RULES`）、helper 依 entity_id／名稱（`HELPER_RULES`）；只會自動歸類符合規則者，其餘進「其他」分頁。看到「其他」有東西就補規則。純狀態／旗標類（`_init`、`_last`、`_flag` 等，見 `FLAG_RE`）會放進「狀態與旗標」卡片。
5. **新增面板分頁**：在腳本的 `CATS` 加一筆（key、標題、icon、說明）並補對應規則。
6. **面板本身的設定**：`/homeassistant/configuration.yaml` 的 `lovelace → dashboards → lovelace-automation`（`mode: yaml`、`filename: automation-panel.yaml`、`show_in_sidebar: true`）。僅在第一次建立或改檔名時需要動它，並需重啟 HA。
7. **失效殘留**：面板「總覽」會顯示已失效（`unavailable`）舊自動化的數量；可到「設定 → 自動化」手動清理（目前沒有 API 權杖，無法由程式代刪）。
8. **驗證**：更新後開啟側邊欄「自動化管理」，確認新項目出現在正確分頁、開關可切換、參數可調整。
9. **版面（2026-10-08 起）**：所有分頁用 layout-card 的 `custom:vertical-layout`（最多 4 欄、每欄最小 340px）：卡片依「說明 → 自動化開關 → 功能小組（`SUBGROUPS` 順序）→ 其他元件種類」排列，程式依估計高度把卡片**按順序**切成最多 4 段放進各欄（`partition()`），欄數不夠時依序往下接——手機 1 欄、iPad 直放 2 欄時順序不變。超過 10 列的清單會拆成連續卡片（標題加「（續）」）。說明卡永遠與下一張卡片同欄。實體來源改讀 `core.restore_state`（最新一批），新增／刪除實體後最多 15 分鐘才會反映。

---

## 四、 機密安全防護與 `.gitignore` 規範（Security Guardrails）

為了確保智慧家庭私密憑證絕不外洩至 GitHub 公開/私有倉庫，`/homeassistant/.gitignore` 必須強制排除以下項目：

```gitignore
# ──────── 敏感憑證與私密金鑰 ────────
secrets.yaml
*.pem
*.key
google_assistant.json

# ──────── 系統動態狀態、資料庫與快取 ────────
home-assistant_v2.db*
*.log*
.storage/
.cloud/
.cache/
.ha_run.lock
.HA_VERSION
.shopping_list.json

# ──────── 多媒體、暫存與大檔 ────────
tts/
image/
dwains-dashboard/
onlineBackupsData/
node-red/
scrypted/
ssl/

# ──────── 系統檔案 ────────
.DS_Store
Thumbs.db
```

---

## 五、 秒級緊急回滾機制（Instant Rollback SOP）

若任何更新在上線後發生異常、邏輯錯誤或導致系統不穩定，可立即執行秒級回滾：

1. **還原所有未提交之修改**：
   ```bash
   cd /homeassistant
   sudo git checkout .
   sudo git clean -fd
   ```
2. **或切回上一版穩定 Commit / Tag**：
   ```bash
   sudo git checkout main
   ```
3. **重新載入 HA 自動化與腳本**，系統將於數秒內 100% 恢復至更動前的穩定狀態。

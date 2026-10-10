# 交接備忘錄：Terncy 無線開關全面啟用 + 08-5C 深夜亮度旗標修正（Claude Code → Antigravity）

> 建立時間：2026-10-09 16:00　分支：`release/V4.1`（尚未 commit，等使用者實體驗證，SOP-6）

## 1. Terncy 無線開關（使用者已在 Terncy app 操作 + Claude 啟用事件實體）
- 全部 13 片 Terncy 面板、37 顆按鈕的「無線開關」(`switch.*_wireless_switch_enabled`) 皆為 on。
  - **客廳環繞燈 / 客廳壁燈 / 客廳崁燈**（面板 `dc8e95fffe8b12e9`）是使用者刻意保留繼電器：單擊 = 原本開關，雙擊 = 無線事件。不要把它們的繼電器關掉。
- 啟用無線模式的按鈕，原本的繼電器 `switch.*` 會變 unavailable（正常，例：三樓開關上2、四樓開關下1～3）。
- 所有 Terncy 按鈕與書房感應開關的 `event.*_single_press` / `_double_press` / `_long_press` 已啟用（75 個由 `disabled_by: integration` 改為啟用）。
  - 做法：停 HA 容器 → 改 `.storage/core.entity_registry` → 啟動。備份：主機 `/tmp/bk_stage/pre_terncy_events/core.entity_registry`。
  - `event.*_button` 仍停用（用不到）。
  - 重啟後確認：38 個 single / 38 double / 38 long 事件實體皆已載入。
- **完整對照表**（哪幾顆是同一片面板、位置、switch 與事件實體 id）：`Terncy開關對照表.md`（本機專案資料夾與主機 `/homeassistant/TERNCY_開關對照表.md` 各一份）。
- 同一片面板 = 同一個 MAC（`unique_id` = `<MAC>-01/02/03`）。HA 把每顆按鈕登錄成獨立 device，沒有「面板」層級；按鈕名稱與房間不一定一致（例：`dc8e95fffe8d69a0` 三鍵分屬車庫 / 餐廳）。
- 日誌的「device ... was split」警告是誤導，**不要**換成新 device_id（事件仍帶舊 id），見記憶 Terncy device ids。
- 雙擊 / 長按要接什麼動作尚未決定，等使用者指示。

## 2. 08-5C 頂樓樓梯燈深夜亮度旗標修正（已部署、已測、未 commit）
- 問題：熟睡鎖解除時樓梯燈若是關著，`ai_08_5c_stairs_leave_night_level` 仍把 `input_boolean.topfloor_stairs_night_used` 清掉，燈泡便卡在深夜亮度（60%/3000K），之後感應開燈不會調回正常亮度。
- 修正：檔案 `Automations/08-5C頂樓樓梯感應燈AI.yaml`，最後清旗標的條件改為「兩盞樓梯燈都 on」才清；燈關著就保留旗標，下次感應或開燈再套用平常亮度。備份：主機 `/tmp/bk_stage/pre_nightflag_fix/`。
- 測試（2026-10-09 11:25）：燈關著時觸發 → 旗標保留；兩盞先後亮起 → 套用 70%/3787K、80%/4000K，旗標清除。通過。
- 待使用者實體驗證（下次熟睡鎖解除後的感應開燈）；通過後再 commit，並納入 V4.1。

## 3. 其他注意
- HA MCP 只有 Assist 控制 / 讀取工具，無法改實體登錄檔；改登錄檔只能停容器後手改（務必先備份）。
- GitHub MCP（`plugin:github:github`）目前連線失敗：`Authorization header is badly formatted`，使用者說先不處理。

## 4. 2026-10-10 11:05 追加：審查後修正（Claude Code，已部署、未 commit）
備份：主機 `/tmp/bk_stage/pre_review_fixes/`。詳細審查見 `Antigravity變更審查與熟睡鎖流程_2026-10-10.md`。
- **08-5G**：`regex_replace` 反斜線改回 `\\1`（`\1` 會被 Jinja 當八進位，頂樓人數恆為 0）。V4.1.1。
- **800-12E / 12F**：state 觸發加「事件 5 秒內、非 unavailable/unknown」條件（原本 HA 重啟／關閉時兩者同時誤觸發，12F 會清熟睡鎖）。
- **08-5H（V4.2.1）**：動態解鎖改為夜燈時間超過 14 小時（或沒按夜燈、08-5H 凌晨強制開鎖、手動切鎖）時，以「鎖被打開的時間」計算，只等到早上基準 09:30／10:30。離線 14 個情境測試通過。
- **22頂樓電風扇**：HomePod 溫濕度改用 regex 取數字（感測器自 10-09 19:23 起回傳 `26.4°C`；來源是外部寫入，根因未查）。
- **spatial_context**：補 `services.yaml`（TLS 驗證關閉的補丁沒動，仍是對所有 rtsps:// 生效）。
- **configuration/automations.yaml** 已與根目錄同步（含 05A、09B 的修改）。注意：根目錄檔案仍是 untracked，commit 前要確認。
- **Terncy 無線開關**：17 顆仍接燈具的按鈕（五樓壁燈、陽台燈、書房燈、二三樓／三樓／三四樓樓梯燈、一樓樓梯燈、廁所燈、餐廳崁燈／壁燈、車庫主燈、廚房燈、客廳環繞燈／壁燈／崁燈、路燈、門口燈）已全部把 `wireless_switch_enabled` 關閉，單擊直接帶動繼電器；雙擊／長按／三擊事件仍會送進 HA（以廁所燈實測）。其餘按鈕（繼電器停用的情境按鈕）維持無線。
- **08-9 單擊切換**：只在按鈕為無線模式時動作，目前這 17 顆都不是，所以不會觸發；保留備用。
- **05E 三擊**：以舊／新 device_id 對照後，17 顆都已有三擊緊急觸發。
- 尚未處理：A6（`input_select.floorplan_active_floor` 殘留於 `new-ui.yaml` 等來源檔，非 live 儀表板）；3D 樓層圖 JS 未審；HomePod 感測器為何開始帶單位。

## 5. 2026-10-10 11:25 追加（Claude Code）
- **08-5F V4.0.3**：熟睡判定統一只看熟睡鎖，移除時間窗與 7 處自行關鎖（解鎖只由 08-5H 鎖管理處理）。
- **重要：08-5C 於 10:01 被覆寫，我之前的「夜間亮度旗標」修正消失**（`ai_08_5c_stairs_leave_night_level` 最後清旗標的條件又變回「燈關著也清」）。已於 11:24 重新套用（兩盞都亮才清旗標）。**請 Antigravity 改 08-5C 前先讀現有檔案再改，不要用舊版整檔覆蓋。**
- HA 現在可用 REST（`$HA_MCP_TOKEN`）重載：`POST /api/services/automation/reload`，改 YAML 後不必重啟 HA。
- `08-9B廁所燈雙擊開車庫樓梯燈AI.yaml`（測試用）已不在主機上，不確定是誰移除；如需要請告知。
- 待決定：書房燈「亮了馬上關」（08-5G 書房回房間關燈，7 天資料顯示 10-07 起幾乎所有 60 秒內的關燈都是它造成）。

## 6. 2026-10-10 12:05 追加（Claude Code，已用 REST 重載，沒有重啟 HA；未 commit）
- **08-5G V4.1.2「書房回房間關燈」**：加兩道防呆——書房燈剛亮 10 秒內不處理；`topfloor_last_path` 為 enter_study 且 10 秒內不處理。（7 天紀錄：10-07 起 60 秒內書房燈亮了又關幾乎都是此規則造成。）
- **動線仲裁（頂樓動線事件發布腳本 V4.1.0，`Scripts/頂樓感應AI.yaml`）**：所有 08-5J 動線都經過此腳本，仲裁放在這裡，08-5J 本身沒改邏輯。
  1. 剛進書房（enter_study）10 秒內不可能離開：`leave_study_bedroom`／`leave_study_down` 略過。
  2. 與前一個動線方向矛盾且相隔不到 4 秒（書房內 enter_study ↔ 書房外 leave_*／enter_bedroom／down_start）：看 PIR 先後（右＝書房側、左＝房間側，10 秒內較晚觸發者）；方向一致才放行；看不出方向則依先前紀錄保留。
  3. 被略過的動線寫 logbook「動線仲裁：略過 …（原因）」，可用來檢視誤判。
  離線重播 11 個情境（含 10-09 23:45 的矛盾連發）全數通過。
- **感應器方向標示更正**：右＝書房側、左＝房間側（使用者 2026-10-06 確認）。已改 08-5G／08-5J 觸發名稱與 `memory/spatial_context.md` 的描述（原本寫成右＝走廊、左＝書房）。
- **自動化面板**：產生器以專案資料夾 `scripts/generate_automation_panel.py` 為準（主機舊版已同步）；106C 歸「保全與門鎖」、`terncy_btn_last` 歸「開關按鈕」，「其他」分頁已清空。流程見記憶 ha-automation-panel-sop。
- 請 Antigravity：改 08-5C／08-5G／08-5H／08-5F／發布腳本前先讀現有檔案，不要整檔覆蓋；改完用 `automation/reload`、`script/reload` 即可，不用重啟。

## 7. 2026-10-10 12:35 追加（Claude Code）
- **HomePod 溫度**：`sensor.5f_homepodmini_temperature` 由外部 iPhone 捷徑經 REST 寫入，10-09 19:23 起狀態變成 `26.9°C` 文字且沒有單位屬性，歷史圖畫不出來。使用者已修好捷徑，12:31 實測改為 `state='26.9'`、`unit='°C'`、device_class temperature，恢復正常。濕度一直正常。
- 備援：新增 `sensor.ding_lou_homepod_temperature_numeric`（`packages/homepod_sensors.yaml`，用範本取出數字並補單位）；寫入端正常後可保留或移除。22 風扇已改為容錯解析，兩種格式都能讀。
- 10-09 19:23～10-10 12:31 之間的舊實體歷史是文字，不會變回折線。
- 2026-10-10 13:30 更新：備援感測器 `sensor.ding_lou_homepod_temperature_numeric` 已移除（`packages/homepod_sensors.yaml` 備份在主機 `/tmp/bk_stage/homepod_numeric/`）；登錄檔留有 unavailable 空殼，可在 UI 刪除。客廳 HomePod 捷徑原本把 device_class／state_class 填反，13:22 起已改正（頂樓、客廳三個溫濕度感測器格式一致）。

## 8. 2026-10-10 13:55 追加（Claude Code，已重載；未 commit）
- **106C V4.1.1**：新增一般廣播（只廣播客廳 HomePod＋車庫攝影機喇叭，不發 LINE／HA 通知，用 `script.turn_on` 不等待播完）；虛擬按鈕一開始就復位。
- **樓梯燈單擊定時 3 分鐘關燈**（`Automations/800-14樓梯燈單擊定時關燈AI.yaml`，4 支，頂樓與車庫樓梯燈不做）：
  - 二三樓樓梯燈：三樓開關下3 單擊（relay_own，已實測 13:35→13:38 準時關）、客廳主開關下1 雙擊（開燈並重新計時）。
  - 三樓樓梯燈：三樓開關下1（relay_own）、三樓開關上3（遙控鍵，HA 切換）。
  - 三四樓樓梯燈：三樓開關上1（relay_own）、四樓開關下3（遙控鍵，HA 切換）。
  - 四樓樓梯燈（yeelink 0fb7）：四樓開關下1 單擊（燈泡仍由 12D 切換，這裡依事件當下狀態判斷開或關）。
  - **原本功能優先**：時間到時若 9A 常開（`topfloor_stairs_keep_on`）或 9B「全開一段時間」（`automation.automation_41`，current>0）正在執行就不關。9A／9B／9C 的按鈕（三樓開關下2、三樓開關上2、四樓開關下2、客廳主開關下1）與 12D 原功能都沒動。
  - 提醒：9A／9B／9C 與 05E 仍使用已不存在的舊 device_id（事件仍帶舊 id，沿用即可，見記憶 Terncy device ids）。

## 9. 2026-10-10 14:20 追加（Claude Code，已重載；未 commit）
- **雙擊常開**（`Automations/800-14樓梯燈單擊定時關燈AI.yaml` V4.1.2）：單擊定時 3 分鐘的每顆按鈕（三樓開關下3／下1／上3／上1、四樓開關下3／下1）雙擊＝開燈、取消倒數、不自動關；再單擊就關燈。
  - 三盞繼電器燈直接開著即可。
  - **四樓樓梯燈（燈泡 0fb7）**：燈泡被頂樓感應（08-5K）在 5 分鐘手動保持後接管，所以雙擊時額外打開 9A 的常開旗標 `topfloor_stairs_keep_on`，並用新 helper `input_boolean.stairs_si_lou_hold`（`packages/stairs_hold.yaml`）記錄「是這支自動化打開的」；四樓樓梯燈一關就只清除自己打開的旗標，不影響 9A 原本的常開。
  - 客廳主開關下1 的雙擊仍是「二三樓樓梯燈開燈＋重新計時」（不是常開）。
  - 9C 長按全關仍會關掉所有樓梯燈（原本功能優先）。

## 10. 2026-10-10 14:05 追加（Claude Code，已重載；未 commit）
- **廁所感應燈重新偵測**（`Automations/08-8B廁所感應燈AI.yaml` 新增 `ai_08_8b_toilet_motion_retrigger`，V3.1.0）：手動關燈後馬上再進廁所不會亮的原因——小米人體感應器（xiaomi_gateway3，`binary_sensor.e406bf25caa1_motion`）有人活動時約每 20 秒回報一次，但狀態一直是 on、只更新 `last_triggered` 屬性；無人約 90 秒才回報 off。原自動化只看「狀態變 on」所以忽略。新增依 `last_triggered` 變化觸發：感應器 on、廁所燈關超過 10 秒、手動關閉模式未啟用 → 開燈。
- 原 08-8B 沒改。要縮短「離開後多久關燈」（現在約 90 秒＋1 分鐘＝2.5 分鐘）可把原自動化 `motion_off` 的 `for: 00:01:00` 調小，使用者尚未要求。

## 11. 2026-10-10 14:20 追加（Claude Code，已重載；未 commit）
- **廁所燈 08-8B V3.1.1**：無人關燈的等待由 1 分鐘縮短為 10 秒（感應器自己約 90 秒才回報無人；離開後約 100 秒關燈，原本約 150 秒）。
- **廚房燈 08-8A V3.3.0**：新增 `ai_08_8a_kitchen_motion_retrigger`。同廁所：小米人體感應器（`binary_sensor.kitchen_motion`）有人活動時約每 20 秒更新 `last_triggered` 但狀態一直是 on，手動關燈後再進去不會亮；新增依 `last_triggered` 或毫米波存在感應器（`unknown_zhan_kong`）off→on 觸發，燈關超過 10 秒才開；長按關閉廚房感應燈自動化（10B 的手動模式）時不動作。廚房關燈仍靠毫米波 off 後 1 分鐘（毫米波會閃爍，緩衝有用，未縮短）。
- 2026-10-10 14:25 更新：廚房重新偵測**只用小米人體感應器**（`kitchen_motion` 的 `last_triggered`），不用毫米波開燈（毫米波容易誤判、偵測範圍太遠）；毫米波仍只用在原自動化的「無人關燈」判斷。

## 12. 2026-10-10 14:45 追加（Claude Code，已生效；未 commit）
- **車庫燈手動關閉冷卻 30→120 秒**：`packages/helper.yaml` 的 `garage_light_cooldown_sec` initial 改為 120（原本寫死 30，重啟會被還原），並已用 `set_value` 套用。104-1 的車庫攝影機動態觸發維持不變（室內車庫，使用者確認不必擔心車燈／光影誤判）。
- 104-4 回家通知：觸發本來就包含 `opening`／`open`；遙控器開門時 iSmartgate（gogogate2）只會回報 `open`（`opening` 只出現在 HA 自己發出的開門指令，會帶 parent_id、不通知），所以已是門離開關閉位置後的最早訊號。

## 13. 2026-10-10 15:10 追加（Claude Code，已生效；未 commit）
- **車庫 104-1 V4.1.1**：手動關燈冷卻 120 秒。`800-開關系列-10餐廳廁所開關1-車庫燈連動`（雙擊切換兩盞車庫燈，自動化發出）切換前先寫手動標記 `input_text.terncy_btn_last`（值 `switch.che_ku_zhu_deng,switch.lou_ti_deng|時間`），104-1 的 `is_manual_action` 改為認「逗號分隔的多個實體」，所以這個雙擊關燈也會啟動冷卻。離家／晚安等情境關燈**不**啟動冷卻（避免你關燈後開鐵門時擋掉自動亮燈）。
- 鐵門開超過 45 分鐘：門關上時 `gate_closed` 會重新啟動 5 分鐘倒數，最後沒人就關燈，不用改。
- 清掉已刪除自動化留下的 unavailable 實體：`108che_ku_tie_men_gan_ying_deng`（104-1A）、`104_1c_..._autooff`、`tie_men_wei_guan_ti_xing`、已移除的 08-9B 測試自動化，以及備援感測器 `ding_lou_homepod_temperature_numeric`。做法：本機 Python `websockets` 連 `ws://192.168.68.97:8125/api/websocket`，用 `HA_MCP_TOKEN` 呼叫 `config/entity_registry/remove`（只刪 state=unavailable 且 restored、設定檔無引用者）。其餘約 54 個 unavailable 的舊自動化實體未動。

## 14. 2026-10-10 16:50 追加（Claude Code，已生效；未 commit）
- **車庫主燈按鈕防小燈**（`Automations/800-15車庫主燈按鈕防小燈AI.yaml`）：車庫主燈剛關不到 5 秒再通電，燈具會切到小燈模式。為了在實體按鈕上也擋住，「車庫主燈」按鈕的無線開關改為 **on**（`switch.che_ku_zhu_deng_wireless_switch_enabled`，使用者已確認）：單擊只送事件，由這支自動化切換——亮著→關燈；關著→開燈，離上次關燈不到 5 秒就等補滿 5.1 秒再開（5 秒內連續點擊＝延長打開）。切換前寫 `terncy_btn_last` 標記讓 104-1 當成手動關燈（冷卻）。取捨：這顆按鈕多一點延遲、且 HA 當機時牆壁開關暫時沒反應；要還原就把無線開關關掉並停用 800-15。
- **800-10 雙擊切換車庫燈**也加了同樣的「主燈剛關不到 5 秒就先等補滿」。
- **氣氛燈 00-2J V4.0.1**：新增觸發——按情境（早安／到家／離家／晚安）時，即使網關模式沒變也重新套用顏色（原本只在 Aqara 模式改變時同步，已在家模式再按早安不會換色，手動改過的多功能網關 1 LED 無法一鍵還原）。已把網關 1 還原為綠色（0,200,80、35%）。

## 15. 2026-10-10 17:45 追加（Claude A，V4.1 批次 1：項目 8 耗材通知修復，已生效；未 commit）
- **V4.1 規劃與分批排程**：`V4.1_八項功能規劃.md`、`V4.1_任務分工.md`（所有批次必讀；含檔案歸屬、介面、規則、流量控制、批次時間表）。
- **00-2C耗材更換AI通知 V4.1.0**：濾網只通知一次；電池階段式提醒（35／20／10）；無效讀數用 7 天內最後有效值，否則排除（廁所夜燈已排除）；單一裝置對照表；`packages/v41_supply.yaml` 新增 3 個輔助項目。舊 `supply_batt_lowest_*` 停用。06 濾網空殼已刪。
- 請 B／C：不要再改 `00-2C`、`v41_supply.yaml`；濾網與電池的通知只在這支，C 的空氣清淨機自動化**不要**再發濾網通知。

## 16. V4.1 批次 2：日出日落時間窗與日型判斷（2026-10-10）
- 見 `V4.1_任務分工.md` 的批次 2 紀錄。重點：Workday 類別改為只用 government（workday 類別是紀念日清單，不可用）；補班日用 `input_text.tw_makeup_workdays`；新時間窗 `binary_sensor.scene_morning_window`（今日 05:22–16:34），尚未被任何既有自動化使用。

## 17. V4.1 批次 3：空氣清淨機整合 AI（影子）＋環境異常通知 AI（2026-10-10）
- 見 `V4.1_任務分工.md` 批次 3 紀錄。`air_ai_shadow` 預設 on（只記錄）；`env_alert_co_dry_run` 預設 on（CO 緊急乾跑）。舊 07 系列未動。06 的一般／重要通知已實際啟用。

## 18. V4.1 批次 4：person 化與失效實體（2026-10-10）
- 見 `V4.1_任務分工.md` 批次 4 紀錄。`helper.yaml` 的 at_home 範本改優先讀 person（狀態逐一比對一致）；新增 `v41_person.yaml`、`00-3`、`00-4`；頂樓三檔未改（等「切換」）；失效實體 71 個清單在 `V4.1_失效實體清理預覽.md`，等「清理」。

## 19. V4.1 批次 5：時間窗接線＋100A AI 版（2026-10-10）
- 見 `V4.1_任務分工.md` 批次 5 紀錄。`scene_window_use_sun` 預設 off（行為不變）；已接線 00-2J、105、800-0、800-0B、800-13（根目錄 automations.yaml 已同步副本）；新 100A AI 版為影子模式，舊 100A 未動。

## 20. V4.1 批次 6：熟睡起床搭配國定假日（2026-10-10）
- 見 `V4.1_任務分工.md` 批次 6 紀錄。08-5H V4.3.0，`sleep_holiday_aware` 預設 off（行為不變）；離線 34 情境全過；補班週六要先填 `tw_makeup_workdays`。

## 21. V4.1 批次 7：緊急模式快照還原（2026-10-10）
- 見 `V4.1_任務分工.md` 批次 7 紀錄。05A 最前面多一個 `script.emergency_snapshot_save`（continue_on_error）；`emergency_restore_route` 預設 off；單元測試用測試實體通過；端對端 HomeKit 測試待使用者在場。

## 22. V4.1 批次 8：106C、面板、總結（2026-10-10）
- 106C V4.2.0（還原路徑預設 off）；面板重新產生（其他＝0）；總結見 `V4.1_完成報告.md`（八項狀態、功能開關預設、待驗證、清理清單、回復方式）。**V4.1 全部 8 批已完成（2026-10-10 當天由同一 session 連續執行，取代原先的排程任務）。未 commit。**

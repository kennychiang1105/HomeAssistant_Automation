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
- Helper 套件版本（`packages/helper.yaml`）：`V4.1.0`（V4.1.5 新增 `packages/v41_emergency_pause.yaml`、`v41_day_label.yaml`、`v41_living_fan.yaml`、`v41_garage_away.yaml`、`v41_disaster_notify.yaml`、`v41_summer_auto.yaml`）
- configuration 主設定檔版本（`configuration.yaml`）：`V4.0`
- 實體分類總表（`ENTITY_REGISTRY.md`）：`V1.0`

<!-- STATS:BEGIN -->
## 數量統計（`scripts/registry_stats.py` 產生，更新於 2026-10-22）

| 項目 | 檔案數 | 數量 |
|---|---|---|
| AI 自動化（`Automations/*.yaml`，一項一個 id） | 61 | **90** |
| AI 腳本（`Scripts/*.yaml`，一支一個 key） | 14 | **31** |

<!-- STATS:END -->

## 現況總表（Automations）

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Automations/00-01系統回應穩定自動化AI.yaml` | `00-01系統回應穩定自動化AI (V4.0.0) / 00-01系統回應穩定自動化AI_小燕網關看門狗 (V4.0.0) / 00-01系統回應穩定自動化AI_UnifiProtect看門狗 (V4.2.2)` | `ai_00_01_system_stability_auto_restart` / `ai_00_01_xiaoyan_gateway_watchdog` / `ai_00_01_unifi_protect_watchdog` | `V4.2.2` |
| `configuration/Automations/00-2A更新紀錄推播AI.yaml` | `00-2A更新紀錄推播AI (V4.0.0)` | `ai_00_2a_release_note_push` | `V4.0.0` |
| `configuration/Automations/00-2BLINE推播AI.yaml` | `00-2BLINE推播AI (V4.0.0)` | `ai_line_bot_quota_guard` | `V4.0.0` |
| `configuration/Automations/00-2C耗材更換AI通知.yaml` | `00-2C耗材更換AI通知 (V4.1.6)` | `ai_00_2c_supply_battery_notify` | `V4.1.6` |
| `configuration/Automations/00-2D通知開關初始化AI.yaml` | `00-2D通知開關初始化AI (V4.0.0)（共 6 支）` | `ai_00_2d_notify_ha_switch_init` / `ai_00_2d_mood_alert_switch_init` / `ai_00_2d_scene_announce_init` / `ai_00_2d_announce_volume_init` / `ai_00_2d_announce_volume_unify` / `ai_00_2d_announce_volume_test` | `V4.0.0` |
| `configuration/Automations/00-2E通知測試AI.yaml` | `00-2E通知測試AI (V4.0.0)` | `ai_00_2e_notify_test` | `V4.0.0` |
| `configuration/Automations/00-2H燈況記憶AI.yaml` | `00-2H燈況記憶AI (V4.1.6)` | `ai_00_2h_light_memory` | `V4.1.6` |
| `configuration/Automations/00-2I快照清理AI.yaml` | `00-2I快照清理AI (V4.0.0)` | `ai_00_2i_snapshot_cleanup` | `V4.0.0` |
| `configuration/Automations/00-2J氣氛燈情境同步AI.yaml` | `00-2J氣氛燈情境同步AI (V4.2.2)` | `ai_00_2j_ambient_scene_sync` | `V4.2.2` |
| `configuration/Automations/00-2K頂樓參數初始化AI.yaml` | `00-2K頂樓參數初始化AI (V4.0.0)` | `ai_00_2k_topfloor_param_init` | `V4.0.0` |
| `configuration/Automations/00-2L廣播快取暖機AI.yaml` | `00-2L廣播快取暖機AI (V4.0.0)` | `ai_00_2l_announce_cache_warm` | `V4.0.0` |
| `configuration/Automations/00-2M實體引用檢查AI.yaml` | `00-2M實體引用檢查AI (V4.1.6)` | `ai_00_2m_entity_reference_check` | `V4.1.6` |
| `configuration/Automations/00-2P門鎖電量每日紀錄AI.yaml` | `00-2P門鎖電量每日紀錄AI (V4.0.0)` | `ai_00_2p_doorlock_battery_daily` | `V4.0.0` |
| `configuration/Automations/00-2S家人主要裝置切換AI.yaml` | `00-2S家人主要裝置切換AI (V4.2.0)` | `ai_00_2s_person_main_device` | `V4.2.0` |
| `configuration/Automations/00-3失效實體巡檢AI.yaml` | `00-3失效實體巡檢AI (V4.1.0)` | `ai_00_3_stale_entity_audit_v41` | `V4.1.0` |
| `configuration/Automations/00-4手機追蹤比對AI.yaml` | `00-4手機追蹤比對AI (V4.1.0)` | `ai_00_4_phone_tracker_compare_v41` | `V4.1.0` |
| `configuration/Automations/03苗栗天氣告知系統AI.yaml` | `03苗栗天氣告知系統AI (V4.2.0)` | `ai_miaoli_weather_disaster_notify` | `V4.2.0` |
| `configuration/Automations/05B緊急模式通知AI.yaml` | `05B緊急模式通知AI (V4.2.2)` | `ai_05b_emergency_mode_notify_v3` | `V4.2.2` |
| `configuration/Automations/05C按鈕自動復位AI.yaml` | `05C按鈕自動復位AI (V3.0)` | `ai_05c_emergency_button_auto_reset_v3` | `V3.0` |
| `configuration/Automations/05D緊急模式虛擬按鈕AI.yaml` | `05D緊急模式虛擬按鈕AI (V3.0)` | `ai_05d_emergency_virtual_button_bridge_v3` | `V3.0` |
| `configuration/Automations/05F緊急模式快照到期AI.yaml` | `05F緊急模式快照到期AI (V4.1.0)` | `ai_05f_emergency_snapshot_expire_v41` | `V4.1.0` |
| `configuration/Automations/05G緊急三擊維修暫停AI.yaml` | `05G緊急三擊維修暫停AI (V4.1.5)` | `ai_05g_emergency_triple_press_pause` | `V4.1.5` |
| `configuration/Automations/06環境異常通知AI.yaml` | `06環境異常通知AI (V4.1.6)` | `ai_06_env_alert_v41` | `V4.1.6` |
| `configuration/Automations/07空氣清淨機整合AI.yaml` | `07空氣清淨機整合AI (V4.2.0)` | `ai_07_air_purifier_v41` | `V4.2.0` |
| `configuration/Automations/08-5A五樓保全系統AI.yaml` | `08-5A 五樓保全系統AI Webhook精準防禦 (V4.2.2)` | `ai_08_5a_5f_security_webhook_guard` | `V4.2.2` |
| `configuration/Automations/08-5C頂樓樓梯感應燈AI.yaml` | `08-5C頂樓樓梯感應燈AI (V4.0.0) / 08-5C頂樓樓梯感應燈自動關閉AI (V4.0.0) / 08-5C頂樓樓梯燈解除深夜亮度AI (V4.1.5)` | `ai_08_5c_topfloor_stairs_motion_light` / `ai_08_5c_topfloor_stairs_motion_light_auto_off` / `ai_08_5c_stairs_leave_night_level` | `V4.0.0` / `V4.1.5` |
| `configuration/Automations/08-5F頂樓自動上下樓情境AI.yaml` | `08-5F頂樓自動上下樓情境AI (V4.0.4) / 08-5F頂樓下樓補判AI (V4.0.1)` | `ai_topfloor_stairs_scene` / `ai_topfloor_down_assist_v4` | `V4.0.4` / `V4.0.1` |
| `configuration/Automations/08-5G書房燈感應AI.yaml` | `08-5G 書房燈感應AI (V4.1.3) / 08-5G 書房燈關閉AI (V4.1.3) / 08-5G 書房燈無人檢查AI (V4.1.3) / 08-5G 書房回房間關燈AI (V4.1.3)` | `ai_08_5g_study_motion_light` / `ai_08_5g_study_light_off_v4` / `ai_08_5g_study_vacancy_check` / `ai_08_5g_study_to_room_off` | `V4.1.3` |
| `configuration/Automations/08-5H頂樓深夜熟睡情境AI.yaml` | `08-5H頂樓深夜熟睡情境AI (V4.3.0) / 08-5H頂樓深夜熟睡鎖管理AI (V4.2.1)` | `ai_08_5h_topfloor_deep_sleep_scene_guard` / `ai_08_5h_topfloor_sleep_lock_manager` | `V4.3.0` / `V4.2.1` |
| `configuration/Automations/08-5J頂樓動線推理AI.yaml` | `08-5J頂樓動線推理AI (V4.2.2) / 08-5J頂樓感應週報 (V4.1.1)` | `ai_08_5j_topfloor_path_inference` / `ai_08_5j_topfloor_weekly_report` | `V4.2.2` |
| `configuration/Automations/08-5K頂樓燈具使用權AI.yaml` | `08-5K頂樓燈具使用權AI (V4.0.0) / 08-5K頂樓樓梯燈手動保持結束AI (V4.0.0) / 08-5K頂樓感應暫停到期AI (V4.0.0) / 08-5K頂樓開機狀態自癒檢查AI (V4.2.2)` | `ai_08_5k_topfloor_light_ownership` / `ai_08_5k_topfloor_manual_hold_end` / `ai_08_5k_topfloor_pause_end` / `ai_08_5k_topfloor_reconcile_on_start` | `V4.2.2` |
| `configuration/Automations/08-6離家保全系統AI.yaml` | `08-6離家保全系統AI (V4.0.0)` | `ai_away_security_system` | `V4.0.0` |
| `configuration/Automations/08-7離家入侵偵測AI.yaml` | `08-7離家入侵偵測AI (V4.2.2) / 08-7D入侵偵測感應器統計AI (V4.2.2)` | `ai_08_7_intrusion_watch` / `ai_08_7d_intrusion_stats` | `V4.2.2` |
| `configuration/Automations/08-7A自動晚安情境AI.yaml` | `08-7A自動晚安情境AI (V4.2.2)` | `ai_08_7a_auto_goodnight_scene` | `V4.2.2` |
| `configuration/Automations/08-8A廚房感應燈AI.yaml` | `08-8A 廚房感應燈AI (V3.2) / 08-8A 廚房感應燈重新偵測AI (V3.3.0) / 08-8A 廚房燈無人保險關燈AI (V3.4.0)` | `ai_08_8a_kitchen_motion_light` / `ai_08_8a_kitchen_motion_retrigger` / `ai_08_8a_kitchen_idle_off` | `V3.2` / `V3.3.0` / `V3.4.0` |
| `configuration/Automations/08-8B廁所感應燈AI.yaml` | `08-8B廁所感應燈AI (V3.0.3) / 08-8B廁所感應燈重新偵測AI (V3.1.0) / 08-8B 廁所燈無人保險關燈AI (V3.2.0)` | `ai_08_8b_toilet_motion_light` / `ai_08_8b_toilet_motion_retrigger` / `ai_08_8b_toilet_idle_off` | `V3.0.3` / `V3.1.0` / `V3.2.0` |
| `configuration/Automations/08-9Terncy無線開關單擊切換AI.yaml` | `08-9Terncy無線開關單擊切換AI (V4.1.1)` | `ai_08_9_terncy_wireless_single_toggle` | `V4.1.1` |
| `configuration/Automations/09C電視待機喚醒AI.yaml` | `09C電視待機喚醒AI (V4.2.2) / 09C電視紅外線開關自動復位AI (V4.2.2)` | `ai_09c_tv_keepalive` / `ai_09c_tv_ir_reset` | `V4.2.2` |
| `configuration/Automations/100A自動啟動到家早安情境AI.yaml` | `100A自動啟動到家早安情境AI (V4.2.0)` | `ai_100a_auto_arrive_morning_v41` | `V4.2.0` |
| `configuration/Automations/100B自動離家AI.yaml` | `100B自動離家AI (V4.2.2)` | `ai_auto_leave_system` | `V4.2.2` |
| `configuration/Automations/100C1客廳門鎖電量分級通知AI.yaml` | `100C1客廳門鎖電量分級通知AI (V4.0.0)` | `ai_doorlock_battery_stage_notify` | `V4.0.0` |
| `configuration/Automations/100C2客廳門鎖電量分級通知AI.yaml` | `100C2客廳門鎖電量分級通知AI (V4.0.0)` | `ai_doorlock_battery_cycle_calibration` | `V4.0.0` |
| `configuration/Automations/100C3客廳門鎖電量下降時間紀錄AI.yaml` | `100C3客廳門鎖電量下降時間紀錄AI (V3.0)` | `ai_doorlock_battery_drop_timestamp_recorder` | `V3.0` |
| `configuration/Automations/100C_GoogleHome情境虛擬按鈕橋接AI.yaml` | `100C GoogleHome情境虛擬按鈕橋接AI (V4.2.2)` | `ai_100c_googlehome_scene_virtual_button_bridge` | `V4.2.2` |
| `configuration/Automations/104-1車庫鐵門感應燈AI.yaml` | `104-1車庫鐵門感應燈AI (V4.2.0) / 104-1B車庫燈手動關閉冷卻AI (V4.2.0) / 104-1C全員離家關閉車庫燈AI (V4.2.0)` | `ai_104_1_garage_gate_motion_light` / `ai_104_1b_garage_manual_off_cooldown` / `ai_104_1c_garage_all_away_off` | `V4.2.0` |
| `configuration/Automations/104-2車牌辨識AI.yaml` | `104-2車牌辨識AI (V4.0.0)` | `ai_lpr_recognition` | `V4.0.0` |
| `configuration/Automations/104-3鐵門判斷未關提醒及作動AI.yaml` | `104-3鐵門判斷未關提醒及作動AI (V4.2.2)` | `ai_104_3_garage_gate_open_guard_and_autoclose` | `V4.2.2` |
| `configuration/Automations/104-4車庫回家通知系統AI.yaml` | `104-4車庫回家通知系統AI (V4.1.5)` | `ai_104_4_garage_arrival_notice` | `V4.1.5` |
| `configuration/Automations/105大門門鈴自動化AI.yaml` | `105大門門鈴自動化AI (V4.0.0)` | `ai_105_front_door_doorbell_notify` | `V4.0.0` |
| `configuration/Automations/106C_解除網關警報整合AI.yaml` | `106C_解除網關警報整合AI (V4.2.1)` | `ai_106c_gateway_alarm_disarm_integration` | `V4.2.1` |
| `configuration/Automations/106網關系統AI.yaml` | `106網關系統AI (V4.1.5)` | `ai_gateway_anomaly_guard` | `V4.1.5` |
| `configuration/Automations/106D網關切換同步Aqara開關AI.yaml` | `106D網關切換同步Aqara開關AI (V4.2.2)` | `ai_106d_gateway_to_aqara_switch` | `V4.2.2` |
| `configuration/Automations/107Tesla充電器狀態與通知AI.yaml` | `107Tesla充電器狀態與通知AI (V4.1.6)` | `ai_107_tesla_charger_status_notify` | `V4.1.6` |
| `configuration/Automations/21A_客廳電風扇整合控制AI.yaml` | `21A_客廳電風扇整合控制AI (V4.2.2)` | `ai_living_room_fan_integrated_control` | `V4.2.2` |
| `configuration/Automations/21B_客廳電風扇異常告警AI.yaml` | `21B_客廳電風扇異常告警AI (V4.0.0)` | `ai_living_room_fan_anomaly_alert` | `V4.0.0` |
| `configuration/Automations/22頂樓電風扇自動化AI.yaml` | `22頂樓電風扇自動化AI (V4.1.5)` | `ai_topfloor_fan_automation` | `V4.1.5` |
| `configuration/Automations/800-14樓梯燈單擊定時關燈AI.yaml` | `800-開關系列-14 二三樓樓梯燈（三樓開關下3單擊／客廳主開關下1雙擊）-定時3分鐘關燈、雙擊常開AI (V4.2.2) / 800-開關系列-14B 三樓樓梯燈（三樓開關下1／三樓開關上3單擊）-定時3分鐘關燈、雙擊常開AI (V4.2.2) / 800-開關系列-14C 三四樓樓梯燈（三樓開關上1／四樓開關下3單擊）-定時3分鐘關燈、雙擊常開AI (V4.2.2) / 800-開關系列-14D 四樓樓梯燈（四樓開關下1單擊）-定時3分鐘關燈、雙擊常開AI (V4.2.2)` | `ai_800_13_san_lou_xia_3_timed_off` / `ai_800_14b_san_lou_stairs_timed_off` / `ai_800_14c_san_si_lou_stairs_timed_off` / `ai_800_14d_si_lou_stairs_timed_off` | `V4.2.2` |
| `configuration/Automations/800-15車庫主燈按鈕防小燈AI.yaml` | `800-開關系列-15 車庫主燈按鈕-單擊切換（5 秒防小燈）AI (V4.1.1)` | `ai_800_15_garage_main_button_small_light_guard` | `V4.1.1` |

## 維護約定
- 調整邏輯時：
  1. 先更新檔內 `variables.automation_version`。
  2. 再同步本總表。
  3. 若有跨檔引用，優先保持 `id` 不變；若必須改 `id`，要全域搜尋後一併更新。

## Helper 變更紀錄

| 版本 | 日期 | 變更描述 |
|---|---|---|
| V4.2.2 | 2026-10-23 | 新增 `packages/v41_garage_away.yaml`：`input_datetime.garage_gate_opened_at`（SOP-20 重啟接續，車庫鐵門開啟時間記錄）。 |
| V4.2.2 | 2026-10-22 | 新增 `packages/v41_person_main_device.yaml`：`input_select.person_main_device_kenny／iris／jerry／elay`、`input_text.person_main_device_custom_*`、`input_boolean.person_main_device_busy`（內部）、`sensor.person_*_source_device`。 |
| V4.2.2 | 2026-10-22 | 升級 `packages/v41_outdoor_brief.yaml`：`sensor.leave_outdoor_brief` 整合近 36 小時在地災害告警（颱風、海嘯、豪雨、強風、淹水等）及白話安全提醒，清理失效的 `/browser_mod.js` 引用。 |
| V4.2.0 | 2026-10-18 | 移除影子模式 helper：`air_ai_shadow`（空氣清淨機）、`auto_scene_shadow`（到家早安）、`intrusion_watch_shadow`（入侵偵測）；新增 `packages/v41_light_anim.yaml`（燈組動畫 helper 與 7 個動畫燈）、`v41_outdoor_air.yaml`、`v41_outdoor_brief.yaml`、`v41_kitchen_air.yaml`。 |
| V4.1.5 | 2026-10-11 | 廚房「空氣品質危險」旗標條件：PM2.5>35 或 CO2>1500 或 TVOC>600 ppb（原 CO2>1000）。 |
| V4.1.5 | 2026-10-11 | 新增 `packages/v41_day_label.yaml`：`sensor.tw_day_label`（今日日型標籤，供 3D 儀表板日期列使用）。 |
| V4.1.5 | 2026-10-11 | 新增 `packages/v41_emergency_pause.yaml`：`input_boolean.emergency_triple_press_pause`（緊急三擊維修暫停，已加入 HomeKit 與自動化管理面板）、`timer.emergency_triple_press_pause`（2 小時自動恢復）。 |
| V4.1.0 | 2026-10-10 | V4.1 發布：at_home 範本優先讀 `person.*`；新增 packages：`manual_broadcast.yaml`、`stairs_hold.yaml`、`terncy_buttons.yaml`、`v41_supply.yaml`、`v41_scene_period.yaml`、`v41_day_type.yaml`、`v41_person.yaml`、`v41_emergency.yaml`、`v41_air_purifier.yaml`、`v41_env_alert.yaml`、`v41_auto_scene.yaml`、`v41_sleep_holiday.yaml`；`garage_light_cooldown_sec` 預設 120 秒。 |
| V4.0.0 | 2026-10-08 | V4.0 發布：新增通知分級／氣氛燈／廣播／頂樓動線／LINE Bot 輪替／車庫回家／門鎖日耗電率等 helper；新增 packages：`topfloor.yaml`、`persons.yaml`、`doorlock_battery.yaml`、`announce_tts.yaml`（詳見 helper.yaml 檔頭與本檔「本次調整（V4.0）」）。 |
| V4.0-beta 1 | 2026-10-04 | UI 重新設計：3D 平面圖 `picture-elements` + 單燈疊圖（`mix-blend-mode: lighten`，亮度/色相/飽和度同步），新增 iPad 橫向與 iPhone 直向首頁；由 `scripts/generate_floorplan_v4.py` 依 `spatial_scene_graph.json` 與 `render_manifest.yaml` 產生各樓層卡片（`floorplan_v4/`）。底圖暫用舊 3D SVG，待實際渲染圖。另新增 `entity_positions.yaml/json` 與 `ENTITY_POSITIONS.md` 位置實體表（含 5F 使用者校正後座標），供後續自動化使用。 |
| V3.24.0 | 2026-09-23 | 修復車庫/二樓 Wi-Fi 綜合判斷（加 30s delay_off、納入 Kenny iPad），強化 AP MAC 模板過濾與更新 Iris 預設追蹤器。 |
| V3.23.0 | 2026-09-20 | 新增 `input_boolean.line_bot_quota_exhausted_notified`（LINE Bot 額度用盡通知去重狀態開關），確保所有 Bot 配額用盡時僅推播一次告警。 |
| V3.22.0 | 2026-08-16 | 新增 `input_button.ding_lou_si_lou_lou_ti_deng_xiao_zheng`（頂樓四樓樓梯燈校正虛擬按鈕），將實體開關按鍵校正功能改由虛擬實體按鈕接管。 |
| V3.21.1 | 2026-08-09 | 修復 `supply_batt_lowest_23cd3dc` 的 friendly_name 為「耗材電量最低値_廚房無線開關」。 |
| V3.21.0 | 2026-08-09 | 新增 `input_number.garage_light_cooldown_sec`（車庫燈手動關閉冷卻秒數，預設 30 秒，可調 0～600 秒）。 |
| V3.19.0 | 2026-08-02 | 新增小米無線開關 HomeKit 門鈴橋接（`binary_sensor.da_men_men_ling`，`device_class: doorbell`），觸發後 3 秒復位。 |
| V3.18.0 | - | 新增 HomeKit 晚安/早安/離家/到家情境輔助開關與按鈕自動復位。 |

## Configuration 主設定檔變更紀錄

| 版本 | 日期 | 變更描述 |
|---|---|---|
| V4.0 | 2026-10-11 | logger 降級事件觸發器「舊 device_id 已拆分」警告；recorder 排除 `ai_version_registry_dynamic`、`ai_version_snapshot_history`（屬性超過 16 KB）。需重啟 HA 生效。 |
| V3.6 | 2026-10-08 | recorder 保留 45 天並排除高頻雜訊實體（`button.*_info`、網路使用率、耗電電流電壓）；新增自動化管理面板與整合儀表板 `lovelace-smart`；packages 新增與 `person` 設定。 |
| V3.5 | 2026-08-16 | 依據 Home Assistant 2026.8 規範移除已棄用之 `http:` 區塊（由 HA 系統網路介面管理）；新增 logger 過濾規則屏蔽 Hisense TV 待機連線日誌與 HACS 自訂整合過渡期棄用警告。 |
| V3.0 | 2026-03-01 | 基礎架構重組，導入 AI managed automations & scripts include，設定 recorder、logger 與 Google Translate TTS。 |


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
4. 清理、同步、預備判斷、取消原因等除錯型 `persistent_notification`，應優先由該系統 Debug Helper 控管；只有實際自動執行的開門、關門、告警、維安動作才預設保留永久通知。
5. Debug Helper 只控制原本不送 LINE 的除錯/清理訊息是否建立永久通知；不可因 Debug 開啟而新增 LINE 發送路徑。


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
1. 修改 `persistent_notification` 或 Debug 通知時，需確認是否新增 LINE 路徑；若該訊息原本不送 LINE，Debug 開啟後也不得送 LINE。
2. **LINE 一律使用 `script.send_line_to_user`**（避免直接呼叫 `notify.line_*` 造成 DNS/整合暫時失效時中斷流程）。
3. 發送前必做三項檢查：
   - 目標 `user_id` 不可為 `unknown/unavailable/none/空字串`。
   - 對應分級開關（一般/重要/緊急）必須為 `on`。
   - 若有子系統額外開關（如 Tesla/耗材額外 LINE 開關）也必須為 `on`。
4. payload 格式統一為 JSON message array（多則訊息），至少包含：
   - 第 1 則：版本標題（例：`【系統名稱AI (Vx.y.z)】` + 等級行）。
   - 第 2 則：事件主訊息（發生什麼事 + 關鍵時間/狀態）。
   - 需要時第 3 則：補充資訊（溫度、電量、附註）。
5. 任何一項檢查不通過時：
   - 不可硬送 LINE。
   - 必須留下 `persistent_notification` 或 logbook 記錄「未發送原因」（例：user_id 無效 / 開關關閉）。
6. 新增或修改通知時，PR 必須附「最小驗證清單」：
   - 一般/重要/緊急各至少 1 條 payload 範例。
   - 開關關閉時不發送的驗證結果。
   - `user_id` 無效時 fallback 記錄結果。

### SOP-11：廣播系統音量恢復規範（每次涉及 TTS 廣播必做）
1. 觸發 TTS 廣播前，**必須先讀取並儲存**各廣播媒體播放器（HomePod 等）的當前音量至 action-level 變數。
   - 使用 `state_attr('media_player.entity_id', 'volume_level') | float(fallback)` 讀取。
   - 若讀取失敗（unknown/unavailable）則使用安全預設値（建議 0.5），避免恢復時静音。
2. 調整音量後呼叫 `tts.speak`，播音完成後必須恢復原始音量。
3. 等待播音完成的標準流程：
   - `tts.speak` 呼叫後延遲 2 秒，讓播放啟動（delay: "00:00:02"）。
   - 使用 `wait_template` 監聽播放器狀態離開 `playing`，timeout 建議設 12 秒。
   - **必須設 `continue_on_timeout: true`**，確保即使播放超時也一定恢復音量。
4. 無論是否 timeout，音量恢復動作必須執行（`wait_template` + `continue_on_timeout` 模式保證此點）。
5. 所有涉及 TTS 廣播的自動化均適用，包括门鈴、保全警報、地震、自定義廣播等。

### SOP-12：開關類自動化更新與維護規範（每次涉及實體開關必做）
1. **衝突檢測先行**：在新增或修改任何實體開關（小燕/小米）自動化手勢前，必須查閱 `SwitchCommand.md`，確認該開關在該手勢（單擊/雙擊/三擊/長按）下未被其他自動化占用。
2. **三擊手勢絕對專用**：全戶三擊（`click_times: 3` / `state: triple`）一律為最高優先權之「緊急模式（05E）」專用，禁止指派區域自訂功能。任何新開關加入時必須主動加入 `05E緊急實體按鈕`（`1744040282451`）。
3. **單擊防呆與消抖標配**：單擊（`click_times: 1`）自動化必須加入 500ms 長按防呆模板與動作序列末端 `- delay: '00:00:00.5'`，模式統一為 `mode: single, max_exceeded: silent`。
4. **雙表同步維護**：每次開關自動化變更完成後，必須同步更新 `SwitchCommand.md`（指令分類對照表）與 `AI_VERSION_REGISTRY.md`。

### SOP-13：Configuration 主設定檔更新與相容性規範（每次修改 configuration.yaml 必做）
1. **頂部更新紀錄格式規範（比照 helper.yaml）**：
   - `configuration.yaml` 檔案最上方必須採用標準分隔線與結構化更新紀錄區塊：
     ```yaml
     # ──────────────────────────────────────────────
     # AI Configuration（Vx.y）
     # ──────────────────────────────────────────────
     # 更新紀錄（統一格式）：
     # - Vx.y（YYYY-MM-DD）：
     #   • 變更摘要項目...
     # ──────────────────────────────────────────────
     ```
   - 每次修改必須由新到舊在頂部逐筆記錄版本、日期與變更細項。
2. **版本號進位原則**：架構重組、官方整合遷移（如 2026.8 移除 http:）升級次版本（`y + 1`，例 `V3.0 -> V3.5`）；細部日誌過濾或參數微調升級修補版（`z + 1`，例 `V3.5 -> V3.5.1`）。
3. **HA 重大升級相容性檢測**：每次 Home Assistant 核心升級時，主動檢視是否有被棄用（Deprecated）的根層級整合（如 HA 2026.8 棄用之 `http:` 區塊），並即時依官方規範遷移至 UI 或相應整合。
4. **Include 結構完整性保護**：嚴格保護所有 include 結構（`packages`、`automation`、`automation ai_managed`、`script`、`script ai_managed`、`recorder`、`logger` 等），禁止任意破壞或漏失引用目錄。
5. **版本雙向同步**：每次修改 `configuration.yaml` 頂部版本後，必須同步更新 `AI_VERSION_REGISTRY.md` 之「依賴版本」與「Configuration 主設定檔變更紀錄」。
6. **語法與重啟驗證**：修改後必須使用 Python YAML 載入器檢驗語法，並於 HA 開發者工具執行「檢查設定」確認無誤後重啟主機生效。

## 現況總表（Scripts）

| File | Alias | id | automation_version |
|---|---|---|---|
| `configuration/Scripts/地震預警系統遠端AI.yaml` | `地震預警系統(遠端)AI (V4.0.0)` | `eq99` | `V4.0.0` |
| `configuration/Scripts/情境檢查AI.yaml` | `情境檢查AI (V4.1.6) / 情境執行廣播AI (V4.1.6) / 離家樓梯燈延遲關閉 (V4.1.6)` | `scene_verify` / `scene_announce` / `stairs_delayed_off` | `V4.1.6` |
| `configuration/Scripts/手動廣播AI.yaml` | `手動廣播AI (V4.1.0)` | `announce_manual` | `V4.1.0` |
| `configuration/Scripts/手動通知AI.yaml` | `手動通知AI (V4.1.0)` | `notify_manual` | `V4.1.0` |
| `configuration/Scripts/氣氛燈AI.yaml` | `氣氛燈單區閃爍 (V4.0.0) / 氣氛燈關閉燈具顏色還原 (V4.0.0) / 氣氛燈機台整段變色 (V4.0.0) / 氣氛燈機台熄滅閃爍 (V4.0.0) / 情境氣氛燈AI-機台情境色 (V4.0.0) / 情境與狀況氣氛燈AI (V4.1.5)` | `mood_alert_pulse` / `mood_alert_restore_off` / `mood_alert_ap_hold` / `mood_alert_ap_blink` / `ambient_scene` / `mood_alert` | `V4.0.0` / `V4.1.5` |
| `configuration/Scripts/漸進情境AI.yaml` | `漸進情境AI (V4.1.6)` | `stage_scene` | `V4.1.6` |
| `configuration/Scripts/統一通知AI.yaml` | `統一通知AI (V4.0.0) / 統一廣播AI (V4.0.0) / 廣播音量保險 (V4.0.0)` | `notify_dispatch` / `announce` / `announce_volume_guard` | `V4.0.0` |
| `configuration/Scripts/緊急模式快照還原AI.yaml` | `緊急模式快照 (V4.1.0) / 緊急模式還原 (V4.1.0)` | `emergency_snapshot_save` / `emergency_restore` | `V4.1.0` |
| `configuration/Scripts/車庫即時影像AI.yaml` | `車庫即時影像AI (V4.0.0)` | `garage_live` | `V4.0.0` |
| `configuration/Scripts/車庫快照AI.yaml` | `車庫快照AI (V4.0.0) / 車庫快照（條件式）AI (V4.0.0)` | `garage_snapshot` / `garage_snapshot_if` | `V4.0.0` |
| `configuration/Scripts/車庫錄影AI.yaml` | `車庫錄影AI (V4.0.0) / 車庫短片LINE發送AI (V4.0.0)` | `garage_video` / `garage_video_line` | `V4.0.0` |
| `configuration/Scripts/頂樓感應AI.yaml` | `頂樓動線事件發布 (V4.1.0) / 頂樓樓梯燈感應關燈（單盞） (V4.0.0) / 頂樓坎燈感應關燈 (V4.0.0) / 頂樓樓梯燈套用平常亮度 (V4.0.0) / 頂樓樓梯燈實體按鈕切換 (V4.0.0)` | `topfloor_publish_path` / `topfloor_stairs_off_one` / `topfloor_kandeng_off_if_auto` / `topfloor_stairs_apply_day` / `topfloor_stairs_button_toggle` | `V4.1.0` / `V4.0.0` |

## 本次調整（V4.2.2 - 2026-10-22：家人主要裝置選擇與卡片、LINE 通知新格式（橫線／備註／示意條）、3D-UI 全域警報彈窗、離家災害提醒整合在地白話指引、災防告警縮短標色排版、離家通知重複修正）

- **SOP-20 重啟接續審核後修正（fix12）**：
  · **104-3 鐵門提醒**：原本「車庫人車活動安靜滿 3 分鐘才提醒」寫在最上層，被改放進巢狀 `if/then` 的 `condition`——巢狀區塊裡 condition 不成立只會結束該區塊、不會中止整個自動化（已在 HA 實測），結果有人車活動也照樣提醒與自動關門。現在改成 `if（不安靜）＋stop`。重啟接手的固定 `delay` 改成 `wait_for_trigger`（鐵門關上就中斷）。
  · **104-3A 鐵門開啟時間記錄（新）**：原本寫在 104-3 內（沒有狀態過濾，屬性變化與 `unavailable` 都會寫入，且 single 模式會在等待期間丟掉開關門事件），拆成獨立 queued 自動化，只在 `open`／`closed` 且來源不是 `unavailable`／`unknown` 時寫入 `input_datetime.garage_gate_opened_at`。
  · **08-4 客廳大門開燈**：重啟接手改用 `if＋stop`（原本燈沒亮也會往下走、約 6 分鐘後把路燈與門口燈關掉），並恢復「日落後」條件、緊急模式中不接手。
  · **08-5G 書房燈關閉**：移除重啟接手（「書房燈無人檢查」每分鐘已涵蓋，原寫法可能在人還在書房時關燈），檔案還原為 V4.1.5。
  · **800-1B 晚安／離家**：移除重啟接手（頂樓孤兒燈已由 08-5K 開機自癒處理，原寫法可能關掉有人在用的樓梯燈）。
  · **08-7 入侵偵測接手**：警報通知帶入實際感應器名稱（原為固定文字）；重複警報由 `入侵警報AI` 既有的 30 分鐘冷卻擋住。
  · **09C 紅外線復位**：延遲改回 3 秒（先前無故改成 5 秒）。另清除多餘的行尾空白。
- **燈號與降雨同在一則訊息（颱風公報）時，本地降雨警戒被忽略**：原本只要有燈號組，卡片、簽章、語音都只處理燈號。2026-10-23 薔琵颱風公報同時有橙色燈號與「新竹縣山區、苗栗縣山區局部豪雨或大豪雨」，降雨部分沒顯示。現在燈號卡片後面接「降雨警戒」本地組（LINE 與 HA 通知）、去重簽章同時包含燈號與降雨組、語音廣播也念本地降雨；只有燈號或只有降雨的訊息輸出與原本完全相同（回歸測試卡片大小一致）。`disaster_digest` 也保留本地降雨組（超過 255 字時先丟降雨再丟其他）。（`notify_body.jinja`：`disaster_sig`、`disaster_voice`、`special_body`、`special_md`、`disaster_digest`）
- **颱風訊息進不來（`sensor.disaster_raw` 狀態超過 255 字元）**：HA 狀態上限 255 字元，REST 感測器內文超過就被改成 `unknown`，每 1～2 分鐘報一次 ERROR，`sensor.disaster` 停在上一則。2026-10-23 的颱風公報長達 1380 字（颱風位置＋降雨＋紅橙黃燈號＋海浪），整則颱風警報因此沒進系統。新增 `disaster_digest` 巨集：超過 255 字時濃縮成只含竹南／苗栗／新竹的燈號組或降雨組（格式與原文相同，簽章與廣播詞與原文一致），255 字內原樣回傳；`earthquake_raw` 也加 255 字保護。（`notify_body.jinja`、`packages/earthquake_disaster.yaml`，REST 平台感測器需重啟 HA 才會生效）
- **SOP-20 重啟接續（批次 3：for: 持續時間與範本觸發類自動化重啟接續）**：
  · **100B 自動離家AI**：新增 `ha_start` 觸發，HA 重啟後 delay 4 分 10 秒重新檢查「全員不在家＋離家情境未開（或剛開過未滿 3 分鐘）」，成立才接續執行離家情境；保留離家已開超過 3 分鐘跳過防重複機制。
  · **08-7A 自動晚安情境AI**：新增 `ha_start` 觸發，重啟 90 秒後重新檢查二樓無人與就寢安全區條件，符合則自動執行晚安情境；二樓有人或晚安已開則安全終止。
  · **09C 電視待機喚醒AI**：新增 `ha_start` 觸發，重啟 2 分鐘後重新檢查電視是否仍斷線，若仍斷線才送紅外線喚醒情境，已連線則自動略過；紅外線復位開關加 ha_start 5 秒自動關閉防呆。
  · **21A 客廳電風扇整合控制AI**：新增 `ha_start` 接手，重啟 15 秒後重新評估環境溫濕度與 Kenny 位置，動態切換兒童鎖與風速調節；全域加入 `trigger.to_state is defined` 保護。
  · **08-5J 頂樓動線推理AI**：保護 `src` 變數（手動執行與 `ha_start` 時防止 `trigger.event` 存取異常），重啟後並行推理自動歸零無殘留旗標。

- **SOP-20 重啟接續（批次 2：安全相關自動化重啟接續與計時保存）**：
  · **08-7 離家入侵偵測AI**：新增 `ha_start` 重啟接手，重啟 1 分鐘後若仍為離家模式、無人在家且近期有 2 個以上感應訊號，重新從 45 秒寬限開始起算並重新評估；保護 `trigger.id` 避免模板未定義錯誤。
  · **05B 緊急模式通知AI**：新增 `ha_start` 重啟接手，重啟 1 分鐘後若緊急模式仍開啟，僅發送一則 HA info 級系統通知，不發 LINE 避免重複洗版與消耗額度。
  · **104-3 鐵門判斷未關提醒及作動AI**：新增 `input_datetime.garage_gate_opened_at`（在開門時記錄時間戳，關門時清除）；重啟 1 分鐘後依此時間戳精確計算已開門時間，接續剩餘秒數倒數後進行 10 分鐘提醒與 2 分鐘觀察關門。
  · **08-5A 五樓保全系統AI**：新增 `ha_start` 重啟接手，重啟 30 秒後若解除開關為開啟則自動復位為關閉，避免解除開關卡住。
  · **00-01 UnifiProtect 看門狗**：新增 `ha_start` 觸發，重啟後重新啟動 1 小時看門狗觀察計時；保護 `trigger.entity_id` 避免未定義錯誤。
  · **100C GoogleHome 情境虛擬按鈕橋接AI**：新增 `ha_start` 接手，重啟 15 秒後重置 4 個虛擬按鈕旗標為關閉，避免按鈕卡在開啟狀態導致語音觸發失效。
  · **長計時器重啟保存（restore: true）**：為 `packages/v41_emergency.yaml` 的 `emergency_snapshot_expire`（2 小時）與 `packages/helper.yaml` 的 `living_room_fan_light_sync_snooze`（1 小時）加上 `restore: true`，確保重啟後計時不歸零。
  · **08-3 鐵門狀態不穩、104-2 車牌辨識、104-4 車庫回家通知、08-5H 深夜熟睡**：經盤點確認重啟後皆能安全重新開始或交由其他機制處理，無重複通知或危險誤動作風險。

- **SOP-20 重啟接續（批次 1：燈光類自動化重啟防呆自癒）**：
  · **800-14 樓梯燈（14、14B、14C、14D）**：新增 `ha_start` 觸發，HA 重啟 1 分鐘後若樓梯燈亮著且非常開模式，自動進入 3 分鐘定時關燈倒數，避免重啟中斷倒數導致樓梯燈常亮；保護 `trigger.to_state is defined`。
  · **08-5K 頂樓開機狀態自癒檢查AI**：重啟 30 秒後若頂樓感應暫停旗標開啟但計時器已結束（或遺失），自動解除感應暫停。
  · **00-2J 氣氛燈情境同步AI**：新增 `ha_start` 重啟接手，重啟 1 分鐘後（避開提醒閃燈）依目前情境自動同步機台氣氛燈顏色。
  · **106D 網關切換同步Aqara開關AI**：新增 `ha_start` 重啟接手，重啟 1 分鐘後檢查網關警戒模式與 Aqara 虛擬情境開關是否一致，不一致則自動同步；全變數與條件加 `trigger.to_state is defined` 保護。
  · **08-4 客廳大門開門燈**：新增 `ha_start` 接手，重啟 1 分鐘後若路燈／門口燈亮著，自動接續檢查大門狀態並在關門後 5 分鐘關燈。
  · **盤點確認無需更動**：800-15、800-10、104-1B、21A 經稽核皆為短等待（<30s）或即時翻轉按鈕，重啟不會遺留懸掛狀態。

- **3D 面板 UI4.0-beta8／全域警報彈窗（`www/floorplan/v4/alert-popup.js`）**：
  · **全域智慧跳窗**：涵蓋智慧家庭儀表板（`/lovelace-smart/*` 所有分頁）與牆上 Kiosk（8130 埠，透過 `window.__kioskHass` 動態載入）。
  · **精準警報過濾**：本地橙色／紅色燈號、疏散、海嘯、土石流、颱風警報、大豪雨與國家級警報才會彈出，一般水務搶修、黃色燈號不再打擾。
  · **逾時防干擾與全文字雜湊去重**：超過 1 小時且未讀的舊災害與地震報告不彈出；使用全文雜湊鍵（`hashStr`）取代前 120 字比對，避免同則訊息後續修訂被誤遮蔽；新地震預警直接覆蓋舊預警。
  · **自適應防跑版與自動倒數**：30 秒倒數進度條自動關閉，支援右上 `✕`、底部「我知道了」、背景遮罩與 `Esc` 關閉；全欄位採用 `min-width:0` 與 `overflow-wrap:anywhere`。
- **離家戶外摘要加入在地災害提醒（`packages/v41_outdoor_brief.yaml`，`sensor.leave_outdoor_brief`）**：
  · 整合近 36 小時內影響苗栗／竹南／新竹的氣象與災防警戒（颱風、海嘯、豪雨、強風燈號、淹水等）。
  · 自動附帶在地白話安全叮嚀（如防風、避開低窪積水等），並與戶外一般降雨／強風提醒智慧去重，避免語音與文字重複叮嚀。
- **通知告警排版縮短與在地顏色標記（`custom_templates/notify_body.jinja` 的 `disaster_hint` 與 `special_body`）**：
  · 離家等通知中的「氣象告警」採用精簡短版：僅保留「原因・災種」與在地燈號，下一行提醒縮減為一句；紅／橙色燈號地區及安全關鍵字精準標色（紅/橘）。
  · 地震預警速報、最新地震報告、氣象告警通知採用一致的結構化卡片與視覺燈號。
- **03苗栗天氣告知系統AI 更新**：同步更新為 `V4.2.0`（`ai_miaoli_weather_disaster_notify`），LINE 告警訊息格式優化。
- **家人主要裝置選擇（`00-2S家人主要裝置切換AI`、`packages/v41_person_main_device.yaml`）**：自動化管理面板「系統維護」每位家人一張現代化卡片，顯示 person.* 目前參考的裝置與在家狀態，可選主要裝置（含「其他（自訂）」輸入 `device_tracker.xxx`，只有選「其他」才出現輸入欄）；Kenny 的手錶追蹤欄位 `input_text.watch_tracker_entity_kenny` 併入卡片。切換前檢查該裝置在家狀態要和 person 一致，再改寫 `persons.yaml` 並 `person.reload`。細節見下方 V4.2.0 區段的追加項目。
- **LINE 通知新格式（`notify_body.jinja`，`PROJECT_RULES.md` SOP-15）**：標題與每個小段落上方橫線、卡片上緣留白、所有 `※` 備註小字並對齊圖示且上方有整條橫線、顏色示意條、氣象告警自成縮排小段落（一個重點一行）、紫外線最多橘色；所有 LINE 卡片（含地震／災害專用卡片標題列）共用。
- **LINE 段落分隔統一（`notify_body.jinja` 的 `flex_rows`）**：訊息裡的空白行就是段落分界，所有 LINE 卡片在分界處自動加一條橫線（原本只有小標題行上方有），不用每則通知各自處理。疑似入侵通知（`入侵警報AI`）同步改寫：刪掉「在『家庭』App 按『解除網關警報』」的括號說明，家人回來改成「到『家庭』App 點選『早安』或『到家』情境」，倒數與結果改成「名稱：數值」列並只把重點（秒數、觸發網關警報）標紅，不再整段紅字、也不會太早換行；「家人回來」保留圖示、合成一段話（「家人回來：到『家庭』App 點選『早安』或『到家』情境，就會取消，不會響警報。」，「就會取消」標綠）。`flex_rows` 的一般句子（沒有「名稱：」的句子）也支援 `⟦o:重點⟧` 顏色標記。
- **離家入侵偵測誤報（`08-7離家入侵偵測AI`、`入侵警報AI` V4.2.2）**：2026-10-22 14:29 家人開車回家，車庫攝影機動作先觸發緊急通知、幾秒後才取消。原因：車庫攝影機在 HA 有兩個名稱相同的裝置（UVC G6 Instant／G6 Instant），一次動作被當成「2 個不同裝置」。①「不同裝置」改用裝置名稱判斷，同一台實體裝置只算一個訊號；②新增寬限 `input_number.intrusion_grace_sec`（預設 45 秒，面板「離家入侵偵測」可調 0～300）：2 個訊號成立後先等這段時間再檢查一次，家人已回到家（手機連上 Wi-Fi 或網關切到在家）就完全不發通知。
- **離家通知重複修正（`100B自動離家AI` V4.2.0）**：重新載入範本／person 造成 `at_home_*_location` 短暫 unavailable，離家計時重啟而重複發送；離家情境已開超過 3 分鐘就不再重發。
- **自由文字災害通知的語音廣播與去重簽章用整段原文**：廣播會把全國縣市整段念出來（違反「只念在地」），簽章也因其他縣市文字改變而不同，NCDR 只改其他縣市重發時會重複通知。現在兩者都改用解析後的本地警戒組：廣播詞只念「時段＋本地地區有○○」加安全提醒（130 字內）；簽章只含警戒種類＋本地地區。實測只改其他縣市的兩版簽章相同。（`notify_body.jinja`：`disaster_voice`、`disaster_sig`）
- **燈號卡片排版**：與竹南／苗栗／新竹無關的燈號組（例如只列臺北、南投的黃色燈號）整組不顯示；本地燈號組內時段、地區標籤、說明之間的間距加大、框內留白加大，較好閱讀（LINE 卡與 HA 通知）。
- **燈號通知地區清單有括號時，竹南／苗栗／新竹被漏掉**：2026-10-22 23:10 的颱風風力橙色燈號，地區清單含「臺東縣(含蘭嶼、綠島)」，LINE／HA 卡片的解析規則碰到括號就從括號後重新開始，只剩「澎湖縣」，漏掉新竹市、新竹縣、苗栗縣（在地廣播詞與去重簽章也受影響）。現在地區部分允許括號，並先移除括號補充說明再拆地區；實測該則訊息可正確標出新竹市、新竹縣、苗栗縣，在地廣播詞與簽章也正確。（`notify_body.jinja`：`parse_alert_region` 與 5 處燈號解析式）
- **HA 重新啟動後車庫燈一直亮（104-1 V4.2.0，加上啟動接手）**：「鐵門關閉＋5 分鐘無人車活動後關燈」是記憶體裡的計時，HA 重啟就消失。2026-10-23 11:29 重啟時剛好在倒數，重啟後主燈與樓梯燈一直亮著（104-1C 全員離家關燈只在沒人在家時才動作）。現在 104-1 加上「HA 啟動」觸發：啟動 1 分鐘後若車庫主燈或樓梯燈亮著，就重新進入關燈流程；`is_manual_action` 變數補上沒有 `to_state` 時的保護。
- **通知內文「一句塞多個重點」改成分行（SOP-15）**：把擠在同一句的多個重點改成「標題行＋名稱：數值列＋※ 備註」，涵蓋緊急模式（05B）、門鎖電量四級與換電池校正（100C1／100C2）、Tesla 充電器（開始、完成、離峰未充、異常、超過 6 小時、插槍未充、測試）、鐵門提醒與自動關門結果與取消（104-3）、車牌辨識關門流程（104-2）、網關回到在家警戒（106）、緊急三擊暫停與恢復（05G）、頂樓風扇三則（22）、疑似入侵取消與未觸發（入侵警報）、失效實體巡檢（00-3）、入侵偵測測試未發送（08-7）、家人主要裝置切換（00-2S，含 `gen_person_main_device.py`）、頂樓感應暫停。地震預警／地震報告與災害卡片本來就由專用卡片處理，LINE 舊式 payload 原本已逐行分好，未更動。
- **LINE 卡片底部連結區**：「開啟家庭控制」頁尾的密碼改為正確大小寫（KIOSK1105@），帳號與密碼同一行、PIN 與「僅外網需要」同一行；底部連結說明與「來源・時間」之間加分割線、間距與灰色區塊內邊距加大；鐵門自動關門卡不再顯示「已執行自動化…」。（`統一通知AI.yaml`）
- **自由文字的災害通知（土石流、颱風豪雨、淹水警戒）沒有標出竹南／苗栗／新竹，也是一整段字**：這類訊息沒有「局部地區有…燈號」句型，原本只顯示一大段文字。現在 LINE 卡與 HA 通知都會：①最上方列出「本地影響」（竹南紅、苗栗藍、新竹綠）；②依「警戒種類（豪雨／大豪雨…）＋時段＋地區」分組，地區中的竹南／苗栗／新竹以顏色標示，其餘縮成灰色小字；③「超大豪雨地區：…」等額外行、④安全提醒條列、⑤注意事項各自成框。沒有提到本地時顯示「本則訊息未提到竹南、苗栗、新竹」。只顯示與竹南／苗栗／新竹有關的警戒組（無關地區整組隱藏、不再列「其他地區」），影響時段每組都顯示；土石流類通知標題改為「淹水災害警戒」（本地不易發生土石流）。（`custom_templates/notify_body.jinja`：`hl_spans`、`hl_html`、`free_parse`、`special_body`、`special_md`）
- **提醒閃燈後機台 LED 停在紅色（`氣氛燈AI` `mood_alert`）**：UniFi 機台 LED／網關夜燈不回報 RGB，`scene.mood_alert_snapshot` 只能還原成「開」不能還原顏色，提醒色（重要＝橘、緊急＝紅）一直留到下一次情境。2026-10-22 21:34 車庫回家通知閃燈後車庫機台停在紅色，但當時是在家模式，重按到家才變綠。現在提醒結束時依 `input_text.ambient_scene_state` 把機台改回目前情境色（呼叫 `script.ambient_scene`）。
- **更新紀錄被誤判成地震預警卡片（`notify_body.jinja` 的 `special_body`／`special_md`）**：每日 18:00 的「智慧家庭更新紀錄」內文列了「地震預警速報、災害訊息、燈號」等字，專用卡片原本連內文一起判斷，被當成地震預警卡片顯示（還帶著舊的 3 級 20 秒）。現在卡片種類只看標題與來源，以及嚴格的訊息格式（地震報告要以「月/日 時:分…發生規模」開頭、災害要有「…局部地區有…（橙色燈號）」句型），標題或來源含「更新紀錄」一律不套專用卡片。HA 通知與 LINE 卡片同時修正。
- **災害訊息不重複通知（`03苗栗天氣告知系統AI` V4.2.2、`notify_body.jinja` 的 `disaster_sig`、`alert-popup.js`）**：NCDR 常常只改其他縣市名單或時段文字就再發一版（10/22 16:55 與 17:23 兩版只差其他縣市，LINE 發了兩次）。改用「在地內容簽章」（燈號＋竹南／苗栗／新竹地區＋條件）判斷是否為新訊息，在地內容沒變就不再通知、不廣播；3D 面板彈窗的已讀鍵也用同一個簽章（HA 與 Kiosk 兩份都更新）。在地內容真的變了（例如苗栗縣橙色燈號解除）仍會通知。
- **智慧家庭儀表板（`smart-home.yaml`，現在納入 git）**：①上方分頁列新增「自動化管理」分頁（`/lovelace-smart/automation-link`），點了直接跳到自動化管理面板（`floorplan-v4-impl.js` 的導向，分頁內也有一顆「前往自動化管理面板」按鈕當備援）；②「系統」頁的「即時通知」改成和自動化管理面板一樣的現代化卡片：氣象與災害告警（燈號分色、地區與條件分行、可展開完整內容）、最新地震報告（規模、最大震度、時間、震央）、Tesla 充電器（狀態標籤），最後保留「清除所有通知」。
- **離家入侵偵測誤報修正與 LINE 段落橫線統一（V4.2.2）**：同一台實體裝置只算一個訊號（車庫攝影機有兩個同名裝置，一次動作被當成兩個）、判定後先寬限 `intrusion_grace_sec`（預設 45 秒）家人回家就不發；LINE 卡片空白行即段落分界、自動加橫線；疑似入侵通知改寫（刪掉括號說明、只標重點色、家人回來合成一段並保留圖示）。細節見下方 V4.2.0 區段的追加項目。
- **V4.2.0 發布後併入本版的修正**：早安／到家廣播報室內空氣、晚安廣播報明日天氣；車庫燈手動關燈冷卻不再被離家情境逐環關燈誤判（104-1B）；04 苗栗天氣（按鈕）LINE 訊息補回 `type`；補回 `auto_scene_earliest_*` 兩個 helper（重複的 `input_datetime`）。

## 本次調整（V4.2.0 - 2026-10-18：燈組動畫與魔方、戶外空氣品質、3D 面板 UI4.0-beta7、通知排版統一、移除影子模式；含原 V4.1.6 全部內容）

- **自動化管理面板新增「耗材與額度」專屬分頁**（`scripts/generate_automation_panel.py`）：
  · **專屬分頁整合**：側邊欄自動化管理面板新增「耗材與額度」（`supply`）頁面，採用 iOS 圓角與自適應 vertical-layout 卡片排版。
  · **LINE Bot 全月消耗預測模型**（`packages/v42_linebot_forecast.yaml`，`sensor.line_bot_forecast`）：依據本月累積發送量與經過天數動態計算日均消耗率，推估一般 Bot（Bot 1~3，門檻 196 則）耗盡日期，精準預警是否會動用到緊急 Bot（智慧家庭A / Bot 0），並預測動用後能否支撐至每月 1 日官方額度重置。
  · **4 大 Bot 額度進度看板**：顯示當前使用中 Bot、輪替目標、各 Bot 已用量、剩餘額度、使用率進度條。
  · **空氣清淨機濾網壽命監控**：即時讀取濾網剩餘壽命百分比，搭配門檻警示（≤10% 準備備品、≤5% 請更換）與通知狀態旗標。
  · **9 大感測器電池壽命預估**：串接 `sensor.battery_forecast`，列出客廳門鎖、鐵門感應器、書房開關、魔方、廁所感應、廚房感應、夜燈、電鈴、無線開關之電量、預估可用天數、耗盡日期與日耗電率。
  · **耗材設定與一鍵測試操作**：耗材更換額外 LINE 推播開關、定期摘要時間設定、一鍵執行耗材電量系統測試按鈕。

- 打包 V4.1.6 草稿至今的全部更新發布為 V4.2.0（次版本：新增動畫燈、戶外空氣品質、通知卡片統一排版等功能）。
- **清理（冗余移除）**：①移除影子模式。07 空氣清淨機（`air_ai_shadow`）與 100A 到家早安（`auto_scene_shadow`）早在 2026-10-10 核准並關閉，程式碼分支與 helper 刪除、行為不變；入侵偵測 08-7（`intrusion_watch_shadow`）依使用者決定改為正式運作，判定成立即緊急通知、廣播、倒數後觸發網關警報，`script.intrusion_alert` 只剩 real／dry／test 三種 mode，乾跑（事件 `intrusion_signal` 加 `test: dry`）與 LINE 測試模式保留。②自動化管理面板不再列這三個開關（`scripts/generate_automation_panel.py` 的 GONE 清單）並已重新部署。③已停用的舊 07／07-1～07-4／舊 100A 在 V4.1.5 已刪除，不再保留。
- **情境廣播（`script.scene_announce`，`Scripts/情境檢查AI.yaml`）**：早安／到家廣播加上目前室內空氣狀況（廚房 PM1.0／2.5／10、CO2、TVOC、甲醛、CO 取最差一項；良好只報良好，稍高或偏高時說明是哪一項並建議開空氣清淨機，偏高時依戶外空氣建議開窗或先不要開窗）；晚安廣播加上明天天氣（用 `weather.get_forecasts` 逐 3 小時預報算天氣、氣溫範圍、降雨機率，必要時提醒帶傘、防曬或加衣；預報讀不到就維持原句）。晚安廣播仍只在手動觸發時播報。
- **車庫燈（`104-1B` V4.2.0）**：修正離家／晚安情境逐環關燈被當成手動關燈而啟動冷卻。2026-10-18 16:28 長按餐廳燈啟動離家情境、約 1 秒後單擊車庫主燈開燈，情境最後一環又把它關掉，因 5 秒內有 Terncy 單擊紀錄被判成手動關燈，啟動 120 秒冷卻，期間攝影機偵測到人與鐵門開啟都不重新開燈。現在離家或晚安情境開啟 90 秒內的關燈不算手動、不啟動冷卻。
- **氣象告警通知縮短（`custom_templates/notify_body.jinja` 的 `disaster_hint`）**：離家等通知裡的「氣象告警」改成短版，只留「原因・災種」與各地區燈號（例：氣象告警：颱風外圍・強風　苗栗縣橙色燈號、新竹市、新竹縣黃色燈號），下一行提醒也縮成一句（例：可能下雨、有強陣風，外出請帶傘、小心行車）；只有紅／橙色燈號的地區與提醒裡的重點動作用橘（紅）色標示，其餘一般色。廣播用的語音文字不變。追加：離家等通知的氣象告警自成一個縮排的小段落放在最後，一個重點一行（「氣象告警：」小標題下，原因、紅／橙／黃色燈號的地區各一行，下面接一句提醒），只有紅／橙色燈號的地區與提醒裡的重點動作上色，其餘一般色；紫外線、空氣品質等其他提醒仍在「戶外狀況」段落內。提醒行改用新的小字標記 `※~`（`notify_body.jinja` 的 `model`／`flex_rows`：LINE 字級 xxs，縮排對齊上一行的圖示而不是文字）；紫外線讀數與提醒最多用橘色（不再用紅色）。所有 LINE 卡片（`flex_rows`）：每個小段落（小標題行或【段落】）上方加一條橫線，提醒小字（`※~`）上方加一條短橫線（連續的提醒只加第一行）；HA 通知與地震／災害專用卡片（`special_body`）沒有改。
- **修正**：①`04苗栗天氣告知系統（按鈕）`（`automations.yaml`）的 LINE 訊息第二則缺少 `"type":"text"`，LINE 會拒收，已補上；②`packages/v41_auto_scene.yaml` 有兩個重複的 `input_datetime:`（V4.1.6 加 `scene_verify_skip_alarm_until` 時造成），後面的蓋掉前面的，`auto_scene_earliest_workday`／`auto_scene_earliest_holiday`（100A 日出時間讀不到時的備援時間）沒有建立，已合併成一個區塊，兩個 helper 恢復（預設 05:30／07:00）。
- **3D 面板 UI4.0-beta8／全域警報彈窗（`www/floorplan/v4/alert-popup.js`）**：①只對本地橙色／紅色燈號、疏散、海嘯、土石流、颱風警報、大豪雨與國家級警報跳窗，水務搶修、黃色燈號與只是提到地區的訊息不再跳；②超過 1 小時且沒讀過的災害／地震報告不彈（災害用 `sensor.disaster_last_valid_update`、地震用報告本身寫的時間，不看會在重載歸零的更新時間），感測器離線後舊訊息回來也不彈；③已讀判斷改用整段文字的雜湊（原本只比對前 120 字）；④新的地震預警直接取代畫面上的上一則；⑤牆上 Kiosk（8130）也載入彈窗：`kiosk/server.py` 的 `/api/states` 多給災害、地震報告、地震預警實體與 `last_updated`，`kiosk/web/index.html` 設 `window.__kioskHass` 後載入 `alert-popup.js`；⑥版本顯示 UI4.0-beta8（HA 與 Kiosk 一致）。
- **家人主要裝置選擇（`00-2S家人主要裝置切換AI`、`packages/v41_person_main_device.yaml`、`scripts/person_set_main.py`、`scripts/gen_person_main_device.py`）**：自動化管理面板「系統維護」頁新增「家人裝置追蹤」：表格顯示 Kenny／Iris／Jerry／Elay 的 person.* 目前實際參考哪個裝置（`sensor.person_<id>_source_device`，取 person 的 source 屬性）與該裝置的在家狀態，下方四個選單（`input_select.person_main_device_<id>`）可選每個人的主要裝置。選擇後先檢查「選的裝置在不在家」要和 person 目前一致（不一致就退回原選項並發 HA 通知，避免切換後在家狀態突然改變而誤觸發離家／到家情境），再改寫 `packages/persons.yaml`（舊檔存 `persons.yaml.bak`）、`person.reload`、驗證並發 HA 資訊通知；HA 啟動 60 秒後選單對齊 person 實際參考的裝置。選項與裝置對照由 `gen_person_main_device.py` 產生（改候選裝置請改這支再執行）。選單最後一項「其他（自訂）」：在該家人的文字欄位（`input_text.person_main_device_custom_<id>`，只接受小寫的 `device_tracker.xxx`，HA 的 pattern 與自動化都會檢查）輸入清單以外的裝置，選「其他」之後改文字欄位也會重新套用；裝置不存在或離線、或在家狀態和 person 不一致都會退回並通知。面板每位家人一張現代化卡片（button-card：頭像、在家狀態、person 目前參考的裝置與其在家狀態），下方是主要裝置選單；自訂裝置輸入欄只有選了「其他」才出現（conditional 卡片），欄位還是空的時選單停在「其他」、不退回也不通知，輸入有效的 device_tracker 後才套用；Kenny 的卡片併入 `input_text.watch_tracker_entity_kenny`（手錶追蹤裝置：顯示名稱與在家狀態，欄位直接在卡片下修改，不再出現在一般清單）。新增 helper：`input_select.person_main_device_kenny／iris／jerry／elay`、`input_text.person_main_device_custom_kenny／iris／jerry／elay`、`input_boolean.person_main_device_busy`（內部，不顯示）。
- **離家通知重複（`100B自動離家AI` V4.2.0）**：重新載入範本／person 時 `sensor.at_home_*_location` 會短暫 unavailable，「全員離家 4 分 10 秒」的計時重新開始，約 4 分鐘後又發一次離家通知（2026-10-22 11:36、13:01、13:08、13:19、13:45 家人群組重複收到，都是範本重新載入造成）。現在離家情境（`aqara_li_jia`）已開著超過 3 分鐘就不再重發。
- **LINE 卡片分割線與間距**：所有 LINE 卡片標題下方加一條橫線（`notify_dispatch`、舊格式轉換卡片、地震／災害專用卡片的標題列下方；LINE Bot 額度通知因沒有標題列，改在標題句下方），卡片內容上緣由 14px 加到 20px，標題上下留白加大。
- **LINE 新格式規定套用到全部訊息（`custom_templates/notify_body.jinja` 的 `model`／`flex_rows`、`PROJECT_RULES.md` SOP-15）**：所有 `※` 備註（不含不縮排的 `※※` 圖例說明）一律小字、縮排對齊上一列圖示、上方一條延伸到右邊的橫線；橫線原本的短線改為整條；新格式規定（標題與段落橫線、同主題重點分行縮排、備註格式、只標重點色）寫進 SOP-15。
- **LINE 顏色示意條**：`※※ 綠色正常　黃色注意　紅色異常` 這類圖例說明改成一條淺灰圓角的小字示意條（「顏色示意　● 正常　● 注意　● 異常」），圓點顏色與卡片裡的綠 `#16A34A`／橘 `#D97706`／紅 `#DC2626` 一致（`flex_rows` 的 `※※` 圖例判斷，所有用這句的通知都套用）。
- **發布注意**：入侵偵測沒有經過影子觀察就轉為正式，若發生誤報請在 Known Bugs 回報；`env_alert_co_dry_run`（CO 緊急乾跑）不是影子模式，維持開啟。

- 3D 儀表板側欄（`www/floorplan/v4/floorplan-v4-3d.js`）：窄版（側欄寬度 < 250px，例如 iPad mini 5 橫向）時，時間旁的日型標籤（工作日／節日名稱）被時間擠成只剩「工…」。現在標籤固定在時間右邊、完整顯示，秒數縮小（.74em）；放不下時 `_fit()` 依序縮小時間與標籤（fit1：23px／10px、fit2：20px／9px、fit3：17px），寬度 130px 以上都能一行完整顯示（瀏覽器實測 240／200／170／150／130px）。HA 與 NAS kiosk 都已更新（載入時不快取，重新整理即可）。
- `100A自動啟動到家早安情境AI`（V4.1.6）新增觸發 `living_room`：任何一位家人（person 位置 `sensor.at_home_*_location`）在客廳停留 1 分鐘（原 2 分鐘，2026-10-14 縮短），且網關不在在家模式（`aqara_zai_jia` 為 off），就依時段自動啟動早安或到家情境。停留期間位置跳到別處或離家會重新計時（只有持續在客廳才算）；仍受最早啟動時間（半夜在客廳不會啟動）、總開關、影子模式、3 分鐘防重複與保全模式限制，不需要「家裡有活動跡象」。
- `100A自動啟動到家早安情境AI`（V4.1.6）：燈光／設備／鐵門觸發（客廳小燈、餐廳燈、廁所燈、廚房燈、客廳電風扇、車庫鐵門關閉）新增條件：至少一位家人（`binary_sensor.at_home_anyone_home`）在家才啟動，避免非家人進屋碰到燈或設備讓網關自動變成在家模式；有人回到家／門鎖解除離家模式／有人在客廳三種觸發不受影響。
- 新增 **離家入侵偵測**（V4.1.6）：`08-7離家入侵偵測AI`（偵測與判定）、`08-7C入侵偵測訊號收集AI`（由 `scripts/intrusion_stats.py` 自動產生，把候選感應器的觸發轉成 `intrusion_signal` 事件）、`08-7D入侵偵測感應器統計AI`（每週日 03:50 或按統計按鈕）、`Scripts/入侵警報AI.yaml`（`script.intrusion_record_signal`、`script.intrusion_alert`）、`packages/v41_intrusion.yaml`（開關、參數、手動覆寫欄位、`sensor.intrusion_sensor_lists`、`sensor.intrusion_effective_summary`）。
  · 監控條件：總開關開、四位家人都離家滿 10 分鐘（`intrusion_arm_nobody_min`）、網關離家情境滿 20 分鐘（`intrusion_arm_away_min`），且網關不在在家模式（在家／早安／到家就不監控，倒數中也取消）。
  · 訊號：室內動作感應器、客廳門鎖（事件型，有人開門才回報，不看離線比例）、車庫鐵門（開啟後緩衝 5 分鐘等家人回來；用 HA／HomeKit／自動化開的不算）、二樓門鎖同步開關（緩衝 90 秒）。5 分鐘內來自「不同裝置」的 2 個以上訊號才判定疑似入侵。
  · 處理：緊急級 LINE／HA 通知（附車庫與頂樓攝影機截圖兩張、攝影機即時影像與「家庭」App 按鈕、備註「家人回來切到在家或早安情境即可避免觸發」）＋廣播 → 倒數 30 秒（家人回來／切到在家模式／關閉功能就取消）→ 觸發網關警報（`aqara_chu_fa`，由 106 同步到實體網關）；30 分鐘內不重複。
  · 面板開關：`intrusion_watch_enable`（總開關）、`intrusion_watch_alarm_enable`（觸發網關警報）、`intrusion_watch_shadow`（影子模式，預設開：只寫 logbook，不通知不響警報）、各項秒數／分鐘設定、強制納入／排除欄位；`intrusion_watch_test` 測試按鈕只發通知（不廣播、不響警報）。
  · 每週統計（離家期間資料）：離線比例 > 10% 或離家時每小時觸發 > 0.5 次的排除，穩定的（觀察 ≥ 24 小時、有回報）自動納入，包含新裝的感應器；有變動發 HA 資訊通知。首次統計（74 小時離家資料）：納入 15 個，排除 3 個（廁所夜燈、車庫夜燈離線比例過高；廚房毫米波每小時亂跳 1.6 次）。
  · `統一通知AI`（V4.1.6）：`notify_dispatch` 新增選填欄位 `image2`（第二張圖）。
  · 限制：家裡沒有獨立的門窗磁簧感應器，窗戶只能靠室內動作偵測；客廳門鎖是事件型感應器。
- `入侵偵測測試通知`（V4.1.6）：新增 `input_boolean.intrusion_watch_test_mode`（LINE 測試模式，預設關）；沒開時按測試按鈕只發一則 HA 說明通知，開了才會真的發 LINE 測試卡（送出一次後自動關閉）。按鈕觸發（測試與統計）加 `not_from: unavailable／unknown`，避免重新載入 helper 時被當成按下（2026-10-13 重新載入時誤發過一次測試通知）。
- `100B自動離家AI`（V4.1.6）離家時「門鎖／鐵門有未上鎖或未關」通知改成說清楚是哪一個（鐵門開著、或二樓門鎖同步開關顯示未上鎖）與狀態更新時間，等級維持緊急。2026-10-13 的誤報原因：`input_boolean.er_lou_men_suo_tong_bu_kai_guan` 的 on／off 設定相反，已由使用者修正。
- `情境檢查AI`（V4.1.6）：保全模式複檢前再等最多 10 秒（網關切換有時要 6 秒以上才回報，原本固定 5 秒；2026-10-14 11:31 的「離家情境補救後仍未到位（保全模式）」誤報原因）；`106C_解除網關警報整合AI`（V4.2.1）重置流程開始時寫入 `input_datetime.scene_verify_skip_alarm_until`（現在＋60 秒），期間情境檢查略過保全模式檢查（離家情境後馬上解除網關）。
- 3D 儀表板「全棟」模式右側樓梯燈標籤被卡片右緣切掉（`floorplan-v4-3d.js`）：右欄標籤位置用第一次量到的寬度（量不到就用 90px）快取，實際標籤比它寬時就超出右緣；改成標籤顯示時每次排版重新量寬度，右欄靠右位置也多留 12px 並保證不小於左邊界。HA 與 NAS kiosk 都已更新（重新整理即可）。
- 3D 儀表板「全棟」模式（手機與電腦，`floorplan-v4-3d.js`）：工具列（恢復預設視角／名稱等按鈕）不再被隱藏；全棟預設顯示名稱標籤（手動切換過名稱按鈕則依使用者設定）；手機版縮小圖示與文字，並限制左右欄標籤寬度不超過卡片一半（過長名稱以刪節號截斷），避免被切掉或跑版。HA 與 NAS kiosk 皆已更新（重新整理即可）。
- LINE 卡片排版（`custom_templates/notify_body.jinja`，所有 LINE 訊息共用，含舊格式純文字訊息）：圖示只留給需要注意的行（警告、異常、未關、未上鎖、離線、不穩…），一般項目不放圖示；「名稱：數值」拆成灰色名稱＋粗體數值；內文與標題中的 emoji 一律移除。
- `08-3鐵門狀態不穩通知`（V4.1.6）：改用統一通知（LINE 卡片），移除舊的三段純文字；鐵門中斷 4 分鐘時，若 UniFi 設備 20 分鐘內剛重開機或不是已連線（例如更新路由器／AP），先最多等 10 分鐘讓鐵門恢復，仍未恢復才通知。
- LINE／HA 通知圖示改版（`custom_templates/notify_body.jinja`）：標題行不放圖示（保持單行）；小標題（冒號結尾）、「名稱：數值」與警告行才放圖示；新增 70 款扁平圓形圖示（`www/icons/b2/<名稱>_<n|g|o|r>.png`，圖案自動置中），顏色依重要度（紅=緊急、橘=警告、綠=正常完成、藍=一般）；依關鍵字自動挑對應圖示（電量、天數、時間、鐵門、門鎖、保全、網路…）。
- LINE 卡片細節：「名稱：數值」間距縮小、注意符號 ⚠︎（無圓圈）緊接在「請注意。」後面、圖示對齊換行文字的第一行；LINE Bot 額度通知（即將切換／額度用盡）改用同一套新格式。
- `00-2J氣氛燈情境同步AI`（V4.1.6）：一樓 mesh、四樓 extender 重開機／更新後 60 秒自動重新套用目前情境顏色（原本更新後 LED 變回預設色，需手動再按情境）。
- `氣氛燈AI`（V4.1.6）：通知閃燈（重要／緊急）加入車庫樓梯燈（`switch.lou_ti_deng`，開關式，閃完還原原本開／關；不可用時略過）。原本已含客廳／餐廳彩燈、三樓樓梯燈（開關）、四樓與頂樓樓梯燈（`yeelink_color5_0fb7/13b8`）及 UniFi 機台 LED。
- LINE 卡片（共用範本）：「…通知」標題用鈴鐺圖示避免與下方內容圖示重複；重點行（開始時間、結束時間、用電量、預估、狀態…）最多 3 行用綠／紫對比色；沒有冒號的舊式行（例如「開始時間 2026-10-15」）也自動當成名稱／數值行。
- 新增 `09C電視待機喚醒AI`（V4.1.6）：客廳電視（Android TV 遙控與 Chromecast）都連不上 2 分鐘 → 開啟 `input_boolean.tv_ir_power`（自動復位，由 Apple 家庭自動化觸發 Aqara 紅外線電視情境）→ 等電視重新連上 → 用網路指令關機，讓電視停在待機且保持連線；連不上發通知不重送。總開關 `input_boolean.tv_keepalive_enable`，維護模式期間不動作。需自行把 `input_boolean.tv_ir_power` 加入 HomeKit 橋接並建立 Apple 家庭自動化。
- Xiaomi Gateway 3（HACS）更新 v4.2.4 → v4.3.0（2026-10-16）：官方只動 `core/devices.py` 以外的轉換器與新裝置支援，你自己改過的 `core/devices.py` 五處（藍牙溫濕度計 19457/19458/18435、Motion Sensor 2s 19552、旋鈕電量 1.p.1、濕度浮點 18440、Linptech 23308）以三方合併保留；本機修改存成補丁 `scripts/xg3_devices_local.patch`（相對官方 v4.2.4），備份在 `backup_20261016_xiaomi_gateway3_v424/`。**之後 HACS 再更新這個整合會把 `devices.py` 蓋回官方版，需要重新套回你的五處修改**。
- 3D 儀表板感測器名稱（`floorplan-v4-3d.js`）：廚房／廁所人體感應固定顯示「廚房人體感應」「廁所人體感應」；廚房兩組溫濕度改名「廚房溫濕計」、空品儀佔用改「廚房空品儀 佔用」；單層畫面不再把「廚房／客廳／餐廳」前綴去掉（同一層有多個房間，只會去掉樓層字樣如頂樓、五樓、車庫）。
- `06環境異常通知AI`（V4.1.6）：空氣品質等通知的讀數改成條列（超標項目、目前讀數各一組，每項一行並縮排），數值與圖示依等級標綠／黃／紅（`notify_body.jinja` 新增行尾標記 `⟦g⟧⟦o⟧⟦r⟧` 與 `env_tag()` 燈號巨集；門檻：CO2 1000／2000、PM2.5 15／35、TVOC 220／600、CO 9／35、甲醛 0.05／0.08、溫度 15–30／10–40、濕度 40–60／30–70），TVOC 改「總揮發性有機物」，「超過門檻」另起一行，內文不再重複標題。其他通知也可在行尾加 `⟦g⟧⟦o⟧⟦r⟧` 標示數值等級。
- `08-5F頂樓自動上下樓情境AI`（V4.1.6）：上樓不再被「剛下樓的保護鎖」卡住——保護期間只要 iPhone 90 秒內連上頂樓 AP 且攝影機 30 秒內看到人（確定回來），就直接成立上樓情境並解除下樓鎖；下樓鎖 90 秒縮為 45 秒（含 `08-5F頂樓下樓補判AI`）。起因：2026-10-17 21:36 下樓補判成立後 20 秒就回頂樓，上樓情境晚了 1 分 40 秒（21:38:04 才成立）。
- 新增統一電池電量預估（`scripts/battery_forecast.py`、`packages/v41_battery_forecast.yaml`、`00-2Q電池預估更新AI`）：讀 HA 長期統計（1 年以上），每日中位數＋5 天移動中位數去掉突波與來回跳動，偵測換電池分段，日耗電率＝本輪平均（含最後一次下降後一直沒掉的時間＋半格）、最近 60 天較快時往快修正、有上一輪完整電池或門鎖上一輪日耗電率時混合；目前電量依耗電率從最後一次下降往下推（不低於最後讀數減一格），所以裝置久久才回報時剩餘天數仍會每天遞減。結果在 `sensor.battery_forecast`（屬性 items），每天 03:50 與 HA 啟動後更新。客廳門鎖 `sensor.doorlock_batt_days_left_last_model` 改為優先使用這個預估（舊公式 291 天 → 新 393 天）。
- `00-2C耗材更換AI通知`（V4.1.6）：定期摘要電量以顏色標在百分比上（綠健康／黃偏低／紅請更換），下一行縮排淡色顯示預估還能用多久（半年以上綠、1～6 個月黃、1 個月內紅），已排除與資料天數改為備註，名稱縮短避免換行，最後附顏色說明；分階段提醒附預估天數。通知範本新增 `※` 開頭的備註行（小字淡色、縮排）與行內顏色標記 `⟦g:文字⟧⟦o:…⟧⟦r:…⟧⟦n:…⟧`。
- V4.1.6 修正與追加：①魔方轉動改成「亮第一個還沒亮的單元（小燈→組一→組二→組三），全亮再轉一格才全關」，不再用已亮數量判斷（避免只亮組一時轉動沒反應）；魔方經 Aqara 網關只回報離散的 rotate 事件，沒有角度或方向，無法依轉動大小細調；②`06環境異常通知AI`：開窗或關門窗統一看戶外空氣（AQI>100／PM2.5≥35.5／PM10≥125 為不佳），空氣品質、甲醛、CO2、溫度警示的 LINE 與廣播在戶外不佳時建議不要開窗、開空氣清淨機，一氧化碳維持開窗通風。
- 燈組動畫 V4.1.6 追加：①「氣氛」色彩依太陽位置分 4 個時段換色調（黎明金橘、白天天藍→淡藍→暖白、黃昏橘→玫瑰→紫、夜晚柔和琥珀→藕紫→靛藍且較暗較慢）；②新增 style「快速」與「滑動」：Aqara 魔方轉動時，新亮起的那組以該時段色調光暈一閃再回到記憶（約 1 秒）；魔方滑動時餐廳三顆光帶快速掃過（約 3 秒）；關燈仍瞬間，helper 選「關閉動畫」時一律瞬間開（`configuration/Scripts/燈組動畫AI.yaml`、`automations.yaml` 魔方自動化 `1781414206841`）。
- 新增客廳／餐廳開燈動畫（`Scripts/燈組動畫AI.yaml` → `script.light_group_on`、`packages/v41_light_anim.yaml`）：打開客廳小燈、燈組一／二／三／全、餐廳燈組、全部時，燈依序（`input_select.light_anim_style`＝依序）或以暖橘→粉色光帶掃過再回到記憶色溫亮度（氣氛）亮起；只對關著的燈做動畫；緊急模式、氣氛燈提醒、熟睡鎖、總開關 `light_anim_enable` 關閉或風格選「關閉動畫」時瞬間開；關燈一律瞬間。入口＝7 個「（動畫）」template light（`light.ke_ting_xiao_deng_dong_hua`、`…_deng_zu_yi/er/san_dong_hua`、`…_deng_zu_quan_dong_hua`、`light.can_ting_deng_zu_dong_hua`、`light.ke_ting_can_ting_quan_bu_dong_hua`）；800-2／800-5／800-6 實體按鈕、`漸進情境AI`（到家／早安開燈）、3D 面板（`floorplan-v4-3d.js` 的 `switchLights`）、Google 暴露清單（`configuration.yaml`）都改走動畫；Apple 家庭請自行把動畫燈加進 HomeKit 橋接。`00-2H燈況記憶AI`（V4.1.6）記憶範圍擴大到客廳 7 顆＋餐廳 3 顆＋四樓／頂樓樓梯燈，改用燈泡自己的 `light.mode`／`light.color_temperature`／`light.brightness` 判斷（HA 的 color_mode 對這些燈常誤報 rgb）。
- 新增戶外空氣品質（`packages/v41_outdoor_air.yaml`）：`sensor.outdoor_pm2_5`／`outdoor_pm10`／`outdoor_aqi_us`（Open-Meteo Air Quality API，免金鑰、CAMS 模式資料、每 30 分鐘更新，座標取自 zone.home）與 `sensor.outdoor_air_quality`（台灣 PM2.5 分級）。`06環境異常通知AI`（V4.1.6）：廚房「空氣品質危險」若只有 PM2.5 超標、其他項目正常且戶外 PM2.5 ≥ 25，改發一般級「戶外空氣品質偏差／太差」（建議關閉門窗並開啟空氣清淨機，語音同步改寫），列出戶外 PM2.5 與等級；其他空氣品質通知的讀數最後多一行戶外 PM2.5。之後想換成環境部測站實測資料（需免費申請 API 金鑰），只要換 rest 的來源，感測器名稱不變。
- 戶外空氣品質改接環境部開放資料（`scripts/moenv_fetch.py`、`packages/v41_outdoor_air.yaml`、`00-2R環境部空品更新AI`；API 金鑰在 `secrets.yaml` 的 `moenv_api_key`，不進 git）：頭份測站 AQI／PM2.5／PM10／O3／NO2／SO2／CO／風速風向、後龍站紫外線指數、竹苗空品區 AQI 預報；每 30 分鐘更新。對外：`sensor.outdoor_air_quality`（官方 AQI 等級，屬性 aqi／pm25／pm10／level／source）、`sensor.outdoor_aqi`、`sensor.outdoor_uv_index`、`sensor.outdoor_aqi_forecast`；環境部資料超過 4 小時沒更新時退回 Open-Meteo。（data.moenv.gov.tw 憑證缺 Subject Key Identifier，Python 3.13+ 預設嚴格檢查會失敗，腳本只關掉 VERIFY_X509_STRICT，憑證鏈與主機名稱仍驗證。）
- 廚房 PM1.0 與 PM10 加入空氣品質檢測：`06環境異常通知AI` 讀數列表、超標項目（PM1.0>35、PM10>125）、戶外成因判斷；新增 `sensor.kitchen_particulate_level`（`packages/v41_kitchen_air.yaml`，三項取最差，良好／普通／偏高）。3D 面板空氣品質方塊改顯示官方 AQI。
- 離家通知與離家廣播加入「戶外狀況」（`packages/v41_outdoor_brief.yaml` 的 `sensor.leave_outdoor_brief`）：天氣、紫外線、空氣品質三行（顏色標記）；異常時附提醒——紫外線 ≥ 6、AQI > 100、降雨機率 ≥ 50% 或正在下雨、氣溫 ≥ 35°C 或體感 ≥ 38°C、氣溫 ≤ 12°C、風速 ≥ 40 km/h。`100B自動離家AI`（V4.1.6）各分支的 HA 與 LINE 通知最後附這段；`scene_announce` 的離家廣播多念一句戶外狀況。
- 3D 面板（`floorplan-v4-3d.js`）：天氣卡片新增紫外線（依等級上色：低量綠／中量黃／高量橘／過量紅／危險紫）；空氣品質卡片改用 Apple 家庭風格的 AQI 圓點圖示——電腦版圖示在左、等級與「AQI 數值 · PM2.5」在右；手機版第一行「圖示＋AQI 數值」、第二行等級小字，與天氣卡片同高。通知範本新增紫外線圖示。
- 3D 面板 UI4.0-beta7（`floorplan-v4-3d.js`）：①廚房室內感測器群組（廚房環境）點一下除了拉近，還會跳出「廚房室內空氣品質」面板：PM1.0、PM2.5、PM10、二氧化碳、總揮發性有機物、甲醛、一氧化碳各項數值與優良／普通／偏高標示，整體結論與建議（含戶外空氣不佳時請先關窗）、溫濕度與戶外 AQI，隨資料即時更新，點背景或 ✕ 關閉；②iPad mini 窄側欄（約 155 px）縮小空氣品質卡、紫外線行與在家成員的間距與字級，並讓成員清單可捲動，4 位成員都能顯示。
- 新增維護模式（`packages/v41_maintenance.yaml`）：`binary_sensor.maintenance_active`（手動 `script.maintenance_start` / `maintenance_stop`、UniFi 設備 20 分鐘內重開機或非已連線、更新安裝中，任一成立即啟動）；維護期間 `notify_dispatch` 與舊格式 `send_line_to_user` 略過一般／重要級且屬連線／離線／失敗／異常類的通知（保全、入侵、門鎖、未關、緊急級照常發送），並寫日誌。
- 新增 `106D網關切換同步Aqara開關AI`（V4.1.6）：在 HA 伺服器（或實體網關、面板）直接切換網關警戒模式時，補上對應的 Aqara 虛擬情境開關（在家警戒→`aqara_zai_jia`、夜間警戒→`aqara_wan_an`、離家警戒→`aqara_li_jia`；先關其他四個再打開目標，避免 106 看到 2 個以上開關同時為 on 而走異常分流）。切換後先等 6 秒讓 Apple 家庭同步，沒對應才由 HA 補上；只處理人為／實體切換（context 無 parent_id），不處理 106／情境／100B 等自動化改的模式，所以不會迴圈。不處理解除與警報觸發（106 的解除情境會先解除再回到在家警戒）。（2026-10-14 紀錄：直接切網關時 Apple 家庭的同步有延遲 1 秒～數分鐘，甚至沒有同步。）
- 修正 `100B自動離家AI`（V4.1.6）：離家通知整個漏掉。2026-10-12 08:09:57 判定全員離家時鐵門正在關（`closing`，08:10:05 才 `closed`），原本兩個通知條件一個要「已關」、一個要「開著」都不成立，什麼都沒發，且觸發條件維持成立不會再觸發。現在通知前先等鐵門停下來（`open`／`closed`，最多 90 秒），並新增預設分支：兩個條件都不成立時仍發一般級離家通知（含情境、鐵門與門鎖同步狀態）。
- `00-2M實體引用檢查AI`（V4.1.6）：不再把服務（action）名稱（`fan.set_preset_mode`、`weather.get_forecasts`…）與「只是前綴」的字串（`sensor.chu_fang_…_chu_fang`，後面用 `~ '_co2'` 組合）當成「可能不存在的實體」誤報（2026-10-12 03:40 的 3 則都是誤報）；修改 `scripts/check_entities.py`，修正後檢查結果為 OK。
- `100A自動啟動到家早安情境AI`（V4.1.6）：新增通知開關 `input_boolean.auto_scene_notify_enable`（預設開，自動化管理面板可關）；關閉後自動啟動情境時不發「自動啟動早安／到家情境」HA 資訊通知，情境照常啟動、logbook 與 `input_text.auto_scene_last` 照常記錄。
- 修正 `107Tesla充電器狀態與通知AI`（V4.1.6）：充飽後 00:02 誤報「離峰時段已過仍未充電／仍未開始充電」。「這次連接後是否已充過電」原本比較 `tesla_charger_start_time`（只到秒）大於 `vehicle_connected.last_changed`（含毫秒），插槍同一秒就進入充電時 start_time 反而略小而判成沒充過；改成容許 10 秒誤差。2026-10-11 18:35:57 插槍即充電、22:12:57 充飽，00:02 誤報一次。
- 新增 `08-8A 廚房燈無人保險關燈AI`（V3.4.0）與 `08-8B 廁所燈無人保險關燈AI`（V3.2.0）：燈亮著、感應器無人超過 10 分鐘就關燈（廚房需小米人體與毫米波兩顆都無人）。原本只在感應器「變成無人」那一刻關燈，手動開燈時感應器本來就是無人（沒有變化）會一直亮著。廚房「感應燈自動化」被長按關掉、廁所「手動關閉模式」啟用時不處理。

## 本次調整（V4.1.5 - 2026-10-11：夏季模式自動判斷、災害訊息分級、到家情境併入門鎖、風扇防抖、車庫誤報修正、緊急三擊維修暫停與清理）

- `22頂樓電風扇自動化AI` 修補版升級至 `V4.1.5`：風扇「關→開」時裝置自行回報的風量變動（0%→N%），以及開機後 10 秒內的風量回報，不再被判定為人為調速（原因：這類更新沒有使用者與上層動作，被 `manual_actor_detected` 誤判，導致 `ding_lou_fan_manual_speed_snooze` 自動開啟、自動調速停擺）。人為在風扇運轉中調速仍會啟用防護罩。
- 同版追加：自動調速門檻由「差 5%」降為「差 2.5%」（與 2.5% 級距一致）；新增每 5 分鐘定時重算觸發（`time_pattern`），感測器長時間沒更新時風量也會跟上；定時觸發時略過「冷氣同步開機」（避免過冷關機後被每 5 分鐘反覆開起），並補強 `manual_actor_detected` 對沒有 `to_state` 觸發的防呆。
- 新增 `05G緊急三擊維修暫停AI (V4.1.5)`＋helper `emergency_triple_press_pause`（開關＋2 小時計時）：維修時暫停「實體開關連點三下→緊急模式」（`05E緊急實體按鈕` 加了「暫停開關不是 on」條件：用範本判斷，開關失聯／不存在時仍可觸發緊急模式，不會因 helper 異常而讓緊急按鈕失效）。到期自動恢復並發 HA 通知；只暫停實體開關三擊，HomeKit／虛擬按鈕、地震預警、CO 自動觸發不受影響。開關已加入 HomeKit（HASS Bridge）與自動化管理面板。
- 修正 `800-開關系列-12E／12F`（UI 自動化，`automations.yaml`）：觸發實體被刪除（`to_state` 為空）時不再誤判為雙擊上樓／長按下樓（2026-10-11 11:09 Terncy 網關重連、裝置被移除，誤觸發上樓情境）；事件觸發（`terncy_pressed`）行為不變。
- 修正 `800-開關系列-12A／12B`（UI 自動化）：「四樓樓梯開關上2」（來源 `540f57fffe8239d3-02`）與「頂樓樓梯燈／四樓樓梯開關上1」（來源 `540f57fffe8239d3-01`）在 2026-10-11 被刪除並重新加入後，`terncy_pressed` 事件改帶新的 device_id（`058a0c17…`、`e259d035…`），原本只認舊 id（`ea7743a9…`、`ad6e414d…`）的單擊觸發失效；已補上新 id（保留舊 id）。05E／12E／12F 原本就已含新 id。
- 修正 `08-5C頂樓樓梯燈解除深夜亮度AI`（V4.1.5）：兩盞樓梯燈同時被打開（如手動上樓情境）時，頂樓樓梯燈會因旗標被先跑完的那一輪清掉而被跳過，卡在深夜亮度（60%／3000K）；改為等 3 秒後依「燈是否仍亮著且仍是深夜亮度／色溫」決定是否調回平常亮度，不再依賴共用旗標。
- 日誌整理（`configuration.yaml` V4.0，需重啟生效）：降級事件觸發器舊 device_id 警告、recorder 排除兩個超大屬性的版本感測器；`00-01` 週期重啟加 `continue_on_error`，檔內三支自動化統一升為 V4.0.0。
- 3D 智慧家庭儀表板日期列新增「日型標籤」：節日／週末紅色、工作日／補班日一般文字色，並顯示節日名稱（含補假、不放假的紀念日）。新增 `packages/v41_day_label.yaml`（`sensor.tw_day_label`：由 `sensor.tw_day_type_today`＋`calendar.tai_wan` 產生，`calendar.get_events` 再以 start<=今天<end 過濾）；前端為 `www/floorplan/v4/floorplan-v4-3d.js` 的 `floorplan-v4-sidebar`（直向 compact、橫向寬版與窄版皆有；標籤過期或感應器不存在時退回週六日＝週末）。前端 JS 已在 git（`www/floorplan/v4/floorplan-v4-3d.js`），本機副本在專案資料夾 `www/floorplan/v4/`。
- 修正 `情境與狀況氣氛燈AI`（`script.mood_alert` V4.1.5）：同一則通知被呼叫兩次時，第二次排隊到第一次跑完才開始，超過 8 秒去重窗口又跑一輪，且快照拍在第一輪收尾的暫時開燈期間，導致原本關著的客廳燈提醒後留成亮著（橘色）。改為結束時重寫去重時間，並在拍快照前等 `mood_alert_restore_off` 結束。
- 廚房「空氣品質危險」旗標（`packages/helper.yaml`，MQTT `kitchenmqtt_pm25_homekit_alarm`）條件：原 PM2.5>35 或 CO2>1000，改為 PM2.5>35 或 CO2>1500 或 TVOC>600 ppb（CO2 與 06 的「重要」門檻 1500 一致，並新增 TVOC）。1000～1500 ppm 只走 06 的「一般」CO2 警示。
- `packages/v41_env_alert.yaml`：`input_number.env_co2_l1`（CO2 一般門檻）預設 1000 → 1500 ppm。同時 `env_co2_l2`（重要）預設 1500 → 2000 ppm，三級為 1500／2000／2500，避免超過 1500 ppm 時一般與重要同時通知。
- `氣氛燈AI` 重要級（橘色）閃爍加長：每次亮 0.8→1.5 秒、熄滅 0.4→0.8 秒（2 次，約 4.6 秒；原約 2.4 秒），緊急級（紅色）不變。
- `06環境異常通知AI`（V4.1.5）：LINE 與 HA 通知內文帶上相關數值——空氣品質／甲醛／一氧化碳危險列出「超標項目」與「目前讀數」（CO2、PM2.5、TVOC、CO、甲醛、溫度、濕度），CO2／CO／溫度分級警示也加上「目前讀數」。
- 修正 `104-1車庫鐵門感應燈AI`（V4.1.5）：樓梯燈被別的自動化關掉時，「燈具關閉」觸發讓 restart 模式的本自動化重啟，中止鐵門關閉後的 5 分鐘關燈倒數，車庫主燈就一直亮著。移除該觸發，手動關燈冷卻拆成 `104-1B`（parallel）。
- 新增 `104-1C全員離家關閉車庫燈AI`（V4.1.5）：所有人都不在家（`binary_sensor.at_home_nobody_home` 持續 1 分鐘，HA 啟動後 2 分鐘也檢查一次）自動關閉車庫主燈與車庫樓梯燈。Jerry 一律只用 iPhone 16 判斷（`person.jerry` 與 `at_home_jerry*` 都只含 `device_tracker.iphone_16_jerry`）。 關燈後的 HA 通知由 `input_boolean.garage_away_off_ha_notify`（`packages/v41_garage_away.yaml`）控制，預設關閉。
- 修正 `104-4車庫回家通知系統AI`（V4.1.5）：人在車庫用遙控器開門時，車庫 Wi-Fi 在家判斷因手機換 AP 短暫掉線（約 30 秒），加上攝影機剛看到人不到 2 分鐘的寬限期，被誤報成「有人即將到家」。現在 Wi-Fi 判斷「剛掉線不到 2 分鐘」也視為車庫有人，不通知。
- `100A自動啟動到家早安情境AI`（V4.1.5）新增「有人回到家」觸發：家裡原本沒人、離家情境（`aqara_li_jia`）持續超過 10 分鐘，之後有人連上 Wi-Fi（`at_home_nobody_home` 由 on 變 off 持續 30 秒），自動啟動早安（早安時段）或到家情境；不受最早啟動時間與活動跡象限制，仍受總開關、影子模式、3 分鐘防重複與保全模式限制。Jerry 只用 iPhone 判斷。
- `100A自動啟動到家早安情境AI`（V4.1.5）：「最早啟動時間」由平日 05:30／假日 07:00 改為日出時間，新增 `input_boolean.auto_scene_earliest_use_sunrise`（預設 on，關閉退回固定時間）與日出後偏移 `input_number.auto_scene_earliest_sunrise_offset_min`（工作日，預設 30 分）、`input_number.auto_scene_earliest_sunrise_offset_holiday_min`（非工作日，預設 150 分＝2.5 小時），`packages/v41_auto_scene.yaml`。
- 刪除已被取代且停用的舊自動化（`automations.yaml`，2026-10-11 使用者確認新版運作正常）：`07空氣清淨機-自動啟動`、`07-1空氣清淨機自動通知`、`07-2空氣嚴重通知`、`07-3空氣嚴重通知 (嚴重)`、`07-4空氣清淨機-自動關閉`（由 `07空氣清淨機整合AI` 取代）、`100A自動啟動到家早安情境`（由 `100A自動啟動到家早安情境AI` 取代）；`configuration.yaml` 同步移除 07-2／07-3 的 Google 助理曝光設定（需重啟生效）。
- `106網關系統AI`（V4.1.5）：移除「自動化重載」觸發（避免每次重載都對實體網關重送警戒指令，2026-10-11 一天內已送出 29 次）；HA 啟動時若實體網關正在警報中／倒數中，不覆蓋它。實體網關 → 虛擬情境開關的回寫維持由 Apple 家庭處理。
- `21A_客廳電風扇整合控制AI`（V4.1.5）自動調速防抖：t_eff 在門檻上下 0.1°C 抖動會讓風量每 15～30 秒大小來回（30 小時 67 次變化）。改為遲滯（`input_number.living_room_fan_hysteresis_c`，預設 0.3°C）、自動調速最短間隔（`input_number.living_room_fan_min_interval_min`，預設 3 分；`timer.living_room_fan_speed_dwell`）、濕度加成改連續線性、曲線下限 20%。新增 `packages/v41_living_fan.yaml`。
- `22頂樓電風扇自動化AI`（V4.1.5）：上樓情境「介於門檻」那一段已設過風速時，步驟 5 略過，不再在同一次執行內重複送同一個風速。
- 決議（2026-10-11 使用者）：`auto_scene_enable` **不**公開給 HomeKit；「補班日資料來源自動化」**不做**（補班日維持手動填 `input_text.tw_makeup_workdays`）。`08-4客廳大門開啟自動開燈` 已用 `sun.sun` 低於地平線判斷（日落／日出），無需再改。
- 清理（2026-10-11 使用者核可）：移除 `packages/helper.yaml` 內 10 個已不使用的 `input_number.supply_batt_lowest_*`（00-2C V4.1.0 起改用 `supply_battery_lastvalid`／`supply_battery_stage`）。`input_text.at_home_*_trackers`（5 個）同日移除：`packages/helper.yaml` 的在家判斷樣板本來就優先讀 `person.*`，現在不再有 input_text 備援（Kenny／Elay／Jerry／Iris 讀 person 的 `device_trackers`，Kenny iPad 固定為 `device_tracker.ipad_pro_2024_kenny`）；移除前後 `binary_sensor.at_home_*`、`sensor.at_home_count`／`who_home` 狀態逐一比對相同。22 個未載入的整合依使用者決定保留。舊 07／07-1～07-4／舊 100A 已於 UI 自動化刪除。
- `08-5F頂樓自動上下樓情境AI`／`08-5G書房燈感應AI`／`08-5J頂樓動線推理AI`（V4.1.5）：手機追蹤實體改讀 `sensor.kenny_phone_tracker`（person.kenny 的 source），不再讀 `input_text.iphone_tracker_entity_kenny`；該輔助項目與 `00-4手機追蹤比對AI`、`binary_sensor.v41_phone_ap_match`、`input_number.v41_phone_match_ok/bad` 一併移除（切換完成）。
- `03苗栗天氣告知系統AI`（V4.1.5）：災害訊息依內容分級。重要類（竹南有影響：竹南的淹水警戒／停水停電／洩洪；縣市層級且列有苗栗的颱風警報、豪雨特報、橙紅燈號）→ LINE／HA 用「一般」級、並廣播；緊急類（疏散、土石流、國家級警報）→「重要」級；info（鄰近鄉鎮、大雨預報、解除、演練演習）只發 HA 資訊通知；地震不處理（由 02 負責）；海嘯仍由 03 處理（內文有苗栗→緊急類，解除或沒寫苗栗→info）。新增 `packages/v41_disaster_notify.yaml` 四個開關：`notify_line_disaster_important_enable`／`notify_line_disaster_emergency_enable`（LINE，已公開給 HomeKit『HASS Bridge』）、`notify_ha_disaster_important_enable`／`notify_ha_disaster_emergency_enable`（HA）。另有廣播開關 `announce_disaster_important_enable`／`announce_disaster_emergency_enable`（不公開給 HomeKit；關閉後該類不廣播、早晨補報也停）。自動化管理面板新增「災害訊息廣播開關」小組。歷史 255 則訊息測試：重要 2、緊急 0、info 23、不通知 230。此自動化目前為**關閉**狀態（2026-08-26 起）。
- `104-4車庫回家通知系統AI`（V4.1.5）：車庫攝影機偵測到人（不論多久）或 60 秒內才剛變沒人時不通知，修正人走進車庫再開鐵門的誤報；Wi-Fi 判斷規則不變。
- `100A自動啟動到家早安情境AI`（V4.1.5）：併入「105門鎖自動判斷到家」（新增觸發 `lock_home`：門鎖解除離家模式 → 依時段啟動早安／到家，不受最早時間與活動跡象限制，但受總開關、3 分鐘防重複、保全模式限制）；舊 105（UI 自動化 id 1691155847932）已刪除。
- 新增 `21B夏季模式自動判斷AI`（V4.1.5）：依今日預報體感最高（weather 每小時預報 feels_like_temperature）與今日實測體感最高（戶外體感感測器）自動開關 `input_boolean.summer_mode`；分數 ≥ 28.5°C 開、< 26°C 關、之間維持現狀，06:30–18:00 每 30 分鐘判斷。人工切換（context 無 parent_id）會記 `input_datetime.summer_manual_date`，當天不再自動調整，隔天恢復。新增 `packages/v41_summer_auto.yaml`：`summer_auto_enable`（總開關）、`summer_auto_on_feels_c`／`summer_auto_off_feels_c`（門檻）、`summer_manual_date`、`summer_auto_today_flag`／`summer_auto_last`（內部）。
- 根目錄 `automations.yaml` 與 `configuration.yaml` 納入 git（2026-10-11）：`configuration.yaml` 的小米風扇 token、LINE 權杖與 client id 改為 `!secret`（值在 `secrets.yaml`，不進 git）。
- Helper 套件版本由 `V4.1.0` 增加獨立 package `v41_emergency_pause.yaml`（`helper.yaml` 本身未異動）。

### Known Bugs／待實體驗證（V4.1.5）
- `03苗栗天氣告知系統AI` 目前為關閉狀態（2026-08-26 起）；分級只以歷史 255 則與模擬訊息驗證，尚無真實災害訊息實測。
- 尚未實體驗證：`05G` 三擊維修暫停（開／關）、`100A` 的 `arrive`（離家超過 10 分鐘後連上 Wi-Fi）與 `lock_home`（門鎖解除離家模式）觸發、`104-4` 車庫攝影機偵測、`21B` 手動切換偵測與隔天恢復。
- 根目錄 `automations.yaml`（UI 自動化）與 `configuration.yaml` 不在 git 內；本版 12A／12B／12E／12F／05E 修補與 105 刪除只存在主機與本機備份（`V4.1.5/automations.yaml`）。

### Next Version（V4.2 候選）
- `104-2車牌辨識AI優化`；智慧家庭 Home UI 4.0 優化（UI 4.0-beta 8）。
- `input_text.at_home_*_trackers` 仍用於在家判斷，評估改讀 `person.*` 後再清除；22 個未載入的整合保留。

## 本次調整（V4.1 - 2026-10-10：八項功能、Terncy 無線開關、樓梯燈／車庫／感應燈與頂樓優化）

### 新功能（八項規劃）
- **耗材通知整合與修復**（`00-2C` V4.1.0）：濾網壽命只通知一次（≤10% 通知、回升 >50% 才重置）；電池改階段式（≤35% 準備備品、≤20% 請更換、≤10% 緊急，各階段一次，≤20% 每 7 天再提醒）；電量讀不到時用 7 天內最後有效值，7 天都沒有就排除（只通知一次）；一鍵測試與 15 天摘要改為真實報告。
- **緊急模式快照還原**：`05A` 啟動時先存快照（`script.emergency_snapshot_save`，38 個受影響設備），解除網關警報時（`106C` V4.2.0，`emergency_restore_route`）可還原燈／開關／風扇／插座／頂樓空調、警報開關關閉；鐵門「無人車才自動關回」，二樓門鎖只通知；地震預警與 CO 自動觸發排除狀況後也可還原；`05F` 管理 2 小時到期。
- **手機追蹤 person 化**：`helper.yaml` 的 `at_home_*` 範本優先讀 `person.*`；新增 `sensor.kenny_phone_ap_mac`，頂樓 `08-5F`／`5G`／`5J` 改讀它（V4.0.4／V4.1.3／V4.1.1）；`00-4` 比對新舊判斷；`00-3` 每週巡檢 unavailable＋restored 失效實體（清理 71 個舊空殼）。
- **日出日落時間窗**：`binary_sensor.scene_morning_window`（日出前 30 分～日落前 60 分，上下限 05:00／18:30，皆可調）；`00-2J`、`105`、`800-0／0B／13`、`106C`、新 `100A` 共用，功能開關 `scene_window_use_sun`（預設開）。
- **假日判斷**：`sensor.tw_day_type_today／tomorrow`、`script.tw_day_type`（Workday 整合只用 `government` 類別；補班日填 `input_text.tw_makeup_workdays`）。
- **100A 自動到家／早安 AI 版**（V4.1.0）：具名觸發、依平日／假日最早時間、HomeKit 總開關；影子模式（`auto_scene_shadow`）預設已關＝實際運作，舊 100A 已停用（未刪除）。
- **熟睡起床搭配國定假日**（`08-5H` V4.3.0）：03:00／05:00、09:30／10:30 改為可調 helper，功能開關 `sleep_holiday_aware`（預設開）。
- **環境異常通知**（`06` V4.1.0）：CO2／CO／廚房溫度三級、危險感測器、攝影機 CO 警報、感測器失聯；CO 危險自動觸發緊急模式已實際接線（`env_alert_co_dry_run` 預設關，可打開改回乾跑）。
- **空氣清淨機整合**（`07` V4.1.0）：單一自動化取代舊 07 系列；影子模式（`air_ai_shadow`）預設已關＝實際運作，舊 07 系列已停用（未刪除）；手動關機尊重 30 分鐘。

### 開關與樓梯燈
- **Terncy 無線開關**（`08-9` V4.1.1）：37 鍵無線模式、單擊切換；雙擊／三擊事件對照表。
- **樓梯燈定時關燈**（`800-14` 系列 V4.1.2／14D V4.1.3）：單擊 3 分鐘後關、雙擊常開；四樓樓梯燈若頂樓感應正在使用，交給頂樓感應與頂樓樓梯燈一起關（`stage_scene` V4.0.1）。
- **車庫主燈**：按鈕 5 秒防小燈（`800-15` V4.1.1）、感應冷卻與保護（`104-1` V4.1.1）、回家通知提早廣播（`104-4`）。
- **廚房／廁所感應燈**：重新偵測與縮短關燈延遲（`08-8A` V3.3.0／`08-8B` V3.1.0），廚房不用毫米波開燈。

### 頂樓
- 熟睡鎖統一只看 `sleep_silent_active`、動態解鎖（`08-5H`）；動線仲裁與書房燈防呆（`08-5J`／`08-5G`）；樓梯燈使用權與手動保持（`08-5K`）。
- `topfloor_publish_path` 動線事件仲裁（`頂樓感應AI` V4.1.0）。

### 其他
- `手動廣播AI`／`手動通知AI`、`00-2J` 氣氛燈、`05B` 復原說明、`22` 頂樓電風扇、自動化管理面板分類更新、3D 平面圖調整。

### 已修正的問題
- `max(0.5)` 過濾器不能用在單一數值（`800-15`、`104-1`、`800-10`：燈關閉 5 秒內再按／再感應時報錯、燈沒開）。
- 自動化 `reload` 會中斷正在等待中的執行（08-5F 下樓 120 秒等待）——操作面提醒，非程式錯誤。

### Known Bugs／待實體驗證
- 新 `07空氣清淨機整合AI`、`100A自動啟動到家早安情境AI` 已實際運作（使用者核准，未經長時間影子觀察）；舊 07／07-1～07-4／舊 100A 已停用但未刪除，異常時重新打開舊的並把 `air_ai_shadow`／`auto_scene_shadow` 開回即可退回。
- CO 危險自動緊急模式（`env_alert_co_dry_run` 已關）尚未實測：會開全屋燈、車庫鐵門、響網關警報、解二樓門鎖；誤觸時可按解除網關警報還原。
- 緊急模式快照還原端對端（HomeKit 觸發 → 解除網關警報）尚未實測；`sleep_holiday_aware` 預設開，補班週六需手動填 `tw_makeup_workdays`。
- `fan.set_preset_mode: Favorite`（空氣非常嚴重加強運作）需實機確認。

### Next Version（V4.2 候選）
- 觀察穩定後：刪除已停用的舊 `07`、`07-1～07-4`、舊 `100A`；刪除 `supply_batt_lowest_*`（9 個）與 `input_text.at_home_*_trackers`、`iphone_tracker_entity_kenny`。
- `08-4客廳大門開啟自動開燈` 改用日落／日出；`auto_scene_enable` 公開給 HomeKit。
- 補班日資料來源（目前手動填）。

## 本次調整（V4.0 - 2026-10-08 AI 4.0 正式版：通知分級、氣氛燈與廣播、頂樓動線重構、車庫回家通知、LINE Bot 輪替）

### 1. 通知與廣播全面統一
- `script.notify_dispatch`：四級（資訊／一般／重要／緊急）HA 通知＋LINE 扁平卡片，內文自動配主題圖示、每句換行；HA 通知分級開關（`notify_ha_*`）；資訊級只發 HA。
- `script.announce`：一律播放「提示音＋語音」合成單一音檔（`mk_announce.py`，同文字快取；`00-2L` 開機與每日 03:30 預先合成 530 句），合成失敗重試 3 次、仍失敗只播提示音並發 HA 資訊通知；可同時指定多個喇叭；新增 `announce_volume_guard`（HomePod 逾時中斷時等廣播結束後還原音量）。
- 地震預警（`eq99`）：廣播最先、不阻塞，開頭廣播與氣氛燈同時開始；第一段（預估秒數）播完 0.1 秒內接第二段緊急音效＋避難提示並再閃一次氣氛燈（原本固定等 25 秒會空 11 秒）。

### 2. 情境與氣氛燈
- 氣氛燈提醒（`mood_alert`）：緊急級各區同時閃、機台 LED（UniFi AP）同步；燈況記憶（`00-2H`）依「色溫＋亮度」還原，還原後確認回到色溫模式（最多重送 3 次）；排隊上限 10；去重窗口 8 秒。
- 情境氣氛燈（`00-2J`）：離家紅／晚安暖橘／早安與到家綠；漸進情境、情境檢查、情境廣播。
- 夜燈情境（08-5D）：確認關閉後單純開燈，讓床頭燈回到最暗夜燈模式。

### 3. 頂樓動線重構（08-5C / 5F / 5G / 5J / 5K）
- 新增 08-5J 動線推理（攝影機、跨線 Webhook、PIR 左（房間）／右（書房）、AP 多證據推理）、08-5K 燈具使用權（手動開燈 5 分鐘保護）。
- 08-5G 書房燈：開燈與無人檢查看右側（書房）PIR；「書房回房間」（左側觸發＋剛上樓或右側先觸發）關書房燈並依延遲關樓梯燈；不再被「進房間」推理事件誤關。
- 08-5C 樓梯燈：深夜（熟睡鎖）60%／3000K，起床後第一次開燈用「燈況記憶」的平常亮度／色溫；牆壁開關、實體按鈕（12A／12B／12D）一致；走出房間（左→右）開燈。
- 08-5F 新增下樓補判；11B 長按暫停頂樓感應（書房燈閃 1／2 下）。

### 4. 其他新增與修復
- 新增 104-4 車庫回家通知系統（遙控開鐵門時廣播＋氣氛燈，不發 LINE）。
- LINE Bot：Auto 沿用主用 Bot（sticky）；「即將切換」預告同一個 Bot 只報一次；切換通知加 30 秒穩定與「不等於主用 Bot」防誤報。
- 107 Tesla：拔槍重插（狀態經 unknown）補發開始充電通知；插槍後「充電完成」但沒充電的 00:02 提醒；充飽不拔槍不再誤報 6 小時未充電。
- 修復：08-6 離家保全（Iris 手機實體已失效）改用 `person.*`；21A 風扇備援感測器與 `t_eff` 判斷；13 魔方、00-2C 魔方電量失效實體；`sensor.lights_on`；門鎖日耗電率 `doorlock_battery_drop_mean_7d` 重建（00-2P 每日紀錄）。
- 新增 00-2M 每晚 03:40 實體引用檢查（`scripts/check_entities.py`）；資料庫保留 45 天並排除雜訊實體；自動化管理側邊欄面板與整合儀表板「智慧家庭」。
- 移出載入範圍：測試觸發機制 00-2G 與 `test_trigger` package（保存在 `deprecated_automations_backup/Archived_20261008/` 與 `scripts/dev_tools/`）、106-1、00-2廣播系統測試、00-3 手動清理空間。

## 本次調整（V4.0-beta1 追加 - 2026-10-05：通知分級、統一廣播、漸進情境、LINE Bot 輪替修正）

| 項目 | 檔案 | 版本 | 說明 |
|---|---|---|---|
| LINE Bot 輪替 | `packages/linebot.yaml` | V1.12 | 沿用主用 Bot（跨月不回 Bot1）、切換預告以 196 門檻計算；`send_line_to_user` 自動將「標題+等級+內文」多泡泡合併為 1 則扁平 Flex 卡片（節省額度） |
| LINE 額度監控 | `00-2BLINE推播AI` | V3.5 | 改用 `notify_dispatch`；切換/低額度=重要、用盡=緊急、例行摘要=資訊 |
| 統一通知 | `Scripts/統一通知AI.yaml` | V1.0.2 | `script.notify_dispatch`（HA 通知+LINE Flex，資訊級不發 LINE）、`script.announce`（提示音播完才播 TTS，播完恢復音量；提示音改本機 media-source，保底秒數=實際長度） |
| 漸進情境 | `Scripts/漸進情境AI.yaml` | V1.0.2 | 依按鈕位置由近到遠分環開/關；離家由開關觸發時樓梯燈豁免，3 分鐘後關閉 |
| 情境檢查 | `Scripts/情境檢查AI.yaml` | V1.0.2 | 晚安/離家/早安/到家執行後檢查、補救；補救成功=資訊（僅 HA），失敗=重要（HA+LINE） |
| 通知開關初始化 | `00-2D通知開關初始化AI` | V1.0.0 | HA 通知資訊/一般/重要開關首次一次性開啟，之後由使用者調整 |
| 通知測試 | `00-2E通知測試AI` | V1.0.0 | 4 個測試按鈕 |
| 等級套用 | 約 20 個 `*AI.yaml` + `automations.yaml` | — | `notify.persistent_notification` → `script.notify_dispatch`（line:false，保留原 LINE 發送）；45 組「提示音+固定延遲+TTS」→ `script.announce` |
| 廣播群組 | HA 設定 | — | 廣播群組All→緊急、通知→重要，新增「廣播群組一般」（客廳 HomePod+車庫攝影機）；實體 ID 不變 |
| Helper | `packages/helper.yaml` | V4.0-beta1 | 新增 `notify_ha_*_enable`、`notify_test_*`、`line_bot_sticky`、`scene_origin_device` 等 |

### V4.0-beta1 追加：情境與狀況氣氛燈AI（2026-10-05）
| 項目 | 檔案 | 版本 | 說明 |
|---|---|---|---|
| 氣氛燈提醒 | `Scripts/氣氛燈AI.yaml` | V1.0.1 | `script.mood_alert`：LINE（重要/緊急）或廣播送出時，客廳小燈→餐廳燈2→三樓樓梯燈→四樓→頂樓樓梯燈依序閃爍（重要=琥珀橘約 4 秒、緊急=紅色約 6 秒），完成後還原；離家模式不提醒、晚安/夜燈情境只有緊急提醒、緊急模式 05A/05B/05E 執行中或 3 分鐘內略過；25 秒內與 LINE/廣播同事件去重 |
| 呼叫點 | `統一通知AI.yaml` V1.0.4、`packages/linebot.yaml` V1.13 | — | `notify_dispatch`、`announce`、舊格式 LINE 送出後觸發 `mood_alert` |
| Helper | `packages/helper.yaml` | V4.0-beta1 | `mood_alert_enable/_important_enable/_emergency_enable`（首次由 00-2D 一次性開啟）、`mood_alert_active`、`mood_alert_last` |

### V4.0-beta1 追加：情境執行廣播（2026-10-05）
| 項目 | 檔案 | 版本 | 說明 |
|---|---|---|---|
| 情境廣播 | `Scripts/情境檢查AI.yaml` | V1.0.4 | 新增 `script.scene_announce`：離家/晚安/早安/到家執行時用「一般」廣播播報；離家、晚安僅手動（實體開關）觸發時播，早安、到家一律播；60 秒內同情境不重複；`scene_verify` 開頭呼叫 |
| Helper | `packages/helper.yaml` | V4.0-beta1 | `scene_announce_enable`（首次由 00-2D 一次性開啟）、`scene_announce_last`、`scene_announce_init` |
| 其他 | 漸進情境 V1.0.3、`07*` 空氣清淨機自動化 | — | 早安/到家不再開空氣清淨機；07/07-1/07-2/07-3 需有人在家（aqara_zai_jia）才啟動 |

### AI 4.0 版號統一（2026-10-05）
V4.0-beta1 期間新增或修改過的自動化與腳本（00-2A/2B/2C/2D/2E、03、05B、08-5A/5F/6、100B、100C1/2、104-2/3、105、106、107、21A/21B、22、地震預警、統一通知、漸進情境、情境檢查、氣氛燈）版本統一為 `V4.0.0`；未異動的檔案維持原版號。00-2A 於 18:00 偵測到版本差異時會自動推播更新通知（依 SOP 步驟 8 不手動設基準）。

## 本次調整（V3.6.9 - 2026-09-20 AI 4.0 測試導入、LINE Bot 額度判定與去重修復、Tesla 充電樁充電完成通知邏輯修復、車庫主燈與樓梯燈自動關閉修復）
- **AI 4.0 測試導入（全新 Agent 與次世代模型完整接管，全面 AI 化更新）**：
  - **全新 Agent 完整接管**：正式導入全新世代 AI Agent 與深度思考模型，全面接管智慧家庭系統架構維護、YAML 自動化開發、版本重構與 HA 核心系統運維。
  - **全自動化 GitOps 升級流程**：實現需求分析、即時代碼調整、Pre-flight 語法檢驗、主機熱重載、實體驗證門禁至自動提交 PR 與 GitHub Release 發布之全流程全面 AI 化。
  - **SOP 步驟 8 確立**：建立 GitHub Release 發布後自動更新「更新推播系統」儀表板實體之標準作業程序（保留版本差異供 00-2A 自動推播）。
- **104-1車庫鐵門感應燈AI 升級至 `V3.4.0`**：
  - **解鎖自動關燈死結**：移除 `mode: restart` 下之「燈具必須為 off」條件限制，允許持續活動時平滑延長 5 分鐘關燈計時，徹底消除開燈等待期間被後續人車偵測中斷導致燈具永遠常亮的致命問題。
  - **納入手動開燈守護**：新增 `light_turned_on` 觸發監聽（`switch.che_ku_zhu_deng` / `switch.lou_ti_deng` 變為 on），雙擊開關、HomeKit 或 App 手動開燈後，若無人車活動滿 5 分鐘亦自動安全關閉。
  - **多重感測融合防抖**：整合 UniFi 人員/車輛偵測與 Scrypted 動作偵測，防止單一 Protect 感測器連線抖動導致關閉失敗。
  - **完善鐵門防呆**：鐵門開啟期間強制維持亮燈，待鐵門關閉後始開始 5 分鐘無人倒數關燈。
  - **保留手動關燈冷卻機制**：手動關燈後 30 秒內不被再次感應點亮（`timer.garage_light_manual_off_cooldown`）。
- **00-2BLINE推播AI 升級至 `V3.4`**：
  - 依據需求將配額完全用盡之計算門檻調整為低於 5 則（因單次推播可能包含多則訊息或需預留安全緩衝，低於 5 即視為完全用盡）。
  - 新增狀態鎖檢查（`already_notified`）：當所有 Bot 配額低於 5 則或 Bot 0 歸零時，僅推播 1 次最終告警通知，避免頻繁發送訊息時持續重複洗版。
  - 新增每月 1 日零點自動復位狀態鎖（`input_boolean.line_bot_quota_exhausted_notified`）。
- **packages/linebot.yaml 升級至 `V1.10`**：
  - `switch_limit` 門檻由 196 調整為 195。
  - `sensor.line_bot_rotation_target`：自動輪播判斷門檻統一要求 `r >= 5`，若剩餘額度低於 5 則自動切換至下一個可用 Bot。
  - `sensor.line_bot_in_use`：當所有 Bot 剩餘額度皆小於 5 則時，明確標示為「無可用 Bot」。
  - `script.send_line_to_user`：在無可用 Token（配額皆已不足 5 則）之 fallback 分支導入 `input_boolean.line_bot_quota_exhausted_notified` 檢查，僅在首次耗盡時發送 1 次緊急警告並上鎖，後續請求僅記錄 log，不再重複推送 LINE 告警。
- **packages/helper.yaml 升級至 `V3.23.0`**：
  - 新增 `input_boolean.line_bot_quota_exhausted_notified`（LINE_Bot額度耗盡已通知狀態）。
- **107Tesla充電器狀態與通知AI 升級至 `V3.4.0`**：
  - **狀態分類修正**：將 `charging_finished` / `charging finished` 自「斷開連接（`disconnected_states`）」移出，建立獨立之 `finished_states`。解決先前狀態由 `charging_finished` 轉入 `waiting_car` 時，被誤判為剛插槍而提早將 `tesla_charger_session_charged` 旗標歸零的 bug。
  - **杜絕重複發送與保護**：在完成通知發送序列最前段加入 `input_boolean.turn_off` 立即重置 `input_boolean.tesla_charger_session_charged`，杜絕充電完成後車輛預熱（Preconditioning）微幅充電或拔槍時引發的二次/重複完成通知。
  - **車輛名稱精準識別**：完成時優先依據充電中（`charging` $
ightarrow$ Tesla、`charging_reduced` $
ightarrow$ Luxgen）之歷史狀態精確識別車輛名稱。

## 本次調整（V3.6.7 Patch (a) - 2026-08-16 Terncy 2026.8+ 底層事件重構、三擊全域統一、樓梯燈優化、晚安情境防誤判修復與設定檔升級）
- **Terncy 開關觸發條件轉換**：將 `automations.yaml` 中 25 支 Terncy 開關自動化及 `08-8B廁所感應燈AI.yaml` 之觸發器從舊版 `platform: device / trigger: device` 遷移為底層 `trigger: event`（`event_type: terncy_pressed` / `event_type: terncy_long_press`），完整保留原始 `device_id`。
- **單擊長按防呆條件**：針對所有單擊自動化導入 500ms 長按防呆模板，避免開關長按放開瞬間誤觸單擊。
- **雙網關消抖與執行模式規範**：所有 Terncy 自動化統一設定 `mode: single` / `mode: restart`、`max_exceeded: silent`，並於單擊動作末端加入 `delay: '00:00:00.5'`，徹底杜絕雙網關 50~100ms 連續重複觸發。
- **三擊緊急模式全域統一**：
  - 全家所有 35 個小燕開關 + 1 個小米無線開關三擊 100% 統一綁定為 `05E緊急實體按鈕`（觸發緊急模式）。
  - 刪除衝突之舊版三擊功能：`800-開關系列-7`（客廳燈部分關）、`800-開關系列-3`（廚房三擊風扇）。
  - 樓梯燈手勢全面優化：
    - **`800-開關系列-9B`（單擊定時全開）**：1F~4F 樓梯開關單擊點亮全棟樓梯燈 3 分鐘，導入 `mode: restart` 解決 3 分鐘內手動關閉後再次單擊無反應問題。
    - **`800-開關系列-9A`（雙擊常開）**：1F~4F 樓梯開關雙擊點亮全棟樓梯燈並維持常開（不計時關閉）。
    - **`800-開關系列-9C`（長按全關）**：各樓層樓梯開關長按立即全關全棟樓梯燈。
    - **`800-開關系列-12C`（頂樓四樓樓梯燈校正）**：將實體開關按鍵校正移出，改由虛擬實體按鈕（`input_button.ding_lou_si_lou_lou_ti_deng_xiao_zheng`）觸發。
- **實體清理**：移除全系統自動化中已停用之舊四樓樓梯燈開關實體 `switch.si_lou_lou_ti_deng`（已由 Yeelight 彩光燈泡 `light.yeelink_color5_0fb7_light` 接管），消除實體遺失/不可用警告。
- **Helper 套件升級至 `V3.22.0`**：新增 `input_button.ding_lou_si_lou_lou_ti_deng_xiao_zheng`（頂樓四樓樓梯燈校正虛擬按鈕）。
- **YAML 語法淨化**：全面清理 `metadata: {}`、空的 `data: {}` 及殘留之 `enabled: false` 動作區塊。
- **08-8B 廁所感應燈AI 升級至 `V3.0.3`**：長按觸發同步升級為 `terncy_long_press` 底層事件。
- **08-5C 頂樓樓梯感應燈AI 升級至 `V3.4.6`**：為自動關閉流程（`ai_08_5c_topfloor_stairs_motion_light_auto_off`）加入 `max_exceeded: silent`，抑制 22 秒動態監聽期間重複感應觸發時產生之 Already running 警告日誌。
- **configuration.yaml 升級至 `V3.5`（HA 2026.8+ HTTP 整合 UI 遷移與日誌淨化）**：
  - 頂部加入標準化更新紀錄區塊（比照 `helper.yaml` 格式規範）。
  - 已自 `configuration.yaml` 移除已棄用的 `http:` 區塊（消除 2027.2.0 失效警告）。
  - 新增 logger 過濾規則屏蔽 Hisense TV 待機連線日誌與 HACS 自訂整合過渡期棄用警告。
- **新增開關指令總表與標準作業程序**：
  - 建立 **`SwitchCommand.md`**：記錄全戶開關分類對照總表、HA 2026.8+ 標準程式碼架構與 YAML 範本；客廳主開關下1（`e35da296`）歸類客廳區域（單擊自訂保留，雙擊 9B 樓梯燈 3 分鐘）。
  - 新增 **`SOP-12：開關類自動化更新與維護規範`**：明定開關手勢排查、三擊專用、防呆消抖與雙表同步。
  - 新增 **`SOP-13：Configuration 主設定檔更新與相容性規範`**：明定頂部更新紀錄格式（比照 helper.yaml）、版本進位、相容性檢測、Include 保護與三方同步。

- **08-7A 自動晚安情境AI 升級至 `V3.4.0 (Patch a)`**：新增「三樓臥室 10 分鐘觀察期」機制，並修復取消判斷範圍（解決同行家人已在「離家」時被誤當作取消條件之 bug）。離家/離家確認中之取消條件精準限縮於被觀察之三樓最後變動者（latest_member）；全域即時取消僅限活動區（客廳/廚房/廁所/車庫），其他家人保持離家狀態正常放行。

## 本次調整（2026-08-09 充電通知修復、晩安防護、廣播音量、車庫與廚房燈控、耗材擴充）
- `107Tesla充電器狀態與通知AI` 功能版升級至 `V3.3.0`：修復 Luxgen→Tesla（或 Tesla→Luxgen）換車充電時無開始通知與用時計算錯誤問題。charge_start 條件新增放行不同車型互轉情境，換車後自動更新起始時間並發送新車開始通知。
- `08-7A自動晩安情境AI` 功能版升級至 `V3.3.0`：Conditions 改用白名單機制（指定安全位置清單），排除車庫/客廣/廚房/廁所/離家確認中等活動狀態後才放行；Actions 安全門改為遙歷全體成員（Kenny/Elay/Jerry/Iris），任一人在活動區即取消晩安。
- `105大門門鈴自動化AI` 功能版升級至 `V3.1.0`：廣播前儲存 HomePod 原始音量，TTS 播音後以 `wait_template`（timeout 12s + `continue_on_timeout: true`）確認播畢後恢復，遵循新增 SOP-11 廣播音量恢復規範。
- `00-2C耗材更換AI通知` 修補版升級至 `V3.1.4`：將廚房無線開關（`sensor.0x00158d00023cd3dc_battery`）電量納入監控，新增至 battery_change 觸發、device_name 對照、lowest_helper 對照與一鍵測試報告。
- `packages/helper.yaml` 修補版升級至 `V3.21.1`：更新 `supply_batt_lowest_23cd3dc` 的 friendly_name 為「耗材電量最低値_廚房無線開關」。
- 新增 **SOP-11 廣播系統音量恢復規範**：明定所有涉及 TTS 廣播的自動化必須帶備播前儲存音量、播完監聽及恢復密封模式。
- LINE 通知檢查：本次未新增任何直接 `notify.line_*` 呼叫，符合 SOP-10。

- `104-1車庫鐵門感應燈AI` 功能版升級至 `V3.3`：手動關閉冷卻時間改為讀取 `input_number.garage_light_cooldown_sec`（預設 30 秒，可自行調整 0～600 秒），取代原固定 5 分鐘冷卻。
- `08-8A廚房感應燈AI` 修補版升級至 `V3.2`：移除手動按鍵後 60 秒防誤觸冷卻判斷，感應燈偵測到動作時直接開燈。
- `packages/helper.yaml` 功能版升級至 `V3.21.0`：新增 `input_number.garage_light_cooldown_sec`（車庫燈手動關閉冷卻秒數），提供 UI 可調整冷卻時間；並將 `timer.garage_light_manual_off_cooldown` 預設 duration 同步更新為 30 秒。
- LINE 通知檢查：本次未新增或修改任何 LINE 發送路徑，未出現直接 `notify.line_*` 呼叫，符合 SOP-10。

## 本次調整（2026-08-02 修復系統與網路警告與門鈴耗材擴充）
- `configuration.yaml`：新增 `logger` 區塊屏蔽 `homeassistant.loader`（第三方整合警告）、`py.warnings` 與 `urllib3.connectionpool`（SSL/InsecureRequest 警告）。
- `packages/helper.yaml` 修補版升級至 `V3.20.0`：新增 `binary_sensor.da_men_men_ling` 門鈴橋接實體與 `input_number.supply_batt_lowest_doorbell_2f` 門鈴電量 Lowest Helper；新增大門門鈴分級 LINE 開關（`input_boolean.notify_line_doorbell_enable`）與自訂通知標題（`input_text.notif_title_doorbell`），並修復 5 處 `| list | first` 在追蹤器清單為空時引發的 TemplateVariableWarning 警告。
- `00-2C耗材更換AI通知` 修補版升級至 `V3.1.3`：納入二樓門口電鈴（`sensor.0x00158d0002419b84_battery`）電量監控與 Lowest Helper 機制，避免 Unknown/抖動問題。
- `00-01系統回應穩定自動化AI` 修補版升級至 `V3.0.3`：UnifiProtect 看門狗 `mode` 由 `single` 改為 `restart`。
- `106網關系統AI` 修補版升級至 `V3.3.1`：`mode` 由 `single` 改為 `restart`，避免 input_boolean 快速切換時丟棄觸發。
- `100B自動離家AI` 修補版升級至 `V3.4.1`：替換 3 處 4-byte Emoji（🪧、🏠）為 ASCII 文字符號，解決 LINE 推送時 JSON 序列化失敗（surrogates not allowed）警告。
- 新增 `105大門門鈴自動化AI (V3.0)`：整合小米門鈴按壓單擊觸發與 HomeKit 橋接感應，連動 HomePod 音量調整廣播與 TTS 音效，並遵循 SOP-10 可靠性規範發送 LINE 智能推播。
- `configuration/automations.yaml`：`07-4空氣清淨機-自動關閉` 改為 `mode: restart` 並加入 5 秒防抖；`102離家情境` 對含有已離線樓梯燈實體的 turn_off action 加上 `continue_on_error: true`。

## 本次調整（2026-08-01 情境防衝突與多項修補）
- `08-8B廁所感應燈AI` 修補版升級至 `V3.0.2`：長按改為 Terncy device trigger。
- `08-7A自動晚安情境AI` 功能版升級至 `V3.2.0`：加入 Kenny/Elay/Jerry/Iris 位置聯合判斷。
- `107Tesla充電器狀態與通知AI` 修補版升級至 `V3.2.4`：移除不存在的功率實體，改以 `sensor.tesla_wall_connector_total_power` 上升判斷本次插槍已有充電，拔槍時重置旗標，支援同日多車連續通知。
- `00-2C耗材更換AI通知` 修補版升級至 `V3.1.2`：客廳魔方電量改接 `sensor.living_room_cube_battery`，0/unknown/unavailable 不覆寫上次有效值。
- Helper 套件功能版升級至 `V3.18.0`：新增 HomeKit 情境輔助開關與離家/晚安 3 分鐘防衝突時間戳。
- `automation.yaml` 修正客廳魔方 shock 動作（同時讀取 sensor/binary_sensor 與 action/action_type 屬性）、100A 3 分鐘冷卻、100/101/102/103 情境 8 秒自我檢查（狀態不符才重送）與 HomeKit 按鈕自動復位。
- LINE 通知檢查：本次既有 Tesla/耗材 LINE 路徑仍使用 `script.send_line_to_user`，含分級開關、額外開關與 user_id 防呆；新增 HomeKit/情境防衝突未新增 LINE 路徑，符合 SOP-10。

## 本次調整（2026-06-14 夏季風扇、Location 與耗材/燈控 AI 擴充、Kenny iPad AtHome 修補）
- `00-2C耗材更換AI通知` 修補版升級至 `V3.1.1`：耗材電量 state trigger 加入 10 秒防抖；客廳 Aqara 魔方與其他裝置測試報告遇 `unknown/unavailable` 時沿用對應最低電量 helper 的上次有效值，避免偶發 Unknown 造成誤判。
- Helper 套件修補版升級至 `V3.17.2`：修正耗材電量 helper 顯示名稱，`08b95f06b466` 改為「廚房小米人體傳感器」、`28d1273d78cf` 改為「廁所夜燈」、廁所人體感應器改為「二樓廁所人體感應器」。
- LINE 通知檢查：耗材濾芯、耗材電量與一鍵測試 LINE 路徑均使用 `script.send_line_to_user`，並檢查一般分級開關、耗材額外開關與 `user_id` 有效性；任一檢查不通過會建立 persistent notification 記錄未發送原因，符合 SOP-10。

- Helper 套件版本維持 `V3.17.1` 不升版：新增/確認 `input_text.at_home_kenny_ipad_trackers` 與 `binary_sensor.at_home_kenny_ipad`，讓 Kenny iPad 與 `binary_sensor.at_home_kenny` 使用不同追蹤清單並完全獨立。
- `sensor.at_home_kenny_ipad_ap_mac` 與 `sensor.at_home_kenny_ipad_location` 僅讀取 Kenny iPad 獨立追蹤清單，預設回退 `device_tracker.ipad_pro_2024_kenny`；不讀取 `input_text.at_home_kenny_trackers` 或 `binary_sensor.at_home_kenny`。
- 確認 iPad helper 僅供額外 double check 使用，未納入 `binary_sensor.at_home_nobody_home`、`binary_sensor.at_home_anyone_home`、`binary_sensor.er_lou_ping_mu_gan_ying_zong_he_pan_duan`、`binary_sensor.che_ku_wa_fi_gan_ying_zong_he_pan_duan` 等在家/占用判斷。
- LINE 通知檢查：本次只新增 helper 與調整 template 來源，未新增或修改 persistent notification / LINE 發送路徑；未出現新的 `notify.line_*` 或直接 LINE 呼叫，符合 SOP-10。

- Helper 套件修補版升級至 `V3.17.1`：移除 `input_select.lpr_last_plate` 重複 `EBH8030` 選項，避免 Home Assistant input_select 驗證失敗；同時移除 Kenny iPad AP template 未使用變數。
- `08-7A自動晚安情境AI` 修補版升級至 `V3.1.1`：修正離家安全重檢條件，重檢後 Kenny 仍為 `離家` 時不再取消晚安情境，僅回到 `客廳` / `廚房` / `廁所` / `車庫` 才停止。
- `08-8B廁所感應燈AI` 修補版升級至 `V3.0.1`：長按切換與閃爍次數判斷統一使用 `manual_override_entity` 變數，移除硬編碼分散。
- LINE 通知檢查：本次只修正 helper options、template 死碼與自動化條件/變數引用，未新增或修改 persistent notification / LINE 發送路徑；未出現新的 `notify.line_*` 或直接 LINE 呼叫，符合 SOP-10。

- `21A_客廳電風扇整合控制AI` 修補版升級至 `V3.2.1`：確認並補強動態兒童鎖低溫解鎖遲滯；Kenny 在二樓主控制區（客廳/廚房/廁所）一律解鎖，Kenny 不在主控制區時 `t_eff > 30.5°C` 才上鎖，並在 `t_eff < 30.0°C` 主動解鎖，30.0～30.5°C 保持現狀避免抖動。
- LINE 通知檢查：本次只調整 21A 兒童鎖控制 service，未新增或修改 persistent notification / LINE 發送路徑，未出現 `notify.line_*` 或直接 LINE 呼叫；既有耗材一鍵測試 LINE 路徑仍符合 SOP-10。

- `21A_客廳電風扇整合控制AI` 功能版升級至 `V3.2.0`：移除開燈連動、加入 Kenny 主控制區動態兒童鎖、夏季曲線上移 2.3°C，非夏季減成改 -10% 並放開最低限制。
- `22頂樓電風扇自動化AI` 功能版升級至 `V3.3.0`：日間曲線門檻全數上調 0.2°C，睡眠降速改用 `input_boolean.sleep_silent_active`，睡眠/非夏季減成擴大為 -10%。
- 新增 `08-8B廁所感應燈AI (V3.0.0)`：廁所感應燈 AI 化，支援 1 分鐘無人關燈、長按事件切換手動關閉模式與 4/2 次閃爍回饋；舊 `automations.yaml` 廁所感應燈已移除。
- `00-2C耗材更換AI通知` 功能版升級至 `V3.1.0`：電量監控清單移除舊 Aqara 魔方，加入廁所人體感應器與新客廳 Aqara 魔方，並新增耗材電量一鍵測試報告。
- `08-7A自動晚安情境AI` 功能版升級至 `V3.1.0`：晚安時段延長至 05:00，二樓無人防抖提高至 90 秒，並加入 Location Helper 安全重檢取消機制。
- `100B自動離家AI` 功能版升級至 `V3.4.0`：離家判斷全面改用 `sensor.at_home_XXX_location` 中文狀態，所有家庭成員「離家」滿 4 分 10 秒才觸發。
- `104-2車牌辨識AI` 修補版升級至 `V3.1.1`：車牌/設備代號 `舊家用車牌` 全域更名為 `EBH8030`，Webhook ID 與通知文字同步。
- Helper 套件功能版升級至 `V3.17`：新增廁所手動關閉模式、耗材測試按鈕、兩個最低電量記錄 helper、Kenny iPad 中文 Location helper，並記錄車牌更名。
- Location 架構字典：`sensor.at_home_XXX_location` 使用中文位置狀態（`客廳`、`廚房`、`廁所`、`車庫`、`離家`、`離家確認中` 等），`binary_sensor.at_home_XXX` 維持在家布林狀態，供未來 AI 情境防抖與安全閘使用。
- LINE 通知檢查：本次新增的耗材一鍵測試 LINE 路徑使用 `script.send_line_to_user`、一般分級開關、耗材額外開關與 user_id 有效性檢查；檢查不通過時建立 persistent notification 記錄未發送原因，符合 SOP-10。

## 本次調整（2026-06-03 Debug 通知開關與車牌開門通知）
- `106網關系統AI` 功能版升級至 `V3.3.0`：新增 `input_boolean.gateway_debug_notify`，將解除歸位、唯一情境同步與無情境歸位等清理型永久通知改為 Debug 開啟時才發送；異常攔截緊急 LINE 維持原有 `script.send_line_to_user`、緊急分級開關與 user_id 防呆，Debug 不新增 LINE 路徑。
- `104-2車牌辨識AI` 功能版升級至 `V3.1.1`：沿用 `input_boolean.lpr_debug_notify` 控管預備/取消類永久通知，將「🙂（預備）條件式關門：不關」改為 Debug 開啟才通知；新增 `input_boolean.lpr_open_notify_enable` 控管實際 LPR 自動開門永久通知，實際自動關門仍保留永久通知。
- Helper 套件功能版升級至 `V3.16`：新增網關 Debug 通知開關與 LPR 車牌開門通知開關。
- SOP 更新：新增 Debug Helper / 清理型永久通知規範，並補充 Debug 不得把原本未送 LINE 的通知升級成 LINE；LINE 通知檢查確認本次未新增任何 `notify.line_*` 或 LPR LINE 路徑，106 既有 LINE 仍符合 SOP-10。

## 本次調整（2026-06-01 網關防抖與頂樓熟睡手動鎖）
- `106網關系統AI` 功能版升級至 `V3.2.0`：Actions 最前方新增 1 秒 Debounce，並將 Aqara 情境數量、情境標籤與唯一情境名稱移至 delay 後的 action variables 即時求值，避免離家/在家開關互搶時使用觸發 0 秒舊狀態。
- `08-5F頂樓自動上下樓情境AI` 功能版升級至 `V3.4.0`：新增 `input_boolean.sleep_silent_active` 熟睡手動鎖；Webhook、AP、攝影機與尾隨寬限的所有上樓成立路徑均需 `not sleep_silent_active`，自動下樓與 AI 離家複檢成立時會自動復歸該 helper。
- Helper 套件升級至 `V3.15`：新增 `input_boolean.sleep_silent_active`，供手機/情境手動維持熟睡狀態。
- LINE 通知檢查：本次未新增或修改 LINE 發送流程；`106網關系統AI` 既有緊急 LINE 仍維持 `script.send_line_to_user`、緊急分級開關、user_id 防呆與未發送 fallback，未新增直接 `notify.line_*` 呼叫，符合 SOP-10。

## 本次調整（2026-05-31 頂樓 Webhook 靜默與樓梯燈救援）
- `08-5F頂樓自動上下樓情境AI` 修補版升級至 `V3.3.2`：將睡眠靜默窗納入 Webhook 跨線判定前置條件，深夜熟睡時間完全忽略三條跨線 Webhook 訊號；原本 AP/攝影機流程與離家事件判斷維持不變。
- `08-5C頂樓樓梯感應燈AI` 功能版升級至 `V3.4.5`：主流程 Webhook 補燈同步納入睡眠靜默窗並避免 Webhook 觸發落入原本攝影機分支；自動關閉 AI 改為 Conditions 僅保留「綜合/原本模式 + 主流程 180 秒內點亮」安全閥，Actions 分流為 A 軌跡完好秒關與 B 預設 22 秒攝影機動態清除救援流，並保留坎燈防誤關複檢。
- LINE 通知檢查：本次未新增或修改 LINE 發送流程，未出現直接 `notify.line_*` 呼叫；SOP-10 無需新增 payload，且既有 `script.send_line_to_user` 規範未受影響。

## 本次調整（2026-05-30 頂樓 Webhook、保全系統、晚安情境、Tesla 充電與樓梯燈綜合優化）
- `08-7A自動晚安情境AI` 修補版升級至 `V3.1.0`：恢復 21:00 `night_check` 觸發，避免二樓在 21:00 前已無人時，因沒有狀態轉換而漏跑晚安情境；保留 30 秒無人等待與取消執行訊息通知。
- `08-5C頂樓樓梯感應燈AI` 修補版升級至 `V3.4.1`：精簡輔助關燈條件，移除被 `elapsed >= 2.5` 覆蓋的 `elapsed > 10` 冗餘判斷，邏輯行為不變。
- LINE 通知檢查：本次只調整 08-7A 觸發補洞與 08-5C 條件可讀性，未新增或修改 LINE 發送流程，未出現直接 `notify.line_*` 或繞過 `script.send_line_to_user` 的呼叫；SOP-10 無需新增 payload。

- `107Tesla充電器狀態與通知AI` 修補版升級至 `V3.2.2`：充電完成通知於用電量上方新增「充電用時 X時X分鐘」；一般 LINE 仍使用 `script.send_line_to_user`，並保留一般分級開關、Tesla 額外 LINE 開關與 user_id 有效性檢查，不通過時留下 `persistent_notification` 未發送原因，符合 SOP-10。
- `106網關系統AI` 修補版升級至 `V3.1.1`：HA 重開機觸發時只執行情境/網關同步，不發送 persistent notification 或 LINE；非 HA 重啟的異常攔截 LINE 仍走 `script.send_line_to_user` 並保留緊急分級開關、user_id 防呆與未發送 fallback，符合 SOP-10。

- `08-5C頂樓樓梯感應燈AI` 功能版升級至 `V3.4.0`：輔助關燈改依主流程最近來源分流；書房線/樓梯線直接放行，臥室線/攝影機 2.5 秒內攔截、2.5～10 秒放行，超過 10 秒一律放行。
- `08-7A自動晚安情境AI` 修補版升級至 `V3.0.2`：移除 night_check 定時觸發，二樓無人等待改為 30 秒，並取消執行訊息通知。
- LINE 通知檢查：本次兩份自動化皆未新增或修改 LINE 發送；08-7A 反而移除執行訊息通知，因此 SOP-10 無需新增 payload，且不會出現繞過 `script.send_line_to_user` 的 LINE 呼叫。

- `107Tesla充電器狀態與通知AI` 升級至 `V3.2.1`：修補版。插槍後若直接進入 `charging` / `charging_reduced`，`charge_done` 的當次已充電記憶重設流程會排除充電中狀態，避免 `input_boolean.tesla_charger_session_charged` 先開啟又瞬間關閉；LINE 發送維持 `script.send_line_to_user`，補齊 user_id 有效性檢查、一般/重要分級開關與 Tesla 額外開關判斷，以及未發送原因 `persistent_notification` fallback，符合 SOP-10。

- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.3.4`：修正輔助關燈 8～180 秒防呆取值方式，改從主流程與備援舊 ID 的 `last_triggered` 中取最新時間，避免 `or` 只取第一個非空時間而忽略近期備援點燈紀錄；本次未新增或修改 LINE 發送流程，SOP-10 不適用但已確認 08-5C 無直接 `notify.line_*` 呼叫。

- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.3.3`：重新啟用輔助關燈時間差防呆，主流程點燈後 8 秒內禁止書房左側感應器觸發輔助關燈，避免剛出房間關門或路過造成樓梯燈誤關；本次未新增或修改 LINE 發送流程，SOP-10 不適用但已確認無直接 `notify.line_*` 呼叫。

- Helper 套件修補版升級至 `V3.14.1`：新增 `binary_sensor.che_ku_wa_fi_gan_ying_zong_he_pan_duan` 與 `binary_sensor.er_lou_ping_mu_gan_ying_zong_he_pan_duan`，沿用 AtHome AP MAC 區域判斷邏輯，補齊 104-3 與 08-7A 依賴實體。
- `104-3鐵門判斷未關提醒及作動AI` 升級至 `V3.3.1`：同步 Helper 相容版本，LINE 標題補版本字串，並明確記錄分級開關關閉或 user_id 無效時的未發送原因，符合 SOP-10。
- `08-7A自動晚安情境AI` 升級至 `V3.0.1`：同步 Helper 相容版本，確認二樓無人判斷 helper 已由 Helper 套件建立。

- `106網關系統AI` 升級至 `V3.1`：正式改名並接管舊版 106 網關同步邏輯，移除舊自動化 ID `1690898378439`，以異常攔截 / 常規同步 / 解除歸位 / 無情境歸位分流避免 Race Condition，LINE 緊急通知依 SOP-10 走 `script.send_line_to_user` 並保留未發送 fallback。
- 新增 `08-7A自動晚安情境AI (V3.0)`：於 21:00 後或 03:00 前，二樓 AP/人員綜合判定無人且晚安情境尚未啟用時自動執行晚安情境。
- `104-3鐵門判斷未關提醒及作動AI` 升級至 `V3.3`：自動關門前新增車庫 AP 人員綜合判定，偵測有人時取消關門且不影響逾時未關提醒；車庫主燈變化排除 unknown/unavailable 抖動，AP 攔截補 LINE 結果通知。
- `08-5C頂樓樓梯感應燈AI` 升級至 `V3.3.2`：攝影機防呆冷卻由 15 秒縮短至 10 秒，燈具實體狀態防呆由 5 秒縮短至 2 秒。

- `08-5A` / `08-5C` / `08-5F` / `08-5G` 修補版升級至 `V3.3.1`：補強手動執行時 `trigger` 未定義防呆，修正 08-5F 下樓 3 分鐘保護窗後 AP 複檢改用即時狀態，並修復 08-5A LINE user_id 為 unknown 時 fallback 失效。

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
- `00-2C耗材更換AI通知` 升級至 `V3.1.0`：修復濾芯壽命重複通知問題（避免 unknown/unavailable 抖動），並在推播中明確標示為「空氣清淨機濾芯壽命」。
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
- `22頂樓電風扇自動化AI` 修補版升級至 `V3.3.0`：修復 `t_eff` 在感測器暫時失效時（`none/unavailable`）造成 `float` 轉型錯誤，補強 `t_eff_valid` 判斷並加入安全預設值，避免自動化中斷。
- Helper 套件修補版升級至 `V3.9.1`：將版本比對模板中的 `dict.update()` 全數改為安全的 `dict(...)` 重新指派寫法，修復新版 Jinja2 的 `SecurityError` 限制。
- `08-5C頂樓樓梯感應燈AI` 修補版升級至 `V3.0.1`：主流程防呆由 8 秒調整為 15 秒，降低關燈後感測延遲造成誤重開。
- `08-5H頂樓深夜熟睡情境AI` 修補版升級至 `V3.0.1`：改為下樓情境執行後 1 分鐘檢查床頭燈（`light.yeelink_bslamp2_4329_light`）是否關閉；若失敗自動重跑一次下樓流程，僅在確認成功後才恢復風扇狀態。
- `100B自動離家AI` 修補版升級至 `V3.4.0`：LINE 通知標題統一移除「100B」編號顯示，並改以 `automation_version` 動態帶入版本，避免版本號未同步更新。
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

- 21A_客廳電風扇整合控制AI 升級至 `V3.2.0`：導入手動調速防護罩（下次開機解除）、manual actor 判斷與 null-safe 條件，避免 AI 與手動調速互搶。
- 廣播設備清理（2026-04）：已移除 `media_player.sony_bravia_tv` 相關音量/切源/狀態判斷流程，避免已下線設備造成自動化錯誤。
- 廣播設備清理延伸修正（2026-04-08）：05B / 08-6 / 21B 與地震遠端 Script 移除已下線 TV remote 實體引用（`61eaa5fb8386221ba077bcb884e74573`），避免 `Unknown entity` 導致自動化與腳本設定失敗；版本升級為 05B V3.1、08-6 V3.1、21B V3.1、EQ Script V3.4。
- 後續廣播更新約定：原 Sony TV 控制位置已統一改以 `# TVSPEAKERTODO:` 註記；未來導入新設備時，優先搜尋 `TVSPEAKERTODO` 後補上新設備音量與播放指令即可。

- Google Home 情境觸發橋接（2026-04）：新增 `100C_GoogleHome情境虛擬按鈕橋接AI`，以 `input_boolean.google_scene_*` 觸發 `100/101/102/103` 情境自動化，並在觸發後自動復位。
- Helper 升級至 `V3.9`：新增 Google Home 情境虛擬按鈕 helpers（早安/晚安/到家/出門）。

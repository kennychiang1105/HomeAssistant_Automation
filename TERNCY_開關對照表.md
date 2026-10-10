# Terncy 無線開關對照表（面板 / 按鈕 / 位置 / 實體）

> 建立：2026-10-09，Claude Code。資料來源：HA `core.entity_registry` / `core.device_registry` / `core.area_registry`。

## 重點

- 同一片實體面板 = 同一個 MAC。`unique_id` 格式 `<MAC>-<按鈕號>`，按鈕號 01/02/03 為同一片面板的三個按鈕（S2 機型只有 01/02）。
- HA 把每顆按鈕登錄成獨立 device（沒有「面板」這一層，via_device 只指向家庭中樞），UI 上看不出哪幾顆同一片，要以 MAC 判斷。
- 按鈕名稱與房間不保證一致：例如 `dc8e95fffe8d69a0` 的三顆分屬車庫 / 餐廳；`540f57fffe8239d3` 的兩顆分屬頂樓 / 樓梯間。
- 2026-10-09 更新：17 顆接實體燈具的按鈕（車庫主燈、樓梯燈、廁所燈、廚房燈、客廳各燈、餐廳各燈、頂樓各燈等），其「無線開關」(`*_wireless_switch_enabled`) 統一改為 off，恢復硬體直接即時切換繼電器；其餘無實體負載按鈕維持 on。全戶 38 顆按鈕之雙擊、三擊（05E 緊急模式）與長按事件皆維持正常運作。
- 2026-10-09：已將所有 Terncy 面板按鈕與書房感應開關的 `single_press` / `double_press` / `long_press` 事件實體啟用（共 75 個由 disabled_by=integration 改為啟用，登錄檔備份在主機 `/tmp/bk_stage/pre_terncy_events/core.entity_registry`）。`event.*_button` 仍維持停用。
- 事件實體名稱規則：`event.<按鈕名>_single_press|double_press|long_press`；按鈕名通常等於繼電器 switch 實體 id 去掉 `switch.`（個別面板有出入，以下表為準）。
- 05E 緊急模式三擊觸發已全面覆蓋全戶 38 顆按鍵，且針對曾發生 split 的 14 顆按鈕同時綁定新舊 device_id 雙保險監聽。

## 面板清單（13 片 Terncy 開關面板共 37 鍵，另加 1 個書房感應開關 PP01，共 14 台 38 鍵）

### 一樓

**面板 `dc8e95fffe8d69a0`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 樓梯燈 | 車庫 | `switch.lou_ti_deng` | `event.lou_ti_deng_single_press / event.lou_ti_deng_double_press / event.lou_ti_deng_long_press` |
| 02 | 廁所燈 | 餐廳 | `switch.ce_suo_deng` | `event.ce_suo_deng_single_press / event.ce_suo_deng_double_press / event.ce_suo_deng_long_press` |
| 03 | 餐廳燈 | 餐廳 | `switch.can_ting_deng` | `event.can_ting_deng_single_press / event.can_ting_deng_double_press / event.can_ting_deng_long_press` |

**面板 `e0798dfffeb3c1af`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 車庫主開關1 | 車庫 | `switch.che_ku_zhu_kai_guan_1` | `event.che_ku_zhu_kai_guan_1_single_press / event.che_ku_zhu_kai_guan_1_double_press / event.che_ku_zhu_kai_guan_1_long_press` |
| 02 | 車庫主燈 | 車庫 | `switch.che_ku_zhu_deng` | `event.che_ku_zhu_deng_single_press / event.che_ku_zhu_deng_double_press / event.che_ku_zhu_deng_long_press` |
| 03 | 車庫主開關3 | 車庫 | `switch.che_ku_zhu_kai_guan_3` | `event.che_ku_zhu_kai_guan_3_single_press / event.che_ku_zhu_kai_guan_3_double_press / event.che_ku_zhu_kai_guan_3_long_press` |

### 二樓

**面板 `dc8e95fffe8b12e9`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 客廳環繞燈 | 客廳 | `switch.ke_ting_bi_deng` | `event.ke_ting_bi_deng_single_press / event.ke_ting_bi_deng_double_press / event.ke_ting_bi_deng_long_press` |
| 02 | 客廳壁燈 | 客廳 | `switch.ke_ting_huan_rao_deng` | `event.ke_ting_huan_rao_deng_single_press / event.ke_ting_huan_rao_deng_double_press / event.ke_ting_huan_rao_deng_long_press` |
| 03 | 客廳崁燈 | 客廳 | `switch.ke_ting_kan_deng` | `event.ke_ting_kan_deng_single_press / event.ke_ting_kan_deng_double_press / event.ke_ting_kan_deng_long_press` |

**面板 `dc8e95fffe8d6b8e`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 餐廳崁燈 | 餐廳 | `switch.can_ting_kan_deng` | `event.can_ting_kan_deng_single_press / event.can_ting_kan_deng_double_press / event.can_ting_kan_deng_long_press` |
| 02 | 餐廳壁燈 | 餐廳 | `switch.can_ting_bi_deng` | `event.can_ting_bi_deng_single_press / event.can_ting_bi_deng_double_press / event.can_ting_bi_deng_long_press` |
| 03 | 餐廳主開關上3 | 餐廳 | `switch.can_ting_zhu_kai_guan_shang_3` | `event.can_ting_zhu_kai_guan_shang_3_single_press / event.can_ting_zhu_kai_guan_shang_3_double_press / event.can_ting_zhu_kai_guan_shang_3_long_press` |

**面板 `dc8e95fffe957fe8`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 客廳主開關下1 | 客廳 | `switch.ke_ting_zhu_kai_guan_xia_1` | `event.ke_ting_zhu_kai_guan_xia_1_single_press / event.ke_ting_zhu_kai_guan_xia_1_double_press / event.ke_ting_zhu_kai_guan_xia_1_long_press` |
| 02 | 客廳主開關下2 | 客廳 | `switch.ke_ting_zhu_kai_guan_xia_2` | `event.ke_ting_zhu_kai_guan_xia_2_single_press / event.ke_ting_zhu_kai_guan_xia_2_double_press / event.ke_ting_zhu_kai_guan_xia_2_long_press` |
| 03 | 客廳主開關下3 | 客廳 | `switch.ke_ting_zhu_kai_guan_xia_3` | `event.ke_ting_zhu_kai_guan_xia_3_single_press / event.ke_ting_zhu_kai_guan_xia_3_double_press / event.ke_ting_zhu_kai_guan_xia_3_long_press` |

**面板 `e0798dfffeb78a38`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 廚房燈 | 廚房 | `switch.chu_fang_deng` | `event.chu_fang_deng_single_press / event.chu_fang_deng_double_press / event.chu_fang_deng_long_press` |
| 02 | 廚房開關2 | 廚房 | `switch.chu_fang_kai_guan_2` | `event.chu_fang_kai_guan_2_single_press / event.chu_fang_kai_guan_2_double_press / event.chu_fang_kai_guan_2_long_press` |
| 03 | 廚房開關3 | 廚房 | `switch.chu_fang_kai_guan_3` | `event.chu_fang_kai_guan_3_single_press / event.chu_fang_kai_guan_3_double_press / event.chu_fang_kai_guan_3_long_press` |

**面板 `e0798dfffec10c5a`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 客廳外開關下1 | 客廳 | `switch.ke_ting_wai_kai_guan_xia_1` | `event.ke_ting_wai_kai_guan_xia_1_single_press / event.ke_ting_wai_kai_guan_xia_1_double_press / event.ke_ting_wai_kai_guan_xia_1_long_press` |
| 02 | 路燈 | 客廳 | `switch.lu_deng` | `event.lu_deng_single_press / event.lu_deng_double_press / event.lu_deng_long_press` |
| 03 | 門口燈 | 客廳 | `switch.men_kou_deng` | `event.men_kou_deng_single_press / event.men_kou_deng_double_press / event.men_kou_deng_long_press` |

### 五樓

**面板 `000d6f0018e18393`**（TERNCY-PP01，1 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 書房感應開關 | 頂樓 | `-` | `event.shu_fang_gan_ying_kai_guan_single_press / event.shu_fang_gan_ying_kai_guan_double_press / event.shu_fang_gan_ying_kai_guan_long_press` |

**面板 `540f57fffe52152c`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 五樓開關上3 | 頂樓 | `switch.wu_lou_kai_guan_shang_3` | `event.wu_lou_kai_guan_shang_3_single_press / event.wu_lou_kai_guan_shang_3_double_press / event.wu_lou_kai_guan_shang_3_long_press` |
| 02 | 壁燈 | 頂樓 | `switch.bi_deng` | `event.bi_deng_single_press / event.bi_deng_double_press / event.bi_deng_long_press` |
| 03 | 陽台燈 | 頂樓 | `switch.yang_tai_deng` | `event.yang_tai_deng_single_press / event.yang_tai_deng_double_press / event.yang_tai_deng_long_press` |

**面板 `540f57fffe8239d3`**（TERNCY-WS07-S2，2 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 頂樓樓梯燈 | 頂樓 | `switch.ding_lou_lou_ti_deng` | `event.ding_lou_lou_ti_deng_single_press / event.ding_lou_lou_ti_deng_double_press / event.ding_lou_lou_ti_deng_long_press` |
| 02 | 四樓樓梯開關上2 | 樓梯間 | `switch.si_lou_lou_ti_kai_guan_shang_2` | `event.si_lou_lou_ti_kai_guan_shang_2_single_press / event.si_lou_lou_ti_kai_guan_shang_2_double_press / event.si_lou_lou_ti_kai_guan_shang_2_long_press` |

**面板 `540f57fffe823cdb`**（TERNCY-WS07-S2，2 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 五樓開關下2 | 頂樓 | `switch.wu_lou_kai_guan_xia_2` | `event.wu_lou_kai_guan_xia_2_single_press / event.wu_lou_kai_guan_xia_2_double_press / event.wu_lou_kai_guan_xia_2_long_press` |
| 02 | 書房燈 | 頂樓 | `switch.shu_fang_deng` | `event.shu_fang_deng_single_press / event.shu_fang_deng_double_press / event.shu_fang_deng_long_press` |

### 機房

**面板 `dc8e95fffe83684d`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 四樓開關下1 | 樓梯間 | `switch.si_lou_lou_ti_deng` | `event.si_lou_lou_ti_deng_single_press / event.si_lou_lou_ti_deng_double_press / event.si_lou_lou_ti_deng_long_press` |
| 02 | 四樓開關下2 | 樓梯間 | `switch.si_lou_kai_guan_xia_2` | `event.si_lou_kai_guan_xia_2_single_press / event.si_lou_kai_guan_xia_2_double_press / event.si_lou_kai_guan_xia_2_long_press` |
| 03 | 四樓開關下3 | 樓梯間 | `switch.si_lou_kai_guan_xia_3` | `event.si_lou_kai_guan_xia_3_single_press / event.si_lou_kai_guan_xia_3_double_press / event.si_lou_kai_guan_xia_3_long_press` |

**面板 `dc8e95fffe8d68f0`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 三樓樓梯燈 | 樓梯間 | `switch.san_lou_lou_ti_deng` | `event.san_lou_lou_ti_deng_single_press / event.san_lou_lou_ti_deng_double_press / event.san_lou_lou_ti_deng_long_press` |
| 02 | 三樓開關下2 | 樓梯間 | `switch.san_lou_kai_guan_xia_2` | `event.san_lou_kai_guan_xia_2_single_press / event.san_lou_kai_guan_xia_2_double_press / event.san_lou_kai_guan_xia_2_long_press` |
| 03 | 二三樓樓梯燈 | 樓梯間 | `switch.er_san_lou_lou_ti_deng` | `event.er_san_lou_lou_ti_deng_single_press / event.er_san_lou_lou_ti_deng_double_press / event.er_san_lou_lou_ti_deng_long_press` |

**面板 `e0798dfffec3163b`**（TERNCY-WS07-S3，3 鍵）

| 鍵 | 名稱 | 房間 | 繼電器 switch | 事件 單擊 / 雙擊 / 長按 |
|---|---|---|---|---|
| 01 | 三四樓樓梯燈 | 樓梯間 | `switch.san_si_lou_lou_ti_deng` | `event.san_si_lou_lou_ti_deng_single_press / event.san_si_lou_lou_ti_deng_double_press / event.san_si_lou_lou_ti_deng_long_press` |
| 02 | 三樓開關上2 | 樓梯間 | `switch.san_lou_kai_guan_shang_2` | `event.san_lou_kai_guan_shang_2_single_press / event.san_lou_kai_guan_shang_2_double_press / event.san_lou_kai_guan_shang_2_long_press` |
| 03 | 三樓開關上3 | 樓梯間 | `switch.san_lou_kai_guan_shang_3` | `event.san_lou_kai_guan_shang_3_single_press / event.san_lou_kai_guan_shang_3_double_press / event.san_lou_kai_guan_shang_3_long_press` |


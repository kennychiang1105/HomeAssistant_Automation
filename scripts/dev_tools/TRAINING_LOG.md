# 影片訓練紀錄（哪些影片已經用過）

NAS 錄影：`\\jnas916p\Family\UniFi\UniFi-Protect_<日期>`；車庫攝影機 `[847848288CA2]`、頂樓攝影機 `[70A7410D7177]`。
檔名格式：`M-D-YYYY, H.MM.SSam GMT+8 - ... [攝影機].mp4`（11 月起月／日是一位數，比對要用 `\d{1,2}`）。

| 模型 | 部署位置 | 已用影片範圍 | 最近訓練 | 結果 |
|---|---|---|---|---|
| 車位有沒有車（CLIP 特徵＋邏輯迴歸） | add-on `/data/occ_model.json`（repo `addons_src/garage_vision/occ_model.json`） | 車庫 10/26～11/07 18:00（frames 10/26～10/30、frames2 10/30 08:30～10/31 09:38、frames3 10/31 09:39～11/07） | 2026-11-07（v3） | 依日期留一：後位困難樣本很有把握判對 11→14/14、很有把握比例 94.8→98.4%；前位很有把握卻判錯 2→1；**已部署 v3**（v2 備份在 add-on `/data/occ_model_v2_backup.json`） |
| 車庫車輛偵測微調（YOLO11m，car／person） | add-on `/data/garage_car.onnx` | 車庫 10/26～10/30 | 2026-10-30 | 11/07 只評估不重訓：新影片上有車畫面偵測率前位 99.7%、後位 99.1%；也負責偵測「人」（方向燈開門等人上車的門檻剛用它校準） |
| 頂樓去向（書房／臥室，邏輯迴歸） | `scripts/topfloor_track.py` 的 `DEST_LR` | 頂樓 10/27～10/31 09:12（訓練）；10/29 10:06～10/30 00:00、10/31 09:13～11/07 已評估 | 2026-10-31 | 11/07 用新影片 173 段評估：部署中模型樣本外 89.6%（追蹤器層級 80.3%）；重訓（整段特徵 79.2%、判斷段特徵 78.0%）沒有比較好 → **維持現行模型**；採用門檻 0.70／0.30 → **0.60／0.40**（261 段判對 217→221、判錯 20→18） |
| 車輛身分（CLIP 樣板 kNN） | add-on `/data/gallery.json` | 車庫 10/31～11/07 967 張（frames3 每 4 張取 1），車牌依位置證實身分、另一車位排除法 | 2026-11-07 | 補學 16 張（前位 Luxgen 開後車廂／昏暗、後位 Luxgen 車頭朝內、前／後位 Tesla 各 4）。依日期留一：判錯 8→1、後位 Luxgen 判對 3→84、前位 Tesla 不採用 23→9；樣板庫 57→73（備份 `/data/gallery_backup_20261107.json`） |

## 第 3 批（2026-11-07）資料位置
- 車庫：`C:\ai_lab\garage\frames3`（3,868 張，每 4 秒一張）、`emb3.npz`、`eval3.json`、`pseudo3.json`、`occ_model_v3.json`
- 頂樓：`C:\ai_lab\topfloor\obs_pose3.json`（347 段，每秒 2 幀姿態）、`clips3\clipmap.json`、`events3.json`（recorder `topfloor_path` 事件）、`dest3.py`、`dest3b.py`
- 下次從 **11/07 18:00 之後**的影片開始。

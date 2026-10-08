# 開發／測試工具（V4.0 發布時從主機載入範圍移出）

- `00-2G測試觸發AI.yaml` + `test_trigger.yaml`：不用 API 權杖也能測試的「檔案觸發」機制。
  做法：把 `test_trigger.txt` 內容改成「指令|參數|序號」，00-2G 就會執行（`tfset`、`tflight`、`tftext`、`tfbright`、`tfsig`、`eqtest`、`mood`、`ambient`、`scene`、`ann`、`gate4`、`ndtest` 等）。
- 要再用：把 `00-2G` 放回主機 `/homeassistant/configuration/Automations/`、`test_trigger.yaml` 放回 `/homeassistant/packages/`，重啟 HA，用完再移出。
- 主機封存位置：`/homeassistant/deprecated_automations_backup/Archived_20261008/`。

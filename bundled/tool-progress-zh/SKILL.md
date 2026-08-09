---
name: tool-progress-zh
description: >-
  將 Hermes Telegram／gateway 工具進度標籤改成繁體中文（執行程式、搜尋檔案、讀取檔案…）。
  Hermes update 後重跑。不依賴作者本機。
---

# tool-progress-zh — 工作進度標籤繁中

## 用途

Telegram 上「Running code / Searching files / Reading …」來自上游硬編碼  
`agent/display.py` 的 `_TOOL_VERBS`，**不走** `display.language` 的 YAML catalog。

本補丁在部署端 Hermes 原始碼注入繁中動詞表；當 `display.language` 為 zh-TW／zh-hant 時自動使用。

## 套用

```bash
# 隨 hermes-tw-setup 安裝後：
python3 ~/.hermes/skills/hermes-tw-setup/bundled/tool-progress-zh/apply_patch.py

# 或由 baseline apply 自動呼叫
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

**必做**：重啟所有相關 gateway 後才生效。

## 驗證

```bash
python3 - <<'PY'
import os, sys
from pathlib import Path
os.environ.setdefault("HERMES_HOME", str(Path.home()/".hermes"))
for p in [
    Path.home()/".hermes"/"hermes-agent",
    Path("/opt/hermes"),
    Path("/opt/hermes/hermes-agent"),
]:
    if (p/"agent"/"display.py").exists():
        sys.path.insert(0, str(p)); break
from agent.display import build_tool_label
print(build_tool_label("search_files", {"pattern":"test"}))
# 期望：搜尋檔案：test
PY
```

## 注意

- 直接改部署端 Hermes source；`hermes update`／git pull 上游後需重跑本腳本
- 冪等：已套用會印「已是繁中」並 exit 0
- 不讀取、不依賴作者機器任何路徑

---
name: telegram-commands-zh
description: 將 Hermes Telegram 選單指令描述改成繁體中文。更新 Hermes 後可重跑。
---

# Telegram 指令繁中

## 套用

```bash
python3 ~/.hermes/skills/telegram-commands-zh/apply_patch.py
# 重啟所有相關 hermes-gateway 後，Telegram 選單才會更新
```

路徑只在 `HERMES_HOME`（預設使用者 Hermes 家目錄）底下找 `hermes_cli/commands.py`。若家目錄不是正式安裝，不會回過去改正式檔。

## 注意

- 補丁後**必須重啟 gateway**，選單才會向 Telegram 重新註冊
- 多 profile 要重啟全部相關 gateway

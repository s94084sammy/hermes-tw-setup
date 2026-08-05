# hermes-tw-setup

**Taiwan baseline for Hermes Agent**  
台灣在地化的 Hermes Agent 初始最佳化設定技能

[![Release](https://img.shields.io/github/v/release/s94084sammy/hermes-tw-setup?label=release)](https://github.com/s94084sammy/hermes-tw-setup/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Overview

`hermes-tw-setup` 定義一套可重現、可檢查、可套用的 **Hermes Agent 台灣基線（baseline）**：在既有 Hermes 安裝之上，統一地區、語言、雙助理架構、搜尋策略、模型備援規範、工作方法技能與本機記憶，並提供跨平台主機常駐建議。

適用對象為使用 Hermes Agent、需要 **繁體中文（台灣）** 與 **可長期運作** 工作站設定的個人與團隊。技能本身不承載帳號憑證；認證與金鑰由部署端依文件完成。

| 能力 | 說明 |
|------|------|
| 診斷 | `check`：完整基線稽核，未通過項目附修復指引 |
| 套用 | `apply`：冪等寫入設定、預裝技能與行為規範 |
| 手冊 | 開箱、OAuth、雙 bot、主機與瀏覽器流程見 `references/` |

---

## Requirements

- 已安裝 [Hermes Agent](https://github.com/NousResearch/hermes-agent)（或相容發行版）
- Python 3，以及 `PyYAML`
- 可選：Docker（隔離驗證）、Chrome／Chromium（DevTools／CDP）

---

## Install

```bash
git clone https://github.com/s94084sammy/hermes-tw-setup.git ~/.hermes/skills/hermes-tw-setup
pip install --user pyyaml
```

建議以 [Releases](https://github.com/s94084sammy/hermes-tw-setup/releases) 的 `v1.0.0` 或更新版本鎖定。

---

## Usage

```bash
# 稽核（唯讀）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check

# 套用基線（冪等；需明確 --yes）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

隔離環境（可選）：

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check \
  --docker <container> --docker-data ~/.hermes-test
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply \
  --docker <container> --docker-data ~/.hermes-test --yes
```

完整操作說明：

- [`references/MANUAL_STEPS.md`](references/MANUAL_STEPS.md) — 開箱與部署步驟  
- [`references/API_KEYS_BROWSER.md`](references/API_KEYS_BROWSER.md) — 以既有瀏覽器工作階段配置 API 金鑰  
- [`SKILL.md`](SKILL.md) — 供 Agent 載入的技能規格  

---

## Baseline scope

### Runtime architecture

- **雙 profile**：主助理 `default`、副助理 `side`
- **技能庫共用**（`skills.external_dirs`）；**排程各自獨立**
- **模型設定共用**；**訊息通道（Telegram）分離**，利於長任務與並行對話

### Locale & interface

- 時區 `Asia/Taipei`
- 介面語言 `display.language: zh-TW`
- 可選台灣 TTS／STT 語音偏好

### Search & models

- 預設網路搜尋：AnySearch（支援匿名路徑）＋免金鑰備援
- 主模型：訂閱制 OAuth（OpenAI Codex 或 xAI 等，依部署選擇）
- 備援：OpenRouter；模型候選限 [Hermes Agent 當期用量前列](https://openrouter.ai/apps/hermes-agent) 所公佈範圍

### Capability pack

- 文件：Word／Excel／PowerPoint／PDF 相關技能
- 影像：Agnes 生圖技能；前端程式碼產圖（設計／Canvas／生成藝術）＋瀏覽器截圖流程
- 工作方法：[Superpowers](https://github.com/obra/superpowers) 技能包
- 記憶：Hermes `holographic` 外部記憶（本機、無需額外套件帳號）
- 預設保留官方 bundled 技能完整集合（不做激進裁剪）

### Host & browser

- Gateway 開機自啟、可關螢幕且避免系統休眠（Linux／macOS／Windows 指引）
- Chrome DevTools MCP 與固定使用者設定檔之 CDP 連線

行為準則寫入 SOUL／MEMORY 摘要：預設協助完成任務、不臆測意圖、執行前查證現行做法、以實際檔案與輸出為準。

---

## Deployment checklist（部署端）

下列項目需在目標環境完成認證或通道設定（技能提供程序與指令，不內嵌憑證）：

1. 主模型 OAuth（例如 `hermes model`）
2. OpenRouter API key，以及依當期 Hermes 用量前列寫入 `fallback_providers`
3. Agnes API key（若使用免費生圖路徑）
4. 兩個獨立的 Telegram Bot token（主／副）
5. 主機自啟與電源策略（變更系統設定前應取得操作者同意）

---

## Repository layout

```text
SKILL.md                      Agent 可載入之技能規格
scripts/baseline.py           check / apply 實作
references/
  MANUAL_STEPS.md             部署手冊
  API_KEYS_BROWSER.md         瀏覽器金鑰流程
  SOUL-TW.md                  行為基線
  MEMORY-SNIPPET.md           記憶摘要
  PRELOAD_SKILLS.md           預裝政策
  DECISIONS.md                設計決策摘要
LICENSE
README.md
```

---

## Design principles

1. **可驗證**：check 輸出可對照、可重跑  
2. **可修復**：apply 以冪等方式收斂至基線；無法自動完成者輸出明確指令  
3. **最小憑證面**：優先免金鑰路徑；密鑰僅存在於部署端環境變數  
4. **在地優先**：台灣時區、繁體中文介面與溝通習慣  
5. **安全預設**：沿用 Hermes 官方防護機制，不另行堆疊說教式拒絕層  

---

## Security notes

- 請勿將 `.env`、token 或私人設定提交至版本庫  
- 金鑰與 OAuth 僅應寫入本機 Hermes 環境；對話與 issue 中避免貼出完整密鑰  
- 第三方技能與上游專案（Hermes、Superpowers、各 API 服務）遵循其各自授權與服務條款  

---

## License

MIT License. 見 [`LICENSE`](LICENSE)。

本倉庫對第三方技能僅提供安裝與整合說明；其著作權與授權以其上游為準。

---

## Disclaimer

本軟體按現況提供。部署後的設定、自動化行為與對外呼叫，由操作者與部署組織自行負責。使用前請確認符合 Hermes 及所連線服務之條款與當地法規。

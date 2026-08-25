# hermes-tw-setup

**Taiwan baseline for Hermes Agent**  
台灣在地化的 Hermes Agent 初始最佳化設定技能

[![Release](https://img.shields.io/github/v/release/s94084sammy/hermes-tw-setup?label=release)](https://github.com/s94084sammy/hermes-tw-setup/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**目前最新發行：[`v1.3.0`](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.3.0)**

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

## What's new in v1.3.0

對齊 [Release v1.3.0](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.3.0)：

- **Telegram 表格紅線**補齊（2026-08-24 定案）：表前必空行、格內禁粗體／斜體、單格 ≤ 約 20 字、欄數 ≤ 4、每行以 `|` 開頭、逐表自檢
- **視覺 QA 檔位紅線**（2026-08-10 定案）：最高檔模型、禁抽樣逐張看、機械過關不算通過、斷線重派不豁免（見 `references/DELIVERY_QA.md`）
- **新增 `references/WRITING_ZH.md`**：對外中文文案下限（中文母語模型加寫、禁寫作術語／中文破折號／AI 排比、溝通三段式）
- **新增 `references/MULTI_AGENT_RULES.md`**：多 agent 共同規則單一來源、短核＋索引按需載入、每日蒸餾
- **金鑰與通道管理**（2026-08-23 定案）：金鑰單一來源、變數只增不改名、通道禁混用（SKILL 七之二）
- **Chrome 分頁衛生**（2026-08-22 定案）：分頁用完必關、任務鎖不關（SKILL 七之三）
- **工具回報 ≠ 事實**：寄信／發布／寫入後驗證落庫或讀端，才宣稱完成（DELIVERY_QA 第 5 節）
- 可先在測試目錄套用，確認沒問題再裝到正在用的環境
- 預裝技能與套件鎖定版本，同一發行裝出來會一樣（見 `references/PINNED_SOURCES.md`）

更早版本摘要見下方 [Changelog](#changelog)。

---

## Requirements

- 已安裝 [Hermes Agent](https://github.com/NousResearch/hermes-agent)（建議 **v0.20+**，表格／rich 行為與此基線一致）
- Python 3，以及 `PyYAML>=6.0.1,<7`
- 可選：Docker（隔離驗證）、Chrome／Chromium（DevTools／CDP）
- apply 時需可連 GitHub／Skills Hub（無網路時仍可套用設定與 `bundled/`，但 Hub 與 Superpowers 會略過）

---

## Install

建議鎖定 **Latest release**（目前 `v1.3.0`）：

```bash
# 新裝：釘最新發行 tag
git clone --branch v1.3.0 \
  https://github.com/s94084sammy/hermes-tw-setup.git \
  ~/.hermes/skills/hermes-tw-setup

pip install --user 'PyYAML>=6.0.1,<7'
```

已有本機目錄時升級：

```bash
cd ~/.hermes/skills/hermes-tw-setup
git fetch --tags
git checkout v1.3.0
```

追 main 開發頭也可，但正式部署仍建議用 [Releases](https://github.com/s94084sammy/hermes-tw-setup/releases) 的 **Latest**。

---

## Usage

```bash
# 稽核（唯讀）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check

# 套用基線（冪等；需明確 --yes）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes

# 改完設定後務必重啟 gateway，Telegram rich／streaming／繁中進度才會生效
```

想先試裝、不動正在用的環境（可選）：

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply \
  --hermes-home /tmp/hermes-tw-test --yes
```

完整操作說明：

- [`references/MANUAL_STEPS.md`](references/MANUAL_STEPS.md) — 開箱與部署步驟
- [`references/TELEGRAM_RICH.md`](references/TELEGRAM_RICH.md) — 表格／rich／streaming 與三層驗證（含 2026-08-24 紅線細節）
- [`references/WRITING_ZH.md`](references/WRITING_ZH.md) — 對外中文文案下限
- [`references/DELIVERY_QA.md`](references/DELIVERY_QA.md) — 檔案交付視覺 QA 與「工具回報 ≠ 事實」驗證
- [`references/MULTI_AGENT_RULES.md`](references/MULTI_AGENT_RULES.md) — 多 agent 共同規則管理
- [`references/NETWORK_SOURCES.md`](references/NETWORK_SOURCES.md) — 依賴來源（隨包 + 網路 only）
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
- Telegram 選單繁中；**工具進度氣泡繁中**（執行程式／搜尋檔案…）
- Telegram：**rich 表格開** + **streaming 關**（v0.20+ 表格才穩）
- 表格是否「真的成功」採三層：設定 → API → 目視格子
- **表格紅線**（2026-08-24 定案）：表前必空行、格內禁粗體／斜體、單格 ≤ 約 20 字、欄數 ≤ 4、每行以 `|` 開頭
- 可選台灣 TTS／STT 語音偏好

### Search & models

- 預設網路搜尋：AnySearch（支援匿名路徑）＋免金鑰備援
- 主模型：訂閱制 OAuth（OpenAI Codex 或 xAI 等，依部署選擇）
- 備援：OpenRouter；模型候選限 [Hermes Agent 當期用量前列](https://openrouter.ai/apps/hermes-agent) 所公佈範圍

### Capability pack

- 文件：Word／Excel／PowerPoint／PDF 相關技能
- 影像：Agnes 生圖技能；前端程式碼產圖（設計／Canvas／生成藝術）＋瀏覽器截圖流程
- 工作方法：[Superpowers](https://github.com/obra/superpowers) 技能包（apply 時網路 clone）
- 記憶：Hermes `holographic` 外部記憶（本機、無需額外套件帳號）
- 預設保留官方 bundled 技能完整集合（不做激進裁剪）

### Host & browser

- Gateway 開機自啟、可關螢幕且避免系統休眠（Linux／macOS／Windows 指引）
- Chrome DevTools MCP 與固定使用者設定檔之 CDP 連線

行為準則寫入 SOUL／MEMORY 摘要：預設協助完成任務、不臆測意圖、執行前查證現行做法、以實際檔案與輸出為準。

### Writing & rules（v1.3.0）

- **對外中文文案下限**：中文母語模型撰寫／修改／擴寫；禁寫作術語、中文破折號、AI 排比（`references/WRITING_ZH.md`）
- **金鑰與通道管理**：金鑰單一來源、變數只增不改名、通道禁混用（SKILL 七之二）
- **Chrome 分頁衛生**：分頁用完必關、任務鎖不關（SKILL 七之三）
- **多 agent 共同規則**：共同檔單一來源、短核＋索引按需載入、每日蒸餾（`references/MULTI_AGENT_RULES.md`）
- **驗證原則**：工具回報 ≠ 事實，寄信／發布／寫入後驗證落庫或讀端（`references/DELIVERY_QA.md` 第 5 節）

---

## Deployment checklist（部署端）

下列項目需在目標環境完成認證或通道設定（技能提供程序與指令，不內嵌憑證）：

1. 主模型 OAuth（例如 `hermes model`）
2. OpenRouter API key，以及依當期 Hermes 用量前列寫入 `fallback_providers`
3. Agnes API key（若使用免費生圖路徑）
4. 兩個獨立的 Telegram Bot token（主／副）
5. 主機自啟與電源策略（變更系統設定前應取得操作者同意）
6. apply 後**重啟 gateway**，再目視確認 Telegram 表格為格子表

---

## Dependency model

**No author-machine skill library required.** Install this repo from GitHub, then `apply` pulls remaining pieces over the network at **pinned** git commits (see [`references/PINNED_SOURCES.md`](references/PINNED_SOURCES.md)).

## Bundled companion skills

發行包內含 `bundled/`，**不依賴**開發者本機其它 skill 目錄：

| 路徑 | 說明 |
|------|------|
| `bundled/telegram-commands-zh` | Telegram 選單繁中 |
| `bundled/tool-progress-zh` | 工具進度氣泡繁中（改部署端 display.py） |
| `bundled/agnes-image-generation` | Agnes 免費生圖 |
| Superpowers | apply 時自 GitHub `obra/superpowers` 釘 tag clone（未內嵌以控制體積） |

Office／frontend 技能從釘版 `anthropics/skills` 複製（不是作者機器、也不是未釘的 Hub）。

## Repository layout

```text
SKILL.md                      Agent 可載入之技能規格
scripts/baseline.py           check / apply 實作
scripts/test_isolation.py     測試目錄套用時，正在用的安裝維持原樣
bundled/                      隨包附屬技能與補丁（不靠作者本機）
references/
  PINNED_SOURCES.md           第三方釘版清單
  MANUAL_STEPS.md             部署手冊
  TELEGRAM_RICH.md            表格／rich／streaming／三層驗證＋紅線細節
  WRITING_ZH.md               對外中文文案下限
  DELIVERY_QA.md              檔案交付視覺 QA＋驗證原則
  MULTI_AGENT_RULES.md        多 agent 共同規則管理
  NETWORK_SOURCES.md          依賴：隨包 + 網路 only
  API_KEYS_BROWSER.md         瀏覽器金鑰流程
  SOUL-TW.md                  行為基線
  MEMORY-SNIPPET.md           記憶摘要
  PRELOAD_SKILLS.md           預裝政策
  DECISIONS.md                設計決策摘要
LICENSE
README.md
```

---

## Changelog

版本由舊到新：

### [v1.0.0](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.0.0) — 2026-08-05

首發：雙 profile、台灣時區／繁中、AnySearch／OpenRouter 方向、預裝與主機常駐基線。

### [v1.1.1](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.1.1) — 2026-08-06

乾淨電腦可 apply：發行包附 `bundled/`（選單繁中、Agnes）；繁中補丁不再寫死絕對路徑。

### [v1.1.2](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.1.2) — 2026-08-06

網路優先依賴：不依賴作者本機 skill；來源表寫入 `NETWORK_SOURCES.md`。

### [v1.3.0](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.3.0) — 2026-08-25（**Latest**）

表格紅線細節（2026-08-24 定案）、視覺 QA 檔位紅線、對外中文文案下限（`WRITING_ZH.md`）、多 agent 共同規則（`MULTI_AGENT_RULES.md`）、金鑰與通道管理、Chrome 分頁衛生、工具回報 ≠ 事實驗證原則。可先在測試目錄套用；預裝來源鎖定版本。

### [v1.2.0](https://github.com/s94084sammy/hermes-tw-setup/releases/tag/v1.2.0) — 2026-08-11

表格穩定（rich 開、streaming 關）、三層驗證、`tool-progress-zh`、網路 only 依賴，以及文件釘 tag 安裝說明。

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

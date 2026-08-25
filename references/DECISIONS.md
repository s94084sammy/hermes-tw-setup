# hermes-tw-setup 定案摘要

日期：2026-08-05

## ID 與名稱

- Skill：`hermes-tw-setup`（台灣 Hermes 通用設定）
- Profile：`default`（主助理）、`side`（副助理）

## 架構

- 技能：`side` → `skills.external_dirs: [~/.hermes/skills]`
- Cron：per-profile 獨立
- 模型：主副同一套 model + fallback_providers
- Telegram：兩隻 bot、兩份 token；附 BotFather 教學
- 平台：macOS、Windows、Linux 主機基線都要

## 搜尋／模型

- AnySearch 匿名預設；修 provider 強制 key 問題
- OpenRouter 備援；榜源 openrouter.ai/apps/hermes-agent 前 10；CDP 必抓到

## 流暢與安全

- 不過度審查；Hermes 預設安全即可
- display.language zh-TW；telegram-commands-zh；SOUL 繁中

## 語音

- 可選，不強迫

## 預裝延伸（2026-08-06）

- **Superpowers** 工作方法技能包：預裝到 skills/superpowers
- **強化記憶**：memory.provider = holographic（本機 SQLite、免 API key）；memory_enabled 開
- **不做 skill 裁剪**：一般人太難；bundled 全留

## 定稿與公開（2026-08-06）

- 該自動的要自動；該人手的**至少都要有完整指令**（MANUAL_STEPS.md + check 未過印 hint）
- 公開 GitHub 專案：台灣 Hermes Agent 初始最佳化設定技能（無私密、無客戶資料）

## 交付與 Telegram（2026-08-06）

- Telegram **rich_messages: true**（表格優先原生渲染）
- 交付後**與使用者確認**是否符合需求
- 檔案交付前必派 **subagent 純視覺 QA**（看圖驗收；**不是**規定檔案要由 subagent 產出）

## Telegram Rich 表格（補充）

- 官方預設 rich_messages=false；基線 true + 重啟 gateway
- 踩坑寫入 TELEGRAM_RICH.md／MANUAL_STEPS（表前空行、分隔列、路徑、rich_drafts 等）

## v1.2.0（2026-08-11）— 表格穩定 + 進度繁中

- **Telegram streaming 預設關**（`streaming.enabled: false` + `display.platforms.telegram.streaming: false`）
- **rich_drafts: false** 寫死建議
- **三層驗證**寫入 TELEGRAM_RICH／SOUL：設定＋API＋目視
- **bundled/tool-progress-zh**：工具進度標籤繁中（不依賴作者本機；改部署端 display.py）
- Superpowers 僅 **釘版本的 git clone**（文件不再寫「從作者本機複製」）
- `tool_progress: none` 視為無效值，apply 改寫成明確 `all`
- **Latest tag：`v1.2.0`**（接在 `v1.1.2` 之後）

## v1.3.0（2026-08-25）— 紅線補齊 + 行為下限

- **表格紅線細節**（2026-08-24 定案）：表前必空行、格內禁粗體／斜體、單格 ≤ 約 20 字、欄數 ≤ 4、每行以 `|` 開頭、逐表自檢；寫入 TELEGRAM_RICH 第 5 節
- **視覺 QA 檔位紅線**（2026-08-10 裁示）：最高檔模型、禁抽樣、機械過關不算、禁自評；斷線重派不豁免（2026-08-25 實戰）；寫入 DELIVERY_QA
- **工具回報 ≠ 事實**：寄信／發布／寫入後驗證落庫或讀端（2026-08 寄信事故）；寫入 DELIVERY_QA 第 5 節
- **對外中文文案下限**：新增 `WRITING_ZH.md`——中文母語模型加寫、禁寫作術語／中文破折號／AI 排比、溝通三段式
- **金鑰與通道管理**（2026-08-23 裁示）：金鑰單一來源、變數只增不改名、通道禁混用；寫入 SKILL 七之二
- **Chrome 分頁衛生**（2026-08-22 裁示）：分頁用完必關、任務鎖不關；寫入 SKILL 七之三
- **多 agent 共同規則**：新增 `MULTI_AGENT_RULES.md`——單一來源、短核＋索引按需載入、每日蒸餾
- 上述為行為規範文件與 SOUL 更新
- 測試目錄與正式安裝分開：`--hermes-home` 只寫指定目錄
- 預裝來源鎖定版本（見 `PINNED_SOURCES.md`）
- **Latest tag：`v1.3.0`**（累積式；舊基線不變）

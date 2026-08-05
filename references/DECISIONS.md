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

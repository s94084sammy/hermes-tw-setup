# 追加到 memories/MEMORY.md（去重後寫入）

- 本機為台灣 Hermes 基線：時區 Asia/Taipei；介面與回覆繁中（zh-TW）。
- 雙助理：主 default、副 side；技能庫共用 `~/.hermes/skills`；排程各自獨立；**模型設定共用**；**Telegram bot 不同**。
- 搜尋預設 AnySearch（可匿名免 API）；備援優先免 API（ddgs 等）。
- 主模型為訂閱 OAuth（Codex 或 xAI SuperGrok／Heavy Build 擇一）；OpenRouter 為 fallback；模型只從前 10（openrouter.ai/apps/hermes-agent 本月 Hermes 用量榜）選，須瀏覽器抓榜。
- 可關螢幕、禁止系統休眠；gateway 開機自啟；Chrome DevTools MCP 必可用。
- 行為：不輕易拒絕、不腦補意圖、先查再做、看實檔；不過度審查；安全維持 Hermes 預設。
- 免費生圖預設 Agnes AI（`AGNES_API_KEY` + 技能 agnes-image-generation）。
- 排版／資訊圖生圖：frontend-design、canvas-design、algorithmic-art + CDP 截圖；氛圍圖用 Agnes。
- OpenRouter／Agnes 的 API key：agent 用**已 Google 登入**的 Chrome（CDP）自取並寫入 .env；不處理 Telegram bot 自動申請。
- 取 OpenRouter／Agnes key：只准 attach 使用者已登入 Chrome（CDP）；禁止陌生／無痕瀏覽器；Chrome/CDP 限制要克服見 API_KEYS_BROWSER.md。
- 預裝 Superpowers 技能包；強化記憶預設 holographic（本機 SQLite）。不強制裁剪 skill。

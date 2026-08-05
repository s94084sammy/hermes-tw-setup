# 用已登入瀏覽器自取 API Key（OpenRouter、Agnes）

## 鐵則（給 agent）

1. **不處理 Telegram bot token**（那兩個 bot 仍由使用者用 BotFather 建立，或另案教學）。
2. **OpenRouter** 與 **Agnes** 的 key：agent 應能**自己透過瀏覽器**完成取得並寫入 `.env`。
3. **預設假設使用者用 Google 登入**上述網站（註冊／登入都走 Google）。
4. **一定要操控「已登入」的瀏覽器**：
   - 使用 **Chrome DevTools MCP 接到已開的 CDP**（常見 `http://127.0.0.1:9222`）。
   - Chrome 必須帶 **固定 user-data-dir**（使用者日常 Google 帳號已登入的那份 profile）。
   - **禁止**為了拿 key 另開無痕、空 profile、或沒掛 user-data-dir 的 headless（會沒有 Google 登入態）。
5. 寫入 `.env` 後**不要在對話中完整貼出 key**；只回報「已寫入 OPENROUTER_API_KEY／AGNES_API_KEY」。

## 主機：已登入 Chrome + CDP

Linux 範例（與常見 Hermes 設定一致）：

```text
google-chrome \
  --user-data-dir=$HOME/.config/google-chrome-personal \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check
```

- macOS／Windows：同樣要「固定使用者資料目錄 + remote debugging port」，路徑依系統調整。
- `config.yaml` 的 chrome-devtools MCP：`--browserUrl http://127.0.0.1:9222`（或實際埠）。
- check：CDP `/json/version` 可連；MCP 已掛。

使用者首次：用這顆 Chrome **手動 Google 登入一次** Gmail／OpenRouter／Agnes 即可；之後 agent 只 attach，不再叫使用者重複登入（除非 session 過期）。

## 流程 A：OpenRouter（備援模型）

1. 確認 CDP 已連上**已登入 profile**。
2. 開頁：`https://openrouter.ai/settings/keys`（未登入會被導向登入；點 **Continue with Google**）。
3. 若出現 Google 帳號選擇器：選使用者預設帳號；若要 2FA，**等使用者在同一視窗完成**，agent 不要略過。
4. 登入後在 Keys 頁：
   - 已有可用 key → 用「複製」取得（DOM 讀取或點 Copy 後從剪貼簿／頁面狀態讀，以實際 UI 為準）。
   - 沒有 → Create Key → 命名如 `hermes` → 建立後**立刻複製**（有的 UI 只顯示一次）。
5. 寫入**主與副** profile 的 `.env`（兩邊共用模型／備援）：
   - `OPENROUTER_API_KEY=...`
6. 用瀏覽器打開 `https://openrouter.ai/apps/hermes-agent`，讀「Top models used by Hermes Agent this month」**前 10**，選一個寫入 `fallback_providers`（主副相同）。
7. 自檢：`hermes` 能用 openrouter 當 fallback（或至少 key 非空且 config 有 fallback 條目）。

## 流程 B：Agnes（免費生圖）

1. 同一顆**已登入 Google 的 Chrome（CDP）**。
2. 開頁：`https://platform.agnes-ai.com` → Settings → API Keys（或文件現行路徑）。
3. **Google 登入**（與上面同一帳號為佳）。
4. 建立或複製 API key。
5. 寫入主（與需要生圖的 profile）`.env`：
   - `AGNES_API_KEY=...`
6. 確認技能 `agnes-image-generation` 已安裝；生圖預設走 Agnes。

## 失敗處理

| 情況 | 做法 |
|------|------|
| CDP 連不上 | 先啟動帶 user-data-dir 的 Chrome，再重試 MCP |
| 開到空白登入頁、沒 Google session | 請使用者在**這顆**瀏覽器手動登入 Google 一次，agent 再繼續（不要換無痕） |
| UI 改版找不到按鈕 | 截圖 + 用當頁 DOM 搜尋 “API” “Create” “Key” “Google” |
| 只要一輪使用者介入 | 僅限 Google 2FA／同意畫面；key 仍由 agent 複製寫入 |

## apply 腳本與 agent 分工

- `baseline.py apply`：裝 skill、修 config、確保 Chrome MCP／CDP 檢查。
- **真正點網頁拿 key**：由執行中的 Hermes agent 依本文件用瀏覽器完成（腳本不代替真人 Google 同意，但應自動做到「能駕馭已登入瀏覽器並完成複製寫入」）。
- 使用者一句「幫我把 OpenRouter／Agnes key 弄好」→ agent 必走本文件，不得只丟註冊連結就停。


## 鐵則補強：只能用「使用者的瀏覽器」

1. **禁止**為了省事開「陌生瀏覽器」：無痕、空 profile、Hermes 預設 `~/.hermes/chrome-debug`（若未登入 Google）、Browserbase／雲端瀏覽器、或 headless 乾淨實例去申請 key。
2. **必須** attach 到使用者日常會登 Google 的那顆 Chrome（固定 `user-data-dir` + CDP）。
3. 官方 Hermes 也支援 `/browser connect` 接到本機 Chromium 系；取 key 時**優先 CDP attach 已開實例**，不要讓 Hermes 隨手 auto-launch 一個沒登入的新 profile。
4. 模型被卡住時：先查限制表、克服後再繼續，**不要**改用陌生瀏覽器「繞過去」。

## Chrome／CDP 常見限制與克服（上網＋實務整理）

| 限制 | 原因 | 怎麼克服 |
|------|------|----------|
| 預設 profile 開不了 debugging port | Chrome 桌面版（約 150+）要求 **非預設** user-data-dir 才能 `--remote-debugging-port` | 固定用例如 `~/.config/google-chrome-personal`（或使用者專用目錄），**不要**用系統預設 `~/.config/google-chrome` |
| 已開著一般 Chrome，再加 flag 沒用 | 新視窗會併進**已存在、沒開 CDP** 的 process，9222 永遠不出現 | 關閉該 profile 的 Chrome 後，用「user-data-dir + remote-debugging-port」**同一條指令**重開；或用 systemd 常駐該 profile |
| auto-launch 開到空 profile | Hermes 預設常 launch `~/.hermes/chrome-debug` 等乾淨目錄，**沒有**使用者 Google cookie | 取 OpenRouter／Agnes key 時**禁用**這條；改接已登入 port（config `browser.cdp_url`／MCP browserUrl） |
| Google 登入／2FA 要真人 | 安全驗證不能代過 | 同一視窗等使用者完成；完成後 agent 繼續，不換瀏覽器 |
| 分頁太多、MCP connect 逾時 | 凍結分頁／大量 tab 拖垮 CDP | 關掉無關分頁後重連；`list_pages` 後選對 tab；重啟 CDP Chrome 服務 |
| 元素點不到、Shadow DOM | 一般 click 失效 | `evaluate_script`／Playwright 接同一 CDP／`browser_cdp` 原生命令 |
| UI 改版找不到「Create Key」 | 網站改版 | 截圖 + 頁內搜尋 API／Key／Create；必要時 `web_search` 查最新設定路徑 |
| WSL／容器連不到 host 9222 | 網路命名空間 | Docker 用 host 網路或正確 gateway；CDP URL 用 host 可達位址 |
| CDP 長連線不穩 | 資源／休眠 | 主機禁休眠（基線已要求）；斷線就重連再 list_pages |
| 複製 key 只顯示一次 | 安全設計 | 建立後**立刻**讀 DOM／剪貼簿寫入 `.env`，不要先關掉 modal |

## 啟動檢查清單（agent 拿 key 前必做）

1. `curl`／請求 `http://127.0.0.1:9222/json/version`（或設定的 port）必須成功。
2. 用 MCP `list_pages` 或開 `chrome://version` 確認 **Profile Path** 是使用者那份，不是陌生目錄。
3. 若 port 死掉：重啟「帶 user-data-dir 的」Chrome（systemd 或手動同一條命令），**不要**改開別的瀏覽器。
4. 確認 Google 帳號已在這 profile 登入（開 accounts.google.com 快速驗證）；未登入則請使用者在**這顆**完成 Google 登入。
5. 再執行 OpenRouter／Agnes 取 key 流程。

## 對模型的明確禁止

- 禁止：「我開一個無頭瀏覽器幫你註冊」當取 key 主路徑。
- 禁止：因 CDP 難用就放棄改成「請使用者自己複製貼上」就結束（可請使用者只完成 2FA；key 仍應由 agent 在已登入瀏覽器寫入）。
- 禁止：把雲端瀏覽器 session 當已登入的使用者 Google 環境（除非使用者明確授權且該環境已登入同一 Google）。

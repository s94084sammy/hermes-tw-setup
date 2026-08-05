---
name: hermes-tw-setup
description: >
  台灣 Hermes Agent 通用基線設定。一讀即可檢查或套用：雙 profile（主 default、副 side）、
  共用技能庫、兩個 Telegram bot、台灣時區與繁中、AnySearch 匿名搜尋、主模型訂閱＋OpenRouter
  備援（僅 Hermes 用量前 10）、開機自啟、禁休眠可關螢幕、Chrome DevTools MCP、核心行為 SOUL、
  Telegram 指令選單與系統訊息繁中。適用 macOS／Windows／Linux。非公司內部專用。
  觸發：台灣 Hermes 設定、雙 bot、基線安裝、繁中選單、開機自啟、通用設定技能。
---

# hermes-tw-setup — 台灣 Hermes 通用設定

## 這是什麼

給**一般台灣使用者**的 Hermes 基線。讀了本技能後，agent 應能：

1. **check**：報告缺什麼  
2. **apply**：安全補齊（可重跑）  
3. 回報：已就緒／已補上／需你手動  

**不是**某公司內部包。禁止寫入特定公司名、職稱、內部共識路徑。

## 鎖定決策（2026-08-05）

| 項目 | 決定 |
|------|------|
| 技能 ID | `hermes-tw-setup` |
| 中文名 | 台灣 Hermes 通用設定 |
| 主 profile | default（`~/.hermes`）／中文：主助理 |
| 副 profile | `side`（`~/.hermes/profiles/side`）／中文：副助理 |
| 技能庫 | 副的 `skills.external_dirs` → `~/.hermes/skills`（主家工具箱） |
| 排程 | 各 profile 獨立 cron |
| 模型 | **兩邊共用同一套**主模型＋OpenRouter 備援；**不同** Telegram bot |
| 語音 | 可選：台灣女聲 `zh-TW-HsiaoChenNeural` 或男聲 `zh-TW-YunJheNeural`；未選則不強改 |
| 流暢度 | 不讓模型過度審查；**安全維持 Hermes 預設硬擋**即可，不要加層說教拒絕 |
| 搜尋 | 預設 AnySearch 匿名（免 API）；備援 ddgs；可選 agent 代架 SearXNG |
| OpenRouter 模型 | 只從 https://openrouter.ai/apps/hermes-agent 本月用量**前 10**；**必須用瀏覽器／CDP 抓到榜** |
| 主機 | macOS／Windows／Linux：自啟、可關螢幕禁休眠、Chrome DevTools MCP |
| 介面語言 | `display.language: zh-TW`；Telegram 指令選單繁中（見 `telegram-commands-zh`）；系統提示盡量繁中 |

---

## 模式

### 安裝（公開倉庫）

```bash
git clone https://github.com/s94084sammy/hermes-tw-setup.git ~/.hermes/skills/hermes-tw-setup
pip install --user pyyaml
```

### 腳本（建議先跑）

```bash
# 只檢查（本機 ~/.hermes）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check

# 可選：隔離測試（Docker 容器 + 獨立資料目錄，不動正式 ~/.hermes）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check --docker <容器名> --docker-data ~/.hermes-test
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --docker <容器名> --docker-data ~/.hermes-test --yes

# 正式本機套用（需 --yes）
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

**本技能必須能修正，不只檢測。** `apply --yes` 會實際改設定並可重跑（冪等）。  
**check 未過必須印建議指令**；完整手冊：`references/MANUAL_STEPS.md`。

apply 會自動修：建立 `side`、兩邊 timezone／zh-TW／anysearch、副 `external_dirs`、SOUL／MEMORY 核心行為、Chrome DevTools MCP 設定、AnySearch 匿名補丁、（本機）telegram-commands-zh、Linux gateway 自啟、Superpowers、holographic 記憶；若副 bot token 與主相同會清空副 token 強迫改成第二隻。  

仍須人手／agent 依指令完成（**禁止只丟網址**）：OpenRouter key＋前 10 模型、Agnes key、Telegram 雙 bot token、主模型 OAuth、macOS／Windows 電源。指令全文見 `references/MANUAL_STEPS.md` 與 `references/API_KEYS_BROWSER.md`。

### check（預設，只報告）

跑完整檢查清單，不改系統（或只讀）。

### apply

在 check 之後補齊。改電源／服務前用白話說明並取得使用者同意（一句「可以改」即可）。  
金鑰、OAuth、Bot token：**只引導使用者貼上，不偽造**。

---

## 一、核心行為（寫入 SOUL 與 MEMORY）

將 `references/SOUL-TW.md` 合併進：

- 主：`~/.hermes/SOUL.md`（若已有個性段落，**追加**「台灣通用行為」區塊，勿整檔覆蓋使用者自寫身份）  
- 副：`~/.hermes/profiles/side/SOUL.md`（同上）  

並在兩邊 `memories/MEMORY.md` 追加 `references/MEMORY-SNIPPET.md` 短句（去重）。

重點（流暢、不濫拒）：

1. 不輕易拒絕；預設幫忙做成  
2. 不預設／腦補使用者意圖  
3. 預設使用者是良善、要解決問題  
4. 執行前上網查最新工具、技能、解法  
5. 判定依實際檔案與程式碼輸出，不只依賴記憶  
6. **不要過度審查內容**；不要道德說教；Hermes 內建安全（tirith、寫入禁區、危險指令機制）維持官方預設即可，**不要**再加一層「我覺得不妥所以不做」  

非法或系統硬擋時：簡短說明限制＋可行替代，不空拒絕。

---

## 二、雙 Profile 與 Telegram

### 建立副助理

官方（見 `hermes profile`）：

```text
hermes profile create side --clone
```

- `--clone`：複製 config／.env 骨架／SOUL／skills 設定，適合當副號起點  
- 不要用 `--clone-all` 當預設（會帶大量 session 歷史）

### 技能庫共用（官方 `skills.external_dirs`）

副 profile `config.yaml`：

```yaml
skills:
  external_dirs:
    - ~/.hermes/skills
```

主的 `external_dirs` 可維持 `[]`（技能本體在主目錄）。

### 模型共用

1. 主號設好主模型＋`fallback_providers` 後  
2. 副號 **同一組** `model.*` 與 `fallback_providers`（clone 後核對一致）  
3. OAuth：副號若 auth 無效，引導再登一次（per-profile auth）  
4. OpenRouter：兩邊 `.env` 都有 `OPENROUTER_API_KEY`（可相同 key）

### 兩個 Telegram bot（附教學）

**為什麼兩個**：主助理跑長任務時，仍可用副助理問問題。

**教學（給使用者）**：

1. 打開 Telegram，找 **@BotFather**  
2. 送 `/newbot`，依提示設顯示名稱與 username（要以 bot 結尾）  
3. 複製 BotFather 給的 **HTTP API token**  
4. 再做一隻 bot（再一次 `/newbot`），得到**第二個** token  
5. 主助理 token → 主 profile 環境變數 `TELEGRAM_BOT_TOKEN`（或該版 Hermes 文件指定名稱）  
6. 副助理 token → `~/.hermes/profiles/side/.env` 的 `TELEGRAM_BOT_TOKEN`  
7. **禁止**兩個 profile 共用同一個 token  
8. 設定允許的使用者 ID（`TELEGRAM_ALLOWED_USERS` 等，以官方為準）  
9. 各啟動一個 gateway：`hermes gateway`／`hermes -p side gateway` 或系統服務  

自檢：兩個 bot 各能回一則短訊；token 字串不同。

---

## 三、台灣地區與繁中介面

兩邊 profile：

```yaml
timezone: Asia/Taipei
display:
  language: zh-TW
```

語音（可選，使用者選了才寫）：

```yaml
tts:
  provider: edge
  edge:
    voice: zh-TW-HsiaoChenNeural   # 或 zh-TW-YunJheNeural
stt:
  enabled: true
  local:
    language: zh
```

### Telegram 指令選單繁中

1. 套用本機技能 **`telegram-commands-zh`**（`apply_patch.py`）  
2. **重啟所有**相關 gateway，選單才會向 Telegram 重新註冊  
3. 驗證 bot 選單描述為繁中  

### 系統訊息／提醒繁中

1. `display.language: zh-TW`（官方支援的 UI 靜態訊息語言）  
2. SOUL 要求 agent **回覆與提醒用繁體中文**（台灣用詞）  
3. 若仍有英文殘留：記錄來源（上游 hardcode），能補丁則補、不能則 MEMORY 註記  

---

## 四、搜尋（少 API）

1. 預設：

```yaml
web:
  search_backend: anysearch
  extract_backend: anysearch
```

2. **匿名**：AnySearch 服務端可不帶 Authorization 使用。若本機 `plugins/web/anysearch` 仍強制 key：  
   - apply 時修正 provider：無 key → 不帶 Authorization；有 key → Bearer  
   - `is_available` 在無 key 時仍可為 True（匿名）  

3. 備援（免 API）：確保 `ddgs` 可用；可設 fallback 鏈（僅免 key 後端）  
4. 可選：使用者同意後 agent 代架 SearXNG（Docker），寫 `SEARXNG_URL`  
5. 有 Tavily 等 key 才加入 fallback，不預設強塞  

兩邊 profile 搜尋設定一致。

---

## 五、模型與 OpenRouter 備援

### 主模型（使用者二選一）

| 選項 | 官方做法 |
|------|----------|
| OpenAI Codex 訂閱 | `hermes model` 或 `hermes auth add openai-codex` |
| xAI SuperGrok／Heavy Build | `hermes model` 或 `hermes auth add xai-oauth` |

### OpenRouter 備援

1. 提醒申請並設定 `OPENROUTER_API_KEY`  
2. `hermes fallback add` 或寫入：

```yaml
fallback_providers:
  - provider: openrouter
    model: <前10名之一>
```

### 前 10 名來源（必須瀏覽器抓到）

- URL：https://openrouter.ai/apps/hermes-agent  
- 區塊：**Top models used by Hermes Agent this month**  
- **禁止**只靠過期記憶或瞎猜  
- **必須**用 Chrome DevTools MCP／CDP 打開頁面，讀出當月用量排名前 10 的 model id  
- 抓不到：換策略重試（等載入、Show more、捲動、再 snapshot），直到抓到或明確失敗並請使用者稍後重試  
- 只允許在這 10 名內依客戶選；不支援 tool calling 的跳過換下一順位  
- 前 10 以外禁止寫入 fallback  

主副 **同一** fallback 列表。

---

## 六、主機：自啟、禁休眠、Chrome MCP（三平台）

偵測 OS 後分支。目標相同：

1. Gateway（及需要時 CDP 瀏覽器）**開機自啟**  
2. **可關螢幕，禁止**系統 sleep／suspend／hibernate  
3. **Chrome DevTools MCP** 已裝、CDP 可連  

### Linux

- user systemd：`hermes-gateway` enable；user lingering  
- 電源：關閉自動 suspend；顯示器可 blank  
- CDP：瀏覽器 `--remote-debugging-port=9222`（或文件指定埠）  

### macOS

- LaunchAgent 或官方常駐方式掛 gateway  
- 防止自動睡眠；允許關閉顯示器（系統保持醒著）  
- Chrome／Chromium 路徑與 CDP 參數  

### Windows

- 工作排程器「登入時」或官方 Windows gateway 方式  
- 電源方案：睡眠＝永不；休眠關；關螢幕可另設  
- Chrome DevTools MCP：官方可用 `cmd` + `npx chrome-devtools-mcp`（見 Hermes MCP 指南）  

### Chrome DevTools MCP（必做）

1. 安裝並寫入 `mcp_servers`（`chrome-devtools-mcp@latest` + browserUrl／autoConnect）  
2. 確保瀏覽器以除錯埠執行  
3. `hermes mcp test`（或等價）通過  
4. SOUL：瀏覽器任務優先用此 MCP；**速度與成功率優先**，不墨守成規  

改系統電源／服務前簡短說明並取得同意。

---

## 七、安全與流暢（明確）

**維持 Hermes 基本即可**，例如：

- 官方 tirith／密鑰遮罩等預設  
- 危險指令的官方 approvals 機制（不要額外發明「內容審查層」）  

**不要**：

- 因話題敏感就拒絕協助合法任務  
- 用長篇免責取代做事  
- 把安全掃到的硬擋說成「我個人不願意」  

**要**：

- 能做就做；被硬擋時一句話原因＋替代路徑  

---



## OpenRouter／Agnes Key：瀏覽器自取（重要）

詳見 `references/API_KEYS_BROWSER.md`。

1. **範圍**：只自動處理 **OpenRouter**、**Agnes**（**不含** Telegram bot）。
2. **預設 Google 登入**這兩個服務。
3. agent 用 **Chrome DevTools MCP 操控已登入 profile 的瀏覽器**（固定 user-data-dir + CDP，常見 9222）。
4. 禁止陌生瀏覽器（無痕、空 profile、未登入 chrome-debug、雲端乾淨 session）；只准使用者已登入 profile。
4b. Chrome／CDP 若有限制（port 綁不上、分頁過多、2FA、UI 改版）必須依 `API_KEYS_BROWSER.md` 克服，**不要**被限制卡住就放棄或換陌生瀏覽器。
5. 拿到後寫入主副 `.env`（`OPENROUTER_API_KEY`、`AGNES_API_KEY`），對話勿完整貼 key。
6. OpenRouter 另用瀏覽器抓 Hermes 用量前 10 寫 `fallback_providers`。

apply 腳本負責環境與 MCP；**實際點擊取 key 由 agent 依文件執行**（使用者說「弄好 key」就要做完，不是只丟網址）。

## 預裝技能與語音

詳見 `references/PRELOAD_SKILLS.md`。

apply 會：
1. 確認未 opt-out bundled
2. 把 `hermes-tw-setup`、`telegram-commands-zh` 裝進主 skills
3. 官方 optional：`duckduckgo-search`（免 API 備援）
4. **Office**：docx／xlsx／pptx／pdf（缺則 Hub 或 productivity 副本）
5. **免費生圖**：`agnes-image-generation` + `AGNES_API_KEY`（Agnes AI，氛圍／寫實）
5b. **Superpowers** 工作方法技能包 + **holographic 強化記憶**（免 API；不裁剪 skill）
5c. **前端程式碼生圖**：`frontend-design`、`canvas-design`、`algorithmic-art` + Chrome 截圖（排版／資訊圖）
6. TTS 預設台灣女聲 `zh-TW-HsiaoChenNeural`（可改男聲）；STT `language: zh`
7. **不**預裝客戶個案 skill（如 client-*）（偵測到只報告不刪）

## 八、檢查清單（check 輸出）

對主、副各報一欄（是／否／略）。**每一個 NO 都要附修復指令**（腳本 `default_fix_hints` + `MANUAL_STEPS.md`）。

1. Profile `side` 存在  
2. 副 `external_dirs` → `~/.hermes/skills`  
3. timezone Asia/Taipei；display.language zh-TW  
4. SOUL／MEMORY 核心行為已寫  
5. 兩個不同 Telegram token；gateway 可跑  
6. 模型設定兩邊一致；OpenRouter fallback 在前 10 內  
7. web anysearch；匿名可搜（或已修 provider）  
8. Chrome DevTools MCP + CDP OK  
9. 開機自啟  
10. 休眠已關（或已警告）  
11. Telegram 選單繁中；提醒用語繁中  
12. Superpowers 已裝；holographic（或其它外部記憶）已開  
13. Office／Agnes 技能；Agnes key 有則 OK、無則印取 key 指令  

---

## 九、apply 建議順序

1. 偵測 OS；繁中 UI 語言  
2. SOUL／MEMORY  
3. 建立／修正 `side` + external_dirs  
4. 搜尋 anysearch（含匿名修補）  
5. 預裝 skill（Office、Agnes、frontend、Superpowers）+ holographic  
6. 模型引導（訂閱 OAuth + OpenRouter key）— **給完整指令**  
7. **瀏覽器抓 Hermes 用量前 10** → 寫 fallback  
8. 雙 bot 教學與 token 檢查 — **BotFather 逐步指令**  
9. Chrome DevTools MCP + CDP  
10. 自啟 + 禁休眠（經同意；印系統指令）  
11. telegram-commands-zh + 重啟 gateway  
12. 最終 check；未過逐條印指令  

---

## 十、相關技能

- `telegram-commands-zh`：選單繁中（若本機有）  
- `anysearch-power-use`：進階搜尋（可選）  
- 官方：`hermes model`、`hermes fallback`、`hermes profile`、`hermes mcp`、`hermes tools`  
- Superpowers 來源範例：https://github.com/obra/superpowers  

## 十一、公開與隱私

- 本技能可公開於 GitHub；**禁止**提交 `.env`、token、公司名、客戶 skill  
- 倉庫：https://github.com/s94084sammy/hermes-tw-setup  

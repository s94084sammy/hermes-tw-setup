# 開箱必做指令手冊（台灣 Hermes 通用基線）

apply 腳本會自動修「能改設定檔／裝 skill」的項目。  
**下列項目必須有指令、agent 也要照做或提醒使用者照做**，不能只說「請自己搞定」。

本檔是**完整指令**；細節還可對照 `API_KEYS_BROWSER.md`。

---

## 0. 安裝本技能

```bash
# 方式 A：從 GitHub 複製到 Hermes 技能目錄
git clone https://github.com/s94084sammy/hermes-tw-setup.git ~/.hermes/skills/hermes-tw-setup

# 方式 B：已有目錄則更新
cd ~/.hermes/skills/hermes-tw-setup && git pull

# 依賴
pip install --user pyyaml

# 檢查／套用
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

未過項目會印「建議指令」；本檔是完整版。

---

## 1. 主模型 OAuth（二選一訂閱）

```bash
# 互動選模型（推薦）
hermes model

# 或明確加登入
hermes auth add openai-codex    # ChatGPT／Codex 訂閱
# 或
hermes auth add xai-oauth       # xAI SuperGrok／Heavy Build

# 副 profile 若 auth 分開：
hermes -p side model
# 或
HERMES_HOME=~/.hermes/profiles/side hermes auth add openai-codex
```

自檢：`hermes` CLI 能正常對話；主副 `config.yaml` 的 `model` 區塊一致。

---

## 2. OpenRouter key ＋ Hermes 用量前 10 fallback

### 2a Key（agent 用已登入 Chrome／CDP）

1. 啟動已登入 profile 的 Chrome：

```bash
# Linux 範例（路徑可改成你的固定 user-data-dir）
google-chrome \
  --user-data-dir=$HOME/.config/google-chrome-personal \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check
```

2. 確認 CDP：

```bash
curl -s http://127.0.0.1:9222/json/version | head
```

3. 用 Chrome DevTools MCP 開：  
   `https://openrouter.ai/settings/keys`  
   Google 登入 → 建立／複製 key。

4. 寫入（**不要**在聊天完整貼 key）：

```bash
# 主
echo 'OPENROUTER_API_KEY=你的key' >> ~/.hermes/.env
# 副（同一 key 即可）
echo 'OPENROUTER_API_KEY=你的key' >> ~/.hermes/profiles/side/.env
```

### 2b 前 10 模型寫入 fallback

1. 瀏覽器開：`https://openrouter.ai/apps/hermes-agent`  
2. 讀 **Top models used by Hermes Agent this month** 前 10 的 model id  
3. 只准這 10 名內；寫入主副 `config.yaml`：

```yaml
fallback_providers:
  - provider: openrouter
    model: <前10名之一>
```

或：

```bash
hermes fallback add
# 再把同一組 fallback 同步到 side 的 config.yaml
```

自檢：

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check
# default.openrouter_fallback / side.openrouter_fallback 應為 OK
```

---

## 3. Agnes 免費生圖 key

```bash
# 已登入 Chrome（同上 CDP）開
# https://platform.agnes-ai.com → Settings → API Keys

echo 'AGNES_API_KEY=你的key' >> ~/.hermes/.env
```

技能：`agnes-image-generation`（apply 會裝）。  
詳見 `API_KEYS_BROWSER.md`。

---

## 4. 雙 Telegram bot

```text
1. Telegram 找 @BotFather
2. /newbot → 第一隻（主助理）→ 複製 token
3. 再 /newbot → 第二隻（副助理）→ 複製第二個 token
4. 兩隻 token 必須不同
```

```bash
# 主
# 編輯 ~/.hermes/.env
TELEGRAM_BOT_TOKEN=第一隻token
TELEGRAM_ALLOWED_USERS=你的Telegram數字ID

# 副
# 編輯 ~/.hermes/profiles/side/.env
TELEGRAM_BOT_TOKEN=第二隻token
TELEGRAM_ALLOWED_USERS=你的Telegram數字ID
```

查自己的數字 ID：Telegram 找 `@userinfobot` 或官方等價方式。

啟動 gateway：

```bash
# 前景測試
hermes gateway
hermes -p side gateway

# Linux 常駐（服務名依安裝為準）
systemctl --user enable --now hermes-gateway
# side 若有獨立 unit，一併 enable
```

自檢：兩個 bot 各回一則短訊。

---

## 5. Superpowers（若 apply 找不到來源）

```bash
git clone --depth 1 https://github.com/obra/superpowers.git /tmp/superpowers
# 上游結構若為 skills/ 子目錄：
mkdir -p ~/.hermes/skills
if [ -d /tmp/superpowers/skills ]; then
  rm -rf ~/.hermes/skills/superpowers
  cp -a /tmp/superpowers/skills ~/.hermes/skills/superpowers
else
  # 或已是扁平技能包
  rm -rf ~/.hermes/skills/superpowers
  mkdir -p ~/.hermes/skills/superpowers
  cp -a /tmp/superpowers/* ~/.hermes/skills/superpowers/ 2>/dev/null || true
fi
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

**不做 skill 裁剪**（bundled 全留）。

---

## 6. 強化記憶 holographic

apply 會寫；手動則編輯主副 `config.yaml`：

```yaml
memory:
  memory_enabled: true
  provider: holographic
```

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

---

## 7. Telegram 指令選單繁中

若本機有 `telegram-commands-zh`：

```bash
python3 ~/.hermes/skills/telegram-commands-zh/apply_patch.py
# 重啟所有相關 gateway 後選單才更新
systemctl --user list-units --type=service --state=running | grep hermes
# 範例（依實際服務名改）
systemctl --user restart hermes-gateway.service
```

---

## 8. 主機：自啟、禁休眠、Chrome CDP

### Linux

```bash
# Gateway 自啟（服務名依 Hermes 安裝）
systemctl --user enable --now hermes-gateway
loginctl enable-linger "$USER"

# 禁 suspend／hibernate（需 sudo，先徵求同意）
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# 已登入 Chrome + CDP（固定 user-data-dir）
google-chrome \
  --user-data-dir=$HOME/.config/google-chrome-personal \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check
```

### macOS

```bash
# Gateway：用 LaunchAgent 或 Hermes 官方常駐方式（以當版文件為準）
# 防睡眠（範例：接電源時）
caffeinate -s &
# 或：系統設定 → 電池／電源轉接器 → 防止自動進入睡眠

# Chrome CDP
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Personal" \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check
```

### Windows（PowerShell／cmd 概念）

```text
# 工作排程器：登入時啟動 hermes gateway（或官方 Windows 服務方式）
# 電源：
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /hibernate off

# Chrome CDP（路徑依安裝調整）
chrome.exe --user-data-dir="%USERPROFILE%\chrome-personal" --remote-debugging-port=9222
```

### Chrome DevTools MCP

`config.yaml` 應有 `chrome-devtools` MCP，browserUrl 指向 `http://127.0.0.1:9222`。  
自檢：`curl http://127.0.0.1:9222/json/version`、`hermes mcp test`（若有）。

---

## 9. 可選：SearXNG

```bash
# 使用者同意後
docker run -d --name searxng -p 8080:8080 searxng/searxng
# .env
echo 'SEARXNG_URL=http://127.0.0.1:8080' >> ~/.hermes/.env
```

---

## 10. 定稿自檢

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check
# 理想：未過 = 0；若仍有 NO，照輸出的 → 指令與本檔對應章節做完再 check
```

---

## Agent 義務（摘要）

| 項目 | 能否腳本代填 | Agent／使用者指令 |
|------|--------------|-------------------|
| side／zh-TW／anysearch／SOUL／MCP／Office／Superpowers／holographic | apply 代做 | `baseline.py apply --yes` |
| OpenRouter／Agnes key | 否（要 Google） | 已登入 CDP 瀏覽器自取，見 API_KEYS_BROWSER.md |
| OpenRouter 前 10 fallback | 否（要當日榜） | 開 hermes-agent 頁抓榜後寫 config |
| Telegram 雙 bot | 否 | BotFather + 寫 .env |
| 主模型 OAuth | 否 | `hermes model` / `hermes auth add …` |
| 禁休眠／自啟 | 半自動 | 本檔 §8；改電源前先問使用者 |

**禁止**：只丟網址沒指令；未過 check 卻不印修復指令。

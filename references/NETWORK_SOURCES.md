# 依賴來源：發行包 + 網路（不靠作者本機）

乾淨機器只要：

1. 從 **GitHub** 取得本技能（網路）  
2. 本機已裝 **Hermes**  
3. apply 時可連 **GitHub / Skills Hub**（網路）

**不需要**作者電腦上的 `~/.hermes/skills/*` 其它目錄。

## 來源表

| 項目 | 來源 | 類型 |
|------|------|------|
| `hermes-tw-setup` 本體 | `git clone` 本倉庫 | 網路 |
| `telegram-commands-zh` | 倉庫 `bundled/telegram-commands-zh` | 隨包（隨 git 下載） |
| `agnes-image-generation` | 倉庫 `bundled/agnes-image-generation` | 隨包 |
| Superpowers | `git clone https://github.com/obra/superpowers` | 網路 |
| Office docx/xlsx/pptx/pdf | `hermes skills install skills-sh/anthropics/skills/…` | 網路 Hub |
| frontend-design / canvas-design / algorithmic-art | 同上 Hub | 網路 Hub |
| duckduckgo-search | `hermes skills repair-official …` | 官方 optional |
| 設定／SOUL／rich_messages | 本技能 scripts + references | 隨包 |

## 允許的本機路徑（不是「作者技能庫」）

| 路徑 | 意義 |
|------|------|
| `$HERMES_HOME`（預設 `~/.hermes`） | **使用者自己的** Hermes 家目錄，apply 寫入目標 |
| `~/.hermes/hermes-agent/skills/productivity` | 該機器 Hermes 安裝附帶的 productivity（Hub 失敗時備援） |
| Docker `/opt/hermes/...` | 容器內 Hermes 安裝樹（`--docker` 測試） |

禁止當成必備來源：`~/.grok/skills`、作者 `~/.claude/plugins/cache`、其它 profile 的私有 skill。

## 離線限制

無網路時：仍可套用 config／SOUL／bundled 兩技能；Hub 與 Superpowers clone 會失敗並在 check 標 NO。

## 驗證乾淨安裝

```bash
# 新目錄模擬
git clone https://github.com/s94084sammy/hermes-tw-setup.git /tmp/hts-clean
export HERMES_HOME=/tmp/hermes-tw-clean-home
mkdir -p "$HERMES_HOME"
# 需有最小 config 或先 hermes 初始化
python3 /tmp/hts-clean/scripts/baseline.py apply --hermes-home "$HERMES_HOME" --yes
python3 /tmp/hts-clean/scripts/baseline.py check --hermes-home "$HERMES_HOME"
```

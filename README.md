# hermes-tw-setup

**台灣 Hermes Agent 通用初始最佳化設定**（公開技能）

給一般台灣使用者的一鍵檢查／套用基線：雙助理、繁中、免 key 搜尋、OpenRouter 備援規範、Office／生圖／Superpowers、強化記憶、主機自啟與 Chrome DevTools。

- **不是**任何公司內部包  
- **不含** API key、Telegram token、客戶資料  
- 密鑰與 OAuth **只引導指令**，不內建秘密

## 快速開始

```bash
# 需要已安裝 Hermes Agent：https://github.com/NousResearch/hermes-agent （或你使用的 Hermes 發行版）
git clone https://github.com/s94084sammy/hermes-tw-setup.git ~/.hermes/skills/hermes-tw-setup
pip install --user pyyaml

python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
```

未過項目會列出**建議指令**。完整開箱步驟：

- [`references/MANUAL_STEPS.md`](references/MANUAL_STEPS.md)  
- Key 用已登入瀏覽器自取：[`references/API_KEYS_BROWSER.md`](references/API_KEYS_BROWSER.md)

## 會自動套用什麼

| 項目 | 說明 |
|------|------|
| 雙 profile | 主 `default` + 副 `side`；技能庫共用；cron 獨立 |
| 台灣／繁中 | `Asia/Taipei`、`display.language: zh-TW` |
| 搜尋 | AnySearch 匿名（免 API）；ddgs 備援 |
| 行為 | SOUL／MEMORY 核心：不濫拒、查最新、依實檔判定 |
| 預裝 | Office、Agnes 生圖技能、frontend 生圖、Superpowers |
| 記憶 | `memory.provider: holographic`（本機、免額外套件） |
| 主機 | Linux 可 enable gateway；macOS／Windows 見手冊 |
| Chrome | DevTools MCP 設定；取 key 必須已登入 profile |

**不做 skill 裁剪**（一般人太難）。

## 仍須你（或 agent 依手冊）完成

1. 主模型 OAuth：`hermes model`（Codex 或 xAI）  
2. OpenRouter key + 從 [Hermes Agent 用量前 10](https://openrouter.ai/apps/hermes-agent) 寫 fallback  
3. Agnes key（免費生圖）  
4. 兩個不同的 Telegram bot token（@BotFather）  
5. 主機禁休眠／自啟（改系統前會要求同意）

## 目錄

```text
SKILL.md                 # 技能說明（給 agent 讀）
scripts/baseline.py      # check / apply
references/
  MANUAL_STEPS.md        # 開箱完整指令
  API_KEYS_BROWSER.md    # OpenRouter／Agnes 瀏覽器自取
  SOUL-TW.md             # 核心行為
  MEMORY-SNIPPET.md
  PRELOAD_SKILLS.md
  DECISIONS.md
LICENSE
README.md
```

## 設計原則

1. **能修就修**（apply 冪等），不只檢測  
2. **該人手的必有指令**，check 未過要印怎麼做  
3. 越少 API 越好；密鑰不進 git  
4. 繁中優先、台灣時區  

## 授權

MIT（見 `LICENSE`）。  
Superpowers 等第三方技能仍遵循其各自授權；本倉庫僅描述如何安裝。

## 免責

使用本技能產生的設定與行為，由使用者自行負責。請遵守 Hermes、OpenRouter、Telegram、各 API 服務條款。

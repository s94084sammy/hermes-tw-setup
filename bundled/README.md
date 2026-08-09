# bundled

公開發行內建、不依賴開發者本機 `~/.hermes/skills` 的附屬技能。

| 目錄 | 用途 |
|------|------|
| `telegram-commands-zh` | Telegram 選單繁中補丁 |
| `tool-progress-zh` | 工具進度氣泡繁中（執行程式／搜尋檔案…） |
| `agnes-image-generation` | Agnes 免費生圖 |

`baseline.py apply` 會優先從此目錄複製到 `$HERMES_HOME/skills/`，並執行對應 `apply_patch.py`。  
Superpowers 改由 GitHub `obra/superpowers` 在 apply 時 clone（體積較大，不進 bundle）。

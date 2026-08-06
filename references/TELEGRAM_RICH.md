# Telegram 富訊息（Rich Messages）與表格

台灣 Hermes 基線預設**開通** Bot API 10.1 富訊息，讓表格等結構能原生渲染。

## 設定（apply 會寫入）

```yaml
telegram:
  extra:
    rich_messages: true
```

官方文件亦可能寫在：

```yaml
gateway:
  platforms:
    telegram:
      extra:
        rich_messages: true
```

`baseline.py` 會同時確保 `telegram.extra.rich_messages: true`（主副 profile）。  
**改完需重啟 gateway** 才生效。

預設上游為 `false`（怕富訊息難複製純文字）；本基線選擇**可讀性優先、表格優先**，故 opt-in 為 true。

## 何時會走 rich

- 內容含合法 GFM pipe table（**必須有** `|---|` 分隔列）
- 任務清單、可折疊區塊、區塊數學等會被 MarkdownV2 降級的結構
- 長度在 Telegram rich 上限內（約 32768 字元）

失敗時閘道會退回 MarkdownV2（表格可能變 bullet 或 code block），訊息不應遺失。

## 寫表格規則（優先用表）

結構化、欄位固定的資料：**優先 Markdown pipe table**，不要只丟一長串點列。

```markdown
（表格前必須空一行）

| 項目 | 狀態 | 備註 |
|------|------|------|
| 時區 | OK | Asia/Taipei |
| 富訊息 | OK | rich_messages |
```

鐵則：

1. **表前空一行**（上一行不可是正文，否則整表不渲染）
2. 必須有分隔列 `|---|`
3. 單則過長（約 4096／rich 上限）會切段；長報告自行分段
4. 禁止 HTML `<table>` 手寫當唯一手段（交給閘道轉）；禁止無分隔列的假表

適合表：排行、對照、狀態清單、檢查結果、參數摘要。  
不適合表：超多欄（約 6 欄以上）且每行長敘述差異大 → 改短段落或 emoji 行格式。

## 自檢

送出前：每個以 `|` 開頭的資料列，其**前一行**必須是空行或同為表格列。

重啟後用一則含 pipe table 的訊息驗證：應看到**格子表**，不是 bullet 群。

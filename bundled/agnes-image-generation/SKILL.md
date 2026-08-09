---
name: agnes-image-generation
description: 使用 Agnes AI 免費 API 生圖（txt2img + img2img），免信用卡、OpenAI 相容格式
category: media
tags: [image, agnes, free, txt2img, img2img]
---

# Agnes AI 免費生圖

台灣 Hermes 基線預設的**免費生圖**路徑。使用者說生圖／產圖時優先用 Agnes，除非明確要求其他服務或 Agnes 失敗。

- 免費、免信用卡（以 Agnes 官網為準）
- Base URL: `https://apihub.agnes-ai.com`
- 模型：`agnes-image-2.1-flash`（以服務端為準）

## 前置

`.env` 設定 `AGNES_API_KEY`。申請：https://platform.agnes-ai.com → Google 登入 → Settings → API Keys

## 使用

```bash
python3 ~/.hermes/skills/agnes-image-generation/scripts/generate.py "prompt" --size 1024x768 --outdir /tmp/agnes-output
# 或技能目錄下 generate.py／scripts/generate.py（以實際安裝為準）
```

img2img 見腳本 `--image` / `--image-file` 參數。

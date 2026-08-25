# Agnes Image 2.1 Flash 能力摘要（2026-06-25）

來源：官方文件 `https://agnes-ai.com/doc/agnes-image-21-flash`、`https://agnes-ai.com/doc/agnes-image-20-flash`、官網 `https://agnes-ai.com`，以及本機 txt2img smoke test。

## 可生成 / 可處理的圖片類型

- Text-to-image：文字生圖。
- Image-to-image：依提示改造既有圖片，支援公開圖片 URL、Data URI Base64，或透過 wrapper 的 `--image-file` 直接送本機圖片。
- Multi-image composition：2.0 文件明列多圖組合；2.1 文件主打高資訊密度與 img2img，實作上腳本支援多個 `--image` URL 或多個 `--image-file`。
- 高資訊密度圖片：複雜場景、細節豐富構圖、行銷素材、產品視覺、封面、banner、縮圖、社群圖。
- 圖片轉換：風格轉換、換背景、換光線、保留構圖的場景重繪。

## 適合風格

官方未列固定 style enum；風格完全靠 prompt 控制。實務可用：

- 寫實 / 攝影：product photo、studio lighting、cinematic realism、lifestyle photo。
- 插畫 / 概念美術：concept art、fantasy、sci-fi、environment art。
- 海報 / 行銷：campaign visual、social media creative、thumbnail、banner、cover。
- 向量 / 扁平：flat vector、minimal icon、clean geometric layout。
- 動漫 / 賽博龐克：anime rendering、cyberpunk neon、rain-soaked night。
- 產品與電商：product mockup、hero image、contextual product scene。

## 檔案與回傳格式

- API 回傳格式：`data[0].url` 或 `data[0].b64_json`。
- txt2img Base64：用 top-level `return_base64: true`。
- img2img Base64：用 `extra_body.response_format: "b64_json"`。
- URL 輸出實測下載為 PNG；官方沒有保證可指定 JPG/WebP。
- 輸入圖片：公開 URL 或 Data URI Base64。

## 尺寸

- 官方示例：`1024x768`、`1024x1024`、`768x1024`。
- API 參數為 `size` 字串，文件稱 flexible/custom size，但未列完整允許清單；生產使用先以 1024 系列為安全值。

## 關鍵踩坑

- `response_format` 不可放頂層，必須放 `extra_body`。
- txt2img 不放 `image`。
- img2img 的 `image` 放 `extra_body.image`。
- 不要傳 `tags: ["img2img"]`。
- Base URL 是 `https://apihub.agnes-ai.com`，不是平台後台網址。
- API key 只放 profile `.env`，不要寫入 skill、文件、腳本或聊天回覆。

## 憑證狀態

- 憑證只放該機器 Hermes 家目錄的 `.env`；不可寫進 skill 文件、腳本、聊天回覆或 commit。
- 本倉庫不承載、不確認任何人的金鑰是否已存在。

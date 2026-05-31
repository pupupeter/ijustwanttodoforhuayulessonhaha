# 華語知識王 (Mandarin Pulse) — 開發

## 專案簡介
以 Flask 建立的華語學習遊戲平台，含題目練習、對戰配對、管理後台。

## 技術棧
- **後端**：Python + Flask
- **前端**：HTML + Tailwind CSS + Material Symbols
- **資料**：Excel 詞語表 / 語法點表 + JSON 手動題庫

---

## ✅ 已完成功能

### 頁面路由
| 路由 | 功能 |
|------|------|
| `/` | 首頁（進度、連勝、Topic Practice） |
| `/lobby` | 遊戲大廳（配對、難度、類型選擇） |
| `/settings` | 設定頁 |
| `/logout` | 登出（清除 session） |
| `/topic/<name>` | 主題頁（cuisine / shopping / tourism / worklife） |
| `/practice/<topic>/<type>` | 主題練習（voc / dia / lis） |
| `/start_game/<mode>` | 開始遊戲（mode 1/2/3） |
| `/start_game_lobby` | 從大廳開始（帶 level + category 參數） |
| `/quiz` | 答題頁（依模式選擇不同 template） |
| `/answer` | 提交答案（計時計分） |
| `/result` | 結果頁 |
| `/admin/questions` | 題目管理後台 |

### REST API（題目 CRUD）
| 方法 | 路由 | 功能 |
|------|------|------|
| GET | `/api/questions` | 列表（支援分頁、搜尋、篩選） |
| POST | `/api/questions` | 新增題目 |
| GET | `/api/questions/<id>` | 取得單筆 |
| PUT | `/api/questions/<id>` | 更新題目 |
| DELETE | `/api/questions/<id>` | 刪除題目 |

### 遊戲機制
- **8 秒計時器**：SVG 圓形倒數，剩 3 秒變紅 + 抖動，時間到自動跳過
- **計時計分**：`分數 = max(100, round(1000 × 剩餘秒數 / 8))`，最高 1000 分/題
- **Bot 對手**：每題隨機模擬 Bot（60% 答對率、隨機答題時間）
- **答題回饋 Toast**：答完顯示 `+XXX pts` 或 `答錯了！`，1.8 秒淡出
- **Bot answered 通知**：Bot 在隨機時間跳出提示，增加緊張感

### 遊戲大廳
- 難度切換：**A1A2** / **B1B2**
- 題型切換：**Vocabulary** / **Grammar** / **Mixed**
- 假配對動畫：2.5～4 秒隨機等待 → 顯示 Bot 對手 → 自動跳轉開始

### 管理後台（`/admin/questions`）
- 新增 / 編輯 / 刪除題目
- 搜尋、篩選（級別 / 主題 / 類型）
- 分頁瀏覽
- QuestionManager JS class 封裝所有 API 呼叫

### 練習模式
- `voc.html`：詞彙卡片（底部導覽連到同主題 dia / lis）
- `lis.html`：聽力題
- `dia.html`：對話練習

---

## 🚧 待開發 / 已知問題

- [ ] 登入 / 註冊系統（目前無驗證）
- [ ] 排行榜（Rank）頁面
- [ ] Friends 頁面
- [ ] Leagues 頁面
- [ ] 個人資料 / 密碼設定子頁面
- [ ] 介面語言切換（目前固定繁中）
- [ ] 真實多人對戰（目前為 Bot 模擬）
- [ ] TTS 音檔整合（`services/tts_service.py` 已建但未接 UI）
- [ ] A1A2 vs B1B2 的詞彙分級篩選（Excel 欄位對應需確認）

---

## 📁 專案結構

```
.
├── 測試用.py              # Flask 主程式（所有路由）
├── services/
│   ├── question_service.py  # 題目 CRUD + 隨機出題
│   └── tts_service.py       # TTS（未接前端）
├── template/               # HTML 模板
│   ├── 介面.html           # 首頁
│   ├── 遊戲大廳.html       # 配對大廳
│   ├── 遊戲頁.html         # 對戰答題（含計時器）
│   ├── 獲勝介面.html       # 結果頁
│   ├── 設定.html           # 設定
│   ├── admin_questions.html # 管理後台
│   ├── cuisine/shopping/tourism/worklife.html
│   ├── voc.html / dia.html / lis.html
│   └── ...
├── data/
│   └── manual_questions.json  # 手動建立的題庫
├── static/                # 靜態資源
└── PROGRESS.md            # 本檔案
```

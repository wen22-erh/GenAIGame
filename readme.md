# 🔥 AI Dragon Slayer

> 一款結合 **Pygame** 與 **Ollama 本地大型語言模型 (LLM)** 的 2D 動作射擊遊戲。Boss 不再是冰冷的程式碼，而是擁有「大腦」、會思考戰術、會根據戰況嘲諷你的智慧生物。

![Python](https://img.shields.io/badge/Python-3.x-blue) ![Pygame](https://img.shields.io/badge/Game_Engine-Pygame-yellow) ![Ollama](https://img.shields.io/badge/AI-Ollama_LLM-orange)

## 實戰演示 (Demo)

看 AI Boss 如何根據血量與距離動態改變戰術，並生成即時對話！

![Gameplay Demo](assets/dragon動畫2.gif)

---

## 專案特色

這不是普通的彈幕遊戲，核心亮點在於 **Boss (火龍) 的 AI 大腦**：

### 1. LLM 驅動的動態決策

Boss 的行動並非隨機亂數，而是由 `Qwen2.5:7b` 模型根據戰場數據即時判斷：

-   **戰況分析**：AI 會監控自身血量 (安全/危急)、與玩家距離、以及過去 3 回合的交戰成效。
-   **策略選擇**：
    -   **血量健康時**：傾向使用 `IDLE` (觀察) 或 `FIRE BALL` (試探)。
    -   **玩家靠近時**：切換為 `ATTACK` (近身肉搏) 或 `TRACKING FIRE BALL` (追蹤火球)。
    -   **瀕死狂暴**：強制觸發 `HEAL` (回血) 或 `ULTIMATE` (全方位終極毀滅)。

### 2. 沉浸式 AI 對話系統

-   **性格演變**：Boss 擁有完整的人設。從開場的「傲慢自大」，到血量低下回血時的「崩潰憤怒」，台詞風格會隨之改變。
-   **戰後講評**：遊戲結束後，AI 會根據勝負結果生成一段獨一無二的 **繁體中文講評**（勝者嘲諷或敗者遺言）。

### 3. 多執行緒架構 (Multi-threading)

為了確保遊戲在呼叫 AI API 時畫面不卡頓，本專案將 LLM 的思考過程封裝在獨立的 **Thread** 中執行，讓火龍的思考時間不影響使用者體驗實現流暢的 60 FPS 遊戲體驗。

---

## 系統架構與設計

以下 canva 展示本專案的系統流程與 AI 決策邏輯跟其中技術細節：

[![Canva Presentation](https://img.shields.io/badge/Canva-%E7%B7%9A%E4%B8%8A%E7%B0%A1%E5%A0%B1-blue?style=for-the-badge&logo=canva)](https://www.canva.com/design/DAG74PId0wY/gjCRkvrOyAel3CRbvD5daQ/edit?utm_content=DAG74PId0wY&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

> **點擊上方按鈕查看完整的系統架構圖與流程設計。** > **設計亮點**：
>
> -   **State Machine**: 管理遊戲狀態 (Menu / Playing / GameOver)。
> -   **API Integration**: 透過 HTTP Request 與本地 Ollama 服務溝通，強制輸出 JSON 格式以利程式解析。

---

## 安裝與執行教學

### 1. 環境準備

# 安裝 Python 依賴

pip install pygame requests
確保已安裝 Python 3.8+。

### 設定 AI 大腦 (Ollama)

## 設定 AI 大腦（Ollama）

1. 前往 Ollama 官網下載並安裝
2. 下載指定模型（qwen2.5:7b）：

```bash
ollama pull qwen2.5:7b
```

確認 Ollama 服務已在背景執行 (預設 port 為 11434)。

### 3.啟動遊戲

```bash
python main.py
```

## 操作說明

| 按鍵             | 功能               |
| ---------------- | ------------------ |
| W / A / S / D    | 移動角色           |
| 滑鼠左鍵 / SPACE | 發射子彈           |
| P                | 遊戲結束後重新開始 |

## 素材與致謝

-   **AI Model**：Qwen2.5:7b via Ollama
-   **Image Generation**：遊戲內素材圖片使用 Gemini（Nano Banana Pro）生成
-   **Game Engine**：Pygame Community
-   **Reference**：Teacher JCode1029 top-down-shooter

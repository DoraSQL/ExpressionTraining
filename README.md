# 🐾 表達能力特訓 Agent (Expression Training Agent)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B?logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20AI-4285F4?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

<p align="center">
  <b>職場保命力 × 高情商回話 × 150 字極限提煉</b><br/>
  專為高效職場溝通打造的雙核心互動特訓基地，由 <b>mia 貓</b> 貼心引導 🐾✨
</p>

</div>

---

## 🌟 專案簡介

在複雜多變的職場與社交場合中，「會說話」能化險為夷，「長話短說」能拯救混亂！  
**《表達能力特訓 Agent》** 結合了 **「連續回合 RPG 闖關」** 與 **「極限字數總結練功房」**，透過 Google Gemini 大語言模型（或免 Key 智慧離線雙軌機制），為使用者提供即時的情商診斷、字句修剪與教科書級的示範變身。

---

## 🎮 雙核心訓練模式

### 1️⃣ 【模式一】高情商闖關大冒險（RPG 關卡對話）
告別死板的一問一答，升級為真實連鎖對話串（Dialogue Chain），與不同性格的 NPC 展開 2～3 回合的溝通攻防戰：

* **🌱 第 1 關：新手破冰村**（應對外貌評價，幽默自嘲＋反誇破冰）
* **🛡️ 第 2 關：溫柔護城河**（優雅拒絕不合理甩鍋，溫和堅定守住底線）
* **💣 第 3 關：拆彈專家**（面對主管焦慮質疑，以客觀事實與行動方案化解對立）
* **👑 第 4 關：情緒大魔王**（應對公開酸言挑釁，四兩撥千斤掌握主導權）

#### 💡 核心機制：
* **X 光透視評分卡**：即時量化「同理心溫度、觀點清晰度、應對得體度」。
* **NPC 真實心理回饋**：即時模擬對方聽完妳的話後的內心轉折與對白。
* **魔法變身示範 (Before / After)**：點出原回答亮點，並示範教科書級神回覆，以生活化比喻解釋好在哪裡。
* **每回合動態錦囊**：卡關時隨時點開 mia 貓量身打造的拆招小抄。

---

### 2️⃣ 【模式二】150 字「長話短說」練功房
隨機生成 350～500 字混亂、資訊爆炸的突發狀況題（系統當機、跨部門推託、大客戶改規格等），挑戰在 150 字內直切要害：

* **📏 動態字數警示膠囊**：打字時即時變色提示，超標時溫柔提醒並引導修剪。
* **✂️ 贅字大掃除與抓漏**：裁判 AI 逐字分析，精準標出可精簡的囉嗦口頭禪與副詞。
* **💡 常駐「保命三大心法」指南**：
  1. **結論先行**：先講火燒眉毛的結果與危機，不從盤古開天開場。
  2. **直擊核心死結**：一句話講出卡關原因，不扯八卦與抱怨。
  3. **眼下最迫切的第一步**：講出當前最該採取的行動對策。
* **🌟 滿分極簡神總結**：提供一份 120～145 字的滿分對照範本與必勝心法口訣。
* **🧼 一鍵自動清空**：採用 Streamlit 官方標準 `on_click` 事件層架構，點擊換題或清空瞬間 100% 擦乾淨。

---

## 🛡️ 工程亮點與防呆架構

* **雙軌無縫運行 (Fail-safe)**：未填入 API Key 時自動啟動「免 Key 離線展示模式」，內建精編情境劇本，保證 100% 順暢可玩；填入金鑰即點亮「🟢 真 AI 在線生成」。
* **動態模型探測與平滑降級**：自動呼叫 `client.models.list()` 探測當前 Key 最相容的 Flash 模型清單，遇到連線波動自動降級切換。
* **三道防線 JSON 解析器**：徹底克服大模型夾帶 Markdown 或問候語導致解析崩潰的問題。
* **高標準隱私防護**：預先配置完善的 `.gitignore`，嚴格將 `.env`、API 金鑰與本地個人資料列入黑名單，確保開源安全。

---

## 🚀 本機快速開始 (Quick Start)

### 1. 複製專案庫
```bash
git clone https://github.com/your-username/ExpressionTraining.git
cd ExpressionTraining
```

### 2. 安裝必要套件
建議使用 Python 3.10 或以上版本：
```bash
pip install -r requirements.txt
```

### 3. 設定環境變數（選配，亦可於介面填入）
複製範例檔並建立 `.env`：
```bash
cp .env.example .env
```
在 `.env` 中填入你的 Google Gemini API Key：
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
> 💡 *若不設定金鑰，系統亦會自動啟動離線展示模式，完全不影響介面操作與流程體驗！*

### 4. 啟動應用程式
```bash
streamlit run app.py
```
啟動後打開瀏覽器前往 `http://localhost:8501` 即可開始特訓！

---

## ☁️ 部署至 Streamlit Community Cloud

本專案支援一鍵免費部署至 [Streamlit Community Cloud](https://share.streamlit.io/)：

1. 將本專案 Fork 或 Push 至你的 GitHub。
2. 登入 Streamlit Community Cloud 並點擊 **New app**。
3. 選擇你的倉庫與 `app.py`。
4. 點開 **Advanced settings** ➔ **Secrets**，加入你的 API Key：
   ```toml
   GEMINI_API_KEY = "你的_GEMINI_API_KEY"
   ```
5. 點擊 **Deploy**，幾秒鐘後即可擁有公開網址，分享給朋友在手機或電腦上體驗！

---

## 🐾 開發夥伴

* 👑 **美女貓貓**（專案主策劃與規格拍板）
* 🐱 **mia 貓**（核心驅動與貼心指導教練）

---

## 📄 授權條款

本專案採用 [MIT License](LICENSE) 授權開源。

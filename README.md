# 🏐 TVL 企業排球聯賽 — 女子組數據分析平台

> 🔗 **Live Demo**: [點此查看互動儀表板](https://tvl-volleyball-analysis-j2rqqqeadt3jjnsqnrhdqj.streamlit.app/) *(部署後替換此連結)*

從零開始建構的全端資料專案：自動爬取台灣企業排球聯賽（TVL）女子組 4 支球隊共 60+ 位球員的比賽數據，經過清洗、分析、視覺化，並以 Streamlit 互動儀表板呈現，同時訓練機器學習模型進行球員分群與表現預測。

## 專案亮點

- **自動化爬蟲**：從 TVL 官網爬取 4 支球隊、60+ 位球員基本資料與逐場比賽數據
- **完整 ETL 流程**：原始 HTML → JSON → 清洗 → 結構化 CSV，處理缺值、格式轉換、衍生欄位計算
- **互動式儀表板**：Streamlit + Plotly 打造 5 個分頁，支援隊伍篩選、球員比較、趨勢分析
- **機器學習建模**：K-Means 球員風格分群 + Ridge Regression 防守效率預測
- **全中文支援**：圖表、介面、報告皆為繁體中文

## 儀表板截圖

> 啟動後瀏覽 `http://localhost:8501`

| 總覽 | 球員分析 | 跨隊比較 |
|------|----------|----------|
| 得分排行、位置組成、身高體重分佈 | 個人資料卡、技術雷達圖 | 各隊身體素質、技術指標對比 |

## 技術架構

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Web Scraper │────▶│  Data Clean  │────▶│   Analysis   │────▶│  Dashboard  │
│  (BS4)       │     │  (Pandas)    │     │  (Stats/ML)  │     │ (Streamlit) │
└─────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
       │                    │                    │                    │
   raw JSON            clean CSV         reports + models      interactive UI
```

## 涵蓋的隊伍（企21 女子組）

| 隊伍 | 代表色 | 備註 |
|------|--------|------|
| 臺北鯨華 | 🔵 深藍 | `/wteam/3` |
| 高雄台電 | 🔴 紅色 | `/wteam/4` |
| 新北中纖 | 🟢 綠色 | `/wteam/5` |
| 義力營造 | 🟠 橘色 | `/wteam/7` |

## 快速開始

```bash
# 環境建置
git clone https://github.com/YOUR_USERNAME/tvl-volleyball-analysis.git
cd tvl-volleyball-analysis
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# 一鍵執行全流程（爬蟲 → 清洗 → 分析 → 視覺化 → ML）
python main.py

# 啟動互動儀表板
python main.py --steps dashboard
```

### 其他指令

```bash
python main.py --team 臺北鯨華           # 只爬取特定隊伍
python main.py --steps scrape clean      # 只執行部分步驟
python main.py --steps dashboard         # 直接啟動儀表板
```

## 專案結構

```
tvl-whales-analysis/
├── config/                 # 全域設定（URL、路徑、隊伍配色）
├── scraper/                # 爬蟲模組
│   ├── team_scraper.py     #   球隊頁面解析（球員清單、教練團）
│   ├── player_scraper.py   #   球員個人頁面（詳細資料+逐場數據）
│   ├── utils.py            #   HTTP 請求、數據解析工具
│   └── run_scraper.py      #   爬蟲入口（支援單隊/全聯盟）
├── analysis/               # 數據分析
│   ├── data_cleaning.py    #   ETL：JSON → 清洗 → CSV
│   ├── descriptive_stats.py#   描述性統計報告
│   ├── match_analysis.py   #   比賽數據分析、對手分析
│   └── player_comparison.py#   球員間比較、位置比較
├── visualization/          # 靜態圖表（Matplotlib）
│   ├── player_profiles.py  #   球員雷達圖
│   ├── team_charts.py      #   散佈圖、圓餅圖、箱型圖
│   ├── match_trends.py     #   月度趨勢、對手比較
│   └── style.py            #   圖表風格（中文字體設定）
├── ml/                     # 機器學習
│   ├── feature_engineering.py  # 特徵工程（滾動平均、One-Hot）
│   ├── train.py            #   K-Means 分群 + Ridge 迴歸
│   ├── predict.py          #   推論
│   └── evaluate.py         #   Silhouette / R² / MAE 評估
├── dashboard/              # Streamlit 互動儀表板
│   └── app.py              #   5 分頁（總覽/球員/比較/趨勢/跨隊）
├── data/                   # 資料層（raw → processed → models）
├── outputs/                # 輸出（figures / reports）
├── docs/                   # 資料字典、使用指南
├── main.py                 # CLI 入口（--steps, --team）
└── requirements.txt
```

## 使用技術

| 類別 | 工具 |
|------|------|
| 語言 | Python 3.12 |
| 爬蟲 | requests, BeautifulSoup4 |
| 資料處理 | pandas, NumPy |
| 靜態視覺化 | Matplotlib, Seaborn |
| 互動視覺化 | Plotly |
| 儀表板 | Streamlit |
| 機器學習 | scikit-learn (KMeans, Ridge, StandardScaler) |
| 模型持久化 | joblib |

## 分析流程

1. **爬蟲抓取** — 自動解析 TVL 官網 HTML 結構，處理 `<a>` 只包 `<img>` 而資訊在兄弟 `<div>` 的非典型結構
2. **資料清洗** — 拆分 `"11 - 25"` 格式為成功/總數欄位、百分比字串轉數字、計算年齡/BMI 等衍生欄位
3. **描述性統計** — 陣容組成、身體素質分佈、各位置比較、賽季出賽彙整
4. **技術指標分析** — 攻擊/攔網/發球/接發球/防守/舉球 六大指標排行、對手分析、月度趨勢
5. **視覺化** — 雷達圖、散佈圖、箱型圖、條狀圖、折線圖，自動為每位球員產生個人報告
6. **機器學習** — K-Means 自動選群 (Silhouette Score) 進行球員風格分群；Ridge Regression 預測防守效率

## 資料來源

- TVL 企業排球聯賽官方網站：https://tvl.ctvba.org.tw/
- 資料僅供學術研究與個人學習使用

## 作者

[易祐辰] — 資料分析 / Python 開發學習中

## License

MIT

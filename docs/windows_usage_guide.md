# 🏐 臺北鯨華球員分析專案 — Windows 使用指南

---

## 事前準備

### 1. 確認 Python 已安裝

打開 **命令提示字元**（按 `Win + R`，輸入 `cmd`，按 Enter）：

```
python --version
```

你應該看到類似 `Python 3.10.x` 或更新的版本。

如果顯示錯誤，請先到 https://www.python.org/downloads/ 下載安裝，
安裝時 **務必勾選「Add Python to PATH」**。

### 2. 選擇專案存放位置

建議放在桌面或文件資料夾，例如：

```
C:\Users\你的使用者名稱\Documents\tvl-whales-analysis
```

---

## 第一步：解壓縮專案

1. 下載 `tvl-whales-analysis.zip`
2. 在檔案上按右鍵 →「解壓縮全部」
3. 選擇你要放的位置（例如 `Documents`）

---

## 第二步：打開終端機並進入專案

打開 **命令提示字元** 或 **PowerShell**，輸入：

```
cd C:\Users\你的使用者名稱\Documents\tvl-whales-analysis
```

> 提示：你也可以在檔案總管中打開 `tvl-whales-analysis` 資料夾，
> 在資料夾空白處按住 Shift + 右鍵 →「在這裡開啟 PowerShell 視窗」

確認你在正確位置：

```
dir
```

你應該看到：

```
README.md
main.py
requirements.txt
config/
scraper/
analysis/
visualization/
ml/
data/
outputs/
...
```

---

## 第三步：建立虛擬環境

```
python -m venv venv
```

等幾秒鐘，完成後啟動虛擬環境：

```
venv\Scripts\activate
```

成功後，你的命令列前面會出現 `(venv)`，像這樣：

```
(venv) C:\Users\...\tvl-whales-analysis>
```

> ⚠️ **每次開新的終端機都要重新啟動虛擬環境**
> 再次進入專案時，記得先執行 `venv\Scripts\activate`

---

## 第四步：安裝套件

```
pip install -r requirements.txt
```

你會看到一堆安裝訊息，大約 1-2 分鐘。
最後應出現 `Successfully installed ...`

如果想確認安裝成功：

```
pip list
```

確認清單中有 `requests`、`beautifulsoup4`、`pandas`、`matplotlib`、`scikit-learn` 等。

---

## 第五步：執行分析

### 方式 A：一鍵全部執行（推薦新手）

```
python main.py
```

你會看到整個流程依序執行：

```
🏐 臺北鯨華女子排球隊 — 球員分析專案
=======================================================

🕷️  [1/5] 爬蟲抓取資料...
  📡 正在讀取 臺北鯨華 球隊頁面...
     找到 16 位球員、5 位教練、2 位行政人員
  📥 正在抓取球員個人頁面...
     球員: 100%|████████████████████| 16/16
  ✅ 爬蟲完成！16 位球員、368 筆比賽紀錄

🧹 [2/5] 資料清洗與前處理...
  ✅ 球員資料：16 筆 → players_clean.csv
  ✅ 比賽紀錄：368 筆 → matches_clean.csv
  ✅ 球員彙總：16 筆 → player_stats_summary.csv

📊 [3/5] 數據分析...
  ✅ 描述性統計報告 → descriptive_stats.md
  ✅ 比賽分析報告 → match_analysis.md

📈 [4/5] 產生視覺化圖表...
  ✅ 球員雷達圖 → figures/
  ✅ 球隊圖表 → figures/
  ✅ 比賽趨勢圖 → figures/

🤖 [5/5] 機器學習建模...
  ✅ 球員分群完成：3 群（silhouette = 0.456）
  ✅ 防守效率預測模型：R² = 0.312, MAE = 14.2%

=======================================================
✅ 全部流程完成！
```

> 爬蟲階段大約需要 20 秒（16 位球員，每位間隔 1 秒避免被封鎖）

### 方式 B：只執行特定步驟

```
python main.py --steps scrape              # 只執行爬蟲
python main.py --steps scrape clean        # 爬蟲 + 清洗
python main.py --steps analyze visualize   # 分析 + 出圖
python main.py --steps ml                  # 只跑機器學習
```

> ⚠️ 注意依賴關係：
> - `clean` 需要先跑過 `scrape`（需要 data/raw/ 裡的原始資料）
> - `analyze` 和 `visualize` 需要先跑過 `clean`（需要 data/processed/ 裡的清洗資料）
> - `ml` 需要先跑過 `clean`

---

## 第六步：查看成果

執行完成後，打開檔案總管，進入專案資料夾，你會看到：

### 📁 `data/raw/` — 原始爬取資料
```
players.json         ← 16 位球員完整資料（含逐場數據）
match_records.json   ← 所有比賽紀錄
coaches.json         ← 教練團資料
admin.json           ← 行政團隊資料
```

### 📁 `data/processed/` — 清洗後的分析資料
```
players_clean.csv         ← 球員基本資料（含年齡、BMI）
matches_clean.csv         ← 逐場數據（已拆分成功/總數欄位）
player_stats_summary.csv  ← 每位球員的賽季彙總統計
player_clusters.csv       ← 球員分群結果
```
> 這些 CSV 可以直接用 Excel 打開查看

### 📁 `outputs/reports/` — 分析報告
```
descriptive_stats.md   ← 描述性統計（陣容組成、身體素質）
match_analysis.md      ← 比賽分析（技術排行、對手比較、月度趨勢）
```
> .md 檔可以用 VS Code 或任何文字編輯器打開

### 📁 `outputs/figures/` — 視覺化圖表
```
height_weight_scatter.png       ← 身高 vs 體重散佈圖
position_pie.png                ← 位置組成圓餅圖
age_distribution.png            ← 年齡分佈直方圖
height_by_position.png          ← 各位置身高箱型圖
scoring_ranking.png             ← 得分排行條狀圖
radar_overview.png              ← 主力球員雷達圖比較
radar_10_陳芃宣.png              ← 個人雷達圖（每人一張）
team_monthly_trend.png          ← 全隊技術月度趨勢
opponent_comparison.png         ← 對不同對手的表現
defense_trend_top_players.png   ← 主力防守效率趨勢
```
> 直接雙擊即可用圖片檢視器打開

### 📁 `data/models/` — ML 模型
```
clustering.joblib         ← 球員分群模型
defense_predictor.joblib  ← 防守效率預測模型
```

---

## 常見問題

### Q: `python` 指令找不到？
Windows 上可能需要改用 `python3` 或 `py`：
```
py -m venv venv
py main.py
```

### Q: 爬蟲階段卡住或報錯？
可能是網路問題或網站暫時無法連線。等幾分鐘後再試：
```
python main.py --steps scrape
```

### Q: 圖表中文字變成方框？
你的系統需要中文字體。在 `visualization/style.py` 中，
確認 `Microsoft JhengHei`（微軟正黑體）在字體清單第一位（Windows 預設已有）。

### Q: 想重新跑全部流程？
直接再執行一次即可，會覆蓋舊資料：
```
python main.py
```

### Q: 怎麼離開虛擬環境？
```
deactivate
```

---

## 進階用法

### 單獨使用某個模組

```python
# 在 Python 互動式環境中
from analysis.player_comparison import compare_players, position_comparison

# 比較指定球員
print(compare_players([210, 48, 52]))

# 各位置平均表現
print(position_comparison())
```

### 用 Jupyter Notebook 互動分析

```
pip install jupyter
jupyter notebook
```

然後在瀏覽器中新增 Notebook，即可 import 專案中的模組來做互動式探索。

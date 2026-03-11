# ☁️ 部署儀表板到 Streamlit Community Cloud

免費、不需要信用卡，部署後任何人都能透過網址直接看到你的儀表板。

---

## 事前準備

確認你已經：
1. ✅ 跑過 `python main.py`（data/processed/ 裡有 CSV 檔案）
2. ✅ 有 GitHub 帳號

---

## 步驟一：上傳專案到 GitHub

### 1.1 建立 GitHub Repo

1. 到 https://github.com/new
2. Repository name 填 `tvl-volleyball-analysis`
3. 選 **Public**
4. **不要** 勾 "Add a README file"（你已經有了）
5. 按 **Create repository**

### 1.2 從你的電腦推上去

打開終端機（命令提示字元或 PowerShell），輸入：

```bash
cd C:\Users\User\Documents\tvl-whales-analysis

git init
git add .
git commit -m "TVL 女子組數據分析平台 - 初始版本"
git branch -M main
git remote add origin https://github.com/你的帳號/tvl-volleyball-analysis.git
git push -u origin main
```

> 如果你還沒安裝 Git，先到 https://git-scm.com/download/win 下載安裝

### 1.3 確認 processed 資料有上傳

到你的 GitHub repo 頁面，確認 `data/processed/` 裡面有這些檔案：
- `players_clean.csv`
- `matches_clean.csv`
- `player_stats_summary.csv`

**這很重要！** 儀表板在雲端是讀這些 CSV 的，如果沒有上傳，儀表板會顯示錯誤。

如果沒有看到這些檔案，在本機執行：
```bash
git add data/processed/*.csv
git commit -m "加入清洗後的資料"
git push
```

---

## 步驟二：部署到 Streamlit Cloud

### 2.1 登入 Streamlit Cloud

1. 到 https://share.streamlit.io
2. 點 **Sign in with GitHub**
3. 授權 Streamlit 存取你的 GitHub

### 2.2 新增應用程式

1. 點 **New app**
2. 設定：
   - **Repository**: `你的帳號/tvl-volleyball-analysis`
   - **Branch**: `main`
   - **Main file path**: `dashboard/app.py`
3. 點 **Deploy!**

### 2.3 等待部署

部署大約需要 2-5 分鐘。Streamlit Cloud 會自動：
- 讀取 `requirements.txt` 安裝套件
- 執行 `dashboard/app.py`
- 產生一個公開網址，格式類似：
  `https://你的帳號-tvl-volleyball-analysis-dashboardapp-xxxxx.streamlit.app`

---

## 步驟三：完成！

部署成功後你會得到一個公開網址，例如：

```
https://yourname-tvl-volleyball-analysis-dashboardapp-abc123.streamlit.app
```

這個網址可以：
- ✅ 放進履歷
- ✅ 在面試時直接打開展示
- ✅ 分享給任何人

---

## 常見問題

### Q: 部署失敗？

最常見的原因是 `requirements.txt` 裡的套件版本衝突。
確認你的 `requirements.txt` 有這些：

```
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.1.0
numpy<2.0
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.18.0
streamlit>=1.30.0
scikit-learn>=1.3.0
joblib>=1.3.0
tqdm>=4.66.0
tabulate>=0.9.0
openpyxl>=3.1.0
```

### Q: 部署後顯示「找不到資料」？

表示 `data/processed/` 裡的 CSV 沒有上傳到 GitHub。
回到本機：
```bash
git add data/processed/*.csv
git commit -m "加入清洗後的資料"
git push
```
Streamlit Cloud 會自動重新部署。

### Q: 想更新資料怎麼辦？

在本機重新爬取後 push 上去：
```bash
python main.py --steps scrape clean
git add data/processed/*.csv
git commit -m "更新賽季數據"
git push
```
Streamlit Cloud 會自動偵測到更新並重新部署。

### Q: 可以自訂網址嗎？

Streamlit Cloud 免費版不能完全自訂，但你可以在 Settings 中修改 URL 的部分文字。

---

## 部署後的加分動作

1. **在 GitHub repo 的 About 欄位** 加上儀表板連結
2. **在 README.md** 最上方加上「🔗 Live Demo: [連結]」
3. **在履歷上** 寫：「互動儀表板：[連結]」

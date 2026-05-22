# HK Breadth Site MVP

港股市寬網站 MVP：

- 支援港股股票清單
- 用 yfinance 抓每日收市價
- 計算 MA10 / MA50 / MA150 / MA250 市寬
- 計算板塊強弱分數
- 顯示 2800 盈富基金對比線
- 前端用 Chart.js 畫圖
- 後端用 FastAPI

## 安裝

```bash
cd hk_breadth_site_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 第一次更新資料

```bash
python update_data.py
```

## 開網站

```bash
uvicorn app:app --reload
```

打開：

```text
http://127.0.0.1:8000
```

## 修改股票池

股票清單在：

```text
data/constituents.json
```

之後可以把股票池擴大到所有市值 3 億以上港股。

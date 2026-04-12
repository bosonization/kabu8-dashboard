# kabu8-dashboard

日本株の売買判断用ダッシュボードです。  
このリポジトリは **表示専用** で、分析ロジック本体は含みません。

## 役割
この公開リポジトリは、非公開リポジトリ側で生成された CSV を `dashboard_data/` に反映し、  
`stock_dashboard.py` で可視化するためのものです。

含むもの:
- `stock_dashboard.py`  
  Streamlit の表示アプリ本体
- `requirements.txt`  
  Streamlit Community Cloud 用の依存関係
- `dashboard_data/*.csv`  
  非公開リポジトリの GitHub Actions が自動反映する表示用データ

含まないもの:
- 株価取得ロジック
- テクニカル判定ロジック
- 決算 PDF 解析ロジック
- バックテストや銘柄選定ロジック本体

---

## デプロイ前提
このリポジトリは、**Streamlit Community Cloud** での公開を前提としています。

想定構成:

```text
stock_dashboard.py
requirements.txt
dashboard_data/
  technical_signals_all.csv
  technical_buy_candidates.csv
  technical_today_top.csv
  ifd_candidates_preopen.csv
  ifd_candidates_0930.csv
  kabupro_progress_all.csv
  technical_run_summary.csv
  kabupro_run_summary.csv
  last_updated_utc.txt
```

---

## ローカル実行方法

### 1. 依存関係をインストール
```bash
pip install -r requirements.txt
```

### 2. アプリを起動
```bash
streamlit run stock_dashboard.py
```

### 3. ブラウザで確認
通常は次のようなローカル URL が表示されます。

```text
http://localhost:8501
```

---

## Streamlit Community Cloud での公開

### 入力値
- **Repository**  
  `https://github.com/bosonization/kabu8-dashboard/blob/main/stock_dashboard.py`
- **Branch**  
  `main`
- **Main file path**  
  `stock_dashboard.py`

### 注意
このリポジトリは公開用です。  
表示ロジックのみを置き、分析本体コードは非公開リポジトリに残します。

---

## データ更新の流れ
1. 非公開リポジトリ側の GitHub Actions が実行される
2. `run_daily_selected10.py` により分析が実行される
3. 生成された CSV をこの公開リポジトリの `dashboard_data/` に自動反映する
4. Streamlit Community Cloud 側で最新データが表示される

---

## dashboard_data に入る主なファイル
- `technical_signals_all.csv`  
  全銘柄のテクニカル評価
- `technical_buy_candidates.csv`  
  買い候補一覧
- `technical_today_top.csv`  
  当日優先候補
- `ifd_candidates_preopen.csv`  
  寄り前 IFD 候補
- `ifd_candidates_0930.csv`  
  9:30 前後 IFD 候補
- `kabupro_progress_all.csv`  
  決算進捗結果
- `technical_run_summary.csv`  
  テクニカル実行サマリー
- `kabupro_run_summary.csv`  
  決算進捗実行サマリー
- `last_updated_utc.txt`  
  最終更新時刻

---

## 公開時の方針
- このリポジトリには **売買ロジック本体を置かない**
- 表示に不要な内部メモや機密情報は CSV に含めない
- `stock_dashboard.py` は **表示専用** にする
- 判定ロジックや PDF 解析ロジックは非公開リポジトリで管理する

---

## トラブルシュート

### 画面は出るがデータが空
`dashboard_data/` に CSV が入っているか確認してください。  
非公開リポジトリ側の GitHub Actions が失敗している可能性があります。

### Streamlit Community Cloud で起動エラーになる
`requirements.txt` が不足している可能性があります。  
最低限、このリポジトリでは以下を使用します。
- streamlit
- pandas
- numpy
- plotly

### 価格チャートが出ない
`stock_dashboard.py` の設定によっては `prices/` が無い環境では価格チャートが限定表示になる場合があります。  
Community Cloud では基本的に `dashboard_data/` の CSV 可視化を主目的としてください。

---

## ライセンス / 取り扱い
この公開リポジトリは表示用途を想定しています。  
分析本体や商用ロジックは、別の非公開リポジトリで管理してください。

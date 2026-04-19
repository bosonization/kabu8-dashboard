# KABU8 Market Lens

**日本株の候補抽出を、毎日ぶれずに。**

KABU8 Market Lens は、日本株の候補抽出を毎日ぶれずに行うための**判断支援ダッシュボード**です。  
テクニカル候補、IFD候補、決算進捗補強を一画面で整理し、売買判断前の迷いを減らすことを目的としています。

このリポジトリは **表示専用** であり、分析ロジック本体は含みません。

---

## このダッシュボードが提供するもの
- テクニカル候補の可視化
- IFD候補の確認
- 決算進捗補強の確認
- 当日確認すべき候補の比較
- 更新状況とデータ信頼性の可視化

## このダッシュボードが提供しないもの
- 投資助言
- 利益保証
- 完全自動売買
- 売買ロジック本体の公開

---

## 役割
この公開リポジトリは、非公開リポジトリ側で生成された CSV を `dashboard_data/` に反映し、  
`stock_dashboard.py` で可視化するためのものです。

含むもの:
- `stock_dashboard.py`  
  Streamlit の表示アプリ本体
- `requirements.txt`  
  Streamlit Community Cloud 用の依存関係
- `.streamlit/config.toml`  
  テーマ設定
- `assets/`  
  アイコン、ロゴ、favicon
- `dashboard_data/*.csv`  
  非公開リポジトリの GitHub Actions が自動反映する表示用データ

含まないもの:
- 株価取得ロジック
- テクニカル判定ロジック
- 決算 PDF 解析ロジック
- バックテストや銘柄選定ロジック本体

---

## 想定ディレクトリ構成

```text
stock_dashboard.py
requirements.txt
README.md
.streamlit/
  config.toml
assets/
  favicon.png
  kabu8_icon_square.png
  kabu8_logo_horizontal.png
dashboard_data/
  technical_signals_all.csv
  technical_buy_candidates.csv
  technical_today_top.csv
  technical_weekly_watchlist.csv
  technical_priority_watchlist.csv
  ifd_candidates_preopen.csv
  ifd_candidates_0930.csv
  ifd_candidates_all.csv
  kabupro_progress_all.csv
  technical_run_summary.csv
  kabupro_run_summary.csv
  run_daily_summary.csv
  last_updated_utc.txt
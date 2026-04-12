from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="株式売買判断ダッシュボード", layout="wide")

BASE_DIR = Path(os.getenv("BASE_DIR", ".")).resolve()
DASHBOARD_DATA_DIR = Path(os.getenv("DASHBOARD_DATA_DIR", BASE_DIR / "dashboard_data"))
PRICES_DIR = Path(os.getenv("PRICES_DIR", BASE_DIR / "prices"))
TECH_DIR = Path(os.getenv("TECH_DIR", BASE_DIR / "technical_outputs"))
KABUPRO_DIR = Path(os.getenv("KABUPRO_DIR", BASE_DIR / "outputs" / "kabupro"))
if not KABUPRO_DIR.exists():
    KABUPRO_DIR = Path(os.getenv("KABUPRO_DIR", BASE_DIR / "kabupro_outputs"))

ACTION_PRIORITY = {
    "買い候補（ブレイク）": 1,
    "買い候補（押し目）": 2,
    "監視候補（戻り初動）": 3,
    "監視候補（週足上昇）": 4,
    "様子見": 8,
    "見送り（週足弱い）": 9,
    "除外（流動性不足）": 10,
    "除外（ボラ条件外）": 10,
}

FILE_MAP = {
    "signals": "technical_signals_all.csv",
    "buy": "technical_buy_candidates.csv",
    "weekly": "technical_weekly_watchlist.csv",
    "priority": "technical_priority_watchlist.csv",
    "today_top": "technical_today_top.csv",
    "ifd_preopen": "ifd_candidates_preopen.csv",
    "ifd_0930": "ifd_candidates_0930.csv",
    "ifd_all": "ifd_candidates_all.csv",
    "kabupro": "kabupro_progress_all.csv",
    "technical_summary": "technical_run_summary.csv",
    "kabupro_summary": "kabupro_run_summary.csv",
    "run_daily_summary": "run_daily_summary.csv",
}


def norm_code(v) -> str:
    s = str(v).strip().upper()
    if s.endswith(".T"):
        s = s[:-2]
    return s


@st.cache_data(ttl=300)
def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path)


def resolve_data_file(file_name: str, fallback_dir: Path | None = None) -> Path:
    dashboard_path = DASHBOARD_DATA_DIR / file_name
    if dashboard_path.exists():
        return dashboard_path
    if fallback_dir is not None:
        return fallback_dir / file_name
    return dashboard_path


@st.cache_data(ttl=300)
def load_data() -> dict[str, pd.DataFrame]:
    paths = {
        "signals": resolve_data_file(FILE_MAP["signals"], TECH_DIR),
        "buy": resolve_data_file(FILE_MAP["buy"], TECH_DIR),
        "weekly": resolve_data_file(FILE_MAP["weekly"], TECH_DIR),
        "priority": resolve_data_file(FILE_MAP["priority"], TECH_DIR),
        "today_top": resolve_data_file(FILE_MAP["today_top"], TECH_DIR),
        "ifd_preopen": resolve_data_file(FILE_MAP["ifd_preopen"], TECH_DIR),
        "ifd_0930": resolve_data_file(FILE_MAP["ifd_0930"], TECH_DIR),
        "ifd_all": resolve_data_file(FILE_MAP["ifd_all"], TECH_DIR),
        "kabupro": resolve_data_file(FILE_MAP["kabupro"], KABUPRO_DIR),
        "technical_summary": resolve_data_file(FILE_MAP["technical_summary"], TECH_DIR),
        "kabupro_summary": resolve_data_file(FILE_MAP["kabupro_summary"], KABUPRO_DIR),
        "run_daily_summary": resolve_data_file(FILE_MAP["run_daily_summary"], BASE_DIR / "final_outputs"),
    }
    return {k: read_csv(v) for k, v in paths.items()}


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    if "code" in out.columns:
        out["code"] = out["code"].map(norm_code)
    for col in out.columns:
        low = str(col).lower()
        if any(k in low for k in ["score", "pct", "ratio", "take", "stop", "entry", "close", "progress", "turnover", "vol_"]):
            out[col] = pd.to_numeric(out[col], errors="ignore")
    return out


def merge_decision_frame(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    signals = prepare(data["signals"])
    ifd_pre = prepare(data["ifd_preopen"])
    ifd_0930 = prepare(data["ifd_0930"])
    kabu = prepare(data["kabupro"])
    if signals.empty:
        return signals.copy()

    base = signals.copy()
    base["action_priority"] = base["action"].map(ACTION_PRIORITY).fillna(99)

    if not ifd_pre.empty:
        cols = [c for c in ["code", "ifd_reco_time", "ifd_order_type", "ifd_entry_price", "ifd_take_profit", "ifd_stop_loss", "ifd_note", "today_rank_score"] if c in ifd_pre.columns]
        tmp = ifd_pre[cols].copy().rename(columns={
            "ifd_reco_time": "preopen_reco_time",
            "ifd_order_type": "preopen_order_type",
            "ifd_entry_price": "preopen_entry_price",
            "ifd_take_profit": "preopen_take_profit",
            "ifd_stop_loss": "preopen_stop_loss",
            "ifd_note": "preopen_note",
            "today_rank_score": "preopen_rank_score",
        })
        base = base.merge(tmp, on="code", how="left")

    if not ifd_0930.empty:
        cols = [c for c in ["code", "ifd_reco_time", "ifd_order_type", "ifd_entry_price", "ifd_take_profit", "ifd_stop_loss", "ifd_note", "today_rank_score"] if c in ifd_0930.columns]
        tmp = ifd_0930[cols].copy().rename(columns={
            "ifd_reco_time": "t0930_reco_time",
            "ifd_order_type": "t0930_order_type",
            "ifd_entry_price": "t0930_entry_price",
            "ifd_take_profit": "t0930_take_profit",
            "ifd_stop_loss": "t0930_stop_loss",
            "ifd_note": "t0930_note",
            "today_rank_score": "t0930_rank_score",
        })
        base = base.merge(tmp, on="code", how="left")

    if not kabu.empty and "code" in kabu.columns:
        keep = [c for c in kabu.columns if c in [
            "code", "used_report_date", "used_report_type", "latest_any_date",
            "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct",
            "status", "parser_note"
        ]]
        tmp = kabu[keep].copy().rename(columns={"status": "kabupro_status", "parser_note": "kabupro_note"})
        base = base.merge(tmp, on="code", how="left")

    for col in ["sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct", "rr1", "rr2", "total_score", "vol_ratio", "risk_pct"]:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce")

    op = base["operating_progress_pct"] if "operating_progress_pct" in base.columns else pd.Series(index=base.index, dtype=float)
    ordinary = base["ordinary_progress_pct"] if "ordinary_progress_pct" in base.columns else pd.Series(index=base.index, dtype=float)
    sales = base["sales_progress_pct"] if "sales_progress_pct" in base.columns else pd.Series(index=base.index, dtype=float)
    base["progress_quality"] = np.where(
        op.notna(),
        op.fillna(0) * 0.45 + ordinary.fillna(0) * 0.35 + sales.fillna(0) * 0.20,
        np.nan,
    )
    base["decision_score"] = (
        (100 - base["action_priority"].fillna(99) * 8)
        + base.get("total_score", 0).fillna(0) * 0.9
        + base.get("rr1", 0).fillna(0) * 5.0
        + np.minimum(base.get("vol_ratio", 0).fillna(0), 3.0) * 3.0
        + np.where(base["progress_quality"].notna(), np.minimum(base["progress_quality"].fillna(0) / 15.0, 12.0), 0)
        - np.where(base.get("risk_pct", pd.Series(index=base.index, dtype=float)).notna(), np.maximum(base.get("risk_pct", 0).fillna(0) - 6.0, 0) * 1.5, 0)
    )
    base["decision_bucket"] = np.select(
        [
            base["action"].eq("買い候補（ブレイク）"),
            base["action"].eq("買い候補（押し目）"),
            base["action"].eq("監視候補（戻り初動）"),
        ],
        ["ブレイク", "押し目", "戻り初動"],
        default="その他",
    )
    return base.sort_values(["decision_score", "total_score"], ascending=False).reset_index(drop=True)


@st.cache_data(ttl=300)
def load_price_for_code(code: str) -> pd.DataFrame:
    code = norm_code(code)
    candidates = [
        PRICES_DIR / f"{code}.T" / f"{code}.T__1d.csv",
        PRICES_DIR / f"{code}.T__1d.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return pd.DataFrame()
    df = read_csv(path)
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    df["Price"] = pd.to_numeric(df[price_col], errors="coerce")
    for c in ["Open", "High", "Low", "Close"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["ma20"] = df["Price"].rolling(20).mean()
    df["ma50"] = df["Price"].rolling(50).mean()
    return df.dropna(subset=["Date", "Price"])


def show_price_chart(code: str):
    df = load_price_for_code(code)
    if df.empty:
        st.info("価格CSVが見つかりません。")
        return
    tail = df.tail(160)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=tail["Date"],
        open=tail.get("Open", tail["Price"]),
        high=tail.get("High", tail["Price"]),
        low=tail.get("Low", tail["Price"]),
        close=tail.get("Close", tail["Price"]),
        name="日足",
    ))
    fig.add_trace(go.Scatter(x=tail["Date"], y=tail["ma20"], mode="lines", name="MA20"))
    fig.add_trace(go.Scatter(x=tail["Date"], y=tail["ma50"], mode="lines", name="MA50"))
    fig.update_layout(height=420, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)


def style_decision_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in [
        "code", "group_name", "action", "setup_type", "decision_score", "total_score", "rr1",
        "risk_pct", "vol_ratio", "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct",
        "entry_low", "entry_high", "stop", "take1", "take2", "preopen_order_type", "t0930_order_type"
    ] if c in df.columns]
    out = df[cols].copy()
    for c in out.columns:
        if pd.api.types.is_numeric_dtype(out[c]):
            out[c] = out[c].round(2)
    return out


def show_status_banner(data: dict[str, pd.DataFrame]):
    sources = []
    for key, file_name in FILE_MAP.items():
        fallback = TECH_DIR if key.startswith("technical") or key in {"signals", "buy", "weekly", "priority", "today_top", "ifd_preopen", "ifd_0930", "ifd_all"} else KABUPRO_DIR
        if key == "run_daily_summary":
            fallback = BASE_DIR / "final_outputs"
        resolved = resolve_data_file(file_name, fallback)
        if resolved.exists():
            sources.append(f"{key}: {resolved}")
    with st.expander("データソース確認"):
        st.write("dashboard_data を優先し、なければローカル出力ディレクトリを参照します。")
        for s in sources:
            st.write("-", s)


def main():
    st.title("株式売買判断ダッシュボード")
    st.caption("run_daily_selected10.py の出力CSVから、当日の売買判断に必要な情報を集約して表示します。")
    if st.button("再読込"):
        st.cache_data.clear()
        st.rerun()

    data = load_data()
    decision = merge_decision_frame(data)
    show_status_banner(data)

    with st.sidebar:
        st.header("設定")
        st.write(f"BASE_DIR: {BASE_DIR}")
        st.write(f"DASHBOARD_DATA_DIR: {DASHBOARD_DATA_DIR}")
        st.write(f"PRICES_DIR: {PRICES_DIR}")
        action_options = sorted(decision["action"].dropna().unique().tolist()) if not decision.empty and "action" in decision.columns else []
        action_filter = st.multiselect("アクション", options=action_options, default=action_options)
        group_options = sorted(decision["group_name"].dropna().unique().tolist()) if not decision.empty and "group_name" in decision.columns else []
        group_filter = st.multiselect("グループ", options=group_options, default=[])
        min_score = st.slider("最低総合点", 0, 100, 55)
        only_ifd = st.checkbox("IFD候補のみ", value=False)
        only_kabupro_ok = st.checkbox("決算進捗取得OKのみ", value=False)
        only_buy_like = st.checkbox("買い候補・戻り初動のみ", value=True)

    dff = decision.copy()
    if not dff.empty:
        if action_filter:
            dff = dff[dff["action"].isin(action_filter)]
        if group_filter and "group_name" in dff.columns:
            dff = dff[dff["group_name"].isin(group_filter)]
        if "total_score" in dff.columns:
            dff = dff[dff["total_score"].fillna(0) >= min_score]
        if only_ifd:
            cols = [c for c in ["preopen_order_type", "t0930_order_type"] if c in dff.columns]
            if cols:
                dff = dff[dff[cols].notna().any(axis=1)]
        if only_kabupro_ok and "kabupro_status" in dff.columns:
            dff = dff[dff["kabupro_status"].eq("ok")]
        if only_buy_like and "action" in dff.columns:
            dff = dff[dff["action"].isin(["買い候補（ブレイク）", "買い候補（押し目）", "監視候補（戻り初動）"])]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("全シグナル", len(data["signals"]))
    c2.metric("買い候補", len(data["buy"]))
    c3.metric("寄り前IFD", len(data["ifd_preopen"]))
    c4.metric("9:30IFD", len(data["ifd_0930"]))
    c5.metric("決算進捗件数", len(data["kabupro"]))

    tab1, tab2, tab3, tab4 = st.tabs(["売買判断ボード", "候補一覧", "個別銘柄詳細", "データ品質"])

    with tab1:
        st.subheader("売買判断ボード")
        if dff.empty:
            st.warning("表示対象がありません。")
        else:
            board = dff.head(15).copy()
            st.dataframe(style_decision_table(board), use_container_width=True, hide_index=True)
            st.markdown("#### 判断の見方")
            st.markdown(
                "- **decision_score**: 当日の優先度。アクション優先度、総合点、RR、出来高、決算進捗を合わせた参考値。\n"
                "- **寄り前IFD**: 主に押し目型。前夜の価格帯で発注しやすい候補。\n"
                "- **9:30IFD**: 主にブレイク型。寄り直後のだましを避けて発注する候補。\n"
                "- **決算進捗**: 売上より営業利益・経常利益の進捗が高いほど質が良いと判断しやすい。"
            )
            colA, colB = st.columns(2)
            with colA:
                st.markdown("#### 寄り前IFD候補")
                pre = dff[dff.get("preopen_order_type", pd.Series(index=dff.index)).notna()].copy()
                cols = [c for c in ["code", "action", "decision_score", "preopen_order_type", "preopen_entry_price", "preopen_take_profit", "preopen_stop_loss", "rr1", "sales_progress_pct", "operating_progress_pct"] if c in pre.columns]
                st.dataframe(pre[cols].head(10).round(2), use_container_width=True, hide_index=True)
            with colB:
                st.markdown("#### 9:30 IFD候補")
                d930 = dff[dff.get("t0930_order_type", pd.Series(index=dff.index)).notna()].copy()
                cols = [c for c in ["code", "action", "decision_score", "t0930_order_type", "t0930_entry_price", "t0930_take_profit", "t0930_stop_loss", "rr1", "sales_progress_pct", "operating_progress_pct"] if c in d930.columns]
                st.dataframe(d930[cols].head(10).round(2), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("候補一覧")
        if dff.empty:
            st.info("候補なし")
        else:
            table = style_decision_table(dff)
            st.dataframe(table, use_container_width=True, hide_index=True)
            csv = table.to_csv(index=False).encode("utf-8-sig")
            st.download_button("表示中データをCSVダウンロード", data=csv, file_name="dashboard_filtered_candidates.csv", mime="text/csv")

    with tab3:
        st.subheader("個別銘柄詳細")
        options = dff["code"].tolist() if not dff.empty else decision["code"].tolist() if not decision.empty else []
        if not options:
            st.info("銘柄がありません。")
        else:
            selected = st.selectbox("銘柄コード", options)
            row = decision[decision["code"] == selected].head(1)
            if not row.empty:
                row = row.iloc[0]
                a, b = st.columns([1.4, 1])
                with a:
                    show_price_chart(selected)
                with b:
                    st.markdown(f"### {selected}")
                    st.write({
                        "action": row.get("action"),
                        "setup_type": row.get("setup_type"),
                        "group_name": row.get("group_name"),
                        "decision_score": row.get("decision_score"),
                        "total_score": row.get("total_score"),
                        "rr1": row.get("rr1"),
                        "risk_pct": row.get("risk_pct"),
                        "entry_low": row.get("entry_low"),
                        "entry_high": row.get("entry_high"),
                        "stop": row.get("stop"),
                        "take1": row.get("take1"),
                        "take2": row.get("take2"),
                        "sales_progress_pct": row.get("sales_progress_pct"),
                        "operating_progress_pct": row.get("operating_progress_pct"),
                        "ordinary_progress_pct": row.get("ordinary_progress_pct"),
                        "used_report_type": row.get("used_report_type"),
                        "used_report_date": row.get("used_report_date"),
                        "kabupro_status": row.get("kabupro_status"),
                    })
                    notes = []
                    if pd.notna(row.get("preopen_order_type", np.nan)):
                        notes.append(f"寄り前: {row.get('preopen_order_type')} / entry={row.get('preopen_entry_price')}")
                    if pd.notna(row.get("t0930_order_type", np.nan)):
                        notes.append(f"9:30: {row.get('t0930_order_type')} / entry={row.get('t0930_entry_price')}")
                    if pd.notna(row.get("kabupro_note", np.nan)):
                        notes.append(f"kabupro: {row.get('kabupro_note')}")
                    if notes:
                        st.markdown("#### メモ")
                        for n in notes:
                            st.write("-", n)

    with tab4:
        st.subheader("データ品質 / 実行確認")
        cols = st.columns(3)
        cols[0].write("technical_run_summary")
        cols[0].dataframe(data["technical_summary"], use_container_width=True, hide_index=True)
        cols[1].write("kabupro_run_summary")
        cols[1].dataframe(data["kabupro_summary"], use_container_width=True, hide_index=True)
        cols[2].write("最新決算進捗")
        preview_cols = [c for c in ["code", "used_report_date", "used_report_type", "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct", "status"] if c in data["kabupro"].columns]
        cols[2].dataframe(data["kabupro"][preview_cols].head(20), use_container_width=True, hide_index=True)
        if not data["run_daily_summary"].empty:
            st.markdown("#### run_daily_summary")
            st.dataframe(data["run_daily_summary"], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# Page config
# ------------------------------------------------------------
ASSETS_DIR = Path("assets")
FAVICON_PATH = ASSETS_DIR / "favicon.png"
LOGO_PATH = ASSETS_DIR / "kabu8_logo_horizontal.png"
ICON_PATH = ASSETS_DIR / "kabu8_icon_square.png"

st.set_page_config(
    page_title="KABU8 Market Lens",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if LOGO_PATH.exists():
    try:
        st.logo(
            image=str(LOGO_PATH),
            icon_image=str(ICON_PATH) if ICON_PATH.exists() else None,
            size="large",
        )
    except Exception:
        pass

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
BASE_DIR = Path(os.getenv("BASE_DIR", ".")).resolve()
DASHBOARD_DATA_DIR = Path(os.getenv("DASHBOARD_DATA_DIR", BASE_DIR / "dashboard_data"))
PRICES_DIR = Path(os.getenv("PRICES_DIR", BASE_DIR / "prices"))
TECH_DIR = Path(os.getenv("TECH_DIR", BASE_DIR / "technical_outputs"))
KABUPRO_DIR = Path(os.getenv("KABUPRO_DIR", BASE_DIR / "outputs" / "kabupro"))
if not KABUPRO_DIR.exists():
    KABUPRO_DIR = Path(os.getenv("KABUPRO_DIR", BASE_DIR / "kabupro_outputs"))

# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown(
    """
<style>
.block-container {
    padding-top: 1.1rem;
    padding-bottom: 2.2rem;
}
.k8-hero {
    padding: 1.2rem 1.4rem 1rem 1.4rem;
    border: 1px solid rgba(120, 120, 120, 0.18);
    border-radius: 16px;
    background: rgba(250, 251, 253, 0.88);
    margin-bottom: 1rem;
}
.k8-section-caption {
    font-size: 0.92rem;
    color: #66758A;
    margin-top: -0.15rem;
    margin-bottom: 0.9rem;
}
.k8-card {
    padding: 0.85rem 1rem;
    border: 1px solid rgba(120, 120, 120, 0.16);
    border-radius: 14px;
    background: white;
    height: 100%;
}
.k8-placeholder {
    padding: 1.2rem 1rem;
    border: 1px dashed rgba(120, 120, 120, 0.28);
    border-radius: 14px;
    background: rgba(248, 250, 252, 0.85);
}
.k8-small {
    font-size: 0.9rem;
    color: #66758A;
}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------
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
    "last_updated": "last_updated_utc.txt",
}


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------
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


@st.cache_data(ttl=300)
def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig").strip()
    except Exception:
        try:
            return path.read_text(encoding="utf-8").strip()
        except Exception:
            return ""


def resolve_data_file(file_name: str, fallback_dir: Path | None = None) -> Path:
    dashboard_path = DASHBOARD_DATA_DIR / file_name
    if dashboard_path.exists():
        return dashboard_path
    if fallback_dir is not None:
        return fallback_dir / file_name
    return dashboard_path


@st.cache_data(ttl=300)
def load_data() -> dict[str, object]:
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

    data = {k: read_csv(v) for k, v in paths.items()}

    last_updated_path = DASHBOARD_DATA_DIR / FILE_MAP["last_updated"]
    data["last_updated_text"] = read_text(last_updated_path)

    source_status = {}
    for key, p in paths.items():
        if str(p).startswith(str(DASHBOARD_DATA_DIR)):
            source_status[key] = "dashboard_data"
        else:
            source_status[key] = str(p.parent)

    source_status["last_updated"] = "dashboard_data" if last_updated_path.exists() else "missing"
    data["source_status"] = source_status
    return data


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    if "code" in out.columns:
        out["code"] = out["code"].map(norm_code)
    for col in out.columns:
        low = str(col).lower()
        if any(k in low for k in ["score", "pct", "ratio", "take", "stop", "entry", "close", "progress", "turnover", "vol_"]):
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def merge_decision_frame(data: dict[str, object]) -> pd.DataFrame:
    signals = prepare(data["signals"])  # type: ignore[index]
    ifd_pre = prepare(data["ifd_preopen"])  # type: ignore[index]
    ifd_0930 = prepare(data["ifd_0930"])  # type: ignore[index]
    kabu = prepare(data["kabupro"])  # type: ignore[index]

    if signals.empty:
        return signals.copy()

    base = signals.copy()
    if "action" in base.columns:
        base["action_priority"] = base["action"].map(ACTION_PRIORITY).fillna(99)
    else:
        base["action_priority"] = 99

    if not ifd_pre.empty:
        cols = [
            c for c in [
                "code", "ifd_reco_time", "ifd_order_type", "ifd_entry_price",
                "ifd_take_profit", "ifd_stop_loss", "ifd_note", "today_rank_score"
            ] if c in ifd_pre.columns
        ]
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
        cols = [
            c for c in [
                "code", "ifd_reco_time", "ifd_order_type", "ifd_entry_price",
                "ifd_take_profit", "ifd_stop_loss", "ifd_note", "today_rank_score"
            ] if c in ifd_0930.columns
        ]
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
        keep = [
            c for c in kabu.columns if c in [
                "code", "used_report_date", "used_report_type", "latest_any_date",
                "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct",
                "status", "parser_note"
            ]
        ]
        tmp = kabu[keep].copy().rename(columns={
            "status": "kabupro_status",
            "parser_note": "kabupro_note",
        })
        base = base.merge(tmp, on="code", how="left")

    for col in [
        "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct",
        "rr1", "rr2", "total_score", "vol_ratio", "risk_pct"
    ]:
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

    risk_series = base["risk_pct"] if "risk_pct" in base.columns else pd.Series(index=base.index, dtype=float)
    rr1_series = base["rr1"] if "rr1" in base.columns else pd.Series(index=base.index, dtype=float)
    score_series = base["total_score"] if "total_score" in base.columns else pd.Series(index=base.index, dtype=float)
    vol_ratio_series = base["vol_ratio"] if "vol_ratio" in base.columns else pd.Series(index=base.index, dtype=float)

    base["decision_score"] = (
        (100 - base["action_priority"].fillna(99) * 8)
        + score_series.fillna(0) * 0.9
        + rr1_series.fillna(0) * 5.0
        + np.minimum(vol_ratio_series.fillna(0), 3.0) * 3.0
        + np.where(base["progress_quality"].notna(), np.minimum(base["progress_quality"].fillna(0) / 15.0, 12.0), 0)
        - np.where(risk_series.notna(), np.maximum(risk_series.fillna(0) - 6.0, 0) * 1.5, 0)
    )

    return base.sort_values(["decision_score", "total_score"], ascending=False).reset_index(drop=True)


def action_to_label(action: object) -> str:
    s = str(action or "")
    if "ブレイク" in s:
        return "ブレイク候補"
    if "押し目" in s:
        return "押し目候補"
    if "戻り初動" in s:
        return "戻り初動候補"
    if "週足上昇" in s:
        return "週足上昇候補"
    if s:
        return s
    return "要確認"


def kabupro_to_label(status: object, note: object) -> str:
    s = str(status or "").strip().lower()
    n = str(note or "").strip()
    if s in {"ok", "success"}:
        return "補強あり"
    if s or n:
        return "一部注意"
    return "未取得"


def trend_label(value: object) -> str:
    try:
        return "上向き" if float(value) == 1 else "要確認"
    except Exception:
        return "要確認"


def ifd_label(row: pd.Series) -> str:
    has_pre = pd.notna(row.get("preopen_order_type", np.nan))
    has_930 = pd.notna(row.get("t0930_order_type", np.nan))
    if has_pre and has_930:
        return "対象"
    if has_pre or has_930:
        return "一部対象"
    return "非対象"


def build_check_note(row: pd.Series) -> str:
    notes = []
    if row.get("action"):
        notes.append(action_to_label(row.get("action")))
    if "weekly_up" in row.index and pd.notna(row.get("weekly_up")) and float(row.get("weekly_up")) == 1:
        notes.append("週足上向き")
    if "daily_up" in row.index and pd.notna(row.get("daily_up")) and float(row.get("daily_up")) == 1:
        notes.append("日足上向き")
    if pd.notna(row.get("vol_ratio", np.nan)) and float(row.get("vol_ratio")) >= 1.2:
        notes.append("出来高増加")
    if pd.notna(row.get("operating_progress_pct", np.nan)):
        notes.append("決算進捗確認可")
    return "・".join(notes[:4]) if notes else "複数条件を確認対象"


def build_display_dataframe(decision: pd.DataFrame) -> pd.DataFrame:
    if decision.empty:
        return decision.copy()

    df = decision.copy()
    df["優先確認の目安"] = pd.to_numeric(df.get("decision_score", np.nan), errors="coerce").round(1)
    df["アクション"] = df["action"].map(action_to_label) if "action" in df.columns else "要確認"
    df["日足"] = df["daily_up"].map(trend_label) if "daily_up" in df.columns else "要確認"
    df["週足"] = df["weekly_up"].map(trend_label) if "weekly_up" in df.columns else "要確認"
    df["IFD候補"] = df.apply(ifd_label, axis=1)
    df["決算進捗"] = df.apply(lambda r: kabupro_to_label(r.get("kabupro_status"), r.get("kabupro_note")), axis=1)
    df["確認メモ"] = df.apply(build_check_note, axis=1)

    keep_cols = [
        c for c in [
            "code", "優先確認の目安", "アクション", "日足", "週足",
            "IFD候補", "決算進捗", "確認メモ", "total_score", "rr1", "risk_pct",
            "preopen_order_type", "preopen_entry_price", "preopen_take_profit", "preopen_stop_loss",
            "t0930_order_type", "t0930_entry_price", "t0930_take_profit", "t0930_stop_loss",
            "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct",
            "used_report_type", "used_report_date", "kabupro_note",
            "entry_low", "entry_high", "stop", "take1", "take2",
        ] if c in df.columns
    ]
    return df[keep_cols].copy()


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


def show_price_chart_or_placeholder(code: str, row: pd.Series):
    df = load_price_for_code(code)
    if not df.empty:
        tail = df.tail(160)
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=tail["Date"],
                open=tail.get("Open", tail["Price"]),
                high=tail.get("High", tail["Price"]),
                low=tail.get("Low", tail["Price"]),
                close=tail.get("Close", tail["Price"]),
                name="日足",
            )
        )
        fig.add_trace(go.Scatter(x=tail["Date"], y=tail["ma20"], mode="lines", name="MA20"))
        fig.add_trace(go.Scatter(x=tail["Date"], y=tail["ma50"], mode="lines", name="MA50"))
        fig.update_layout(
            height=420,
            xaxis_rangeslider_visible=False,
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    st.markdown('<div class="k8-placeholder">', unsafe_allow_html=True)
    st.subheader("価格チャート未連携")
    st.write("この公開環境では価格CSVが配置されていないため、チャートは表示していません。")
    st.write("その代わりに、現在の候補判定と価格帯情報を下記で確認できます。")
    summary = {
        "優先確認の目安": row.get("decision_score"),
        "総合点": row.get("total_score"),
        "エントリー下限": row.get("entry_low"),
        "エントリー上限": row.get("entry_high"),
        "ストップ": row.get("stop"),
        "利確1": row.get("take1"),
        "利確2": row.get("take2"),
    }
    st.write(summary)
    st.markdown("</div>", unsafe_allow_html=True)


def render_brand_header(data: dict[str, object], display_df: pd.DataFrame):
    raw_last_updated = str(data.get("last_updated_text") or "").strip()
    last_updated = raw_last_updated if raw_last_updated and raw_last_updated.lower() != "unknown" else "未取得"

    target_count = len(data["signals"]) if isinstance(data.get("signals"), pd.DataFrame) else 0
    top_count = len(display_df)
    ifd_count = int((display_df["IFD候補"].isin(["対象", "一部対象"]).sum())) if not display_df.empty and "IFD候補" in display_df.columns else 0

    st.markdown('<div class="k8-hero">', unsafe_allow_html=True)
    col1, col2 = st.columns([3.5, 1.8], gap="large")

    with col1:
        st.title("KABU8 Market Lens")
        st.markdown("**日本株の候補抽出を、毎日ぶれずに。**")
        st.write(
            "テクニカル候補、IFD候補、決算進捗補強を一画面で整理し、"
            "売買判断前の迷いを減らすための判断支援ダッシュボードです。"
        )

    with col2:
        st.metric("最終更新", last_updated)
        st.metric("対象銘柄数", target_count)
        st.metric("注目候補数", top_count)
        st.metric("IFD確認候補", ifd_count)

    st.caption(
        "本サービスは投資助言、利益保証、完全自動売買を行うものではありません。"
        "最終的な投資判断はご自身でお願いします。"
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar(decision: pd.DataFrame):
    with st.sidebar:
        st.markdown("## KABU8 Market Lens")
        st.caption("日本株の候補抽出を、毎日ぶれずに。")

        st.markdown("### 使い方")
        st.markdown(
            "1. 今日の判断ボードで優先候補を確認  \n"
            "2. 注目候補一覧で比較  \n"
            "3. 個別分析で深掘り  \n"
            "4. 更新状況とデータ信頼性を確認"
        )

        st.markdown("### フィルタ")
        action_options = sorted(decision["action"].dropna().unique().tolist()) if not decision.empty and "action" in decision.columns else []
        action_filter = st.multiselect("アクション", options=action_options, default=action_options)

        min_score = st.slider("最低総合点", 0, 100, 55)
        only_ifd = st.checkbox("IFD候補のみ", value=False)
        only_kabupro_ok = st.checkbox("決算進捗補強ありのみ", value=False)
        only_buy_like = st.checkbox("買い候補・戻り初動のみ", value=True)

        st.markdown("### 表示前提")
        st.caption("dashboard_data を優先して読み込み、不足時のみ fallback を参照します。")

        st.markdown("### 免責")
        st.caption(
            "本サービスは投資助言、利益保証、完全自動売買を行うものではありません。"
        )

    return {
        "action_filter": action_filter,
        "min_score": min_score,
        "only_ifd": only_ifd,
        "only_kabupro_ok": only_kabupro_ok,
        "only_buy_like": only_buy_like,
    }


def apply_filters(decision: pd.DataFrame, filters: dict[str, object]) -> pd.DataFrame:
    dff = decision.copy()
    if dff.empty:
        return dff

    action_filter = filters["action_filter"]
    min_score = filters["min_score"]
    only_ifd = filters["only_ifd"]
    only_kabupro_ok = filters["only_kabupro_ok"]
    only_buy_like = filters["only_buy_like"]

    if action_filter:
        dff = dff[dff["action"].isin(action_filter)]
    if "total_score" in dff.columns:
        dff = dff[dff["total_score"].fillna(0) >= min_score]
    if only_ifd:
        cols = [c for c in ["preopen_order_type", "t0930_order_type"] if c in dff.columns]
        if cols:
            dff = dff[dff[cols].notna().any(axis=1)]
    if only_kabupro_ok and "kabupro_status" in dff.columns:
        dff = dff[dff["kabupro_status"].isin(["ok", "success"])]
    if only_buy_like and "action" in dff.columns:
        dff = dff[dff["action"].isin(["買い候補（ブレイク）", "買い候補（押し目）", "監視候補（戻り初動）"])]

    return dff


def render_metrics(data: dict[str, object]):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("全シグナル", len(data["signals"]))  # type: ignore[arg-type]
    c2.metric("買い候補", len(data["buy"]))  # type: ignore[arg-type]
    c3.metric("寄り前IFD", len(data["ifd_preopen"]))  # type: ignore[arg-type]
    c4.metric("9:30IFD", len(data["ifd_0930"]))  # type: ignore[arg-type]
    c5.metric("決算進捗件数", len(data["kabupro"]))  # type: ignore[arg-type]


def render_today_board(display_df: pd.DataFrame):
    st.header("今日の判断ボード")
    st.markdown(
        '<div class="k8-section-caption">今日まず確認したい候補を、優先順に整理しています。</div>',
        unsafe_allow_html=True,
    )

    if display_df.empty:
        st.warning("表示対象がありません。")
        return

    top_df = display_df.head(3).copy()
    cols = st.columns(len(top_df), gap="medium")

    for col, (_, row) in zip(cols, top_df.iterrows()):
        with col:
            st.markdown('<div class="k8-card">', unsafe_allow_html=True)
            st.subheader(f'{row["code"]}')
            st.metric("優先確認の目安", row.get("優先確認の目安"))
            st.write(f'アクション: {row.get("アクション", "要確認")}')
            st.write(f'日足: {row.get("日足", "要確認")}')
            st.write(f'週足: {row.get("週足", "要確認")}')
            st.write(f'IFD候補: {row.get("IFD候補", "非対象")}')
            st.write(f'決算進捗: {row.get("決算進捗", "未取得")}')
            st.caption(str(row.get("確認メモ", "")))
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 確認の考え方")
    st.markdown(
        "- **優先確認の目安**: 当日の確認優先度をまとめた参考値です。  \n"
        "- **IFD候補**: 発注設計の補助材料です。  \n"
        "- **決算進捗**: 補助的な確認情報であり、単独で推奨を意味しません。"
    )


def render_candidate_table(display_df: pd.DataFrame):
    st.header("注目候補一覧")
    st.markdown(
        '<div class="k8-section-caption">複数の判断材料を横断して比較できます。個別分析で詳細を確認してください。</div>',
        unsafe_allow_html=True,
    )

    if display_df.empty:
        st.info("候補がありません。")
        return

    show_cols = [c for c in ["code", "優先確認の目安", "アクション", "日足", "週足", "IFD候補", "決算進捗", "確認メモ"] if c in display_df.columns]
    renamed = display_df[show_cols].rename(columns={"code": "コード"})
    st.dataframe(renamed, use_container_width=True, hide_index=True)

    csv = renamed.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "表示中データをCSVダウンロード",
        data=csv,
        file_name="kabu8_market_lens_candidates.csv",
        mime="text/csv",
    )


def render_detail(decision: pd.DataFrame, display_df: pd.DataFrame):
    st.header("個別分析")
    st.markdown(
        '<div class="k8-section-caption">候補の背景を、価格・テクニカル・補助判断材料の順に確認します。</div>',
        unsafe_allow_html=True,
    )

    if display_df.empty:
        st.info("銘柄がありません。")
        return

    options = display_df["code"].astype(str).tolist()
    selected = st.selectbox("銘柄を選択", options)

    row_df = decision[decision["code"] == selected].head(1)
    if row_df.empty:
        st.info("銘柄詳細がありません。")
        return

    row = row_df.iloc[0]
    a, b = st.columns([1.7, 1.2], gap="large")

    with a:
        show_price_chart_or_placeholder(selected, row)

    with b:
        st.subheader(selected)

        action_label = action_to_label(row.get("action"))
        daily_label = trend_label(row.get("daily_up"))
        weekly_label = trend_label(row.get("weekly_up"))
        ifd_state = ifd_label(row)
        kabupro_state = kabupro_to_label(row.get("kabupro_status"), row.get("kabupro_note"))

        st.write(
            f"現在は {weekly_label} の中で、日足は {daily_label} です。"
            f" IFD候補は {ifd_state}、決算進捗は {kabupro_state} として確認されています。"
        )
        st.metric("優先確認の目安", round(float(row.get("decision_score", np.nan)), 1) if pd.notna(row.get("decision_score", np.nan)) else "-")
        st.write(f"アクション: {action_label}")
        st.write(f"日足: {daily_label}")
        st.write(f"週足: {weekly_label}")
        st.write(f"IFD候補: {ifd_state}")
        st.write(f"決算進捗: {kabupro_state}")

        with st.expander("テクニカル・価格帯の詳細"):
            detail_map = {
                "総合点": row.get("total_score"),
                "RR1": row.get("rr1"),
                "リスク率": row.get("risk_pct"),
                "エントリー下限": row.get("entry_low"),
                "エントリー上限": row.get("entry_high"),
                "ストップ": row.get("stop"),
                "利確1": row.get("take1"),
                "利確2": row.get("take2"),
            }
            st.write(detail_map)

        with st.expander("IFD / 決算進捗メモ"):
            notes = []
            if pd.notna(row.get("preopen_order_type", np.nan)):
                notes.append(f"寄り前: {row.get('preopen_order_type')} / entry={row.get('preopen_entry_price')}")
            if pd.notna(row.get("t0930_order_type", np.nan)):
                notes.append(f"9:30: {row.get('t0930_order_type')} / entry={row.get('t0930_entry_price')}")
            if pd.notna(row.get("used_report_type", np.nan)) or pd.notna(row.get("used_report_date", np.nan)):
                notes.append(f"決算資料: {row.get('used_report_type')} / {row.get('used_report_date')}")
            if pd.notna(row.get("kabupro_note", np.nan)):
                notes.append(f"決算進捗メモ: {row.get('kabupro_note')}")
            if notes:
                for n in notes:
                    st.write("-", n)
            else:
                st.caption("追加メモはありません。")


def render_aux_materials(decision: pd.DataFrame):
    st.header("補助判断材料")
    st.markdown(
        '<div class="k8-section-caption">候補判断を補足する情報として、IFD候補と決算進捗補強を確認します。</div>',
        unsafe_allow_html=True,
    )

    if decision.empty:
        st.info("補助判断材料がありません。")
        return

    aux1, aux2 = st.columns(2, gap="large")

    with aux1:
        st.subheader("IFD候補の確認")
        pre = decision[decision.get("preopen_order_type", pd.Series(index=decision.index)).notna()].copy()
        d930 = decision[decision.get("t0930_order_type", pd.Series(index=decision.index)).notna()].copy()

        st.markdown("##### 寄り前 IFD")
        cols = [c for c in ["code", "action", "decision_score", "preopen_order_type", "preopen_entry_price", "preopen_take_profit", "preopen_stop_loss"] if c in pre.columns]
        if cols:
            tmp = pre[cols].head(10).copy()
            for c in tmp.columns:
                if pd.api.types.is_numeric_dtype(tmp[c]):
                    tmp[c] = tmp[c].round(2)
            st.dataframe(tmp.rename(columns={"code": "コード", "action": "判定"}), use_container_width=True, hide_index=True)
        else:
            st.caption("寄り前 IFD 候補はありません。")

        st.markdown("##### 9:30 IFD")
        cols = [c for c in ["code", "action", "decision_score", "t0930_order_type", "t0930_entry_price", "t0930_take_profit", "t0930_stop_loss"] if c in d930.columns]
        if cols:
            tmp = d930[cols].head(10).copy()
            for c in tmp.columns:
                if pd.api.types.is_numeric_dtype(tmp[c]):
                    tmp[c] = tmp[c].round(2)
            st.dataframe(tmp.rename(columns={"code": "コード", "action": "判定"}), use_container_width=True, hide_index=True)
        else:
            st.caption("9:30 IFD 候補はありません。")

    with aux2:
        st.subheader("決算進捗の確認")
        cols = [c for c in ["code", "used_report_date", "used_report_type", "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct", "kabupro_status", "kabupro_note"] if c in decision.columns]
        if cols:
            tmp = decision[cols].head(15).copy()
            tmp["状態"] = tmp.apply(lambda r: kabupro_to_label(r.get("kabupro_status"), r.get("kabupro_note")), axis=1)
            show_cols = [c for c in ["code", "used_report_date", "used_report_type", "sales_progress_pct", "operating_progress_pct", "ordinary_progress_pct", "状態"] if c in tmp.columns]
            for c in show_cols:
                if c in tmp.columns and pd.api.types.is_numeric_dtype(tmp[c]):
                    tmp[c] = tmp[c].round(2)
            st.dataframe(
                tmp[show_cols].rename(columns={
                    "code": "コード",
                    "used_report_date": "資料日付",
                    "used_report_type": "資料種別",
                    "sales_progress_pct": "売上進捗",
                    "operating_progress_pct": "営業益進捗",
                    "ordinary_progress_pct": "経常益進捗",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("決算進捗データはありません。")


def render_quality_panel(data: dict[str, object]):
    st.header("更新状況とデータ信頼性")
    st.markdown(
        '<div class="k8-section-caption">表示中のデータがいつ更新され、どのソースから読み込まれたかを確認できます。</div>',
        unsafe_allow_html=True,
    )

    raw_last_updated = str(data.get("last_updated_text") or "").strip()
    last_updated = raw_last_updated if raw_last_updated and raw_last_updated.lower() != "unknown" else "未取得"

    tech_status_label = "正常" if isinstance(data.get("technical_summary"), pd.DataFrame) and not data["technical_summary"].empty else "未取得"
    kabupro_status_label = "正常" if isinstance(data.get("kabupro_summary"), pd.DataFrame) and not data["kabupro_summary"].empty else "未取得"
    price_status_label = "未連携でも表示可"

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("最終更新", last_updated)
    q2.metric("テクニカル更新", tech_status_label)
    q3.metric("決算進捗補強", kabupro_status_label)
    q4.metric("価格データ状態", price_status_label)

    tab1, tab2 = st.tabs(["読込元", "実行状況"])

    with tab1:
        source_status = data.get("source_status", {})
        if isinstance(source_status, dict):
            source_df = pd.DataFrame([{"データ": k, "読込元": v} for k, v in source_status.items()])
            st.dataframe(source_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("テクニカル実行状況")
        if isinstance(data.get("technical_summary"), pd.DataFrame):
            st.dataframe(data["technical_summary"], use_container_width=True, hide_index=True)

        st.subheader("決算進捗実行状況")
        if isinstance(data.get("kabupro_summary"), pd.DataFrame):
            st.dataframe(data["kabupro_summary"], use_container_width=True, hide_index=True)

        if isinstance(data.get("run_daily_summary"), pd.DataFrame) and not data["run_daily_summary"].empty:
            st.subheader("日次実行サマリー")
            st.dataframe(data["run_daily_summary"], use_container_width=True, hide_index=True)


def main():
    if st.button("再読込"):
        st.cache_data.clear()
        st.rerun()

    data = load_data()
    decision = merge_decision_frame(data)
    filters = render_sidebar(decision)
    decision_filtered = apply_filters(decision, filters)
    display_df = build_display_dataframe(decision_filtered)

    render_brand_header(data, display_df)
    render_metrics(data)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["今日の判断ボード", "注目候補一覧", "個別分析", "更新状況とデータ信頼性"]
    )

    with tab1:
        render_today_board(display_df)

    with tab2:
        render_candidate_table(display_df)

    with tab3:
        base_df = decision_filtered if not decision_filtered.empty else decision
        render_detail(base_df, build_display_dataframe(base_df))

    with tab4:
        base_df = decision_filtered if not decision_filtered.empty else decision
        render_aux_materials(base_df)
        st.markdown("---")
        render_quality_panel(data)


if __name__ == "__main__":
    main()
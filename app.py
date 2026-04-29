# GitHub連携テスト用のコメントです。
import streamlit as st

from config import TIMEFRAME_CONFIG, PERIOD_CONFIG, INTRADAY_TIMEFRAMES
from utils import parse_symbols
from ui import build_summary_table, render_symbol_view
from favorites import load_favorites, save_favorite

# 画面の基本設定です。
st.set_page_config(
    page_title="株価ウォッチ + 移動平均",
    page_icon="📈",
    layout="centered",
)

st.markdown(
    """
    <style>
    :root {
        --stock-blue: #2563eb;
        --stock-teal: #14b8a6;
        --stock-coral: #f97316;
        --stock-gold: #f59e0b;
        --stock-ink: #172033;
        --stock-muted: #667085;
        --stock-border: #d7e3f5;
        --stock-soft: #f7fbff;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(20, 184, 166, 0.16), transparent 28rem),
            radial-gradient(circle at top right, rgba(249, 115, 22, 0.12), transparent 26rem),
            linear-gradient(180deg, #f7fbff 0%, #ffffff 38%, #fffaf3 100%);
        color: var(--stock-ink);
    }
    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #ecfeff 0%, #fff7ed 48%, #eef2ff 100%);
        border-right: 1px solid var(--stock-border);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #0f766e;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #475467;
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    .hero-panel {
        border: 1px solid rgba(37, 99, 235, 0.18);
        border-radius: 18px;
        padding: 1.4rem 1.5rem 1.25rem;
        margin-bottom: 1.3rem;
        background:
            linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(20, 184, 166, 0.12) 45%, rgba(249, 115, 22, 0.1));
        box-shadow: 0 16px 40px rgba(23, 32, 51, 0.08);
    }
    .app-title {
        font-size: clamp(2.2rem, 4.2vw, 4rem);
        font-weight: 700;
        line-height: 1.15;
        letter-spacing: 0;
        white-space: nowrap;
        margin: 0 0 0.35rem 0;
        color: #172033;
    }
    .app-title span {
        color: var(--stock-blue);
    }
    .hero-copy {
        color: var(--stock-muted);
        font-size: 1rem;
        margin: 0.25rem 0 0;
    }
    h2, h3 {
        color: #172033;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid var(--stock-border);
        border-top: 4px solid var(--stock-teal);
        border-radius: 14px;
        padding: 0.75rem 0.85rem;
        box-shadow: 0 10px 24px rgba(23, 32, 51, 0.06);
    }
    div[data-testid="stMetricValue"] {
        color: var(--stock-ink);
        font-size: 1.4rem !important;
    }
    div[data-testid="stMetric"] label {
        color: #475467;
        font-size: 0.8rem !important;
        white-space: normal !important;
    }
    div[data-testid="stMetricValue"] > div {
        white-space: normal !important;
        word-break: break-word !important;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--stock-border);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 10px 28px rgba(23, 32, 51, 0.05);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
        border-bottom: 1px solid var(--stock-border);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px 999px 0 0;
        padding: 0.55rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        color: #dc2626;
        background: #fff7ed;
    }
    .stButton > button,
    .stDownloadButton > button {
        border: 0;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--stock-blue), var(--stock-teal));
        color: white;
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.2);
    }
    div[data-baseweb="input"] input,
    textarea,
    div[data-baseweb="select"] > div {
        border-color: var(--stock-border);
        background-color: rgba(255, 255, 255, 0.9);
    }
    @media (max-width: 720px) {
        .app-title {
            white-space: normal;
            font-size: 2.15rem;
        }
        .hero-panel {
            padding: 1.1rem;
            border-radius: 14px;
        }
    }
    </style>
    <div class="hero-panel">
        <h1 class="app-title">株価ウォッチ <span>+ 移動平均</span>表示アプリ</h1>
        <p class="hero-copy">価格・移動平均・RSI・MACDを、少し明るいダッシュボードで確認できます。</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("学習用の参考アプリです。売買の判断を自動で行うものではありません。")
st.write("設定はサイドバー、結果はメイン画面で確認できます。")

favorites_dict = load_favorites()

def on_favorite_change():
    selected = st.session_state.fav_selectbox
    if selected != "(選択しない)":
        st.session_state.user_input = favorites_dict[selected]

with st.sidebar:
    st.header("表示設定")
    st.caption("銘柄コードや時間軸、表示期間、チャート形式をここで切り替えます。")

    st.subheader("★ お気に入り")
    fav_options = ["(選択しない)"] + list(favorites_dict.keys())
    st.selectbox(
        "保存したリストから読み込む", 
        options=fav_options, 
        key="fav_selectbox", 
        on_change=on_favorite_change
    )

    if "user_input" not in st.session_state:
        st.session_state.user_input = favorites_dict.get("デフォルト (GAFAM)", "AAPL, MSFT, GOOGL, AMZN, META")

    user_input = st.text_area(
        "銘柄コード",
        key="user_input",
        help="AAPL, MSFT, 7203 のようにカンマ区切りで複数入力できます。改行でも入力できます。",
        height=100,
    )

    with st.expander("今入力している銘柄を保存"):
        new_fav_name = st.text_input("お気に入り名（例: 半導体）", key="new_fav_name")
        if st.button("保存する"):
            if new_fav_name and user_input:
                save_favorite(new_fav_name, user_input)
                st.success(f"「{new_fav_name}」を保存しました！")
                st.rerun()
    selected_timeframe = st.selectbox(
        "時間軸",
        options=list(TIMEFRAME_CONFIG.keys()),
        index=2,
    )
    selected_period_label = st.selectbox(
        "表示期間",
        options=list(PERIOD_CONFIG.keys()),
        index=2,
    )
    today_only_available = selected_timeframe in INTRADAY_TIMEFRAMES
    today_only = st.checkbox(
        "当日だけ表示",
        value=False,
        help="1時間足・30分足・15分足・5分足のときに、最新日のデータだけへ絞り込みます。",
        disabled=not today_only_available,
    )
    if not today_only_available:
        today_only = False
    chart_style = st.radio(
        "株価チャート表示",
        options=["ローソク足表示", "線グラフ表示"],
        index=0,
    )
    st.markdown("---")
    st.caption("例: `AAPL, MSFT, 7203`")

symbols = parse_symbols(user_input)

if symbols:
    st.write("複数銘柄を比較しやすいように、銘柄ごとにタブで表示しています。")
    summary_df = build_summary_table(symbols, selected_timeframe, selected_period_label, today_only)

    if not summary_df.empty and len(symbols) > 1:
        st.subheader("複数銘柄の比較一覧")
        st.caption("まずここで全体を比べて、詳しく見たい銘柄を下のタブで開けます。")
        st.dataframe(
            summary_df.style.format(
                {
                    column: "{:,.2f}"
                    for column in summary_df.columns
                    if column not in ["銘柄コード", "銘柄名", "RSIコメント"]
                }
            ),
            width="stretch",
        )

    if len(symbols) == 1:
        render_symbol_view(symbols[0], selected_timeframe, selected_period_label, chart_style, today_only)
    else:
        tabs = st.tabs(symbols)
        for tab, symbol in zip(tabs, symbols):
            with tab:
                render_symbol_view(symbol, selected_timeframe, selected_period_label, chart_style, today_only)
else:
    st.info("サイドバーに銘柄コードを1つ以上入力してください。")

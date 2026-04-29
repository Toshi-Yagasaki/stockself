import pandas as pd
import streamlit as st

from config import TIMEFRAME_CONFIG, INTRADAY_TIMEFRAMES
from data import (
    resolve_request_period,
    load_symbol_name,
    load_price_data,
    filter_today_data,
    add_moving_averages,
    add_rsi,
    add_macd,
    load_news,
)
from charts import (
    build_candlestick_chart,
    build_line_chart,
    calculate_y_axis_domain,
    build_macd_chart,
)

def get_rsi_comment(rsi_value: float) -> str:
    """
    RSI の値に応じた参考コメントを返します。
    """
    if pd.isna(rsi_value):
        return "RSIは、まだ計算できるだけのデータがありません。"
    if rsi_value >= 70:
        return "RSIは高めです"
    if rsi_value <= 30:
        return "RSIは低めです"
    return "RSIは中間くらいです"


def get_macd_comment(macd_value: float, signal_value: float) -> str:
    """
    MACD の最新状態に応じた参考コメントを返します。
    """
    if pd.isna(macd_value) or pd.isna(signal_value):
        return "MACDは、まだ計算できるだけのデータがありません。"
    if macd_value > signal_value:
        return "MACDがシグナルラインより上です"
    if macd_value < signal_value:
        return "MACDがシグナルラインより下です"
    return "MACDがシグナルラインとほぼ同じです"


def compare_price_and_line(latest_price: float, line_value: float, line_name: str) -> str:
    """
    最新株価が移動平均線より上か下かを、日本語で返します。
    """
    if pd.isna(line_value):
        return f"{line_name}は、まだ計算できるだけのデータがありません。"

    if latest_price > line_value:
        return f"最新株価は {line_name} より上です。"
    if latest_price < line_value:
        return f"最新株価は {line_name} より下です。"
    return f"最新株価は {line_name} とほぼ同じです。"


def build_export_data(df: pd.DataFrame, ma5_label: str, ma25_label: str) -> pd.DataFrame:
    """
    CSV 保存用のデータを作ります。
    画面に出している列を、そのまま分かりやすい名前で並べます。
    """
    export_df = df[["Open", "High", "Low", "Close", "MA5", "MA25", "RSI14", "MACD", "Signal", "Histogram"]].copy().reset_index()
    export_df = export_df.rename(
        columns={
            export_df.columns[0]: "Date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "MA5": ma5_label,
            "MA25": ma25_label,
            "RSI14": "RSI(14)",
            "MACD": "MACD",
            "Signal": "Signal",
            "Histogram": "Histogram",
        }
    )
    return export_df


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """
    DataFrame を CSV 文字列に変えて、ダウンロードしやすい形にします。
    CSV は、表データを保存するときによく使うシンプルな形式です。
    """
    return df.to_csv(index=False).encode("utf-8-sig")


def build_download_filename(symbol: str) -> str:
    """
    ダウンロード用のファイル名を分かりやすく整えます。
    """
    filename_symbol = symbol.replace(".T", "")
    return f"stock_data_{filename_symbol}.csv"


def build_summary_row(
    symbol: str,
    selected_timeframe: str,
    selected_period_label: str,
    today_only: bool,
) -> dict[str, object] | None:
    """
    複数銘柄を見比べるための一覧表1行分を作ります。
    """
    timeframe = TIMEFRAME_CONFIG[selected_timeframe]
    request_period, _ = resolve_request_period(selected_timeframe, selected_period_label)
    ma5_label = f"5{timeframe['unit']}移動平均"
    ma25_label = f"25{timeframe['unit']}移動平均"

    symbol_name = load_symbol_name(symbol)
    price_df = load_price_data(
        symbol,
        period=request_period,
        interval=timeframe["interval"],
    )

    if price_df.empty:
        return None

    if today_only and selected_timeframe in INTRADAY_TIMEFRAMES:
        price_df = filter_today_data(price_df)

    if price_df.empty:
        return None

    price_df = add_moving_averages(price_df)
    price_df = add_rsi(price_df)
    price_df = add_macd(price_df)

    latest_close = price_df["Close"].iloc[-1]
    latest_ma5 = price_df["MA5"].iloc[-1]
    latest_ma25 = price_df["MA25"].iloc[-1]
    latest_rsi = price_df["RSI14"].iloc[-1]
    latest_macd = price_df["MACD"].iloc[-1]

    return {
        "銘柄コード": symbol,
        "銘柄名": symbol_name,
        "最新終値": latest_close,
        ma5_label: latest_ma5,
        ma25_label: latest_ma25,
        "RSI(14)": latest_rsi,
        "MACD": latest_macd,
        "RSIコメント": get_rsi_comment(latest_rsi),
    }


def build_summary_table(
    symbols: list[str],
    selected_timeframe: str,
    selected_period_label: str,
    today_only: bool,
) -> pd.DataFrame:
    """
    複数銘柄の比較表を作ります。
    """
    summary_rows = []

    for symbol in symbols:
        row = build_summary_row(symbol, selected_timeframe, selected_period_label, today_only)
        if row is not None:
            summary_rows.append(row)

    return pd.DataFrame(summary_rows)


def render_symbol_view(
    symbol: str,
    selected_timeframe: str,
    selected_period_label: str,
    chart_style: str,
    today_only: bool,
) -> None:
    """
    1銘柄分の表示をまとめた関数です。
    複数銘柄でも、この関数を繰り返し呼べば同じ見た目で表示できます。
    """
    timeframe = TIMEFRAME_CONFIG[selected_timeframe]
    request_period, period_notice = resolve_request_period(
        selected_timeframe,
        selected_period_label,
    )
    ma5_label = f"5{timeframe['unit']}移動平均"
    ma25_label = f"25{timeframe['unit']}移動平均"

    with st.spinner(f"{symbol} の銘柄情報を確認しています..."):
        symbol_name = load_symbol_name(symbol)

    st.subheader(f"{symbol_name} ({symbol})")
    display_scope = "当日だけ表示" if today_only and selected_timeframe in INTRADAY_TIMEFRAMES else f"表示期間: {selected_period_label}"
    st.caption(f"表示中の時間軸: {selected_timeframe} / {display_scope}")
    if period_notice:
        st.warning(period_notice)
    if today_only and selected_timeframe not in INTRADAY_TIMEFRAMES:
        st.info("当日だけ表示は、1時間足・30分足・15分足・5分足のときに使えます。")

    with st.spinner(f"{symbol} の株価データを取得しています..."):
        price_df = load_price_data(
            symbol,
            period=request_period,
            interval=timeframe["interval"],
        )

    if price_df.empty:
        st.error(
            "株価データを取得できませんでした。銘柄コードが正しいか、通信できる状態かを確認してください。"
        )
        return

    if today_only and selected_timeframe in INTRADAY_TIMEFRAMES:
        price_df = filter_today_data(price_df)

    if price_df.empty:
        st.warning("当日データが見つからなかったため、表示できませんでした。")
        return

    price_df = add_moving_averages(price_df)
    price_df = add_rsi(price_df)
    price_df = add_macd(price_df)

    latest_close = price_df["Close"].iloc[-1]
    latest_ma5 = price_df["MA5"].iloc[-1]
    latest_ma25 = price_df["MA25"].iloc[-1]
    latest_rsi = price_df["RSI14"].iloc[-1]
    latest_macd = price_df["MACD"].iloc[-1]
    latest_signal = price_df["Signal"].iloc[-1]
    latest_histogram = price_df["Histogram"].iloc[-1]

    st.subheader("最新データ")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("最新終値", f"{latest_close:,.2f}")
    col2.metric(ma5_label, "-" if pd.isna(latest_ma5) else f"{latest_ma5:,.2f}")
    col3.metric(ma25_label, "-" if pd.isna(latest_ma25) else f"{latest_ma25:,.2f}")
    col4.metric("RSI(14)", "-" if pd.isna(latest_rsi) else f"{latest_rsi:,.2f}")
    col5.metric("MACD", "-" if pd.isna(latest_macd) else f"{latest_macd:,.4f}")

    st.subheader("判定メッセージ")
    st.info(compare_price_and_line(latest_close, latest_ma5, ma5_label))
    st.info(compare_price_and_line(latest_close, latest_ma25, ma25_label))
    st.info(get_rsi_comment(latest_rsi))
    st.info(get_macd_comment(latest_macd, latest_signal))
    st.caption("RSIは、最近の値動きの強さを 0 から 100 で見やすくした参考指標です。")
    st.caption("MACDは、短期と長期の流れの差を見やすくした参考指標です。")
    st.caption("表示内容は参考情報です。将来の値動きや売買を示すものではありません。")

    st.subheader(f"{selected_timeframe}チャート")
    y_axis_domain = calculate_y_axis_domain(price_df)
    if chart_style == "ローソク足表示":
        st.altair_chart(
            build_candlestick_chart(price_df, ma5_label, ma25_label, y_axis_domain),
            width="stretch",
        )
        st.caption("ローソク足に移動平均線を重ねて表示しています。縦軸は見やすいように自動調整しています。")
    else:
        st.altair_chart(
            build_line_chart(price_df, ma5_label, ma25_label, y_axis_domain),
            width="stretch",
        )
        st.caption("終値と移動平均線を線グラフで表示しています。縦軸は見やすいように自動調整しています。")

    st.subheader("MACDチャート")
    macd_col1, macd_col2, macd_col3 = st.columns(3)
    macd_col1.metric("MACDライン", "-" if pd.isna(latest_macd) else f"{latest_macd:,.4f}")
    macd_col2.metric("シグナルライン", "-" if pd.isna(latest_signal) else f"{latest_signal:,.4f}")
    macd_col3.metric("ヒストグラム", "-" if pd.isna(latest_histogram) else f"{latest_histogram:,.4f}")
    st.altair_chart(build_macd_chart(price_df), width="stretch")
    st.caption("緑と赤の棒がヒストグラム、線が MACD ラインとシグナルラインです。")

    export_df = build_export_data(price_df, ma5_label, ma25_label)
    csv_data = convert_df_to_csv(export_df)

    st.subheader("データ表")
    st.dataframe(
        export_df.tail(10).style.format(
            {
                "Open": "{:,.2f}",
                "High": "{:,.2f}",
                "Low": "{:,.2f}",
                "Close": "{:,.2f}",
                ma5_label: "{:,.2f}",
                ma25_label: "{:,.2f}",
                "RSI(14)": "{:,.2f}",
                "MACD": "{:,.4f}",
                "Signal": "{:,.4f}",
                "Histogram": "{:,.4f}",
            }
        ),
        width="stretch",
    )
    st.subheader("CSV保存")
    st.caption("上の表に表示しているデータを、そのままCSVで保存できます。")
    st.download_button(
        label="CSVダウンロード",
        data=csv_data,
        file_name=build_download_filename(symbol),
        mime="text/csv",
        key=f"download_{symbol}_{selected_timeframe}_{selected_period_label}",
    )

    st.subheader("直近のニュース")
    yahoo_finance_url = f"https://finance.yahoo.co.jp/quote/{symbol}"
    st.markdown(f"🔗 **[Yahoo!ファイナンスで {symbol_name} ({symbol}) の詳細・掲示板を見る]({yahoo_finance_url})**")

    with st.spinner("ニュースを取得しています..."):
        news_items = load_news(symbol)
        
    if news_items:
        for item in news_items[:5]:
            pub_date_str = item["pubDate"]
            date_display = ""
            if pub_date_str:
                try:
                    date_display = pub_date_str.split("T")[0].replace("-", "/")
                except Exception:
                    date_display = pub_date_str
            
            provider_text = f" ({item['provider']})" if item['provider'] else ""
            date_text = f" [{date_display}]" if date_display else ""
            st.markdown(f"- [{item['title']}]({item['url']}){provider_text}{date_text}")
    else:
        st.info("関連するニュースは見つかりませんでした。")

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf


# 画面の基本設定です。
st.set_page_config(
    page_title="株価ウォッチ + 移動平均",
    page_icon="📈",
    layout="centered",
)


TIMEFRAME_CONFIG = {
    "月足": {"period": "10y", "interval": "1mo", "unit": "か月"},
    "週足": {"period": "5y", "interval": "1wk", "unit": "週"},
    "日足": {"period": "6mo", "interval": "1d", "unit": "日"},
    "1時間足": {"period": "60d", "interval": "1h", "unit": "時間", "max_period": "1y"},
    "30分足": {"period": "60d", "interval": "30m", "unit": "本", "max_period": "1mo"},
    "15分足": {"period": "30d", "interval": "15m", "unit": "本", "max_period": "1mo"},
    "5分足": {"period": "30d", "interval": "5m", "unit": "本", "max_period": "1mo"},
}

PERIOD_CONFIG = {
    "1か月": {"period": "1mo"},
    "3か月": {"period": "3mo"},
    "6か月": {"period": "6mo"},
    "1年": {"period": "1y"},
}

PERIOD_ORDER = ["1mo", "3mo", "6mo", "1y"]
INTRADAY_TIMEFRAMES = {"1時間足", "30分足", "15分足", "5分足"}
PRICE_LINE_COLORS = ["#2563eb", "#f97316", "#14b8a6"]
MACD_LINE_COLORS = ["#7c3aed", "#f59e0b"]


def normalize_symbol(user_input: str) -> str:
    """
    入力された銘柄コードを、取得しやすい形に整えます。

    例:
    - AAPL   -> AAPL
    - 7203   -> 7203.T  （日本株として扱う）
    """
    symbol = user_input.strip().upper()

    # 数字だけなら、日本株のコードと考えて .T を付けます。
    if symbol.isdigit():
        return f"{symbol}.T"

    return symbol


def parse_symbols(user_input: str) -> list[str]:
    """
    カンマ区切りや改行区切りで入力された複数銘柄を整えます。
    例: AAPL, MSFT, 7203
    """
    raw_items = user_input.replace("\n", ",").split(",")
    symbols = []

    for item in raw_items:
        if not item.strip():
            continue

        normalized_symbol = normalize_symbol(item)
        if normalized_symbol not in symbols:
            symbols.append(normalized_symbol)

    return symbols


@st.cache_data(show_spinner=False)
def load_price_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    """
    yfinance を使って株価データを取得します。
    無料で使える方法として、学習用の小さなアプリに向いています。
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    # データが取れなかったときに備えて、必要な列だけを確認します。
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()

    # 日付を見やすく扱うため、タイムゾーン情報は外しておきます。
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)

    return df


@st.cache_data(show_spinner=False)
def load_symbol_name(symbol: str) -> str:
    """
    銘柄名を取得します。取得できないときは銘柄コードをそのまま返します。
    """
    ticker = yf.Ticker(symbol)

    try:
        info = ticker.info
    except Exception:
        return symbol

    return (
        info.get("shortName")
        or info.get("longName")
        or info.get("displayName")
        or symbol
    )


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    移動平均線を追加します。
    移動平均は「直近の平均」を線で見やすくしたものです。
    """
    result = df.copy()
    result["MA5"] = result["Close"].rolling(window=5).mean()
    result["MA25"] = result["Close"].rolling(window=25).mean()
    return result


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    RSI を追加します。
    RSI は、最近の値動きの強さを 0 から 100 の範囲で見やすくした指標です。
    """
    result = df.copy()
    close_diff = result["Close"].diff()
    up = close_diff.clip(lower=0)
    down = -close_diff.clip(upper=0)

    # 初心者向けに単純移動平均で計算しています。
    average_up = up.rolling(window=period).mean()
    average_down = down.rolling(window=period).mean()

    rs = average_up / average_down
    result["RSI14"] = 100 - (100 / (1 + rs))

    # 下落が全くないときは RSI を 100 として扱います。
    result.loc[(average_down == 0) & average_up.notna(), "RSI14"] = 100

    return result


def add_macd(
    df: pd.DataFrame,
    short_period: int = 12,
    long_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """
    MACD を追加します。
    MACD は、短めの平均と長めの平均の差を見て、流れの変化をつかみやすくした指標です。
    """
    result = df.copy()
    short_ema = result["Close"].ewm(span=short_period, adjust=False).mean()
    long_ema = result["Close"].ewm(span=long_period, adjust=False).mean()

    result["MACD"] = short_ema - long_ema
    result["Signal"] = result["MACD"].ewm(span=signal_period, adjust=False).mean()
    result["Histogram"] = result["MACD"] - result["Signal"]

    return result


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


def resolve_request_period(selected_timeframe: str, selected_period_label: str) -> tuple[str, str | None]:
    """
    時間軸と期間の組み合わせから、yfinance に渡す取得期間を決めます。
    短い時間軸は取得できる期間に制限があるため、必要なときだけ短い期間に調整します。
    """
    timeframe = TIMEFRAME_CONFIG[selected_timeframe]
    request_period = PERIOD_CONFIG[selected_period_label]["period"]
    max_period = timeframe.get("max_period")

    if max_period and PERIOD_ORDER.index(request_period) > PERIOD_ORDER.index(max_period):
        return (
            max_period,
            f"{selected_timeframe}は取得できる期間に制限があるため、{selected_period_label}の代わりに表示可能な範囲で表示しています。",
        )

    return request_period, None


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


def filter_today_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    取得済みデータのうち、最新日と同じ日付だけに絞ります。
    当日分だけ見たいときに使います。
    """
    if df.empty:
        return df

    latest_date = df.index.max().date()
    return df[df.index.date == latest_date].copy()


def build_chart_view_data(
    df: pd.DataFrame,
    ma5_label: str,
    ma25_label: str,
) -> pd.DataFrame:
    """
    Altair で扱いやすい縦長データへ変換します。
    """
    chart_df = df[["Close", "MA5", "MA25"]].copy().reset_index()
    chart_df.columns = ["Date", "Close", ma5_label, ma25_label]
    return chart_df.melt(
        id_vars="Date",
        value_vars=["Close", ma5_label, ma25_label],
        var_name="Series",
        value_name="Price",
    )


def build_candlestick_chart(
    df: pd.DataFrame,
    ma5_label: str,
    ma25_label: str,
    y_axis_domain: list[float],
) -> alt.Chart:
    """
    ローソク足と移動平均線を 1つのチャートにまとめます。
    """
    chart_df = df[["Open", "High", "Low", "Close", "MA5", "MA25"]].copy().reset_index()
    chart_df.columns = ["Date", "Open", "High", "Low", "Close", ma5_label, ma25_label]
    chart_df["Up"] = chart_df["Close"] >= chart_df["Open"]

    wick_chart = (
        alt.Chart(chart_df)
        .mark_rule()
        .encode(
            x=alt.X("Date:T", title="日時"),
            y=alt.Y("Low:Q", title="価格", scale=alt.Scale(domain=y_axis_domain, zero=False)),
            y2="High:Q",
            color=alt.condition(alt.datum.Up, alt.value("#d32f2f"), alt.value("#1976d2")),
            tooltip=[
                alt.Tooltip("Date:T", title="日時"),
                alt.Tooltip("Open:Q", title="始値", format=",.2f"),
                alt.Tooltip("High:Q", title="高値", format=",.2f"),
                alt.Tooltip("Low:Q", title="安値", format=",.2f"),
                alt.Tooltip("Close:Q", title="終値", format=",.2f"),
            ],
        )
    )

    body_chart = (
        alt.Chart(chart_df)
        .mark_bar(size=8)
        .encode(
            x=alt.X("Date:T", title="日時"),
            y=alt.Y("Open:Q", title="価格", scale=alt.Scale(domain=y_axis_domain, zero=False)),
            y2="Close:Q",
            color=alt.condition(alt.datum.Up, alt.value("#ef5350"), alt.value("#42a5f5")),
            tooltip=[
                alt.Tooltip("Date:T", title="日時"),
                alt.Tooltip("Open:Q", title="始値", format=",.2f"),
                alt.Tooltip("High:Q", title="高値", format=",.2f"),
                alt.Tooltip("Low:Q", title="安値", format=",.2f"),
                alt.Tooltip("Close:Q", title="終値", format=",.2f"),
            ],
        )
    )

    line_df = chart_df.melt(
        id_vars="Date",
        value_vars=[ma5_label, ma25_label],
        var_name="Series",
        value_name="Price",
    )

    ma_chart = (
        alt.Chart(line_df)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title="日時"),
            y=alt.Y("Price:Q", title="価格", scale=alt.Scale(domain=y_axis_domain, zero=False)),
            color=alt.Color(
                "Series:N",
                title="系列",
                scale=alt.Scale(
                    domain=[ma5_label, ma25_label],
                    range=PRICE_LINE_COLORS[1:],
                ),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="日時"),
                alt.Tooltip("Series:N", title="系列"),
                alt.Tooltip("Price:Q", title="価格", format=",.2f"),
            ],
        )
    )

    return (wick_chart + body_chart + ma_chart).properties(height=420).interactive()


def build_line_chart(
    df: pd.DataFrame,
    ma5_label: str,
    ma25_label: str,
    y_axis_domain: list[float],
) -> alt.Chart:
    """
    終値と移動平均線を線グラフで表示します。
    """
    chart_view_df = build_chart_view_data(df, ma5_label, ma25_label)

    return (
        alt.Chart(chart_view_df)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title="日時"),
            y=alt.Y("Price:Q", title="価格", scale=alt.Scale(domain=y_axis_domain, zero=False)),
            color=alt.Color(
                "Series:N",
                title="系列",
                scale=alt.Scale(
                    domain=["Close", ma5_label, ma25_label],
                    range=PRICE_LINE_COLORS,
                ),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="日時"),
                alt.Tooltip("Series:N", title="系列"),
                alt.Tooltip("Price:Q", title="価格", format=",.2f"),
            ],
        )
        .properties(height=420)
        .interactive()
    )


def calculate_y_axis_domain(df: pd.DataFrame) -> list[float]:
    """
    値動きが小さい銘柄でも線がつぶれにくいよう、表示範囲に余白を持たせます。
    """
    price_values = df[["Open", "High", "Low", "Close", "MA5", "MA25"]].stack().dropna()

    if price_values.empty:
        return [0.0, 1.0]

    min_value = float(price_values.min())
    max_value = float(price_values.max())
    spread = max_value - min_value

    if spread == 0:
        padding = max(abs(max_value) * 0.02, 1.0)
    else:
        padding = spread * 0.1

    return [min_value - padding, max_value + padding]


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


def build_macd_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    MACD チャート用に、日時つきのデータを作ります。
    """
    chart_df = df[["MACD", "Signal", "Histogram"]].copy().reset_index()
    chart_df.columns = ["Date", "MACD", "Signal", "Histogram"]
    return chart_df


def build_macd_chart(df: pd.DataFrame) -> alt.Chart:
    """
    MACD ライン、シグナルライン、ヒストグラムを 1つのグラフで表示します。
    """
    macd_chart_df = build_macd_chart_data(df)

    histogram_chart = (
        alt.Chart(macd_chart_df)
        .mark_bar(opacity=0.45)
        .encode(
            x=alt.X("Date:T", title="日時"),
            y=alt.Y("Histogram:Q", title="MACD"),
            color=alt.condition(
                alt.datum.Histogram >= 0,
                alt.value("#2e7d32"),
                alt.value("#c62828"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="日時"),
                alt.Tooltip("Histogram:Q", title="ヒストグラム", format=",.4f"),
            ],
        )
    )

    line_data = macd_chart_df.melt(
        id_vars="Date",
        value_vars=["MACD", "Signal"],
        var_name="Series",
        value_name="Value",
    )

    line_chart = (
        alt.Chart(line_data)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title="日時"),
            y=alt.Y("Value:Q", title="MACD"),
            color=alt.Color(
                "Series:N",
                title="系列",
                scale=alt.Scale(domain=["MACD", "Signal"], range=MACD_LINE_COLORS),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="日時"),
                alt.Tooltip("Series:N", title="系列"),
                alt.Tooltip("Value:Q", title="値", format=",.4f"),
            ],
        )
    )

    return (histogram_chart + line_chart).properties(height=260).interactive()


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
    div[data-testid="stMetric"] label {
        color: #475467;
    }
    div[data-testid="stMetricValue"] {
        color: var(--stock-ink);
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

with st.sidebar:
    st.header("表示設定")
    st.caption("銘柄コードや時間軸、表示期間、チャート形式をここで切り替えます。")
    user_input = st.text_area(
        "銘柄コード",
        value="AAPL, MSFT",
        help="AAPL, MSFT, 7203 のようにカンマ区切りで複数入力できます。改行でも入力できます。",
        height=100,
    )
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



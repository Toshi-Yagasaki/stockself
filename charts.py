import altair as alt
import pandas as pd
from config import PRICE_LINE_COLORS, MACD_LINE_COLORS

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

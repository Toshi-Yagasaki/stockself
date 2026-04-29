import pandas as pd
import streamlit as st
import yfinance as yf
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from config import TIMEFRAME_CONFIG, PERIOD_CONFIG, PERIOD_ORDER

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


def filter_today_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    取得済みデータのうち、最新日と同じ日付だけに絞ります。
    当日分だけ見たいときに使います。
    """
    if df.empty:
        return df

    latest_date = df.index.max().date()
    return df[df.index.date == latest_date].copy()


@st.cache_data(show_spinner=False, ttl=3600)
def load_news(symbol: str) -> list[dict]:
    """
    Google NewsのRSSを使って、銘柄に関連する日本の直近ニュースを取得します。
    """
    symbol_name = load_symbol_name(symbol)
    ticker_code = symbol.split('.')[0]
    query = f"{ticker_code} {symbol_name} 株価"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        root = ET.fromstring(html)
        
        items = root.findall('.//item')
        results = []
        for item in items:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            source_elem = item.find('source')
            
            if title_elem is not None and link_elem is not None:
                title = title_elem.text
                url_str = link_elem.text
                
                # タイトルの末尾にある「 - プロバイダ名」を取り除く（表示が重複するため）
                provider = source_elem.text if source_elem is not None else ""
                if provider and title.endswith(f" - {provider}"):
                    title = title[:-(len(provider) + 3)]
                    
                # 日付のフォーマット（Sat, 25 Apr 2026 03:00:00 GMT -> 2026/04/25）
                pub_date_str = pub_date_elem.text if pub_date_elem is not None else ""
                formatted_date = pub_date_str
                is_recent = True
                if pub_date_str:
                    try:
                        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                        # 180日（約半年）以上前のニュースは除外する
                        # GMTとしてパースされたnaive datetimeなので、UTCの現在時刻と比較する
                        import datetime as dt_module
                        now_utc = dt_module.datetime.now(dt_module.timezone.utc).replace(tzinfo=None)
                        if (now_utc - dt).days > 180:
                            is_recent = False
                        else:
                            formatted_date = dt.strftime("%Y/%m/%d")
                    except Exception:
                        pass
                
                if is_recent:
                    results.append({
                        "title": title,
                        "provider": provider,
                        "url": url_str,
                        "pubDate": formatted_date
                    })
        
        return results
    except Exception:
        return []

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

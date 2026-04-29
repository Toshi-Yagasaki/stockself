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

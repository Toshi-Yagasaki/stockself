import json
import os

FAVORITES_FILE = "favorites.json"

def load_favorites() -> dict[str, str]:
    """
    お気に入りリストをファイルから読み込みます。
    ファイルがない場合や読み込みに失敗した場合はデフォルトリストを返します。
    """
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {"デフォルト (GAFAM)": "AAPL, MSFT, GOOGL, AMZN, META", "日本株": "7203, 9984, 8306"}


def save_favorite(name: str, symbols: str) -> None:
    """
    お気に入りの銘柄グループを保存します。
    """
    favs = load_favorites()
    favs[name] = symbols
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)


def delete_favorite(name: str) -> None:
    """
    お気に入りグループを削除します。
    """
    favs = load_favorites()
    if name in favs:
        del favs[name]
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False, indent=2)

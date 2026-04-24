# 株価ウォッチ + 移動平均表示アプリ

Streamlit で作った株価確認アプリです。銘柄コードを入力すると、株価、移動平均、RSI、MACD を確認できます。

## ローカルで起動

Linux / macOS:

```bash
./run_app.sh
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud で公開

1. GitHub に新しいリポジトリを作成します。
2. このフォルダの `app.py`, `requirements.txt`, `README.md`, `.gitignore` を GitHub にアップロードします。
3. https://share.streamlit.io/ にログインします。
4. `New app` から GitHub リポジトリを選びます。
5. Main file path に `app.py` を指定して Deploy します。
6. 発行された `https://xxxxx.streamlit.app` のURLをスマホで開きます。

## GitHub に上げないもの

以下はPCごとの作業用ファイルなので、GitHubへ上げないでください。

```text
.venv/
.streamlit-home/
__pycache__/
```

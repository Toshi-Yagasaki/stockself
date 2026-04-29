# Streamlit Cloud 更新手順メモ

このメモは、株価ウォッチアプリを変更したあとに、ローカルPCで確認してから公開中のStreamlitアプリへ反映するための手順です。

## 1. アプリのファイル構成

GitHubとStreamlit Community Cloudに必要な主なファイルは次の4つです。

```text
app.py
requirements.txt
README.md
.gitignore
```

アップロードしないもの:

```text
.venv/
.streamlit-home/
__pycache__/
```

## 2. ローカルPCで変更する

このディレクトリで `app.py` を編集します。

```text
/home/user/code/stockself
```

見た目、チャート、文章、計算ロジックなどを変更したら、まずローカルで確認します。

## 3. 端末でローカル起動する

このディレクトリで次を実行します。

```bash
./run_app.sh
```

起動に成功すると、端末に次のようなURLが表示されます。

```text
Local URL: http://localhost:8501
```

ブラウザで次を開きます。

```text
http://localhost:8501
```

## 4. ローカルで確認するポイント

ブラウザで以下を確認します。

- アプリ画面が表示される
- サイドバーの入力欄、時間軸、表示期間が使える
- AAPLやMSFTなどの株価データが表示される
- 表、タブ、チャートが崩れていない
- スマホでも見やすそうな幅になっている
- エラー表示が出ていない

端末で簡単な構文チェックをする場合:

```bash
.venv/bin/python3 -m py_compile app.py
```

依存関係チェックをする場合:

```bash
.venv/bin/python3 -m pip check
```

## 5. ローカル確認がOKならGitHubを更新する

ブラウザでGitHubのリポジトリを開きます。

```text
https://github.com/Toshi-Yagasaki/stockself
```

手順:

1. ファイル一覧から `app.py` を開く
2. 右上の鉛筆アイコン、または `Edit this file` を押す
3. GitHub上の `app.py` の中身を全部選択して削除する
4. ローカルPCの最新版 `app.py` の中身を全部コピーして貼り付ける
5. ページ下の `Commit changes` までスクロールする
6. コミットメッセージを入れる

例:

```text
Update app design
```

7. 緑の `Commit changes` ボタンを押す

## 6. Streamlit Cloudへの反映

GitHubにコミットすると、Streamlit Community Cloudが自動で変更を検知して再デプロイします。

通常は何もしなくても、数十秒から数分で公開アプリに反映されます。

公開URL:

```text
https://stockself-rrvddomnz...
```

ブラウザで公開URLを再読み込みして確認します。

## 7. 反映されない場合

数分待っても変わらない場合だけ、Streamlit側で再起動します。

手順:

1. 公開アプリを開く
2. 右上のメニュー、または `Manage app` を開く
3. `Reboot app` や再起動に相当するボタンを押す
4. 再読み込みして確認する

## 8. 別PCやスマホで見る

公開アプリは、URLを知っていれば外出先のスマホからも見られます。

AndroidスマホではChromeで公開URLを開きます。

```text
https://stockself-rrvddomnz...
```

## 9. よくある注意点

- GitHubに `.venv/` はアップロードしない
- GitHubに `__pycache__/` はアップロードしない
- `requirements.txt` を変更した場合もGitHubにコミットする
- 公開アプリでエラーが出たら、Streamlit Cloudのログを見る
- 株価データ取得は `yfinance` を使っているため、通信状況や取得元の都合で一時的に失敗することがある

## 10. いつもの流れ

普段はこの流れで進めます。

```text
app.pyを編集
↓
./run_app.sh でローカル確認
↓
問題なければGitHubのapp.pyを更新
↓
Commit changes
↓
Streamlit Cloudが自動更新
↓
公開URLで確認
```

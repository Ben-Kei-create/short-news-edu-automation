# Short News Education Automation

## 概要・主要機能

このプロジェクトは、最新のニュースを基に教育コンテンツを自動生成し、YouTubeに投稿するツールです。

### 主要機能

- **ニュース記事の取得**: RSSフィードから最新のニュース記事を自動的に取得します。
- **スクリプト生成**: 取得したニュース記事を基に、教育的なショートビデオ用のスクリプトを生成します。
- **音声生成**: 生成されたスクリプトを**Google Cloud TTS**または**VOICEVOX**を使用して自然な音声に変換します。
- **画像生成**: スクリプトの内容に基づき、以下の方法で画像を生成します。
    - **Stable Diffusion**: 高品質な画像を生成します。
    - **Google Search**: 関連する画像をウェブから検索・取得します。
    - **DALL-E**: AIによる創造的な画像を生成します。
- **ビデオ合成**: 生成された音声、画像、および字幕を組み合わせて、60秒程度のショートビデオを自動的に作成します。
- **YouTube投稿**: 生成されたビデオをYouTubeに自動的にアップロードし、公開します。

---

## 詳細設計

### 1. RSS取得と設定ファイル

- **RSSフィードURL**: `config/settings.yaml`内の`rss_feeds`リストに、取得対象のRSSフィードURLを複数指定します。
- **取得ロジック**: 起動時にすべてのRSSフィードから最新記事を取得し、その中からランダムで1つの記事を処理対象として選択します。
- **設定ファイル仕様 (`config/settings.yaml`)**:
  ```yaml
  rss_feeds:
    - http://example.com/rss1
    - http://example.com/rss2
  ```

### 2. スクリプト生成

- **パラメータ**: `config/settings.yaml`で以下のパラメータを設定可能とします。
  - `script_length`: 生成する動画の目標の長さ（秒）。デフォルトは60秒。
  - `script_tone`: 台本のトーン（例: `専門的`, `カジュアル`, `子供向け`）。
  - `target_audience`: 対象層（例: `初心者`, `専門家`, `学生`）。
- **プロンプト**: 上記パラメータと記事の内容を基に、Gemini APIへのプロンプトが動的に生成されます。

### 3. 画像生成

- **優先順位**: `config/settings.yaml`で指定された各画像生成API（`sd_api`, `dalle`, `google_search`）の有効/無効に基づき、以下の優先順位で画像生成を試みます。
  1. Stable Diffusion (`--use-sd_api`)
  2. DALL-E (`--use-dalle`)
  3. Google Search (`--use-google-search`)
- **生成枚数**: スクリプトを文単位で分割し、各文に対応する画像を1枚ずつ生成します。
- **対応部分**: 生成された画像は、スクリプトの各文の表示タイミングで順次表示されます。

### 4. 字幕生成

- **フォント・スタイル**: `config/settings.yaml`で字幕のスタイルを詳細に設定します。
  ```yaml
  subtitle:
    font: "path/to/your/font.ttf" # フォントファイルのパス
    fontsize: 24
    color: "white"
    stroke_color: "black"
    stroke_width: 1
    position: "bottom" # top, center, bottom
  ```
- **焼き付けロジック**: `moviepy.TextClip` を利用します。音声合成時に生成される文ごとのタイムスタンプ情報を基に、各文が話されるタイミングで画面下部に表示されるように字幕を動画に焼き付けます。

### 5. YouTube投稿

- **メタデータ設定**: `config/settings.yaml`にタイトル、説明、タグのテンプレートを記述できます。
  ```yaml
  youtube:
    title_template: "【教育ニュース】{theme}について解説！"
    description_template: "この動画では、{theme}について分かりやすく解説します。

#shorts #教育 #ニュース"
    tags: ["教育", "ニュース解説"]
  ```
- **自動生成**: 上記テンプレートの`{theme}`部分に動画のテーマを埋め込みます。さらに、Gemini APIを活用し、動画内容からより最適なタイトル、説明、タグを生成することも可能です。
- **サムネイル**: 生成された画像の中から最も内容を象徴する1枚をサムネイルとして自動設定します。

### 6. エラーハンドリングとログ

- **エラー処理**: すべての外部API連携（RSS, LLM, 画像生成, YouTube）やファイルI/O処理は`try-except`ブロックで囲み、エラー発生時もプロセスが異常終了しないようにします。
- **ログ出力**:
  - ログは`output/logs/`ディレクトリに`YYYYMMDD_HHMMSS.log`形式で保存されます。
  - ログレベル（INFO, WARNING, ERROR）を設定し、APIリクエストの内容、エラーメッセージ、処理の進捗などを記録します。
- **進捗表示**: コンソールには「RSSフィード取得中...」「台本生成中...」といった現在の処理状況がリアルタイムで表示されます。

### 7. テスト計画

- **フレームワーク**: `pytest`を使用します。
- **単体テスト**: `tests/`ディレクトリに各モジュール（`audio_manager`, `script_generator`等）に対応するテストファイルを作成します。
  - `test_script_generator.py`: ダミーの記事データを入力し、期待される形式のスクリプトが生成されるかテストします。
- **結合テスト**:
  - API連携部分: `unittest.mock`を使用して外部APIへのリクエストをモック化し、正常系・異常系のレスポンスに対する挙動をテストします。
  - `make_short.py`: 主要な引数パターン（`--use-sd_api`など）でスクリプトを実行し、一連のフローがエラーなく完了するかテストします。

### 8. 多言語対応案

- **言語設定**: `config/settings.yaml`に`language: "ja"`のような項目を追加します。
- **実装方針**:
  - **スクリプト/メタデータ**: Gemini APIへのプロンプトに、指定された言語で生成するよう指示を追加します。
  - **音声合成**: Google Cloud TTSやVOICEVOXの言語・話者設定を指定された言語に合わせて変更します。
  - **字幕**: `config/settings.yaml`で言語ごとにフォントを指定可能にします。

---

## セットアップと実行方法

### 1. 前提条件

1.  **Pythonのインストール**: Python 3.10以上がインストールされていることを確認してください。

2.  **ライブラリのインストール**: プロジェクトのルートディレクトリで、以下のコマンドを実行して必要なライブラリをインストールします。
    ```bash
    pip install -r requirements.txt
    ```

3.  **設定ファイルの準備**: 
    - `config/settings.yaml` を開き、`api_keys`セクションにご自身のAPIキーを入力してください。
    - 各APIキーの取得方法については `docs/troubleshooting.md` を参照してください。

### 2. 基本的な実行方法

設定が完了したら、以下のコマンドを実行するだけで動画が自動生成されます。

```bash
python make_short.py
```

このコマンドは、`config/settings.yaml`の設定に従い、RSSフィードからテーマを取得し、一連の動画生成プロセスを実行します。

### 3. 応用的な使い方

#### VOICEVOXを利用する場合

Google Cloud TTSの代わりに、無料で利用できる高品質な音声合成エンジンVOICEVOXを使用できます。

1.  **VOICEVOX Engineの準備**: 
    - [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)から、お使いのOSに対応したVOICEVOXソフトウェアをダウンロードし、インストール・起動しておきます。
    - **注意**: このアプリケーションがローカルで起動していないと、音声生成は失敗します。

2.  **設定の変更**: `config/settings.yaml`の以下の項目を変更します。
    ```yaml
    # 使用する音声合成エンジンを 'voicevox' に変更
    audio_engine: "voicevox"
    
    # (任意) VOICEVOXの設定で使用したい話者のIDに変更
    voicevox:
      speaker_id: 1 # 例: 1は四国めたん（ノーマル）
    ```

3.  **実行**: 通常通りスクリプトを実行します。
    ```bash
    python make_short.py
    ```

#### Stable Diffusionを利用する場合

より高品質な画像を生成するために、ローカル環境のStable Diffusion WebUI (Automatic1111)と連携できます。

1.  **Stable Diffusion WebUIの準備**:
    - `docs/troubleshooting.md`の`torch`関連の項目を参考に、WebUIの環境構築を行ってください。
    - 起動バッチ/シェルスクリプトの`COMMANDLINE_ARGS`に`--api`を追加して、APIモードで起動します。

2.  **設定の変更**: `config/settings.yaml`で、画像生成APIとして`stable_diffusion`を有効にします。
    ```yaml
    image:
      enabled_apis:
        stable_diffusion: true # ここをtrueに
        dalle: false
        google_search: false
    ```

#### 特定のテーマで実行する場合

RSSフィードからのテーマ取得をスキップし、任意のテーマで動画を生成したい場合は`--theme`引数を使用します。

```bash
# 「日本の城」というテーマで動画を1本生成
python make_short.py --theme "日本の城"

# 複数のテーマで動画を連続生成
python make_short.py --theme "江戸時代の文化" "戦国時代の合戦"
```

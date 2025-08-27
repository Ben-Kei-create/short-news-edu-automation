# 改修タスクリスト

## 概要

このドキュメントは、`short-news-edu-automation`プロジェクトの今後の改修タスクを管理するためのものです。

---

## タスク一覧

### 1. VOICEVOX API対応

- **担当**: `modules/audio_manager.py`
- **内容**:
  - VOICEVOX APIと連携し、テキストから音声を生成する機能を追加する。
  - `config/settings.yaml`にVOICEVOXサーバーのURLや話者ID（speaker ID）を設定する項目を追加する。
  - `make_short.py`の`--use-voicevox`引数でGoogle Cloud TTSと切り替えられるように実装する。

### 2. Automatic1111 (Stable Diffusion) 連携強化

- **担当**: `docs/`, `modules/image_manager.py`
- **内容**:
  - `docs/automatic1111_setup.md`を作成し、Stable Diffusion WebUIをAPIモードで起動するまでの詳細なセットアップ手順を記述する。
  - `image_manager.py`に、プロンプト、ネガティブプロンプト、画像サイズ、サンプリングステップ数等の詳細なパラメータを`config/settings.yaml`から読み込み、APIリクエストに含める機能を実装する。

### 3. torchバージョンエラーの回避策を文書化

- **担当**: `docs/troubleshooting.md`
- **内容**:
  - Python 3.10環境で`stable-diffusion-webui`の`requirements.txt`をインストールする際に発生しやすい`torch`関連のバージョンコンフリクトについて記述する。
  - `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118` のように、適切なCUDAバージョンに対応したコマンドを明記し、ユーザーがエラーを自己解決できるように案内する。

### 4. 字幕生成ロジックの実装

- **担当**: `modules/subtitle_generator.py`, `modules/video_composer.py`
- **内容**:
  - `subtitle_generator.py`を新規作成し、音声合成時に得られるタイムスタンプ情報を基に、`SRT`形式または`ASS`形式の字幕ファイルを生成するロジックを実装する。
  - `video_composer.py`で、`moviepy` (`TextClip`) または `ffmpeg`コマンドのサブプロセス呼び出しを用いて、動画に字幕を焼き付ける処理を実装する。
  - `config/settings.yaml`で定義されたフォント、色、位置設定が反映されるようにする。

### 5. 設定ファイル(config/settings.yaml)のサンプル提供

- **担当**: `config/settings.yaml`
- **内容**:
  - プロジェクトで設定可能なすべてのオプション（RSSフィード、各種APIキー、スクリプトパラメータ、字幕スタイル等）を含む、包括的なサンプル設定を記述する。
  - APIキーや個人情報は`"YOUR_API_KEY"`のようなプレースホルダー形式で記述し、ユーザーが自身の情報を入力しやすいようにする。

### 6. CLI引数処理の改修

- **担当**: `make_short.py`
- **内容**:
  - `argparse`のロジックを見直し、引数の役割をより直感的にする。
  - **デフォルト動作**: 引数なしで実行した場合、RSSからテーマ取得 → スクリプト生成 → 音声生成 → 画像生成 → 動画合成という一連のフローが自動で実行されるようにする。
  - **オプション化**: `--bgm "path/to/bgm.mp3"`のように、BGMファイルなど、ユーザーが任意で指定したい項目のみをオプション引数として残す。
  - 各API（SD, DALL-E等）の使用有無は、引数ではなく`config/settings.yaml`のフラグで制御する設計に変更する。

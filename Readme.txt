[Input Manager] → [Theme Selector]
        ↓
[Script Generator] → 台本チェック・修正
        ↓
[Image Manager] → 重複/偏り補正
        ↓
[Audio Manager] → 音声生成
        ↓
[BGM Manager] → 音量調整
        ↓
[Video Composer] → 画像+音声+BGMを合成
        ↓
[Subtitle Generator] → SRT字幕作成
        ↓
[Thumbnail Generator] → サムネ生成
        ↓
[Post & Log Manager] → SNS投稿 + CSVログ保存


# Short News Edu Automation

ニュースやトレンドをもとに「しくじり先生風」ショート動画を自動生成するパイプラインです。
台本生成、画像生成、音声合成、動画作成、投稿までフル自動対応します。

---

## 概要

このリポジトリは、以下の自動化を目的としたパイプラインを提供します。

- ニュースRSSやトレンド情報から動画テーマを抽出
- Gemini API/LLMで面白く教養的な台本を生成
- 手動画像優先＋AI画像生成（Stable Diffusion API連携、LoRA対応）で動画素材を準備
- Google Cloud TTSで台本を音声化（速度調整可能）
- BGM挿入・音量調整
- moviepy/FFmpegで縦動画MP4を作成（TikTok / YouTube Shorts向け、画像5秒固定）
- サムネイル作成、字幕生成（カスタムフォント対応、動画に焼き付け）
- SNS APIで自動投稿（TikTok / YouTube Shorts）

---

## 特徴

- **フル自動 + 手動ハイブリッド**
  引数指定や手動素材の差し替えが可能

- **量産対応**
  複数動画を一括生成可能

- **バズ最適化**
  高品質プロンプト生成、SEO・トレンド・ハッシュタグを自動生成

- **運用効率化**
  生成ログ管理、エラー自動補填、リトライ機能付き

---

## 環境・依存

- Python 3.10+
- 仮想環境 (venv推奨)
- 必要なライブラリ (requirements.txt参照)
  - `requests`
  - `google-generativeai`
  - `google-cloud-texttospeech`
  - `python-dotenv`
  - `moviepy`
  - `numpy`
  - `feedparser`
  - `Pillow`
- **Stable Diffusion Web UI (AUTOMATIC1111版)**
  - APIモード (`--api`) で起動している必要があります。
- **Google Cloud Platform 認証情報**
  - `google_credentials.json` にサービスアカウントキーを設定する必要があります。

---

## ディレクトリ構造

```
input/
├── scripts/          # 台本（ユーザー指定 or 自動生成）
├── images/           # 手動 or 自動生成 or 自動収集
│   └── 20250824_1530/ # 実行ごとにタイムスタンプで素材フォルダを自動生成
│       ├── 0001.png
│       └── ...
├── bgm/              # 必須BGM
└── fonts/            # カスタムフォント (.ttf, .otf)

output/
├── videos/           # 完成動画
├── subtitles/        # 生成されたSRT字幕ファイル
├── thumbnails/       # 生成されたサムネイル画像
└── logs/             # 実行ログ
```

---

## 処理フロー

1.  **台本取得:**
    *   ユーザー指定台本があれば使用。
    *   指定なしの場合、ニュース記事/トレンド記事を自動収集し、60秒分の原稿を自動生成（Gemini API）。
2.  **画像生成:**
    *   ユーザー指定画像があれば使用。
    *   指定なしの場合、Stable Diffusion API（`--use_sd_api`）で画像を自動生成（Geminiでプロンプト生成、LoRA対応）。
    *   APIが利用できない場合、プレースホルダー画像を使用。
    *   生成画像は`input/images/{タイムスタンプ}/`に保存。
3.  **音声生成（Google Cloud TTS）:**
    *   原稿テキストを音声合成（速度調整可能）。
    *   音声長が60秒未満ならエラーで停止。
    *   音声ファイルを`temp/`に保存。
4.  **字幕生成:**
    *   音声のテキストをもとにSRT形式の字幕ファイルを自動生成。
    *   `output/subtitles/`に保存。
5.  **動画合成（MoviePy）:**
    *   画像スライドショー化（1枚5秒固定）。
    *   縦長1080x1920の黒背景に中央配置。
    *   ナレーション音声を映像の長さに合わせて速度調整。
    *   BGMを合成（音量調整済み）。
    *   字幕を動画に焼き付け（カスタムフォント対応）。
    *   `output/videos/`に保存。

---

## 使用方法

### 1. セットアップ

1.  **Pythonと仮想環境の準備:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # macOS/Linux
    # .\venv\Scripts\activate # Windows
    ```
2.  **依存ライブラリのインストール:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Google Cloud TTS 認証情報の設定:**
    *   Google Cloud Platformでサービスアカウントキー（JSON形式）を払い出し、その内容をプロジェクトルートの `google_credentials.json` ファイルに貼り付けてください。
    *   サービスアカウントには `Cloud Text-to-Speech API` のロールが必要です。
4.  **Stable Diffusion Web UI のインストールとAPI起動:**
    *   AUTOMATIC1111版のStable Diffusion Web UIをインストールします。
        *   [https://github.com/AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
    *   モデルファイル（.ckpt/.safetensors）を `stable-diffusion-webui/models/Stable-diffusion/` に配置します。
    *   Web UIをAPIモードで起動します。
        ```bash
        cd path/to/stable-diffusion-webui
        ./webui.sh --api # macOS/Linux
        # webui.bat --api # Windows
        ```
        *   PyTorchのバージョン問題が発生した場合、`pip install torch==2.2.2 torchvision==0.17.2 --extra-index-url https://download.pytorch.org/whl/cpu` を試してください。
5.  **カスタムフォントの配置 (任意):**
    *   プロジェクトルートに `input/fonts/` フォルダを作成し、使用したいフォントファイル（.ttf, .otf）を配置します。

### 2. 実行

`make_short.py` を実行します。

```bash
# 仮想環境を有効化 (まだの場合)
source venv/bin/activate

# 最小実行例 (台本・画像は自動生成、BGMはデフォルトを探す)
venv/bin/python make_short.py --theme "日本の歴史"

# Stable Diffusion APIとLoRA、カスタムフォントを使用する例
venc/bin/python make_short.py \
    --theme "グリム童話" \
    --style "fantasy art, fairytale illustration" \
    --use_sd_api \
    --sd_model "Cute kawayi_2d_v1.0.safetensors" \
    --lora_model "Gloss_Tweaker_v2.0" \
    --lora_weight 0.8 \
    --font "MyCustomFont.ttf" # input/fonts/MyCustomFont.ttf が存在する場合

# 全ての引数を指定する例
venc/bin/python make_short.py \
    --theme "最新ニュース" \
    --bgm_path "input/bgm/my_bgm.mp3" \
    --script_file "input/scripts/my_script.txt" \
    --manual_images "input/images/my_set/" \
    --style "photorealistic" \
    --use_sd_api \
    --sd_model "realisticVisionV51.safetensors" \
    --lora_model "add_detail" \
    --lora_weight 0.7 \
    --font "NotoSansJP-Regular.otf"
```

---

## モジュール構成

-   **`make_short.py`**: メイン実行ファイル。引数解析、モジュール呼び出し、バッチ処理を統括。
-   **`modules/input_manager.py`**: 引数解析、ニュースRSS取得、テーマ抽出。
-   **`modules/theme_selector.py`**: テーマ重複排除、複数動画生成時のテーマ分割、トレンド情報チェック。
-   **`modules/script_generator.py`**: Gemini API/LLM呼び出し、台本生成・文体調整・バズ要素追加。
-   **`modules/image_manager.py`**: 手動画像優先、AI画像生成（Stable Diffusion API連携、LoRA対応）、画風指定対応。
-   **`modules/audio_manager.py`**: Google Cloud TTS呼び出し、声質・速度調整、出力音声ファイル管理。
-   **`modules/bgm_manager.py`**: 指定BGMの読み込み or 自動選定、音量調整。
-   **`modules/video_composer.py`**: moviepy/FFmpegによる動画作成、画像スライド（5秒固定）+ 音声 + BGM + 字幕統合（カスタムフォント対応）、縦動画MP4作成。
-   **`modules/subtitle_generator.py`**: 台本 → SRTファイル作成、音声タイミングに同期。
-   **`modules/thumbnail_generator.py`**: 動画内フレーム抽出 or 指定画像をサムネイル化。
-   **`modules/post_log_manager.py`**: SNS API連携（TikTok / YouTube Shorts投稿）、タイトル・説明文・ハッシュタグ自動生成、CSVログ管理。
-   **`modules/utils.py`**: 共通ユーティリティ（ファイル操作、フォルダ作成、ログ出力補助など）。
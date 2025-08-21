# short-news-edu-automation プロジェクト実行手順

## 1. 前提条件
- Python 3.10 以上がインストールされていること
- Homebrew や pyenv で Python 環境を管理していると便利

## 2. 仮想環境の作成と有効化
```bash
cd short-news-edu-automation
python -m venv venv
source venv/bin/activate
```

## 3. 必要ライブラリのインストール

```bash
pip install --upgrade pip setuptools wheel
pip install moviepy==2.2.1 imageio_ffmpeg numpy pillow proglog python-dotenv
```

※ moviepy 2.x 系を使用する場合、インポート先が 1.x 系と異なるため注意

```python
# 例: moviepy 2.x 系の場合
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
```

## 4. 使い方 (Usage)

1.  **`input` フォルダに素材を入れる**
    - プロジェクトルートに `input` フォルダがない場合は、スクリプトが自動で作成します。
    - 動画にしたい**画像ファイル**（.png, .jpg, .jpeg）と**音声ファイル**（.mp4, .mp3, .wav, .m4a）を1つずつ `input` フォルダに入れてください。
    - **注意:** 音声ファイルの長さは60秒以上である必要があります。60秒未満の場合はエラーで停止します。

2.  **スクリプトを実行する**
    - 仮想環境を有効化した後 (`source venv/bin/activate`)、以下のコマンドを実行します。

    ```bash
    python3 generate_60s_video.py
    ```
    - `input` フォルダ内の最初の画像・音声ファイルが自動的に使用されます。

3.  **成果物を確認する**
    - 処理が完了すると、`output` フォルダに `（元の画像ファイル名）_short_video.mp4` という名前で動画ファイルが生成されます。

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

## 4. プロジェクトの実行

```bash
# 任意のスクリプトを実行
python main.py
```

## 5. 注意点

* moviepy 2.x 系では `moviepy.editor` は存在しません。インポート先を上記に変更してください
* Python バージョンが合わない場合は pyenv で切り替え可能
* 依存ライブラリは venv 内にインストールしてください

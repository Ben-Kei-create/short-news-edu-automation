# Short News Education Automation

## 概要・主要機能

このプロジェクトは、最新のニュースを基に教育コンテンツを自動生成し、YouTubeに投稿するツールです。

### 主要機能

- **ニュース記事の取得**: RSSフィードから最新のニュース記事を自動的に取得します。
- **スクリプト生成**: 取得したニュース記事を基に、教育的なショートビデオ用のスクリプトを生成します。
- **音声生成**: 生成されたスクリプトを**Google Cloud TTS**を使用して自然な音声に変換します。
- **画像生成**: スクリプトの内容に基づき、以下の方法で画像を生成します。
    - **Stable Diffusion**: 高品質な画像を生成します。
    - **Google Search**: 関連する画像をウェブから検索・取得します。
    - **DALL-E**: AIによる創造的な画像を生成します。
- **ビデオ合成**: 生成された音声、画像、および字幕を組み合わせて、60秒程度のショートビデオを自動的に作成します。
- **YouTube投稿**: 生成されたビデオをYouTubeに自動的にアップロードし、公開します。

## 引数仕様

本ツールは、以下のコマンドライン引数に対応しています。

| 引数名               | 説明                                                                 | デフォルト値 |
| :------------------- | :------------------------------------------------------------------- | :----------- |
| `--use-sd_api`       | Stable Diffusion APIを使用して画像を生成します。                     | `False`      |
| `--use-google-search`| Google Search APIを使用して画像を検索・取得します。                  | `False`      |
| `--use-dalle`        | DALL-E APIを使用して画像を生成します。                               | `False`      |
| `--post-to-youtube`  | 生成されたビデオをYouTubeに自動投稿します。                          | `False`      |

## 推奨環境

本プロジェクトは以下の環境で動作確認されています。

- Python 3.x

### 必要なライブラリ

`requirements.txt` に記載されているライブラリをインストールしてください。

```bash
pip install -r requirements.txt
```

現在の `requirements.txt` の内容:
- `requests`
- `google-generativeai`
- `google-cloud-texttospeech`
- `moviepy==1.0.3`
- `numpy`
- `feedparser`
- `Pillow==9.5.0`
- `PyYAML`
- `pytest`
- `openai`
- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`

## 運用フロー

1. スクリプトがニュース記事を取得し、ビデオスクリプトを生成します。
2. 生成されたスクリプトに基づいて、音声と画像が生成されます。画像生成は、`--use-sd_api`, `--use-google-search`, `--use-dalle` の引数に応じて、Stable Diffusion、Google Search、DALL-Eのいずれかまたは複数を組み合わせて行われます。
3. 音声、画像、字幕が合成され、ショートビデオが作成されます。
4. `--post-to-youtube` 引数が指定されている場合、生成されたビデオはYouTubeに自動的に投稿されます。

## 注意点

- YouTubeへの自動投稿機能を利用するには、Google Cloud Platformでプロジェクトを作成し、YouTube Data APIを有効にする必要があります。また、OAuth 2.0クライアントIDを設定し、`client_secret.json` ファイルをプロジェクトのルートディレクトリに配置する必要があります。初回実行時には、OAuth認証フローが開始され、ブラウザでの認証が必要になります。
- Google Custom Search APIを利用して画像を検索する場合、Google Cloud PlatformでCustom Search APIを有効にし、APIキーと検索エンジンID（CX）を設定する必要があります。
- DALL-E APIを利用して画像を生成する場合、OpenAIのAPIキーを設定する必要があります。

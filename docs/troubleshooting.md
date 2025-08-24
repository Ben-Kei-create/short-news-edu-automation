# トラブルシューティングガイド

このドキュメントは、本プロジェクトの実行中に発生する可能性のある一般的な問題とその解決策を提供します。

## 1. Python環境と依存関係に関する問題

### 1.1. `ModuleNotFoundError` または `ImportError`

**問題**: `ModuleNotFoundError: No module named 'xxx'` や `ImportError: cannot import name 'xxx' from 'yyy'` のようなエラーが発生する。

**原因**: 必要なPythonライブラリがインストールされていないか、仮想環境が正しくアクティブ化されていません。

**解決策**:
1.  **仮想環境の確認**: プロジェクトのルートディレクトリで仮想環境がアクティブ化されていることを確認してください。
    ```bash
    source venv/bin/activate  # Linux/macOS
    .\venv\Scripts\activate   # Windows PowerShell
    ```
2.  **依存関係のインストール**: `requirements.txt` に記載されている全てのライブラリがインストールされていることを確認してください。
    ```bash
    pip install -r requirements.txt
    ```

### 1.2. `torch` 関連のエラー (特にPython 3.10環境)

**問題**: `torch` や `torchvision`、`torchaudio` 関連のエラーが発生する。特にPython 3.10環境で発生しやすい場合があります。

**原因**: `torch` の特定のバージョンが、使用しているPythonバージョンやCUDA（GPU）環境と互換性がない可能性があります。`requirements.txt` には `torch` が直接指定されていないため、他のライブラリの依存関係としてインストールされる際に問題が生じることがあります。

**解決策**:
1.  **既存の `torch` のアンインストール**:
    ```bash
    pip uninstall torch torchvision torchaudio -y
    ```
2.  **PyTorch公式サイトからのインストール**:
    *   PyTorchの公式ウェブサイト (https://pytorch.org/get-started/locally/) にアクセスします。
    *   ご自身の環境（OS, Package, Language, CUDA version）に合ったインストールコマンドを選択し、実行してください。
    *   例 (Linux/CUDA 11.7の場合):
        ```bash
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
        ```
    *   例 (macOSの場合):
        ```bash
        pip install torch torchvision torchaudio
        ```
    *   **注意**: `requirements.txt` を再インストールする前に、この手順を実行してください。

## 2. APIキーと認証に関する問題

### 2.1. `settings.yaml` のAPIキーが未設定

**問題**: `settings.yaml` にAPIキーが「YOUR_..._API_KEY」のまま、または「ここに」のようなプレースホルダーのままになっている。

**原因**: 必要なAPIキーが設定ファイルに正しく入力されていません。

**解決策**:
1.  `config/settings.yaml` ファイルを開きます。
2.  `api_keys` セクションにある各APIキーのプレースホルダーを、ご自身の有効なAPIキーに置き換えてください。
    *   `gemini`: Google Cloud ConsoleでGemini APIキーを取得。
    *   `google_cloud_tts`: Google Cloud ConsoleでText-to-Speech APIを有効にし、サービスアカウントキーを取得。
    *   `google_custom_search`, `google_custom_search_cx`: Google Cloud ConsoleでCustom Search APIを有効にし、APIキーと検索エンジンID (CX) を取得。
    *   `openai`: OpenAIのウェブサイトでAPIキーを取得 (DALL-E用)。

### 2.2. YouTube投稿時の認証エラー

**問題**: YouTubeへの動画投稿時に認証エラーが発生する。

**原因**: OAuth 2.0認証が完了していないか、`client_secret.json` が見つからない、または `youtube_token.json` が破損しています。

**解決策**:
1.  **`client_secret.json` の確認**: Google Cloud ConsoleでOAuth 2.0クライアントIDを作成し、ダウンロードした `client_secret.json` ファイルがプロジェクトのルートディレクトリに配置されていることを確認してください。
2.  **初回認証の実行**: プロジェクトを初めて実行する際、ブラウザが開きGoogleアカウントでの認証を求められます。指示に従って認証を完了してください。
3.  **`youtube_token.json` の削除**: 認証トークンが破損している可能性がある場合、プロジェクトルートにある `youtube_token.json` ファイルを削除してから再度実行してください。これにより、再認証が促されます。

## 3. その他の一般的な問題

### 3.1. 動画生成が途中で停止する/エラーになる

**原因**:
*   API呼び出しの失敗（レートリミット、無効なプロンプトなど）。
*   一時ファイルの生成失敗（ディスク容量不足、権限問題）。
*   MoviePy/FFmpeg関連の問題。

**解決策**:
1.  **ログの確認**: `output/logs/app.log` ファイルを確認し、詳細なエラーメッセージやスタックトレースを確認してください。
2.  **APIキーの確認**: 各APIキーが有効で、利用制限に達していないか確認してください。
3.  **ディスク容量**: `temp` ディレクトリや `output` ディレクトリに十分な空き容量があることを確認してください。
4.  **FFmpegのインストール**: MoviePyが依存するFFmpegが正しくインストールされ、パスが通っていることを確認してください。
    *   macOS: `brew install ffmpeg`
    *   Windows: FFmpegの公式サイトからダウンロードし、システムPATHに追加。
5.  **プロンプトの調整**: 画像生成やスクリプト生成のプロンプトがAPIのポリシーに違反していないか確認してください。

---

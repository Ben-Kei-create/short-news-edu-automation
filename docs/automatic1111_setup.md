# Automatic1111 (Stable Diffusion web UI) セットアップと連携ガイド

このドキュメントは、ローカル環境でAutomatic1111のStable Diffusion web UIをセットアップし、本プロジェクトと連携させるための手順を説明します。

## 1. Automatic1111のインストール

1.  **リポジトリのクローン**:
    ```bash
    git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
    cd stable-diffusion-webui
    ```

2.  **依存関係のインストールと初回起動**:
    *   Windowsの場合: `webui-user.bat` を実行します。
    *   Linux/macOSの場合: `webui-user.sh` を実行します。
    初回起動時に必要なPythonパッケージやモデルが自動的にダウンロード・インストールされます。完了すると、Web UIがブラウザで開きます。

## 2. モデルのダウンロードと配置

Automatic1111は様々なモデル（Checkpoint, LoRAなど）をサポートしています。

1.  **Checkpointモデル**:
    *   Civitai (civitai.com) や Hugging Face (huggingface.co) などから `.safetensors` または `.ckpt` 形式のモデルファイルをダウンロードします。
    *   ダウンロードしたモデルは `stable-diffusion-webui/models/Stable-diffusion/` ディレクトリに配置します。

2.  **LoRAモデル**:
    *   Civitaiなどから `.safetensors` 形式のLoRAモデルファイルをダウンロードします。
    *   ダウンロードしたモデルは `stable-diffusion-webui/models/Lora/` ディレクトリに配置します。

## 3. APIモードでの起動

本プロジェクトからAutomatic1111の画像生成機能を利用するためには、APIモードで起動する必要があります。

1.  `stable-diffusion-webui/` ディレクトリに移動します。
2.  以下のコマンドでWeb UIを起動します。
    *   Windowsの場合:
        ```bash
        webui-user.bat --api
        ```
    *   Linux/macOSの場合:
        ```bash
        ./webui-user.sh --api
        ```
    これにより、Web UIが起動するとともに、APIエンドポイントが利用可能になります。通常、APIは `http://127.0.0.1:7860` でリッスンします。

## 4. プロジェクトの設定ファイル (`config/settings.yaml`) の更新

本プロジェクトの `config/settings.yaml` ファイルを編集し、Automatic1111のAPIエンドポイントを設定します。

```yaml
# Image Generation Settings
image_generation:
  # ... (他の設定) ...
  stable_diffusion_api_url: "http://127.0.0.1:7860/sdapi/v1/txt2img" # Automatic1111のAPIエンドポイント
  # ... (その他のStable Diffusion関連設定) ...
```

*   `stable_diffusion_api_url`: Automatic1111がAPIを公開しているURLを指定します。デフォルトでは `http://127.0.0.1:7860/sdapi/v1/txt2img` です。
*   `sd_model` や `lora_model` など、使用したいモデル名を `config/settings.yaml` またはCLI引数で指定できます。

これで、本プロジェクトからAutomatic1111のStable Diffusion APIを利用して画像を生成できるようになります。

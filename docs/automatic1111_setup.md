# Automatic1111 (Stable Diffusion WebUI) セットアップガイド

> **トラブルシューティングが必要な場合はこちらを参照**  
> - [公式GitHub Issues](https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues)  
> - [Torchインストールエラー](https://pytorch.org/get-started/previous-versions/)  
> - [CUDA関連エラー対策](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Troubleshooting)

---

## 手順1: リポジトリの取得

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
```

---

## 手順2: Python仮想環境と依存関係のインストール

### 2.1. 仮想環境の作成と有効化

```bash
python3 -m venv venv
source venv/bin/activate   # Windowsなら venv\Scripts\activate
```

### 2.2. torch のインストール（OS / GPU構成ごと）

> **注意:** WebUIの自動インストールが失敗する場合は、以下のコマンドを手動実行してください。

#### NVIDIA GPU (CUDA 12.1) の場合（推奨）

```bash
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2   --index-url https://download.pytorch.org/whl/cu121
```

#### NVIDIA GPU (CUDA 11.8) の場合

```bash
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2   --index-url https://download.pytorch.org/whl/cu118
```

#### GPU非搭載 (CPUのみ) / macOS の場合

```bash
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2
```

> **Note:** CPUでの画像生成は非常に時間がかかります（1枚あたり数分〜数十分）。

### 2.3. 残りの依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

---

## 手順3: APIモードでの起動設定

Stable Diffusion WebUIを**APIモード**で起動し、本ツールからHTTP経由で操作できるようにします。

### Windowsの場合: `webui-user.bat` の編集

1. メモ帳などのテキストエディタで `webui-user.bat` を開く
2. `set COMMANDLINE_ARGS=` の行を以下のように書き換え

   ```batch
   set COMMANDLINE_ARGS=--api
   ```

### macOS / Linuxの場合: `webui-user.sh` の編集

1. テキストエディタで `webui-user.sh` を開く
2. `#export COMMANDLINE_ARGS=""` のコメントアウトを解除し、以下に変更

   ```bash
   export COMMANDLINE_ARGS="--api"
   ```

> **Note (GPUなし環境):**
> 起動時にCUDA関連のエラーが出る場合、`--skip-torch-cuda-test` フラグを追加すると解決することがあります。
>
> ```batch
> set COMMANDLINE_ARGS=--api --skip-torch-cuda-test
> ```

---

## 手順4: モデルファイルの配置と初回起動

### 4.1. モデルファイルの配置

1. [Hugging Face](https://huggingface.co/models?pipeline_tag=text-to-image&sort=downloads)
   や [Civitai](https://civitai.com/) から `.safetensors` 形式のモデルファイルをダウンロード
2. ダウンロードしたファイルを以下に配置

   ```
   stable-diffusion-webui/models/Stable-diffusion/
   ```

### 4.2. 初回起動

WebUIを起動:

```bash
# Windows
webui-user.bat

# macOS / Linux
./webui-user.sh
```

* **注意:** 初回起動時は追加モデル（CLIP, CodeFormer など）の自動ダウンロードが行われ、完了まで数分〜数十分かかります。
* **成功の確認:** ターミナルに以下のようなログが出力されれば起動成功です。

  ```
  Running on local URL:  http://127.0.0.1:7860
  ```

### 4.3. APIの動作確認

ブラウザで以下のURLにアクセス:

```
http://127.0.0.1:7860/docs
```

* 「Stable Diffusion API」というタイトルの下に「POST `/sdapi/v1/txt2img`」などのエンドポイントが表示されていればOKです。

---

## 手順5: 本ツールとの連携設定

最後に、本ツールの `config/settings.yaml` を編集し、Stable Diffusion連携を有効にします。

```yaml
image:
  enabled_apis:
    stable_diffusion: true
    dalle: false
    google_search: false

  stable_diffusion:
    # WebUIを起動したURLのAPIエンドポイント
    url: "http://127.0.0.1:7860/sdapi/v1/txt2img"

    # 手順4.1で配置したモデルファイル名を指定
    model: "v1-5-pruned-emaonly.safetensors"

    # (任意) LoRAモデル設定
    lora_model: ""
    lora_weight: 0.8

    # 生成パラメータ
    steps: 30
    width: 1024
    height: 1792
    negative_prompt: "worst quality, low quality, bad anatomy, ugly, deformed"
    quality_keywords: "masterpiece, best quality"
```

---

## これで準備完了

* Stable Diffusion WebUI (Automatic1111) がAPIモードで起動可能
* `http://127.0.0.1:7860/docs` にアクセスして動作確認
* 本ツールから画像生成が可能になります

---
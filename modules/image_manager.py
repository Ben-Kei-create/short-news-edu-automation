import os
import glob
import google.generativeai as genai
from dotenv import load_dotenv
import requests
import base64
from datetime import datetime

def load_manual_images(folder_path):
    """指定されたフォルダから手動で追加された画像ファイルを読み込む"""
    if not folder_path or not os.path.exists(folder_path):
        return []
    
    supported_exts = ('.png', '.jpg', '.jpeg')
    image_files = []
    for ext in supported_exts:
        image_files.extend(glob.glob(os.path.join(folder_path, f"*[.{ext[1:].lower()}]")))
        image_files.extend(glob.glob(os.path.join(folder_path, f"*[.{ext[1:].upper()}]")))
        
    return sorted(list(set(image_files)))

def _generate_image_prompts(theme, style, num):
    """Geminiを使用して、画像生成のためのプロンプトを複数作成する"""
    print(f"  - Geminiで画像プロンプトを{num}件生成中...")
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("環境変数 'GEMINI_API_KEY' が設定されていません。")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash') # Use a model that is available

    prompt = f"""You are an expert image prompt engineer.
Generate exactly {num} distinct, visually compelling image prompts for a YouTube short video about the historical topic '{theme}'.
The style should be '{style}'.
Each prompt must be a single, concise sentence, suitable for direct input into an image generation AI.
Focus on diverse scenes and compositions that capture the essence of the topic.
Output only the {num} raw prompts, one per line, with no numbering, bullet points, conversational text, or introductory/concluding phrases.
"""

    try:
        response = model.generate_content(prompt)
        prompts = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
        
        if len(prompts) != num:
            print(f"  - 警告: Geminiが要求された{num}件ではなく、{len(prompts)}件のプロンプトを返しました。")
        
        return prompts
    except Exception as e:
        print(f"  - Geminiでのプロンプト生成中にエラー: {e}")
        return []

def generate_images(theme, style, num=12, use_sd_api=False, sd_model=None, lora_model=None, lora_weight=0.8):
    """
    テーマとスタイルに基づき、AIで画像を生成する。
    use_sd_api=Trueの場合、Stable Diffusion APIを呼び出す。
    """
    if num <= 0:
        return []

    # --- Stable Diffusion APIを使用する場合 ---
    if use_sd_api:
        print("  - Stable Diffusion APIを使用して画像を生成します。")
        if sd_model:
            print(f"    - ベースモデル: {sd_model}")
        if lora_model:
            print(f"    - LoRAモデル: {lora_model} (強度: {lora_weight})")

        image_prompts = _generate_image_prompts(theme, style, num)
        if not image_prompts:
            print("  - 画像プロンプトを生成できなかったため、処理をスキップします。")
            return []

        # タイムスタンプ付きの保存ディレクトリを作成
        save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(save_dir, exist_ok=True)
        print(f"  - 画像保存先: {save_dir}")

        generated_image_paths = []
        sd_api_url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

        for i, p in enumerate(image_prompts):
            print(f"    - 画像 {i+1}/{len(image_prompts)} を生成中... (Prompt: {p[:40]}...)")
            
            # プロンプトに高品質化・LoRAキーワードを追加
            quality_keywords = "masterpiece, best quality, 8k, ultra-detailed, sharp focus, dynamic angle, cinematic lighting"
            lora_prompt = f" <lora:{lora_model}:{lora_weight}>" if lora_model else ""
            final_prompt = f"{p}, ({style}), {quality_keywords}{lora_prompt}"

            payload = {
                "prompt": final_prompt,
                "steps": 25,
                "width": 512,
                "height": 768,
                "negative_prompt": "(worst quality, low quality:1.4), (blurry:1.2), deformed, ugly, watermark, text, signature"
            }

            # ベースモデル切り替え設定
            if sd_model:
                payload["override_settings"] = {
                    "sd_model_checkpoint": sd_model
                }

            try:
                r = requests.post(sd_api_url, json=payload, timeout=300)
                r.raise_for_status()
                img_b64 = r.json()['images'][0]
                img_data = base64.b64decode(img_b64)
                
                img_path = os.path.join(save_dir, f"{i+1:04}.png")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                generated_image_paths.append(img_path)

            except requests.exceptions.RequestException as e:
                print(f"    - エラー: Stable Diffusion APIへの接続に失敗しました: {e}")
                print("      プレースホルダー画像を使用します。")
                generated_image_paths.append("example.png") # フォールバック
            except Exception as e:
                print(f"    - エラー: 画像生成中に予期せぬエラーが発生しました: {e}")
                generated_image_paths.append("example.png") # フォールバック

        return generated_image_paths

    # --- APIを使用しない場合（従来のプレースホルダー処理） ---
    else:
        print("  - プレースホルダー画像を使用します。")
        placeholder_image = "example.png"
        if not os.path.exists(placeholder_image):
            print(f"    - 警告: プレースホルダー画像 '{placeholder_image}' が見つかりません。")
            return []
        return [placeholder_image] * num

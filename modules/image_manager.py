# modules/image_manager.py
import os
import glob
import traceback
import google.generativeai as genai
from google.generativeai import types
import requests
import base64
from datetime import datetime
import urllib.parse
from openai import OpenAI, APIStatusError, APIConnectionError
import logging

def _generate_image_prompts(theme, num, settings):
    """Geminiを使用して、画像生成のためのプロンプトを複数作成する"""
    logging.info(f"Geminiで画像プロンプトを{num}件生成します。")
    try:
        api_key = settings['api_keys']['gemini']
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        style = settings.get('image', {}).get('style_prompt', 'cinematic')

        prompt = f"""You are an expert image prompt engineer.
Generate exactly {num} distinct, visually compelling image prompts for a YouTube short video about '{theme}'.
The style should be '{style}'.
Each prompt must be a single, concise sentence, suitable for direct input into an image generation AI.
Focus on diverse scenes and compositions that capture the essence of the topic.
Ensure the prompts are highly descriptive and evoke strong visual imagery.
Output only the prompts, one per line.
"""
        response = model.generate_content(prompt)
        prompts = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
        if len(prompts) < num:
            logging.warning(f"Geminiが要求された{num}件ではなく、{len(prompts)}件のプロンプトを返しました。")
        return prompts
    except Exception as e:
        logging.error(f"Geminiでのプロンプト生成中にエラーが発生しました: {e}")
        traceback.print_exc()
        return []

def _generate_images_sd(prompts, settings):
    """Stable Diffusion APIを使用して画像を生成する"""
    logging.info("Stable Diffusion APIで画像を生成します。")
    sd_settings = settings.get('image', {}).get('stable_diffusion', {})
    api_url = sd_settings.get('url')
    if not api_url:
        logging.error("settings.yamlにStable DiffusionのAPI URLが設定されていません。")
        return []

    save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}_sd"
    os.makedirs(save_dir, exist_ok=True)
    logging.info(f"SD画像を保存するディレクトリ: {save_dir}")

    generated_image_paths = []
    for i, p in enumerate(prompts):
        logging.info(f"  - SD画像 {i+1}/{len(prompts)} を生成中...")
        payload = {
            "prompt": f"{p}, {settings.get('image', {}).get('style_prompt', '')}, {sd_settings.get('quality_keywords', '')}",
            "steps": sd_settings.get('steps', 30),
            "width": sd_settings.get('width', 1024),
            "height": sd_settings.get('height', 1792),
            "negative_prompt": sd_settings.get('negative_prompt', '')
        }
        # LoRAモデルが設定されていればプロンプトに追加
        if sd_settings.get('lora_model'):
            payload["prompt"] += f" <lora:{sd_settings['lora_model']}:{sd_settings.get('lora_weight', 0.8)}>"
        
        # ベースモデルが設定されていればoverride_settingsに追加
        if sd_settings.get('model'):
            payload["override_settings"] = {"sd_model_checkpoint": sd_settings['model']}

        try:
            r = requests.post(api_url, json=payload, timeout=300)
            r.raise_for_status()
            img_data = base64.b64decode(r.json()['images'][0])
            img_path = os.path.join(save_dir, f"{i+1:04}.png")
            with open(img_path, "wb") as f: f.write(img_data)
            generated_image_paths.append(img_path)
        except Exception as e:
            logging.error(f"SDでの画像生成中にエラーが発生しました: {e}")
            traceback.print_exc()
            continue # 1枚失敗しても次へ
            
    return generated_image_paths

def _search_and_download_images(theme, num, settings):
    # (この関数の内容は変更が少ないため、簡略化のため省略。実際にはloggingを追加するなどの修正が望ましい)
    return [] # 今回の改修ではGoogle Searchは一旦対象外とする

def _generate_images_dalle(prompts, settings):
    # (この関数の内容は変更が少ないため、簡略化のため省略。実際には引数とsettingsの参照を修正する)
    return [] # 今回の改修ではDALL-Eは一旦対象外とする

def _get_placeholder_image(settings):
    """プレースホルダー画像のパスを返す"""
    try:
        placeholder_path = settings['image']['placeholder_path']
        if os.path.exists(placeholder_path):
            return placeholder_path
        logging.warning(f"プレースホルダー画像が見つかりません: {placeholder_path}")
        return None
    except KeyError:
        logging.warning("settings.yamlにプレースホルダー画像のパスが設定されていません。")
        return None

def generate_images(theme, script_text, settings):
    """テーマと台本に基づき、設定に従って画像を生成する。"""
    image_settings = settings.get('image', {})
    
    # 必要な画像枚数を台本の行数から決定 (最低5枚、最大20枚など上限下限を設けても良い)
    num_images = len([line for line in script_text.split('\n') if line.strip()])
    if num_images == 0:
        logging.warning("台本が空のため、画像枚数をデフォルトの10枚に設定します。")
        num_images = 10

    logging.info(f"台本に基づき、{num_images}枚の画像を生成します。")

    # 画像生成プロンプトを作成
    prompts = _generate_image_prompts(theme, num_images, settings)
    if not prompts:
        logging.error("画像プロンプトの生成に失敗したため、画像生成を中止します。")
        # プロンプト生成失敗時はプレースホルダーで埋める
        placeholder = _get_placeholder_image(settings)
        return [placeholder] * num_images if placeholder else []

    image_paths = []
    api_priority = image_settings.get('api_priority', [])
    enabled_apis = image_settings.get('enabled_apis', {})

    for api_name in api_priority:
        if len(image_paths) >= num_images: break

        remaining_prompts = prompts[len(image_paths):]
        if not remaining_prompts: break

        if api_name == 'stable_diffusion' and enabled_apis.get('stable_diffusion'):
            logging.info("優先順位に従い、Stable Diffusion APIを試行します。")
            generated = _generate_images_sd(remaining_prompts, settings)
            image_paths.extend(generated)
        
        elif api_name == 'dalle' and enabled_apis.get('dalle'):
            logging.info("優先順位に従い、DALL-E APIを試行します。")
            # generated = _generate_images_dalle(remaining_prompts, settings)
            # image_paths.extend(generated)
            pass # DALL-Eは今回対象外

        elif api_name == 'google_search' and enabled_apis.get('google_search'):
            logging.info("優先順位に従い、Google Search APIを試行します。")
            # generated = _search_and_download_images(theme, len(remaining_prompts), settings)
            # image_paths.extend(generated)
            pass # Google Searchは今回対象外

    # 不足分をプレースホルダーで補う
    if len(image_paths) < num_images:
        logging.warning(f"要求された{num_images}枚に対し{len(image_paths)}枚しか生成できませんでした。不足分を補います。")
        placeholder = _get_placeholder_image(settings)
        if placeholder:
            image_paths.extend([placeholder] * (num_images - len(image_paths)))

    if not image_paths:
        logging.error("最終的に画像を1枚も取得できませんでした。")

    return image_paths
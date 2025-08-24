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

def load_manual_images(folder_path):
    """指定されたフォルダから手動で追加された画像ファイルを読み込む"""
    if not folder_path or not os.path.exists(folder_path):
        return []
    
    supported_exts = ('.png', '.jpg', '.jpeg')
    image_files = []
    for ext in supported_exts:
        image_files.extend(glob.glob(os.path.join(folder_path, f"*.{ext[1:].lower()}")))
        image_files.extend(glob.glob(os.path.join(folder_path, f"*.{ext[1:].upper()}")))
        
    return sorted(list(set(image_files)))

def _generate_image_prompts(theme, style, num, settings):
    """Geminiを使用して、画像生成のためのプロンプトを複数作成する"""
    print(f"  - Geminiで画像プロンプトを{num}件生成中...")
    try:
        api_key = settings['api_keys']['gemini']
        if not api_key or "ここに" in api_key:
            print("  - エラー: settings.yamlに有効な 'api_keys.gemini' が設定されていません。")
            return []
    except KeyError:
        print("  - エラー: settings.yamlに 'api_keys.gemini' の設定がありません。")
        return []

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    prompt = f"""You are an expert image prompt engineer.
Generate exactly {num} distinct, visually compelling image prompts for a YouTube short video about the historical topic '{theme}'.
The style should be '{style}'.
Each prompt must be a single, concise sentence, suitable for direct input into an image generation AI.
Focus on diverse scenes and compositions that capture the essence of the topic.
Ensure the prompts are highly descriptive and evoke strong visual imagery.
"""

    try:
        response = model.generate_content(prompt)
        prompts = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
        if len(prompts) != num:
            print(f"  - 警告: Geminiが要求された{num}件ではなく、{len(prompts)}件のプロンプトを返しました。")
        return prompts
    except types.BlockedPromptException as e:
        print(f"  - エラー: Gemini APIが不適切なコンテンツを検出しました: {e}")
    except Exception:
        print(f"  - エラー: Geminiでのプロンプト生成中に予期せぬエラーが発生しました。")
        traceback.print_exc()
    return []

def _generate_images_sd(theme, style, num, settings, sd_model, lora_model, lora_weight):
    """Stable Diffusion APIを使用して画像を生成する"""
    print("  - Stable Diffusion APIで画像を生成します。")
    try:
        sd_api_url = settings['stable_diffusion']['api_url']
        if not sd_api_url or "http" not in sd_api_url:
            print(f"  - エラー: settings.yamlに有効なSD API URL ('stable_diffusion.api_url')が設定されていません。")
            return []
    except KeyError:
        print(f"  - エラー: settings.yamlにSD API URL ('stable_diffusion.api_url')の設定がありません。")
        return []

    if sd_model: print(f"    - ベースモデル: {sd_model}")
    if lora_model: print(f"    - LoRAモデル: {lora_model} (強度: {lora_weight})")

    image_prompts = _generate_image_prompts(theme, style, num, settings)
    if not image_prompts:
        print("  - 画像プロンプトを生成できなかったため、SDでの画像生成をスキップします。")
        return []

    save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}_sd"
    os.makedirs(save_dir, exist_ok=True)
    print(f"  - 画像保存先: {save_dir}")

    generated_image_paths = []
    for i, p in enumerate(image_prompts):
        print(f"    - 画像 {i+1}/{len(image_prompts)} を生成中...")
        payload = {
            "prompt": f"{p}, ({style}), {settings['stable_diffusion']['quality_keywords']}" + (f" <lora:{lora_model}:{lora_weight}>" if lora_model else ""),
            "steps": settings['stable_diffusion']['steps'],
            "width": settings['stable_diffusion']['width'],
            "height": settings['stable_diffusion']['height'],
            "negative_prompt": settings['stable_diffusion']['negative_prompt']
        }
        if sd_model:
            payload["override_settings"] = {"sd_model_checkpoint": sd_model}

        try:
            r = requests.post(sd_api_url, json=payload, timeout=300)
            r.raise_for_status()
            img_data = base64.b64decode(r.json()['images'][0])
            img_path = os.path.join(save_dir, f"{i+1:04}.png")
            with open(img_path, "wb") as f: f.write(img_data)
            generated_image_paths.append(img_path)
        except requests.exceptions.Timeout:
            print(f"    - エラー: SD APIへの接続がタイムアウトしました。")
        except requests.exceptions.ConnectionError:
            print(f"    - エラー: SD APIへの接続に失敗しました。APIサーバーが起動しているか確認してください。")
        except requests.exceptions.HTTPError as e:
            print(f"    - エラー: SD APIからHTTPエラー (ステータスコード: {e.response.status_code})。レスポンス: {e.response.text[:200]}")
        except Exception:
            print(f"    - エラー: SDでの画像生成中に予期せぬエラーが発生しました。")
            traceback.print_exc()
    return generated_image_paths

def _search_and_download_images(theme, num, settings):
    """Google Custom Search APIを使って画像を検索・ダウンロードする"""
    print(f"  - Google Custom Search APIで画像を{num}件検索・ダウンロードします。")
    try:
        api_key = settings['api_keys']['google_custom_search']['api_key']
        cse_id = settings['api_keys']['google_custom_search']['cse_id']
        if "ここに" in api_key or "ここに" in cse_id:
            print("  - エラー: Google APIキーまたはCSE IDがプレースホルダーのままです。")
            return []
    except KeyError:
        print("  - エラー: settings.yamlにGoogleのAPIキー/CSE ID設定がありません。")
        return []

    save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}_google"
    os.makedirs(save_dir, exist_ok=True)
    print(f"  - 画像保存先: {save_dir}")

    downloaded_image_paths = []
    start_index = 1
    while len(downloaded_image_paths) < num:
        params = {
            'key': api_key, 'cx': cse_id, 'q': urllib.parse.quote(f"{theme} photography"),
            'searchType': 'image', 'num': min(10, num - len(downloaded_image_paths)),
            'start': start_index, 'rights': 'cc_publicdomain,cc_attribute,cc_sharealike', 'imgSize': 'large'
        }
        try:
            response = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=30)
            response.raise_for_status()
            for item in response.json().get('items', []):
                try:
                    image_url = item['link']
                    image_data = requests.get(image_url, timeout=30).content
                    file_extension = os.path.splitext(urllib.parse.urlparse(image_url).path)[1] or '.jpg'
                    img_path = os.path.join(save_dir, f"{len(downloaded_image_paths) + 1:04}{file_extension}")
                    with open(img_path, "wb") as f: f.write(image_data)
                    downloaded_image_paths.append(img_path)
                    print(f"    - 画像 {len(downloaded_image_paths)}/{num} をダウンロードしました。")
                    if len(downloaded_image_paths) >= num: break
                except Exception as e:
                    print(f"    - 警告: 画像のダウンロードまたは保存に失敗しました ({image_url})。スキップします: {e}")
            if 'nextPage' not in response.json().get('queries', {}): break
            start_index += 10
        except requests.exceptions.Timeout:
            print("  - エラー: Google APIへの接続がタイムアウトしました。")
            break
        except requests.exceptions.HTTPError as e:
            print(f"  - エラー: Google APIからHTTPエラー (ステータスコード: {e.response.status_code})。レスポンス: {e.response.text[:200]}")
            break
        except requests.exceptions.RequestException as e:
            print(f"  - エラー: Google APIへのリクエスト中にエラーが発生しました: {e}")
            break
    return downloaded_image_paths

def _generate_images_dalle(theme, style, num, settings):
    """DALL-E APIを使用して画像を生成する"""
    print(f"  - DALL-E APIで画像を{num}件生成します。")
    try:
        api_key = settings['api_keys']['dalle']['api_key']
        if "ここに" in api_key:
            print("  - エラー: DALL-EのAPIキーがプレースホルダーのままです。")
            return []
    except KeyError:
        print("  - エラー: settings.yamlにDALL-EのAPIキー設定がありません。")
        return []

    client = OpenAI(api_key=api_key)
    image_prompts = _generate_image_prompts(theme, style, num, settings)
    if not image_prompts:
        print("  - 画像プロンプトを生成できなかったため、DALL-Eでの画像生成をスキップします。")
        return []

    save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}_dalle"
    os.makedirs(save_dir, exist_ok=True)
    print(f"  - 画像保存先: {save_dir}")

    generated_image_paths = []
    for i, p in enumerate(image_prompts):
        print(f"    - 画像 {i+1}/{len(image_prompts)} を生成中...")
        try:
            response = client.images.generate(model="dall-e-3", prompt=f"{p}, {style}", size="1024x1792", quality="standard", n=1)
            image_url = response.data[0].url
            image_data = requests.get(image_url, timeout=60).content
            img_path = os.path.join(save_dir, f"{i+1:04}.png")
            with open(img_path, "wb") as f: f.write(image_data)
            generated_image_paths.append(img_path)
            print(f"      -> 画像をダウンロードしました: {img_path}")
        except APIConnectionError as e:
            print(f"    - エラー: DALL-E APIへの接続に失敗しました: {e.__cause__}")
        except APIStatusError as e:
            print(f"    - エラー: DALL-E APIからエラーステータス: status_code={e.status_code}, response={e.response}")
        except requests.exceptions.RequestException as e:
            print(f"    - エラー: DALL-Eが生成した画像のダウンロードに失敗しました: {e}")
        except Exception:
            print(f"    - エラー: DALL-Eでの処理中に予期せぬエラーが発生しました。")
            traceback.print_exc()
    return generated_image_paths

def _get_placeholder_images(num, settings):
    """プレースホルダー画像のリストを返す"""
    if num <= 0:
        return []
    print(f"  - プレースホルダー画像で{num}枚を補います。")
    try:
        placeholder_image = settings['general']['placeholder_image_path']
        if not os.path.exists(placeholder_image):
            print(f"    - 警告: プレースホルダー画像 '{placeholder_image}' が見つかりません。")
            return []
        return [placeholder_image] * num
    except KeyError:
        print("    - 警告: settings.yamlにプレースホルダー画像パスが設定されていません。")
        return []

def generate_images(theme, style, num=12, use_sd_api=False, use_google_search=False, use_dalle=False, sd_model=None, lora_model=None, lora_weight=0.8, settings=None):
    """テーマとスタイルに基づき、AIで画像を生成または検索する。"""
    if num <= 0:
        return []

    image_paths = []
    if use_dalle:
        image_paths = _generate_images_dalle(theme, style, num, settings)
    elif use_google_search:
        image_paths = _search_and_download_images(theme, num, settings)
    elif use_sd_api:
        image_paths = _generate_images_sd(theme, style, num, settings, sd_model, lora_model, lora_weight)
    else:
        # No image generation method selected, use placeholders directly
        print("  - 画像生成方法が指定されていないため、プレースホルダー画像を使用します。")
        image_paths = _get_placeholder_images(num, settings)

    # Fallback logic
    if len(image_paths) < num:
        print(f"  - 警告: 要求された{num}枚の画像に対し、{len(image_paths)}枚しか取得できませんでした。")
        placeholders = _get_placeholder_images(num - len(image_paths), settings)
        image_paths.extend(placeholders)

    if not image_paths:
        print("  - 致命的エラー: 画像を1枚も取得できず、プレースホルダーも利用できませんでした。")

    return image_paths

import os
import glob
import google.generativeai as genai
from google.generativeai import types
import requests
import base64
from datetime import datetime
import urllib.parse
from openai import OpenAI

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
    except KeyError:
        print("  - エラー: settings.yamlに 'api_keys.gemini' が設定されていません。")
        return []

    if not api_key or "AIza" not in api_key:
        raise ValueError("設定ファイルに有効な 'api_keys.gemini' が設定されていません。")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    prompt = f"""You are an expert image prompt engineer.
Generate exactly {num} distinct, visually compelling image prompts for a YouTube short video about the historical topic '{theme}'.
The style should be '{style}'.
Each prompt must be a single, concise sentence, suitable for direct input into an image generation AI.
Focus on diverse scenes and compositions that capture the essence of the topic.
Ensure the prompts are highly descriptive and evoke strong visual imagery.
Consider the following aspects for each prompt:
- **Subject**: What is the main focus of the image?
- **Action/Emotion**: What is happening or what emotion is conveyed?
- **Setting/Environment**: Where is the scene taking place?
- **Lighting/Atmosphere**: What is the mood or time of day?
- **Composition/Angle**: How is the scene framed? (e.g., close-up, wide shot, dynamic angle)
- **Color Palette**: What colors dominate the scene?

Output only the {num} raw prompts, one per line, with no numbering, bullet points, conversational text, or introductory/concluding phrases.
"""

    try:
        response = model.generate_content(prompt)
        prompts = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
        
        if len(prompts) != num:
            print(f"  - 警告: Geminiが要求された{num}件ではなく、{len(prompts)}件のプロンプトを返しました。")
        
        return prompts
    except types.BlockedPromptException as e:
        print(f"  - エラー: Gemini APIが不適切なコンテンツを検出しました。プロンプトを調整してください: {e}")
        return []
    except Exception as e:
        print(f"  - エラー: Geminiでのプロンプト生成中に予期せぬエラーが発生しました: {e}")
        return []

def _search_and_download_images(theme, num, settings):
    """Google Custom Search APIを使って画像を検索し、ダウンロードする"""
    print(f"  - Google Custom Search APIを使用して画像を{num}件検索・ダウンロードします。")
    try:
        api_key = settings['api_keys']['google_custom_search']['api_key']
        cse_id = settings['api_keys']['google_custom_search']['cse_id']
    except KeyError:
        print("  - エラー: settings.yamlに 'api_keys.google_custom_search' の 'api_key' または 'cse_id' が設定されていません。")
        return []

    if "ここに" in api_key or "ここに" in cse_id:
        print("  - エラー: APIキーまたはCSE IDが設定ファイル内でプレースホルダーのままです。")
        return []

    save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}_google"
    os.makedirs(save_dir, exist_ok=True)
    print(f"  - 画像保存先: {save_dir}")

    search_url = "https://www.googleapis.com/customsearch/v1"
    query = urllib.parse.quote(f"{theme} photography")

    downloaded_image_paths = []
    start_index = 1
    while len(downloaded_image_paths) < num:
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'searchType': 'image',
            'num': min(10, num - len(downloaded_image_paths)),
            'start': start_index,
            'rights': 'cc_publicdomain,cc_attribute,cc_sharealike',
            'imgSize': 'large'
        }

        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            search_results = response.json()

            if 'items' not in search_results or not search_results['items']:
                print("  - 警告: これ以上画像が見つかりませんでした。")
                break

            for item in search_results['items']:
                try:
                    image_url = item['link']
                    image_data = requests.get(image_url, timeout=30).content
                    
                    file_extension = os.path.splitext(urllib.parse.urlparse(image_url).path)[1]
                    if not file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                        file_extension = '.jpg'
                    
                    img_path = os.path.join(save_dir, f"{len(downloaded_image_paths) + 1:04}{file_extension}")

                    with open(img_path, "wb") as f:
                        f.write(image_data)
                    downloaded_image_paths.append(img_path)
                    print(f"    - 画像 {len(downloaded_image_paths)}/{num} をダウンロードしました: {img_path}")

                    if len(downloaded_image_paths) >= num:
                        break
                except Exception as e:
                    print(f"    - 警告: 画像のダウンロードまたは保存に失敗しました ({image_url})。スキップします: {e}")
            
            start_index += 10
            if 'nextPage' not in search_results.get('queries', {}):
                break

        except requests.exceptions.Timeout:
            print("  - エラー: Google Custom Search APIへの接続がタイムアウトしました。")
            break
        except requests.exceptions.RequestException as e:
            print(f"  - エラー: Google Custom Search APIへのリクエスト中にエラーが発生しました: {e}")
            break
        except Exception as e:
            print(f"  - エラー: 画像検索中に予期せぬエラーが発生しました: {e}")
            break
            
    if not downloaded_image_paths:
        print("  - 警告: Google画像検索で有効な画像を1枚も取得できませんでした。")
        placeholder_image = settings.get('general', {}).get('placeholder_image_path', 'example.png')
        if os.path.exists(placeholder_image):
            return [placeholder_image] * num
        return []

    return downloaded_image_paths

def _generate_images_dalle(theme, style, num, settings):
    """DALL-E APIを使用して画像を生成する"""
    print(f"  - DALL-E APIを使用して画像を{num}件生成します。")
    try:
        api_key = settings['api_keys']['dalle']['api_key']
    except KeyError:
        print("  - エラー: settings.yamlに 'api_keys.dalle.api_key' が設定されていません。")
        return []

    if "ここに" in api_key:
        print("  - エラー: DALL-EのAPIキーが設定ファイル内でプレースホルダーのままです。")
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
        print(f"    - 画像 {i+1}/{len(image_prompts)} を生成中... (Prompt: {p[:40]}...)")
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"{p}, {style}",
                size="1024x1792",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            image_data = requests.get(image_url, timeout=60).content

            img_path = os.path.join(save_dir, f"{i+1:04}.png")
            with open(img_path, "wb") as f:
                f.write(image_data)
            generated_image_paths.append(img_path)
            print(f"      -> 画像をダウンロードしました: {img_path}")

        except Exception as e:
            print(f"    - エラー: DALL-Eでの画像生成またはダウンロード中にエラーが発生しました: {e}")
            print("      プレースホルダー画像を使用します。")
            generated_image_paths.append(settings['general']['placeholder_image_path'])

    return generated_image_paths

def generate_images(theme, style, num=12, use_sd_api=False, use_google_search=False, use_dalle=False, sd_model=None, lora_model=None, lora_weight=0.8, settings=None):
    """
    テーマとスタイルに基づき、AIで画像を生成または検索する。
    """
    if num <= 0:
        return []

    if use_dalle:
        return _generate_images_dalle(theme, style, num, settings)
    elif use_google_search:
        return _search_and_download_images(theme, num, settings)
    elif use_sd_api:
        print("  - Stable Diffusion APIを使用して画像を生成します。")
        if sd_model:
            print(f"    - ベースモデル: {sd_model}")
        if lora_model:
            print(f"    - LoRAモデル: {lora_model} (強度: {lora_weight})")

        image_prompts = _generate_image_prompts(theme, style, num, settings)
        if not image_prompts:
            print("  - 画像プロンプトを生成できなかったため、処理をスキップします。")
            return []

        save_dir = f"input/images/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(save_dir, exist_ok=True)
        print(f"  - 画像保存先: {save_dir}")

        generated_image_paths = []
        sd_api_url = settings['stable_diffusion']['api_url']

        for i, p in enumerate(image_prompts):
            print(f"    - 画像 {i+1}/{len(image_prompts)} を生成中... (Prompt: {p[:40]}...)")
            
            quality_keywords = settings['stable_diffusion']['quality_keywords']
            lora_prompt = f" <lora:{lora_model}:{lora_weight}>" if lora_model else ""
            final_prompt = f"{p}, ({style}), {quality_keywords}{lora_prompt}"

            payload = {
                "prompt": final_prompt,
                "steps": settings['stable_diffusion']['steps'],
                "width": settings['stable_diffusion']['width'],
                "height": settings['stable_diffusion']['height'],
                "negative_prompt": settings['stable_diffusion']['negative_prompt']
            }

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

            except requests.exceptions.Timeout as e:
                print(f"    - エラー: Stable Diffusion APIへの接続がタイムアウトしました: {e}")
                print("      プレースホルダー画像を使用します。")
                generated_image_paths.append(settings['general']['placeholder_image_path'])
            except requests.exceptions.ConnectionError as e:
                print(f"    - エラー: Stable Diffusion APIへの接続に失敗しました。APIサーバーが起動しているか確認してください: {e}")
                print("      プレースホルダー画像を使用します。")
                generated_image_paths.append(settings['general']['placeholder_image_path'])
            except requests.exceptions.HTTPError as e:
                print(f"    - エラー: Stable Diffusion APIからHTTPエラーが返されました: {e}")
                print("      プレースホルダー画像を使用します。")
                generated_image_paths.append(settings['general']['placeholder_image_path'])
            except requests.exceptions.RequestException as e:
                print(f"    - エラー: Stable Diffusion APIへのリクエスト中に予期せぬエラーが発生しました: {e}")
                print("      プレースホルダー画像を使用します。")
                generated_image_paths.append(settings['general']['placeholder_image_path'])
            except Exception as e:
                print(f"    - エラー: 画像生成中に予期せぬエラーが発生しました: {e}")
                generated_image_paths.append(settings['general']['placeholder_image_path'])

        return generated_image_paths
    else:
        print("  - プレースホルダー画像を使用します。")
        placeholder_image = settings['general']['placeholder_image_path']
        if not os.path.exists(placeholder_image):
            print(f"    - 警告: プレースホルダー画像 '{placeholder_image}' が見つかりません。")
            return []
        return [placeholder_image] * num
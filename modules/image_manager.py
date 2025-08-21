# modules/image_manager.py
import os
import glob
import google.generativeai as genai
from dotenv import load_dotenv

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
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
# 指示
あなたはクリエイティブディレクターです。
以下のテーマと画風に基づき、YouTubeショート動画用の画像を生成するための、創造的で多様なプロンプトを{num}個、リスト形式で提案してください。

# テーマ
{theme}

# 画風
{style}

# 条件
- 各プロンプトは、英語で記述してください。
- 1つのプロンプトは1文で、簡潔かつ視覚的にイメージしやすいものにしてください。
- 多様なシーンや構図を提案してください。

# 出力形式
- プロンプト1
- プロンプト2
..."

    try:
        response = model.generate_content(prompt)
        # 生成されたテキストを行ごとに分割し、先頭の "- " を削除
        prompts = [line.strip().lstrip('- ') for line in response.text.strip().split('\n') if line.strip()] 
        return prompts
    except Exception as e:
        print(f"  - Geminiでのプロンプト生成中にエラー: {e}")
        return []

def generate_images(theme, style, num=5):
    """
    テーマとスタイルに基づき、AIで画像を生成する。
    現在はプロンプト生成のみを実装し、画像はプレースホルダーを返す。
    """
    if num <= 0:
        return []

    # Step 1: Geminiで画像プロンプトを生成
    image_prompts = _generate_image_prompts(theme, style, num)
    if not image_prompts:
        print("  - 画像プロンプトを生成できなかったため、処理をスキップします。")
        return []

    generated_image_paths = []
    print(f"  - {len(image_prompts)}件のプロンプトで画像を生成します (現在はプレースホルダーを使用)。")

    # Step 2: 各プロンプトで画像を生成（現在はプレースホルダー）
    for i, prompt_text in enumerate(image_prompts):
        print(f"    - Prompt {i+1}: {prompt_text}")
        # --- ここに将来的に画像生成AIの呼び出しコードを実装 ---
        # 例: generated_image = some_image_generator(prompt_text)
        # -----------------------------------------------------
        
        # 仮のプレースホルダー画像を使用
        placeholder_image = "example.png"
        if os.path.exists(placeholder_image):
            generated_image_paths.append(placeholder_image)
        else:
            print(f"    - 警告: プレースホルダー画像 '{placeholder_image}' が見つかりません。")

    return generated_image_paths

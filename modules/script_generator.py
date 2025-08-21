# modules/script_generator.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

def generate_script(theme):
    """
    Gemini APIを使用して、指定されたテーマで「しくじり先生」風の台本を生成します。
    """
    # .envファイルから環境変数を読み込む
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("環境変数 'GEMINI_API_KEY' が設定されていません。.envファイルを確認してください。")

    # Gemini APIキーを設定
    genai.configure(api_key=api_key)

    # プロンプトの作成
    prompt = f"""
あなたはプロの放送作家です。
以下のテーマについて、視聴者が引き込まれるような「しくじり先生」風の面白いショート動画（60秒程度）の台本を生成してください。

# テーマ
{theme}

# 台本作成のポイント
- 冒頭で視聴者の興味を引く「ツカミ」を入れる。
- 教訓や学びがある、教育的な要素を含める。
- ユーモアを交え、堅苦しくなりすぎないようにする。
- 視聴者が「へぇ！」と思うような意外な事実を盛り込む。
- 全体はナレーションベースで構成する。
- 生成する台本はナレーション部分のみとし、他の説明は含めないでください。

# 出力形式
ナレーション本文のみ
"""

    try:
        # Geminiモデルを初期化してコンテンツを生成
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # 生成されたテキストを返す
        return response.text.strip()

    except Exception as e:
        print(f"Gemini APIの呼び出し中にエラーが発生しました: {e}")
        # エラー発生時は、テーマをそのまま返すなど、代替の挙動も検討可能
        return f"エラーにより台本を生成できませんでした。テーマ: {theme}"

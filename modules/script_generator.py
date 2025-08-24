# modules/script_generator.py
import os
import google.generativeai as genai
# from dotenv import load_dotenv # 削除

# generate_script 関数の引数に settings を追加
def generate_script(theme, settings):
    """
    Gemini APIを使用して、指定されたテーマで「しくじり先生」風の台本を生成します。
    """
    # .envファイルから環境変数を読み込む (削除)
    # load_dotenv()
    # api_key = os.getenv("GEMINI_API_KEY") # 変更
    api_key = settings['api_keys']['gemini']

    if not api_key:
        raise ValueError("設定ファイルに 'api_keys.gemini' が設定されていません。") # エラーメッセージ変更

    # Gemini APIキーを設定
    genai.configure(api_key=api_key)

    # プロンプトの作成
    prompt = f"""
あなたはプロの放送作家です。
以下のテーマについて、視聴者が最後まで釘付けになる「しくじり先生」風のバズりやすいショート動画の台本を生成してください。
動画の長さは厳密に60秒になるように、文字数を調整してください。
（日本語の場合、60秒のナレーションは約300文字から350文字程度が目安です。）

# テーマ
{theme}

# 台本作成のポイント

## 必須の構成（バズりやすい黄金パターン）
1. **フック（0-3秒）**: 衝撃的な一言で開始
   - 例：「え、まって！○○が実は××だったって知ってる？」
   - 例：「これ知らないとヤバい！○○の真実がこちら」
   
2. **問題提起（3-8秒）**: 視聴者の常識を覆す
   - 偉人の意外な一面や失敗を予告
   - 「実は○○は××で大失敗していた」
   
3. **本編・展開（8-45秒）**: ストーリーテリング
   - 具体的なエピソードを時系列で
   - 3つのポイントに分けて説明（理解しやすい）
   - 感情を揺さぶる表現を使用
   
4. **クライマックス（45-52秒）**: 最大の驚き
   - 一番衝撃的な事実を最後に持ってくる
   - 「だから○○は××になった」
   
5. **締め（52-60秒）**: 共感と行動喚起
   - 現代への教訓
   - 「みんなはどう思う？コメントで教えて！」

## バズりやすさを高める要素
- **感情フック**: 驚き、共感、笑い、怒りなど強い感情を誘発
- **ギャップ**: 期待と現実のギャップを最大化
- **親近感**: 現代の事例と関連付ける
- **コメント誘発**: 議論を呼ぶような問いかけで終了
- **リズム感**: 短文でテンポよく進行
- **視覚的な言葉**: 映像が浮かぶような表現を多用

## 禁止事項
- 冗長な説明や前置き
- 複雑すぎる内容
- ネガティブすぎる終わり方
- 教科書的な堅い表現

## 文字数配分の目安
- フック：15-20文字
- 問題提起：30-40文字  
- 本編：180-220文字
- クライマックス：50-60文字
- 締め：30-40文字
- 合計：300-350文字

# 出力形式
以下の形式で台本を作成してください：

【台本】
（ここに台本本文）

【文字数】○○文字

【構成メモ】
- フック：（内容）
- 問題提起：（内容）
- 本編：（内容）
- クライマックス：（内容）
- 締め：（内容）
"""

    try:
        # Geminiモデルを初期化してコンテンツを生成
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # 生成されたテキストを返す
        return response.text.strip()

    except genai.types.BlockedPromptException as e:
        print(f"エラー: Gemini APIが不適切なコンテンツを検出しました。プロンプトを調整してください: {e}")
        return f"エラーにより台本を生成できませんでした。テーマ: {theme}"
    except genai.types.APIError as e:
        print(f"エラー: Gemini APIの呼び出し中にAPIエラーが発生しました。APIキーまたはネットワーク接続を確認してください: {e}")
        return f"エラーにより台本を生成できませんでした。テーマ: {theme}"
    except Exception as e:
        print(f"エラー: Gemini APIの呼び出し中に予期せぬエラーが発生しました: {e}")
        return f"エラーにより台本を生成できませんでした。テーマ: {theme}"

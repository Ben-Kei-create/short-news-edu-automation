# modules/script_generator.py
import os
import google.generativeai as genai
from google.generativeai import types
import re
import logging # 追加

logger = logging.getLogger(__name__) # ロガーを取得

# generate_script 関数の引数に settings を追加
def generate_script(theme, settings):
    """
    Gemini APIを使用して、指定されたテーマで「しくじり先生」風の台本を生成します。
    成功した場合は台本テキストを、失敗した場合はNoneを返します。
    """
    try:
        api_key = settings['api_keys']['gemini']
        if not api_key or "ここに" in api_key:
            raise ValueError("設定ファイルに 'api_keys.gemini' が設定されていません。")
    except KeyError:
        raise ValueError("設定ファイルに 'api_keys.gemini' が設定されていません。")

    genai.configure(api_key=api_key)

    # settingsからスクリプト生成パラメータを取得
    script_settings = settings.get('script_generation', {})
    length = script_settings.get('length', 'short')
    tone = script_settings.get('tone', 'educational_humorous')
    target_audience = script_settings.get('target_audience', 'general_public')
    max_script_length_chars = script_settings.get('max_script_length_chars', 1000)

    # 長さに応じた文字数目安の調整
    if length == "short":
        duration_text = "厳密に60秒になるように、文字数を調整してください。（日本語の場合、60秒のナレーションは約300文字から350文字程度が目安です。）"
        char_guideline = "合計：300-350文字"
    elif length == "medium":
        duration_text = "厳密に90秒になるように、文字数を調整してください。（日本語の場合、90秒のナレーションは約450文字から525文字程度が目安です。）"
        char_guideline = "合計：450-525文字"
    elif length == "long":
        duration_text = "厳密に120秒になるように、文字数を調整してください。（日本語の場合、120秒のナレーションは約600文字から700文字程度が目安です。）"
        char_guideline = "合計：600-700文字"
    else: # デフォルトはshort
        duration_text = "厳密に60秒になるように、文字数を調整してください。（日本語の場合、60秒のナレーションは約300文字から350文字程度が目安です。）"
        char_guideline = "合計：300-350文字"

    prompt = f"""
あなたはプロの放送作家です。
以下のテーマについて、視聴者が最後まで釘付けになる「しくじり先生」風のショート動画の台本を生成してください。
動画の長さは{duration_text}
トーンは「{tone}」で、ターゲット視聴者は「{target_audience}」です。

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
- {char_guideline}

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
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(prompt, request_options={"timeout": 120})
        
        # レスポンスから台本部分のみを抽出
        match = re.search(r"【台本】(.*?)【文字数】", response.text, re.DOTALL)
        if match:
            script_text = match.group(1).strip()
            # max_script_length_chars を超える場合は切り詰める
            if len(script_text) > max_script_length_chars:
                script_text = script_text[:max_script_length_chars] + "..."
                logger.warning(f"生成された台本が最大文字数({max_script_length_chars})を超えたため、切り詰めました。")
            return script_text
        
        logger.error("生成されたテキストから台本の抽出に失敗しました。")
        # 修正: f-stringの閉じ忘れを修正
        logger.error(f"---{response.text[:500]}...")
        return None

    except types.BlockedPromptException as e:
        logger.error(f"Gemini APIが不適切なコンテンツを検出しました。テーマを変更してください: {e}", exc_info=True)
        return f"エラーにより台本を生成できませんでした。テーマ: {theme}"
    except Exception as e:
        logger.error(f"Gemini APIの呼び出し中に予期せぬエラーが発生しました: {e}", exc_info=True)
        return f"エラーにより台本を生成できませんでした。テーマ: {theme}"

import os
import google.generativeai as genai
from dotenv import load_dotenv
     
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
     
if not api_key:
    print("エラー: 環境変数 'GEMINI_API_KEY' が設定されていません。")
else:
    genai.configure(api_key=api_key)
    print("利用可能なGeminiモデル:")
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name} (Supported methods: {m.supported_generation_methods})")

# ショート動画自動生成パイプライン
# 「しくじり先生風ニュース連動ショート」
# フル自動 + 手動ハイブリッド対応

【概要】
本パイプラインは、ニュースやトレンド情報を基に、短尺（60秒以内）の
「しくじり先生風ショート動画」を自動生成するシステムです。
完全自動化に加え、手動画像や台本の差し替えも可能なハイブリッド設計です。
出力は縦動画MP4形式で、TikTok / YouTube Shorts用に最適化されています。

---

【主な機能】

1. ニュース取得
   * Google News RSSやトレンド情報からテーマを自動抽出
   * 引数でテーマ指定も可能

2. 台本生成
   * Gemini API / LLM を使用して、面白く教養的な台本を生成
   * 文体、テンポ、フック、SEO・バズ要素を自動調整

3. 画像生成・管理
   * AIによる偉人や失敗シーンのイラスト生成
   * 手動画像を優先採用、足りない分を自動生成で補填
   * 画像の偏り・重複を自動チェック
   * **MoviePy 2.x 系では `resize` → `resized` を使用**

4. 音声生成
   * ElevenLabs TTSで台本を音声化
   * 声質・感情・速度調整可能
   * 動画にセットする場合、**`subclip` → `subclipped`** を使用して任意秒数に切り出し

5. BGM設定
   * 指定MP3または自動選定
   * 音量調整でセリフを邪魔しない
   * BGMは60秒以上必要です。60秒未満のファイルが指定された場合は、エラーで処理を停止します。

6. 動画生成
   * moviepy / FFmpegで縦動画MP4作成
   * 画像スライド、音声、字幕、BGMを合成
   * 縦画面対応（TikTok / YouTube Shorts用）
   * **画像クリップの duration は `set_duration` → `with_duration`**

7. 投稿・管理自動化
   * TikTok / YouTube Shorts APIで自動投稿
   * タイトル・説明文・ハッシュタグ自動生成
   * 出力動画ログ管理（テーマ・画像・画風・BGM・生成日時）

8. 量産対応
   * バッチ生成で複数動画量産
   * 引数指定 or 自動生成で1回の実行で複数本生成可能

---

【引数仕様】

* theme       : 動画のテーマ（省略時は自動取得）
* bgm_path    : BGMファイルパス（省略時は自動選定）
* style       : 画像の画風（省略時は自動選定）
* script_file : 台本ファイルを指定（省略時はGemini自動生成）

使用例:

1. 完全自動生成
   ```bash
   python make_short.py
   ```

2. テーマ指定
   ```bash
   python make_short.py "ダイナマイト事故"
   ```

3. テーマ+BGM+画風指定
   ```bash
   python make_short.py "ダイナマイト事故" "bgm.mp3" "コミカル・ポップ"
   ```

---

【運用フロー】

1. ニュースRSS / 引数指定 → テーマ選定
2. Gemini API / LLM → 台本生成 + クオリティチェック
3. 画像選定
   * 手動画像優先
   * 足りない分を自動生成で補填
   * 画像重複チェック・バリエーション調整
   * **MoviePy 2.x 系対応: `resized`, `with_duration`**
4. ElevenLabs TTS → 音声生成
5. BGM選定・音量調整
   * BGMを選定し、音量を調整します。BGMの長さは60秒以上である必要があり、短い場合はエラーとなります。
6. moviepy / FFmpeg → 縦動画MP4生成
   * 音声クリップは `subclipped` を使用して60秒に切り出し
7. サムネイル・タイトル・説明文生成
8. 投稿・管理ログ更新 → TikTok / YouTube Shorts自動投稿

---

【拡張ポイント】

* Gemini API: 台本、画像プロンプト、タイトル、説明文生成
* ElevenLabs: 高品質TTS音声生成
* 手動画像統合: 自動生成画像と混在可能
* 投稿自動化: タイトル・説明文・タグ付与
* バズ最適化: SEO・トレンド連動、ハッシュタグ生成
* 運用効率化: バッチ生成、プリセット管理、エラー自動補填

---

【推奨環境】

* Python 3.10+
* ライブラリ:
  * openai / Gemini APIクライアント
  * requests (ElevenLabs TTS呼び出し)
  * moviepy / FFmpeg（MoviePy 2.x 系対応）
  * その他: pandas (ログ管理), os, random

---

【注意点】

* Gemini API / ElevenLabsのAPIキーが必要
* 投稿自動化には各SNSのAPI権限が必要
* 生成画像・音声は著作権や肖像権に注意
* 量産時はリソース負荷（画像生成・音声生成・動画合成）に注意
* MoviePy 2.x 系ではメソッド名が旧バージョンと異なるため注意
  * 例: `resize → resized`, `set_duration → with_duration`, `subclip → subclipped`
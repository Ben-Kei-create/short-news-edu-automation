import os
import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip
import traceback
import logging

logger = logging.getLogger(__name__)

def _find_font(settings):
    """設定ファイルからフォントパスを検索し、見つからなければフォールバックする"""
    font_path = settings.get('subtitle', {}).get('font')
    if font_path and os.path.exists(font_path):
        logger.info(f"サムネイルフォントとして設定ファイルの値を使用: {font_path}")
        return font_path
    
    # フォールバック
    logger.warning(f"設定されたフォントが見つかりません: {font_path}。システムフォントを探します。")
    for p in ['/System/Library/Fonts/ヒラギノ角ゴ ProN W3.otf', 'C:/Windows/Fonts/meiryo.ttc']:
        if os.path.exists(p):
            logger.info(f"フォールバックフォントを使用: {p}")
            return p
    
    logger.warning("適切な日本語フォントが見つかりませんでした。Arialで代用します。")
    return 'Arial'

def _draw_text_with_stroke(draw, pos, text, font, fill_color, stroke_color='black', stroke_width=2):
    """指定された位置に縁取り付きのテキストを描画する"""
    x, y = pos
    # 縁取りを描画
    for i in range(-stroke_width, stroke_width + 1):
        for j in range(-stroke_width, stroke_width + 1):
            if i != 0 or j != 0:
                draw.text((x + i, y + j), text, font=font, fill=stroke_color)
    # 本体を描画
    draw.text(pos, text, font=font, fill=fill_color)

def generate_thumbnail(video_file, theme, images, settings):
    """
    動画のテーマと画像リストからサムネイルを生成する。
    """
    yt_settings = settings.get('youtube', {})
    output_dir = "output/thumbnails"
    os.makedirs(output_dir, exist_ok=True)
    safe_theme = "".join(c for c in theme if c.isalnum())[:50]
    output_path = os.path.join(output_dir, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}_thumb.jpg")

    base_image_pil = None

    # --- 1. ベースとなる画像を取得 ---
    if yt_settings.get('thumbnail_from_video') and video_file and os.path.exists(video_file):
        frame_time = yt_settings.get('thumbnail_frame_time', 5)
        logger.info(f"動画の{frame_time}秒地点からサムネイル画像を抽出します。")
        try:
            with VideoFileClip(video_file) as clip:
                frame = clip.get_frame(frame_time)
                base_image_pil = Image.fromarray(frame)
        except Exception as e:
            logger.error(f"動画からのフレーム抽出に失敗しました: {e}", exc_info=True)
            # 失敗した場合は画像リストからの生成にフォールバック

    if base_image_pil is None:
        logger.info("生成された画像リストの最初の画像をサムネイルのベースとして使用します。")
        if not images or not os.path.exists(images[0]):
            logger.error("サムネイルの元となる画像がありません。")
            return None
        try:
            base_image_pil = Image.open(images[0])
        except Exception as e:
            logger.error(f"サムネイルのベース画像の読み込みに失敗しました: {e}", exc_info=True)
            return None

    try:
        # --- 2. 画像のリサイズと背景作成 ---
        resolution = settings.get('video', {}).get('resolution', [1080, 1920])
        thumbnail = Image.new("RGB", tuple(resolution), (0, 0, 0))
        
        base_image_pil.thumbnail(tuple(resolution), Image.Resampling.LANCZOS)
        paste_pos = ((resolution[0] - base_image_pil.width) // 2, (resolution[1] - base_image_pil.height) // 2)
        thumbnail.paste(base_image_pil, paste_pos)
        
        draw = ImageDraw.Draw(thumbnail)
        
        # --- 3. フォントの準備 ---
        font_path = _find_font(settings)
        subtitle_fontsize = settings.get('subtitle', {}).get('fontsize', 48)
        try:
            title_font = ImageFont.truetype(font_path, int(subtitle_fontsize * 1.5))
            series_font = ImageFont.truetype(font_path, int(subtitle_fontsize * 0.8))
        except Exception as e:
            logger.warning(f"指定フォントの読み込みに失敗({e})。デフォルトフォントで代替します。")
            title_font = ImageFont.load_default(size=int(subtitle_fontsize * 1.5))
            series_font = ImageFont.load_default(size=int(subtitle_fontsize * 0.8))

        # --- 4. テキストの描画 ---
        title_color = settings.get('subtitle', {}).get('color', 'white')
        series_text = yt_settings.get('thumbnail_series_text', '')
        series_color = (255, 255, 0) # 黄色固定

        # メインテーマを描画
        title_bbox = draw.textbbox((0, 0), theme, font=title_font)
        title_pos = ((resolution[0] - (title_bbox[2] - title_bbox[0])) / 2, 100)
        _draw_text_with_stroke(draw, title_pos, theme, title_font, title_color)

        # シリーズ名を描画
        if series_text:
            series_bbox = draw.textbbox((0, 0), series_text, font=series_font)
            series_pos = ((resolution[0] - (series_bbox[2] - series_bbox[0])) / 2, resolution[1] - 200)
            _draw_text_with_stroke(draw, series_pos, series_text, series_font, series_color)

        # --- 5. 保存 ---
        thumbnail.convert("RGB").save(output_path, "JPEG", quality=95)
        logger.info(f"サムネイルを生成しました: {output_path}")
        return output_path

    except Exception as e:
        logger.critical(f"サムネイル生成中に予期せぬエラーが発生しました: {e}", exc_info=True)
        return None

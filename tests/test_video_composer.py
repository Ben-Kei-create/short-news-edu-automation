import pytest
from unittest.mock import patch, MagicMock
import os

from modules.video_composer import compose_video

# settingsのモック
@pytest.fixture
def mock_settings():
    return {
        "video_composer": {
            "image_duration": 5.0,
            "bgm_volume": 0.08,
            "font_size": 60,
            "font_color": "white",
            "font_stroke_color": "black",
            "font_stroke_width": 2,
            "subtitle_width": 800,
            "subtitle_position_y_ratio": 0.8,
            "output_fps": 24
        }
    }

# compose_videoのテスト
@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.ColorClip')
@patch('moviepy.editor.CompositeVideoClip')
@patch('moviepy.editor.concatenate_videoclips')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.concatenate_audioclips')
@patch('moviepy.editor.CompositeAudioClip')
@patch('moviepy.video.tools.subtitles.SubtitlesClip')
@patch('moviepy.editor.TextClip')
@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('moviepy.editor.vfx.speedx')
@patch('moviepy.audio.fx.all.audio_loop')
@patch('builtins.open', new_callable=MagicMock) # 追加
def test_compose_video_success(
    mock_audio_loop, mock_speedx, mock_exists, mock_makedirs, mock_TextClip, mock_SubtitlesClip,
    mock_CompositeAudioClip, mock_concatenate_audioclips, mock_AudioFileClip,
    mock_concatenate_videoclips, mock_CompositeVideoClip, mock_ColorClip, mock_ImageClip,
    mock_settings
):
    """動画合成が成功した場合をテスト"""
    # モックの設定
    mock_image_clip_instance = MagicMock()
    mock_image_clip_instance.resize.return_value.set_position.return_value = MagicMock()
    mock_ImageClip.return_value = mock_image_clip_instance
    # ImageClip のコンストラクタが呼び出されたときに、ダミーの ImageClip オブジェクトを返すようにする
    mock_ImageClip.side_effect = lambda file_path: mock_image_clip_instance

    mock_color_clip_instance = MagicMock()
    mock_ColorClip.return_value = mock_color_clip_instance

    mock_composite_video_clip_instance = MagicMock()
    mock_composite_video_clip_instance.duration = 60.0
    mock_composite_video_clip_instance.set_audio.return_value = mock_composite_video_clip_instance
    mock_composite_video_clip_instance.write_videofile.return_value = None
    mock_CompositeVideoClip.return_value = mock_composite_video_clip_instance

    mock_audio_file_clip_instance = MagicMock()
    mock_audio_file_clip_instance.volumex.return_value = mock_audio_file_clip_instance
    mock_AudioFileClip.return_value = mock_audio_file_clip_instance

    mock_narration_clip_raw = MagicMock()
    mock_narration_clip_raw.duration = 60.0
    mock_concatenate_audioclips.return_value = mock_narration_clip_raw

    mock_narration_clip = MagicMock()
    mock_speedx.return_value = mock_narration_clip

    mock_final_audio = MagicMock()
    mock_CompositeAudioClip.return_value = mock_final_audio

    mock_subtitles_clip_instance = MagicMock()
    mock_subtitles_clip_instance.set_position.return_value = mock_subtitles_clip_instance
    mock_SubtitlesClip.return_value = mock_subtitles_clip_instance

    mock_TextClip.return_value = MagicMock()

    # テストデータの準備
    theme = "テストテーマ"
    images = ["image1.png", "image2.png"]
    audio_segments_info = [
        {"path": "audio1.mp3", "duration": 30.0, "text": ""},
        {"path": "audio2.mp3", "duration": 30.0, "text": ""}
    ]
    bgm_path = "bgm.mp3"
    subtitle_file = "subtitle.srt"
    font_filename = "font.ttf"
    image_duration = 5.0

    # 関数呼び出し
    video_file = compose_video(
        theme, images, audio_segments_info, bgm_path, subtitle_file, font_filename, image_duration, mock_settings
    )

    # アサーション
    assert video_file.endswith(".mp4")
    mock_makedirs.assert_called_once_with("output/videos", exist_ok=True)
    mock_ImageClip.assert_called_with("image1.png")
    mock_ImageClip.assert_called_with("image2.png")
    assert mock_image_clip_instance.set_duration.call_count == 2
    assert mock_image_clip_instance.resize.call_count == 2
    assert mock_image_clip_instance.resize.call_args_list[0].kwargs['width'] == 1080
    mock_ColorClip.assert_called_once_with(size=(1080, 1920), color=(0, 0, 0))
    assert mock_CompositeVideoClip.call_count == 2 # concatenate_videoclips と final_clip の合成
    mock_concatenate_videoclips.assert_called_once()
    mock_AudioFileClip.assert_called_with("audio1.mp3")
    mock_AudioFileClip.assert_called_with("audio2.mp3")
    mock_concatenate_audioclips.assert_called_once()
    mock_speedx.assert_called_once()
    mock_AudioFileClip.assert_called_with("bgm.mp3")
    mock_audio_loop.assert_called_once()
    mock_CompositeAudioClip.assert_called_once()
    mock_SubtitlesClip.assert_called_once_with(subtitle_file, MagicMock())
    mock_subtitles_clip_instance.set_position.assert_called_once_with(('center', 0.8))
    mock_composite_video_clip_instance.write_videofile.assert_called_once()

@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.ColorClip')
@patch('moviepy.editor.CompositeVideoClip')
@patch('moviepy.editor.concatenate_videoclips')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.concatenate_audioclips')
@patch('moviepy.editor.CompositeAudioClip')
@patch('moviepy.video.tools.subtitles.SubtitlesClip')
@patch('moviepy.editor.TextClip')
@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('moviepy.editor.vfx.speedx')
@patch('moviepy.audio.fx.all.audio_loop')
@patch('builtins.open', new_callable=MagicMock) # 追加
def test_compose_video_no_audio_segments(
    mock_open, mock_audio_loop, mock_speedx, mock_exists, mock_makedirs, mock_TextClip, mock_SubtitlesClip,
    mock_CompositeAudioClip, mock_concatenate_audioclips, mock_AudioFileClip,
    mock_concatenate_videoclips, mock_CompositeVideoClip, mock_ColorClip, mock_ImageClip,
    mock_settings
):
    """音声セグメントがない場合にNoneを返すことをテスト"""
    mock_image_clip_instance = MagicMock()
    mock_image_clip_instance.resize.return_value.set_position.return_value = MagicMock()
    mock_ImageClip.return_value = mock_image_clip_instance
    mock_ImageClip.side_effect = lambda file_path: mock_image_clip_instance # 追加

    mock_color_clip_instance = MagicMock()
    mock_ColorClip.return_value = mock_color_clip_instance

    mock_composite_video_clip_instance = MagicMock()
    mock_composite_video_clip_instance.duration = 60.0
    mock_composite_video_clip_instance.set_audio.return_value = mock_composite_video_clip_instance
    mock_composite_video_clip_instance.write_videofile.return_value = None
    mock_CompositeVideoClip.return_value = mock_composite_video_clip_instance

    mock_concatenate_videoclips.return_value = mock_composite_video_clip_instance

    video_file = compose_video("テーマ", ["image1.png"], [], "bgm.mp3", "subtitle.srt", "font.ttf", 5.0, mock_settings)
    assert video_file is None

@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.ColorClip')
@patch('moviepy.editor.CompositeVideoClip')
@patch('moviepy.editor.concatenate_videoclips')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.concatenate_audioclips')
@patch('moviepy.editor.CompositeAudioClip')
@patch('moviepy.video.tools.subtitles.SubtitlesClip')
@patch('moviepy.editor.TextClip')
@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('moviepy.editor.vfx.speedx')
@patch('moviepy.audio.fx.all.audio_loop')
@patch('builtins.open', new_callable=MagicMock) # 追加
def test_compose_video_no_subtitle_file(
    mock_open, mock_audio_loop, mock_speedx, mock_exists, mock_makedirs, mock_TextClip, mock_SubtitlesClip,
    mock_CompositeAudioClip, mock_concatenate_audioclips, mock_AudioFileClip,
    mock_concatenate_videoclips, mock_CompositeVideoClip, mock_ColorClip, mock_ImageClip,
    mock_settings
):
    """字幕ファイルがない場合に字幕なしで動画が合成されることをテスト"""
    # モックの設定 (test_compose_video_success と同様)
    mock_image_clip_instance = MagicMock()
    mock_image_clip_instance.resize.return_value.set_position.return_value = MagicMock()
    mock_ImageClip.return_value = mock_image_clip_instance
    mock_ImageClip.side_effect = lambda file_path: mock_image_clip_instance # 追加

    mock_color_clip_instance = MagicMock()
    mock_ColorClip.return_value = mock_color_clip_instance

    mock_composite_video_clip_instance = MagicMock()
    mock_composite_video_clip_instance.duration = 60.0
    mock_composite_video_clip_instance.set_audio.return_value = mock_composite_video_clip_instance
    mock_composite_video_clip_instance.write_videofile.return_value = None
    mock_CompositeVideoClip.return_value = mock_composite_video_clip_instance

    mock_audio_file_clip_instance = MagicMock()
    mock_audio_file_clip_instance.volumex.return_value = mock_audio_file_clip_instance
    mock_AudioFileClip.return_value = mock_audio_file_clip_instance

    mock_narration_clip_raw = MagicMock()
    mock_narration_clip_raw.duration = 60.0
    mock_concatenate_audioclips.return_value = mock_narration_clip_raw

    mock_narration_clip = MagicMock()
    mock_speedx.return_value = mock_narration_clip

    mock_final_audio = MagicMock()
    mock_CompositeAudioClip.return_value = mock_final_audio

    mock_TextClip.return_value = MagicMock()

    # テストデータの準備
    theme = "テストテーマ"
    images = ["image1.png"]
    audio_segments_info = [
        {"path": "audio1.mp3", "duration": 60.0, "text": ""}
    ]
    bgm_path = "bgm.mp3"
    subtitle_file = None # 字幕ファイルなし
    font_filename = "font.ttf"
    image_duration = 5.0

    # 関数呼び出し
    video_file = compose_video(
        theme, images, audio_segments_info, bgm_path, subtitle_file, font_filename, image_duration, mock_settings
    )

    # アサーション
    assert video_file.endswith(".mp4")
    mock_SubtitlesClip.assert_not_called() # 字幕が生成されないことを確認
    mock_composite_video_clip_instance.write_videofile.assert_called_once()

@patch('moviepy.editor.ImageClip')
@patch('moviepy.editor.ColorClip')
@patch('moviepy.editor.CompositeVideoClip')
@patch('moviepy.editor.concatenate_videoclips')
@patch('moviepy.editor.AudioFileClip')
@patch('moviepy.editor.concatenate_audioclips')
@patch('moviepy.editor.CompositeAudioClip')
@patch('moviepy.video.tools.subtitles.SubtitlesClip')
@patch('moviepy.editor.TextClip')
@patch('os.makedirs')
@patch('os.path.exists', return_value=True)
@patch('moviepy.editor.vfx.speedx')
@patch('moviepy.audio.fx.all.audio_loop')
@patch('builtins.open', new_callable=MagicMock) # 追加
def test_compose_video_font_fallback(
    mock_open, mock_audio_loop, mock_speedx, mock_exists, mock_makedirs, mock_TextClip, mock_SubtitlesClip,
    mock_CompositeAudioClip, mock_concatenate_audioclips, mock_AudioFileClip,
    mock_concatenate_videoclips, mock_CompositeVideoClip, mock_ColorClip, mock_ImageClip,
    mock_settings
):
    """フォントファイルが見つからない場合にフォールバックすることをテスト"""
    # モックの設定 (test_compose_video_success と同様)
    mock_image_clip_instance = MagicMock()
    mock_image_clip_instance.resize.return_value.set_position.return_value = MagicMock()
    mock_ImageClip.return_value = mock_image_clip_instance
    mock_ImageClip.side_effect = lambda file_path: mock_image_clip_instance # 追加

    mock_color_clip_instance = MagicMock()
    mock_ColorClip.return_value = mock_color_clip_instance

    mock_composite_video_clip_instance = MagicMock()
    mock_composite_video_clip_instance.duration = 60.0
    mock_composite_video_clip_instance.set_audio.return_value = mock_composite_video_clip_instance
    mock_composite_video_clip_instance.write_videofile.return_value = None
    mock_CompositeVideoClip.return_value = mock_composite_video_clip_instance

    mock_audio_file_clip_instance = MagicMock()
    mock_audio_file_clip_instance.volumex.return_value = mock_audio_file_clip_instance
    mock_AudioFileClip.return_value = mock_audio_file_clip_instance

    mock_narration_clip_raw = MagicMock()
    mock_narration_clip_raw.duration = 60.0
    mock_concatenate_audioclips.return_value = mock_narration_clip_raw

    mock_narration_clip = MagicMock()
    mock_speedx.return_value = mock_narration_clip

    mock_final_audio = MagicMock()
    mock_CompositeAudioClip.return_value = mock_final_audio

    mock_TextClip.return_value = MagicMock()

    # os.path.exists のモックを調整して、カスタムフォントが見つからないようにする
    mock_exists.side_effect = lambda path: path != os.path.join("input/fonts", "non_existent_font.ttf")

    # テストデータの準備
    theme = "テストテーマ"
    images = ["image1.png"]
    audio_segments_info = [
        {"path": "audio1.mp3", "duration": 60.0, "text": ""}
    ]
    bgm_path = "bgm.mp3"
    subtitle_file = "subtitle.srt"
    font_filename = "non_existent_font.ttf" # 存在しないフォントを指定
    image_duration = 5.0

    # 関数呼び出し
    video_file = compose_video(
        theme, images, audio_segments_info, bgm_path, subtitle_file, font_filename, image_duration, mock_settings
    )

    # アサーション
    assert video_file.endswith(".mp4")
    mock_SubtitlesClip.assert_not_called() # 字幕が生成されないことを確認
    mock_composite_video_clip_instance.write_videofile.assert_called_once()

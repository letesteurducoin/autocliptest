import sys
import os
import json
from datetime import datetime, date

sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

import get_top_clips
import download_clip
import generate_metadata
# import upload_youtube  # temporairement désactivé
from classify_clip_type import classify_clip_type
from process_video_gameplay import process_gameplay_clip
from process_video_chatting import process_chatting_clip

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PUBLISHED_HISTORY_FILE = os.path.join(DATA_DIR, 'published_shorts_history.json')
RAW_CLIP_PATH = os.path.join(DATA_DIR, 'temp_raw_clip.mp4')
PROCESSED_CLIP_PATH = os.path.join(DATA_DIR, 'temp_processed_short.mp4')

NUMBER_OF_CLIPS_TO_ATTEMPT_TO_PUBLISH = 3

def load_published_history():
    if not os.path.exists(PUBLISHED_HISTORY_FILE):
        return {}
    try:
        with open(PUBLISHED_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_published_history(history_data):
    with open(PUBLISHED_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)

def get_today_published_ids(history_data):
    today_str = date.today().isoformat()
    return [item["twitch_clip_id"] for item in history_data.get(today_str, [])]

def add_to_history(history_data, clip_id, youtube_id):
    today_str = date.today().isoformat()
    if today_str not in history_data:
        history_data[today_str] = []
    history_data[today_str].append({
        "twitch_clip_id": clip_id,
        "youtube_short_id": youtube_id,
        "timestamp": datetime.now().isoformat()
    })

def main():
    history = load_published_history()
    today_published_ids = get_today_published_ids(history)

    clips_attempted_in_this_run = []
    twitch_token = get_top_clips.get_twitch_access_token()
    if not twitch_token:
        return

    eligible_clips_list = get_top_clips.get_eligible_short_clips(
        access_token=twitch_token,
        num_clips_per_source=50,
        days_ago=1,
        already_published_clip_ids=today_published_ids
    )
    if not eligible_clips_list:
        return

    clips_published_count = 0
    for selected_clip in eligible_clips_list:
        if clips_published_count >= NUMBER_OF_CLIPS_TO_ATTEMPT_TO_PUBLISH:
            break

        if selected_clip['id'] in clips_attempted_in_this_run or selected_clip['id'] in today_published_ids:
            continue

        clips_attempted_in_this_run.append(selected_clip['id'])
        downloaded_file = download_clip.download_twitch_clip(selected_clip['url'], RAW_CLIP_PATH)
        if not downloaded_file:
            continue

        clip_type = classify_clip_type(selected_clip)
        print(f"📂 Type de clip détecté : {clip_type}")

        if clip_type == "chatting":
            processed_file_path_returned = process_chatting_clip(
                input_path=downloaded_file,
                output_path=PROCESSED_CLIP_PATH,
                max_duration_seconds=get_top_clips.MAX_VIDEO_DURATION_SECONDS,
                clip_data=selected_clip
            )
        else:
            processed_file_path_returned = process_gameplay_clip(
                input_path=downloaded_file,
                output_path=PROCESSED_CLIP_PATH,
                max_duration_seconds=get_top_clips.MAX_VIDEO_DURATION_SECONDS,
                clip_data=selected_clip
            )

        if not processed_file_path_returned:
            continue

        youtube_metadata = generate_metadata.generate_youtube_metadata(selected_clip)

        # youtube_service = upload_youtube.get_authenticated_service()
        # youtube_video_id = upload_youtube.upload_youtube_short(youtube_service, processed_file_path_returned, youtube_metadata)
        youtube_service = None
        youtube_video_id = f"TEST-{selected_clip['id']}"
        print("🚫 Upload YouTube désactivé pour les tests. Vidéo non publiée.")

        if youtube_video_id:
            add_to_history(history, selected_clip['id'], youtube_video_id)
            save_published_history(history)
            today_published_ids = get_today_published_ids(history)
            clips_published_count += 1

    print(f"\n🎉 {clips_published_count} Short(s) traité(s) avec succès.")

if __name__ == "__main__":
    main()
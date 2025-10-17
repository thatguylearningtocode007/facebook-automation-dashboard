```python
import os
import re
import uuid
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip
import yt_dlp
from tiktok_downloader import TikTokDownloader
from google.cloud import storage

# --- Configuration Loading ---
CONFIG_FILE = 'config.json'
PENDING_POSTS_FILE = 'pending_posts.json'

def load_config():
    """Loads configuration from config.json."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    # Default structure if file doesn't exist
    return {
        "FACEBOOK_ACCESS_TOKEN_PAGES": "",
        "FACEBOOK_ACCESS_TOKEN_GROUPS": "",
        "YOUTUBE_API_KEY": "",
        "YOUTUBE_CLIENT_SECRETS_FILE": "",
        "FACEBOOK_PAGES_TO_POST": [],
        "FACEBOOK_GROUPS_TO_POST": [],
        "YOUTUBE_CHANNELS_TO_POST": [],
        "GCS_BUCKET_NAME": os.environ.get("GCS_BUCKET_NAME", "your-gcs-bucket-name-here")
    }

def save_config(config_data):
    """Saves the configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

def load_pending_posts():
    """Loads pending posts from pending_posts.json."""
    if os.path.exists(PENDING_POSTS_FILE):
        with open(PENDING_POSTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_pending_posts(posts_data):
    """Saves pending posts to pending_posts.json."""
    with open(PENDING_POSTS_FILE, 'w') as f:
        json.dump(posts_data, f, indent=4)

config = load_config()

# --- Flask App and GCS Initialization ---
class AppConfig:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(AppConfig())
CORS(app)

# GCS Configuration
GCS_BUCKET_NAME = config.get("GCS_BUCKET_NAME")
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# --- Logging for Approvals ---
def log_pending_post(post_id, platform, group_id=None):
    """Logs a post that is pending approval."""
    pending_posts = load_pending_posts()
    scheduled_time = datetime.now()
    removal_time = scheduled_time + timedelta(days=3)
    
    pending_posts[post_id] = {
        "post_id": post_id,
        "platform": platform,
        "group_id": group_id,
        "scheduled_time": scheduled_time.isoformat(),
        "removal_time": removal_time.isoformat()
    }
    save_pending_posts(pending_posts)
    
    # Schedule the check for this post
    scheduler.add_job(
        id=f'check_approval_{post_id}',
        func=check_and_remove_unapproved_post,
        trigger='date',
        run_date=removal_time,
        args=[post_id]
    )
    print(f"Post {post_id} logged as pending. Approval check scheduled for {removal_time.isoformat()}.")

# --- GCS Helper Functions ---
def upload_to_gcs(file_path, destination_blob_name):
    """Uploads a file to the GCS bucket."""
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    print(f"File {file_path} uploaded to {destination_blob_name} in bucket {GCS_BUCKET_NAME}.")
    # Return a GCS URI for internal use
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"

def download_from_gcs(source_blob_name, destination_file_name):
    """Downloads a blob from the GCS bucket."""
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
    return destination_file_name

def delete_from_gcs(blob_name):
    """Deletes a blob from the GCS bucket."""
    try:
        blob = bucket.blob(blob_name)
        blob.delete()
        print(f"Blob {blob_name} deleted.")
    except Exception as e:
        print(f"Error deleting blob {blob_name}: {e}")

def get_gcs_public_url(blob_name):
    """Gets a public URL for a GCS blob."""
    blob = bucket.blob(blob_name)
    # Make the blob publicly viewable.
    blob.make_public()
    return blob.public_url

# --- API Posting Functions ---
def post_video_to_facebook_reels(page_id, video_url, caption):
    """Posts a video to a Facebook Page's Reels."""
    print(f"--- Posting to Facebook Reels for Page ID: {page_id} ---")
    api_url = f"https://graph.facebook.com/v18.0/{page_id}/video_reels"
    params = {
        'access_token': config.get('FACEBOOK_ACCESS_TOKEN_PAGES'),
        'video_url': video_url,
        'description': caption,
        'upload_phase': 'start'
    }
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        print(f"SUCCESS: Post to Facebook Reels for page {page_id} initiated.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post to Facebook Reels for page {page_id}: {e.response.text}")
        return False

def post_video_to_facebook_group(group_id, video_url, caption):
    """Posts a video to a Facebook Group."""
    print(f"--- Posting to Facebook Group: {group_id} ---")
    api_url = f"https://graph.facebook.com/{group_id}/videos"
    params = {
        'access_token': config.get('FACEBOOK_ACCESS_TOKEN_GROUPS'),
        'file_url': video_url,
        'description': caption
    }
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        post_id = response.json().get('id')
        print(f"SUCCESS: Video posted to Facebook Group {group_id}. Post ID: {post_id}")
        # Log this post for approval tracking
        log_pending_post(post_id, 'facebook_group', group_id)
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post to Facebook Group {group_id}: {e.response.text}")
        return False

def post_video_to_instagram_reels(video_url, caption):
    """Placeholder function to post a video to Instagram Reels."""
    instagram_user_id = os.environ.get("INSTAGRAM_USER_ID", "mock_ig_user_id")
    print(f"--- Posting to Instagram Reels for Account: {instagram_user_id} ---")
    print(f"Video URL: {video_url}")
    print(f"Caption: {caption}")
    print("SUCCESS: Mock post to Instagram Reels complete.")
    return True

def post_video_to_youtube_shorts(video_path, title, description):
    """Placeholder function to upload a video as a YouTube Short."""
    print(f"--- Posting to YouTube Shorts ---")
    print(f"Video Path: {video_path}")
    print(f"Title: {title}")
    print(f"Description: {description} #shorts")
    print("SUCCESS: Mock post to YouTube Shorts complete.")
    return True

def remove_facebook_post(post_id):
    """Deletes a post from Facebook (Group or Page)."""
    api_url = f"https://graph.facebook.com/{post_id}"
    params = {'access_token': config.get('FACEBOOK_ACCESS_TOKEN_GROUPS')}
    try:
        response = requests.delete(api_url, params=params)
        response.raise_for_status()
        print(f"SUCCESS: Post {post_id} removed from Facebook.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to remove post {post_id}: {e.response.text}")
        return False

# --- Video Processing & Scheduling Logic ---
def download_video(url, local_download_path):
    """Downloads a video from a URL, handling TikTok watermarks."""
    if re.search(r'tiktok\.com', url):
        print("TikTok URL detected. Using watermark removal downloader.")
        try:
            downloader = TikTokDownloader()
            video_path_with_ext = f"{local_download_path}.mp4"
            downloader.download(url, output_name=video_path_with_ext, watermark=False)
            print(f"TikTok video downloaded without watermark to: {video_path_with_ext}")
            return video_path_with_ext
        except Exception as e:
            print(f"TikTok download failed: {e}. Falling back to yt-dlp.")
    
    print("Using yt-dlp for download.")
    ydl_opts = {
        'outtmpl': local_download_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not filename.endswith('.mp4'):
            base, _ = os.path.splitext(filename)
            filename = f"{base}.mp4"
    return filename

def process_video(input_gcs_blob, logo_gcs_blob, overlay_text):
    """Applies overlays to a video stored in GCS."""
    local_video_path = os.path.join('/tmp', os.path.basename(input_gcs_blob))
    local_logo_path = os.path.join('/tmp', os.path.basename(logo_gcs_blob))
    local_output_filename = f"processed_{uuid.uuid4()}.mp4"
    local_output_path = os.path.join('/tmp', local_output_filename)
    processed_gcs_blob_name = None

    try:
        download_from_gcs(input_gcs_blob, local_video_path)
        download_from_gcs(logo_gcs_blob, local_logo_path)

        video_clip = VideoFileClip(local_video_path)
        w, h = video_clip.size
        logo = (ImageClip(local_logo_path)
                .set_duration(video_clip.duration)
                .resize(height=int(h * 0.1))
                .margin(right=10, top=10, opacity=0)
                .set_pos(("right", "top")))
        text_clip = (TextClip(overlay_text, fontsize=40, color='white', font='Arial-Bold',
                              stroke_color='black', stroke_width=2)
                     .set_position('center')
                     .set_duration(video_clip.duration))
        final_clip = CompositeVideoClip([video_clip, logo, text_clip])
        final_clip.write_videofile(local_output_path, codec="libx264", audio_codec="aac")
        video_clip.close()
        final_clip.close()

        processed_gcs_blob_name = f"processed/{local_output_filename}"
        upload_to_gcs(local_output_path, processed_gcs_blob_name)
    finally:
        for path in [local_video_path, local_logo_path, local_output_path]:
            if os.path.exists(path): os.remove(path)
    return processed_gcs_blob_name

def check_and_remove_unapproved_post(post_id):
    """Scheduled job to check if a post was approved and remove it if not."""
    with app.app_context():
        print(f"Checking approval status for post_id: {post_id}")
        pending_posts = load_pending_posts()
        post_info = pending_posts.get(post_id)

        if not post_info:
            print(f"Post {post_id} not found in pending list. Already approved or removed.")
            return

        api_url = f"https://graph.facebook.com/{post_id}"
        params = {
            'fields': 'is_published',
            'access_token': config.get('FACEBOOK_ACCESS_TOKEN_GROUPS')
        }
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            is_published = response.json().get('is_published', False)

            if not is_published:
                print(f"Post {post_id} was not approved. Removing post and group.")
                remove_facebook_post(post_id)
                group_id_to_remove = post_info.get('group_id')
                if group_id_to_remove and group_id_to_remove in config['FACEBOOK_GROUPS_TO_POST']:
                    config['FACEBOOK_GROUPS_TO_POST'].remove(group_id_to_remove)
                    save_config(config)
                    print(f"Removed group {group_id_to_remove} from posting list.")
            else:
                print(f"Post {post_id} was approved.")
            
            # Clean up from pending list
            del pending_posts[post_id]
            save_pending_posts(pending_posts)

        except requests.exceptions.RequestException as e:
            # If the post doesn't exist (404), it might have been deleted by user. Treat as "not approved".
            if e.response and e.response.status_code == 404:
                 print(f"Post {post_id} not found on Facebook. Assuming not approved, removing group.")
                 group_id_to_remove = post_info.get('group_id')
                 if group_id_to_remove and group_id_to_remove in config['FACEBOOK_GROUPS_TO_POST']:
                    config['FACEBOOK_GROUPS_TO_POST'].remove(group_id_to_remove)
                    save_config(config)
                    print(f"Removed group {group_id_to_remove} from posting list.")
                 del pending_posts[post_id]
                 save_pending_posts(pending_posts)
            else:
                print(f"Error checking post status for {post_id}: {e}")

def scheduled_post_task(video_url, logo_gcs_blob, overlay_text, caption, platforms):
    """The complete task that downloads, processes, and posts a video."""
    with app.app_context():
        print(f"Executing scheduled task for URL: {video_url} on platforms: {platforms}")
        raw_video_gcs_blob = None
        processed_video_gcs_blob = None
        local_processed_video_path = None

        try:
            # Download and upload raw video
            local_raw_filename = os.path.join('/tmp', f"raw_{uuid.uuid4()}")
            local_downloaded_path = download_video(video_url, local_raw_filename)
            raw_video_gcs_blob_name = f"raw/{os.path.basename(local_downloaded_path)}"
            upload_to_gcs(local_downloaded_path, raw_video_gcs_blob_name)
            os.remove(local_downloaded_path)

            # Process video
            processed_video_gcs_blob_name = process_video(raw_video_gcs_blob_name, logo_gcs_blob, overlay_text)
            print(f"Video processed and saved to GCS: {processed_video_gcs_blob_name}")
            
            # Get a public URL for posting APIs
            public_video_url = get_gcs_public_url(processed_video_gcs_blob_name)
            print(f"Public URL for posting: {public_video_url}")

            # Post to selected platforms
            if "facebook_page" in platforms:
                for page_id in config.get('FACEBOOK_PAGES_TO_POST', []):
                    post_video_to_facebook_reels(page_id, public_video_url, caption)
            
            if "facebook_group" in platforms:
                for group_id in config.get('FACEBOOK_GROUPS_TO_POST', []):
                    post_video_to_facebook_group(group_id, public_video_url, caption)
            
            if "instagram" in platforms:
                post_video_to_instagram_reels(public_video_url, caption)
            
            if "youtube" in platforms:
                # YouTube API requires local file path, so we need to download the processed video
                local_processed_video_path = os.path.join('/tmp', os.path.basename(processed_video_gcs_blob_name))
                download_from_gcs(processed_video_gcs_blob_name, local_processed_video_path)
                youtube_title = caption[:100]
                for channel_id in config.get('YOUTUBE_CHANNELS_TO_POST', []):
                    print(f"Posting to YouTube Channel: {channel_id}") # Placeholder for channel selection
                    post_video_to_youtube_shorts(local_processed_video_path, youtube_title, caption)

        except Exception as e:
            print(f"An error occurred during the scheduled task: {e}")
        finally:
            print("Cleaning up temporary files and GCS blobs...")
            if local_processed_video_path and os.path.exists(local_processed_video_path):
                os.remove(local_processed_video_path)
            if raw_video_gcs_blob_name: delete_from_gcs(raw_video_gcs_blob_name)
            if processed_video_gcs_blob_name: delete_from_gcs(processed_video_gcs_blob_name)
            if logo_gcs_blob: delete_from_gcs(logo_gcs_blob)
            print("Cleanup complete.")

# --- API Endpoints ---
@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """Endpoint to get or update the configuration."""
    global config
    if request.method == 'POST':
        data = request.json
        # Selectively update to avoid overwriting with missing keys
        for key, value in data.items():
            if key in config:
                config[key] = value
        save_config(config)
        return jsonify({"message": "Configuration updated successfully."}), 200
    else: # GET
        return jsonify(config), 200

@app.route('/api/config/remove-group', methods=['POST'])
def remove_group_from_config():
    """Endpoint to remove a specific Facebook group from the posting list."""
    data = request.json
    group_id_to_remove = data.get('group_id')
    if not group_id_to_remove:
        return jsonify({"error": "Missing 'group_id' in request body."}), 400
    
    if group_id_to_remove in config['FACEBOOK_GROUPS_TO_POST']:
        config['FACEBOOK_GROUPS_TO_POST'].remove(group_id_to_remove)
        save_config(config)
        return jsonify({"message": f"Group {group_id_to_remove} removed successfully."}), 200
    else:
        return jsonify({"error": f"Group {group_id_to_remove} not found in the list."}), 404

@app.route('/api/logs/pending', methods=['GET'])
def get_pending_logs():
    """Endpoint to view the live log of pending posts."""
    return jsonify(load_pending_posts()), 200

@app.route('/api/schedule-post', methods=['POST'])
def schedule_post():
    """Schedules a video to be downloaded, processed, and posted."""
    if 'videoUrl' not in request.form or 'platforms' not in request.form:
        return jsonify({"error": "Missing 'videoUrl' or 'platforms'"}), 400

    video_url = request.form['videoUrl']
    overlay_text = request.form.get('overlayText', 'Default Text')
    caption = request.form.get('caption', 'Check out this cool video!')
    schedule_str = request.form.get('scheduleDateTime')
    platforms = [p.strip().lower() for p in request.form.get('platforms').split(',')]
    
    valid_platforms = {'facebook_page', 'facebook_group', 'instagram', 'youtube'}
    if not all(p in valid_platforms for p in platforms):
        return jsonify({"error": f"Invalid platform. Use: {', '.join(valid_platforms)}"}), 400

    logo_gcs_blob_name = None
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file.filename != '':
            ext = os.path.splitext(logo_file.filename)[1]
            local_logo_filename = f"logo_{uuid.uuid4()}{ext}"
            local_logo_path = os.path.join('/tmp', local_logo_filename)
            logo_file.save(local_logo_path)
            
            logo_gcs_blob_name = f"logos/{local_logo_filename}"
            upload_to_gcs(local_logo_path, logo_gcs_blob_name)
            os.remove(local_logo_path)

    if not logo_gcs_blob_name:
        return jsonify({"error": "Logo file is required"}), 400

    try:
        schedule_time = datetime.fromisoformat(schedule_str) if schedule_str else datetime.now()
        scheduler.add_job(
            id=f'post_{uuid.uuid4()}',
            func=scheduled_post_task,
            trigger='date',
            run_date=schedule_time,
            args=[video_url, logo_gcs_blob_name, overlay_text, caption, platforms]
        )
        return jsonify({
            "message": "Video post scheduled successfully!",
            "scheduled_time": schedule_time.isoformat(),
            "platforms": platforms
        }), 202
    except Exception as e:
        print(f"Error scheduling post: {e}")
        if logo_gcs_blob_name:
            delete_from_gcs(logo_gcs_blob_name)
        return jsonify({"error": f"Failed to schedule post: {str(e)}"}), 500

if __name__ == '__main__':
    if not GCS_BUCKET_NAME or GCS_BUCKET_NAME == "your-gcs-bucket-name-here":
        print("ERROR: GCS_BUCKET_NAME is not set in config.json or environment variable.")
    else:
        app.run(host='0.0.0.0', port=8080)
```
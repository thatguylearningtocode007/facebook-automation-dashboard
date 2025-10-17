```python
import os
import re
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip
import yt_dlp
from tiktok_downloader import TikTokDownloader
from google.cloud import storage

# --- Configuration ---
class Config:
    SCHEDULER_API_ENABLED = True

# GCS Configuration
# It's recommended to set this via environment variables.
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "your-gcs-bucket-name-here")
# For authentication, the Google Cloud client library will automatically use
# credentials if the GOOGLE_APPLICATION_CREDENTIALS environment variable is set.
# Example: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

app = Flask(__name__)
app.config.from_object(Config())
CORS(app) # Enable Cross-Origin Resource Sharing

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# --- GCS Helper Functions ---

def upload_to_gcs(file_path, destination_blob_name):
    """Uploads a file to the GCS bucket."""
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    print(f"File {file_path} uploaded to {destination_blob_name} in bucket {GCS_BUCKET_NAME}.")
    return blob.public_url

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

# --- Placeholder API Authentication and Posting Functions ---
# Note: Real implementation requires OAuth 2.0 flows and specific API client libraries.
# Credentials should be securely stored (e.g., environment variables, secret manager).

def post_video_to_facebook_reels(page_id, video_path, caption):
    """
    Placeholder function to post a video to Facebook Reels.
    The actual implementation requires the Facebook Graph API.
    """
    print(f"--- Posting to Facebook Reels ---")
    print(f"Page ID: {page_id}")
    print(f"Video Path: {video_path}")
    print(f"Caption: {caption}")
    print(f"SUCCESS: Mock post to Facebook Reels for page {page_id} complete.")
    # Real implementation would involve multipart/form-data POST request to
    # https://graph.facebook.com/v18.0/{page_id}/video_reels
    return True

def post_video_to_instagram_reels(video_path, caption):
    """
    Placeholder function to post a video to Instagram Reels.
    The actual implementation requires the Instagram Graph API.
    """
    # In a real scenario, you'd get the IG User ID from an auth token.
    instagram_user_id = os.environ.get("INSTAGRAM_USER_ID", "mock_ig_user_id")
    print(f"--- Posting to Instagram Reels ---")
    print(f"Instagram Account: {instagram_user_id}")
    print(f"Video Path: {video_path}")
    print(f"Caption: {caption}")
    print(f"SUCCESS: Mock post to Instagram Reels for account {instagram_user_id} complete.")
    # Real implementation is a multi-step process:
    # 1. POST to `/{ig-user-id}/media` to create a container.
    # 2. POST video file to the URL from step 1.
    # 3. POST to `/{ig-user-id}/media_publish` with the container ID to publish.
    return True

def post_video_to_youtube_shorts(video_path, title, description):
    """
    Placeholder function to upload a video as a YouTube Short.
    The actual implementation requires the YouTube Data API v3.
    """
    print(f"--- Posting to YouTube Shorts ---")
    print(f"Video Path: {video_path}")
    print(f"Title: {title}")
    print(f"Description: {description} #shorts")
    print(f"SUCCESS: Mock post to YouTube Shorts complete.")
    # Real implementation uses google_auth_oauthlib and googleapiclient
    # to upload to the `videos.insert` endpoint. The video must be < 60s
    # and have a vertical aspect ratio. Adding '#shorts' to the title or
    # description is recommended.
    return True

# --- Video Processing Logic (Adapted for GCS) ---

def download_video(url, local_download_path):
    """
    Downloads a video from a URL to a local temporary path.
    Uses a watermark removal library for TikTok URLs.
    Uses yt-dlp for all other URLs.
    Returns the path to the locally downloaded file.
    """
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
            pass

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
    """
    Downloads video and logo from GCS, applies overlays, and uploads the result back to GCS.
    """
    local_video_path = os.path.join('/tmp', os.path.basename(input_gcs_blob))
    local_logo_path = os.path.join('/tmp', os.path.basename(logo_gcs_blob))
    local_output_filename = f"processed_{uuid.uuid4()}.mp4"
    local_output_path = os.path.join('/tmp', local_output_filename)

    processed_gcs_blob = None
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

        processed_gcs_blob = f"processed/{local_output_filename}"
        upload_to_gcs(local_output_path, processed_gcs_blob)

    finally:
        if os.path.exists(local_video_path): os.remove(local_video_path)
        if os.path.exists(local_logo_path): os.remove(local_logo_path)
        if os.path.exists(local_output_path): os.remove(local_output_path)

    return processed_gcs_blob

# --- Scheduled Task ---

def scheduled_post_task(video_url, logo_gcs_blob, overlay_text, caption, platforms):
    """
    The complete task that downloads, processes, and posts a video to selected platforms.
    """
    with app.app_context():
        print(f"Executing scheduled task for URL: {video_url} on platforms: {platforms}")
        raw_video_gcs_blob = None
        processed_video_gcs_blob = None
        local_processed_video_path = None

        try:
            local_raw_filename = os.path.join('/tmp', f"raw_{uuid.uuid4()}")
            local_downloaded_path = download_video(video_url, local_raw_filename)
            
            raw_video_gcs_blob = f"raw/{os.path.basename(local_downloaded_path)}"
            upload_to_gcs(local_downloaded_path, raw_video_gcs_blob)
            
            if os.path.exists(local_downloaded_path):
                os.remove(local_downloaded_path)

            processed_video_gcs_blob = process_video(raw_video_gcs_blob, logo_gcs_blob, overlay_text)
            print(f"Video processed and saved to GCS: {processed_video_gcs_blob}")

            local_processed_video_path = os.path.join('/tmp', os.path.basename(processed_video_gcs_blob))
            download_from_gcs(processed_video_gcs_blob, local_processed_video_path)

            # Post to selected platforms
            if "facebook" in platforms:
                # In a real app, you'd iterate over selected page IDs
                mock_page_id = os.environ.get("FACEBOOK_PAGE_ID", "mock_fb_page_id")
                post_video_to_facebook_reels(mock_page_id, local_processed_video_path, caption)
            
            if "instagram" in platforms:
                post_video_to_instagram_reels(local_processed_video_path, caption)
            
            if "youtube" in platforms:
                # YouTube title has a 100 char limit, description is longer.
                youtube_title = caption[:100]
                post_video_to_youtube_shorts(local_processed_video_path, youtube_title, caption)

        except Exception as e:
            print(f"An error occurred during the scheduled task: {e}")
        finally:
            print("Cleaning up temporary files...")
            if local_processed_video_path and os.path.exists(local_processed_video_path):
                os.remove(local_processed_video_path)
            
            if raw_video_gcs_blob: delete_from_gcs(raw_video_gcs_blob)
            if processed_video_gcs_blob: delete_from_gcs(processed_video_gcs_blob)
            if logo_gcs_blob: delete_from_gcs(logo_gcs_blob)
            print("Cleanup complete.")

# --- API Endpoints ---

@app.route('/api/schedule-post', methods=['POST'])
def schedule_post():
    """Schedules a video to be downloaded, processed, and posted."""
    if 'videoUrl' not in request.form:
        return jsonify({"error": "Missing videoUrl"}), 400
    if 'platforms' not in request.form:
        return jsonify({"error": "Missing platforms list (e.g., 'facebook,instagram')"}), 400

    video_url = request.form['videoUrl']
    overlay_text = request.form.get('overlayText', 'Default Text')
    caption = request.form.get('caption', 'Check out this cool video!')
    schedule_str = request.form.get('scheduleDateTime')
    platforms = [p.strip().lower() for p in request.form.get('platforms').split(',')]
    
    # Validate platforms
    valid_platforms = {'facebook', 'instagram', 'youtube'}
    if not all(p in valid_platforms for p in platforms):
        return jsonify({"error": f"Invalid platform detected. Use a comma-separated list of: {', '.join(valid_platforms)}"}), 400

    logo_gcs_blob = None
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file.filename != '':
            filename_base = f"logo_{uuid.uuid4()}"
            ext = os.path.splitext(logo_file.filename)[1]
            local_logo_filename = f"{filename_base}{ext}"
            local_logo_path = os.path.join('/tmp', local_logo_filename)
            logo_file.save(local_logo_path)
            
            logo_gcs_blob = f"logos/{local_logo_filename}"
            upload_to_gcs(local_logo_path, logo_gcs_blob)
            
            if os.path.exists(local_logo_path): os.remove(local_logo_path)

    if not logo_gcs_blob:
        return jsonify({"error": "Logo file is required"}), 400

    try:
        schedule_time = datetime.fromisoformat(schedule_str) if schedule_str else datetime.now()
        
        scheduler.add_job(
            id=f'post_{uuid.uuid4()}',
            func=scheduled_post_task,
            trigger='date',
            run_date=schedule_time,
            args=[video_url, logo_gcs_blob, overlay_text, caption, platforms]
        )
        
        return jsonify({
            "message": "Video post scheduled successfully!",
            "scheduled_time": schedule_time.isoformat(),
            "platforms": platforms
        }), 202

    except Exception as e:
        print(f"Error scheduling post: {e}")
        if logo_gcs_blob:
            delete_from_gcs(logo_gcs_blob)
        return jsonify({"error": f"Failed to schedule post: {str(e)}"}), 500

if __name__ == '__main__':
    if GCS_BUCKET_NAME == "your-gcs-bucket-name-here":
        print("ERROR: GCS_BUCKET_NAME is not set. Please set the environment variable.")
    else:
        # For platforms like Replit, use 0.0.0.0 to be accessible.
        app.run(host='0.0.0.0', port=8080)
```
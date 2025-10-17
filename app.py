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

# --- Placeholder API Authentication and Functions ---

def get_facebook_pages_from_api():
    """
    Placeholder function to fetch user's managed Facebook pages.
    """
    print("Fetching Facebook pages from API...")
    mock_pages = [
        {"id": "123456789012345", "name": "My First Awesome Page"},
        {"id": "987654321098765", "name": "My Second Business Page"},
        {"id": "555555555555555", "name": "Test Page for Videos"}
    ]
    return mock_pages

def post_video_to_facebook_page(page_id, video_path, caption):
    """
    Placeholder function to post a video to a specific Facebook Page.
    """
    print(f"--- Posting to Facebook Page ---")
    print(f"Page ID: {page_id}")
    print(f"Video Path: {video_path}")
    print(f"Caption: {caption}")
    print(f"SUCCESS: Mock post to Facebook page {page_id} complete.")
    return True

def post_video_to_youtube(video_path, title, description):
    """
    Placeholder function to upload a video to YouTube.
    """
    print(f"--- Posting to YouTube ---")
    print(f"Video Path: {video_path}")
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"SUCCESS: Mock post to YouTube complete.")
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
    # Define local temporary paths
    local_video_path = os.path.join('/tmp', os.path.basename(input_gcs_blob))
    local_logo_path = os.path.join('/tmp', os.path.basename(logo_gcs_blob))
    local_output_filename = f"processed_{uuid.uuid4()}.mp4"
    local_output_path = os.path.join('/tmp', local_output_filename)

    processed_gcs_blob = None
    try:
        # Download files from GCS
        download_from_gcs(input_gcs_blob, local_video_path)
        download_from_gcs(logo_gcs_blob, local_logo_path)

        # Perform video editing
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

        # Upload processed video to GCS
        processed_gcs_blob = f"processed/{local_output_filename}"
        upload_to_gcs(local_output_path, processed_gcs_blob)

    finally:
        # Clean up local temporary files
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        if os.path.exists(local_logo_path):
            os.remove(local_logo_path)
        if os.path.exists(local_output_path):
            os.remove(local_output_path)

    return processed_gcs_blob

# --- Scheduled Task ---

def scheduled_post_task(video_url, logo_gcs_blob, overlay_text, page_ids, caption):
    """
    The complete task that will be executed by the scheduler using GCS.
    """
    with app.app_context():
        print(f"Executing scheduled task for URL: {video_url}")
        raw_video_gcs_blob = None
        processed_video_gcs_blob = None
        local_processed_video_path = None

        try:
            # 1. Download video to a local temp file first
            local_raw_filename = os.path.join('/tmp', f"raw_{uuid.uuid4()}")
            local_downloaded_path = download_video(video_url, local_raw_filename)
            
            # 2. Upload raw video to GCS
            raw_video_gcs_blob = f"raw/{os.path.basename(local_downloaded_path)}"
            upload_to_gcs(local_downloaded_path, raw_video_gcs_blob)
            print(f"Raw video uploaded to GCS: {raw_video_gcs_blob}")
            
            # Clean up local raw video
            if os.path.exists(local_downloaded_path):
                os.remove(local_downloaded_path)

            # 3. Process video (downloads from GCS, processes, uploads back to GCS)
            processed_video_gcs_blob = process_video(raw_video_gcs_blob, logo_gcs_blob, overlay_text)
            print(f"Video processed and saved to GCS: {processed_video_gcs_blob}")

            # 4. Download the final processed video for posting
            local_processed_video_path = os.path.join('/tmp', os.path.basename(processed_video_gcs_blob))
            download_from_gcs(processed_video_gcs_blob, local_processed_video_path)

            # 5. Post to Facebook Pages
            for page_id in page_ids:
                post_video_to_facebook_page(page_id, local_processed_video_path, caption)

            # 6. Post to YouTube
            post_video_to_youtube(local_processed_video_path, caption, caption)

        except Exception as e:
            print(f"An error occurred during the scheduled task: {e}")
        finally:
            # 7. Cleanup local and GCS files
            print("Cleaning up temporary files...")
            if local_processed_video_path and os.path.exists(local_processed_video_path):
                os.remove(local_processed_video_path)
            
            if raw_video_gcs_blob:
                delete_from_gcs(raw_video_gcs_blob)
            if processed_video_gcs_blob:
                delete_from_gcs(processed_video_gcs_blob)
            if logo_gcs_blob:
                delete_from_gcs(logo_gcs_blob)
            print("Cleanup complete.")

# --- API Endpoints ---

@app.route('/api/facebook-pages', methods=['GET'])
def get_facebook_pages():
    """Endpoint to fetch the list of Facebook pages managed by the user."""
    try:
        pages = get_facebook_pages_from_api()
        return jsonify(pages)
    except Exception as e:
        print(f"Error fetching Facebook pages: {e}")
        return jsonify({"error": "Failed to fetch Facebook pages"}), 500

@app.route('/api/schedule-post', methods=['POST'])
def schedule_post():
    """Schedules a video to be downloaded, processed, and posted using GCS."""
    if 'videoUrl' not in request.form:
        return jsonify({"error": "Missing videoUrl"}), 400
    if 'page_ids' not in request.form:
        return jsonify({"error": "Missing page_ids"}), 400

    video_url = request.form['videoUrl']
    overlay_text = request.form.get('overlayText', 'Default Text')
    caption = request.form.get('caption', 'Check out this cool video!')
    schedule_str = request.form.get('scheduleDateTime')
    page_ids = request.form.get('page_ids').split(',')

    logo_gcs_blob = None
    local_logo_path = None
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file.filename != '':
            # Save logo locally first
            filename_base = f"logo_{uuid.uuid4()}"
            ext = os.path.splitext(logo_file.filename)[1]
            local_logo_filename = f"{filename_base}{ext}"
            local_logo_path = os.path.join('/tmp', local_logo_filename)
            logo_file.save(local_logo_path)
            
            # Upload logo to GCS
            logo_gcs_blob = f"logos/{local_logo_filename}"
            upload_to_gcs(local_logo_path, logo_gcs_blob)
            
            # Clean up local logo file immediately after upload
            if os.path.exists(local_logo_path):
                os.remove(local_logo_path)

    if not logo_gcs_blob:
        return jsonify({"error": "Logo file is required"}), 400

    try:
        schedule_time = datetime.fromisoformat(schedule_str)
        
        scheduler.add_job(
            id=f'post_{uuid.uuid4()}',
            func=scheduled_post_task,
            trigger='date',
            run_date=schedule_time,
            args=[video_url, logo_gcs_blob, overlay_text, page_ids, caption]
        )
        
        return jsonify({
            "message": "Video post scheduled successfully!",
            "scheduled_time": schedule_time.isoformat(),
            "post_to_pages": page_ids
        }), 202

    except Exception as e:
        print(f"Error scheduling post: {e}")
        # If scheduling fails, delete the uploaded logo from GCS
        if logo_gcs_blob:
            delete_from_gcs(logo_gcs_blob)
        return jsonify({"error": f"Failed to schedule post: {str(e)}"}), 500

if __name__ == '__main__':
    # Ensure the GCS bucket name is configured
    if GCS_BUCKET_NAME == "your-gcs-bucket-name-here":
        print("ERROR: GCS_BUCKET_NAME is not set. Please set the environment variable.")
    else:
        app.run(debug=True, port=5001)
```
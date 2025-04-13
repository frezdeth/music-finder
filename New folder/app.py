from flask import Flask, render_template, request
import yt_dlp
import os
import re
import shutil
import glob

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
TEMP_DIR = "temp_downloads"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    artist = request.form['artist']
    search_query = f"{artist}"
    search_string = f"ytsearch10:{search_query}"

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Step 1: Get video URLs from search
    ydl_opts_extract = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
    }

    video_urls = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts_extract) as ydl:
            result = ydl.extract_info(search_string, download=False)
            if 'entries' in result:
                for entry in result['entries']:
                    video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
            else:
                video_urls.append(f"https://www.youtube.com/watch?v={result['id']}")
    except Exception as e:
        return f"❌ Failed to extract video list: {str(e)}"

    # Step 2: Download all videos from extracted URLs
    download_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': os.path.join(TEMP_DIR, '%(title).50s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'restrictfilenames': True,
        'overwrites': True,
        'nooverwrites': False,
        'noutm': True,
    }

    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            ydl.download(video_urls)
    except Exception as e:
        return f"❌ Error while downloading songs: {str(e)}"

    # Step 3: Move MP3 files to final folder
    mp3_files = glob.glob(os.path.join(TEMP_DIR, '*.mp3'))
    moved_files = []

    for mp3_path in mp3_files:
        filename = os.path.basename(mp3_path)
        dest_path = os.path.join(DOWNLOAD_DIR, filename)
        try:
            shutil.move(mp3_path, dest_path)
            moved_files.append(filename)
        except Exception as move_err:
            print(f"⚠️ Failed to move {filename}: {move_err}")

    return f"✅ Downloaded and moved {len(moved_files)} songs for {artist}!"

if __name__ == '__main__':
    app.run(debug=True)

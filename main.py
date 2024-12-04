import pyktok as pyk
from moviepy import VideoFileClip  # Simplified import from moviepy
import os
import shutil

def download_tiktok_video(video_url, download_dir):
    try:
        # Initialize Pyktok with the specified browser
        pyk.specify_browser('firefox')
       
        # Download the video (without download_dir argument)
        pyk.save_tiktok(video_url, save_video=True)
        print("Video downloaded successfully")

        # Move the downloaded video to the desired directory
        video_file = [f for f in os.listdir() if f.endswith('.mp4')][0]
        video_path = os.path.join(download_dir, video_file)

        # Move video file to the target directory
        shutil.move(video_file, video_path)
        print(f"Video moved to {video_path}")
        
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def convert_to_audio(download_dir):
    try:
        # Check if video exists in the specified directory
        video_files = [f for f in os.listdir(download_dir) if f.endswith('.mp4')]
        if not video_files:
            print("No video found in the specified directory")
            return False
        
        # Use the first video file found
        full_video_path = os.path.join(download_dir, video_files[0])
        
        # Load the video
        video = VideoFileClip(full_video_path)
        
        # Extract audio
        audio_path = os.path.join(download_dir, 'audio.mp3')
        # The extraction remains the same
        video.audio.write_audiofile(audio_path)
        
        # Close the video to free up resources
        video.close()
        
        print(f"Audio extracted to {audio_path}")
        return True
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return False

if __name__ == "__main__":
    # Set your download directory (absolute path)
    download_dir = r"C:\Users\Solomon\Python Projects\tiktok_downloader"
    
    # Replace with the TikTok video URL you want to download
    tiktok_url = "https://www.tiktok.com/@diego.php/video/7387213306492112133"
   
    # Ensure the download directory exists
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Download the video
    if download_tiktok_video(tiktok_url, download_dir):
        # Convert to audio
        if convert_to_audio(download_dir):
            print("Audio conversion completed successfully.")
        else:
            print("Failed to convert video to audio.")

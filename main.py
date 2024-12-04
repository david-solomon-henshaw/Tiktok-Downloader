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
        
        return video_path  # Return the path of the downloaded video for audio conversion
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def convert_to_audio(download_dir, video_path):
    try:
        # Extract the video file name without extension
        video_filename = os.path.basename(video_path)
        video_name_without_ext = os.path.splitext(video_filename)[0]

        # Load the video
        video = VideoFileClip(video_path)
        
        # Create a unique audio path with the video name
        audio_path = os.path.join(download_dir, f"{video_name_without_ext}.mp3")
        
        # Extract audio
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
    
    # Ask the user to input a TikTok URL
    tiktok_url = input("Please enter the TikTok video URL: ").strip()
   
    # Ensure the download directory exists
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Download the video and get its path
    video_path = download_tiktok_video(tiktok_url, download_dir)
    
    if video_path:
        # Convert to audio using the video file name as the audio name
        if convert_to_audio(download_dir, video_path):
            print("Audio conversion completed successfully.")
        else:
            print("Failed to convert video to audio.")

import os
import shutil
import pyktok as pyk
from moviepy import VideoFileClip
import cloudinary
import cloudinary.uploader
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import tempfile
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask_cors import CORS
import cv2

print(cv2.__version__)
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

CORS(app)  # Allow CORS for all routes
# Initialize Firebase Admin SDK with environment variables
cred = credentials.Certificate({
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),  # Replace escape sequence for new lines
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
})
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# Function to extract frame and upload it
def extract_and_upload_frame(video_path, temp_dir):
    try:
        # Open the video file
        video = cv2.VideoCapture(video_path)
        
        # Read the first frame (first few seconds)
        success, frame = video.read()
        
        if not success:
            print("Could not extract frame from video")
            return None
        
        # Generate a unique filename for the frame
        frame_filename = os.path.join(temp_dir, f"video_frame_{os.path.basename(video_path)}.jpg")
        
        # Save the frame as an image
        cv2.imwrite(frame_filename, frame)
        
        # Upload the frame to Cloudinary
        frame_upload_result = cloudinary.uploader.upload(frame_filename, resource_type="image")
        frame_url = frame_upload_result['secure_url']
        
        # Close the video capture
        video.release()
        
        return frame_url
    except Exception as e:
        print(f"Error extracting and uploading frame: {e}")
        return None

# Function to upload audio to Cloudinary
def upload_audio_to_cloudinary(audio_path):
    try:
        # Upload the audio to Cloudinary (auto-detect file type)
        upload_result = cloudinary.uploader.upload(audio_path, resource_type="auto")
        audio_url = upload_result['secure_url']
        return audio_url
    except Exception as e:
        print(f"Error uploading audio: {e}")
        return None

def download_and_convert_to_audio(video_url):
    try:
        # Create a temporary directory in the current project
        temp_dir = 'temp_downloads'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Initialize Pyktok with the specified browser
       # pyk.specify_browser('firefox')
        
        # Download the TikTok video
        pyk.save_tiktok(video_url, save_video=True)
        print("Video downloaded successfully")
        
        # Find the downloaded video file in the current directory
        video_files = [f for f in os.listdir() if f.endswith('.mp4')]
        
        if not video_files:
            raise ValueError("No video file found after download")
        
        video_file = video_files[0]
        video_path = os.path.join(temp_dir, video_file)
        
        # Move the video to the temp directory
        shutil.move(video_file, video_path)
        
        # Load the video with moviepy
        video = VideoFileClip(video_path)
        
        # Create the audio file path
        audio_path = os.path.join(temp_dir, f"{os.path.splitext(video_file)[0]}.mp3")
        
        # Extract audio and save it as an MP3 file
        video.audio.write_audiofile(audio_path)
        
        # Get audio duration
        audio_duration = video.duration
        audio_title = os.path.splitext(video_file)[0]
        
        # Close the video to free up resources
        video.close()
        
        print(f"Audio extracted to {audio_path}")
        print(f"Audio duration: {audio_duration}")
        
        return audio_path, audio_duration, audio_title, video_url, video_path
    
    except Exception as e:
        print(f"Error in downloading or converting video: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None

# Function to verify Firebase token and get user ID
def get_user_id_from_token(token):
    try:
        # Verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']  # Extract the user ID (UID)
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

# API endpoint to convert TikTok video and upload audio to Cloudinary
@app.route("/convert", methods=["POST"])
def convert_and_upload():
    print('initiated')
    # Get Firebase token from request headers
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token missing"}), 400
    token = token.split(' ')[1]  # Extract token from "Bearer token"

    # Get user ID from the Firebase token
    user_id = get_user_id_from_token(token)
    if not user_id:
        return jsonify({"error": "Invalid token or user not found"}), 401
    
    # Check if URL is provided in the request
    if 'url' not in request.json:
        return jsonify({"error": "No URL provided"}), 400

    video_url = request.json['url']

     # Modify the unpacking to include video_path
    audio_file_path, audio_duration, audio_title, video_url, video_path = download_and_convert_to_audio(video_url)
    
    
    if not audio_file_path:
        return jsonify({"error": "Audio conversion failed"}), 500
    
    # Upload the audio to Cloudinary
    audio_url = upload_audio_to_cloudinary(audio_file_path)

     # Extract and upload frame
    frame_url = extract_and_upload_frame(video_path, 'temp_downloads')
    
    
    if audio_url:
        # Store audio data in Firebase Firestore
        audio_data = {
            "audio_duration": audio_duration,  # Duration in seconds
            "audio_title": audio_title,
            "audio_url": audio_url,
            "frame_url": frame_url,  # Add frame URL to the document
            "converted_at": firestore.SERVER_TIMESTAMP,
            "user_id": user_id,  # Store user_id automatically from Firebase token
            "video_url": video_url  # Store the original TikTok video URL
        }
        
        # Save the audio data to Firestore
        db.collection('audio_files').add(audio_data)
        
        if os.path.exists('temp_downloads'):
            shutil.rmtree('temp_downloads')
        
        return jsonify({
            "audio_url": audio_url, 
            "audio_title": audio_title, 
            "audio_duration": audio_duration,
            "frame_url": frame_url
        }), 200
    else:
        return jsonify({"error": "Audio upload to Cloudinary failed"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Bind to all available IPs

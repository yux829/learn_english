import os
import whisper
import numpy as np
from scipy.io import wavfile

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ImportError:
    # Handle MoviePy 2.x
    from moviepy import VideoFileClip, AudioFileClip

class VideoProcessor:
    def __init__(self, model_size="base", model=None):
        """
        Initialize the VideoProcessor with a Whisper model.
        Args:
            model_size (str): The size of the Whisper model to use (e.g., "tiny", "base", "small", "medium", "large").
            model: Pre-loaded Whisper model instance. If provided, model_size is ignored.
        """
        self.model_size = model_size
        if model:
            self.model = model
        else:
            print(f"Loading Whisper model: {model_size}...")
            self.model = whisper.load_model(model_size)
            print("Model loaded.")

    def extract_audio(self, video_path, audio_path):
        """
        Extract audio from a video file in WAV format (16kHz, mono).
        Whisper works best with 16kHz mono audio.
        """
        try:
            print(f"Extracting audio from {video_path} to {audio_path}...")
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                print(f"Error: No audio track found in {video_path}")
                video.close()
                return False
                
            # Use standard parameters for Whisper
            video.audio.write_audiofile(
                audio_path, 
                fps=16000, 
                nbytes=2, 
                codec='pcm_s16le', 
                ffmpeg_params=["-ac", "1"], # Mono
                verbose=False, 
                logger=None
            )
            video.close()
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"Audio extraction successful: {os.path.getsize(audio_path)} bytes.")
                return True
            else:
                print(f"Audio extraction failed: file {audio_path} is empty or missing.")
                return False
        except Exception as e:
            print(f"Error extracting audio: {e}")
            import traceback
            traceback.print_exc()
            return False

    def transcribe_audio(self, audio_path, language="en"):
        """
        Transcribe audio using Whisper and return segments.
        If segments are missing, try to construct one from the full text.
        Manual audio loading is used to bypass Whisper's internal ffmpeg dependency.
        """
        try:
            if not os.path.exists(audio_path):
                print(f"Error: Audio file not found at {audio_path}")
                return []
            
            file_size = os.path.getsize(audio_path)
            print(f"Starting transcription for: {audio_path} (Size: {file_size} bytes)...")
            
            # Manual load to bypass Whisper's internal ffmpeg dependency
            try:
                # Load audio using scipy.io.wavfile
                # Since we extracted as 16kHz mono PCM_S16LE, this works perfectly.
                sample_rate, data = wavfile.read(audio_path)
                # Convert to float32 and normalize to [-1, 1]
                audio_data = data.astype(np.float32) / 32768.0
                print(f"Audio loaded manually (SR: {sample_rate}Hz, length: {len(audio_data)} samples)")
                
                # Use the numpy array directly
                result = self.model.transcribe(
                    audio_data, 
                    language=language, 
                    task="transcribe",
                    temperature=0,
                    beam_size=5,
                    best_of=5
                )
            except Exception as load_err:
                print(f"Manual audio load failed: {load_err}. Falling back to default (needs ffmpeg).")
                # Fallback to default path-based transcription
                result = self.model.transcribe(
                    audio_path, 
                    language=language, 
                    task="transcribe",
                    temperature=0,
                    beam_size=5,
                    best_of=5
                )
            
            segments = result.get("segments", [])
            full_text = result.get("text", "").strip()
            
            print(f"Transcription complete. Found {len(segments)} segments.")
            
            # Fallback: if segments are empty but we have full text, create a single segment
            if not segments and full_text:
                print("No segments found, but full text available. Creating a single segment.")
                # We need to get the duration of the audio
                try:
                    audio = AudioFileClip(audio_path)
                    duration = audio.duration
                    audio.close()
                except:
                    duration = 0
                    
                segments = [{
                    "id": 0,
                    "start": 0.0,
                    "end": duration,
                    "text": full_text
                }]
                
            return segments
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            import traceback
            traceback.print_exc()
            return []

    def process_video(self, video_file, output_dir="processed"):
        """
        Process the uploaded video: save it, extract audio, and transcribe.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save video file
        video_filename = video_file.name
        video_path = os.path.join(output_dir, video_filename)
        
        with open(video_path, "wb") as f:
            f.write(video_file.getbuffer())

        # Use WAV for better compatibility
        audio_filename = os.path.splitext(video_filename)[0] + ".wav"
        audio_path = os.path.join(output_dir, audio_filename)
        
        success = self.extract_audio(video_path, audio_path)
        
        if not success:
            return {
                "video_path": video_path,
                "audio_path": None,
                "segments": [],
                "error": "Audio extraction failed."
            }

        # Transcribe
        segments = self.transcribe_audio(audio_path)

        return {
            "video_path": video_path,
            "audio_path": audio_path,
            "segments": segments
        }

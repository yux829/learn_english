# English Learning App

A local application for learning English by practicing dictation with video content.
It uses OpenAI's Whisper model for automatic speech recognition and Streamlit for the user interface.

## Features

- **Video Upload**: Upload any English video (mp4, mov, avi).
- **Automatic Transcription**: Splits the video into sentences using Whisper AI.
- **Dictation Practice**:
    - Listen to each sentence segment.
    - Type what you hear.
    - Get instant feedback with diff highlighting (Red for errors, Green for corrections).
- **Progress Tracking**: Compare your input with the AI-generated transcript.

## Prerequisites

- Python 3.8+
- FFmpeg (usually installed automatically with moviepy/imageio-ffmpeg, but if issues arise, install it manually and add to PATH)

## Installation

1.  Clone or download this repository.
2.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    *Note: Installing `openai-whisper` and `torch` might take some time depending on your internet connection.*

## Usage

1.  Run the Streamlit app:

    ```bash
    streamlit run app.py
    ```

2.  The application will open in your default web browser (usually at `http://localhost:8501`).

3.  Upload a video file from the sidebar.

4.  Click "Process Video" and wait for the AI to transcribe it.

5.  Select a sentence, listen to the audio, and type your transcription!

## Troubleshooting

-   **FFmpeg Error**: If you see errors related to audio extraction, ensure FFmpeg is installed and accessible.
-   **Model Loading**: The first time you run the app, it will download the Whisper model (approx. 140MB for 'base' model).

## Tech Stack

-   **Python**: Core logic
-   **Streamlit**: UI Framework
-   **OpenAI Whisper**: Speech-to-Text
-   **MoviePy**: Video/Audio processing

import streamlit as st
import streamlit.components.v1 as components
import os
import difflib
import whisper
import string
import shutil
from video_processor import VideoProcessor
try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ImportError:
    # Handle MoviePy 2.x
    from moviepy import VideoFileClip, AudioFileClip

# Configure page
st.set_page_config(
    page_title="English Learning App", 
    layout="centered", # Better for mobile
    initial_sidebar_state="collapsed" # Save space on mobile
)

# Custom CSS for Mobile Optimization
st.markdown("""
    <style>
    /* Adjust for mobile screens */
    .stApp {
        max-width: 100%;
        margin: 0 auto;
    }
    
    /* Make buttons easier to tap on mobile */
    .stButton button {
        width: 100%;
        height: 3rem;
        margin-bottom: 0.5rem;
    }
    
    /* Optimize font sizes for mobile */
    h1 {
        font-size: 1.5rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
    }
    
    /* Better spacing for navigation buttons */
    [data-testid="column"] {
        padding: 0 5px !important;
    }
    
    /* Fix audio player width */
    audio {
        width: 100%;
    }
    
    /* Hide top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'current_sentence_index' not in st.session_state:
    st.session_state.current_sentence_index = 0
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

def cleanup_temp():
    """Clean up the temp directory."""
    if os.path.exists("temp"):
        try:
            shutil.rmtree("temp")
        except Exception as e:
            # If rmtree fails (e.g. file locked), try to delete files individually
            for filename in os.listdir("temp"):
                file_path = os.path.join("temp", filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception:
                    pass
    if not os.path.exists("temp"):
        os.makedirs("temp")

def highlight_diff(user_text, original_text):
    """
    Compare user text with original text and return formatted markdown.
    """
    user_words = user_text.strip().split()
    original_words = original_text.strip().split()
    
    matcher = difflib.SequenceMatcher(None, user_words, original_words)
    output = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            output.append(" ".join(user_words[i1:i2]))
        elif tag == 'replace':
            output.append(f":red[{' '.join(user_words[i1:i2])}] :green[{' '.join(original_words[j1:j2])}]")
        elif tag == 'delete':
            output.append(f":red[{' '.join(user_words[i1:i2])}]")
        elif tag == 'insert':
            output.append(f":green[{' '.join(original_words[j1:j2])}]")
            
    return " ".join(output)

def safe_rerun():
    """
    Rerun the app in a way that's compatible with different Streamlit versions.
    """
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

def main():
    st.title("English Learning - Video Dictation")

    # Sidebar for upload and settings
    with st.sidebar:
        st.header("设置")
        model_size = st.selectbox("选择 Whisper 模型大小:", ["tiny", "base", "small", "medium", "large"], index=1, help="模型越大越准确，但速度越慢且占用更多显存/内存。")
        
        st.header("上传视频")
        uploaded_file = st.file_uploader("选择一个视频文件", type=['mp4', 'mov', 'avi', 'mkv'])
        
        # Check if a new file is uploaded
        if uploaded_file is not None and (st.session_state.last_uploaded_file != uploaded_file.name):
            st.session_state.processed_data = None
            st.session_state.current_sentence_index = 0
            st.session_state.last_uploaded_file = uploaded_file.name
        
        if uploaded_file is not None:
            if st.button("开始处理视频"):
                # Clear previous data and files
                cleanup_temp()
                
                # Use specified model size
                if 'processor' in st.session_state and st.session_state.processor.model_size != model_size:
                    # Reload model if size changed
                    st.info(f"正在切换到 {model_size} 模型...")
                    del st.session_state.processor
                    st.session_state.processor = VideoProcessor(model_size=model_size)
                
                if 'processor' not in st.session_state:
                    st.info(f"正在加载 {model_size} 模型...")
                    st.session_state.processor = VideoProcessor(model_size=model_size)
                
                processor = st.session_state.processor
                
                # Use a placeholder for granular progress
                progress_placeholder = st.empty()
                with st.spinner("正在处理视频..."):
                    try:
                        # Step 1: Save Video
                        progress_placeholder.info("1/3: 正在保存视频文件...")
                        video_path = os.path.join("temp", uploaded_file.name)
                        with open(video_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Step 2: Extract Audio
                        progress_placeholder.info("2/3: 正在提取音频 (16kHz WAV)...")
                        audio_path = os.path.join("temp", os.path.splitext(uploaded_file.name)[0] + ".wav")
                        if processor.extract_audio(video_path, audio_path):
                            # Step 3: Transcribe
                            progress_placeholder.info("3/3: AI 正在转录文本 (这可能需要一些时间)...")
                            segments = processor.transcribe_audio(audio_path)
                            
                            if segments:
                                st.session_state.processed_data = {
                                    "video_path": video_path,
                                    "audio_path": audio_path,
                                    "segments": segments
                                }
                                progress_placeholder.success(f"处理完成！成功识别出 {len(segments)} 个语句。")
                            else:
                                progress_placeholder.error("AI 识别失败：未在视频中找到任何语句。")
                        else:
                            progress_placeholder.error("音频提取失败，请检查视频文件格式。")
                    except Exception as e:
                        progress_placeholder.error(f"处理过程中出错: {e}")

    # Main content area
    if st.session_state.processed_data:
        data = st.session_state.processed_data
        segments = data["segments"]
        
        # Display Video
        st.video(data["video_path"])
        
        st.divider()
        st.subheader("Dictation Practice")
        
        # Select sentence
        if not segments:
            st.warning("No sentences found in the video.")
            return

        # Ensure index is within range
        if st.session_state.current_sentence_index >= len(segments):
            st.session_state.current_sentence_index = 0

        # Navigation Buttons and Selection
        # Mobile optimized layout: Buttons in rows
        row1_col1, row1_col2 = st.columns([1, 1])
        with row1_col1:
            if st.button("⬅️ 上一句", disabled=st.session_state.current_sentence_index <= 0):
                st.session_state.current_sentence_index -= 1
                st.session_state.play_count = st.session_state.get('play_count', 0) + 1
                safe_rerun()
        with row1_col2:
            if st.button("下一句 ➡️", disabled=st.session_state.current_sentence_index >= len(segments) - 1):
                st.session_state.current_sentence_index += 1
                st.session_state.play_count = st.session_state.get('play_count', 0) + 1
                safe_rerun()
        
        if st.button("▶️ 播放当前句子"):
            st.session_state.play_count = st.session_state.get('play_count', 0) + 1
            safe_rerun()

        sentence_options = [f"{i+1}. {seg['text'][:30]}..." for i, seg in enumerate(segments)]
        selected_index = st.selectbox(
            "跳转到句子:", 
            range(len(segments)), 
            format_func=lambda x: sentence_options[x],
            index=st.session_state.current_sentence_index
        )
        
        if selected_index != st.session_state.current_sentence_index:
            st.session_state.current_sentence_index = selected_index
            st.session_state.play_count = st.session_state.get('play_count', 0) + 1
            safe_rerun()
        
        selected_index = st.session_state.current_sentence_index
        if selected_index is not None:
            current_seg = segments[selected_index]
            
            st.info(f"Listen to the segment ({current_seg['start']:.1f}s - {current_seg['end']:.1f}s)")
            
            # Create segment audio
            segment_audio_path = f"temp/segment_{selected_index}.mp3"
            
            # Use moviepy to slice audio if not exists
            if not os.path.exists(segment_audio_path):
                try:
                    # Load audio file directly using moviepy
                    audio_clip = AudioFileClip(data["audio_path"])
                    # Create subclip
                    subclip = audio_clip.subclip(current_seg['start'], current_seg['end'])
                    subclip.write_audiofile(segment_audio_path, verbose=False, logger=None)
                    audio_clip.close()
                    subclip.close()
                except Exception as e:
                    st.error(f"Error creating audio segment: {e}")

            if os.path.exists(segment_audio_path):
                # For older Streamlit versions that don't support 'key' and 'autoplay' in st.audio
                # We show the standard player and use a small HTML/JS for autoplay/replay
                st.audio(segment_audio_path)
                
                # Autoplay/Replay trigger
                import base64
                with open(segment_audio_path, "rb") as f:
                    audio_base64 = base64.b64encode(f.read()).decode()
                
                audio_html = f"""
                    <!-- key: {selected_index}_{st.session_state.get('play_count', 0)} -->
                    <audio autoplay>
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                components.html(audio_html, height=0)
            
            if st.button("Show Answer"):
                st.info(f"Answer: {current_seg['text']}")

            st.subheader("Type what you hear:")
            
            # Typing sound effect using JS
            typing_sound_js = """
            <script>
            const audio = new Audio('https://www.soundjay.com/communication/typewriter-key-1.mp3');
            function attachListeners() {
                const doc = window.parent.document;
                const textareas = doc.querySelectorAll('textarea');
                
                textareas.forEach(textarea => {
                    if (!textarea.dataset.hasTypingListener) {
                        textarea.addEventListener('input', () => {
                            audio.currentTime = 0;
                            audio.play().catch(e => console.log('Audio play failed:', e));
                        });
                        textarea.dataset.hasTypingListener = 'true';
                    }
                });
            }
            // Run immediately and also after a short delay to ensure elements are rendered
            attachListeners();
            // Use MutationObserver to handle dynamically added elements by Streamlit
            const observer = new MutationObserver(attachListeners);
            observer.observe(window.parent.document.body, { childList: true, subtree: true });
            
            setTimeout(attachListeners, 500);
            setTimeout(attachListeners, 1000);
            </script>
            """
            components.html(typing_sound_js, height=1)

            user_input = st.text_area("Your transcription:", height=100, key=f"input_{selected_index}")
            
            if st.button("Check Answer", key=f"check_{selected_index}"):
                original_text = current_seg["text"].strip()
                
                # Normalize text for comparison (remove punctuation, lower case)
                translator = str.maketrans('', '', string.punctuation)
                norm_user = user_input.translate(translator).lower().strip()
                norm_orig = original_text.translate(translator).lower().strip()
                
                if norm_user == norm_orig:
                    st.success("Correct! Great job!")
                else:
                    st.warning("Needs improvement. See differences below:")
                    st.markdown(highlight_diff(user_input, original_text))
                    st.write(f"**Original:** {original_text}")

    else:
        st.info("Please upload a video to start.")

if __name__ == "__main__":
    main()

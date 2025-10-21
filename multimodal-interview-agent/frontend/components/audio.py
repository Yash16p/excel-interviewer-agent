import streamlit as st
import numpy as np

try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError as e:
    PYAUDIO_AVAILABLE = False
    st.warning(f"Audio libraries not available: {e}")

class AudioComponent:
    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.pyaudio_available = PYAUDIO_AVAILABLE
        
        if self.pyaudio_available:
            try:
                self.audio = pyaudio.PyAudio()
            except Exception as e:
                st.error(f"Failed to initialize audio: {e}")
                self.audio = None
                self.pyaudio_available = False
        else:
            self.audio = None
    
    def record_audio(self, duration=5):
        """Record audio from microphone"""
        if not self.pyaudio_available or not self.audio:
            st.error("Audio recording not available - microphone access required")
            return None
            
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            for _ in range(0, int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            return frames
        except Exception as e:
            st.error(f"Audio recording failed: {e}")
            return None
    
    def detect_multiple_speakers(self, audio_data):
        """Detect if multiple speakers are present"""
        if not audio_data:
            return False
        # Placeholder for speaker detection
        return False
    
    def analyze_speech_quality(self, audio_data):
        """Analyze speech quality metrics"""
        if not audio_data:
            return {"quality": "unknown", "message": "No audio data"}
        # Placeholder for speech analysis
        return {"quality": "good", "confidence": 0.8}
    
    def get_audio_input(self):
        """Get audio input from user - simplified interface"""
        
        # Try Streamlit's native audio input first
        try:
            if hasattr(st, 'audio_input'):
                return st.audio_input("🎤 Record your response:")
        except:
            pass
        
        # Fallback: Simple recording button
        if st.button("🎤 Record Response", type="primary", use_container_width=True):
            if self.pyaudio_available and self.audio:
                with st.spinner("🎙️ Recording... (5 seconds)"):
                    import time
                    time.sleep(1)
                    audio_data = self.record_audio(duration=5)
                    if audio_data:
                        st.success("✅ Recording completed!")
                        return b"".join(audio_data)
            else:
                with st.spinner("🎙️ Demo recording..."):
                    import time
                    time.sleep(2)
                    st.success("✅ Demo recording completed!")
                    return b"demo_audio_data"
        
        return None
    
    def show_browser_audio_recorder(self):
        """Show browser-based audio recorder using JavaScript"""
        st.markdown("### 🎙️ Browser Audio Recorder")
        
        # JavaScript-based audio recorder
        audio_recorder_js = """
        <div id="audio-recorder">
            <button id="startBtn" onclick="startRecording()">🎤 Start Recording</button>
            <button id="stopBtn" onclick="stopRecording()" disabled>⏹️ Stop Recording</button>
            <div id="status">Ready to record</div>
            <audio id="audioPlayback" controls style="display:none;"></audio>
        </div>
        
        <script>
        let mediaRecorder;
        let audioChunks = [];
        
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    const audioPlayback = document.getElementById('audioPlayback');
                    audioPlayback.src = audioUrl;
                    audioPlayback.style.display = 'block';
                    
                    // Convert to base64 and send to Streamlit
                    const reader = new FileReader();
                    reader.onloadend = function() {
                        const base64data = reader.result.split(',')[1];
                        window.parent.postMessage({
                            type: 'audio_recorded',
                            data: base64data
                        }, '*');
                    };
                    reader.readAsDataURL(audioBlob);
                    
                    document.getElementById('status').textContent = 'Recording completed!';
                    audioChunks = [];
                };
                
                mediaRecorder.start();
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').textContent = 'Recording... Speak clearly';
                
                // Auto-stop after 10 seconds
                setTimeout(() => {
                    if (mediaRecorder.state === 'recording') {
                        stopRecording();
                    }
                }, 10000);
                
            } catch (err) {
                document.getElementById('status').textContent = 'Error: ' + err.message;
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
            
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
        </script>
        
        <style>
        #audio-recorder {
            padding: 20px;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        }
        
        #audio-recorder button {
            margin: 5px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        
        #startBtn {
            background-color: #4CAF50;
            color: white;
        }
        
        #stopBtn {
            background-color: #f44336;
            color: white;
        }
        
        #status {
            margin: 10px 0;
            font-weight: bold;
        }
        </style>
        """
        
        st.components.v1.html(audio_recorder_js, height=200)
        
        return None
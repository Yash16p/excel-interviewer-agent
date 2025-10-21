import os
import base64
import time
from typing import Optional
import requests
from io import BytesIO

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

class TTSModule:
    """Text-to-Speech module for AI interviewer voice"""
    
    def __init__(self, engine_type="pyttsx3"):
        self.engine_type = engine_type
        self.engine = None
        
        if engine_type == "pyttsx3" and PYTTSX3_AVAILABLE:
            self._initialize_pyttsx3()
        elif engine_type == "openai":
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to use a female voice for more professional feel
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech rate (words per minute)
            self.engine.setProperty('rate', 180)  # Slightly slower for clarity
            
            # Set volume (0.0 to 1.0)
            self.engine.setProperty('volume', 0.9)
            
            print("✅ TTS Engine initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def speak_question(self, question_text: str, save_audio: bool = False) -> Optional[str]:
        """
        Convert question text to speech
        
        Args:
            question_text: The question to speak
            save_audio: Whether to save audio file
            
        Returns:
            Path to audio file if saved, None otherwise
        """
        
        if self.engine_type == "pyttsx3" and self.engine:
            return self._speak_with_pyttsx3(question_text, save_audio)
        elif self.engine_type == "openai":
            return self._speak_with_openai(question_text, save_audio)
        else:
            print("❌ No TTS engine available")
            return None
    
    def _speak_with_pyttsx3(self, text: str, save_audio: bool = False) -> Optional[str]:
        """Use pyttsx3 for text-to-speech"""
        try:
            if save_audio:
                # Save to file
                audio_filename = f"question_audio_{int(time.time())}.wav"
                self.engine.save_to_file(text, audio_filename)
                self.engine.runAndWait()
                return audio_filename
            else:
                # Just speak
                self.engine.say(text)
                self.engine.runAndWait()
                return None
                
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return None
    
    def _speak_with_openai(self, text: str, save_audio: bool = False) -> Optional[str]:
        """Use OpenAI TTS API for text-to-speech"""
        try:
            if not self.openai_api_key:
                print("❌ OpenAI API key not found")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "tts-1",
                "input": text,
                "voice": "nova",  # Professional female voice
                "response_format": "mp3"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                if save_audio:
                    audio_filename = f"question_audio_{int(time.time())}.mp3"
                    with open(audio_filename, 'wb') as f:
                        f.write(response.content)
                    return audio_filename
                else:
                    # For web playback, return base64 encoded audio
                    audio_b64 = base64.b64encode(response.content).decode()
                    return audio_b64
            else:
                print(f"❌ OpenAI TTS API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI TTS Error: {e}")
            return None
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if self.engine_type == "pyttsx3" and self.engine:
            try:
                voices = self.engine.getProperty('voices')
                return [{"id": voice.id, "name": voice.name} for voice in voices]
            except:
                return []
        elif self.engine_type == "openai":
            return [
                {"id": "alloy", "name": "Alloy"},
                {"id": "echo", "name": "Echo"}, 
                {"id": "fable", "name": "Fable"},
                {"id": "onyx", "name": "Onyx"},
                {"id": "nova", "name": "Nova"},
                {"id": "shimmer", "name": "Shimmer"}
            ]
        return []
    
    def set_voice_properties(self, rate: int = 180, volume: float = 0.9, voice_id: str = None):
        """Set voice properties for pyttsx3"""
        if self.engine_type == "pyttsx3" and self.engine:
            try:
                self.engine.setProperty('rate', rate)
                self.engine.setProperty('volume', volume)
                
                if voice_id:
                    self.engine.setProperty('voice', voice_id)
                    
                print(f"✅ Voice properties updated: rate={rate}, volume={volume}")
            except Exception as e:
                print(f"❌ Failed to set voice properties: {e}")
    
    def create_interview_intro(self) -> str:
        """Create and speak interview introduction"""
        intro_text = """
        Hello! Welcome to your AI-powered interview session. 
        I'm your AI interviewer, and I'll be asking you a series of questions 
        to evaluate your skills and experience. 
        
        Please speak clearly and take your time to answer each question thoughtfully. 
        The interview will consist of about 5 to 7 questions, and should take 
        approximately 15 to 20 minutes to complete.
        
        Are you ready to begin? Let's start with our first question.
        """
        
        return self.speak_question(intro_text.strip())
    
    def create_interview_conclusion(self) -> str:
        """Create and speak interview conclusion"""
        conclusion_text = """
        Thank you for completing the interview! 
        Your responses have been recorded and will be evaluated by our AI system. 
        You should receive feedback and results within the next 24 hours.
        
        We appreciate your time and interest in this position. 
        Good luck with your application!
        """
        
        return self.speak_question(conclusion_text.strip())

# Utility function for Streamlit integration
def create_audio_player_html(audio_b64: str, autoplay: bool = True) -> str:
    """Create HTML audio player for Streamlit"""
    autoplay_attr = "autoplay" if autoplay else ""
    
    html = f"""
    <audio controls {autoplay_attr} style="width: 100%;">
        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    
    return html

if __name__ == "__main__":
    # Test TTS module
    print("🎤 Testing TTS Module...")
    
    tts = TTSModule(engine_type="pyttsx3")
    
    # Test basic speech
    test_question = "Hello! This is a test of the AI interviewer voice. Can you hear me clearly?"
    
    print("Speaking test question...")
    tts.speak_question(test_question)
    
    # Show available voices
    voices = tts.get_available_voices()
    print(f"\n🎵 Available voices: {len(voices)}")
    for voice in voices[:3]:  # Show first 3
        print(f"  - {voice['name']}")
    
    print("\n✅ TTS Module test completed!")
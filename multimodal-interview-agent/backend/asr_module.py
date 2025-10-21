import whisper
import numpy as np
from typing import Union

class ASRModule:
    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)
    
    def transcribe(self, audio_data: Union[bytes, np.ndarray, str]) -> str:
        """Convert audio to text using Whisper"""
        try:
            result = self.model.transcribe(audio_data)
            return result["text"].strip()
        except Exception as e:
            print(f"ASR Error: {e}")
            return ""
    
    def transcribe_with_timestamps(self, audio_data: Union[bytes, np.ndarray, str]) -> dict:
        """Transcribe with word-level timestamps"""
        try:
            result = self.model.transcribe(audio_data, word_timestamps=True)
            return {
                "text": result["text"].strip(),
                "segments": result["segments"],
                "language": result["language"]
            }
        except Exception as e:
            print(f"ASR Error: {e}")
            return {"text": "", "segments": [], "language": "en"}
    
    def detect_language(self, audio_data: Union[bytes, np.ndarray, str]) -> str:
        """Detect spoken language"""
        try:
            # Detect language from first 30 seconds
            audio = whisper.load_audio(audio_data)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            return max(probs, key=probs.get)
        except Exception as e:
            print(f"Language detection error: {e}")
            return "en"
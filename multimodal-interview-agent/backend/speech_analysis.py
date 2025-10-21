import librosa
import numpy as np
from typing import Dict, List
import re

class SpeechAnalyzer:
    def __init__(self):
        self.filler_words = ["um", "uh", "like", "you know", "so", "actually", "basically"]
    
    def analyze_speech_patterns(self, audio_data: np.ndarray, transcript: str, sample_rate: int = 16000) -> Dict:
        """Comprehensive speech pattern analysis"""
        
        analysis = {
            "fluency_score": self._calculate_fluency(audio_data, transcript, sample_rate),
            "confidence_indicators": self._analyze_confidence(audio_data, transcript, sample_rate),
            "filler_word_count": self._count_filler_words(transcript),
            "speech_rate": self._calculate_speech_rate(transcript, len(audio_data) / sample_rate),
            "pause_analysis": self._analyze_pauses(audio_data, sample_rate),
            "tone_analysis": self._analyze_tone(audio_data, sample_rate)
        }
        
        return analysis
    
    def _calculate_fluency(self, audio_data: np.ndarray, transcript: str, sample_rate: int) -> float:
        """Calculate speech fluency score (0-10)"""
        # Analyze speech continuity, pause patterns, and hesitations
        duration = len(audio_data) / sample_rate
        word_count = len(transcript.split())
        
        # Simple fluency metric based on words per minute and pause frequency
        wpm = (word_count / duration) * 60
        optimal_wpm = 150  # Average conversational speed
        
        fluency_score = max(0, 10 - abs(wpm - optimal_wpm) / 20)
        return min(10, fluency_score)
    
    def _analyze_confidence(self, audio_data: np.ndarray, transcript: str, sample_rate: int) -> Dict:
        """Analyze confidence indicators in speech"""
        # Voice stability, volume consistency, pitch variation
        rms_energy = librosa.feature.rms(y=audio_data)[0]
        pitch = librosa.yin(audio_data, fmin=50, fmax=400)
        
        return {
            "voice_stability": np.std(rms_energy),
            "pitch_variation": np.std(pitch[~np.isnan(pitch)]),
            "volume_consistency": 1.0 - (np.std(rms_energy) / np.mean(rms_energy))
        }
    
    def _count_filler_words(self, transcript: str) -> Dict:
        """Count filler words and calculate percentage"""
        words = transcript.lower().split()
        total_words = len(words)
        
        filler_counts = {}
        total_fillers = 0
        
        for filler in self.filler_words:
            count = words.count(filler)
            filler_counts[filler] = count
            total_fillers += count
        
        return {
            "total_filler_words": total_fillers,
            "filler_percentage": (total_fillers / total_words * 100) if total_words > 0 else 0,
            "filler_breakdown": filler_counts
        }
    
    def _calculate_speech_rate(self, transcript: str, duration: float) -> Dict:
        """Calculate words per minute and syllables per minute"""
        words = transcript.split()
        word_count = len(words)
        
        # Estimate syllable count (simplified)
        syllable_count = sum(self._count_syllables(word) for word in words)
        
        return {
            "words_per_minute": (word_count / duration) * 60 if duration > 0 else 0,
            "syllables_per_minute": (syllable_count / duration) * 60 if duration > 0 else 0
        }
    
    def _analyze_pauses(self, audio_data: np.ndarray, sample_rate: int) -> Dict:
        """Analyze pause patterns in speech"""
        # Detect silent segments
        rms_energy = librosa.feature.rms(y=audio_data, frame_length=2048, hop_length=512)[0]
        silence_threshold = np.mean(rms_energy) * 0.1
        
        silent_frames = rms_energy < silence_threshold
        pause_segments = self._find_consecutive_segments(silent_frames)
        
        # Convert frame indices to time
        hop_length = 512
        pause_durations = [(end - start) * hop_length / sample_rate for start, end in pause_segments]
        
        return {
            "total_pause_time": sum(pause_durations),
            "pause_count": len(pause_durations),
            "average_pause_duration": np.mean(pause_durations) if pause_durations else 0,
            "long_pause_count": sum(1 for duration in pause_durations if duration > 2.0)
        }
    
    def _analyze_tone(self, audio_data: np.ndarray, sample_rate: int) -> Dict:
        """Analyze emotional tone and energy in speech"""
        # Extract spectral features for tone analysis
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        
        return {
            "average_pitch": np.mean(spectral_centroids),
            "pitch_range": np.max(spectral_centroids) - np.min(spectral_centroids),
            "energy_level": np.mean(librosa.feature.rms(y=audio_data)[0]),
            "spectral_features": np.mean(mfccs, axis=1).tolist()
        }
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count in a word"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _find_consecutive_segments(self, boolean_array: np.ndarray) -> List[tuple]:
        """Find consecutive True segments in boolean array"""
        segments = []
        start = None
        
        for i, value in enumerate(boolean_array):
            if value and start is None:
                start = i
            elif not value and start is not None:
                segments.append((start, i))
                start = None
        
        if start is not None:
            segments.append((start, len(boolean_array)))
        
        return segments
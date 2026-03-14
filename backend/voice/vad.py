import numpy as np
import logging
from typing import List, Dict
try:
    from silero_vad import load_silero_vad, get_speech_timestamps
except ImportError:
    logging.warning("silero_vad not installed. VAD will be disabled.")
    load_silero_vad = None
    get_speech_timestamps = None

class VoiceActivityDetector:
    """
    Detects voice activity in audio streams using Silero VAD.
    """
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.model = None
        
        if load_silero_vad is not None:
            try:
                # Load the ONNX version by default for speed
                self.model = load_silero_vad(onnx=True)
                logging.info("Silero VAD ONNX model loaded successfully.")
            except Exception as e:
                logging.error(f"Failed to load Silero VAD model: {e}")

    def has_speech(self, audio_chunk: np.ndarray, threshold: float = 0.5) -> bool:
        """
        Quickly check if a single chunk has speech.
        """
        if self.model is None or get_speech_timestamps is None:
            return True # Fallback if model failed to load
            
        # Ensure float32 in range [-1, 1]
        if audio_chunk.dtype == np.int16:
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0
            
        try:
            # get_speech_timestamps expects 1D float32 array
            timestamps = get_speech_timestamps(
                audio_chunk, 
                self.model, 
                sampling_rate=self.sample_rate,
                threshold=threshold,
                return_seconds=False
            )
            return len(timestamps) > 0
        except Exception as e:
            logging.error(f"Error in VAD has_speech: {e}")
            return True

    def get_speech_segments(self, audio_data: np.ndarray, threshold: float = 0.5) -> List[Dict[str, int]]:
        """
        Get timestamps (in samples) of speech segments in the provided audio.
        """
        if self.model is None or get_speech_timestamps is None:
            return [{"start": 0, "end": len(audio_data)}]
            
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
            
        try:
            timestamps = get_speech_timestamps(
                audio_data, 
                self.model, 
                sampling_rate=self.sample_rate,
                threshold=threshold
            )
            return timestamps
        except Exception as e:
            logging.error(f"Error extracting speech segments: {e}")
            return [{"start": 0, "end": len(audio_data)}]

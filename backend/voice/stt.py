import os
import logging
import numpy as np
try:
    from faster_whisper import WhisperModel
except ImportError:
    logging.warning("faster-whisper not installed. Local STT will fail.")
    WhisperModel = None

class SpeechToText:
    """
    Local Speech-To-Text pipeline using faster-whisper.
    """
    def __init__(self, model_size: str = "base.en", compute_type: str = "float16"):
        self.model_size = model_size
        self.compute_type = compute_type
        
        # Determine device based on CUDA availability
        self.device = "cuda" if self._is_cuda_available() else "cpu"
        
        # If CPU, float16 is not supported by ctranslate2 usually, fallback to int8
        if self.device == "cpu" and self.compute_type == "float16":
            self.compute_type = "int8"
            
        logging.info(f"Loading faster-whisper model '{self.model_size}' on {self.device} with {self.compute_type}")
        
        if WhisperModel is not None:
            try:
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
                logging.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logging.error(f"Failed to load whisper model: {e}")
                self.model = None
        else:
            self.model = None

    def _is_cuda_available(self) -> bool:
        """
        Check if CUDA is available via PyTorch or environment.
        """
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def transcribe(self, audio_data, sample_rate: int = 16000) -> str:
        """
        Transcribe audio data (1D numpy array or file path)
        """
        if self.model is None:
            return "Error: STT model not loaded."
            
        # Ensure proper shape and type if it's a numpy array
        if isinstance(audio_data, np.ndarray):
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
        try:
            segments, info = self.model.transcribe(audio_data, beam_size=5, language="en")
            
            text = ""
            for segment in segments:
                text += segment.text + " "
                
            return text.strip()
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return f"Error transcribing audio: {e}"

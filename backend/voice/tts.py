import os
import queue
import threading
import logging
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None
    logging.warning("sounddevice not installed. Audio output will be mocked.")

try:
    from piper.voice import PiperVoice
except ImportError:
    PiperVoice = None
    logging.warning("piper-tts not installed or loaded.")

class TextToSpeech:
    """
    Local Text-To-Speech pipeline using Piper with a threaded audio queue.
    """
    def __init__(self, model_path: str = "en_US-lessac-high.onnx"):
        self.model_path = model_path
        self.voice = None
        self.audio_queue = queue.Queue()
        self.is_playing = False
        
        # In a real setup, we would download the model if it doesn't exist
        if PiperVoice is not None and os.path.exists(model_path):
            try:
                self.voice = PiperVoice.load(model_path)
                logging.info(f"Piper TTS model '{model_path}' loaded.")
            except Exception as e:
                logging.error(f"Failed to load Piper model: {e}")
                
        # Start the playback worker thread
        self.worker_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.worker_thread.start()

    def speak(self, text: str):
        """
        Synthesizes text to speech and queues it for playback.
        """
        if not text.strip():
            return
            
        if self.voice is None or sd is None:
            logging.info(f"JARVIS [TTS Mock]: {text}")
            return
            
        try:
            # Piper can yield audio streams. We'll simplify and synthesize to memory then queue.
            audio_stream = self.voice.synthesize_stream_raw(text)
            for chunk in audio_stream:
                # Piper returns 16-bit raw PCM usually, 22050Hz for lessac
                audio_np = np.frombuffer(chunk, dtype=np.int16)
                self.audio_queue.put(audio_np)
        except Exception as e:
            logging.error(f"TTS synthesis error: {e}")

    def _playback_worker(self):
        """
        Runs in background, streaming queued audio to the default sound device.
        """
        while True:
            chunk = self.audio_queue.get()
            if chunk is None: # Sentinel to exit
                break
                
            self.is_playing = True
            try:
                if sd is not None:
                    # Default piper sample rate is often 22050
                    sd.play(chunk, samplerate=22050, blocking=True)
            except Exception as e:
                logging.error(f"Audio playback error: {e}")
            finally:
                self.is_playing = False
                self.audio_queue.task_done()

    def stop_speaking(self):
        """
        Interrupts current speech and clears the queue.
        """
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
                
        if sd is not None and self.is_playing:
            sd.stop()
            self.is_playing = False

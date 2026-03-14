import logging
import queue
import threading
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None
    
try:
    from openwakeword.model import Model
except ImportError:
    Model = None
    logging.warning("openwakeword not installed. Wake word detection will be mocked.")

class WakeWordDetector:
    """
    Listens to the microphone stream for the wake word using OpenWakeWord.
    Runs inference in a non-blocking background thread.
    """
    def __init__(self, wake_word="alexa", threshold=0.5):
        # We use a built-in pre-trained wake word for the scaffold (e.g. 'alexa', 'hey siri') 
        # since custom JARVIS wake words require training a new model.
        self.wake_word = wake_word
        self.threshold = threshold
        self.model = None
        self.is_listening = False
        
        if Model is not None:
            try:
                # Load pre-trained model. 
                # OpenWakeWord comes with 'alexa', 'hey_mycroft', 'hey_siri', 'timer'
                self.model = Model(wakeword_models=[self.wake_word])
                logging.info(f"OpenWakeWord model '{self.wake_word}' loaded.")
            except Exception as e:
                logging.error(f"Failed to load OpenWakeWord model: {e}")

    def listen_blocking(self) -> bool:
        """
        Blocks until the wake word is detected in the input stream.
        """
        if self.model is None or sd is None:
            logging.info(f"Listening for '{self.wake_word}'... (Mocking)")
            import time
            time.sleep(2)
            logging.info("Wake word detected! (Mock)")
            return True
            
        logging.info(f"Listening for wake word: {self.wake_word}...")
        
        # openwakeword expects 16khz, 1 channel, 16-bit PCM chunks of 1280 samples (80ms)
        CHUNK = 1280
        RATE = 16000
        
        # We use a crude blocking loop polling sounddevice InputStream
        with sd.InputStream(samplerate=RATE, channels=1, dtype='int16') as stream:
            while True:
                # Read 1280 frames
                audio, overflowed = stream.read(CHUNK)
                if overflowed:
                    logging.warning("Audio input overflowed.")
                    
                # audio is (CHUNK, 1) shaping. Reshape to 1D flat array for openwakeword
                audio_data = audio.flatten()
                
                # predict returns a dict: { 'model_name': float_score }
                prediction = self.model.predict(audio_data)
                
                for mdl_name, score in prediction.items():
                    if score >= self.threshold:
                        logging.info(f"Wake word detected! (Score: {score:.2f})")
                        # Reset model RNN state after detection to prevent rapid re-triggering
                        self.model.reset()
                        return True

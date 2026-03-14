import importlib.metadata
# Patch to prevent transformers from hanging indefinitely while scanning pip packages on Python 3.10+
importlib.metadata.packages_distributions = lambda: {}

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .websockets import router as websocket_router, broadcast_system_vitals
from backend.voice.tts import TextToSpeech
import logging
from backend.llm.factory import LLMFactory
import asyncio
from backend.config import settings

# API Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="JARVIS-X Backend Air-Traffic Control")

@app.on_event("startup")
async def startup_event():
    logging.info("Initializing JARVIS-X subsystems...")
    is_healthy = await LLMFactory.test_connection()
    if not is_healthy:
        logging.warning("CRITICAL: Primary LLM Provider is unreachable. Operating in degraded state or relying on fallbacks.")
    else:
        logging.info("Primary LLM Provider is ONLINE and responding.")
        
    # Start background tasks
    asyncio.create_task(broadcast_system_vitals())

# Initialize global TTS engine
tts_engine = TextToSpeech()

# Configure SlowAPI global handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Restrict CORS to specific frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)

@app.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request):
    return {"status": "online", "agent": "JARVIS-X"}

@app.post("/voice/mute")
@limiter.limit("30/minute")
def mute_tts(request: Request):
    """Interrupts any ongoing Text-to-Speech output."""
    try:
        tts_engine.stop_speaking()
        return {"status": "muted"}
    except Exception as e:
        logging.error(f"Failed to mute TTS: {e}")
        return {"status": "error", "reason": str(e)}

from fastapi import UploadFile, File
import os

@app.post("/voice/transcribe")
@limiter.limit("30/minute")
async def transcribe_audio(request: Request, file: UploadFile = File(...)):
    try:
        from backend.voice.stt import SpeechToText
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        stt = SpeechToText()
        text = stt.transcribe(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"text": text}
    except Exception as e:
        logging.error(f"Failed to transcribe: {e}")
        return {"status": "error", "reason": str(e)}

@app.get("/plugins")
@limiter.limit("60/minute")
def get_plugins(request: Request):
    """Returns a list of all active plugins and their tools."""
    from backend.plugins.plugin_manager import plugin_manager
    return {"plugins": plugin_manager.get_plugin_metadata()}

@app.post("/plugins/reload")
@limiter.limit("30/minute")
def reload_plugins(request: Request):
    """Hot-reloads all plugins from the file system."""
    from backend.plugins.plugin_manager import plugin_manager
    plugin_manager.reload_plugins()
    return {"status": "success", "tools_loaded": len(plugin_manager.get_all_tools())}


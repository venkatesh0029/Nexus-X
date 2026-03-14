import pyautogui
import base64
from io import BytesIO
from PIL import Image
import httpx
import json

class VisionTool:
    def __init__(self, use_lm_studio=True, lm_studio_url="http://localhost:1234/v1/chat/completions"):
        self.use_lm_studio = use_lm_studio
        self.lm_studio_url = lm_studio_url

    def capture_and_encode(self, max_size=(1280, 720)) -> str:
        """Captures screen, resizes to save tokens, and returns base64 jpeg."""
        try:
            # Capture the primary screen
            screenshot = pyautogui.screenshot()
            
            # Resize while maintaining aspect ratio
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (jpeg doesn't support RGBA)
            if screenshot.mode != 'RGB':
                screenshot = screenshot.convert('RGB')
                
            # Compress and save to buffer
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG", quality=75)
            
            # Encode
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            return f"Error capturing screen: {e}"

    def analyze_screen(self, query: str) -> str:
        """Captures screen and sends it to the vision LLM with the query."""
        if not self.use_lm_studio:
            return "Vision analysis requires LM Studio configuration."
            
        print("[Vision] Capturing screen for analysis...")
        b64_image = self.capture_and_encode()
        
        if b64_image.startswith("Error"):
            return b64_image
            
        print("[Vision] Sending image to local vision model...")
        
        payload = {
            "model": "local-model", # Usually ignored by LM Studio, but required by API
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": b64_image
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2
        }
        
        try:
            headers = {"Content-Type": "application/json"}
            # Use synchronous HTTPX for tool execution
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.lm_studio_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                description = data['choices'][0]['message']['content']
                return f"Vision Analysis Result:\n{description}"
        except httpx.TimeoutException:
            return "Error: Vision model request timed out. Ensure the model is loaded in LM Studio and has vision capabilities."
        except httpx.RequestError as e:
             return f"Error communicating with local vision model: {e}. Is LM Studio running on port 1234?"
        except Exception as e:
            return f"Unexpected error during vision analysis: {e}"

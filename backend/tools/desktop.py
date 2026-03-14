import pyautogui
import easyocr
import time
import logging
import cv2
import numpy as np
from typing import Dict, Any

class DesktopTool:
    """
    A suite of tools for controlling the host PC via PyAutoGUI and EasyOCR.
    This allows JARVIS-X to look at the screen, find textual elements, and interact with them.
    """
    
    def __init__(self):
        # Initialize the OCR reader lazily to save startup time if not used
        self.reader = None
        
        # PyAutoGUI failsafes
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5 

    def _get_reader(self):
        if self.reader is None:
            logging.info("Initializing EasyOCR Model (this may take a moment on first run)...")
            self.reader = easyocr.Reader(['en'], gpu=False) # Default to CPU for maximum compatibility
        return self.reader

    def click_coordinates(self, args: Dict[str, Any]) -> str:
        """Clicks directly on specific X, Y coordinates."""
        try:
            x = int(args.get("x", 0))
            y = int(args.get("y", 0))
            clicks = int(args.get("clicks", 1))
            button = args.get("button", "left")
            
            pyautogui.moveTo(x, y, duration=0.5)
            pyautogui.click(clicks=clicks, button=button)
            return f"Successfully clicked at ({x}, {y}) {clicks} times using the {button} button."
        except Exception as e:
            return f"Error executing click_coordinates: {e}"

    def type_text(self, args: Dict[str, Any]) -> str:
        """Types out a specific string of text, optionally hitting enter afterward."""
        try:
            text = args.get("text", "")
            press_enter = args.get("press_enter", False)
            
            if not text:
                return "Error: No text provided to type."
                
            pyautogui.write(text, interval=0.05)
            
            if press_enter:
                pyautogui.press('enter')
                return f"Successfully typed text '{text}' and pressed enter."
            return f"Successfully typed text '{text}'."
        except Exception as e:
            return f"Error executing type_text: {e}"

    def press_key(self, args: Dict[str, Any]) -> str:
        """Presses a specific keyboard key (e.g. 'win', 'enter', 'tab')."""
        try:
            key = args.get("key", "")
            if not key:
                return "Error: No key provided."
                
            pyautogui.press(key)
            return f"Successfully pressed the '{key}' key."
        except Exception as e:
            return f"Error executing press_key: {e}"

    def click_text(self, args: Dict[str, Any]) -> str:
        """
        Takes a screenshot, uses OCR to find the bounding box of the target text,
        and clicks the center of the first occurrence.
        """
        try:
            target_text = args.get("text", "").lower()
            if not target_text:
                return "Error: No target text provided to click."

            logging.info(f"Taking screenshot to locate text: '{target_text}'")
            screenshot = pyautogui.screenshot()
            
            # Convert to OpenCV format (BGR)
            img_np = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            reader = self._get_reader()
            results = reader.readtext(img_np)
            
            # Search for the text
            for (bbox, text, prob) in results:
                if target_text in text.lower():
                    # bbox is a list of 4 points: [top-left, top-right, bottom-right, bottom-left]
                    # Calc center
                    tl_x, tl_y = bbox[0]
                    br_x, br_y = bbox[2]
                    
                    center_x = int((tl_x + br_x) / 2)
                    center_y = int((tl_y + br_y) / 2)
                    
                    logging.info(f"Found '{target_text}' at ({center_x}, {center_y}) with {prob:.2f} confidence.")
                    
                    # Move and click
                    pyautogui.moveTo(center_x, center_y, duration=0.5)
                    pyautogui.click()
                    return f"Found and clicked '{target_text}' at coordinates ({center_x}, {center_y})."
                    
            return f"Could not find the text '{target_text}' on the screen. The Vision Agent may have hallucinated or the UI changed."
        except Exception as e:
            return f"Error executing click_text: {e}"

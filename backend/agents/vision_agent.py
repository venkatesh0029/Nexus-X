import logging
import json
from langchain_core.messages import HumanMessage, SystemMessage
from backend.llm.factory import LLMFactory
from .state import AgentState
from backend.tools.vision import VisionTool
from backend.tools.desktop import DesktopTool

v_tool = VisionTool()
d_tool = DesktopTool()

def vision_agent_node(state: AgentState):
    """
    Dedicated sub-agent for autonomous UI navigation.
    Uses computer vision to analyze the screen and desktop tools to interact.
    """
    logging.info("Executing Vision Agent Node")
    llm = LLMFactory.get_model()
    
    # 1. Capture the screen
    b64_image = v_tool.capture_and_encode()
    
    system_prompt = """You are JARVIS-X's Computer Vision Agent.
Your goal is to autonomously navigate the desktop to fulfill the user's request.
You are seeing a screenshot of the current screen.

Available Tools:
- click_text : Clicks exact text on the screen. Args: {"text": "exact word to click"}
- click_coordinates: Clicks specific x,y coordinates. Args: {"x": 100, "y": 200, "clicks": 1}
- type_text : Types string. Args: {"text": "...", "press_enter": true/false}
- press_key : Presses a key. Args: {"key": "win"}
- finish : Goal is complete. Args: {"response": "Completed."}

Analyze the user's request and the screenshot. Decide the single NEXT logical action to take.
CRITICAL INSTRUCTION: You MUST respond ONLY with a valid JSON object. Do not include markdown framing. Do not include introductory text. Do not apologize. 
Exactly like this:
{"tool": "name", "args": {"key": "value"}}
"""

    # Get the original user request from the history
    # Typically it's the first HumanMessage or the most recent one
    # To be safe, we just grab the last message's content
    last_message = state["messages"][-1].content
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=[
            {"type": "text", "text": f"Goal: {last_message}"},
            {
                "type": "image_url",
                "image_url": {"url": b64_image}
            }
        ])
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.replace("```json", "").replace("```", "").strip()
        
        try:
            # 1. Strip markdown json block tags if they exist
            content = content.replace("```json", "").replace("```", "").strip()
            
            # 2. Try raw parsing
            try:
                decision = json.loads(content)
            except json.JSONDecodeError:
                # 3. Fallback: Search for any dictionary structure { ... }
                import re
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    decision_text = match.group(0)
                    decision = json.loads(decision_text)
                else:
                    return {"final_response": f"Vision Agent failed to parse decision from: {content}", "next_agent": "FINISH"}
                    
            tool = decision.get("tool")
            args = decision.get("args", {})
            logging.info(f"[VISION AGENT] Decided to use tool: {tool} with args: {args}")
            
        except Exception as e:
            return {"final_response": f"Vision Agent crashed during parsing: {e} | Raw output: {content}", "next_agent": "FINISH"}
        
        result_str = ""
        if tool == "click_text":
            result_str = d_tool.click_text(args)
        elif tool == "click_coordinates":
            result_str = d_tool.click_coordinates(args)
        elif tool == "type_text":
            result_str = d_tool.type_text(args)
        elif tool == "press_key":
            result_str = d_tool.press_key(args)
        elif tool == "finish":
            return {"final_response": args.get("response", "Visual Task complete."), "next_agent": "FINISH"}
        else:
            result_str = f"Unknown tool requested: {tool}"
            
        return {
            "final_response": f"Vision Action -> {tool} executed: {result_str}",
            "next_agent": "FINISH"  # Returning FINISH for the scaffold. A full RPA loop would route back to 'vision_agent'.
        }
        
    except Exception as e:
        return {"final_response": f"Vision Agent failed: {e}", "next_agent": "FINISH"}

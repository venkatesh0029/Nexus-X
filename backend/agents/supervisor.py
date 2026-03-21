import json
import logging
import traceback
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from backend.llm.factory import LLMFactory
from .state import AgentState

def supervisor_node(state: AgentState):
    """
    Acts as the main router. Analyzes the user's request and delegates 
    it to the most appropriate specialized sub-agent.
    """
    llm = LLMFactory.get_model()
    
    # Define available agents and their specialties
    system_prompt = """You are the Supervisor of JARVIS-X, a multi-agent AI system.
Your job is to read the user's request and decide which specialized worker agent should handle it.

Available Agents:
1. system_agent - Use ONLY for executing headless CLI terminal commands, file system operations, memory retrieval, or generic conversational tasks. (Default)
2. coding_agent - Use strictly for writing complex scripts, debugging codefiles, or deep software architectures.
3. research_agent - Use when the user asks about current events, news, general knowledge, summarizing web pages, looking up information, or performing web scraping.
4. vision_agent - CRITICAL: Use THIS agent ANY TIME the user asks to click on the screen, type text into a GUI, control the mouse/keyboard, or visually navigate the physical desktop.

Respond ONLY with a valid JSON object in this exact format, with no markdown formatting or extra text:
{"next_agent": "<agent_name>"}

If the task is complete or you just want to reply directly without invoking a tool, use "FINISH".
"""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("user", "{input}")
    ])
    
    last_message = state["messages"][-1].content
    
    try:
        response = llm.invoke(prompt.format_prompt(input=last_message))
        logging.info(f"RAW SUPERVISOR LLM OUTPUT: {response.content}")
        content = response.content.replace("```json", "").replace("```", "").strip()
        
        try:
            decision = json.loads(content)
            if isinstance(decision, dict):
                next_agent = decision.get("next_agent", "system_agent")
            else:
                next_agent = "system_agent"
        except json.JSONDecodeError:
            # Fallback for weak local models
            import re
            match = re.search(r'"next_agent"\s*:\s*"([^"]+)"', content)
            if match:
                next_agent = match.group(1)
            else:
                next_agent = "system_agent"
                
        # Validate agent name
        valid_agents = ["system_agent", "coding_agent", "research_agent", "vision_agent", "FINISH"]
        if next_agent not in valid_agents:
            next_agent = "system_agent"
            
        logging.info(f"Supervisor routed task to: {next_agent}")
        return {"next_agent": next_agent}
        
    except Exception as e:
        logging.error(f"Supervisor failed to parse choice, defaulting to system_agent:\n{traceback.format_exc()}")
        return {"next_agent": "system_agent"}

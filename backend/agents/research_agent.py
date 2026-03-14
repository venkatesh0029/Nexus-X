from langchain_core.prompts import ChatPromptTemplate
from backend.llm.factory import LLMFactory
from .state import AgentState
import logging

def research_agent_node(state: AgentState):
    """
    Dedicated sub-agent for deep research and information synthesis.
    """
    logging.info("Executing Research Agent Node")
    llm = LLMFactory.get_model()
    
    memory_context = state.get("memory_context", "")
    memory_addon = f"\nRelevant Background Knowledge:\n{memory_context}\n" if memory_context else ""
    
    system_prompt = f"""You are the Lead Research agent for JARVIS-X.
Your purpose is to synthesize large amounts of information, analyze documentation, and provide concise, accurate reports.
Structure your findings with clear headings and bullet points.
{memory_addon}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}")
    ])
    
    last_message = state["messages"][-1].content
    
    try:
        response = llm.invoke(prompt.format_prompt(input=last_message))
        
        return {
            "final_response": response.content,
            "next_agent": "FINISH" 
        }
    except Exception as e:
        return {"final_response": f"Research Agent failed: {e}", "next_agent": "FINISH"}

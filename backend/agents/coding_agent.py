from langchain_core.prompts import ChatPromptTemplate
from backend.llm.factory import LLMFactory
from .state import AgentState
import logging

def coding_agent_node(state: AgentState):
    """
    Dedicated sub-agent for complex programming tasks.
    """
    logging.info("Executing Coding Agent Node")
    llm = LLMFactory.get_model()
    
    memory_context = state.get("memory_context", "")
    memory_addon = f"\nRelevant Code/Architecture Context:\n{memory_context}\n" if memory_context else ""
    
    system_prompt = f"""You are the Senior Staff Engineer agent for JARVIS-X.
Your sole purpose is to write, debug, and architecture highly optimized code.
Provide full code blocks with inline comments.

When you are finished, you do not need to call any tools. Just provide the code directly.
{memory_addon}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}")
    ])
    
    last_message = state["messages"][-1].content
    
    try:
        response = llm.invoke(prompt.format_prompt(input=last_message))
        
        # We simulate a "plan" that just has one direct output step to reuse the existing executor structure if we want,
        # or we just return the final response directly. We'll return the final response and skip the tools for purely code-gen tasks.
        return {
            "final_response": response.content,
            "next_agent": "FINISH" 
        }
    except Exception as e:
        return {"final_response": f"Coding Agent failed: {e}", "next_agent": "FINISH"}

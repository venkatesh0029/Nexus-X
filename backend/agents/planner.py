import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from .state import AgentState
from backend.llm.factory import LLMFactory
from backend.memory.plan_store import plan_store
import httpx
import os

# Enable SQLite caching to instantly return identical repeated prompts
cache_path = os.path.join(os.path.dirname(__file__), "..", "llm_cache.db")
set_llm_cache(SQLiteCache(database_path=cache_path))

# Define exponential backoff retry for LLM calls to handle LM Studio/Ollama hiccups
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10), 
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, Exception))
)
def invoke_llm_with_retry(llm, prompt_value):
    return llm.invoke(prompt_value)

def planner_node(state: AgentState):
    """
    Takes the user request and breaks it down into actionable steps.
    Includes a Circuit Breaker pattern for resilience.
    """
    error_count = state.get("error_count", 0)
    
    # Circuit Breaker: If we've failed too many times across the graph, abort.
    if error_count >= 3:
        logging.error("Circuit Breaker OPEN: Aborting graph execution due to persistent failures.")
        return {
            "approval_status": "rejected",
            "final_response": "I've encountered multiple consecutive errors trying to process this request. Let's simplify the task, or could you provide more specific instructions?"
        }
        
    llm = LLMFactory.get_model()
    
    # Load user profile and memory
    memory_context = state.get("memory_context", "")
    persona_addon = f"\nRelevant Memory/Context:\n{memory_context}\n" if memory_context else ""
    
    profile_path = os.path.join(os.path.dirname(__file__), "..", "user_profile.json")
    if os.path.exists(profile_path):
        import json
        try:
            with open(profile_path, "r") as f:
                profile = json.load(f)
                name = profile.get("name", "User")
                tone = profile.get("tone", "helpful")
                persona_addon = f"\nYou are addressing {name}. Please adopt a {tone} tone in your internal reasoning and final output.\n"
        except Exception as e:
                print(f"Failed to load user profile: {e}")
                
    # Escape any curly braces in memory_context to prevent Langchain format errors
    persona_addon = persona_addon.replace("{", "{{").replace("}", "}}")
            
    # Load Plugins
    from backend.plugins.plugin_manager import plugin_manager
    tool_registry = plugin_manager.get_all_tools()
    plugin_tool_descriptions = []
    for t_name, t_data in tool_registry.items():
        desc = t_data['description'].replace('{', '{{').replace('}', '}}')
        plugin_tool_descriptions.append(f"- {t_name} (args: {desc})")
            
    plugin_text = "\n".join(plugin_tool_descriptions)
            
    system_prompt = f"""You are JARVIS-X, an autonomous agent. {persona_addon}
Break down the user's request into actionable steps using a STRICT ReAct format. 
You have access to the following actions:
- system_command (args: {{{{"command": "string"}}}})
- respond_to_user (args: {{{{"text": "string"}}}})
- browser_goto (args: {{{{"url": "string"}}}})
- read_file (args: {{{{"filepath": "string"}}}})
- write_file (args: {{{{"filepath": "string", "content": "string"}}}})
- list_dir (args: {{{{"directory": "string"}}}})
- system_monitor (args: {{{{}}}})
- desktop_type (args: {{{{"text": "string"}}}})
- analyze_screen (args: {{{{"question": "string"}}}})
{plugin_text}

For each step, you MUST respond EXACTLY in this format:
Thought: your reasoning for this step
Action: the Action Name from the list above
Action Input: a valid JSON object containing the arguments

Separate each step with a blank line. Do not include markdown code block formatting like ```json."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}")
    ])
    
    last_message = state["messages"][-1].content
    
    # 1. Check Plan Optimization Cache
    cached_plan = plan_store.get_plan(last_message)
    if cached_plan:
        logging.info("Plan optimization cache hit. Bypassing LLM.")
        return {"plan": cached_plan, "current_step_idx": 0, "error_count": 0}
        
    try:
        response = invoke_llm_with_retry(llm, prompt.format_prompt(input=last_message))
        
        # Parse ReAct blocks
        plan_steps = []
        blocks = response.content.split("Thought:")
        for b in blocks:
            b = b.strip()
            if not b: continue
            plan_steps.append("Thought: " + b)
        
        if not plan_steps:
            plan_steps = ["Thought: Process user request\nAction: system_command\nAction Input: {\"command\": \"echo no plan generated\"}"]
        else:
            # 2. Save successful generation to Plan Optimization Cache
            plan_store.save_plan(last_message, plan_steps)
            
        return {"plan": plan_steps, "current_step_idx": 0, "error_count": 0}
        
    except Exception as e:
        logging.error(f"LLM Invocation failed after retries: {e}")
        return {
            "error_count": error_count + 1,
            "plan": [],
            "approval_status": "rejected",
            "final_response": f"Failed to generate plan due to LLM error: {e}"
        }

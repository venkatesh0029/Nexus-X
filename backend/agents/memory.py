from langchain_core.messages import SystemMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState
from backend.memory.vector_store import VectorMemoryStore
from backend.memory.semantic_graph import SemanticMemoryGraph
from backend.llm.factory import LLMFactory

episodic_store = VectorMemoryStore()
semantic_store = SemanticMemoryGraph()

def memory_node(state: AgentState):
    """
    Retrieves relevant user context from FAISS and NetworkX, and summarizes old messages.
    """
    if not state.get("messages"):
        return {"memory_context": "No context available."}
        
    latest_message = state["messages"][-1].content
    
    # Query Databases
    episodic_context = episodic_store.search_context(latest_message, n_results=3)
    semantic_context = semantic_store.query_facts(latest_message)
    
    context = f"{semantic_context}\n\n{episodic_context}".strip()
    
    # Extract Semantic Facts from new user messages
    last_msg = state["messages"][-1]
    if last_msg.type == "human":
        fact_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract any explicit user preferences, personal details, or permanent architectural facts from the user's message. Format each on a new line as: FACT: Subject -> predicate -> Object\nIf none are present, output NONE."),
            ("user", "{input}")
        ])
        try:
            llm = LLMFactory.get_model()
            fact_response = llm.invoke(fact_prompt.format_prompt(input=last_msg.content))
            if "FACT:" in fact_response.content:
                semantic_store.extract_and_add_fact(fact_response.content)
        except Exception as e:
            print(f"Fact extraction failed: {e}")
            
    # Re-query semantic context if new facts were added
    semantic_context = semantic_store.query_facts(latest_message)
    context = f"{semantic_context}\n\n{episodic_context}".strip()
    
    # Summarization Logic (Compress history if context window is too large)
    messages = state["messages"]
    total_chars = sum(len(m.content) for m in messages if isinstance(m.content, str))
    
    if total_chars > 12000 and len(messages) > 4:
        llm = LLMFactory.get_model()
        # Summarize older messages, leaving the 4 most recent intact
        messages_to_summarize = messages[:-4]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize the following conversation history briefly and concisely. Focus on the user's intent and any key facts established."),
            ("user", "History: {history}")
        ])
        
        history_text = "\n".join([f"{m.type}: {m.content}" for m in messages_to_summarize if m.type in ["human", "ai"]])
        
        try:
            summary_response = llm.invoke(prompt.format_prompt(history=history_text))
            summary_msg = SystemMessage(content=f"Previous Conversation Summary: {summary_response.content}")
            
            # Use LangGraph's RemoveMessage to delete old messages from state
            delete_msgs = [RemoveMessage(id=m.id) for m in messages_to_summarize]
            
            # Return updates to state (add the summary message, delete the old ones)
            return {
                "memory_context": context,
                "messages": [summary_msg] + delete_msgs
            }
        except Exception as e:
            # If summarization fails (e.g. LLM timeout), just return the context and skip compression
            print(f"Summarization failed: {e}")
            pass
            
    return {"memory_context": context}

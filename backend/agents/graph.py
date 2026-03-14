import os
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import AgentState
from .planner import planner_node
from .executor import executor_node
from .security import security_node
from .memory import memory_node
from .supervisor import supervisor_node
from .coding_agent import coding_agent_node
from .research_agent import research_agent_node
from .vision_agent import vision_agent_node
from .safety_agent import safety_agent_node

# Set up SQLite checkpointer for Langgraph states
db_path = os.path.join(os.path.dirname(__file__), "..", "checkpoints.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
memory_saver = SqliteSaver(conn)

def build_graph():
    """
    Compiles the main multi-agent orchestration graph with persistence.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("memory", memory_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)    # legacy system_agent
    workflow.add_node("executor", executor_node)
    workflow.add_node("security", security_node)
    workflow.add_node("coding_agent", coding_agent_node)
    workflow.add_node("research_agent", research_agent_node)
    workflow.add_node("vision_agent", vision_agent_node)
    
    workflow.add_node("safety_agent", safety_agent_node)
    
    # Edges
    workflow.set_entry_point("safety_agent")
    
    def check_safety(state: AgentState):
        if not state.get("is_safe", True):
            return END
        return "memory"
        
    workflow.add_conditional_edges("safety_agent", check_safety, {
        "memory": "memory",
        END: END
    })
    
    workflow.add_edge("memory", "supervisor")
    
    # Supervisor routes to specific agents
    def route_supervisor(state: AgentState):
        agent = state.get("next_agent", "system_agent")
        if agent == "coding_agent":
            return "coding_agent"
        elif agent == "research_agent":
            return "research_agent"
        elif agent == "vision_agent":
            return "vision_agent"
        elif agent == "FINISH":
            return END
        else:
            return "planner" # Default/System Agent

    workflow.add_conditional_edges("supervisor", route_supervisor, {
        "coding_agent": "coding_agent",
        "research_agent": "research_agent",
        "vision_agent": "vision_agent",
        "planner": "planner",
        END: END
    })
    
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "security")
    
    # Sub-agents that just output direct answers terminate naturally
    workflow.add_edge("coding_agent", END)
    workflow.add_edge("research_agent", END)
    workflow.add_edge("vision_agent", END)
    
    # Conditional logic based on security status
    def check_approval(state: AgentState):
        status = state.get("approval_status", "pending")
        if status == "rejected":
            return END # Stop execution
        if status == "pending":
            return END # Break to human-in-the-loop
        
        step_idx = state.get("current_step_idx", 0)
        is_autonomous = state.get("is_autonomous", False)
        
        # Hard cycle limit to prevent infinite recursion
        cycle_limit = 100 if is_autonomous else 25
        if step_idx >= cycle_limit:
            return END
            
        # If approved, loop back for next step if available
        if step_idx < len(state.get("plan", [])):
            return "executor"
        return END

    workflow.add_conditional_edges("security", check_approval, {
        "executor": "executor",
        END: END
    })
    
    # Compile with memory checkpointer
    return workflow.compile(checkpointer=memory_saver)

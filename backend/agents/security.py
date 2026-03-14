from .state import AgentState
from backend.security import CommandValidator

validator = CommandValidator()

def security_node(state: AgentState):
    """
    Validates pending tool calls and sets approval status.
    """
    tool_calls = state.get("tool_calls", [])
    if not tool_calls:
        return {"approval_status": "approved"}
        
    overall_status = "approved"
    
    for call in tool_calls:
        if call.get("action") == "system_command":
            cmd = call.get("args", {}).get("command", "")
            status, reason = validator.evaluate(cmd)
            
            if status == "BLOCKED":
                return {
                    "approval_status": "rejected", 
                    "final_response": f"Command blocked by security layer: {reason}"
                }
            elif status == "REQUIRES_APPROVAL":
                overall_status = "pending"
                
    return {"approval_status": overall_status}

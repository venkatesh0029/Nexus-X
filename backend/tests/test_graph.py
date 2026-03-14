import pytest
from backend.agents.planner import planner_node
from langchain_core.messages import HumanMessage, AIMessage

# Mock LLM factory logic
class MockLLM:
    def __init__(self, response_text):
        self.response_text = response_text
        
    def invoke(self, *args, **kwargs):
        return AIMessage(content=self.response_text)

@pytest.fixture
def mock_planner(monkeypatch):
    """Mocks the LLMFactory to return deterministic responses for testing."""
    def mock_get_model(*args, **kwargs):
        return MockLLM(
            "Thought: The user wants me to say hello.\n"
            "Action: system_command\n"
            "Action Input: {\"command\": \"echo Hello\"}"
        )
    monkeypatch.setattr("backend.agents.planner.LLMFactory.get_model", mock_get_model)

def test_planner_node_parsing(mock_planner):
    """Test that the planner correctly parses ReAct output from the LLM."""
    state = {
        "messages": [HumanMessage(content="Say Hello")],
        "error_count": 0,
        "plan": [],
        "current_step_idx": 0
    }
    
    new_state = planner_node(state)
    
    assert "plan" in new_state
    assert len(new_state["plan"]) == 1
    assert "Action: system_command" in new_state["plan"][0]
    assert "current_step_idx" in new_state
    assert new_state["current_step_idx"] == 0

def test_circuit_breaker():
    """Test if planner node directly aborts when error count is >= 3."""
    state = {
        "messages": [HumanMessage(content="Hello")],
        "error_count": 3
    }
    new_state = planner_node(state)
    assert new_state.get("approval_status") == "rejected"
    assert "multiple consecutive errors" in new_state.get("final_response", "")

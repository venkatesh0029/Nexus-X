# JARVIS-X Plugin Developer Guide

Welcome to the JARVIS-X ecosystem! This guide will teach you how to create custom tools and capabilities that inject seamlessly into the JARVIS-X reasoning loop.

JARVIS-X uses a dynamic plugin loader that automatically scans the `backend/plugins/` directory at startup.

## Creating a Plugin

1. Navigate to the `backend/plugins/` directory.
2. Create a new Python file ending in `_plugin.py` (e.g. `smart_home_plugin.py`).
3. Your file MUST import and subclass the `JarvisPlugin` base interface.

### The `JarvisPlugin` Interface

Here is a minimum viable example:

```python
from backend.plugins import JarvisPlugin

class HelloPlugin(JarvisPlugin):
    # These properties are required metadata
    name = "HelloPlugin"
    description = "Provides a greeting tool."

    def say_hello(self, target_name: str) -> str:
        \"\"\"
        The actual python function that performs the action.
        Must return a string for the LLM to read.
        \"\"\"
        return f"Hello, {target_name}! Welcome to JARVIS-X."

    def get_tools(self) -> list[dict]:
        \"\"\"
        This function registers your tools with the LLM and the Executor node.
        \"\"\"
        return [
            {
                "name": "say_hello_tool",
                "description": "- say_hello_tool (args: {{\\"target_name\\": \\"string\\"}}) - Greets a user.",
                "callable": self.say_hello
            }
        ]
```

### Security Considerations

When a user prompts JARVIS-X to execute a plugin action, the system evaluates the risk. Currently, all custom plugin tools are categorized with a **medium** risk level by the `Security Gateway`, meaning they will be queued in the UI for user approval before execution.

If your plugin interacts with internal networks (like a Home Assistant bridge) or deletes data, ensure your logic gracefully catches network timeouts and exceptions so it doesn't crash the main LangGraph execution loop.

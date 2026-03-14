import os
import importlib
import inspect
import logging

class JarvisPlugin:
    """
    Base class for JARVIS-X Plugins.
    All plugins must inherit from this class and implement `get_tools()`.
    """
    name: str = "BasePlugin"
    description: str = "A basic plugin interface"
    
    def get_tools(self) -> list[dict]:
        """
        Returns a list of tools provided by the plugin.
        Each tool should be a dictionary with:
        - 'name': The action name (e.g., 'get_local_weather')
        - 'description': String describing the tool and its arguments for the LLM
        - 'callable': The actual python function to execute
        """
        return []

def load_plugins():
    """Dynamically loads all plugins in the `backend/plugins` directory."""
    plugins_dir = os.path.dirname(__file__)
    loaded_plugins = []
    
    for filename in os.listdir(plugins_dir):
        if filename.endswith("_plugin.py") and not filename.startswith("__"):
            module_name = f"backend.plugins.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, JarvisPlugin) and obj != JarvisPlugin:
                        loaded_plugins.append(obj())
                        logging.getLogger().info(f"Loaded plugin: {obj.name}")
            except Exception as e:
                logging.getLogger().error(f"Failed to load plugin {module_name}: {e}")
                
    return loaded_plugins

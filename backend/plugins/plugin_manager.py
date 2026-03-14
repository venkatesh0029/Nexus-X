import os
import importlib
import inspect
import sys
import logging

class PluginManager:
    """
    Manages dynamic loading, hot-reloading, and registry of all JARVIS-X plugins.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        self.plugins_dir = os.path.dirname(__file__)
        self.active_plugins = {}  # { module_name: plugin_instance }
        self.tool_registry = {}   # { tool_name: { 'callable': func, 'description': str, 'plugin': str } }
        self._loaded = False
        
    def reload_plugins(self):
        """Scans the plugins directory and hot-reloads all available plugins."""
        logging.info("Scanning for plugins...")
        new_active_plugins = {}
        new_tool_registry = {}
        
        # We still respect the base class approach for backwards compatibility or explicit inheritance
        from backend.plugins import JarvisPlugin
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith("_plugin.py") and not filename.startswith("__"):
                module_name = f"backend.plugins.{filename[:-3]}"
                
                try:
                    # If module already loaded, explicitly reload it
                    if module_name in sys.modules:
                        module = importlib.reload(sys.modules[module_name])
                    else:
                        module = importlib.import_module(module_name)
                        
                    # Find plugin classes
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, JarvisPlugin) and obj != JarvisPlugin:
                            instance = obj()
                            new_active_plugins[module_name] = instance
                            
                            # Register tools
                            tools = instance.get_tools()
                            for t in tools:
                                new_tool_registry[t["name"]] = {
                                    "callable": t["callable"],
                                    "description": t.get("description", ""),
                                    "plugin": instance.name
                                }
                            logging.info(f"Loaded plugin via OOP: {instance.name}")
                            
                    # Find functional tools (decorated with @plugin_tool)
                    # For future-proofing as requested by V3 architecture
                    if hasattr(module, "JARVIS_TOOLS"):
                        for tool_name, tool_data in module.JARVIS_TOOLS.items():
                            new_tool_registry[tool_name] = {
                                "callable": tool_data["callable"],
                                "description": tool_data["description"],
                                "plugin": module_name
                            }
                            logging.info(f"Loaded functional tool: {tool_name}")
                            
                except Exception as e:
                    logging.error(f"Failed to load plugin {module_name}: {e}")
                    
        self.active_plugins = new_active_plugins
        self.tool_registry = new_tool_registry
        self._loaded = True
        logging.info(f"Plugin reload complete. {len(self.tool_registry)} tools registered.")
        
    def get_all_tools(self):
        if not self._loaded:
            self.reload_plugins()
        return self.tool_registry
        
    def get_plugin_metadata(self):
        """Returns JSON-serializable info for the React frontend."""
        if not self._loaded:
            self.reload_plugins()
        return [
            {
                "module": mod_name,
                "name": getattr(instance, "name", mod_name),
                "description": getattr(instance, "description", ""),
                "tools": [
                    {"name": t_name, "description": t_data["description"]} 
                    for t_name, t_data in self.tool_registry.items() 
                    if t_data["plugin"] == getattr(instance, "name", mod_name)
                ]
            }
            for mod_name, instance in self.active_plugins.items()
        ]

# Global access
plugin_manager = PluginManager()

# Decorator for functional plugin registration
def plugin_tool(name: str, description: str):
    """
    Decorator to easily register a function as a JARVIS-X tool.
    Example:
    @plugin_tool(name="github_search", description="Search github repos")
    def search_github(query: str): ...
    """
    def decorator(func):
        # We inject this into the module's JARVIS_TOOLS dict so the manager can find it
        mod = sys.modules[func.__module__]
        if not hasattr(mod, "JARVIS_TOOLS"):
            mod.JARVIS_TOOLS = {}
        mod.JARVIS_TOOLS[name] = {"callable": func, "description": description}
        return func
    return decorator

from . import JarvisPlugin
import random

class WeatherPlugin(JarvisPlugin):
    name = "WeatherPlugin"
    description = "Provides local weather information."
    
    def get_local_weather(self, location: str) -> str:
        """Mock tool to fetch weather."""
        # In a real plugin, this would call an external API like OpenWeatherMap
        conditions = ["Sunny", "Cloudy", "Raining", "Snowing", "Clear"]
        temp = random.randint(40, 95)
        return f"The current weather in {location} is {random.choice(conditions)} and {temp} degrees."
        
    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "get_local_weather",
                "description": "- get_local_weather (args: {{\"location\": \"string\"}})",
                "callable": self.get_local_weather
            }
        ]

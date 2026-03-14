import os

class FileSystemTools:
    @staticmethod
    def read_file(filepath: str) -> str:
        """Reads contents of a local file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return content[:5000] # Truncate to prevent context overflow
        except Exception as e:
            return f"Error reading file {filepath}: {e}"

    @staticmethod
    def write_file(filepath: str, content: str) -> str:
        """Writes given content to a file."""
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing to file {filepath}: {e}"

    @staticmethod
    def list_dir(directory: str) -> str:
        """Lists files and folders inside a given directory."""
        try:
            items = os.listdir(directory)
            if not items:
                return f"Directory {directory} is empty."
            return f"Contents of {directory}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory {directory}: {e}"

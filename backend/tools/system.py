import subprocess
import yaml
import os
import docker
from docker.errors import DockerException, NotFound
from typing import Dict, Any

class SystemCommandTool:
    """
    Executes raw system commands locally or within a Docker sandbox.
    """
    
    def __init__(self, use_sandbox: bool = None):
        self.config = self._load_config()
        self.use_sandbox = use_sandbox if use_sandbox is not None else self.config.get("security", {}).get("docker_sandbox", {}).get("enabled", False)
        self.sandbox_image = self.config.get("security", {}).get("docker_sandbox", {}).get("image", "python:3.11-slim")
        
        if self.use_sandbox:
            try:
                self.client = docker.from_env()
            except DockerException as e:
                print(f"[Warning] Docker is not available or running. Sandbox execution will fail. Error: {e}")
                self.client = None

    def _load_config(self) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception:
            return {}
        
    def execute(self, command: str) -> str:
        if self.use_sandbox:
            if not self.client:
                return f"Error: Docker sandbox is enabled but Docker daemon is not accessible."
                
            try:
                # Ephemeral, hardened container execution
                output = self.client.containers.run(
                    self.sandbox_image,
                    command=["timeout", "10s", "sh", "-c", command],
                    remove=True,
                    read_only=True,
                    tmpfs={'/tmp': ''},
                    cap_drop=['ALL'],
                    network_mode='none',
                    mem_limit='256m',
                    nano_cpus=int(0.5 * 1e9),
                    user="1000:1000",
                    stdout=True,
                    stderr=True
                )
                
                result = output.decode('utf-8') if isinstance(output, bytes) else str(output)
                return f"[Isolated Sandbox] " + (result if result.strip() else "Command executed successfully with no output.")
            except docker.errors.ContainerError as e:
                # Command returned non-zero exit status
                stderr = e.stderr.decode('utf-8') if e.stderr else str(e)
                return f"[Sandbox Execution Failed]\n{stderr}"
            except Exception as e:
                return f"[Sandbox Error] Failed to execute in container: {str(e)}"
            
        # Local host execution
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
                
            return output if output.strip() else "Command executed successfully with no output."
        except Exception as e:
            return f"Error executing command: {str(e)}"

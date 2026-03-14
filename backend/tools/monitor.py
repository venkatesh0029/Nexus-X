import psutil
import json

class SystemMonitorTool:
    @staticmethod
    def get_system_metrics() -> str:
        """Returns current CPU usage, available RAM, and process count."""
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            procs = len(psutil.pids())
            metrics = {
                "cpu_percent": cpu,
                "ram_available_gb": round(ram.available / (1024 ** 3), 2),
                "ram_total_gb": round(ram.total / (1024 ** 3), 2),
                "active_processes": procs
            }
            return json.dumps(metrics, indent=2)
        except Exception as e:
            return f"Failed to get system metrics: {e}"

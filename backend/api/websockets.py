from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.agents.graph import build_graph
from langchain_core.messages import HumanMessage
import json
import asyncio
import time
import psutil

router = APIRouter()
graph = build_graph()

class RateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.clients = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.clients:
            self.clients[client_id] = []
        self.clients[client_id] = [t for t in self.clients[client_id] if now - t < self.window]
        if len(self.clients[client_id]) >= self.limit:
            return False
        self.clients[client_id].append(now)
        return True

ws_limiter = RateLimiter(limit=10, window=60) # 10 execution req per minute

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass
            
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass

manager = ConnectionManager()

async def broadcast_system_vitals():
    """Background task to poll system metrics and broadcast to all connected clients."""
    while True:
        try:
            if manager.active_connections:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                await manager.broadcast({
                    "type": "system_vitals",
                    "cpu": cpu,
                    "ram": ram
                })
        except Exception as e:
            print(f"Error broadcasting vitals: {e}")
        await asyncio.sleep(2)

task_queue = asyncio.Queue()

async def execute_graph(user_input: str, websocket: WebSocket, thread_id: str, manager: ConnectionManager, is_autonomous: bool):
    await manager.send_personal_message({"type": "status", "message": f"Processing user request: {user_input}"}, websocket)
    
    # Initialize state
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "plan": [],
        "current_step_idx": 0,
        "tool_calls": [],
        "approval_status": "none",
        "memory_context": "",
        "final_response": "",
        "is_autonomous": is_autonomous,
        "is_safe": True
    }
    
    # Keep track of final output to save to memory
    final_plan_text = ""
    last_tool_calls = []
    step_idx_to_send = 0
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Using .stream() to get step-by-step updates
    for output in graph.stream(initial_state, config=config):
        for node_name, state_update in output.items():
            # Notify frontend which node is active
            await manager.send_personal_message({
                "type": "node_active",
                "node": node_name
            }, websocket)
            
            if "final_response" in state_update and state_update["final_response"] and node_name not in ["security", "safety_agent"]:
                await manager.send_personal_message({
                    "type": "ai_response",
                    "message": str(state_update["final_response"])
                }, websocket)

            if node_name == "supervisor":
                next_agent = state_update.get("next_agent", "system_agent")
                await manager.send_personal_message({
                    "type": "thought",
                    "message": f"[SUPERVISOR] Delegated task to: {next_agent}"
                }, websocket)
                
            elif node_name == "planner":
                plan = state_update.get("plan", [])
                final_plan_text = "\\n".join(plan)
                await manager.send_personal_message({
                    "type": "thought",
                    "message": f"System Agent created a plan with {len(plan)} steps."
                }, websocket)
                
            elif node_name == "executor":
                step_idx = state_update.get("current_step_idx", 1) - 1 # it was incremented
                plan = state_update.get("plan", [])
                
                if step_idx < len(plan):
                    step_desc = plan[step_idx]
                    step_idx_to_send = step_idx
                    await manager.send_personal_message({
                        "type": "thought",
                        "message": f"Executing step: {step_desc}"
                    }, websocket)
                
                tool_calls = state_update.get("tool_calls", [])
                if tool_calls:
                    last_tool_calls = tool_calls
                    await manager.send_personal_message({
                        "type": "node_active",
                        "node": "tools"
                    }, websocket)
                    
            elif node_name == "security":
                approval_status = state_update.get("approval_status", "none")
                
                if approval_status == "rejected":
                    final_response = state_update.get("final_response", "Command blocked by security.")
                    await manager.send_personal_message({
                        "type": "status",
                        "message": final_response
                    }, websocket)
                elif approval_status == "pending" and last_tool_calls:
                    tc = last_tool_calls[0]
                    await manager.send_personal_message({
                        "type": "approval_required",
                        "action": tc.get("action", "unknown"),
                        "command": str(tc.get("args", {})),
                        "id": f"cmd-{step_idx_to_send}",
                        "riskLevel": tc.get("riskLevel", "medium")
                    }, websocket)

    # Mark end node
    await manager.send_personal_message({
         "type": "node_active",
         "node": None
    }, websocket)

    # After stream finishes, save interaction to memory
    try:
        from backend.agents.memory import episodic_store, semantic_store
        session_id = str(id(websocket)) # crude session id for scaffold
        episodic_store.add_interaction(session_id, user_input, final_plan_text)
        semantic_store.extract_and_add_fact(final_plan_text)
    except Exception as e:
        print(f"Failed to save to memory: {e}")

async def background_worker_loop():
    while True:
        task = await task_queue.get()
        try:
            await execute_graph(
                task["user_input"], 
                task["websocket"], 
                task["thread_id"], 
                task["manager"], 
                task["is_autonomous"]
            )
        except Exception as e:
            print(f"Goal worker failed: {e}")
        finally:
            task_queue.task_done()

worker_started = False

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global worker_started
    if not worker_started:
        asyncio.create_task(background_worker_loop())
        worker_started = True

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                # expecting JSON from frontend
                payload = json.loads(data)
                user_input = str(payload.get("message", ""))
                
                # if frontend sends explicit approval/rejection
                action = payload.get("action")
                if action in ["approve", "reject"]:
                    await manager.send_personal_message({"type": "status", "message": f"User {action}d the action. Resuming graph..."}, websocket)
                    # For a real implementation, we would need to load the paused state and resume it.
                    # As a scaffold, we'll just log it for now.
                    continue
                    
            except json.JSONDecodeError:
                user_input = str(data)
            
            if not user_input:
                continue
                
            # Rate Limit check
            client_ip = websocket.client.host if websocket.client else "unknown"
            if not ws_limiter.is_allowed(client_ip):
                await manager.send_personal_message({"type": "status", "message": "[SECURITY] Execution rate limit exceeded (10 requests/min). Please wait."}, websocket)
                continue
                
            is_autonomous = False
            if user_input.startswith("/goal ") or user_input.startswith("/goal"):
                user_input = user_input.replace("/goal", "").strip()
                is_autonomous = True
                await manager.send_personal_message({"type": "status", "message": f"Autonomous Goal Queued: {user_input}"}, websocket)
                await task_queue.put({
                    "user_input": user_input,
                    "websocket": websocket,
                    "thread_id": str(id(websocket)),
                    "manager": manager,
                    "is_autonomous": is_autonomous
                })
                continue
                
            # If not a goal, execute immediately
            await execute_graph(user_input, websocket, str(id(websocket)), manager, False)
                            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

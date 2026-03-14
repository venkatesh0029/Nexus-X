import React, { useState, useEffect, useRef } from 'react';
import CommandApproval from './components/CommandApproval';
import LangGraphVisualizer from './components/LangGraphVisualizer';
import AgentTimeline from './components/AgentTimeline';

function App() {
  const [logs, setLogs] = useState([]);
  const [agentThoughts, setAgentThoughts] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [activeNode, setActiveNode] = useState(null);
  const [vitals, setVitals] = useState({ cpu: 0, ram: 0 });
  const [isRecording, setIsRecording] = useState(false);
  const logsEndRef = useRef(null);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    // Establish WebSocket Connection
    wsRef.current = new WebSocket('ws://localhost:8000/ws');

    wsRef.current.onopen = () => {
      setIsConnected(true);
      setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'status', message: 'WebSocket Connected to JARVIS-X Core' }]);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'approval_required') {
        setPendingApprovals((prev) => [...prev, data]);
      } else if (data.type === 'node_active') {
        setActiveNode(data.node);
      } else if (data.type === 'system_vitals') {
        setVitals({ cpu: data.cpu, ram: data.ram });
      } else if (data.type === 'thought' || (data.message && data.message.startsWith('['))) {
         // Direct backend execution blocks to the Timeline
         setAgentThoughts((prev) => [...prev, data.message]);
      } else {
         // User-facing chat logs
         setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), ...data }]);
      }
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'alert', message: 'WebSocket Disconnected' }]);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleApprove = (id) => {
    const approvedItem = pendingApprovals.find(req => req.id === id);
    if (!approvedItem) return;

    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'action', message: `Executing command: ${approvedItem.command}` }]);
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({ action: 'approve', id }));
    }
    setPendingApprovals((prev) => prev.filter(req => req.id !== id));
  };

  const handleReject = (id) => {
    const rejectedItem = pendingApprovals.find(req => req.id === id);
    if (!rejectedItem) return;

    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'alert', message: `User aborted execution of ${rejectedItem.command}` }]);
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({ action: 'reject', id }));
    }
    setPendingApprovals((prev) => prev.filter(req => req.id !== id));
  };

  const handleBatchApprove = () => {
    pendingApprovals.forEach(req => {
        setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'action', message: `Batch Executing: ${req.command}` }]);
        if (wsRef.current && isConnected) {
          wsRef.current.send(JSON.stringify({ action: 'approve', id: req.id }));
        }
    });
    setPendingApprovals([]);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        
        setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'status', message: 'Transcribing audio...' }]);
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.wav');
        
        try {
          const res = await fetch('http://localhost:8000/voice/transcribe', {
            method: 'POST',
            body: formData,
          });
          const result = await res.json();
          if (result.text) {
             setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'audio', message: `[VOICE INPUT]: "${result.text}"` }]);
             if (wsRef.current && isConnected) {
               wsRef.current.send(JSON.stringify({ message: result.text }));
             }
          } else {
             setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'alert', message: `Transcription failed: ${result.reason || 'Unknown error'}` }]);
          }
        } catch (err) {
          setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'alert', message: 'Failed to connect to transcription server' }]);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
      setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'alert', message: 'Microphone access denied' }]);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Optimistic UI update
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'audio', message: `[USER INPUT]: "${inputValue}"` }]);

    // Send over WebSocket
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({ message: inputValue }));
    }

    setInputValue('');
  };

  const getLogStyle = (type) => {
    switch (type) {
      case 'status': return 'text-cyan-400';
      case 'audio': return 'text-fuchsia-400 font-medium';
      case 'thought': return 'text-gray-400 italic';
      case 'action': return 'text-emerald-400 font-bold';
      case 'alert': return 'text-rose-500 font-bold';
      default: return 'text-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-gray-900 to-black text-gray-100 flex flex-col items-center py-10 px-4">
      <header className="w-full max-w-6xl mb-6 flex justify-between items-end border-b border-white/10 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-widest">JARVIS-X</h1>
          <p className="text-sm text-cyan-500 font-mono tracking-widest uppercase mt-1">Autonomous Operations Center</p>
        </div>
        <div className={`text-sm font-mono flex items-center bg-black/40 px-3 py-1.5 rounded-full border border-white/5 ${isConnected ? 'text-emerald-400' : 'text-rose-500'}`}>
          <span className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></span>
          {isConnected ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
        </div>
      </header>

      <main className="w-full max-w-6xl flex flex-col lg:flex-row gap-6">

        {/* Action Panel (Chat & Input) */}
        <div className="flex-[0.4] bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-2xl flex flex-col h-[700px] overflow-hidden">
          <div className="bg-black/40 border-b border-white/10 px-4 py-3 font-mono text-cyan-500 text-xs tracking-widest uppercase flex items-center justify-between">
            <span>Communication Link</span>
            <span className="text-gray-500 hidden sm:inline">SECURE</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-sm">
            {logs.length === 0 ? (
              <div className="text-gray-400 italic text-center mt-10">Awaiting input...</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className={`flex items-start ${getLogStyle(log.type)}`}>
                  <span className="text-gray-400 text-xs mr-4 mt-1 min-w-[80px]">{log.time}</span>
                  <span>{log.message}</span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
          <div className="border-t border-white/10 p-3 bg-black/40">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <button
                type="button"
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onMouseLeave={stopRecording}
                className={`flex-none px-4 py-2 text-white font-medium text-sm rounded-md transition-all shadow-lg ${isRecording ? 'bg-rose-600 animate-pulse shadow-rose-500/50' : 'bg-gray-700 hover:bg-gray-600'}`}
                title="Hold to speak"
                disabled={!isConnected}
              >
                {isRecording ? 'Listening...' : '🎤 PTT'}
              </button>
              <div className="flex-1 flex shadow-sm">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type to command JARVIS..."
                  className="flex-1 bg-black/50 text-gray-100 px-4 py-2 border border-white/10 border-r-0 rounded-l-md focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 text-sm placeholder-gray-500"
                  disabled={!isConnected}
                />
                <button type="submit" disabled={!isConnected} className="bg-cyan-600 text-white px-6 py-2 rounded-r-md text-sm font-medium hover:bg-cyan-500 disabled:opacity-50 transition-colors shadow-lg shadow-cyan-500/20">
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Middle Panel (Timeline) */}
        <div className="flex-[0.4] h-[700px] shadow-2xl">
            <AgentTimeline thoughts={agentThoughts} />
        </div>

        {/* Right Sidebar (Visualizer, Vitals, Security) */}
        <div className="flex-[0.3] flex flex-col gap-6 max-h-[700px]">
          
          {/* LangGraph Visualizer */}
          <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-2xl flex flex-col h-[300px] overflow-hidden">
             <div className="bg-black/40 border-b border-white/10 px-4 py-3 font-mono text-cyan-500 text-xs tracking-widest uppercase flex justify-between items-center">
                <span>Execution Graph</span>
                {activeNode && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded-full animate-pulse border border-emerald-500/30">RUNNING</span>}
             </div>
             <div className="flex-1 w-full bg-black/20 relative">
                 <LangGraphVisualizer activeNode={activeNode} />
             </div>
          </div>

          <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-2xl p-5 hidden lg:block">
            <h3 className="font-mono text-cyan-500 text-xs tracking-widest uppercase mb-4">System Vitals</h3>
            <div className="text-sm space-y-5">
              
              {/* CPU Progress Bar */}
              <div>
                  <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-gray-400 font-medium">CPU USAGE</span>
                      <span className="font-mono text-cyan-400">{vitals.cpu}%</span>
                  </div>
                  <div className="w-full bg-black/50 rounded-full h-1.5 border border-white/5">
                      <div className={`h-1.5 rounded-full ${vitals.cpu > 80 ? 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]' : 'bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]'}`} style={{ width: `${vitals.cpu}%`, transition: 'width 0.5s ease-in-out' }}></div>
                  </div>
              </div>

              {/* RAM Progress Bar */}
              <div>
                  <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-gray-400 font-medium">RAM ALLOCATION</span>
                      <span className="font-mono text-fuchsia-400">{vitals.ram}%</span>
                  </div>
                  <div className="w-full bg-black/50 rounded-full h-1.5 border border-white/5">
                      <div className={`h-1.5 rounded-full ${vitals.ram > 85 ? 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]' : 'bg-fuchsia-500 shadow-[0_0_10px_rgba(217,70,239,0.5)]'}`} style={{ width: `${vitals.ram}%`, transition: 'width 0.5s ease-in-out' }}></div>
                  </div>
              </div>

              <div className="flex justify-between mt-4 pt-4 border-t border-white/10">
                <span className="text-gray-500 text-xs font-mono uppercase tracking-wider">Provider Network</span>
                <span className="font-medium text-emerald-400 text-xs text-right animate-pulse">LM STUDIO : ONLINE</span>
              </div>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-2xl flex-1 flex flex-col overflow-hidden">
            <div className={`px-4 py-3 font-mono text-xs tracking-widest uppercase border-b ${pendingApprovals.length > 0 ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-black/40 text-cyan-500 border-white/10'}`}>
              Security Gateway {pendingApprovals.length > 0 && `(${pendingApprovals.length} PENDING)`}
            </div>
            <div className="flex-1 p-4 flex flex-col justify-center">
                <CommandApproval
                  pendingApprovals={pendingApprovals}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  onBatchApprove={handleBatchApprove}
                />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

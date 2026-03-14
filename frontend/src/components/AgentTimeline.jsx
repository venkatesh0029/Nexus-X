import React, { useRef, useEffect } from 'react';

export default function AgentTimeline({ thoughts }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thoughts]);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0a] text-gray-300 font-mono text-sm border border-gray-800 rounded-lg overflow-hidden shadow-2xl relative">
      <div className="bg-[#111111] border-b border-gray-800 px-4 py-2 flex items-center justify-between sticky top-0 z-10">
        <h3 className="font-semibold text-gray-400 tracking-wider text-xs">AGENT EXECUTION TIMELINE</h3>
        <div className="flex space-x-2">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {thoughts.length === 0 ? (
          <div className="text-gray-600 italic text-center mt-10">Awaiting task delegation...</div>
        ) : (
          thoughts.map((log, index) => {
              // Parse out the tag if it exists (e.g. [THOUGHT], [NODE], [STATUS])
              let tag = "LOG";
              let content = log;
              let bgColor = "bg-gray-800 bg-opacity-40";
              let textColor = "text-gray-400";
              let borderLeft = "border-l-2 border-gray-600";
              
              const match = content.match(/^\[(.*?)\] (.*)/s);
              if (match) {
                  tag = match[1];
                  content = match[2];
                  
                  if (tag === "THOUGHT") {
                      bgColor = "bg-blue-900 bg-opacity-20";
                      textColor = "text-blue-300";
                      borderLeft = "border-l-2 border-blue-500";
                  } else if (tag === "ACTION") {
                      bgColor = "bg-orange-900 bg-opacity-20";
                      textColor = "text-orange-300";
                      borderLeft = "border-l-2 border-orange-500";
                  } else if (tag === "NODE") {
                      bgColor = "bg-purple-900 bg-opacity-20";
                      textColor = "text-purple-300";
                      borderLeft = "border-l-2 border-purple-500";
                  } else if (tag === "STATUS") {
                      bgColor = "bg-green-900 bg-opacity-20";
                      textColor = "text-green-300";
                      borderLeft = "border-l-2 border-green-500";
                  } else if (tag === "ERROR") {
                      bgColor = "bg-red-900 bg-opacity-20";
                      textColor = "text-red-400";
                      borderLeft = "border-l-2 border-red-500";
                  }
              }

              return (
                <div key={index} className={`flex items-start ${bgColor} ${borderLeft} rounded-r-md px-3 py-2 shadow-sm transition-all duration-300 hover:bg-opacity-40`}>
                  <div className="min-w-[70px] mr-3 font-bold text-[10px] uppercase tracking-widest opacity-70 mt-0.5">
                    {tag}
                  </div>
                  <div className={`flex-1 whitespace-pre-wrap ${textColor}`}>
                    {content}
                  </div>
                </div>
              );
          })
        )}
        <div ref={endRef} />
      </div>

      <style jsx="true">{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0a0a0a;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #333;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #555;
        }
      `}</style>
    </div>
  );
}

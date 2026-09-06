import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

export default function ModelActivityLog({ logs }) {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="bg-[#0f172a] rounded-xl shadow-lg border border-slate-700 overflow-hidden flex flex-col h-full">
      <div className="bg-[#1e293b] px-4 py-3 flex items-center justify-between border-b border-slate-700">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500"></div>
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <Terminal className="w-4 h-4" />
          <span className="text-xs font-mono font-medium tracking-wider">AI_ROUTER_LOG</span>
        </div>
        <div className="w-12"></div> {/* Spacer for centering */}
      </div>
      
      <div 
        ref={scrollRef}
        className="p-5 flex-1 overflow-y-auto font-mono text-sm space-y-2 h-[300px]"
      >
        {logs.length === 0 ? (
          <p className="text-slate-500 italic">Waiting for activity...</p>
        ) : (
          logs.map((log, index) => {
            let textColor = "text-slate-300";
            if (log.includes("[ROUTER]")) textColor = "text-blue-400";
            if (log.includes("[GEMINI]") || log.includes("[GROK]")) textColor = "text-emerald-400";
            if (log.includes("ERROR") || log.includes("FALLBACK")) textColor = "text-amber-400";
            if (log.includes("VALIDATED")) textColor = "text-fuchsia-400";

            return (
              <div key={index} className="flex gap-3 items-start animate-fade-in-up">
                <span className="text-slate-600 select-none shrink-0">
                  {new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
                </span>
                <span className={`${textColor} break-words`}>{log}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

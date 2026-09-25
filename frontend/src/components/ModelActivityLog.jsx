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
    <div className="bg-white/[0.02] backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/[0.05] overflow-hidden flex flex-col h-full relative">
      {/* Subtle top glow */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-pink-500/20 to-transparent"></div>
      
      <div className="px-6 py-5 flex items-center justify-between border-b border-white/[0.05]">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 tracking-wide">
          <Terminal className="w-4 h-4 text-pink-500" />
          SYSTEM ACTIVITY
        </h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
          <span className="text-xs text-slate-500 font-medium tracking-widest uppercase">Live</span>
        </div>
      </div>
      
      <div 
        ref={scrollRef}
        className="p-6 flex-1 overflow-y-auto font-mono text-[13px] space-y-3 h-[300px]"
      >
        {logs.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-slate-500 italic font-sans tracking-wide">Waiting for process initiation...</p>
          </div>
        ) : (
          logs.map((logObj, index) => {
            const logStr = typeof logObj === 'string' ? logObj : logObj.message;
            const timeStr = typeof logObj === 'string' ? new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' }) : logObj.time;
            
            let textColor = "text-slate-300";
            let dotColor = "bg-slate-600";
            
            if (logStr.includes("failed") || logStr.includes("Error")) {
              textColor = "text-red-400";
              dotColor = "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]";
            } else if (logStr.includes("successful") || logStr.includes("completed")) {
              textColor = "text-emerald-400";
              dotColor = "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]";
            } else if (logStr.includes("Uploading") || logStr.includes("Task ID")) {
              textColor = "text-pink-300";
              dotColor = "bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.5)]";
            } else {
              dotColor = "bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.5)]";
            }

            return (
              <div key={index} className="flex gap-4 items-start animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex flex-col items-center mt-1.5 gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${dotColor}`}></div>
                  {index !== logs.length - 1 && <div className="w-[1px] h-4 bg-white/10"></div>}
                </div>
                <div className="flex-1">
                  <span className={`${textColor} break-words leading-relaxed`}>{logStr}</span>
                </div>
                <span className="text-slate-600 select-none shrink-0 text-[11px] mt-0.5 tabular-nums">
                  {timeStr}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

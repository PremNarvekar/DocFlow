import React from 'react';
import { Terminal, Check, X, AlertTriangle } from 'lucide-react';

const ModelActivityLog = ({ logs }) => {
  return (
    <div className="bg-gray-900 rounded-xl shadow-sm border border-gray-800 overflow-hidden text-gray-300 font-mono text-sm">
      <div className="px-4 py-3 border-b border-gray-800 bg-gray-950 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-gray-400" />
          <h2 className="text-sm font-semibold text-gray-200">AI Model Activity</h2>
        </div>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-green-500"></div>
        </div>
      </div>
      
      <div className="p-4 h-64 overflow-y-auto space-y-3">
        {logs.length === 0 ? (
          <div className="text-gray-600 italic">Waiting for activity...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex gap-3">
              <span className="text-gray-500 shrink-0">{log.time}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-blue-400 font-semibold">{log.model}</span>
                  <span className="text-gray-500">|</span>
                  <span className="text-gray-300">{log.task}</span>
                </div>
                
                {log.status === 'SUCCESS' && (
                  <div className="flex items-center gap-1.5 text-green-400 mt-1">
                    <Check className="w-3 h-3" />
                    <span>SUCCESS</span>
                    {log.latency && <span className="text-gray-500 text-xs ml-2">Latency: {log.latency}</span>}
                  </div>
                )}
                
                {log.status === 'FAILED' && (
                  <div className="flex flex-col mt-1">
                    <div className="flex items-center gap-1.5 text-red-400">
                      <X className="w-3 h-3" />
                      <span>FAILED</span>
                    </div>
                    {log.reason && <span className="text-red-300/70 text-xs mt-0.5 ml-4.5">Reason: {log.reason}</span>}
                  </div>
                )}
                
                {log.status === 'FALLBACK' && (
                  <div className="flex items-center gap-1.5 text-yellow-400 mt-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Triggering Fallback...</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ModelActivityLog;

import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, Sparkles } from 'lucide-react';
import FileUploader from './components/FileUploader';
import DocumentHistory from './components/DocumentHistory';
import WorkflowVisualizer from './components/WorkflowVisualizer';
import ModelActivityLog from './components/ModelActivityLog';
import ResultsViewer from './components/MockResultsViewer';
import { uploadDocument, getTaskStatus, askQuestion } from './lib/api';

export default function App() {
  const [appState, setAppState] = useState('idle'); // idle, uploading, processing, complete
  const [logs, setLogs] = useState([]);
  const [taskId, setTaskId] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatQuery, setChatQuery] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const addLog = (message) => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message }]);
  };

  const handleUpload = async (file, provider = "auto") => {
    setAppState('uploading');
    setLogs([]);
    setResultData(null);
    setChatHistory([]);
    addLog(`Uploading ${file.name} (Model: ${provider})...`);
    try {
      const res = await uploadDocument(file, provider);
      addLog(`Upload successful. Task ID: ${res.task_id}`);
      setTaskId(res.task_id);
      setDocumentId(res.document_id);
      setAppState('processing');
    } catch (err) {
      addLog(`Upload failed: ${err.message}`);
      setAppState('idle');
    }
  };

  const handleSelectDocument = (doc) => {
    if (doc.status === 'COMPLETED') {
      setDocumentId(doc.id);
      setTaskId(doc.task_id);
      setAppState('processing'); 
      addLog(`Loaded previous document: ${doc.filename}`);
    } else {
      addLog(`Cannot load document ${doc.filename} (Status: ${doc.status})`);
    }
  };

  useEffect(() => {
    let intervalId;
    if (appState === 'processing' && taskId) {
      intervalId = setInterval(async () => {
        try {
          const statusRes = await getTaskStatus(taskId);
          if (statusRes.status === 'COMPLETED') {
            clearInterval(intervalId);
            setAppState('complete');
            addLog(`Extraction completed successfully.`);
            setDocumentId(statusRes.document_id);
            setResultData(statusRes.result?.extracted_data || statusRes.result);
          } else if (statusRes.status === 'FAILED') {
            clearInterval(intervalId);
            setAppState('idle');
            addLog(`Extraction failed.`);
          } else {
            addLog(`Task status: ${statusRes.status}...`);
          }
        } catch (err) {
          addLog(`Status poll failed: ${err.message}`);
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [taskId, appState]);

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!chatQuery.trim() || !documentId) return;

    const q = chatQuery;
    setChatQuery("");
    setChatHistory(prev => [...prev, { role: 'user', content: q }]);
    setChatLoading(true);

    try {
      const res = await askQuestion(documentId, q);
      setChatHistory(prev => [...prev, { role: 'assistant', content: res.answer, meta: res.metadata }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: `[Error: ${err.message}]` }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent font-sans text-white pb-12">
      {/* Premium Header */}
      <header className="bg-white/[0.02] backdrop-blur-3xl border-b border-white/[0.05] sticky top-0 z-10 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-pink-500 p-2 rounded-xl shadow-[0_0_20px_rgba(236,72,153,0.3)]">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-black italic tracking-tighter text-white">DocFlow</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-slate-400 hidden sm:block">Provider-Agnostic AI Document Intelligence</span>
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 mt-10">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
          
          {/* Left Column: Input & Status */}
          <div className="xl:col-span-4 flex flex-col gap-6">
            <FileUploader 
              onUpload={handleUpload} 
              isUploading={appState === 'uploading' || appState === 'processing'} 
            />
            <DocumentHistory 
              onSelectDocument={handleSelectDocument} 
              currentDocumentId={documentId} 
            />
          </div>

          {/* Right Column: Workflow, Terminal, Results */}
          <div className="xl:col-span-8 flex flex-col gap-6">
            <WorkflowVisualizer currentStep={appState} />
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 min-h-[420px]">
              <div className={`${appState === 'complete' ? 'xl:col-span-1' : 'xl:col-span-2'} transition-all duration-500 ease-in-out h-[500px] xl:h-full`}>
                <ModelActivityLog logs={logs} />
              </div>
              
              {appState === 'complete' && resultData && (
                <div className="xl:col-span-1 flex flex-col gap-6 animate-in fade-in zoom-in-95 duration-500">
                  <div className="flex-1 min-h-[500px]">
                    <ResultsViewer data={resultData} />
                  </div>
                  
                  {/* Chat Interface */}
                  <div className="bg-white/[0.02] backdrop-blur-2xl rounded-2xl shadow-2xl border border-white/[0.05] overflow-hidden flex flex-col h-[500px]">
                    <div className="bg-white/[0.01] border-b border-white/[0.05] px-5 py-4">
                      <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-pink-500" /> Ask Document
                      </h3>
                    </div>
                    
                    <div className="flex-1 p-5 overflow-y-auto space-y-4">
                      {chatHistory.length === 0 ? (
                        <p className="text-sm text-slate-500 italic text-center mt-10">Ask a question about this document.</p>
                      ) : (
                        chatHistory.map((msg, idx) => (
                          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'assistant' && (
                              <div className="w-8 h-8 rounded-full bg-pink-500/20 flex items-center justify-center flex-shrink-0 shadow-[0_0_10px_rgba(236,72,153,0.2)]">
                                <Bot className="w-4 h-4 text-pink-500" />
                              </div>
                            )}
                            <div className={`px-4 py-3 rounded-2xl max-w-[85%] text-sm ${msg.role === 'user' ? 'bg-pink-500 text-white rounded-br-none shadow-[0_4px_14px_0_rgba(236,72,153,0.39)]' : 'bg-white/[0.05] border border-white/10 text-slate-200 rounded-bl-none backdrop-blur-md'}`}>
                              <p className="whitespace-pre-wrap">{msg.content}</p>
                              {msg.meta && (
                                <p className="text-[10px] text-slate-500 mt-2 italic">
                                  {msg.meta.model} • {msg.meta.latency_ms}ms • {msg.meta.chunks_used} chunks
                                </p>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                      {chatLoading && (
                        <div className="flex gap-3">
                          <div className="w-8 h-8 rounded-full bg-pink-500/20 flex items-center justify-center flex-shrink-0 animate-pulse shadow-[0_0_10px_rgba(236,72,153,0.2)]">
                            <Bot className="w-4 h-4 text-pink-500" />
                          </div>
                          <div className="px-4 py-4 rounded-2xl bg-white/[0.05] border border-white/10 rounded-bl-none flex gap-1.5 items-center">
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-75"></div>
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-150"></div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <form onSubmit={handleAskQuestion} className="border-t border-white/[0.05] p-3 bg-white/[0.01] flex gap-2">
                      <input
                        type="text"
                        value={chatQuery}
                        onChange={e => setChatQuery(e.target.value)}
                        placeholder="Type a question..."
                        className="flex-1 px-4 py-2.5 bg-white/[0.05] border border-white/10 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-500/50 focus:border-pink-500 transition-all text-white placeholder-slate-500"
                        disabled={chatLoading}
                      />
                      <button 
                        type="submit" 
                        disabled={!chatQuery.trim() || chatLoading}
                        className="bg-pink-500 hover:bg-pink-400 text-white px-4 py-2.5 rounded-xl transition-all disabled:opacity-50 shadow-[0_4px_14px_0_rgba(236,72,153,0.39)] hover:shadow-[0_6px_20px_rgba(236,72,153,0.23)] disabled:shadow-none"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </form>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import FileUploader from './components/FileUploader';
import AIModelStatus from './components/AIModelStatus';
import WorkflowVisualizer from './components/WorkflowVisualizer';
import ModelActivityLog from './components/ModelActivityLog';
import ResultsViewer from './components/MockResultsViewer';
import DocumentHistory from './components/DocumentHistory';
import Auth from './components/Auth';
import { Layers, LogOut, Send, Bot, User as UserIcon } from 'lucide-react';
import { uploadDocument, getTaskStatus, askQuestion } from './lib/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const [appState, setAppState] = useState('idle'); // idle, uploading, processing, complete
  const [logs, setLogs] = useState([]);
  const [taskId, setTaskId] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [resultData, setResultData] = useState(null);

  // Chat State
  const [chatQuery, setChatQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  const addLog = (msg) => {
    setLogs(prev => [...prev, msg]);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  const handleSelectDocument = (doc) => {
    setLogs([]);
    setResultData(null);
    setChatHistory([]);
    setDocumentId(doc.id);
    setTaskId(doc.task_id);
    setAppState('processing');
    addLog(`Loading history for ${doc.filename}...`);
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setAppState('uploading');
    setLogs([]);
    setResultData(null);
    setTaskId(null);
    setDocumentId(null);
    setChatHistory([]);
    
    addLog(`Uploading ${file.name}...`);
    
    try {
      const res = await uploadDocument(file);
      addLog(`Upload success, task: ${res.task_id}`);
      setTaskId(res.task_id);
      setAppState('processing');
    } catch (err) {
      addLog(`Upload failed: ${err.message}`);
      setAppState('idle');
    }
  };

  useEffect(() => {
    let intervalId;

    if (taskId && appState === 'processing') {
      intervalId = setInterval(async () => {
        try {
          const statusRes = await getTaskStatus(taskId);
          
          if (statusRes.status === 'COMPLETED') {
            clearInterval(intervalId);
            setAppState('complete');
            addLog(`Extraction completed successfully.`);
            setDocumentId(statusRes.document_id);
            setResultData(statusRes.result.extracted_data);
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

  if (!isAuthenticated) {
    return <Auth onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 font-sans text-white pb-12">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-xl border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="bg-pink-600 p-1.5 rounded-lg">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">DocFlow</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-slate-500 hidden sm:block">Provider-Agnostic AI Document Intelligence</span>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-500 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Input & Status */}
          <div className="lg:col-span-4 space-y-6">
            <FileUploader 
              onUpload={handleUpload} 
              isUploading={appState === 'uploading' || appState === 'processing'} 
            />
            <DocumentHistory 
              onSelectDocument={handleSelectDocument} 
              currentDocumentId={documentId} 
            />
            <AIModelStatus />
          </div>

          {/* Right Column: Workflow, Terminal, Results */}
          <div className="lg:col-span-8 flex flex-col space-y-6">
            <WorkflowVisualizer currentStep={appState} />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[420px]">
              <div className={`${appState === 'complete' ? 'lg:col-span-1' : 'lg:col-span-2'} transition-all h-[400px] lg:h-full`}>
                <ModelActivityLog logs={logs} />
              </div>
              
              {appState === 'complete' && resultData && (
                <div className="lg:col-span-1 flex flex-col gap-6 animate-in fade-in slide-in-from-right-4 duration-500">
                  <div className="flex-1 min-h-[400px]">
                    <ResultsViewer data={resultData} />
                  </div>
                  
                  {/* Chat Interface */}
                  <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl shadow-lg shadow-pink-500/5 border border-white/10 overflow-hidden flex flex-col h-[400px]">
                    <div className="bg-slate-950 border-b border-white/10 px-4 py-3">
                      <h3 className="font-semibold text-slate-200 text-sm">Ask Document</h3>
                    </div>
                    
                    <div className="flex-1 p-4 overflow-y-auto space-y-4">
                      {chatHistory.length === 0 ? (
                        <p className="text-sm text-slate-500 italic text-center mt-4">Ask a question about this document.</p>
                      ) : (
                        chatHistory.map((msg, idx) => (
                          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.role === 'assistant' && (
                              <div className="w-8 h-8 rounded-full bg-pink-500/20 flex items-center justify-center flex-shrink-0">
                                <Bot className="w-5 h-5 text-pink-500" />
                              </div>
                            )}
                            <div className={`px-4 py-2 rounded-2xl max-w-[85%] text-sm ${msg.role === 'user' ? 'bg-pink-600 text-white rounded-br-none' : 'bg-slate-800 text-slate-200 rounded-bl-none'}`}>
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
                          <div className="w-8 h-8 rounded-full bg-pink-500/20 flex items-center justify-center flex-shrink-0 animate-pulse">
                            <Bot className="w-5 h-5 text-pink-500" />
                          </div>
                          <div className="px-4 py-3 rounded-2xl bg-slate-800 rounded-bl-none flex gap-1 items-center">
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-75"></div>
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-150"></div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <form onSubmit={handleAskQuestion} className="border-t border-white/10 p-3 bg-slate-900/50 backdrop-blur-xl flex gap-2">
                      <input
                        type="text"
                        value={chatQuery}
                        onChange={e => setChatQuery(e.target.value)}
                        placeholder="Type a question..."
                        className="flex-1 px-3 py-2 border border-white/20 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-pink-500"
                        disabled={chatLoading}
                      />
                      <button 
                        type="submit" 
                        disabled={!chatQuery.trim() || chatLoading}
                        className="bg-pink-600 hover:bg-pink-700 text-white px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
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

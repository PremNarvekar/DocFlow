import React, { useState, useEffect } from 'react';
import FileUploader from './components/FileUploader';
import AIModelStatus from './components/AIModelStatus';
import WorkflowVisualizer from './components/WorkflowVisualizer';
import ModelActivityLog from './components/ModelActivityLog';
import MockResultsViewer from './components/MockResultsViewer';
import { Layers } from 'lucide-react';

export default function App() {
  const [appState, setAppState] = useState('idle'); // idle, uploading, processing, complete
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs(prev => [...prev, msg]);
  };

  const handleUpload = () => {
    setAppState('uploading');
    setLogs([]);
    addLog("> Initializing upload sequence...");
    addLog("[SYSTEM] File received: invoice_acme.pdf (1.2MB)");

    setTimeout(() => {
      setAppState('processing');
      addLog("> Upload complete. Beginning extraction pipeline.");
      addLog("[PIPELINE] PyMuPDF extracting raw text pages [1/1]...");
      
      setTimeout(() => {
        addLog("[ROUTER] task=document_classification");
        addLog("[GROK] Routing classification request to Grok-3-mini...");
        
        setTimeout(() => {
          addLog("[GROK] Result: { \"document_type\": \"invoice\" } (Latency: 412ms)");
          addLog("[ROUTER] task=structured_extraction schema=InvoiceData");
          addLog("[GEMINI] Routing extraction request to Gemini-2.5-Flash...");
          
          setTimeout(() => {
            addLog("[GEMINI] Structured output received (Latency: 825ms)");
            addLog("[PYDANTIC] VALIDATED: InvoiceData schema matches.");
            addLog("> Pipeline complete.");
            setAppState('complete');
          }, 1200);
        }, 800);
      }, 1000);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 pb-12">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="bg-blue-600 p-1.5 rounded-lg">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">DocFlow</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-slate-500 hidden sm:block">Provider-Agnostic AI Document Intelligence</span>
            <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-sm font-semibold text-slate-600 border border-slate-300">
              PN
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Input & Status (4 cols on lg) */}
          <div className="lg:col-span-4 space-y-6">
            <FileUploader 
              onUpload={handleUpload} 
              isUploading={appState === 'uploading' || appState === 'processing'} 
            />
            <AIModelStatus />
          </div>

          {/* Right Column: Workflow, Terminal, Results (8 cols on lg) */}
          <div className="lg:col-span-8 flex flex-col space-y-6">
            <WorkflowVisualizer currentStep={appState} />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[420px]">
              {/* Terminal occupies full width if not complete, or half if complete on large screens */}
              <div className={`${appState === 'complete' ? 'lg:col-span-1' : 'lg:col-span-2'} transition-all h-[400px] lg:h-full`}>
                <ModelActivityLog logs={logs} />
              </div>
              
              {/* Results appear when complete */}
              {appState === 'complete' && (
                <div className="lg:col-span-1 h-full animate-in fade-in slide-in-from-right-4 duration-500">
                  <MockResultsViewer />
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

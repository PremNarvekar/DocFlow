import React, { useState, useEffect } from 'react';
import AIModelStatus from './components/AIModelStatus';
import FileUploader from './components/FileUploader';
import WorkflowVisualizer from './components/WorkflowVisualizer';
import ModelActivityLog from './components/ModelActivityLog';
import ProcessingQueue from './components/ProcessingQueue';
import DocumentCard from './components/DocumentCard';
import NLQueryBox from './components/NLQueryBox';

// Dummy Data
const DUMMY_MODELS = [
  { id: '1', name: 'Grok', provider: 'xAI', status: 'available', tasks: ['Classification', 'Extraction'], latency: '820ms' },
  { id: '2', name: 'Gemini 2.5', provider: 'Google', status: 'available', tasks: ['Extraction', 'RAG'], latency: '1.2s' },
  { id: '3', name: 'Llama 3 70B', provider: 'Groq', status: 'not_configured', tasks: ['Classification'], latency: '--' },
  { id: '4', name: 'Mistral Large', provider: 'Mistral', status: 'not_configured', tasks: ['Extraction'], latency: '--' },
  { id: '5', name: 'Llama 3 8B', provider: 'Cerebras', status: 'available', tasks: ['Classification'], latency: '150ms' },
  { id: '6', name: 'Claude 3.5 Sonnet', provider: 'OpenRouter', status: 'available', tasks: ['RAG', 'Extraction'], latency: '2.1s' },
];

const App = () => {
  const [models, setModels] = useState(DUMMY_MODELS);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(null);
  const [activeModel, setActiveModel] = useState(null);
  const [failedModels, setFailedModels] = useState([]);
  const [logs, setLogs] = useState([]);
  const [documentResult, setDocumentResult] = useState(null);

  const addLog = (log) => {
    setLogs((prev) => [{ time: new Date().toLocaleTimeString(), ...log }, ...prev]);
  };

  const handleUpload = (file) => {
    // Reset state
    setIsProcessing(true);
    setCurrentStep('upload');
    setActiveModel(null);
    setFailedModels([]);
    setLogs([]);
    setDocumentResult(null);

    // Simulate pipeline timeline
    const timeline = [
      { step: 'validation', delay: 1000 },
      { step: 'extraction', delay: 2000 },
      { step: 'classification', delay: 3500 },
      { step: 'ai_router', delay: 4500, action: () => simulateRouter() },
    ];

    let currentDelay = 0;
    timeline.forEach(({ step, delay, action }) => {
      setTimeout(() => {
        setCurrentStep(step);
        if (action) action();
      }, delay);
    });
  };

  const simulateRouter = () => {
    // Mark Grok as active then failed
    setActiveModel('Grok');
    setModels(m => m.map(x => x.name === 'Grok' ? { ...x, status: 'active' } : x));
    
    setTimeout(() => {
      // Grok fails
      addLog({ model: 'Grok', task: 'Classification', status: 'FAILED', reason: 'quota exhausted' });
      addLog({ model: 'Router', task: 'Routing', status: 'FALLBACK' });
      setFailedModels(['Grok']);
      setModels(m => m.map(x => x.name === 'Grok' ? { ...x, status: 'quota_exhausted' } : x));
      
      setTimeout(() => {
        // Fallback to Gemini
        setActiveModel('Gemini');
        setModels(m => m.map(x => x.name === 'Gemini 2.5' ? { ...x, status: 'fallback' } : x));
        
        setTimeout(() => {
          // Gemini succeeds
          addLog({ model: 'Gemini', task: 'Classification', status: 'SUCCESS', latency: '820ms' });
          setModels(m => m.map(x => x.name === 'Gemini 2.5' ? { ...x, status: 'available' } : x));
          
          // Move to next steps
          setCurrentStep('structured');
          setTimeout(() => {
            addLog({ model: 'Gemini', task: 'Structured Extraction', status: 'SUCCESS', latency: '1.4s' });
            setCurrentStep('pydantic');
            setTimeout(() => {
              setCurrentStep('anomaly');
              setTimeout(() => {
                setCurrentStep('storage');
                setTimeout(() => {
                  finishProcessing();
                }, 1000);
              }, 1000);
            }, 1000);
          }, 2000);
          
        }, 1500);
      }, 1000);
    }, 1500);
  };

  const finishProcessing = () => {
    setIsProcessing(false);
    setCurrentStep(null);
    setDocumentResult({
      type: 'Invoice',
      confidence: 0.98,
      anomalies: [
        { text: 'Tax amount mismatch detected', severity: 'warning' }
      ],
      data: {
        vendor_name: 'Acme Corp',
        invoice_number: 'INV-2024-001',
        date: '2024-05-12',
        total_amount: '$1,250.00',
        currency: 'USD',
        tax_amount: '$100.00' // simulated anomaly source
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">DocFlow Dashboard</h1>
          <p className="text-gray-500 mt-1">Provider-Agnostic AI Document Intelligence</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Upload & Model Info */}
          <div className="lg:col-span-1 space-y-6">
            <FileUploader onUpload={handleUpload} isProcessing={isProcessing} />
            <AIModelStatus models={models} />
          </div>

          {/* Middle Column: Workflow & Queue */}
          <div className="lg:col-span-1 space-y-6">
            <WorkflowVisualizer 
              currentStep={currentStep} 
              activeModel={activeModel} 
              failedModels={failedModels} 
            />
            <ProcessingQueue 
              currentStep={currentStep} 
              activeModel={activeModel} 
            />
          </div>

          {/* Right Column: Activity Log & Results */}
          <div className="lg:col-span-1 space-y-6 flex flex-col h-full">
            <ModelActivityLog logs={logs} />
            
            {documentResult ? (
              <div className="space-y-6 flex-1 flex flex-col">
                <DocumentCard document={documentResult} />
                <div className="flex-1">
                  <NLQueryBox activeModel={activeModel} />
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center text-gray-400 border-dashed flex-1 flex flex-col items-center justify-center">
                <p>Upload a document to see extracted data</p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default App;

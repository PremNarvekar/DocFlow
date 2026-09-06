import React from 'react';
import { ArrowDown, Database, FileText, CheckCircle2, Zap, BrainCircuit, ShieldAlert, Cpu } from 'lucide-react';

const WorkflowVisualizer = ({ currentStep, activeModel, failedModels }) => {
  const steps = [
    { id: 'upload', label: 'PDF Upload', icon: FileText },
    { id: 'validation', label: 'Document Validation', icon: CheckCircle2 },
    { id: 'extraction', label: 'PyMuPDF Text Extraction', icon: FileText },
    { id: 'classification', label: 'Document Classification', icon: BrainCircuit },
    { id: 'ai_router', label: 'AI Router', icon: Cpu },
    { id: 'structured', label: 'Structured Extraction', icon: BrainCircuit },
    { id: 'pydantic', label: 'Pydantic Validation', icon: ShieldAlert },
    { id: 'anomaly', label: 'Anomaly Detection', icon: Zap },
    { id: 'storage', label: 'Vector / Metadata Storage', icon: Database },
  ];

  const getStepStatus = (stepId, index) => {
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    if (currentIndex === -1) return 'pending';
    if (index < currentIndex) return 'completed';
    if (index === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center">
      <h2 className="text-lg font-semibold text-gray-800 mb-6 self-start">Workflow Visualization</h2>
      
      <div className="flex flex-col items-center space-y-2 w-full max-w-md">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id, index);
          const Icon = step.icon;
          
          return (
            <React.Fragment key={step.id}>
              {/* Step Node */}
              <div className={`w-full p-3 rounded-lg border-2 flex items-center justify-between transition-all ${
                status === 'completed' ? 'border-green-500 bg-green-50' :
                status === 'active' ? 'border-blue-500 bg-blue-50 shadow-md scale-105' :
                'border-gray-200 bg-white text-gray-400'
              }`}>
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${
                    status === 'completed' ? 'bg-green-100 text-green-600' :
                    status === 'active' ? 'bg-blue-100 text-blue-600 animate-pulse' :
                    'bg-gray-100 text-gray-400'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className={`font-medium ${
                    status === 'completed' ? 'text-green-700' :
                    status === 'active' ? 'text-blue-700' :
                    'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                </div>
                {status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                {status === 'active' && <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>}
              </div>

              {/* AI Router Sub-branch logic */}
              {step.id === 'ai_router' && status !== 'pending' && (
                <div className="flex flex-col items-center w-full my-2">
                  <ArrowDown className={`w-5 h-5 ${status === 'completed' ? 'text-green-500' : 'text-blue-500'}`} />
                  
                  <div className="w-full flex justify-between px-4 my-4 relative">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-px bg-gray-300"></div>
                    <div className="absolute top-0 left-[12.5%] w-px h-4 bg-gray-300"></div>
                    <div className="absolute top-0 left-[50%] w-px h-4 bg-gray-300"></div>
                    <div className="absolute top-0 left-[87.5%] w-px h-4 bg-gray-300"></div>
                    
                    {['Grok', 'Gemini', 'Groq'].map((modelName) => {
                      const isFailed = failedModels.includes(modelName);
                      const isActive = activeModel === modelName;
                      
                      return (
                        <div key={modelName} className="flex flex-col items-center mt-4">
                          <div className={`px-4 py-2 rounded-md border text-sm font-medium ${
                            isFailed ? 'bg-red-50 border-red-200 text-red-600' :
                            isActive ? 'bg-blue-500 border-blue-600 text-white shadow-md' :
                            'bg-gray-50 border-gray-200 text-gray-500'
                          }`}>
                            {modelName}
                          </div>
                          {isFailed && (
                            <span className="text-[10px] text-red-500 mt-1 font-semibold text-center leading-tight">
                              FAILED<br/>fallback
                            </span>
                          )}
                          {isActive && (
                            <span className="text-[10px] text-blue-500 mt-1 font-semibold">
                              SUCCESS
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className={`px-4 py-2 rounded-full text-xs font-bold border ${
                    activeModel ? 'bg-green-100 text-green-700 border-green-200' : 'bg-gray-100 text-gray-500 border-gray-200'
                  }`}>
                    {activeModel ? `BEST SUCCESSFUL MODEL: ${activeModel.toUpperCase()}` : 'ROUTING...'}
                  </div>
                </div>
              )}

              {/* Arrow down between regular steps */}
              {index < steps.length - 1 && (
                <ArrowDown className={`w-5 h-5 ${
                  status === 'completed' ? 'text-green-500' : 'text-gray-300'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default WorkflowVisualizer;

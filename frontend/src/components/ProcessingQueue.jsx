import React from 'react';
import { Check, Loader2, Circle } from 'lucide-react';

const ProcessingQueue = ({ currentStep, activeModel }) => {
  const steps = [
    { id: 'upload', label: 'UPLOAD' },
    { id: 'extraction', label: 'TEXT EXTRACTION' },
    { id: 'classification', label: 'CLASSIFICATION' },
    { id: 'structured', label: 'EXTRACTION' },
    { id: 'validation', label: 'VALIDATION' },
    { id: 'anomaly', label: 'ANOMALY DETECTION' },
    { id: 'storage', label: 'STORAGE' },
  ];

  const getStepStatus = (stepId, index) => {
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    if (currentIndex === -1) return 'pending';
    if (index < currentIndex) return 'completed';
    if (index === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl shadow-lg shadow-pink-500/5 border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Processing Timeline</h2>
      
      <div className="space-y-4">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id, index);
          
          return (
            <div key={step.id} className="flex flex-col">
              <div className="flex items-center gap-3">
                {status === 'completed' ? (
                  <div className="bg-green-100 p-1 rounded-full">
                    <Check className="w-4 h-4 text-green-600" />
                  </div>
                ) : status === 'active' ? (
                  <div className="bg-pink-500/20 p-1 rounded-full">
                    <Loader2 className="w-4 h-4 text-pink-500 animate-spin" />
                  </div>
                ) : (
                  <div className="text-gray-300 p-1">
                    <Circle className="w-4 h-4" />
                  </div>
                )}
                
                <span className={`font-medium ${
                  status === 'completed' ? 'text-gray-900' :
                  status === 'active' ? 'text-pink-400' :
                  'text-gray-400'
                }`}>
                  {step.label}
                </span>
              </div>
              
              {/* Optional sub-info for AI steps */}
              {status === 'completed' && ['classification', 'structured'].includes(step.id) && activeModel && (
                <div className="ml-9 mt-1 text-xs text-gray-500 border-l-2 border-gray-100 pl-3 py-1">
                  Model: <span className="font-semibold text-pink-500">{activeModel}</span> ✓
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {activeModel && (
        <div className="mt-6 pt-4 border-t border-gray-100 bg-gray-50 -mx-6 -mb-6 px-6 pb-6 rounded-b-xl">
          <p className="text-sm text-gray-500 uppercase tracking-wider mb-1">Final Model</p>
          <p className="text-lg font-bold text-pink-500">{activeModel}</p>
        </div>
      )}
    </div>
  );
};

export default ProcessingQueue;

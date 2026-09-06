import React from 'react';
import { FileUp, Search, Cpu, CheckCircle2 } from 'lucide-react';

export default function WorkflowVisualizer({ currentStep }) {
  // Steps: 0: idle, 1: uploading, 2: processing (extract/classify), 3: complete
  
  const steps = [
    { id: 1, name: 'Upload', icon: FileUp, desc: 'Document ingestion' },
    { id: 2, name: 'Extract & Route', icon: Search, desc: 'PyMuPDF + Router' },
    { id: 3, name: 'AI Parse', icon: Cpu, desc: 'Structured extraction' },
    { id: 4, name: 'Done', icon: CheckCircle2, desc: 'Pydantic validated' }
  ];

  const getStatus = (stepId) => {
    if (currentStep === 'idle') return 'pending';
    if (currentStep === 'uploading' && stepId === 1) return 'active';
    if (currentStep === 'uploading' && stepId > 1) return 'pending';
    if (currentStep === 'processing' && stepId <= 3) return 'active';
    if (currentStep === 'processing' && stepId > 3) return 'pending';
    if (currentStep === 'complete') return 'completed';
    return 'pending';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6">
      <div className="flex justify-between items-start relative">
        {/* Background line */}
        <div className="absolute top-5 left-[10%] right-[10%] h-[2px] bg-slate-100 -z-10"></div>
        {/* Active line fill */}
        <div 
          className="absolute top-5 left-[10%] h-[2px] bg-blue-500 transition-all duration-500 -z-10"
          style={{ 
            width: currentStep === 'idle' ? '0%' : 
                   currentStep === 'uploading' ? '25%' : 
                   currentStep === 'processing' ? '65%' : '80%' 
          }}
        ></div>

        {steps.map((step) => {
          const status = getStatus(step.id);
          const Icon = step.icon;
          
          return (
            <div key={step.id} className="flex flex-col items-center w-1/4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-3 border-2 transition-colors bg-white ${
                status === 'completed' ? 'border-emerald-500 text-emerald-500' :
                status === 'active' ? 'border-blue-500 text-blue-500 shadow-[0_0_0_4px_rgba(59,130,246,0.1)]' :
                'border-slate-200 text-slate-400'
              }`}>
                <Icon className="w-5 h-5" />
              </div>
              <p className={`text-sm font-semibold mb-0.5 ${
                status === 'active' ? 'text-blue-600' : 
                status === 'completed' ? 'text-emerald-600' : 'text-slate-600'
              }`}>
                {step.name}
              </p>
              <p className="text-xs text-slate-400 hidden sm:block text-center">{step.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

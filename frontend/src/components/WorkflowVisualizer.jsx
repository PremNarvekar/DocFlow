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
    <div className="bg-white/[0.02] backdrop-blur-2xl rounded-3xl border border-white/[0.05] p-6 mb-6 shadow-2xl relative overflow-hidden">
      {/* Ambient animated background glow for active processing */}
      {currentStep === 'processing' && (
        <div className="absolute inset-0 bg-pink-500/[0.03] animate-pulse pointer-events-none" />
      )}
      
      <div className="flex justify-between items-start relative z-10">
        {/* Subtle Background line */}
        <div className="absolute top-5 left-[12%] right-[12%] h-[2px] bg-white/[0.05] -z-10 rounded-full"></div>
        
        {/* Active line fill with glow */}
        <div 
          className="absolute top-5 left-[12%] h-[2px] bg-pink-500 transition-all duration-1000 ease-in-out -z-10 rounded-full shadow-[0_0_10px_rgba(236,72,153,0.8)]"
          style={{ 
            width: currentStep === 'idle' ? '0%' : 
                   currentStep === 'uploading' ? '25%' : 
                   currentStep === 'processing' ? '65%' : '76%' 
          }}
        ></div>

        {steps.map((step) => {
          const status = getStatus(step.id);
          const Icon = step.icon;
          
          return (
            <div key={step.id} className="flex flex-col items-center w-1/4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-3 transition-all duration-500 backdrop-blur-md ${
                status === 'completed' 
                  ? 'bg-white/[0.05] border border-white/20 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)]' 
                  : status === 'active' 
                    ? 'bg-pink-500 text-white border-none shadow-[0_4px_20px_rgba(236,72,153,0.5)] scale-110 animate-in zoom-in' 
                    : 'bg-[#0a0a0f] border border-white/5 text-slate-600'
              }`}>
                <Icon className={`w-4 h-4 ${status === 'active' ? 'animate-pulse' : ''}`} />
              </div>
              <p className={`text-xs font-semibold tracking-wide uppercase transition-colors duration-500 ${
                status === 'active' ? 'text-pink-400' : 
                status === 'completed' ? 'text-slate-300' : 'text-slate-600'
              }`}>
                {step.name}
              </p>
              <p className="text-[10px] text-slate-500 hidden sm:block text-center mt-1 font-medium tracking-wide opacity-70">{step.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

import React from 'react';
import { UploadCloud } from 'lucide-react';

export default function FileUploader({ onUpload, isUploading }) {
  const fileInputRef = React.useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-xl shadow-lg shadow-pink-500/5 border border-white/10">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-200">Process Document</h3>
        <p className="text-sm text-slate-500">Upload a PDF to extract structured data using AI.</p>
      </div>

      <input 
        type="file" 
        accept="application/pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      <div 
        className={`relative group flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all ${
          isUploading 
            ? 'border-blue-300 bg-pink-500/10 cursor-wait' 
            : 'border-white/20 hover:border-pink-500 hover:bg-slate-950 cursor-pointer'
        }`}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <div className={`p-4 rounded-full mb-3 ${isUploading ? 'bg-pink-500/20 text-pink-500 animate-pulse' : 'bg-slate-800 text-slate-500 group-hover:bg-pink-500/20 group-hover:text-pink-500 transition-colors'}`}>
          <UploadCloud className="w-8 h-8" />
        </div>
        
        {isUploading ? (
          <div className="text-center">
            <p className="text-sm font-medium text-pink-500 mb-1">Uploading document...</p>
            <p className="text-xs text-blue-400">Please wait</p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-sm font-medium text-slate-700 mb-1">
              <span className="text-pink-500">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500">PDF documents up to 10MB</p>
          </div>
        )}
      </div>
    </div>
  );
}

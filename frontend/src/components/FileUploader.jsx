import React, { useState, useEffect } from 'react';
import { UploadCloud, ChevronDown } from 'lucide-react';
import { fetchProviderStatus } from '../lib/api';

export default function FileUploader({ onUpload, isUploading }) {
  const fileInputRef = React.useRef(null);
  const [provider, setProvider] = useState("auto");
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    fetchProviderStatus().then(setProviders).catch(console.error);
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0], provider);
    }
  };

  return (
    <div className="bg-white/[0.02] backdrop-blur-2xl p-6 rounded-2xl shadow-2xl border border-white/[0.05]">
      <div className="mb-5 flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold text-slate-200">Process Document</h3>
          <p className="text-sm text-slate-500 mt-1">Upload a PDF to extract structured data.</p>
        </div>
      </div>

      <div className="mb-5">
        <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">Select AI Model</label>
        <div className="relative">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            disabled={isUploading}
            className="appearance-none w-full bg-white/[0.03] border border-white/10 text-slate-200 text-sm rounded-xl px-4 py-3 pr-10 focus:outline-none focus:ring-2 focus:ring-pink-500/50 focus:border-pink-500 transition-all cursor-pointer disabled:opacity-50"
          >
            <option value="auto" className="bg-slate-900">✨ Auto (Best Available)</option>
            {providers.map(p => (
              <option key={p.name} value={p.name} className="bg-slate-900">
                {p.name.charAt(0).toUpperCase() + p.name.slice(1)} ({p.model})
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      <input 
        type="file" 
        accept="application/pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      <div 
        className={`relative group flex flex-col items-center justify-center p-8 border border-dashed rounded-xl transition-all duration-300 ${
          isUploading 
            ? 'border-pink-500/50 bg-pink-500/[0.02] cursor-wait' 
            : 'border-white/20 hover:border-pink-500 hover:bg-white/[0.02] cursor-pointer'
        }`}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <div className={`p-4 rounded-full mb-3 shadow-lg ${isUploading ? 'bg-pink-500/20 text-pink-400 animate-pulse shadow-pink-500/20' : 'bg-white/[0.05] text-slate-400 group-hover:bg-pink-500/20 group-hover:text-pink-400 transition-colors group-hover:shadow-pink-500/20'}`}>
          <UploadCloud className="w-8 h-8" />
        </div>
        
        {isUploading ? (
          <div className="text-center">
            <p className="text-sm font-medium text-pink-400 mb-1">Uploading document...</p>
            <p className="text-xs text-slate-400">Please wait</p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-sm font-medium text-slate-300 mb-1">
              <span className="text-pink-400">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500">PDF documents up to 10MB</p>
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, ChevronDown, Check } from 'lucide-react';
import { fetchProviderStatus } from '../lib/api';

export default function FileUploader({ onUpload, isUploading }) {
  const fileInputRef = useRef(null);
  const dropdownRef = useRef(null);
  const [provider, setProvider] = useState("auto");
  const [providers, setProviders] = useState([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    fetchProviderStatus().then(setProviders).catch(console.error);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0], provider);
    }
  };

  const getProviderDisplayName = (val) => {
    if (val === 'auto') return 'Auto (Best Available)';
    const p = providers.find(x => x.name === val);
    if (!p) return val;
    return `${p.name.charAt(0).toUpperCase() + p.name.slice(1)} (${p.model})`;
  };

  return (
    <div className="bg-white/[0.02] backdrop-blur-2xl p-6 rounded-2xl shadow-2xl border border-white/[0.05]">
      <div className="mb-5 flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold text-slate-200">Process Document</h3>
          <p className="text-sm text-slate-500 mt-1">Upload a PDF to extract structured data.</p>
        </div>
      </div>

      <div className="mb-5" ref={dropdownRef}>
        <label className="block text-xs font-medium text-slate-400 mb-2 uppercase tracking-wider">AI Model</label>
        <div className="relative">
          <div 
            onClick={() => !isUploading && setIsDropdownOpen(!isDropdownOpen)}
            className={`w-full flex items-center justify-between bg-white/[0.03] border border-white/10 text-slate-200 text-sm rounded-xl px-4 py-3 transition-all ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-pink-500/50 hover:bg-white/[0.05]'}`}
          >
            <span>{getProviderDisplayName(provider)}</span>
            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </div>

          {isDropdownOpen && (
            <div className="absolute z-20 w-full mt-2 bg-[#0a0a0f] border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
              <div 
                onClick={() => { setProvider('auto'); setIsDropdownOpen(false); }}
                className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-white/[0.05] transition-colors"
              >
                <span className={`text-sm ${provider === 'auto' ? 'text-pink-400 font-medium' : 'text-slate-300'}`}>
                  Auto (Best Available)
                </span>
                {provider === 'auto' && <Check className="w-4 h-4 text-pink-400" />}
              </div>
              
              {providers.map(p => (
                <div 
                  key={p.name}
                  onClick={() => { setProvider(p.name); setIsDropdownOpen(false); }}
                  className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-white/[0.05] transition-colors border-t border-white/5"
                >
                  <span className={`text-sm ${provider === p.name ? 'text-pink-400 font-medium' : 'text-slate-300'}`}>
                    {p.name.charAt(0).toUpperCase() + p.name.slice(1)} <span className="text-slate-500 ml-1">({p.model})</span>
                  </span>
                  {provider === p.name && <Check className="w-4 h-4 text-pink-400" />}
                </div>
              ))}
            </div>
          )}
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

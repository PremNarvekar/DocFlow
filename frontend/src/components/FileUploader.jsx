import React from 'react';
import { UploadCloud } from 'lucide-react';

export default function FileUploader({ onUpload, isUploading }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-800">Process Document</h3>
        <p className="text-sm text-slate-500">Upload a PDF to extract structured data using AI.</p>
      </div>

      <div 
        className={`relative group flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all ${
          isUploading 
            ? 'border-blue-300 bg-blue-50 cursor-wait' 
            : 'border-slate-300 hover:border-blue-500 hover:bg-slate-50 cursor-pointer'
        }`}
        onClick={() => !isUploading && onUpload()}
      >
        <div className={`p-4 rounded-full mb-3 ${isUploading ? 'bg-blue-100 text-blue-600 animate-pulse' : 'bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-600 transition-colors'}`}>
          <UploadCloud className="w-8 h-8" />
        </div>
        
        {isUploading ? (
          <div className="text-center">
            <p className="text-sm font-medium text-blue-600 mb-1">Uploading document...</p>
            <p className="text-xs text-blue-400">Please wait</p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-sm font-medium text-slate-700 mb-1">
              <span className="text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500">PDF documents up to 10MB</p>
          </div>
        )}
      </div>
    </div>
  );
}

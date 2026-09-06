import React, { useCallback } from 'react';
import { Upload, File } from 'lucide-react';

const FileUploader = ({ onUpload, isProcessing }) => {
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    if (isProcessing) return;
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onUpload(files[0]);
    }
  }, [onUpload, isProcessing]);

  const handleChange = (e) => {
    if (e.target.files.length > 0) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <div 
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
        isProcessing ? 'border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed' : 'border-blue-300 hover:border-blue-500 hover:bg-blue-50 cursor-pointer bg-white'
      }`}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <input 
        type="file" 
        id="file-upload" 
        className="hidden" 
        onChange={handleChange}
        accept=".pdf"
        disabled={isProcessing}
      />
      <label htmlFor="file-upload" className={isProcessing ? "cursor-not-allowed" : "cursor-pointer"}>
        <div className="flex flex-col items-center justify-center">
          <div className="bg-blue-100 p-3 rounded-full mb-4">
            <Upload className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            Upload Document
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Drag and drop your PDF here, or click to browse
          </p>
          <div className="flex items-center text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
            <File className="w-3 h-3 mr-1" />
            PDF up to 10MB
          </div>
        </div>
      </label>
    </div>
  );
};

export default FileUploader;

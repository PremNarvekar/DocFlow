import React, { useEffect, useState } from 'react';
import { fetchDocuments } from '../lib/api';
import { FileText, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function DocumentHistory({ onSelectDocument, currentDocumentId }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await fetchDocuments();
      setDocuments(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    
    // Poll every 10 seconds just to keep the history up to date if they upload something
    const interval = setInterval(loadDocuments, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && documents.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex justify-center items-center h-48">
        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[400px]">
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex justify-between items-center">
        <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-500" />
          Document History
        </h3>
        <span className="text-xs font-medium bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
          {documents.length} files
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {error && (
          <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg m-2">
            Failed to load history.
          </div>
        )}
        
        {documents.length === 0 && !error ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 p-6 text-center">
            <FileText className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">No documents uploaded yet.</p>
          </div>
        ) : (
          documents.map(doc => (
            <button
              key={doc.id}
              onClick={() => onSelectDocument(doc)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                currentDocumentId === doc.id 
                  ? 'bg-blue-50 border-blue-200' 
                  : 'bg-white border-transparent hover:bg-slate-50 hover:border-slate-200'
              } flex items-start gap-3`}
            >
              <div className="mt-0.5">
                {doc.status === 'COMPLETED' ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : doc.status === 'FAILED' ? (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                ) : (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">
                  {doc.filename}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {new Date(doc.created_at).toLocaleDateString()} at {new Date(doc.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </p>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

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
      <div className="bg-white/[0.02] backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/[0.05] p-6 flex justify-center items-center h-[350px]">
        <Loader2 className="w-6 h-6 text-pink-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-white/[0.02] backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/[0.05] overflow-hidden flex flex-col h-[350px]">
      <div className="bg-white/[0.01] border-b border-white/[0.05] px-6 py-5 flex justify-between items-center">
        <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2 tracking-wide">
          <Clock className="w-4 h-4 text-pink-500" />
          HISTORY
        </h3>
        <span className="text-xs font-semibold bg-pink-500/20 text-pink-400 px-3 py-1 rounded-full shadow-[0_0_10px_rgba(236,72,153,0.1)]">
          {documents.length} Files
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {error && (
          <div className="p-4 text-sm text-red-400 bg-red-500/10 rounded-xl m-2 border border-red-500/20">
            Failed to load history.
          </div>
        )}
        
        {documents.length === 0 && !error ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 p-6 text-center">
            <FileText className="w-8 h-8 mb-3 opacity-30" />
            <p className="text-sm tracking-wide">No documents processed yet.</p>
          </div>
        ) : (
          documents.map(doc => (
            <button
              key={doc.id}
              onClick={() => onSelectDocument(doc)}
              className={`w-full text-left px-4 py-3.5 rounded-2xl border transition-all duration-300 ${
                currentDocumentId === doc.id 
                  ? 'bg-pink-500/[0.05] border-pink-500/30 shadow-[0_0_15px_rgba(236,72,153,0.1)] scale-[0.98]' 
                  : 'bg-transparent border-transparent hover:bg-white/[0.03] hover:border-white/10'
              } flex items-center gap-4 group`}
            >
              <div className="shrink-0 flex items-center justify-center">
                {doc.status === 'COMPLETED' ? (
                  <CheckCircle className={`w-5 h-5 ${currentDocumentId === doc.id ? 'text-pink-500' : 'text-slate-400 group-hover:text-pink-400'} transition-colors`} />
                ) : doc.status === 'FAILED' ? (
                  <AlertCircle className="w-5 h-5 text-red-400" />
                ) : (
                  <Loader2 className="w-5 h-5 text-pink-500 animate-spin" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold truncate transition-colors ${currentDocumentId === doc.id ? 'text-pink-400' : 'text-slate-200 group-hover:text-white'}`}>
                  {doc.filename}
                </p>
                <p className="text-xs text-slate-500 mt-1 font-medium tracking-wide">
                  {new Date(doc.created_at).toLocaleDateString()} • {new Date(doc.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </p>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

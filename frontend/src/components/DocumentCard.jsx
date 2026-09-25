import React from 'react';
import { FileText, Database } from 'lucide-react';
import AnomalyBadge from './AnomalyBadge';

const DocumentCard = ({ document }) => {
  if (!document) return null;

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl shadow-lg shadow-pink-500/5 border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-800">Extracted Document Data</h2>
        </div>
        <span className="px-2.5 py-1 text-xs font-medium bg-pink-500/20 text-pink-400 rounded-full uppercase">
          {document.type}
        </span>
      </div>
      
      <div className="p-6">
        {document.anomalies && document.anomalies.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {document.anomalies.map((anom, idx) => (
              <AnomalyBadge key={idx} text={anom.text} type={anom.severity} />
            ))}
          </div>
        )}
        
        <div className="grid grid-cols-2 gap-y-4 gap-x-8">
          {Object.entries(document.data).map(([key, value]) => (
            <div key={key} className="border-b border-gray-50 pb-2">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                {key.replace(/_/g, ' ')}
              </p>
              <p className="text-sm text-gray-900 font-medium">
                {value || <span className="text-gray-300 italic">Not found</span>}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-8 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5" />
            Stored in Vector DB
          </div>
          <span>Confidence: {(document.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
};

export default DocumentCard;

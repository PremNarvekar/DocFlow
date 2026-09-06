import React from 'react';
import { AlertTriangle } from 'lucide-react';

const AnomalyBadge = ({ text, type = 'warning' }) => {
  const colors = {
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200'
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium ${colors[type]}`}>
      <AlertTriangle className="w-3.5 h-3.5" />
      {text}
    </div>
  );
};

export default AnomalyBadge;

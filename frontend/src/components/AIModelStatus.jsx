import React from 'react';
import { CheckCircle2, AlertCircle, XCircle, Settings, Clock, Activity } from 'lucide-react';

const AIModelStatus = ({ models }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'available': return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'not_configured': return <Settings className="w-5 h-5 text-gray-400" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'rate_limited': return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'quota_exhausted': return <AlertCircle className="w-5 h-5 text-orange-500" />;
      case 'active': return <Activity className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'fallback': return <Activity className="w-5 h-5 text-purple-500" />;
      default: return <Settings className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'available': return 'Available';
      case 'not_configured': return 'Not Configured';
      case 'error': return 'Error';
      case 'rate_limited': return 'Rate Limited';
      case 'quota_exhausted': return 'Quota Exhausted';
      case 'active': return 'Active';
      case 'fallback': return 'Fallback Active';
      default: return 'Unknown';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">AI Model Status</h2>
        <Activity className="w-5 h-5 text-gray-500" />
      </div>
      <div className="divide-y divide-gray-100">
        {models.map((model) => (
          <div key={model.id} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                {getStatusIcon(model.status)}
                <div>
                  <h3 className="font-medium text-gray-900">{model.name}</h3>
                  <p className="text-sm text-gray-500">{model.provider}</p>
                </div>
              </div>
              <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                model.status === 'available' ? 'bg-green-100 text-green-700' :
                model.status === 'not_configured' ? 'bg-gray-100 text-gray-600' :
                model.status === 'active' ? 'bg-blue-100 text-blue-700' :
                model.status === 'fallback' ? 'bg-purple-100 text-purple-700' :
                'bg-red-100 text-red-700'
              }`}>
                {getStatusText(model.status)}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-3 pl-8">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Tasks</p>
                <p className="text-sm text-gray-700">{model.tasks.join(', ')}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Latency</p>
                <p className="text-sm text-gray-700">{model.latency || '--'}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AIModelStatus;

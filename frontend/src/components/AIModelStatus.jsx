import React, { useState, useEffect } from 'react';
import { Activity, Server } from 'lucide-react';
import api from '../lib/api';

export default function AIModelStatus() {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await api.get('/providers/status');
        setProviders(response.data);
      } catch (error) {
        console.error('Failed to fetch provider status:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProviders();
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 mt-6 overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-200 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-slate-600" />
          <h3 className="font-semibold text-slate-800">AI Provider Status</h3>
        </div>
        <Activity className="w-4 h-4 text-emerald-500" />
      </div>

      <div className="divide-y divide-slate-100">
        {loading ? (
          <div className="px-5 py-4 text-sm text-slate-500 text-center">Checking connected models...</div>
        ) : providers.length === 0 ? (
          <div className="px-5 py-4 text-sm text-slate-500 text-center">No AI models configured.</div>
        ) : (
          providers.map((provider) => (
            <div key={provider.name} className="px-5 py-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-slate-800 text-sm">{provider.name}</span>
                  <span className={`flex w-2 h-2 rounded-full ${provider.status === 'Available' ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
                </div>
                <p className="text-xs text-slate-500 font-mono">{provider.model}</p>
              </div>
              <div className="text-right">
                <span className={`inline-block px-2 py-1 rounded-md text-xs font-medium mb-1 ${
                  provider.status === 'Available' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600 border border-slate-200'
                }`}>
                  {provider.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

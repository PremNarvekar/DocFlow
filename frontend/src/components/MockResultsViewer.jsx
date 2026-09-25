import React from 'react';
import { FileText, CheckCircle } from 'lucide-react';

export default function ResultsViewer({ data }) {
  if (!data) return null;

  const isInvoice = data.items && Array.isArray(data.items);

  return (
    <div className="bg-white/[0.02] backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/[0.05] overflow-hidden flex flex-col h-full">
      <div className="bg-white/[0.01] border-b border-white/[0.05] px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-pink-500" />
          <h3 className="font-semibold text-slate-200 tracking-wide text-sm">EXTRACTED DATA</h3>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full text-xs font-semibold shadow-[0_0_15px_rgba(16,185,129,0.15)]">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Validated</span>
        </div>
      </div>
      
      <div className="p-6 flex-1 overflow-auto custom-scrollbar">
        {isInvoice ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-6 mb-8">
              <div>
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Vendor</p>
                <p className="text-sm font-semibold text-white">{data.vendor_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Customer</p>
                <p className="text-sm font-semibold text-white">{data.customer_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Invoice Number</p>
                <p className="text-sm font-medium text-slate-300">{data.invoice_number || 'N/A'}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Date</p>
                <p className="text-sm font-medium text-slate-300">{data.invoice_date || 'N/A'}</p>
              </div>
            </div>

            <div className="mb-6">
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-white/10 pb-2">Line Items</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-[11px] text-slate-400 bg-white/[0.03] uppercase font-bold tracking-wider">
                    <tr>
                      <th className="px-4 py-3 rounded-l-xl">Description</th>
                      <th className="px-4 py-3 text-right">Qty</th>
                      <th className="px-4 py-3 text-right">Price</th>
                      <th className="px-4 py-3 text-right rounded-r-xl">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.05]">
                    {data.items.map((item, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-4 py-3.5 text-slate-300">{item.description}</td>
                        <td className="px-4 py-3.5 text-right text-slate-400">{item.quantity}</td>
                        <td className="px-4 py-3.5 text-right text-slate-400">${item.unit_price}</td>
                        <td className="px-4 py-3.5 text-right font-semibold text-white">${item.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-white/10 mt-2">
              <div className="w-full sm:w-1/2 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Subtotal</span>
                  <span className="font-medium text-slate-200">${data.subtotal || 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Tax</span>
                  <span className="font-medium text-slate-200">${data.tax || 0}</span>
                </div>
                <div className="flex justify-between text-base font-bold pt-3 border-t border-white/10">
                  <span className="text-white">Total <span className="text-slate-500 font-medium text-sm ml-1">({data.currency || 'USD'})</span></span>
                  <span className="text-pink-400 drop-shadow-[0_0_10px_rgba(236,72,153,0.5)]">${data.total || 0}</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <pre className="text-xs bg-[#0a0a0f] border border-white/10 text-slate-300 p-5 rounded-2xl overflow-x-auto shadow-inner">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

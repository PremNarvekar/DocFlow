import React from 'react';
import { FileText, CheckCircle } from 'lucide-react';

export default function ResultsViewer({ data }) {
  if (!data) return null;

  const isInvoice = data.items && Array.isArray(data.items);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
      <div className="bg-slate-50 border-b border-slate-200 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-slate-800">Extracted Document Data</h3>
        </div>
        <div className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full text-xs font-medium border border-emerald-100">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Validated</span>
        </div>
      </div>
      
      <div className="p-5 flex-1 overflow-auto">
        {isInvoice ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 mb-6">
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Vendor</p>
                <p className="text-sm font-semibold text-slate-900">{data.vendor_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Customer</p>
                <p className="text-sm font-semibold text-slate-900">{data.customer_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Invoice Number</p>
                <p className="text-sm font-medium text-slate-800">{data.invoice_number || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Date</p>
                <p className="text-sm font-medium text-slate-800">{data.invoice_date || 'N/A'}</p>
              </div>
            </div>

            <div className="mb-4">
              <h4 className="text-sm font-semibold text-slate-800 mb-2 border-b border-slate-100 pb-2">Line Items</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 bg-slate-50 uppercase font-medium">
                    <tr>
                      <th className="px-3 py-2 rounded-l-md">Description</th>
                      <th className="px-3 py-2 text-right">Qty</th>
                      <th className="px-3 py-2 text-right">Price</th>
                      <th className="px-3 py-2 text-right rounded-r-md">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.items.map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2.5 text-slate-800">{item.description}</td>
                        <td className="px-3 py-2.5 text-right text-slate-600">{item.quantity}</td>
                        <td className="px-3 py-2.5 text-right text-slate-600">${item.unit_price}</td>
                        <td className="px-3 py-2.5 text-right font-medium text-slate-800">${item.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-200">
              <div className="w-full sm:w-1/2 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Subtotal</span>
                  <span className="font-medium text-slate-800">${data.subtotal || 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Tax</span>
                  <span className="font-medium text-slate-800">${data.tax || 0}</span>
                </div>
                <div className="flex justify-between text-base font-bold pt-2 border-t border-slate-100">
                  <span className="text-slate-900">Total ({data.currency || 'USD'})</span>
                  <span className="text-blue-600">${data.total || 0}</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <pre className="text-xs bg-slate-800 text-slate-200 p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

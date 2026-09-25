import React, { useState } from 'react';
import { Search, Bot, User, Send, Loader2 } from 'lucide-react';

const NLQueryBox = ({ activeModel }) => {
  const [query, setQuery] = useState('');
  const [chat, setChat] = useState([
    { role: 'bot', text: 'Document processed. You can now ask questions about it using RAG.' }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Add user message
    const newChat = [...chat, { role: 'user', text: query }];
    setChat(newChat);
    setQuery('');
    setIsTyping(true);

    // Simulate RAG response
    setTimeout(() => {
      setChat([...newChat, { 
        role: 'bot', 
        text: `Based on the document context, I found the information you requested. (Simulated answer from ${activeModel || 'AI Router'})`
      }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl shadow-lg shadow-pink-500/5 border border-gray-100 flex flex-col h-full">
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-pink-400" />
          <h2 className="text-lg font-semibold text-gray-800">Natural Language Query (RAG)</h2>
        </div>
      </div>
      
      <div className="flex-1 p-6 overflow-y-auto min-h-[250px] max-h-[400px] flex flex-col gap-4">
        {chat.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
              msg.role === 'user' ? 'bg-gray-100 text-gray-600' : 'bg-pink-500/20 text-pink-500'
            }`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`px-4 py-2 rounded-2xl max-w-[80%] text-sm ${
              msg.role === 'user' ? 'bg-pink-500 text-white rounded-tr-sm' : 'bg-gray-100 text-gray-800 rounded-tl-sm'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-pink-500/20 text-pink-500 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="px-4 py-2 rounded-2xl bg-gray-100 text-gray-500 rounded-tl-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Thinking...
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-100">
        <form onSubmit={handleSubmit} className="relative">
          <input 
            type="text" 
            placeholder="Ask a question about the document..."
            className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-pink-500/20 focus:border-pink-500 transition-all text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isTyping}
          />
          <button 
            type="submit"
            disabled={isTyping || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default NLQueryBox;

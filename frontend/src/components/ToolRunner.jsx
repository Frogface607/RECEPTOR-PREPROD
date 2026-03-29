import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft, Play, Loader2, Copy, Check, Lock, Crown } from 'lucide-react';
import axios from 'axios';
import { API_URL, USER_ID } from '../config';
import { getToolById, CATEGORIES } from '../data/tools-catalog';
import { toast } from './Toast';

function ToolRunner({ toolId, onBack }) {
  const tool = getToolById(toolId);
  const [fields, setFields] = useState({});
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!tool) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        Инструмент не найден
      </div>
    );
  }

  const cat = CATEGORIES.find(c => c.id === tool.category);

  const handleRun = async () => {
    // Check required fields
    const missing = tool.fields.filter(f => f.required && !fields[f.id]?.trim());
    if (missing.length > 0) {
      toast(`Заполните: ${missing.map(f => f.label).join(', ')}`, 'warning');
      return;
    }

    setLoading(true);
    setResult('');

    try {
      // Build prompt from tool definition
      const prompt = tool.buildPrompt(fields);

      // Send to chat API (reuse existing LLM infrastructure)
      const response = await axios.post(`${API_URL}/chat/message`, {
        messages: [{ role: 'user', content: prompt }],
        user_id: USER_ID,
      });

      setResult(response.data.content || 'Нет результата');
    } catch (error) {
      if (error.response?.status === 429) {
        toast('Превышен лимит запросов. Попробуйте позже.', 'error');
      } else {
        toast('Ошибка генерации. Попробуйте ещё раз.', 'error');
      }
      console.error('Tool run error:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyResult = async () => {
    const text = result.replace(/[#*`_~\[\]()]/g, '').replace(/\n{3,}/g, '\n\n');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast('Скопировано!', 'success');
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          Назад к инструментам
        </button>

        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            {cat?.name}
            {!tool.free && (
              <span className="flex items-center gap-1 text-amber-400 text-xs">
                <Crown size={12} />
                Pro
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">{tool.name}</h1>
          <p className="text-gray-400">{tool.description}</p>
        </div>

        {/* Input Fields */}
        <div className="space-y-4 mb-6">
          {tool.fields.map(field => (
            <div key={field.id}>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                {field.label}
                {field.required && <span className="text-red-400 ml-1">*</span>}
              </label>
              {field.multiline ? (
                <textarea
                  value={fields[field.id] || ''}
                  onChange={(e) => setFields({ ...fields, [field.id]: e.target.value })}
                  placeholder={field.placeholder}
                  rows={4}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 resize-none"
                />
              ) : (
                <input
                  type="text"
                  value={fields[field.id] || ''}
                  onChange={(e) => setFields({ ...fields, [field.id]: e.target.value })}
                  placeholder={field.placeholder}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50"
                />
              )}
            </div>
          ))}
        </div>

        {/* Run Button */}
        <button
          onClick={handleRun}
          disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 disabled:opacity-50 text-white rounded-xl font-semibold text-lg transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Генерирую...
            </>
          ) : (
            <>
              <Play size={20} />
              Сгенерировать
            </>
          )}
        </button>

        {/* Result */}
        {result && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-white">Результат</h2>
              <button
                onClick={copyResult}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
              >
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? 'Скопировано' : 'Копировать'}
              </button>
            </div>
            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
              <ReactMarkdown
                className="prose prose-invert prose-sm max-w-none"
                components={{
                  h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-2 text-white" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-2 text-white mt-4" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-base font-semibold mb-1 text-white mt-3" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                  li: ({node, ...props}) => <li className="text-gray-300" {...props} />,
                  p: ({node, ...props}) => <p className="mb-2 last:mb-0 text-gray-300" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                  table: ({node, ...props}) => (
                    <div className="overflow-x-auto my-3">
                      <table className="min-w-full border-collapse border border-gray-700 rounded-lg" {...props} />
                    </div>
                  ),
                  th: ({node, ...props}) => <th className="px-3 py-2 text-left text-sm font-semibold text-white border border-gray-700 bg-gray-800" {...props} />,
                  td: ({node, ...props}) => <td className="px-3 py-2 text-sm text-gray-300 border border-gray-700" {...props} />,
                }}
              >
                {result}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ToolRunner;

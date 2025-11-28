import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
const API = `${BACKEND_URL}/api`;

const CulinaryAssistant = ({ 
  userId, 
  mode = 'center', // 'center' | 'sidebar'
  onTechCardRequest = null // Callback для создания техкарты из чата
}) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Привет! Я RECEPTOR — твой AI-ассистент в ресторанном бизнесе. Я специально обучен делать твою жизнь проще, кухню эффективнее, а ресторан прибыльнее. Спроси меня, что я могу.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Фокус на input при загрузке
  useEffect(() => {
    if (mode === 'center' && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [mode]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      console.log('Sending message to:', `${API}/assistant/chat`);
      const response = await axios.post(`${API}/assistant/chat`, {
        user_id: userId || 'demo_user',
        message: currentInput,
        conversation_id: conversationId
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        suggestions: response.data.suggestions || [],
        tool_calls: response.data.tool_calls || [],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }

      // Обработка tool calls - если была создана техкарта
      if (response.data.tool_calls && response.data.tool_calls.length > 0) {
        console.log('Tool calls received:', response.data.tool_calls);
        response.data.tool_calls.forEach(toolCall => {
          console.log('Processing tool call:', toolCall);
          if (toolCall.tool === 'generateTechcard') {
            console.log('generateTechcard tool call:', toolCall);
            if (toolCall.result?.success && onTechCardRequest) {
              // Вызываем callback для создания техкарты
              const dishName = toolCall.result.dish_name || toolCall.result.card?.name || '';
              console.log('Calling onTechCardRequest with:', { dishName, hasCard: !!toolCall.result.card });
              if (dishName || toolCall.result.card) {
                // Передаем данные техкарты через callback
                onTechCardRequest({
                  dishName: dishName,
                  techCard: toolCall.result.card
                });
              }
            } else {
              console.warn('generateTechcard failed or no callback:', {
                success: toolCall.result?.success,
                hasCallback: !!onTechCardRequest,
                error: toolCall.result?.error
              });
            }
          }
        });
      }
    } catch (error) {
      console.error('Assistant error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Неизвестная ошибка';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Извините, произошла ошибка: ${errorMessage}. Попробуйте еще раз.`,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestion = (suggestion) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Центральный режим (как ChatGPT, темная тема)
  if (mode === 'center') {
    return (
      <div className="flex flex-col h-[calc(100vh-200px)] max-w-4xl mx-auto bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700 shadow-xl">
        {/* Заголовок */}
        <div className="px-6 py-4 border-b border-gray-700 bg-gray-800/70 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <div>
              <h2 className="font-semibold text-gray-200">RECEPTOR Assistant</h2>
              <p className="text-xs text-gray-400">AI-ассистент для ресторанного бизнеса</p>
            </div>
          </div>
        </div>

        {/* Сообщения */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 bg-purple-600/20 rounded-full flex items-center justify-center mb-2">
                    <span className="text-purple-400 font-bold text-sm">R</span>
                  </div>
                )}
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  
                  {/* Отображение tool calls */}
                  {msg.tool_calls && msg.tool_calls.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {msg.tool_calls.map((toolCall, i) => (
                        <div key={i} className="bg-purple-900/30 border border-purple-500/30 rounded-lg p-3">
                          {toolCall.tool === 'generateTechcard' && toolCall.result?.success && (
                            <div className="flex items-center gap-2">
                              <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span className="text-sm text-green-300">
                                Техкарта "{toolCall.result.dish_name}" успешно создана!
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {msg.suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => handleSuggestion(suggestion)}
                        className="text-xs bg-gray-700 border border-gray-600 text-gray-200 rounded-full px-3 py-1.5 hover:bg-gray-600 hover:border-purple-500 transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="max-w-[85%]">
                <div className="w-8 h-8 bg-purple-600/20 rounded-full flex items-center justify-center mb-2">
                  <span className="text-purple-400 font-bold text-sm">R</span>
                </div>
                <div className="bg-gray-700 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Ввод */}
        <div className="px-6 py-4 border-t border-gray-700 bg-gray-800/70 rounded-b-2xl">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Спросите что-нибудь..."
                rows={1}
                className="w-full px-4 py-3 pr-12 bg-gray-700 text-white border border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none max-h-32 overflow-y-auto placeholder-gray-400"
                disabled={loading}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="absolute right-2 bottom-2 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Каждое сообщение стоит 5 токенов
          </p>
        </div>
      </div>
    );
  }

  // Режим сайдбара (компактный, темная тема)
  return (
    <div className="flex flex-col h-full bg-gray-800/50 backdrop-blur-lg rounded-2xl border border-gray-700 shadow-lg">
      {/* Заголовок */}
      <div className="px-4 py-3 border-b border-gray-700 bg-gray-800/70 rounded-t-2xl">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-xs">R</span>
          </div>
          <h3 className="font-semibold text-sm text-gray-200">RECEPTOR Assistant</h3>
        </div>
      </div>

      {/* Сообщения */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-xs ${
                msg.role === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-200'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              
              {/* Отображение tool calls */}
              {msg.tool_calls && msg.tool_calls.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.tool_calls.map((toolCall, i) => (
                    <div key={i} className="bg-purple-900/30 border border-purple-500/30 rounded p-2">
                      {toolCall.tool === 'generateTechcard' && toolCall.result?.success && (
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span className="text-xs text-green-300">
                            Техкарта "{toolCall.result.dish_name}" создана!
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-lg px-3 py-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Ввод */}
      <div className="px-4 py-3 border-t border-gray-700 bg-gray-800/70 rounded-b-2xl">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Спросите что-нибудь..."
            className="flex-1 px-3 py-2 text-sm bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent placeholder-gray-400"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {loading ? '...' : 'Отправить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CulinaryAssistant;


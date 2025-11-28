import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
  const [conversations, setConversations] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
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

  // Загружаем список бесед при монтировании
  useEffect(() => {
    if (userId && mode === 'center') {
      loadConversations();
    }
  }, [userId, mode]);

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API}/assistant/conversations`, {
        params: { user_id: userId || 'demo_user' }
      });
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadConversation = async (convId) => {
    try {
      const response = await axios.get(`${API}/assistant/conversations/${convId}`, {
        params: { user_id: userId || 'demo_user' }
      });
      
      // Преобразуем сообщения из формата БД в формат компонента
      const loadedMessages = response.data.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        tool_calls: msg.tool_calls
      }));
      
      setMessages(loadedMessages);
      setConversationId(convId);
      setShowHistory(false);
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const startNewConversation = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Привет! Я RECEPTOR — твой AI-ассистент в ресторанном бизнесе. Я специально обучен делать твою жизнь проще, кухню эффективнее, а ресторан прибыльнее. Спроси меня, что я могу.',
        timestamp: new Date()
      }
    ]);
    setConversationId(null);
    setShowHistory(false);
  };

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
        // Обновляем список бесед после отправки сообщения
        loadConversations();
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

  // Центральный режим (как ChatGPT, темная тема, премиум дизайн)
  if (mode === 'center') {
    return (
      <div className="flex flex-col h-[calc(100vh-200px)] max-w-5xl mx-auto bg-gradient-to-b from-gray-900/95 to-gray-800/95 backdrop-blur-xl rounded-3xl border border-gray-700/50 shadow-2xl overflow-hidden">
        {/* Заголовок - премиум стиль */}
        <div className="px-6 py-5 border-b border-gray-700/50 bg-gradient-to-r from-gray-800/80 to-gray-800/60 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
                <span className="text-white font-bold text-base">R</span>
              </div>
              <div>
                <h2 className="font-semibold text-gray-100 text-lg">RECEPTOR Assistant</h2>
                <p className="text-xs text-gray-400">AI-ассистент для ресторанного бизнеса</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="px-4 py-2 text-sm font-medium bg-gray-700/80 hover:bg-gray-600/80 text-gray-200 rounded-xl transition-all duration-200 hover:scale-105 border border-gray-600/50"
              >
                {showHistory ? 'Скрыть' : 'История'}
              </button>
              <button
                onClick={startNewConversation}
                className="px-4 py-2 text-sm font-medium bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-xl transition-all duration-200 hover:scale-105 shadow-lg shadow-purple-500/20"
              >
                Новая беседа
              </button>
            </div>
          </div>
        </div>
        
        {/* История бесед */}
        {showHistory && (
          <div className="px-6 py-4 border-b border-gray-700 bg-gray-800/50 max-h-64 overflow-y-auto">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Предыдущие беседы</h3>
            {conversations.length === 0 ? (
              <p className="text-sm text-gray-400">Нет сохраненных бесед</p>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <button
                    key={conv.conversation_id}
                    onClick={() => loadConversation(conv.conversation_id)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      conversationId === conv.conversation_id
                        ? 'bg-purple-600/30 border border-purple-500'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-200 truncate">
                      {conv.title}
                    </div>
                    <div className="text-xs text-gray-400 mt-1 truncate">
                      {conv.last_message}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {conv.message_count} сообщений • {new Date(conv.updated_at).toLocaleDateString('ru-RU')}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Сообщения - премиум стиль */}
        <div className="flex-1 overflow-y-auto px-8 py-8 space-y-8 scroll-smooth">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-300`}
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              {msg.role === 'assistant' && (
                <div className="w-9 h-9 bg-gradient-to-br from-purple-600/30 to-purple-700/30 rounded-xl flex items-center justify-center flex-shrink-0 border border-purple-500/20 shadow-lg">
                  <span className="text-purple-300 font-bold text-sm">R</span>
                </div>
              )}
              <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                <div
                  className={`rounded-2xl px-5 py-4 shadow-lg ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-purple-600 to-purple-700 text-white border border-purple-500/30'
                      : 'bg-gray-800/80 text-gray-100 border border-gray-700/50 backdrop-blur-sm'
                  }`}
                >
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed text-gray-100">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                        em: ({ children }) => <em className="italic text-gray-200">{children}</em>,
                        ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1 text-gray-200">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1 text-gray-200">{children}</ol>,
                        li: ({ children }) => <li className="ml-2">{children}</li>,
                        code: ({ children, className }) => {
                          const isInline = !className;
                          return isInline ? (
                            <code className="bg-gray-900/50 text-purple-300 px-1.5 py-0.5 rounded text-sm font-mono border border-gray-700/50">
                              {children}
                            </code>
                          ) : (
                            <code className="block bg-gray-900/70 text-gray-200 p-3 rounded-lg text-sm font-mono border border-gray-700/50 overflow-x-auto">
                              {children}
                            </code>
                          );
                        },
                        pre: ({ children }) => <pre className="mb-3">{children}</pre>,
                        h1: ({ children }) => <h1 className="text-xl font-bold mb-2 text-white">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 text-white">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-semibold mb-2 text-gray-100">{children}</h3>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-purple-500/50 pl-4 italic text-gray-300 my-3">
                            {children}
                          </blockquote>
                        ),
                        a: ({ children, href }) => (
                          <a href={href} className="text-purple-400 hover:text-purple-300 underline" target="_blank" rel="noopener noreferrer">
                            {children}
                          </a>
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  
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
                  <div className="mt-4 flex flex-wrap gap-2">
                    {msg.suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => handleSuggestion(suggestion)}
                        className="text-xs font-medium bg-gray-700/80 border border-gray-600/50 text-gray-200 rounded-full px-4 py-2 hover:bg-gray-600/80 hover:border-purple-500/50 hover:scale-105 transition-all duration-200"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-9 h-9 bg-gradient-to-br from-purple-600/20 to-purple-700/20 rounded-xl flex items-center justify-center flex-shrink-0 border border-purple-500/20 order-1">
                  <span className="text-purple-300 font-bold text-sm">Вы</span>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex items-start gap-4 justify-start">
              <div className="w-9 h-9 bg-gradient-to-br from-purple-600/30 to-purple-700/30 rounded-xl flex items-center justify-center flex-shrink-0 border border-purple-500/20 shadow-lg">
                <span className="text-purple-300 font-bold text-sm">R</span>
              </div>
              <div className="max-w-[80%]">
                <div className="bg-gray-800/80 border border-gray-700/50 rounded-2xl px-5 py-4 backdrop-blur-sm">
                  <div className="flex gap-2">
                    <span className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce"></span>
                    <span className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                    <span className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Ввод - премиум стиль */}
        <div className="px-8 py-5 border-t border-gray-700/50 bg-gradient-to-t from-gray-800/90 to-gray-800/70 backdrop-blur-sm">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Напишите сообщение..."
                rows={1}
                className="w-full px-5 py-4 pr-14 bg-gray-800/80 text-white border border-gray-700/50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 resize-none max-h-32 overflow-y-auto shadow-inner placeholder:text-gray-500 transition-all duration-200"
                disabled={loading}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="absolute right-3 bottom-3 w-10 h-10 bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-xl flex items-center justify-center hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-110 disabled:hover:scale-100 shadow-lg shadow-purple-500/20"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-3 text-center">
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


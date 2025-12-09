import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
const API = `${BACKEND_URL}/api`;

const CulinaryAssistant = ({ 
  userId, 
  mode = 'center', // 'center' | 'sidebar'
  onTechCardRequest = null, // Callback для создания техкарты из чата
  onTokenUpdate = null // Callback для обновления баланса токенов
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
  const [isListening, setIsListening] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(true); // Показывать сайдбар по умолчанию
  const [toast, setToast] = useState(null); // Toast notification state
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Автоскролл к последнему сообщению (только внутри контейнера, не всей страницы)
  useEffect(() => {
    if (messagesContainerRef.current && messagesEndRef.current) {
      // Используем scrollTo с блокировкой скролла страницы
      const container = messagesContainerRef.current;
      const scrollToBottom = () => {
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        });
      };
      
      // Используем requestAnimationFrame для плавности
      requestAnimationFrame(() => {
        scrollToBottom();
      });
    }
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

  // Инициализация Web Speech API для голосового ввода
  useEffect(() => {
    if (mode === 'center' && 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'ru-RU';
      
      recognition.onstart = () => {
        setIsListening(true);
      };
      
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInput(prev => prev + (prev ? ' ' : '') + transcript);
        setIsListening(false);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'not-allowed') {
          alert('Разрешите доступ к микрофону для голосового ввода');
        }
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      recognitionRef.current = recognition;
      
      return () => {
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
      };
    }
  }, [mode]);

  // Функция для начала/остановки голосового ввода
  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Голосовой ввод не поддерживается в вашем браузере');
      return;
    }
    
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error('Error starting recognition:', error);
        setIsListening(false);
      }
    }
  };

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API}/assistant/conversations`, {
        params: { 
          user_id: userId || 'demo_user',
          limit: 100 // Загружаем до 100 бесед
        }
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
      // Загружаем ВСЕ сообщения без ограничений
      const loadedMessages = (response.data.messages || []).map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp || new Date()),
        tool_calls: msg.tool_calls || []
      }));
      
      // Если нет сообщений, добавляем приветственное
      if (loadedMessages.length === 0) {
        loadedMessages.push({
          role: 'assistant',
          content: 'Привет! Я RECEPTOR — твой AI-ассистент в ресторанном бизнесе. Я специально обучен делать твою жизнь проще, кухню эффективнее, а ресторан прибыльнее. Спроси меня, что я могу.',
          timestamp: new Date()
        });
      }
      
      setMessages(loadedMessages);
      setConversationId(convId);
      setShowHistorySidebar(false); // Закрываем сайдбар после загрузки
    } catch (error) {
      console.error('Error loading conversation:', error);
      alert('Ошибка загрузки беседы. Попробуйте еще раз.');
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

    // Check token balance before sending (check for chat with tools - higher cost)
    try {
      const balanceCheck = await axios.post(`${API}/user/${userId || 'demo_user'}/tokens/check`, null, {
        params: { operation_type: 'ai_chat_with_tools' }
      });
      
      if (!balanceCheck.data.has_enough) {
        showToast(`Недостаточно токенов. Требуется: ${balanceCheck.data.required_tokens} NC, доступно: ${balanceCheck.data.current_balance} NC`, 'error');
        return;
      }
    } catch (error) {
      console.error('Error checking token balance:', error);
      // Continue anyway if check fails (for demo users)
    }

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
      
      // Show token deduction notification
      if (response.data.tokens_deducted) {
        const toolCallsText = response.data.tool_calls && response.data.tool_calls.length > 0 
          ? ` (с использованием инструментов)` 
          : '';
        showToast(`Списано ${response.data.tokens_deducted} NC${toolCallsText}. Баланс: ${response.data.tokens_balance} NC`, 'success');
        
        // Update parent component's token balance
        if (onTokenUpdate && response.data.tokens_balance !== undefined) {
          onTokenUpdate(response.data.tokens_balance);
        }
      }
      
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
      
      // Handle token balance errors
      if (error.response?.status === 402) {
        showToast(errorMessage, 'error');
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Недостаточно токенов для выполнения операции. Пожалуйста, пополните баланс.`,
          timestamp: new Date()
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Извините, произошла ошибка: ${errorMessage}. Попробуйте еще раз.`,
          timestamp: new Date()
        }]);
      }
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
      e.stopPropagation(); // Предотвращаем всплытие события
      sendMessage();
      return false;
    }
  };

  const handleKeyDown = (e) => {
    // Дополнительная защита от скролла страницы
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
    }
  };

  // Центральный режим (как ChatGPT, темная тема, премиум дизайн)
  if (mode === 'center') {
    return (
      <div className="flex gap-4 h-[calc(100vh-200px)] max-w-7xl mx-auto">
        {/* Сайдбар с историей бесед */}
        {showHistorySidebar && (
          <div className="w-80 flex-shrink-0 bg-gray-800/90 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-xl overflow-hidden flex flex-col">
            <div className="px-4 py-4 border-b border-gray-700/50 bg-gray-800/80">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-200 text-sm">История бесед</h3>
                <button
                  onClick={() => setShowHistorySidebar(false)}
                  className="text-gray-400 hover:text-gray-200 transition-colors"
                  title="Скрыть историю"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <button
                onClick={startNewConversation}
                className="w-full px-4 py-2 text-sm font-medium bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-xl transition-all duration-200 hover:scale-105 shadow-lg shadow-purple-500/20"
              >
                + Новая беседа
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto px-4 py-2">
              {conversations.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-400">Нет сохраненных бесед</p>
                  <p className="text-xs text-gray-500 mt-2">Начните новую беседу</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {conversations.map((conv) => (
                    <button
                      key={conv.conversation_id}
                      onClick={() => loadConversation(conv.conversation_id)}
                      className={`w-full text-left px-3 py-3 rounded-xl transition-all duration-200 ${
                        conversationId === conv.conversation_id
                          ? 'bg-purple-600/30 border-2 border-purple-500/50 shadow-lg shadow-purple-500/10'
                          : 'bg-gray-700/50 hover:bg-gray-700 border border-gray-600/30'
                      }`}
                    >
                      <div className="text-sm font-medium text-gray-200 truncate mb-1">
                        {conv.title || 'Беседа без названия'}
                      </div>
                      <div className="text-xs text-gray-400 truncate mb-2">
                        {conv.last_message || 'Нет сообщений'}
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{conv.message_count || 0} сообщений</span>
                        <span>{new Date(conv.updated_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Основной чат */}
        <div className="flex-1 flex flex-col bg-gradient-to-b from-gray-900/95 to-gray-800/95 backdrop-blur-xl rounded-3xl border border-gray-700/50 shadow-2xl overflow-hidden">
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
              {!showHistorySidebar && (
                <button
                  onClick={() => setShowHistorySidebar(true)}
                  className="px-4 py-2 text-sm font-medium bg-gray-700/80 hover:bg-gray-600/80 text-gray-200 rounded-xl transition-all duration-200 hover:scale-105 border border-gray-600/50"
                  title="Показать историю бесед"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Сообщения - премиум стиль */}
        <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-8 py-8 space-y-8 scroll-smooth">
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
                onKeyDown={handleKeyDown}
                placeholder="Напишите сообщение..."
                rows={1}
                className="w-full px-5 py-4 pr-24 bg-gray-800/80 text-white border border-gray-700/50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 resize-none max-h-32 overflow-y-auto shadow-inner placeholder:text-gray-500 transition-all duration-200"
                disabled={loading}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
              />
              {/* Кнопка голосового ввода */}
              <button
                onClick={toggleVoiceInput}
                disabled={loading || !recognitionRef.current}
                className={`absolute right-14 bottom-3 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                  isListening
                    ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                    : 'bg-gray-700/80 hover:bg-gray-600/80 text-gray-300'
                } disabled:opacity-30 disabled:cursor-not-allowed`}
                title={isListening ? 'Остановить запись' : 'Голосовой ввод'}
              >
                {isListening ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
              </button>
              {/* Кнопка отправки */}
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
          <div className="flex items-center justify-between mt-3">
            <p className="text-xs text-gray-500">
              {isListening && (
                <span className="text-red-400 animate-pulse">🎤 Запись...</span>
              )}
            </p>
            <p className="text-xs text-gray-500">
              Каждое сообщение стоит 5 токенов
            </p>
          </div>
        </div>
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
            onKeyDown={handleKeyDown}
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
      
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transition-all duration-300 ${
          toast.type === 'error' 
            ? 'bg-red-600 text-white' 
            : toast.type === 'success' 
            ? 'bg-green-600 text-white' 
            : 'bg-blue-600 text-white'
        }`}>
          <div className="flex items-center gap-2">
            <span>{toast.message}</span>
            <button
              onClick={() => setToast(null)}
              className="ml-2 text-white hover:text-gray-200"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CulinaryAssistant;


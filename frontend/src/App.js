import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Menu, Plus, ChefHat, FileText, Settings, Database, Loader2, Store, Link2, MessageSquare, Trash2 } from 'lucide-react';
import axios from 'axios';
import VenueProfile from './components/VenueProfile';
import Integrations from './components/Integrations';

const API_URL = process.env.REACT_APP_API_URL || 'https://receptor-preprod-production.up.railway.app/api';

// Временный user_id (потом заменим на авторизацию)
const USER_ID = 'default_user';

const WELCOME_MESSAGE = {
  role: 'assistant',
  content: 'Привет! Я RECEPTOR Copilot. Я знаю всё о ресторанном бизнесе, стандартах HACCP, СанПиН, и интегрирован с вашей системой iiko.\n\nЧем могу помочь сегодня?'
};

function App() {
  const [currentPage, setCurrentPage] = useState('chat');
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // Chat history state
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Load chat history on mount
  useEffect(() => {
    loadChatHistory();
  }, []);

  // Auto-save chat after each message
  useEffect(() => {
    if (messages.length > 1 && currentPage === 'chat') {
      saveCurrentChat();
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ============ CHAT HISTORY FUNCTIONS ============

  const loadChatHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await axios.get(`${API_URL}/history/chats/${USER_ID}`);
      setChatHistory(response.data || []);
    } catch (error) {
      console.error('Error loading chat history:', error);
    } finally {
      setHistoryLoading(false);
    }
  };

  const saveCurrentChat = async () => {
    // Don't save if only welcome message
    if (messages.length <= 1) return;
    
    try {
      if (currentChatId) {
        // Update existing chat
        await axios.put(`${API_URL}/history/chat/${currentChatId}`, {
          messages: messages
        });
      } else {
        // Create new chat
        const response = await axios.post(`${API_URL}/history/chats`, {
          user_id: USER_ID,
          messages: messages
        });
        setCurrentChatId(response.data.id);
        // Refresh history
        loadChatHistory();
      }
    } catch (error) {
      console.error('Error saving chat:', error);
    }
  };

  const loadChat = async (chatId) => {
    try {
      const response = await axios.get(`${API_URL}/history/chat/${chatId}`);
      setMessages(response.data.messages || [WELCOME_MESSAGE]);
      setCurrentChatId(chatId);
      setCurrentPage('chat');
    } catch (error) {
      console.error('Error loading chat:', error);
    }
  };

  const startNewChat = () => {
    setMessages([WELCOME_MESSAGE]);
    setCurrentChatId(null);
    setCurrentPage('chat');
  };

  const deleteChat = async (chatId, e) => {
    e.stopPropagation();
    if (!window.confirm('Удалить этот чат?')) return;
    
    try {
      await axios.delete(`${API_URL}/history/chat/${chatId}`);
      setChatHistory(prev => prev.filter(c => c.id !== chatId));
      
      // If deleted current chat, start new
      if (chatId === currentChatId) {
        startNewChat();
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  // ============ CHAT FUNCTIONS ============

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat/message`, {
        messages: [...messages, userMessage],
        user_id: USER_ID
      });
      
      setMessages(prev => [...prev, response.data]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Извините, произошла ошибка соединения с сервером. Пожалуйста, попробуйте еще раз.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-64' : 'w-0'} bg-gray-950 border-r border-gray-800 transition-all duration-300 flex flex-col flex-shrink-0 overflow-hidden`}>
        <div className="p-4 flex items-center gap-2 border-b border-gray-800">
          <ChefHat className="text-emerald-500 w-8 h-8" />
          <span className="font-bold text-xl tracking-tight">RECEPTOR</span>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {/* New Chat Button */}
          <button 
            onClick={startNewChat}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-medium border bg-emerald-600/10 text-emerald-500 border-emerald-600/20 hover:bg-emerald-600/20"
          >
            <Plus size={16} />
            Новый чат
          </button>
          
          {/* Chat History */}
          <div className="mt-6 text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 flex items-center justify-between">
            <span>История</span>
            {historyLoading && <Loader2 size={12} className="animate-spin" />}
          </div>
          
          <div className="space-y-1 mt-2">
            {chatHistory.length === 0 && !historyLoading && (
              <p className="text-gray-600 text-xs px-3 py-2">Нет сохранённых чатов</p>
            )}
            {chatHistory.map((chat) => (
              <button 
                key={chat.id}
                onClick={() => loadChat(chat.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate flex items-center justify-between group ${
                  chat.id === currentChatId 
                    ? 'bg-gray-800 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1">
                  <MessageSquare size={14} className="flex-shrink-0" />
                  <span className="truncate">{chat.title}</span>
                </div>
                <button
                  onClick={(e) => deleteChat(chat.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-700 rounded transition-all"
                >
                  <Trash2 size={12} className="text-gray-500 hover:text-red-400" />
                </button>
              </button>
            ))}
          </div>
        </div>

        {/* Bottom Navigation */}
        <div className="p-4 border-t border-gray-800 space-y-1">
          <button 
            onClick={() => setCurrentPage('profile')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              currentPage === 'profile'
                ? 'bg-emerald-600/10 text-emerald-500'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Store size={16} />
            Профиль заведения
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg text-sm transition-colors">
            <Database size={16} />
            База знаний
          </button>
          <button 
            onClick={() => setCurrentPage('integrations')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              currentPage === 'integrations'
                ? 'bg-emerald-600/10 text-emerald-500'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Link2 size={16} />
            Интеграции (iiko)
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg text-sm transition-colors">
            <Settings size={16} />
            Настройки
          </button>
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-14 bg-gray-900/50 backdrop-blur border-b border-gray-800 flex items-center justify-between px-4 z-10">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">GPT-4o + RAG + iiko</span>
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
          </div>
          <div className="w-8"></div>
        </header>

        {/* Content based on current page */}
        {currentPage === 'profile' ? (
          <VenueProfile userId={USER_ID} onBack={() => setCurrentPage('chat')} />
        ) : currentPage === 'integrations' ? (
          <Integrations userId={USER_ID} apiUrl={API_URL} />
        ) : (
          <>
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
              <div className="max-w-3xl mx-auto space-y-6 pb-4">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'assistant' ? 'bg-emerald-600' : 'bg-gray-700'}`}>
                      {msg.role === 'assistant' ? <ChefHat size={16} className="text-white" /> : <div className="text-xs font-bold">U</div>}
                    </div>
                    <div className={`rounded-2xl px-5 py-3.5 max-w-[85%] shadow-sm ${
                      msg.role === 'user' 
                        ? 'bg-gray-800 text-gray-100 rounded-tr-none' 
                        : 'bg-gray-900 border border-gray-800 text-gray-100 rounded-tl-none'
                    }`}>
                      <ReactMarkdown 
                        className="prose prose-invert prose-sm max-w-none leading-relaxed"
                        components={{
                          h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-2 text-white" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-2 text-white mt-4" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-base font-bold mb-1 text-white mt-3" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li className="text-gray-300" {...props} />,
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0 text-gray-300" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                          a: ({node, ...props}) => <a className="text-emerald-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                          blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-gray-700 pl-4 py-1 my-2 bg-gray-800/50 rounded-r text-gray-400 italic" {...props} />,
                          code: ({node, inline, className, children, ...props}) => {
                            return inline ? (
                              <code className="bg-gray-800 px-1 py-0.5 rounded text-sm text-emerald-300 font-mono" {...props}>{children}</code>
                            ) : (
                              <code className="block bg-gray-950 p-3 rounded-lg text-sm font-mono overflow-x-auto my-2 border border-gray-800" {...props}>{children}</code>
                            )
                          }
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))}
                {loading && (
                   <div className="flex gap-4">
                     <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center flex-shrink-0 animate-pulse">
                       <ChefHat size={16} className="text-white" />
                     </div>
                     <div className="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-none px-5 py-3.5 flex items-center">
                       <Loader2 className="animate-spin text-emerald-500 mr-2" size={16} />
                       <span className="text-gray-400 text-sm">Думаю...</span>
                     </div>
                   </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Area */}
            <div className="p-4 bg-gray-900/80 backdrop-blur-sm border-t border-gray-800">
              <div className="max-w-3xl mx-auto">
                <form onSubmit={handleSubmit} className="relative group">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Спроси о HACCP, выручке или попроси создать техкарту..."
                    className="w-full bg-gray-800 text-white placeholder-gray-500 border border-gray-700 rounded-xl py-4 pl-5 pr-12 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all shadow-lg"
                    disabled={loading}
                  />
                  <button 
                    type="submit" 
                    disabled={!input.trim() || loading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 disabled:hover:bg-emerald-600 transition-colors shadow-lg shadow-emerald-900/20"
                  >
                    <Send size={18} />
                  </button>
                </form>
                <div className="mt-2 text-center text-xs text-gray-500">
                  RECEPTOR Copilot может допускать ошибки. Проверяйте важную информацию.
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;

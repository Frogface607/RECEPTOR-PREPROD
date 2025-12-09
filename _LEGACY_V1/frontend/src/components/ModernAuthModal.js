import React, { useState } from 'react';
import GoogleAuth from './GoogleAuth';

/**
 * 🚀 Современный модал авторизации
 * Как в SaaS продуктах: красиво, просто, быстро
 */

const ModernAuthModal = ({ isOpen, onClose, onLogin, onRegister, onGoogleSuccess }) => {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      if (mode === 'login') {
        await onLogin(email, password);
      } else {
        await onRegister(email, password);
      }
    } catch (error) {
      console.error('Auth error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSuccess = (user, token) => {
    console.log('✅ Google auth success:', user);
    
    // Сохраняем пользователя и токен в localStorage
    localStorage.setItem('receptor_user', JSON.stringify(user));
    localStorage.setItem('receptor_token', token);
    console.log('✅ User saved to localStorage');
    
    // Если есть кастомный обработчик - вызываем его (для обновления состояния)
    if (onGoogleSuccess) {
      onGoogleSuccess(user, token);
    }
    
    // НЕ вызываем onLogin - это для email/password, не для Google!
    // Google авторизация уже завершена, просто сохраняем данные
    
    // Закрываем модал
    onClose();
    console.log('✅ Modal closed, user state updated');
  };

  const handleGoogleError = (error) => {
    console.error('Google auth error:', error);
    // Показываем пользователю ошибку
    alert('Ошибка авторизации. Попробуйте позже или используйте email.');
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-md">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">
            {mode === 'login' ? 'Добро пожаловать!' : 'Создать аккаунт'}
          </h2>
          <p className="text-gray-400">
            {mode === 'login' 
              ? 'Войдите в свой аккаунт RECEPTOR PRO' 
              : 'Начните создавать техкарты уже сегодня'
            }
          </p>
        </div>

        {/* Google OAuth */}
        <div className="mb-6">
          <GoogleAuth 
            mode={mode}
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
          />
        </div>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-700"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-gray-900 text-gray-400">или</span>
          </div>
        </div>

        {/* Email Form */}
        <form onSubmit={handleEmailAuth} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="your@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Пароль
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="••••••••"
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '⏳ Загрузка...' : (mode === 'login' ? 'Войти' : 'Создать аккаунт')}
          </button>
        </form>

        {/* Switch Mode */}
        <div className="text-center mt-6">
          <p className="text-gray-400">
            {mode === 'login' ? 'Нет аккаунта?' : 'Уже есть аккаунт?'}
            <button
              onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
              className="text-blue-400 hover:text-blue-300 ml-2 font-medium transition-colors"
            >
              {mode === 'login' ? 'Зарегистрироваться' : 'Войти'}
            </button>
          </p>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default ModernAuthModal;

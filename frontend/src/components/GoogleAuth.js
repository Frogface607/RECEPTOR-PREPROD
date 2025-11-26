import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { loadGoogleAPI, GOOGLE_CLIENT_ID } from '../config/googleAuth';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
const API = `${BACKEND_URL}/api`;

/**
 * 🔐 Google OAuth компонент для современной авторизации
 * Как в SaaS продуктах: один клик, красиво, быстро
 */

const GoogleAuth = ({ onSuccess, onError, mode = 'login' }) => {
  const [isGoogleLoaded, setIsGoogleLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Загружаем Google API при монтировании компонента
    loadGoogleAPI()
      .then(() => {
        // Проверяем что client_id установлен
        if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === 'your-google-client-id.apps.googleusercontent.com') {
          console.warn('⚠️ Google Client ID not configured. Google OAuth will not work.');
          setIsGoogleLoaded(true);
          return;
        }
        
        // Инициализируем Google OAuth только один раз
        if (window.google && window.google.accounts) {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: async (response) => {
              console.log('🔵 Google OAuth callback received');
              try {
                // Декодируем JWT токен от Google
                const token = response.credential;
                const payload = JSON.parse(atob(token.split('.')[1]));
                console.log('🔵 Google payload decoded:', payload.email);
                
                // Отправляем данные на backend
                console.log('🔵 Sending to backend:', `${API}/v1/auth/google`);
                const authResponse = await axios.post(`${API}/v1/auth/google`, {
                  email: payload.email,
                  name: payload.name || payload.email.split('@')[0],
                  google_id: payload.sub,
                  avatar_url: payload.picture
                });
                
                console.log('🔵 Backend response:', authResponse.data);
                
                if (authResponse.data.success && onSuccess) {
                  console.log('🔵 Calling onSuccess callback');
                  onSuccess(authResponse.data.user, authResponse.data.token);
                } else {
                  console.warn('⚠️ Backend response missing success or onSuccess handler');
                }
              } catch (error) {
                console.error('❌ Google auth callback error:', error);
                if (onError) {
                  onError(error);
                }
              }
            },
            auto_select: false,
            cancel_on_tap_outside: true
          });
        }
        setIsGoogleLoaded(true);
      })
      .catch(error => {
        console.error('Failed to load Google API:', error);
        setIsGoogleLoaded(true); // Показываем кнопку даже если API не загрузился
      });
  }, []);

  const handleGoogleAuth = async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    
    try {
      if (window.google && window.google.accounts) {
        // Реальная Google OAuth
        await handleRealGoogleAuth();
      } else {
        // Fallback на mock авторизацию
        await handleMockGoogleAuth();
      }
    } catch (error) {
      console.error('Google OAuth error:', error);
      if (onError) {
        onError(error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRealGoogleAuth = async () => {
    // Проверяем что client_id установлен
    if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === 'your-google-client-id.apps.googleusercontent.com') {
      if (onError) {
        onError(new Error('Google Client ID not configured. Please set REACT_APP_GOOGLE_CLIENT_ID in environment variables.'));
      }
      return;
    }
    
    if (!window.google || !window.google.accounts) {
      if (onError) {
        onError(new Error('Google API not loaded'));
      }
      return;
    }
    
    try {
      // Используем Google One Tap (показывается автоматически)
      // Или используем renderButton для кнопки
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          // One Tap не показан - используем кнопку
          // Кнопка уже рендерится в компоненте, но нужно обработать клик
          // Для этого используем renderButton
          const buttonContainer = document.getElementById('google-signin-button');
          if (buttonContainer) {
            window.google.accounts.id.renderButton(buttonContainer, {
              theme: 'outline',
              size: 'large',
              width: '100%',
              text: mode === 'login' ? 'signin_with' : 'signup_with',
              type: 'standard'
            });
          }
        }
      });
    } catch (error) {
      console.error('Google auth error:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  const handleMockGoogleAuth = async () => {
    // Fallback: если Google API недоступен, используем реальный backend
    console.log('Google API недоступен, используем backend авторизацию');
    
    try {
      // Получаем backend URL из env или используем дефолтный
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
      
      // Пробуем отправить на backend - но нужны реальные данные от Google
      // Пока показываем ошибку, что нужна реальная Google авторизация
      if (onError) {
        onError(new Error('Google OAuth недоступен. Пожалуйста, используйте email/password для входа или проверьте настройки Google OAuth.'));
      }
    } catch (error) {
      console.error('Google auth error:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  // Проверяем что Google Client ID настроен
  const isGoogleConfigured = GOOGLE_CLIENT_ID && GOOGLE_CLIENT_ID !== 'your-google-client-id.apps.googleusercontent.com';
  
  // Если Google Client ID не настроен, не показываем кнопку
  if (!isGoogleConfigured) {
    return null;
  }
  
  return (
    <>
      <div id="google-signin-button" className="w-full"></div>
      <button
        onClick={handleGoogleAuth}
        disabled={isLoading || !isGoogleLoaded}
        className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-900 font-medium py-3 px-4 rounded-lg border border-gray-300 transition-all duration-200 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            Загрузка...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {mode === 'login' ? 'Войти через Google' : 'Регистрация через Google'}
          </>
        )}
      </button>
    </>
  );
};

export default GoogleAuth;

/**
 * 🔐 Google OAuth 2.0 Configuration
 * Конфигурация для реальной Google авторизации
 */

// Google OAuth Client ID (получить в Google Cloud Console)
export const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || 'your-google-client-id.apps.googleusercontent.com';

// Google OAuth Scope
export const GOOGLE_SCOPE = 'openid email profile';

// Google OAuth Discovery Document
export const GOOGLE_DISCOVERY_DOC = 'https://accounts.google.com/.well-known/openid_configuration';

// Google OAuth Configuration
export const GOOGLE_AUTH_CONFIG = {
  client_id: GOOGLE_CLIENT_ID,
  scope: GOOGLE_SCOPE,
  discovery_docs: [GOOGLE_DISCOVERY_DOC],
  ux_mode: 'popup',
  redirect_uri: window.location.origin,
  response_type: 'code',
  access_type: 'offline',
  prompt: 'select_account'
};

/**
 * Инициализация Google OAuth (deprecated - теперь инициализация в компоненте)
 * Оставлено для обратной совместимости
 */
export const initGoogleAuth = () => {
  return new Promise((resolve, reject) => {
    if (window.google) {
      // Инициализация теперь в компоненте GoogleAuth
      resolve();
    } else {
      reject(new Error('Google API not loaded'));
    }
  });
};

/**
 * Обработчик Google OAuth callback
 */
export const handleGoogleCallback = (response) => {
  console.log('Google OAuth response:', response);
  // Здесь будет обработка токена
  return response;
};

/**
 * Загрузка Google API
 */
export const loadGoogleAPI = () => {
  return new Promise((resolve, reject) => {
    if (window.google) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google API'));
    document.head.appendChild(script);
  });
};

/**
 * 🔍 Скрипт для проверки настройки Google OAuth
 * Запусти: node check_google_oauth.js
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Проверка настройки Google OAuth...\n');

// Проверяем frontend/.env
const frontendEnvPath = path.join(__dirname, 'frontend', '.env');
let frontendEnvExists = fs.existsSync(frontendEnvPath);
let googleClientId = null;

if (frontendEnvExists) {
  const envContent = fs.readFileSync(frontendEnvPath, 'utf8');
  // Ищем REACT_APP_GOOGLE_CLIENT_ID в разных форматах
  const lines = envContent.split('\n');
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('REACT_APP_GOOGLE_CLIENT_ID=')) {
      googleClientId = trimmedLine.split('=')[1].trim();
      break;
    }
  }
}

// Проверяем backend/google_auth.py
const backendAuthPath = path.join(__dirname, 'backend', 'google_auth.py');
const backendAuthExists = fs.existsSync(backendAuthPath);

// Проверяем frontend компоненты
const googleAuthComponentPath = path.join(__dirname, 'frontend', 'src', 'components', 'GoogleAuth.js');
const googleAuthComponentExists = fs.existsSync(googleAuthComponentPath);

console.log('📋 Результаты проверки:\n');

// Frontend .env
console.log('1. Frontend .env файл:');
if (frontendEnvExists) {
  console.log('   ✅ Файл существует');
  if (googleClientId) {
    if (googleClientId === 'your-google-client-id.apps.googleusercontent.com') {
      console.log('   ⚠️  Google Client ID не настроен (используется дефолтное значение)');
    } else {
      console.log(`   ✅ Google Client ID настроен: ${googleClientId.substring(0, 20)}...`);
    }
  } else {
    console.log('   ⚠️  REACT_APP_GOOGLE_CLIENT_ID не найден в .env');
  }
} else {
  console.log('   ❌ Файл не существует');
  console.log('   💡 Создай frontend/.env с REACT_APP_GOOGLE_CLIENT_ID');
}

console.log('');

// Backend
console.log('2. Backend Google Auth:');
if (backendAuthExists) {
  console.log('   ✅ backend/google_auth.py существует');
  console.log('   ✅ Endpoint /api/v1/auth/google готов');
} else {
  console.log('   ❌ backend/google_auth.py не найден');
}

console.log('');

// Frontend компонент
console.log('3. Frontend компонент:');
if (googleAuthComponentExists) {
  console.log('   ✅ frontend/src/components/GoogleAuth.js существует');
} else {
  console.log('   ❌ frontend/src/components/GoogleAuth.js не найден');
}

console.log('');

// Итоговый статус
console.log('📊 ИТОГОВЫЙ СТАТУС:\n');

if (backendAuthExists && googleAuthComponentExists) {
  if (googleClientId && googleClientId !== 'your-google-client-id.apps.googleusercontent.com') {
    console.log('✅ ВСЁ ГОТОВО! Google OAuth должен работать.');
    console.log('   Просто перезапусти frontend и проверь работу.');
  } else {
    console.log('⚠️  КОД ГОТОВ, но нужно настроить Google Client ID:');
    console.log('   1. Получи Client ID в Google Cloud Console');
    console.log('   2. Добавь в frontend/.env: REACT_APP_GOOGLE_CLIENT_ID=твой-id');
    console.log('   3. Перезапусти frontend');
    console.log('\n   📖 Подробная инструкция: GOOGLE_OAUTH_QUICK_SETUP.md');
  }
} else {
  console.log('❌ Что-то не так с файлами. Проверь структуру проекта.');
}

console.log('');




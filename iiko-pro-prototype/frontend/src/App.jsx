/**
 * 🏢 iiko PRO Module - Frontend
 * Простой интерфейс для подключения и экспорта в iiko
 * Цель: максимум 500 строк кода
 */

import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8002';

function App() {
  // ============================================================================
  // СОСТОЯНИЯ (минимум useState)
  // ============================================================================
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [credentials, setCredentials] = useState({
    host: 'edison-bar.iiko.it',
    login: 'Sergey',
    password: '',
    user_id: 'demo_user'
  });
  const [isConnecting, setIsConnecting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportData, setExportData] = useState({
    techcard_ids: ['tc1', 'tc2', 'tc3'],
    organization_id: 'default'
  });

  // ============================================================================
  // ЭФФЕКТЫ
  // ============================================================================
  useEffect(() => {
    fetchStatus();
  }, []);

  // ============================================================================
  // API ФУНКЦИИ
  // ============================================================================
  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/iiko/status?user_id=${credentials.user_id}`);
      const data = await response.json();
      setConnectionStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const response = await fetch(`${API_BASE}/iiko/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Connection successful:', result);
        await fetchStatus(); // Обновляем статус
      } else {
        const error = await response.json();
        alert(`Ошибка подключения: ${error.detail}`);
      }
    } catch (error) {
      alert(`Ошибка: ${error.message}`);
    }
    setIsConnecting(false);
  };

  const handleExport = async () => {
    if (connectionStatus?.status !== 'connected') {
      alert('Сначала подключитесь к iiko');
      return;
    }

    setIsExporting(true);
    try {
      const response = await fetch(`${API_BASE}/iiko/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...exportData,
          user_id: credentials.user_id
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Экспорт успешен! Экспортировано: ${result.exported_count} техкарт`);
        await fetchStatus(); // Обновляем статус
      } else {
        const error = await response.json();
        alert(`Ошибка экспорта: ${error.detail}`);
      }
    } catch (error) {
      alert(`Ошибка: ${error.message}`);
    }
    setIsExporting(false);
  };

  // ============================================================================
  // RENDER
  // ============================================================================
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">🏢 iiko PRO Module</h1>
          <p className="text-purple-300">Автономный модуль для интеграции с iiko RMS</p>
          <p className="text-sm text-gray-400 mt-2">
            Версия 1.0.0 • 3 эндпоинта • Микросервис
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Левая панель - Подключение */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              🔌 Подключение к iiko RMS
            </h2>
            
            {/* Статус подключения */}
            <div className="mb-4 p-3 rounded-lg bg-black/20">
              <div className="text-sm font-medium">Статус:</div>
              <div className={`text-lg font-bold ${
                connectionStatus?.status === 'connected' ? 'text-green-400' : 
                connectionStatus?.status === 'expired' ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {connectionStatus?.status === 'connected' && '✅ Подключено'}
                {connectionStatus?.status === 'expired' && '⏰ Сессия истекла'}  
                {connectionStatus?.status === 'not_connected' && '❌ Не подключено'}
              </div>
              {connectionStatus?.host && (
                <div className="text-sm text-gray-300 mt-1">
                  Хост: {connectionStatus.host} | Логин: {connectionStatus.login}
                </div>
              )}
            </div>

            {/* Форма подключения */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Хост сервера:</label>
                <input
                  type="text"
                  value={credentials.host}
                  onChange={(e) => setCredentials({...credentials, host: e.target.value})}
                  className="w-full px-3 py-2 bg-black/30 rounded-lg border border-white/20 text-white"
                  placeholder="edison-bar.iiko.it"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Логин:</label>
                <input
                  type="text"
                  value={credentials.login}
                  onChange={(e) => setCredentials({...credentials, login: e.target.value})}
                  className="w-full px-3 py-2 bg-black/30 rounded-lg border border-white/20 text-white"
                  placeholder="Ваш логин iiko"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Пароль:</label>
                <input
                  type="password"
                  value={credentials.password}
                  onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                  className="w-full px-3 py-2 bg-black/30 rounded-lg border border-white/20 text-white"
                  placeholder="Ваш пароль iiko"
                />
              </div>

              <button
                onClick={handleConnect}
                disabled={isConnecting || !credentials.password}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-all"
              >
                {isConnecting ? '🔄 Подключение...' : '🔌 Подключиться'}
              </button>
            </div>
          </div>

          {/* Правая панель - Экспорт */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              📤 Экспорт техкарт
            </h2>

            {/* Статистика */}
            <div className="mb-4 p-3 rounded-lg bg-black/20">
              <div className="text-sm font-medium">Статистика экспорта:</div>
              <div className="text-lg font-bold text-blue-400">
                Всего экспортировано: {connectionStatus?.exported_count || 0} техкарт
              </div>
              {connectionStatus?.last_export && (
                <div className="text-sm text-gray-300 mt-1">
                  Последний экспорт: {new Date(connectionStatus.last_export).toLocaleString()}
                </div>
              )}
            </div>

            {/* Форма экспорта */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">ID техкарт для экспорта:</label>
                <textarea
                  value={exportData.techcard_ids.join('\n')}
                  onChange={(e) => setExportData({
                    ...exportData, 
                    techcard_ids: e.target.value.split('\n').filter(id => id.trim())
                  })}
                  className="w-full px-3 py-2 bg-black/30 rounded-lg border border-white/20 text-white h-24"
                  placeholder="tc1&#10;tc2&#10;tc3"
                />
                <div className="text-xs text-gray-400 mt-1">
                  По одному ID на строку. Всего: {exportData.techcard_ids.length}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">ID организации:</label>
                <input
                  type="text"
                  value={exportData.organization_id}
                  onChange={(e) => setExportData({...exportData, organization_id: e.target.value})}
                  className="w-full px-3 py-2 bg-black/30 rounded-lg border border-white/20 text-white"
                  placeholder="default"
                />
              </div>

              <button
                onClick={handleExport}
                disabled={isExporting || connectionStatus?.status !== 'connected' || exportData.techcard_ids.length === 0}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-all"
              >
                {isExporting ? '📤 Экспорт...' : `📤 Экспортировать ${exportData.techcard_ids.length} техкарт`}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-400 text-sm">
          <p>iiko PRO Module • Receptor Ecosystem • $99/месяц</p>
          <p className="mt-1">
            🎯 Revenue Share с iiko • 69,000+ ресторанов в базе
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
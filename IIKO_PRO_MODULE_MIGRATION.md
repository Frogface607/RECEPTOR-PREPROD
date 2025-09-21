# 🏢 iiko PRO MODULE - Детальный план миграции

## 🎯 ЦЕЛЬ: Первый автономный микросервис

Извлекаем весь iiko функционал из монолита в отдельное приложение с 3 эндпоинтами.

## 📋 ЧТО ИЗВЛЕКАЕМ ИЗ ТЕКУЩЕГО КОДА

### Из Backend:
```
/app/backend/receptor_agent/routes/iiko_rms_v2.py  ✅
/app/backend/receptor_agent/routes/iiko_v2.py      ✅  
/app/backend/receptor_agent/routes/iiko_xlsx_import.py ✅
/app/backend/receptor_agent/integrations/iiko_rms_service.py ✅
/app/backend/receptor_agent/exports/ (iiko related) ✅
```

### Из Frontend (App.js):
```javascript
// iiko RMS состояния (строки ~350-400)
const [iikoRmsConnection, setIikoRmsConnection] = useState({});
const [showIikoRmsModal, setShowIikoRmsModal] = useState(false);
const [iikoRmsCredentials, setIikoRmsCredentials] = useState({});

// iiko Export функции (строки ~5000-6000)  
const handleIikoExport = async () => { ... }
const fetchIikoRmsStatus = async () => { ... }
```

## 🏗️ НОВАЯ АРХИТЕКТУРА iiko PRO

### Структура проекта:
```
iiko-pro-module/
├── backend/
│   ├── main.py                 # FastAPI app (3 endpoints)
│   ├── models/
│   │   ├── connection.py       # Модели подключения
│   │   └── export.py          # Модели экспорта
│   ├── services/
│   │   ├── iiko_client.py     # Клиент iiko API
│   │   └── techcard_export.py # Экспорт техкарт
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Простой интерфейс (500 строк max)
│   │   ├── components/
│   │   │   ├── ConnectionForm.jsx
│   │   │   ├── ExportPanel.jsx
│   │   │   └── StatusDisplay.jsx
│   │   └── hooks/
│   │       └── useIiko.js     # Все iiko логика
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🔌 ТРИ ЭНДПОИНТА (МАКСИМУМ)

### 1. **POST /iiko/connect** 
```python
@app.post("/iiko/connect")
async def connect_to_iiko(credentials: IikoCredentials):
    """
    Подключение к iiko RMS
    - Авторизация в iiko
    - Получение списка организаций  
    - Сохранение сессии
    """
    pass
```

### 2. **POST /iiko/export**
```python  
@app.post("/iiko/export")
async def export_techcards(export_request: ExportRequest):
    """
    Экспорт техкарт в iiko
    - Конвертация в формат iiko
    - Создание номенклатуры
    - Загрузка в iiko RMS
    """
    pass
```

### 3. **GET /iiko/status**
```python
@app.get("/iiko/status")
async def get_iiko_status(user_id: str):
    """
    Статус подключения к iiko
    - Проверка активной сессии
    - Статус последнего экспорта
    - Количество экспортированных техкарт
    """
    pass
```

## 🔄 ПЛАН МИГРАЦИИ (3 недели)

### Неделя 1: Backend
1. **День 1-2**: Создание структуры проекта
   - Настройка FastAPI приложения
   - Копирование iiko-related файлов
   - Адаптация под новую структуру

2. **День 3-4**: Реализация эндпоинтов
   - Реализация `/iiko/connect`
   - Тестирование подключения к вашему iiko

3. **День 5**: Экспорт функционал
   - Реализация `/iiko/export`  
   - Реализация `/iiko/status`

### Неделя 2: Frontend
1. **День 1-2**: Простой интерфейс подключения
2. **День 3-4**: Панель экспорта техкарт
3. **День 5**: Статус и мониторинг

### Неделя 3: Интеграция и тестирование
1. **День 1-2**: Интеграция с Receptor Core
2. **День 3-4**: Тестирование полного цикла
3. **День 5**: Деплой и документация

## 💰 МОНЕТИЗАЦИЯ iiko PRO

### Ценообразование:
- **$99/месяц** за полный доступ
- **Revenue Share 30/70** с iiko (наша доля 30%)
- **Enterprise**: $299/месяц с поддержкой

### Целевая аудитория:
- 69,000 ресторанов в базе iiko
- Конверсия 1% = 690 клиентов  
- Revenue: 690 × $99 = $68,310/месяц
- После Revenue Share: $20,493/месяц чистого дохода

## 🚀 КОД ДЛЯ СТАРТА

### Backend (main.py):
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="iiko PRO Module", version="1.0.0")

class IikoCredentials(BaseModel):
    host: str
    login: str  
    password: str
    user_id: str

class ExportRequest(BaseModel):
    techcard_ids: list[str]
    organization_id: str
    user_id: str

@app.post("/iiko/connect")
async def connect_to_iiko(credentials: IikoCredentials):
    # Здесь копируем логику из iiko_rms_v2.py
    return {"status": "connected", "organizations": []}

@app.post("/iiko/export") 
async def export_techcards(export_request: ExportRequest):
    # Здесь копируем логику экспорта
    return {"status": "exported", "count": len(export_request.techcard_ids)}

@app.get("/iiko/status")
async def get_iiko_status(user_id: str):
    # Здесь проверяем статус подключения
    return {"status": "connected", "last_export": None}
```

### Frontend (App.jsx):
```jsx
import React, { useState } from 'react';

function IikoProApp() {
    const [connection, setConnection] = useState(null);
    const [credentials, setCredentials] = useState({
        host: '', login: '', password: ''
    });

    const handleConnect = async () => {
        // Вызов POST /iiko/connect
    };

    const handleExport = async (techcardIds) => {
        // Вызов POST /iiko/export  
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            <h1>🏢 iiko PRO Module</h1>
            {/* Простой интерфейс подключения и экспорта */}
        </div>
    );
}

export default IikoProApp;
```

## ✅ КРИТЕРИИ УСПЕХА

1. **Функциональность**: Все текущие iiko функции работают
2. **Производительность**: < 3 секунды на подключение
3. **Размер кода**: < 2000 строк общего кода  
4. **Автономность**: Работает без основного приложения
5. **Монетизация**: Готов к продаже через 3 недели

## 🔗 ИНТЕГРАЦИЯ С ЭКОСИСТЕМОЙ

- **Auth**: Использует общий SSO сервис
- **Billing**: Интегрируется с центральным биллингом
- **Data**: Получает техкарты из Receptor Core API
- **Notifications**: Уведомления об экспорте через общий сервис
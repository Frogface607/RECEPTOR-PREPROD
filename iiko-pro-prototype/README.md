# 🏢 iiko PRO Module

Автономный микросервис для интеграции с iiko RMS. Первый модуль экосистемы Receptor.

## 🎯 Концепция

- **Максимум 3 эндпоинта** (принцип микросервисов)
- **Автономная работа** (не зависит от основного приложения)
- **Простота кода** (< 2000 строк общего кода)
- **Четкая монетизация** ($99/месяц)

## 🚀 Запуск

### Backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
# Сервер запустится на http://localhost:8002
```

### Frontend:
```bash  
cd frontend
npm install
npm start
# Откроется http://localhost:3000
```

## 📋 API Эндпоинты

### 1. POST /iiko/connect
Подключение к iiko RMS сервер и получение организаций.

**Request:**
```json
{
  "host": "edison-bar.iiko.it",
  "login": "Sergey", 
  "password": "your_password",
  "user_id": "demo_user"
}
```

**Response:**
```json
{
  "status": "connected",
  "host": "edison-bar.iiko.it",
  "organizations": [...],
  "session_expires_at": "2025-09-21T18:00:00"
}
```

### 2. POST /iiko/export
Экспорт техкарт в iiko RMS.

**Request:**
```json
{
  "techcard_ids": ["tc1", "tc2", "tc3"],
  "organization_id": "default",
  "user_id": "demo_user",
  "format": "iiko_rms"
}
```

**Response:**
```json
{
  "status": "exported",
  "exported_count": 3,
  "export_id": "uuid-here",
  "timestamp": "2025-09-21T15:30:00"
}
```

### 3. GET /iiko/status?user_id=demo_user
Статус подключения и статистика.

**Response:**
```json
{
  "status": "connected",
  "host": "edison-bar.iiko.it",
  "login": "Sergey",
  "organization_id": "default",
  "session_expires_at": "2025-09-21T18:00:00",
  "last_export": "2025-09-21T15:30:00",
  "exported_count": 15
}
```

## 💰 Монетизация

- **Цена**: $99/месяц за модуль
- **Revenue Share**: 30/70 с iiko (наша доля 30%)
- **Целевая аудитория**: 69,000 ресторанов в базе iiko
- **Потенциальный доход**: $20,493/месяц при 1% конверсии

## 🏗️ Архитектура

```
iiko-pro-module/
├── backend/          # FastAPI, 3 эндпоинта
├── frontend/         # React, простой интерфейс  
├── docker-compose.yml # Контейнеризация
└── README.md         # Документация
```

## ✅ Преимущества перед монолитом

1. **Простота**: 500 строк frontend vs 18,960 в монолите
2. **Автономность**: не зависит от основного приложения
3. **Фокус**: только iiko интеграция, ничего лишнего
4. **Масштабируемость**: легко деплоить и обновлять
5. **Монетизация**: четкая ценность для клиентов

## 🔗 Интеграция с экосистемой

- **Auth Service**: общая авторизация
- **Billing Service**: централизованный биллинг
- **Receptor Core**: получение техкарт через API
- **Notification Service**: уведомления об экспорте

## 📈 Следующие шаги

1. Завершить разработку (3 недели)
2. Тестирование с реальными данными iiko
3. Настройка Revenue Share с iiko
4. Маркетинг для 69k ресторанов
5. Разработка следующего модуля (AI Kitchen)
# 🚀 ДЕПЛОЙ НА FLY.IO (АЛЬТЕРНАТИВА)

## ✅ ПРЕИМУЩЕСТВА FLY.IO

- ✅ **Бесплатный tier** - 3 shared-cpu VMs
- ✅ **Быстрый старт** - не спит как Render
- ✅ **Глобальная сеть** - CDN из коробки
- ✅ **Простой CLI** - удобное управление

## 📋 БЫСТРЫЙ СТАРТ

### 1. Установка CLI

```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Или через winget
winget install -e --id Fly.Flyctl
```

### 2. Логин

```bash
flyctl auth login
```

### 3. Создание приложения

```bash
cd backend
flyctl launch
```

**Ответь на вопросы:**
- App name: `receptor-backend` (или любое уникальное)
- Region: `fra` (Frankfurt) или `iad` (Washington)
- PostgreSQL: `No` (используем MongoDB)
- Redis: `No`

### 4. Настройка переменных

```bash
flyctl secrets set MONGODB_URI="твой_mongodb_uri"
flyctl secrets set JWT_SECRET="твой_секретный_ключ"
flyctl secrets set OPENAI_API_KEY="твой_openai_key"
flyctl secrets set ENVIRONMENT="production"
flyctl secrets set DB_NAME="receptor_pro"
```

### 5. Деплой

```bash
flyctl deploy
```

### 6. Получи URL

```bash
flyctl status
```

URL будет вида: `https://receptor-backend.fly.dev`

## 🔧 КОНФИГУРАЦИЯ

Создай `fly.toml` в `backend/`:

```toml
app = "receptor-backend"
primary_region = "fra"

[build]

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

## 📝 ПОЛЕЗНЫЕ КОМАНДЫ

```bash
# Посмотреть логи
flyctl logs

# Перезапустить
flyctl restart

# Посмотреть статус
flyctl status

# SSH в контейнер
flyctl ssh console

# Обновить secrets
flyctl secrets set KEY="value"
```

---

**Готово!** Fly.io обычно быстрее чем Render, но требует больше настройки.




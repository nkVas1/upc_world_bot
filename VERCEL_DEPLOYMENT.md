# 🚀 ДЕПЛОЙ НА VERCEL + PRODUCTION SETUP

## 📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ

```
Bot Framework: python-telegram-bot 21.6
Website URL: https://under-people-club.vercel.app
Database: PostgreSQL (требуется отдельный хостинг)
Caching: Redis (требуется отдельный хостинг)
```

---

## ⚙️ ДЕПЛОЙ БОТА

### Вариант 1: Railway.app (РЕКОМЕНДУЕТСЯ)

Railway.app работает отлично для Telegram ботов и поддерживает PostgreSQL + Redis

**Шаг 1: Создание Railway проекта**
```bash
# 1. Перейдите на https://railway.app
# 2. Нажмите "New Project"
# 3. Выберите "Deploy from GitHub"
# 4. Авторизуйтесь и выберите ваш репозиторий
```

**Шаг 2: Добавление сервисов**
```bash
# 1. В Railway нажмите "Add Service"
# 2. Добавьте PostgreSQL
# 3. Добавьте Redis
# 4. Railway автоматически создаст переменные окружения
```

**Шаг 3: Настройка Environment Variables**
```
# Railway автоматически установит:
DATABASE_URL (PostgreSQL)
REDIS_URL (Redis)

# Добавьте вручную:
BOT_TOKEN=your_bot_token
WEBSITE_URL=https://under-people-club.vercel.app
ADMIN_IDS=your_admin_id
SECRET_KEY=random_secret_key
ENCRYPTION_KEY=random_encryption_key_32_chars
```

**Шаг 4: Deploy**
```bash
# Railway автоматически запустит после push на main
# Проверьте "Deployments" вкладку
```

---

### Вариант 2: Render.com

**Шаг 1: Создание Web Service**
```
1. Перейдите на https://render.com
2. Нажмите "New +"
3. Выберите "Web Service"
4. Подключите GitHub репозиторий
```

**Шаг 2: Конфигурация**
```
Name: upc-world-bot
Environment: Python 3.11
Build Command: pip install -r requirements.txt
Start Command: python -m bot.main
```

**Шаг 3: Добавление PostgreSQL**
```
1. Создайте PostgreSQL базу отдельно
2. Скопируйте CONNECTION_STRING
3. Установите как DATABASE_URL в Web Service
```

**Шаг 4: Deploy**
```bash
git push origin main
# Render автоматически запустит деплой
```

---

### Вариант 3: Heroku (бесплатный tier больше не доступен)

Heroku больше не имеет бесплатного tier, используйте Railway или Render вместо этого.

---

## 🌐 СИНХРОНИЗАЦИЯ С VERCEL САЙТОМ

### Настройка API интеграции

**1. На сайте (Vercel):**
```
GET /api/users/{telegram_id}
POST /api/users/sync
POST /api/transactions/sync
GET /api/tickets/user/{telegram_id}
GET /api/events/upcoming
POST /api/tickets/validate
```

**2. В боте (.env):**
```env
WEBSITE_URL=https://under-people-club.vercel.app
WEBSITE_API_KEY=your_secure_api_key
WEBSITE_WEBHOOK_SECRET=your_webhook_secret
```

**3. WebhookURL для сайта:**
```
https://your-bot-deployment-url.com/webhook/website-sync
```

---

## 🔐 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ДЛЯ PRODUCTION

### Минимально необходимо:
```env
# Bot
BOT_TOKEN=your_token_from_botfather

# Database (от Railway/Render/другого хостинга)
DATABASE_URL=postgresql+asyncpg://...

# Redis (от Railway/Render/другого хостинга)
REDIS_URL=redis://...

# Website
WEBSITE_URL=https://under-people-club.vercel.app
WEBSITE_API_KEY=your_secure_api_key
WEBSITE_WEBHOOK_SECRET=your_webhook_secret

# Security
SECRET_KEY=random_32_character_string
ENCRYPTION_KEY=random_32_character_string
JWT_SECRET=random_jwt_secret_string

# Admin
ADMIN_IDS=your_telegram_id
```

### Дополнительно (опционально):
```env
# Telegram Login Widget (если используется)
TELEGRAM_BOT_ID=your_bot_id
TELEGRAM_LOGIN_CALLBACK_URL=https://under-people-club.vercel.app/auth/telegram

# Payment
PAYMENT_PROVIDER_TOKEN=stripe_or_other_token
PAYMENT_WEBHOOK_URL=https://your-bot-url/payment-webhook

# Monitoring
SENTRY_DSN=your_sentry_dsn

# Features
ENABLE_CARD_GAME=true
ENABLE_MINI_GAMES=true
ENABLE_REFERRAL=true
ENABLE_SHOP=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 📊 МОНИТОРИНГ И ЛОГИ

### На Railway
```bash
# 1. Откройте проект на railway.app
# 2. Выберите Bot сервис
# 3. Откройте "Logs" вкладку
# 4. Логи обновляются в реальном времени
```

### На Render
```bash
# 1. Откройте Web Service
# 2. Перейдите в "Logs"
# 3. Смотрите все логи приложения
```

### Локально
```bash
# Просмотр последних логов
tail -f logs/bot_*.log

# С Docker
docker-compose logs -f bot
```

---

## 🔄 ОБНОВЛЕНИЯ И ДЕПЛОЙ

### Процесс обновления:

```bash
# 1. Сделайте изменения
git add .
git commit -m "[FEAT] Новая фича / New feature"

# 2. Пушьте на GitHub
git push origin main

# 3. Railway/Render автоматически:
#    - Запустит тесты (GitHub Actions)
#    - Задеплоит новую версию
#    - Обновит production
```

---

## 🚨 TROUBLESHOOTING

### Бот не запускается на production

**Проверьте:**
```bash
# 1. Логи deployment
# Railway → Logs вкладка

# 2. Environment variables
# Убедитесь что все переменные установлены

# 3. BOT_TOKEN
# Проверьте что token правильно скопирован
```

### Ошибка подключения к БД

```bash
# 1. Проверьте DATABASE_URL
# Убедитесь что формат: postgresql+asyncpg://user:pass@host:port/db

# 2. Проверьте пароль
# В пароле не должно быть спецсимволов (или экранируйте их)

# 3. Тестируйте локально
# psql "postgresql://user:pass@localhost/db"
```

### Ошибка подключения к Redis

```bash
# 1. Проверьте REDIS_URL
# Убедитесь что формат: redis://localhost:6379/0

# 2. Redis должен быть доступен
# Проверьте что Redis сервис запущен
```

---

## 💡 РЕКОМЕНДАЦИИ

### Для разработки
```bash
python start.py  # Локальный запуск
```

### Для тестирования
```bash
docker-compose up -d  # Docker окружение
```

### Для production
```bash
# Railway.app (5 минут настройки)
# или Render.com (10 минут)
# GitHub → Push → Автоматический деплой
```

---

## 🎯 ЧЕКЛИСТ ДЕПЛОЯ

- [ ] Git репозиторий готов
- [ ] GitHub репо публичный (или Railway имеет доступ)
- [ ] requirements.txt актуален
- [ ] .env не коммичен (в .gitignore)
- [ ] Dockerfile и docker-compose.yml готовы
- [ ] BOT_TOKEN получен от @BotFather
- [ ] ADMIN_ID добавлен
- [ ] WEBSITE_URL установлен на Vercel
- [ ] DATABASE_URL от Railway/Render/другого хостинга
- [ ] REDIS_URL от Railway/Render/другого хостинга
- [ ] GitHub Actions workflows готовы (они уже в проекте)
- [ ] Railway/Render проект создан
- [ ] Environment variables установлены
- [ ] Deploy запустился успешно

---

## 📈 ПОСЛЕ ЗАПУСКА

1. **Мониторьте логи** (Railway/Render logs)
2. **Тестируйте функциональность** (отправьте /start в Telegram)
3. **Проверьте интеграцию** (синхронизация с vercel.app сайтом)
4. **Добавьте мониторинг** (Sentry, DataDog, итд - опционально)
5. **Настройте webhooks** (если нужны - документация в DEPLOYMENT.md)

---

## 🔗 ПОЛЕЗНЫЕ ССЫЛКИ

- 🚀 [Railway.app](https://railway.app) - Рекомендуемый хостинг
- 🎨 [Render.com](https://render.com) - Альтернатива
- 🤖 [Python Telegram Bot](https://python-telegram-bot.readthedocs.io/)
- 🐘 [PostgreSQL Docs](https://www.postgresql.org/docs/)
- 📖 [DEPLOYMENT.md](DEPLOYMENT.md) - Более подробный гайд
- 💡 [NEXT_STEPS.md](NEXT_STEPS.md) - Что дальше

---

## ✅ ГОТОВО К PRODUCTION!

Все компоненты настроены для деплоя на production.

**Начните с Railway.app - это займет 5 минут!** 🚀

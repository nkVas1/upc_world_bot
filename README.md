# UPC World Bot - Under People Club

## Описание

Современный профессиональный Telegram-бот для молодёжного сообщества Under People Club.

- 🎟️ Система покупки билетов на события
- 💰 Внутренняя валюта UP Coins с интеграцией на сайт
- 🔗 Реферальная программа с многоуровневыми наградами
- 👤 Персональный кабинет с QR-кодами
- 📊 Админ-панель с полной статистикой
- 🎮 Система достижений и игр

## Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/underpeople/upc-world-bot.git
cd upc-world-bot
```

2. **Запустите стартер скрипт**
```bash
# Linux/Mac
python start.py

# Windows
python start.py
```

Скрипт автоматически:
- Проверит .env файл
- Создаст виртуальную среду
- Установит зависимости
- Запустит бота

3. **Или ручная установка**
```bash
# Создайте виртуальную среду
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Скопируйте .env файл
cp .env.example .env

# Запустите бота
python -m bot.main
```

### Docker (рекомендуется)

```bash
# Скопируйте .env
cp .env.example .env

# Запустите контейнеры
docker-compose up -d

# Проверьте логи
docker-compose logs -f bot
```

## Конфигурация

Создайте файл `.env` на основе `.env.example`:

```env
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=UPCworld_bot
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/upc_bot
REDIS_URL=redis://localhost:6379/0
WEBSITE_URL=https://underpeople.club
WEBSITE_API_KEY=your_api_key
SECRET_KEY=your_secret_key_32_chars_long_here
ENCRYPTION_KEY=your_encryption_key_32chars
ADMIN_IDS=123456789,987654321
```

## Структура проекта

```
bot/
├── config.py              # Конфигурация
├── main.py               # Точка входа
├── database/             # Модели БД и репозитории
│   ├── models.py
│   ├── base.py
│   ├── session.py
│   └── repositories/
├── handlers/             # Обработчики команд
│   ├── start.py
│   ├── profile.py
│   ├── referral.py
│   ├── shop.py
│   └── admin.py
├── services/             # Бизнес-логика
│   ├── user_service.py
│   ├── referral_service.py
│   ├── website_sync.py
│   └── qr_generator.py
├── middlewares/          # Middleware для обработки запросов
├── keyboards/            # Кнопки и клавиатуры
└── utils/                # Утилиты
```

## Основные команды

- `/start` - Запустить бота
- `/profile` - Личный кабинет
- `/referral` - Реферальная программа
- `/daily` - Ежедневный бонус
- `/help` - Справка
- `/about` - О клубе
- `/admin` - Админ-панель (только для админов)

## Админ-команды

- `/userinfo [user_id]` - Информация о пользователе
- `/addcoins [user_id] [amount]` - Начислить UP Coins
- `/broadcast [message]` - Рассылка сообщений
- `/ban [user_id]` - Заблокировать пользователя

## Деплой

### Railway.app (Рекомендуется)

1. Создайте аккаунт на [railway.app](https://railway.app)
2. Подключите GitHub репозиторий
3. Добавьте PostgreSQL и Redis плагины
4. Установите переменные окружения в Settings
5. Бот автоматически развернётся

### Render.com

1. Создайте новый PostgreSQL сервис
2. Создайте новый Web Service из GitHub
3. Установите переменные окружения
4. Deploy запустится автоматически

### VPS (DigitalOcean, Linode, Hetzner)

```bash
# SSH на сервер
ssh root@your_server_ip

# Клонируйте репозиторий
git clone https://github.com/underpeople/upc-world-bot.git
cd upc-world-bot

# Установите Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Запустите контейнеры
docker-compose up -d
```

## Разработка

### Установка зависимостей для разработки

```bash
pip install -r requirements.txt
```

### Запуск тестов

```bash
pytest
```

### Код стиль

```bash
# Форматирование
black bot/

# Проверка
flake8 bot/
mypy bot/
```

### Миграции БД

```bash
# Создать миграцию
alembic revision --autogenerate -m "Add new field"

# Применить миграции
alembic upgrade head
```

## API Интеграция

Бот интегрируется с веб-сайтом через REST API:

- **Синхронизация пользователей** через Telegram Login Widget
- **Единый баланс UP Coins**
- **Общая система билетов**
- **Синхронизация достижений**

### Endpoints

```
GET  /api/v1/users/telegram/{telegram_id}
POST /api/v1/users/sync
POST /api/v1/transactions/sync
GET  /api/v1/tickets/user/{telegram_id}
GET  /api/v1/events/upcoming
POST /api/v1/tickets/validate
```

## Логирование

Логи сохраняются в JSON формате для интеграции с системами мониторинга:

```bash
# Просмотр логов (Docker)
docker-compose logs -f bot

# Просмотр логов (локально)
tail -f logs/bot_*.log
```

## Мониторинг

Поддерживается интеграция с:
- Sentry (обработка ошибок)
- DataDog (метрики)
- ELK Stack (логирование)

## Лицензия

Proprietary - Under People Club

## Автор

Under People Club Tech Team

## Поддержка

- 📧 Email: tech@underpeople.club
- 🔗 Telegram: [@underpeople_club](https://t.me/underpeople_club)
- 🌐 Сайт: [underpeople.club](https://underpeople.club)

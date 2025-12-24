# Разработка UPC World Bot

Руководство для разработчиков проекта.

## Первый запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/underpeople/upc-world-bot.git
cd upc-world-bot
```

### 2. Установите зависимости

```bash
# Создайте виртуальную среду
python -m venv venv

# Активируйте
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Установите dev зависимости
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

### 3. Настройте .env

```bash
cp .env.example .env
# Отредактируйте .env и добавьте реальные значения
nano .env
```

### 4. Подготовьте БД

```bash
# Если используете Docker для БД
docker-compose up -d postgres redis

# Примените миграции
python -m alembic upgrade head
```

### 5. Запустите бота

```bash
python -m bot.main
```

## Архитектура

```
bot/
├── config.py              # Конфигурация Pydantic
├── main.py               # Точка входа
│
├── database/             # БД слой
│   ├── base.py          # Базовые классы
│   ├── models.py        # SQLAlchemy модели
│   ├── session.py       # Управление сессиями
│   └── repositories/     # DAO слой
│       ├── user_repository.py
│       ├── transaction_repository.py
│       ├── event_repository.py
│       └── __init__.py
│
├── services/             # Бизнес-логика
│   ├── user_service.py       # Операции с пользователями
│   ├── referral_service.py   # Реферальная программа
│   ├── website_sync.py       # Синхронизация с сайтом
│   ├── qr_generator.py       # Генерация QR кодов
│   └── __init__.py
│
├── handlers/             # Обработчики команд
│   ├── start.py         # /start и главное меню
│   ├── profile.py       # Личный кабинет
│   ├── referral.py      # Реферальная система
│   ├── shop.py          # Магазин билетов
│   ├── admin.py         # Админ панель
│   └── __init__.py
│
├── middlewares/          # Middleware
│   ├── auth.py          # Авторизация пользователя
│   ├── throttling.py    # Rate limiting
│   ├── logging.py       # Логирование
│   └── __init__.py
│
├── keyboards/            # Кнопки
│   ├── inline.py        # Inline кнопки
│   └── __init__.py
│
├── utils/                # Утилиты
│   ├── formatters.py    # Форматирование текста
│   ├── decorators.py    # Декораторы
│   ├── logger.py        # Структурированное логирование
│   └── __init__.py
│
└── __init__.py
```

## Разработка новой фичи

### 1. Создайте ветку

```bash
git checkout -b feature/my-feature
```

### 2. Напишите код

**Пример: новый обработчик**

```python
# bot/handlers/games.py
"""Games handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.decorators import handle_errors, member_only
from bot.keyboards import kb


@handle_errors
@member_only
async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /games command."""
    await update.message.reply_text(
        "🎮 Выберите игру:",
        reply_markup=kb.games_menu()
    )


# Зарегистрируйте в main.py:
# from bot.handlers import games
# application.add_handler(CommandHandler("games", games.games_command))
```

### 3. Напишите тесты

```python
# tests/test_games.py
"""Tests for games handler."""

import pytest
from unittest.mock import AsyncMock, patch

from telegram import Update, User as TGUser, Chat, Message
from bot.handlers.games import games_command
from bot.database.models import User


@pytest.mark.asyncio
async def test_games_command_member():
    """Test /games command for members."""
    # Setup
    update = AsyncMock(spec=Update)
    update.effective_user = TGUser(id=123, is_bot=False, first_name="Test")
    update.message = AsyncMock()
    
    context = AsyncMock()
    context.user_data = {"user": User(id=123, is_member=True)}
    
    # Execute
    await games_command(update, context)
    
    # Verify
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Выберите игру" in call_args[0][0]


@pytest.mark.asyncio
async def test_games_command_non_member():
    """Test /games command for non-members."""
    update = AsyncMock(spec=Update)
    update.effective_user = TGUser(id=456, is_bot=False, first_name="Guest")
    update.message = AsyncMock()
    
    context = AsyncMock()
    context.user_data = {"user": User(id=456, is_member=False)}
    
    # Should not proceed due to @member_only
    # Decorator will handle the response
```

### 4. Запустите тесты

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=bot

# Конкретный файл
pytest tests/test_games.py

# Конкретный тест
pytest tests/test_games.py::test_games_command_member -v
```

### 5. Проверьте стиль кода

```bash
# Форматирование (исправляет автоматически)
black bot/

# Проверка стиля
flake8 bot/

# Типизация
mypy bot/

# Все сразу
black bot/ && flake8 bot/ && mypy bot/ && pytest
```

### 6. Коммитьте изменения

```bash
git add .
git commit -m "[FEAT] Добавлена система игр / Add games system"
git push origin feature/my-feature
```

### 7. Создайте Pull Request

В GitHub создайте PR с описанием:
- Что добавляет/исправляет
- Примеры использования
- Скриншоты (если UI)
- Результаты тестов

## Стиль кода

### Black форматирование

```python
# ✅ Правильно - 100 символов максимум
def get_user_profile(
    user_id: int,
    include_achievements: bool = False,
) -> dict:
    """Get user profile."""
```

### Type hints обязательны

```python
# ❌ Неправильно
def add_coins(user, amount):
    return user

# ✅ Правильно
def add_coins(user: User, amount: int) -> User:
    """Add coins to user balance."""
    user.coins += amount
    return user
```

### Async/await паттерны

```python
# ❌ Неправильно - блокирующие операции
def get_user(user_id: int) -> User:
    session = Session()
    return session.query(User).get(user_id)

# ✅ Правильно - асинхронно
async def get_user(user_id: int) -> User:
    async with db_manager.session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

### Логирование

```python
# ✅ Используйте структурированное логирование
from bot.utils.logger import logger

logger.info(
    "user_registered",
    user_id=user.id,
    referral_code=user.referral_code,
)

# Не используйте print()
print("User registered")  # ❌ Неправильно
```

## Базы данных

### Миграции

```bash
# Создайте миграцию для новой модели
alembic revision --autogenerate -m "Add games table"

# Проверьте миграцию
cat alembic/versions/xxx_add_games_table.py

# Примените
alembic upgrade head

# Откатитесь если что-то не так
alembic downgrade -1
```

### Запросы к БД

```python
# ✅ Используйте SQLAlchemy async ORM
from sqlalchemy import select
from bot.database.models import User

# В handlers/services:
async with db_manager.session() as session:
    # Получить одного пользователя
    stmt = select(User).where(User.id == user_id)
    user = await session.execute(stmt)
    user = user.scalar_one_or_none()
    
    # Получить несколько
    stmt = select(User).where(User.is_member == True)
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    # Обновить
    user.coins += 100
    await session.commit()
```

## Логирование и отладка

### Структурированное логирование

```python
from bot.utils.logger import logger

# Все логи автоматически в JSON формате
logger.info("user_action", user_id=123, action="buy_ticket", amount=500)
```

### Debug режим

```bash
# Установите LOG_LEVEL=DEBUG в .env
LOG_LEVEL=DEBUG python -m bot.main
```

### Просмотр логов

```bash
# Docker
docker-compose logs -f bot

# Фильтр по уровню
docker-compose logs bot | grep ERROR

# JSON парсинг
docker-compose logs bot | jq '.level'
```

## Производительность

### Оптимизация запросов

```python
# ❌ N+1 проблема
users = await get_all_users()
for user in users:
    transactions = await get_user_transactions(user.id)  # Много запросов!

# ✅ Используйте eager loading
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.transactions))
users = await session.execute(stmt)
```

### Кэширование

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_referral_rewards(tier: int) -> dict:
    """Get cached rewards."""
    return REWARDS_BY_TIER[tier]
```

### Асинхронность

```python
import asyncio

# ❌ Неправильно - блокирует
time.sleep(5)

# ✅ Правильно
await asyncio.sleep(5)

# Параллельные операции
results = await asyncio.gather(
    get_user(1),
    get_user(2),
    get_user(3),
)
```

## Debugging Tips

### Используйте debugger

```python
import pdb

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler with debugging."""
    breakpoint()  # Python 3.7+
    # или
    # pdb.set_trace()
```

### Логи в реальном времени

```bash
# Terminal 1
docker-compose logs -f bot

# Terminal 2 (edit code)
# Changes auto-reload (if implemented)
```

### Тестирование в REPL

```bash
# Интерактивная оболочка с контекстом проекта
python -c "from bot.config import settings; print(settings.BOT_TOKEN)"
```

## Полезные команды

```bash
# Информация о проекте
wc -l bot/**/*.py  # Количество строк кода
find bot -name "*.py" | wc -l  # Количество файлов

# Анализ кода
radon cc bot/  # Сложность функций
radon mi bot/  # Индекс поддерживаемости

# Проверки безопасности
bandit -r bot/  # Security issues

# Обновление зависимостей
pip list --outdated
pip install --upgrade -r requirements.txt
```

## Ресурсы

- [python-telegram-bot документация](https://python-telegram-bot.readthedocs.io/)
- [SQLAlchemy 2.0 документация](https://docs.sqlalchemy.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Async Python](https://docs.python.org/3/library/asyncio.html)

## Общение

Вопросы в Telegram: [@underpeople_club](https://t.me/underpeople_club)

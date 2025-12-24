# Contributing to UPC World Bot

Спасибо за интерес к нашему проекту! Этот документ описывает процесс разработки и отправки контрибуций.

## Процесс разработки

### 1. Fork и Clone

```bash
git clone https://github.com/YOUR_USERNAME/upc-world-bot.git
cd upc-world-bot
```

### 2. Создайте ветку для вашей фичи

```bash
git checkout -b feature/my-amazing-feature
```

Используйте префиксы:
- `feature/` - новая функция
- `fix/` - исправление баги
- `docs/` - обновления документации
- `refactor/` - переструктуризация кода

### 3. Разработка

Установите зависимости:
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 mypy
```

Убедитесь что ваш код соответствует стилю проекта:
```bash
# Форматирование
black bot/

# Проверка стиля
flake8 bot/

# Типизация
mypy bot/
```

### 4. Тесты

Напишите тесты для новой функциональности:
```bash
# Запустите все тесты
pytest

# С покрытием
pytest --cov=bot

# Конкретный тест
pytest tests/test_handlers.py::test_start_command
```

### 5. Коммиты

Используйте понятные сообщения на русском языке:

```bash
git commit -m "Добавлена новая функция реферралов / Add new referral feature"
```

Формат:
```
[Тип] Описание на русском / Description in English

Опциональное подробное объяснение
```

Типы:
- `[FEAT]` - новая функция
- `[FIX]` - исправление
- `[DOCS]` - документация
- `[STYLE]` - форматирование, без логических изменений
- `[REFACTOR]` - переструктуризация
- `[TEST]` - добавление тестов
- `[CI]` - CI/CD изменения

### 6. Push и Pull Request

```bash
git push origin feature/my-amazing-feature
```

Создайте Pull Request с описанием:
- Что добавляет/исправляет
- Чему это способствует
- Как это тестировали

## Требования к коду

### Стиль

- **Line length**: максимум 100 символов
- **Indentation**: 4 пробела
- **Imports**: упорядочены (stdlib, third-party, local)
- **Docstrings**: для всех публичных функций

### Пример:

```python
"""Module description."""

import asyncio
from typing import Optional

from telegram import Update

from bot.database.models import User


async def get_user_info(user_id: int) -> Optional[User]:
    """Fetch user information from database.
    
    Args:
        user_id: Telegram user ID.
        
    Returns:
        User object if found, None otherwise.
    """
    # Implementation
    pass
```

### Typing

Всегда используйте type hints:

```python
# ❌ Плохо
def process_data(data):
    return data

# ✅ Хорошо
def process_data(data: dict) -> dict:
    """Process user data."""
    return data
```

### Async/Await

```python
# ✅ Правильно для Telegram бота
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming message."""
    async with get_session() as session:
        user = await session.get(User, update.effective_user.id)
```

## Структура для новых файлов

### Новый обработчик

```python
# bot/handlers/new_handler.py
"""Description."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.decorators import handle_errors


@handle_errors
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /newcommand."""
    pass
```

### Новый сервис

```python
# bot/services/new_service.py
"""Description."""

import logging

logger = logging.getLogger(__name__)


class NewService:
    """Service description."""
    
    async def method(self) -> None:
        """Method description."""
        pass
```

## Тестирование

Обязательно покройте новый код тестами:

```python
# tests/test_new_handler.py
"""Tests for new_handler module."""

import pytest
from unittest.mock import AsyncMock

from telegram import Update, User as TGUser
from bot.handlers.new_handler import new_command


@pytest.mark.asyncio
async def test_new_command(update: Update, context):
    """Test new_command handler."""
    await new_command(update, context)
    # Assertions...
```

## Documentation

Обновляйте документацию если добавляете/изменяете публичный API:

- `README.md` - добавить новую команду если применимо
- Docstrings в коде
- Комментарии для сложной логики

## Review Process

1. **Автоматические проверки**
   - Tests должны пройти
   - Linting должен быть успешным
   - Coverage не должен упасть

2. **Код ревью**
   - Минимум 1 approval
   - Все suggestions должны быть рассмотрены

3. **Merge**
   - После approval может быть мержено в main
   - Используйте "Squash and merge" для чистой истории

## Reporting Issues

Используйте GitHub Issues для:
- **Bugs**: Опишите проблему и как её воспроизвести
- **Features**: Предложите новый функционал с примерами
- **Questions**: Если вам нужна помощь

Шаблон для bug report:
```markdown
## Description
Краткое описание проблемы

## Steps to Reproduce
1. Сделайте это
2. Потом это
3. И это

## Expected
Что должно было случиться

## Actual
Что на самом деле случилось

## Environment
- Python 3.11
- python-telegram-bot 21.6
- OS: Linux
```

## Communication

- 💬 Telegram: [@underpeople_club](https://t.me/underpeople_club)
- 📧 Email: tech@underpeople.club
- 📝 Issues: GitHub Issues
- 💭 Discussions: GitHub Discussions

## License

Отправляя Pull Request, вы соглашаетесь что ваш код будет под лицензией проекта.

Спасибо за вклад! 🎉

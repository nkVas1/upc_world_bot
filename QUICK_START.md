# 🚀 Быстрый старт UPC World Bot

## За 5 минут до первого запуска

### Windows

1. **Скопируйте .env**
```cmd
copy .env.example .env
```

2. **Отредактируйте .env**
```cmd
notepad .env
```
Добавьте минимум:
- `BOT_TOKEN=` - получите от @BotFather в Telegram
- `ADMIN_IDS=` - ваш Telegram ID (можно узнать у @userinfobot)

3. **Запустите стартер**
```cmd
python start.py
```

Скрипт автоматически:
- Создаст виртуальную среду
- Установит зависимости
- Запустит бота

### Linux/Mac

```bash
# Клонируйте
git clone https://github.com/underpeople/upc-world-bot.git
cd upc-world-bot

# Запустите
python start.py
```

## С Docker (рекомендуется)

```bash
# Скопируйте и отредактируйте
cp .env.example .env
nano .env

# Запустите
docker-compose up -d

# Проверьте логи
docker-compose logs -f bot
```

## Первые шаги после запуска

1. Откройте Telegram и найдите вашего бота
2. Отправьте `/start`
3. Бот должен ответить с приветствием

Готово! 🎉

## Что дальше?

### Разработка
- [DEVELOPMENT.md](DEVELOPMENT.md) - Руководство для разработчиков
- [bot/handlers/](bot/handlers/) - Обработчики команд
- [bot/services/](bot/services/) - Бизнес-логика

### Деплой
- [DEPLOYMENT.md](DEPLOYMENT.md) - Развертывание на production
- Поддерживаются: Railway, Render, Heroku, VPS

### Мониторинг
```bash
# Локально
tail -f logs/bot_*.log

# Docker
docker-compose logs -f bot
```

## Команды для разработки

```bash
# Запуск тестов
pytest

# Форматирование кода
black bot/

# Проверка стиля
flake8 bot/

# Типизация
mypy bot/

# Все проверки
make lint test

# С Docker
make docker
make docker-logs
```

## Troubleshooting

**Бот не запускается**
```bash
# Проверьте .env
cat .env

# Проверьте TOKEN
echo $BOT_TOKEN

# Посмотрите ошибки
python -m bot.main
```

**Ошибка БД**
```bash
# Docker
docker-compose logs postgres

# Проверьте подключение
docker-compose exec postgres psql -U upc_user -d upc_bot
```

**Нужны зависимости**
```bash
pip install -r requirements.txt
```

## Полезные ссылки

- 📚 [python-telegram-bot документация](https://python-telegram-bot.readthedocs.io/)
- 🗄️ [SQLAlchemy документация](https://docs.sqlalchemy.org/)
- 🤖 [Telegram Bot API](https://core.telegram.org/bots/api)
- 📖 [Async Python](https://docs.python.org/3/library/asyncio.html)

## Поддержка

Вопросы в Telegram: [@underpeople_club](https://t.me/underpeople_club)

# 📤 Гайд по пушу на GitHub

## 1. Создайте репозиторий на GitHub

1. Перейдите на [github.com/new](https://github.com/new)
2. Нажмите **New repository**
3. Заполните форму:
   - **Repository name**: `upc-world-bot`
   - **Description**: "Modern Telegram Bot for Under People Club"
   - **Public/Private**: Выберите в зависимости от политики
   - **Initialize**: НЕ инициализируйте (уже есть локальный репо)
4. Нажмите **Create repository**

## 2. Свяжите локальный репо с GitHub

```bash
cd upc-world-bot

# Добавьте remote
git remote add origin https://github.com/YOUR_USERNAME/upc-world-bot.git

# Переименуйте branch на main (если нужно)
git branch -M main

# Проверьте remote
git remote -v
```

## 3. Сделайте первый push

```bash
# Пушьте код
git push -u origin main

# Проверьте на GitHub
# https://github.com/YOUR_USERNAME/upc-world-bot
```

## 4. Добавьте GitHub Secrets для CI/CD

Перейдите в **Settings → Secrets and variables → Actions**

Добавьте следующие secrets (для деплоя):

### Railway.app
```
RAILWAY_TOKEN: (получить из Railway)
```

### Render.com
```
RENDER_API_KEY: (получить из Render)
RENDER_SERVICE_ID: (ID сервиса)
```

### VPS (DigitalOcean, Linode, Hetzner)
```
VPS_HOST: your.vps.ip
VPS_USERNAME: root
VPS_SSH_KEY: (приватный SSH ключ)
```

### Slack уведомления (опционально)
```
SLACK_WEBHOOK: (webhook URL из Slack)
```

## 5. Настройте GitHub настройки

1. Перейдите в **Settings**

2. **General**:
   - Description: "Modern Telegram Bot for Under People Club"
   - Website: https://underpeople.club
   - Topics: `telegram`, `bot`, `python`, `async`

3. **Branch protection** (опционально для production):
   - Перейдите в **Branches**
   - Добавьте правило для `main`
   - Требуйте 1 review перед merge

4. **Actions permissions**:
   - Перейдите в **Actions → General**
   - Выберите "Allow all actions and reusable workflows"

## 6. Настройте CI/CD

### GitHub Actions уже настроены!

Просто проверьте что работают:

1. Перейдите в **Actions**
2. Посмотрите статус workflows:
   - ✅ Tests (запускается при push)
   - ✅ Deploy (запускается только на main)

## 7. Обновления и версионирование

### Правила для коммитов

```bash
# Формат коммитов
git commit -m "[ТИП] Описание на русском / English description"

# Типы:
# [FEAT] - Новая функция
# [FIX]  - Исправление
# [DOCS] - Документация
# [STYLE] - Форматирование
# [REFACTOR] - Переструктуризация
# [TEST] - Тесты
# [CI] - CI/CD

# Примеры:
git commit -m "[FEAT] Добавлена система достижений / Add achievement system"
git commit -m "[FIX] Исправлена ошибка авторизации / Fix auth bug"
git commit -m "[DOCS] Обновлена документация / Update docs"
```

### Версионирование

Используйте semver (semantic versioning):

```
vMAJOR.MINOR.PATCH

v3.0.0 - Мажорный релиз (breaking changes)
v3.1.0 - Минорный релиз (новые фичи)
v3.0.1 - Патч (исправления)
```

### Создание релиза

```bash
# Создайте тег
git tag -a v3.0.1 -m "Bug fixes and improvements"

# Пушьте тег
git push origin v3.0.1
```

Затем на GitHub:
1. Перейдите в **Releases**
2. Нажмите **Create a release**
3. Выберите тег
4. Добавьте описание
5. Нажмите **Publish release**

## 8. Защита от ошибок

### Pre-commit hook (опционально)

Создайте `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "Running checks..."

# Форматирование
black bot/ || exit 1

# Линтер
flake8 bot/ || echo "Warning: flake8 issues found"

# Типы
mypy bot/ || echo "Warning: mypy issues found"

# Тесты
pytest || exit 1

echo "✅ All checks passed!"
```

Сделайте исполняемым:
```bash
chmod +x .git/hooks/pre-commit
```

## 9. Настройка README бейджей (опционально)

Добавьте в начало README.md:

```markdown
# UPC World Bot

[![Tests](https://github.com/YOUR_USERNAME/upc-world-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/upc-world-bot/actions)
[![Deploy](https://github.com/YOUR_USERNAME/upc-world-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/YOUR_USERNAME/upc-world-bot/actions)
[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
```

## 10. Что дальше?

### Текущие шаги
- ✅ Репозиторий создан и пушлен
- ✅ CI/CD настроены
- ✅ Документация актуальна

### Следующие версии
- Добавить больше тестов
- Интегрировать Sentry для мониторинга
- Добавить DataDog метрики
- Раширить игровую систему
- Добавить больше команд и фич

## 11. Полезные команды

```bash
# Просмотр истории
git log --oneline

# Просмотр веток
git branch -a

# Обновление из GitHub
git pull origin main

# Создание ветки
git checkout -b feature/my-feature

# Мержинг
git merge feature/my-feature

# Отправка ветки
git push origin feature/my-feature
```

## 12. Troubleshooting

### Ошибка при push
```bash
# Если конфликты
git pull origin main
# Разрешите конфликты
git add .
git commit -m "Merge conflicts resolved"
git push origin main
```

### Отменить последний коммит
```bash
# Отменить с сохранением изменений
git reset --soft HEAD~1

# Отменить без сохранения
git reset --hard HEAD~1
```

### Очистить локальные ветки
```bash
# Удалить локальную ветку
git branch -d feature/my-feature

# Удалить на GitHub
git push origin --delete feature/my-feature
```

## Итого

✅ Репозиторий готов к GitHub!

Следующие команды для push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/upc-world-bot.git
git branch -M main
git push -u origin main
```

Поздравляем! 🎉 Ваш бот теперь на GitHub!

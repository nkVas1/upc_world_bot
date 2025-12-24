# Развертывание UPC World Bot

Полное руководство по деплою бота в различные окружения.

## Локальная разработка

### Windows

1. Установите Python 3.11+
2. Запустите стартер скрипт:
```cmd
python start.py
```

### Linux/Mac

```bash
# Клонируйте репозиторий
git clone https://github.com/underpeople/upc-world-bot.git
cd upc-world-bot

# Запустите стартер скрипт
python start.py
```

## Docker (локально)

```bash
# Скопируйте .env
cp .env.example .env

# Отредактируйте .env
nano .env

# Запустите контейнеры
docker-compose up -d

# Проверьте логи
docker-compose logs -f bot

# Остановите контейнеры
docker-compose down
```

## Production Deployment

### Railway.app (рекомендуется для быстрого старта)

1. **Создайте аккаунт**: https://railway.app
2. **Подключите GitHub**:
   - Кликнете "New Project"
   - Выберите "Deploy from GitHub repo"
   - Авторизуйтесь и выберите репозиторий

3. **Добавьте PostgreSQL**:
   - Кликнете "Add Service"
   - Выберите "PostgreSQL"
   - Railway создаст базу автоматически

4. **Добавьте Redis**:
   - Кликнете "Add Service"
   - Выберите "Redis"

5. **Установите переменные окружения**:
   - Перейдите в Settings → Variables
   - Добавьте все переменные из `.env.example`
   - Оставьте DATABASE_URL и REDIS_URL пустыми - Railway установит автоматически

6. **Deploy начнется автоматически**:
   - Проверьте логи в "Deployments"
   - После успешного деплоя бот будет работать 24/7

### Render.com

1. **Создайте новый Web Service**:
   - https://dashboard.render.com/new/web-service
   - Выберите GitHub репозиторий
   - Дайте имя (например `upc-world-bot`)
   - Выберите Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m bot.main`

2. **Добавьте PostgreSQL Database**:
   - https://dashboard.render.com/new/database
   - Имя: `upc-bot-db`
   - Выберите регион

3. **Добавьте Redis**:
   - Кликнете "Add Service"
   - Выберите "Redis"

4. **Установите Environment Variables**:
   - BOT_TOKEN
   - DATABASE_URL (из Render PostgreSQL)
   - REDIS_URL (из Render Redis)
   - Остальные из `.env.example`

5. **Deploy**:
   - Кликнете "Create Web Service"
   - Render автоматически развернет бота

### Heroku (устаревший, но работает)

```bash
# Установите Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Логин
heroku login

# Создайте приложение
heroku create upc-world-bot

# Добавьте PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Добавьте Redis
heroku addons:create heroku-redis:premium-0

# Установите переменные
heroku config:set BOT_TOKEN=your_token
heroku config:set SECRET_KEY=your_secret

# Deploy
git push heroku main

# Проверьте логи
heroku logs --tail
```

### Пользовательский VPS (DigitalOcean, Linode, Hetzner)

#### 1. Подготовка сервера

```bash
# Подключитесь по SSH
ssh root@your_server_ip

# Обновите систему
apt update && apt upgrade -y

# Установите необходимое ПО
apt install -y python3 python3-pip python3-venv git curl

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установите Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создайте директорию для приложения
mkdir -p /app/upc-world-bot
cd /app/upc-world-bot
```

#### 2. Клонируйте код

```bash
# Инициализируйте git
git clone https://github.com/underpeople/upc-world-bot.git .

# Создайте .env файл
cp .env.example .env

# Отредактируйте .env с вашими данными
nano .env
```

#### 3. Запустите контейнеры

```bash
# Запустите Docker Compose
docker-compose up -d

# Проверьте статус
docker-compose ps

# Посмотрите логи
docker-compose logs -f bot

# Примените миграции (если нужно)
docker-compose exec bot alembic upgrade head
```

#### 4. Настройте Nginx (опционально)

```bash
# Установите Nginx
apt install -y nginx

# Создайте конфиг
cat > /etc/nginx/sites-available/upc-bot << 'EOF'
server {
    listen 80;
    server_name your.domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Активируйте сайт
ln -s /etc/nginx/sites-available/upc-bot /etc/nginx/sites-enabled/
systemctl restart nginx
```

#### 5. SSL с Let's Encrypt (если используете Nginx)

```bash
# Установите Certbot
apt install -y certbot python3-certbot-nginx

# Получите сертификат
certbot --nginx -d your.domain.com

# Автоматическое обновление
systemctl enable certbot.timer
```

### Kubernetes (продвинуто)

Создайте `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: upc-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: upc-bot
  template:
    metadata:
      labels:
        app: upc-bot
    spec:
      containers:
      - name: bot
        image: your-registry/upc-world-bot:latest
        env:
        - name: BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: token
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

Деплойте:

```bash
kubectl apply -f k8s/deployment.yaml
```

## Post-Deployment

### 1. Проверьте что бот работает

```bash
# Отправьте сообщение боту в Telegram
# Нажмите /start

# Или проверьте логи
# Docker: docker-compose logs -f bot
# Railway/Render: В веб-интерфейсе в logs
```

### 2. Установите Webhook (опционально для лучшей производительности)

Вместо polling используйте webhook:

```python
# bot/main.py
await application.bot.set_webhook(
    url="https://your-domain.com/webhook",
    drop_pending_updates=True,
)

# Запустите как web server
app = web.Application()
app.router.post("/webhook", handle, name="webhook")
app.router.post("/webhook/telegram", webhook_handler)
```

### 3. Мониторинг

Добавьте мониторинг с Sentry:

```python
# bot/config.py
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(settings.SENTRY_DSN)
```

### 4. Backup БД

```bash
# Автоматический backup каждый день
0 3 * * * pg_dump $DATABASE_URL | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# На Render/Railway - используйте встроенные tools
```

### 5. Обновления

```bash
# Когда готов новый код
git pull origin main

# Примените миграции
docker-compose exec bot alembic upgrade head

# Перезапустите контейнер
docker-compose restart bot
```

## Troubleshooting

### Бот не отвечает

```bash
# Проверьте TOKEN
echo $BOT_TOKEN

# Проверьте логи
docker-compose logs bot

# Перезапустите
docker-compose restart bot
```

### Ошибки БД

```bash
# Проверьте подключение
docker-compose exec postgres psql -U upc_user -d upc_bot -c "SELECT 1"

# Примените миграции
docker-compose exec bot alembic upgrade head

# Очистите и переинициализируйте
docker-compose down -v
docker-compose up -d
```

### Redis проблемы

```bash
# Проверьте Redis
docker-compose exec redis redis-cli ping

# Очистите кэш
docker-compose exec redis redis-cli FLUSHALL
```

## Мониторинг и Логирование

### Структурированное логирование

Все логи выводятся в JSON для удобной обработки:

```bash
# Просмотр в реальном времени
docker-compose logs -f bot | jq .

# Фильтр по уровню
docker-compose logs bot | jq 'select(.level=="ERROR")'
```

### Интеграция с ELK Stack

```bash
# Настройте logstash для чтения логов
# И отправки в Elasticsearch
```

### Prometheus метрики

Добавьте `/metrics` endpoint для Prometheus:

```python
from prometheus_client import start_http_server

if __name__ == "__main__":
    start_http_server(8001)  # Метрики на :8001/metrics
```

## Масштабирование

Для большого количества пользователей:

1. **Масштабируйте БД**: добавьте replicas
2. **Используйте Redis для сессий**: встроено в конфиг
3. **Webhook вместо polling**: лучше производительность
4. **Кэширование**: используйте Redis для кэша
5. **Несколько инстансов бота**: load balancer перед ними

## Финальная проверка

```bash
# Убедитесь что все работает
curl -X GET https://api.telegram.org/bot${BOT_TOKEN}/getMe

# Проверьте метрики
curl http://localhost:8001/metrics  # Если включены

# Проверьте БД
docker-compose exec postgres psql -U upc_user -d upc_bot -c "SELECT COUNT(*) FROM \"user\";"
```

Все готово! 🎉 Ваш бот работает в production!

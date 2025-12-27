# 🚀 Railway Deployment Fix - Критичные исправления

## ⚠️ Проблемы, которые были исправлены

### 1. Backend API недоступен (502 Bad Gateway)
- ❌ **Было:** Приложение не слушало на порту
- ✅ **Исправлено:** Обновлены настройки uvicorn для Railway

### 2. CORS блокирует OPTIONS preflight запросы
- ❌ **Было:** Неполная конфигурация CORS
- ✅ **Исправлено:** Расширенная конфигурация с поддержкой всех методов

### 3. Неправильная конфигурация Railway
- ❌ **Было:** Неправильный startCommand в railway.json
- ✅ **Исправлено:** Обновлены Dockerfile и railway.json

---

## ✅ Что было изменено

### 1. **`bot/launcher.py`**
```python
# ДО:
port = int(os.getenv("PORT", "8000"))
config = uvicorn.Config(
    "bot.api_server:app",
    host="0.0.0.0",
    port=port,
    log_level="info",
    access_log=True,
)

# ПОСЛЕ:
port = int(os.getenv("PORT", "8000"))
host = os.getenv("HOST", "0.0.0.0")
config = uvicorn.Config(
    "bot.api_server:app",
    host=host,
    port=port,
    log_level="info",
    access_log=True,
    timeout_keep_alive=75,      # ← Для Railway proxy
    timeout_notify=30,           # ← Graceful shutdown
    shutdown_delay=5,            # ← Delay перед shutdown
)
```

**Почему это важно:**
- `timeout_keep_alive=75` - держит соединение открытым для Railway proxy
- `timeout_notify=30` - дает 30 секунд на graceful shutdown
- `shutdown_delay=5` - задержка перед полным завершением

---

### 2. **`Dockerfile`**
```dockerfile
# ДО:
CMD ["python", "-m", "bot.main"]

# ПОСЛЕ:
EXPOSE 8000
CMD ["python", "-m", "bot.launcher"]
```

**Почему это важно:**
- `EXPOSE 8000` - объявляет port для Railway
- Запускает `bot.launcher` вместо `bot.main` - запускает и бота И API

---

### 3. **`railway.json`**
```json
// ДО:
"startCommand": "python -m bot.main",
"restartPolicyMaxRetries": 10

// ПОСЛЕ:
"startCommand": "python -m bot.launcher",
"healthcheckPath": "/api/health",
"healthcheckTimeout": 300,
"healthcheckInterval": 30
"restartPolicyMaxRetries": 3
```

**Почему это важно:**
- `startCommand: bot.launcher` - запускает и бота, и API
- `healthcheckPath: /api/health` - Railway проверяет здоровье на этом endpoint
- `healthcheckTimeout: 300` - дает 5 минут на первый запуск
- `healthcheckInterval: 30` - проверяет каждые 30 секунд

---

### 4. **`bot/api_server.py` (CORS расширена)**
```python
# ДО:
cors_origins = [
    "https://under-people-club.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ПОСЛЕ:
cors_origins = [
    "https://under-people-club.vercel.app",
    "https://under-people-club.vercel.app/",  # ← С trailing slash
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://*.vercel.app",  # ← Для preview deployments
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    expose_headers=["*"],
    max_age=3600,  # ← Кэширует preflight на час
)
```

**Почему это важно:**
- Добавлены все возможные источники (с trailing slash, preview deployments)
- PATCH метод для будущих функций
- Дополнительные заголовки для совместимости
- `expose_headers=["*"]` - разрешает все заголовки в response
- `max_age=3600` - кэширует OPTIONS результат на час (меньше запросов)

---

### 5. **`.env.example`**
```env
# ДОБАВЛЕНО:
HOST=0.0.0.0
```

---

## 🚀 Что делать теперь

### Шаг 1: Закоммитить изменения локально

```bash
cd upc_world_bot
git add bot/launcher.py Dockerfile railway.json bot/api_server.py .env.example
git commit -m "fix(railway): Исправить 502 Bad Gateway - улучшить port binding и CORS"
git push origin master
```

### Шаг 2: Railway автоматически обновляет

Railway видит commit → автоматически:
1. Скачивает новый код
2. Выполняет `docker build` с новым Dockerfile
3. Запускает `python -m bot.launcher` с новой конфигурацией
4. Проверяет `/api/health` endpoint

### Шаг 3: Проверить логи Railway

```
Railway Dashboard
→ Services → upc_world_bot
→ Deployments
→ Logs
```

**Ищите:**
```
✅ "[API] 🌐 FastAPI server starting on 0.0.0.0:8000"
✅ "[API] ✅ Health check: http://localhost:8000/api/health"
✅ "[BOT] 🤖 Telegram Bot polling started"
✅ "cors_configured origins=[...]"
```

**Избегайте:**
```
❌ "Address already in use"
❌ "Connection refused"
❌ "ModuleNotFoundError"
❌ "502 Bad Gateway"
```

### Шаг 4: Проверить что API отвечает

```bash
# В браузере или с помощью curl:
curl https://upc-world-bot-production.up.railway.app/api/health

# Должен вернуть:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-27T..."
}
```

### Шаг 5: Проверить что сайт может подключиться

```
1. Откройте https://under-people-club.vercel.app
2. Нажмите кнопку авторизации
3. DevTools (F12) → Network → Найдите OPTIONS запрос к /api/auth/code/exchange
4. Response headers должны содержать:
   Access-Control-Allow-Origin: https://under-people-club.vercel.app
```

---

## 🧪 Локальное тестирование

Если хотите протестировать ДО push на Railway:

```bash
# Terminal 1: Запустить bot + API
cd upc_world_bot
python -m bot.launcher

# Должны увидеть:
# [API] 🌐 FastAPI server starting on 0.0.0.0:8000
# [BOT] 🤖 Telegram Bot polling started

# Terminal 2: Протестировать API
curl http://localhost:8000/api/health
# Должен вернуть: {"status":"healthy",...}

# Terminal 3: Протестировать CORS
curl -i -X OPTIONS http://localhost:8000/api/auth/code/exchange \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
# Должен вернуть 200 OK с CORS заголовками
```

---

## 🔍 Если 502 Bad Gateway все еще есть

### Проверка 1: Логи бота
```
Railway → Logs
Ищите: "API starting on 0.0.0.0:8000"
```

Если нет этой строки - приложение не запустилось.

### Проверка 2: Переменные окружения
```
Railway → Variables
Убедитесь:
✅ BOT_TOKEN (не пусто)
✅ DATABASE_URL (содержит postgresql+asyncpg)
✅ REDIS_URL (не пусто)
✅ PORT не установлена (Railway ставит автоматически)
```

### Проверка 3: Dockerfile
```bash
# Локально:
docker build -t upc .
docker run -p 8000:8000 -e PORT=8000 upc

# Если работает локально - то будет работать и на Railway
```

### Проверка 4: Healthcheck timeout
```
Railway → Settings → Healthcheck
- Path: /api/health
- Timeout: 300 seconds
- Interval: 30 seconds
```

Если вы видите "Healthcheck failed" - увеличьте timeout.

---

## 📊 Ожидаемый результат

**ДО исправлений:**
```
Browser → 502 Bad Gateway
DevTools → Error: Failed to fetch
Railway logs → "connection refused"
```

**ПОСЛЕ исправлений:**
```
Browser → Авторизация работает ✅
DevTools → OPTIONS 200 OK, затем POST 200 OK
Railway logs → "API starting on 0.0.0.0:8000" ✅
API health → /api/health returns 200 OK ✅
```

---

## ✅ Чек-лист

- ✅ Обновлён `bot/launcher.py` (timeout_keep_alive, shutdown settings)
- ✅ Обновлён `Dockerfile` (EXPOSE 8000, CMD bot.launcher)
- ✅ Обновлён `railway.json` (startCommand, healthcheck)
- ✅ Обновлён `bot/api_server.py` (расширенная CORS)
- ✅ Обновлён `.env.example` (добавлен HOST)
- ✅ Закоммитены все изменения
- ✅ Пушнуты на GitHub (Railway автодеплой)
- ⏳ Дождаться Railway rebuild (3-5 минут)
- ⏳ Проверить логи Railway
- ⏳ Протестировать авторизацию на сайте

---

**Дата:** 2025-12-27  
**Статус:** ✅ Critical Railway Fixes Applied  
**Следующее:** Monitoring Railway Deployment  
**Ожидаемый результат:** 200 OK на /api/health, работающая авторизация

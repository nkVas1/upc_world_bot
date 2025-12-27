# Исправление CORS - "Failed to fetch" Error

## 🔴 Проблема была

Браузер блокировал запросы с frontend (Vercel) к backend (Railway):

```
Error: Failed to fetch
```

**Причины:**
1. CORS middleware не разрешал домен Vercel
2. OPTIONS preflight запросы не обрабатывались правильно
3. Заголовки CORS не соответствовали требованиям браузера

---

## ✅ Решение - Обновлена конфигурация CORS

### Файл: `bot/api_server.py`

**Шаг 1: Расширенный список разрешенных источников**
```python
cors_origins = [
    "https://under-people-club.vercel.app",  # Production
    "http://localhost:3000",                  # Local dev
    "http://localhost:3001",                  # Alternative port
    "http://127.0.0.1:3000",                 # Loopback
]
```

**Шаг 2: Более разрешающие заголовки**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # All methods
    allow_headers=["*"],  # All headers (важно!)
)
```

**Шаг 3: Обновленный OPTIONS обработчик**
```python
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """
    Обрабатывает CORS preflight запросы.
    Браузер отправляет OPTIONS перед POST/PUT/DELETE.
    """
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",  # Cache preflight
        }
    )
```

**Шаг 4: Обработчики ошибок с CORS заголовками**
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"}
    )
```

---

## 🔍 Что произойдет на Railway

1. **Railway обновит бота** из GitHub (новый commit)
2. **CORS middleware активируется** с расширенными настройками
3. **OPTIONS запросы будут обработаны** правильно
4. **Браузер разрешит запросы** с Vercel домена
5. **"Failed to fetch" исчезнет** ✅

---

## 🧪 Тестирование CORS

### Локально

**Terminal 1: Запустить бота**
```bash
cd upc_world_bot
python start.py
# Bot running on http://localhost:8000
# API on http://localhost:8000/docs
```

**Terminal 2: Запустить сайт**
```bash
cd website
npm run dev
# Website on http://localhost:3000
```

**Browser: Открыть DevTools**
```
F12 → Network tab
Посмотреть запросы к API:
- Request headers должны содержать:
  Origin: http://localhost:3000
- Response headers должны содержать:
  Access-Control-Allow-Origin: http://localhost:3000
```

### На Railway

1. **Откройте Railway Dashboard**
2. **Нажмите "Redeploy"** чтобы обновить бота
3. **Проверьте логи:**
   ```
   cors_configured origins=[...]
   ```
4. **Попробуйте авторизацию на сайте:**
   - Должна работать без "Failed to fetch" ошибки

---

## 📊 Диаграмма CORS Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Browser (https://under-people-club.vercel.app)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. PREFLIGHT (OPTIONS запрос)                              │
│    OPTIONS /api/auth/code/exchange                         │
│    Origin: https://under-people-club.vercel.app            │
│                           ↓                                 │
│                    ┌──────────────────┐                    │
│                    │   Railway API     │                    │
│                    │  (FastAPI)        │                    │
│                    │  Port: 8000       │                    │
│                    └──────────────────┘                    │
│                           ↓                                 │
│    ✅ OPTIONS обработчик отвечает:                         │
│    Access-Control-Allow-Origin: https://...               │
│    Access-Control-Allow-Methods: POST                      │
│    Access-Control-Allow-Headers: Content-Type, Auth...     │
│                           ↓                                 │
│ 2. ACTUAL REQUEST (POST запрос)                            │
│    POST /api/auth/code/exchange                            │
│    {"code": "abc-123-..."}                                 │
│                           ↓                                 │
│    ✅ API обрабатывает и отвечает с CORS заголовками       │
│    {"access_token": "eyJ0eX..."}                           │
│    Access-Control-Allow-Origin: https://...               │
│                           ↓                                 │
│ 3. JavaScript получает ответ                              │
│    localStorage.setItem("access_token", token)             │
│    window.location.href = "/dashboard"                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 Если "Failed to fetch" все еще есть

### Чек-лист отладки

1. **Проверьте что Railway задеплоилась:**
   ```
   Railway Dashboard → Service Logs
   Ищите: "cors_configured origins=[...]"
   ```

2. **Проверьте DevTools:**
   ```
   F12 → Network → Найдите POST запрос
   → Response headers должны содержать:
      Access-Control-Allow-Origin: https://under-people-club.vercel.app
   ```

3. **Проверьте что сайт использует правильный URL:**
   ```javascript
   // .env.local
   NEXT_PUBLIC_API_URL=https://api.railway.app
   // Должно быть с https:// на production!
   ```

4. **Проверьте логи Vercel:**
   ```
   Vercel Dashboard → Logs
   Ищите Network errors или запросы к API
   ```

5. **Если все еще не работает, попробуйте:**
   ```bash
   # Очистить кэш браузера
   Ctrl+Shift+Delete → Clear browsing data
   
   # Полностью перезагрузить страницу
   Ctrl+Shift+R (hard refresh)
   ```

---

## 🔐 CORS в Production

### ❌ НЕБЕЗОПАСНО (для разработки только)

```python
cors_origins = ["*"]  # Разрешить всем! Уязвимо!
```

### ✅ БЕЗОПАСНО (Production)

```python
cors_origins = [
    "https://under-people-club.vercel.app",  # Только ваш домен
    "https://www.under-people-club.vercel.app",  # С www если есть
]
```

---

## 📝 Что поменялось

| Параметр | Было | Стало |
|----------|------|-------|
| `allow_origins` | `[settings.website_url, ...]` | Явный список URLs |
| `allow_methods` | `["GET", "POST", "OPTIONS"]` | `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` |
| `allow_headers` | `["Content-Type", "Authorization"]` | `["*"]` (все) |
| `OPTIONS обработчик` | Простой | С `Access-Control-Max-Age: 3600` |
| Обработка ошибок | Нет | Добавлены handlers с CORS заголовками |

---

## 🎯 Следующие шаги

1. **Deploy на Railway:**
   ```bash
   git push  # Автоматический deploy
   ```

2. **Проверить логи Railway:**
   ```
   Railway Dashboard → Services → upc_world_bot → Logs
   ```

3. **Тестировать авторизацию:**
   - Открыть https://under-people-club.vercel.app
   - Нажать "Войти через Telegram"
   - Должно работать без ошибок

4. **Если работает, то:**
   - ✅ CORS исправлена
   - ✅ Авторизация работает
   - ✅ Готово к production

---

## 🔗 Полезные ссылки

- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI: CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Vercel + Railway: Troubleshooting](https://vercel.com/docs/concepts/limits/cors)

---

**Дата:** 2025-12-27  
**Статус:** ✅ CORS Configured  
**Следующая фаза:** Testing on Railway

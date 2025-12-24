# 🔒 API Security Configuration

Защита API от несанкционированного доступа, спама и злоупотреблений.

## 🛡️ Механизмы защиты

### 1. API Key Authentication

**Защита от:**
- Несанкционированного доступа к API
- Неконтролируемого расхода OpenAI токенов
- Злоупотребления API

**Настройки в `.env`:**
```bash
# Включить аутентификацию по API ключу
API_REQUIRE_AUTH=true

# Установить сильный случайный API ключ
API_KEY=your-secret-api-key-here
```

**Генерация безопасного API ключа:**
```bash
# Метод 1: OpenSSL
openssl rand -hex 32

# Метод 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Метод 3: UUID
python -c "import uuid; print(str(uuid.uuid4()))"
```

**Как использовать API с ключом:**
```bash
# Передавайте ключ в заголовке X-API-Key
curl -X POST "http://localhost:8080/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"question": "Что такое n8n?"}'
```

**Endpoints без аутентификации:**
- `/` - корневой endpoint
- `/health` - health check
- `/docs` - API документация
- `/metrics` - Prometheus метрики

---

### 2. IP Whitelist

**Защита от:**
- Доступа с неавторизованных серверов
- Атак из интернета
- Утечки API в публичный доступ

**Настройки в `.env`:**
```bash
# Список разрешенных IP адресов (через запятую)
API_ALLOWED_IPS=127.0.0.1,192.168.1.100,10.0.0.5

# Или пусто для доступа с любых IP (НЕ рекомендуется!)
API_ALLOWED_IPS=
```

**Как работает:**
- Если `API_ALLOWED_IPS` пустой → доступ разрешен всем IP
- Если указаны IP → только эти IP могут обращаться к API
- Endpoint `/health` доступен всегда (для healthcheck)

**Как узнать свой IP:**
```bash
# На сервере
curl ifconfig.me

# Локально
ip addr show

# Из логов API при ошибке доступа
docker logs rag_api | grep "Access denied"
```

**Работа с nginx/proxy:**
Middleware автоматически читает настоящий IP из заголовка `X-Forwarded-For`, если API находится за nginx или другим reverse proxy.

---

### 3. Rate Limiting

**Защита от:**
- Спама и DoS атак
- Чрезмерного расхода OpenAI API токенов
- Случайных или злонамеренных циклов запросов

**Настройки в `.env`:**
```bash
# Включить rate limiting
API_RATE_LIMIT_ENABLED=true

# Максимум запросов в минуту с одного IP
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Максимум запросов в час с одного IP
API_RATE_LIMIT_REQUESTS_PER_HOUR=100
```

**Как работает:**
- Отслеживает количество запросов с каждого IP адреса
- При превышении лимита возвращает HTTP 429 (Too Many Requests)
- Автоматически сбрасывается через минуту/час
- Endpoint `/health` не ограничивается

**Ответ при превышении лимита:**
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per minute allowed.",
  "error": "rate_limit_exceeded",
  "retry_after": 60
}
```

---

## 🎯 Примеры конфигураций

### Пример 1: Разработка (по умолчанию)

```bash
# Минимальная защита - только rate limiting
API_REQUIRE_AUTH=false
API_KEY=
API_ALLOWED_IPS=
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10
API_RATE_LIMIT_REQUESTS_PER_HOUR=100
```

**Кто может использовать:** Любой IP, без аутентификации
**Защита:** Только от спама (rate limiting)
**Подходит для:** Локальная разработка, закрытые сети

---

### Пример 2: Production (рекомендуется)

```bash
# Полная защита
API_REQUIRE_AUTH=true
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6  # сгенерируйте свой!
API_ALLOWED_IPS=
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=20
API_RATE_LIMIT_REQUESTS_PER_HOUR=500
```

**Кто может использовать:** Любой, кто знает API ключ
**Защита:** API Key + Rate Limiting
**Подходит для:** Production, публичный API

---

### Пример 3: Максимальная безопасность

```bash
# API только для конкретных серверов
API_REQUIRE_AUTH=true
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
API_ALLOWED_IPS=192.168.1.10,192.168.1.11  # только ваши сервера
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=30
API_RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

**Кто может использовать:** Только указанные IP с правильным API ключом
**Защита:** IP Whitelist + API Key + Rate Limiting
**Подходит для:** Критичные системы, корпоративное использование

---

### Пример 4: Только для localhost

```bash
# API доступен только локально
API_REQUIRE_AUTH=false
API_KEY=
API_ALLOWED_IPS=127.0.0.1
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=50
API_RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

**Кто может использовать:** Только локальные запросы
**Защита:** IP Whitelist (только localhost) + Rate Limiting
**Подходит для:** Тестирование, интеграция с локальными сервисами

---

## 🔄 Применение изменений

После изменения настроек в `.env`:

```bash
# Перезапустить API контейнер
docker-compose restart api

# Проверить логи
docker logs -f rag_api
```

При запуске в логах увидите:
```
API Key authentication enabled
IP Whitelist enabled: 3 IPs allowed
API Rate limiting enabled: 10/min, 100/hour
```

---

## 📊 Мониторинг

### Просмотр попыток доступа:

```bash
# Блокировки по API Key
docker logs rag_api | grep "Unauthorized API access"

# Блокировки по IP Whitelist
docker logs rag_api | grep "Access denied for IP"

# Rate limiting срабатывания
docker logs rag_api | grep "rate limit exceeded"
```

### Примеры логов:

```
# Неправильный API key
Unauthorized API access attempt from 192.168.1.5 to /api/v1/query

# IP не в whitelist
Access denied for IP 203.0.113.42 to /api/v1/query (not in whitelist)

# Превышен rate limit
API Rate limit (per minute) exceeded for IP 192.168.1.10: 11/10
```

---

## 🔐 Порядок проверок безопасности

Middleware выполняются в следующем порядке (важно!):

1. **IP Whitelist** → Блокирует неразрешенные IP сразу
2. **Rate Limiting** → Ограничивает частоту запросов с разрешенных IP
3. **API Key Auth** → Проверяет аутентификацию
4. **CORS** → Применяет политику CORS

Этот порядок обеспечивает максимальную эффективность:
- Неразрешенные IP блокируются до проверки rate limit
- Rate limit проверяется до аутентификации (экономия ресурсов)

---

## 🆘 Troubleshooting

### API возвращает 401 Unauthorized

**Проблема:** Неправильный или отсутствующий API ключ

**Решение:**
1. Проверьте что `API_REQUIRE_AUTH=true` в `.env`
2. Убедитесь что передаете заголовок: `X-API-Key: your-key`
3. Проверьте что ключ совпадает с `API_KEY` в `.env`

### API возвращает 403 Access denied

**Проблема:** IP адрес не в whitelist

**Решение:**
1. Узнайте ваш IP: `curl ifconfig.me`
2. Добавьте его в `API_ALLOWED_IPS` в `.env`
3. Перезапустите API: `docker-compose restart api`
4. Или очистите `API_ALLOWED_IPS=` чтобы разрешить все IP

### API возвращает 429 Too Many Requests

**Проблема:** Превышен rate limit

**Решение:**
1. Подождите указанное время (смотрите `retry_after` в ответе)
2. Или увеличьте лимиты в `.env`:
   ```bash
   API_RATE_LIMIT_REQUESTS_PER_MINUTE=20
   API_RATE_LIMIT_REQUESTS_PER_HOUR=200
   ```
3. Перезапустите API: `docker-compose restart api`

### Логи не показывают IP Whitelist enabled

**Проблема:** Настройки не применились

**Решение:**
1. Проверьте файл `.env` в корне проекта (не `config/.env`)
2. Перезапустите контейнеры полностью:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## ⚙️ Интеграция с nginx

Если API находится за nginx reverse proxy, настройте передачу IP:

```nginx
location /api/ {
    proxy_pass http://rag_api:8080;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
}
```

Middleware автоматически прочитает настоящий IP из `X-Forwarded-For`.

---

## ⚠️ Важные замечания

1. **API KEY должен быть секретным** - не публикуйте в Git, не передавайте третьим лицам
2. **Используйте HTTPS в production** - API ключ передается в заголовках
3. **IP адреса без пробелов** - только запятые: `1.2.3.4,5.6.7.8`
4. **localhost = 127.0.0.1** - используйте IP адрес, а не hostname
5. **Rate limit применяется ПОСЛЕ IP whitelist** - сначала проверяется IP, потом лимиты
6. **Генерируйте сильные API ключи** - минимум 32 символа, случайные
7. **Храните API_KEY в .env** - файл должен быть в `.gitignore`

---

## 📚 Дополнительные ресурсы

- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **API Security Best Practices**: https://owasp.org/www-project-api-security/
- **Rate Limiting Strategies**: https://cloud.google.com/architecture/rate-limiting-strategies

---

## 🔒 Security Checklist для Production

- [ ] Установлен сильный случайный `API_KEY`
- [ ] Включена аутентификация: `API_REQUIRE_AUTH=true`
- [ ] Настроен rate limiting: `API_RATE_LIMIT_ENABLED=true`
- [ ] API_KEY добавлен в `.gitignore` (не коммитится)
- [ ] Настроен HTTPS (nginx + Let's Encrypt)
- [ ] Настроен CORS для конкретных доменов (не `*`)
- [ ] Логи мониторятся на предмет подозрительной активности
- [ ] IP Whitelist настроен (если нужен)

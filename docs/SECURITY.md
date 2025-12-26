# Security Guide

Комплексное руководство по настройке безопасности Telegram RAG Bot и REST API.

## Содержание

- [Telegram Bot Security](#telegram-bot-security)
  - [Rate Limiting](#1-rate-limiting-ограничение-частоты-запросов)
  - [User Whitelist](#2-whitelist-пользователей-белый-список-для-личных-сообщений)
  - [Group Whitelist](#3-whitelist-групп-белый-список-групп)
- [API Security](#api-security)
  - [API Key Authentication](#1-api-key-authentication)
  - [IP Whitelist](#2-ip-whitelist)
  - [API Rate Limiting](#3-rate-limiting-1)
- [Примеры конфигураций](#примеры-конфигураций)
- [Мониторинг безопасности](#мониторинг-безопасности)
- [Troubleshooting](#troubleshooting)
- [Security Checklist](#security-checklist-для-production)

---

## Telegram Bot Security

Бот имеет встроенную систему защиты от спама и несанкционированного доступа.

### 1. Rate Limiting (Ограничение частоты запросов)

**Защита от:**
- Спама
- DoS атак
- Чрезмерного расхода API токенов OpenAI

**Настройки в `.env`:**
```bash
# Включить/выключить rate limiting
RATE_LIMIT_ENABLED=true

# Максимум запросов в минуту на одного пользователя
RATE_LIMIT_REQUESTS_PER_MINUTE=5

# Максимум запросов в час на одного пользователя
RATE_LIMIT_REQUESTS_PER_HOUR=20
```

**Как работает:**
- Отслеживает количество запросов от каждого пользователя
- При превышении лимита отправляет сообщение пользователю
- Автоматически сбрасывается через минуту/час

**Сообщения пользователям:**
- Превышен лимит в минуту: "Максимум N запросов в минуту. Подождите немного."
- Превышен лимит в час: "Максимум N запросов в час. Попробуйте позже."

---

### 2. Whitelist пользователей (Белый список для личных сообщений)

**Защита от:**
- Несанкционированного использования бота
- Нецелевого использования

**Настройки в `.env`:**
```bash
# Включить белый список пользователей
WHITELIST_USERS_ENABLED=false

# Список разрешенных пользователей (Telegram user IDs через запятую)
WHITELIST_USERS=123456789,987654321,555666777
```

**Как работает:**
- Если `WHITELIST_USERS_ENABLED=true`, только пользователи из списка могут писать боту в личные сообщения
- Если `WHITELIST_USERS` пустой, доступ разрешен всем (даже если enabled=true)
- Если `WHITELIST_USERS_ENABLED=false`, белый список не проверяется

**Сообщение пользователям:**
- Нет доступа: "🔒 Извините, доступ к боту ограничен. Для получения доступа обратитесь к администратору."

**Как узнать User ID:**

1. **Через @userinfobot:**
   - Напишите боту @userinfobot
   - Получите свой ID

2. **Через логи бота:**
   - Напишите что-то боту
   - Посмотрите логи: `docker logs rag_bot | grep "user"`
   - Найдите строку вида: `Message from user 123456789`

---

### 3. Whitelist групп (Белый список групп)

**Защита от:**
- Несанкционированного добавления бота в группы
- Использования бота в нецелевых группах

**Настройки в `.env`:**
```bash
# Включить белый список групп
WHITELIST_GROUPS_ENABLED=false

# Список разрешенных групп (Chat IDs через запятую)
WHITELIST_GROUPS=-1001234567890,-1009876543210
```

**Как работает:**
- Если `WHITELIST_GROUPS_ENABLED=true`, бот отвечает только в группах из списка
- Если `WHITELIST_GROUPS` пустой, доступ разрешен во всех группах
- В группах бот отвечает только на упоминания `@bot_username`

**Сообщение пользователям:**
- Группа не в списке: "🔒 Бот не активирован в этой группе. Для активации обратитесь к администратору."

**Как узнать Group/Chat ID:**

1. **Через @getmyid_bot:**
   - Добавьте бота в группу
   - Отправьте `/id@getmyid_bot`
   - Получите Chat ID (начинается с `-`)

2. **Через логи вашего бота:**
   - Добавьте бота в группу
   - Упомяните его: `@your_bot test`
   - Посмотрите логи: `docker logs rag_bot | grep "chat"`

---

## API Security

REST API защищен от несанкционированного доступа, спама и злоупотреблений.

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

**Интеграция с nginx:**

```nginx
location /api/ {
    proxy_pass http://rag_api:8080;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
}
```

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

## Примеры конфигураций

### Telegram Bot: Полностью открытый (по умолчанию)

```bash
# Только rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=20

WHITELIST_USERS_ENABLED=false
WHITELIST_GROUPS_ENABLED=false
```

**Кто может использовать:** Все пользователи, все группы
**Защита:** Только от спама (rate limiting)
**Подходит для:** Публичные боты, сообщества

---

### Telegram Bot: Закрытый бот для команды

```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=10
RATE_LIMIT_REQUESTS_PER_HOUR=50

# Только для определенных пользователей
WHITELIST_USERS_ENABLED=true
WHITELIST_USERS=123456789,987654321,555666777

# Группы не используются
WHITELIST_GROUPS_ENABLED=false
```

**Кто может использовать:** Только 3 пользователя из списка
**Защита:** Rate limiting + ограничение доступа
**Подходит для:** Приватные боты, корпоративное использование

---

### Telegram Bot: Только для корпоративных групп

```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=30

# Личные сообщения для всех
WHITELIST_USERS_ENABLED=false

# Только в корпоративных группах
WHITELIST_GROUPS_ENABLED=true
WHITELIST_GROUPS=-1001234567890,-1009876543210,-1008887776665
```

**Кто может использовать:**
- Любой в личных сообщениях
- Только в 3 разрешенных группах

**Защита:** Rate limiting + ограничение групп
**Подходит для:** Корпоративные чаты

---

### API: Разработка (по умолчанию)

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

### API: Production (рекомендуется)

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

### API: Максимальная безопасность

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

### API: Только для localhost

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

## Применение изменений

### После изменения настроек Telegram Bot

```bash
# Перезапустить бота
./reload-config.sh bot

# Или через docker-compose
cd docker && docker-compose up -d --force-recreate --no-build bot

# Проверить логи
docker logs -f rag_bot
```

При запуске в логах увидите:
```
User whitelist enabled: 3 users
Group whitelist enabled: 2 groups
Rate limiting enabled: 5/min, 20/hour
```

---

### После изменения настроек API

```bash
# Перезапустить API
./reload-config.sh api

# Или через docker-compose
cd docker && docker-compose up -d --force-recreate --no-build api

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

## Мониторинг безопасности

### Telegram Bot

```bash
# Rate limiting срабатывания
docker logs rag_bot | grep "Rate limit"

# Whitelist блокировки
docker logs rag_bot | grep "Whitelist blocked"

# Заблокированные пользователи
docker logs rag_bot | grep "Access denied"
```

---

### API

```bash
# Блокировки по API Key
docker logs rag_api | grep "Unauthorized API access"

# Блокировки по IP Whitelist
docker logs rag_api | grep "Access denied for IP"

# Rate limiting срабатывания
docker logs rag_api | grep "rate limit exceeded"
```

**Примеры логов:**

```
# Неправильный API key
Unauthorized API access attempt from 192.168.1.5 to /api/v1/query

# IP не в whitelist
Access denied for IP 203.0.113.42 to /api/v1/query (not in whitelist)

# Превышен rate limit
API Rate limit (per minute) exceeded for IP 192.168.1.10: 11/10
```

---

## Порядок проверок безопасности

### Telegram Bot
1. **Whitelist (User/Group)** → Проверка разрешен ли доступ
2. **Rate Limiting** → Ограничение частоты запросов

### API
1. **IP Whitelist** → Блокирует неразрешенные IP сразу
2. **Rate Limiting** → Ограничивает частоту запросов с разрешенных IP
3. **API Key Auth** → Проверяет аутентификацию
4. **CORS** → Применяет политику CORS

Этот порядок обеспечивает максимальную эффективность:
- Неразрешенные IP/пользователи блокируются до проверки rate limit
- Rate limit проверяется до аутентификации (экономия ресурсов)

---

## Troubleshooting

### Telegram Bot: Бот не отвечает в группе

**Решение:**
- Проверьте что группа в `WHITELIST_GROUPS` (если enabled=true)
- Проверьте что вы упоминаете бота: `@bot_username вопрос`
- Проверьте логи: `docker logs rag_bot`

---

### Telegram Bot: Бот не отвечает в личных сообщениях

**Решение:**
- Проверьте что ваш ID в `WHITELIST_USERS` (если enabled=true)
- Проверьте rate limiting лимиты
- Проверьте логи: `docker logs rag_bot`

---

### Telegram Bot: "Rate limit exceeded"

**Решение:**
- Подождите 1 минуту или 1 час (зависит от лимита)
- Увеличьте лимиты в `.env` если нужно
- Перезапустите бота после изменений: `./reload-config.sh bot`

---

### API: 401 Unauthorized

**Проблема:** Неправильный или отсутствующий API ключ

**Решение:**
1. Проверьте что `API_REQUIRE_AUTH=true` в `.env`
2. Убедитесь что передаете заголовок: `X-API-Key: your-key`
3. Проверьте что ключ совпадает с `API_KEY` в `.env`

---

### API: 403 Access denied

**Проблема:** IP адрес не в whitelist

**Решение:**
1. Узнайте ваш IP: `curl ifconfig.me`
2. Добавьте его в `API_ALLOWED_IPS` в `.env`
3. Перезапустите API: `./reload-config.sh api`
4. Или очистите `API_ALLOWED_IPS=` чтобы разрешить все IP

---

### API: 429 Too Many Requests

**Проблема:** Превышен rate limit

**Решение:**
1. Подождите указанное время (смотрите `retry_after` в ответе)
2. Или увеличьте лимиты в `.env`:
   ```bash
   API_RATE_LIMIT_REQUESTS_PER_MINUTE=20
   API_RATE_LIMIT_REQUESTS_PER_HOUR=200
   ```
3. Перезапустите API: `./reload-config.sh api`

---

### Настройки не применились

**Решение:**

1. Проверьте файл `.env` в корне проекта (не `config/.env.example`)
2. Используйте `reload-config.sh` для применения изменений:
   ```bash
   ./reload-config.sh bot  # Только бот
   ./reload-config.sh api  # Только API
   ./reload-config.sh      # Все сервисы
   ```
3. Или пересоздайте контейнеры вручную:
   ```bash
   cd docker
   docker-compose up -d --force-recreate --no-build
   ```

---

## Security Checklist для Production

### Telegram Bot

- [ ] Включен rate limiting: `RATE_LIMIT_ENABLED=true`
- [ ] Настроены разумные лимиты (5/мин, 20/час)
- [ ] Whitelist пользователей настроен (если нужен)
- [ ] Whitelist групп настроен (если нужен)
- [ ] Логи мониторятся на предмет спама

### API

- [ ] Установлен сильный случайный `API_KEY`
- [ ] Включена аутентификация: `API_REQUIRE_AUTH=true`
- [ ] Настроен rate limiting: `API_RATE_LIMIT_ENABLED=true`
- [ ] API_KEY добавлен в `.gitignore` (не коммитится)
- [ ] Настроен HTTPS (nginx + Let's Encrypt)
- [ ] Настроен CORS для конкретных доменов (не `*`)
- [ ] Логи мониторятся на предмет подозрительной активности
- [ ] IP Whitelist настроен (если нужен)

### Общее

- [ ] `.env` файл не попадает в Git (в `.gitignore`)
- [ ] Secrets хранятся безопасно (не в README, не в коде)
- [ ] Docker volumes с данными регулярно бэкапятся
- [ ] Настроен мониторинг (Prometheus + Grafana)
- [ ] Логи ротируются и не занимают много места

---

## Важные замечания

### Telegram Bot
1. **User IDs всегда положительные числа** (например: 123456789)
2. **Group IDs всегда отрицательные и начинаются с -100** (например: -1001234567890)
3. **Без пробелов в списках** - только запятые: `123,456,789`
4. **Rate limiting применяется ПОСЛЕ whitelist** - сначала проверяется доступ, потом лимиты
5. **Для отключения whitelist** установите `ENABLED=false`, а не очищайте список

### API
1. **API KEY должен быть секретным** - не публикуйте в Git, не передавайте третьим лицам
2. **Используйте HTTPS в production** - API ключ передается в заголовках
3. **IP адреса без пробелов** - только запятые: `1.2.3.4,5.6.7.8`
4. **localhost = 127.0.0.1** - используйте IP адрес, а не hostname
5. **Rate limit применяется ПОСЛЕ IP whitelist** - сначала проверяется IP, потом лимиты
6. **Генерируйте сильные API ключи** - минимум 32 символа, случайные
7. **Храните API_KEY в .env** - файл должен быть в `.gitignore`

---

## Дополнительные ресурсы

- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **API Security Best Practices**: https://owasp.org/www-project-api-security/
- **Rate Limiting Strategies**: https://cloud.google.com/architecture/rate-limiting-strategies
- **Telegram Bot Security**: https://core.telegram.org/bots/features#privacy-mode

---

## См. также

- [Usage Guide](USAGE.md) - Использование Telegram Bot и API
- [API Documentation](API.md) - Подробная документация REST API
- [Configuration](CONFIGURATION.md) - Все параметры .env файла
- [Monitoring](MONITORING.md) - Prometheus метрики и логи

# Configuration Guide

Полное руководство по всем параметрам конфигурации Telegram RAG Bot.

## Содержание

- [Файл конфигурации](#файл-конфигурации)
- [OpenAI Configuration](#openai-configuration)
- [PostgreSQL Configuration](#postgresql-configuration)
- [RAG Pipeline Configuration](#rag-pipeline-configuration)
- [Telegram Bot Configuration](#telegram-bot-configuration)
- [API Configuration](#api-configuration)
- [Security Configuration](#security-configuration)
- [Application Configuration](#application-configuration)
- [Metrics Configuration](#metrics-configuration)
- [Примеры конфигураций](#примеры-конфигураций)

---

## Файл конфигурации

Все параметры задаются в файле `.env` в корне проекта.

**Создание .env файла:**

```bash
# Скопируйте шаблон
cp config/.env.example .env

# Отредактируйте параметры
nano .env  # или vim, или любой редактор
```

**Важно:**
- Файл `.env` должен находиться в корне проекта (не в `config/`)
- Используйте `reload-config.sh` для применения изменений без пересборки
- Не коммитьте `.env` файл в Git (уже в `.gitignore`)

---

## OpenAI Configuration

### OPENAI_API_KEY

**Описание:** API ключ для доступа к OpenAI API

**Тип:** String (обязательный)

**Пример:**
```env
OPENAI_API_KEY=sk-proj-...
```

**Как получить:**
1. Зарегистрируйтесь на https://platform.openai.com/
2. Перейдите в API Keys
3. Создайте новый ключ
4. Скопируйте и вставьте в .env

---

### EMBEDDING_MODEL

**Описание:** Модель для создания эмбеддингов текста

**Тип:** String

**По умолчанию:** `text-embedding-ada-002`

**Доступные модели:**
- `text-embedding-ada-002` - 1536 dimensions (рекомендуется)
- `text-embedding-3-small` - 1536 dimensions (новая, дешевле)
- `text-embedding-3-large` - 3072 dimensions (выше качество, дороже)

**Пример:**
```env
EMBEDDING_MODEL=text-embedding-ada-002
```

**Важно:** При изменении модели потребуется переиндексация всей базы данных

---

### LLM_MODEL

**Описание:** Модель для генерации ответов и reranking

**Тип:** String

**По умолчанию:** `gpt-4o-mini`

**Доступные модели:**
- `gpt-4o-mini` - быстрая, дешевая (рекомендуется)
- `gpt-4o` - высокое качество, дороже
- `gpt-4-turbo` - предыдущее поколение
- `gpt-3.5-turbo` - самая дешевая

**Пример:**
```env
LLM_MODEL=gpt-4o-mini
```

---

### TEMPERATURE

**Описание:** Температура генерации (креативность модели)

**Тип:** Float (0.0 - 2.0)

**По умолчанию:** `0.0`

**Рекомендации:**
- `0.0` - детерминированные ответы (рекомендуется для RAG)
- `0.3-0.5` - небольшая вариативность
- `0.7-1.0` - креативные ответы
- `>1.0` - очень креативно (не рекомендуется)

**Пример:**
```env
TEMPERATURE=0.0
```

---

### MAX_TOKENS

**Описание:** Максимальная длина генерируемого ответа в токенах

**Тип:** Integer

**По умолчанию:** `1000`

**Рекомендации:**
- `500-1000` - краткие ответы
- `1000-2000` - детальные ответы (текущая настройка)
- `2000-4000` - очень подробные ответы

**Пример:**
```env
MAX_TOKENS=1000
```

**Стоимость:** Больше токенов = выше стоимость запроса

---

## PostgreSQL Configuration

### DB_HOST

**Описание:** Хост PostgreSQL сервера

**Тип:** String

**По умолчанию:** `pgdb` (Docker service name)

**Примеры:**
```env
# Docker
DB_HOST=pgdb

# Localhost
DB_HOST=localhost

# Remote server
DB_HOST=192.168.1.100
```

---

### DB_PORT

**Описание:** Порт PostgreSQL

**Тип:** Integer

**По умолчанию:** `5432`

**Пример:**
```env
DB_PORT=5432
```

---

### DB_NAME

**Описание:** Имя базы данных

**Тип:** String

**По умолчанию:** `pgdb`

**Пример:**
```env
DB_NAME=pgdb
```

---

### DB_USER

**Описание:** Имя пользователя PostgreSQL

**Тип:** String

**По умолчанию:** `pguser`

**Пример:**
```env
DB_USER=pguser
```

---

### DB_PASSWORD

**Описание:** Пароль PostgreSQL

**Тип:** String (обязательный)

**Пример:**
```env
DB_PASSWORD=your_secure_password_here
```

**Важно:** Используйте сильный пароль в production

---

### VECTOR_TABLE

**Описание:** Имя таблицы с векторами и документами

**Тип:** String

**По умолчанию:** `openai_231225`

**Пример:**
```env
VECTOR_TABLE=openai_231225
```

**Важно:** Таблица должна существовать и содержать колонку `embedding` типа `vector(1536)`

---

## RAG Pipeline Configuration

### CONTEXT_WINDOW

**Описание:** Количество последних сообщений в истории диалога, отправляемых в GPT

**Тип:** Integer

**По умолчанию:** `7`

**Рекомендации:**
- `3-5` - краткая история (экономия токенов)
- `7-10` - средняя история (рекомендуется)
- `>10` - длинная история (больше контекста, больше токенов)

**Пример:**
```env
CONTEXT_WINDOW=7
```

**Важно:**
- Полные ответы сохраняются в БД
- При отправке в GPT используются только краткие ответы (~100-200 токенов)
- Экономия ~1500-2000 токенов на запрос

---

### TOP_K_RESULTS

**Описание:** Количество документов для начального векторного поиска

**Тип:** Integer

**По умолчанию:** `15`

**Рекомендации:**
- `10-15` - быстрый поиск
- `15-30` - лучше recall
- `>30` - медленнее, не всегда лучше

**Пример:**
```env
TOP_K_RESULTS=15
```

---

### RERANK_TOP_K

**Описание:** Количество документов после reranking LLM

**Тип:** Integer

**По умолчанию:** `5`

**Рекомендации:**
- `3-5` - оптимально (рекомендуется)
- `5-10` - больше контекста для LLM
- `>10` - риск переполнения context window

**Пример:**
```env
RERANK_TOP_K=5
```

---

### QUERY_EXPANSION_ENABLED

**Описание:** Включить расширение запроса для обработки аббревиатур

**Тип:** Boolean

**По умолчанию:** `true`

**Описание функции:**
- Расширяет аббревиатуры (ЗК → Закрытый Контур, ЕКП → Единый Комплект Поставки)
- Добавляет синонимы и технические термины
- Улучшает качество поиска для специфичных терминов

**Пример:**
```env
QUERY_EXPANSION_ENABLED=true
```

**Влияние на производительность:**
- `+1-2s` на запрос
- `+~500 токенов` (стоимость GPT-4o-mini минимальная)

---

## Telegram Bot Configuration

### TELEGRAM_BOT_TOKEN

**Описание:** Токен Telegram бота

**Тип:** String (обязательный)

**Пример:**
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Как получить:**
1. Напишите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

---

### BOT_USERNAME

**Описание:** Username бота (без @)

**Тип:** String (обязательный)

**Пример:**
```env
BOT_USERNAME=my_rag_bot
```

**Важно:** Используется для детекции упоминаний (@mention)

---

### TELEGRAM_ENABLE_FEEDBACK

**Описание:** Показывать кнопки обратной связи (👍👌👎)

**Тип:** Boolean

**По умолчанию:** `true`

**Пример:**
```env
TELEGRAM_ENABLE_FEEDBACK=true
```

---

### TELEGRAM_WEBHOOK_ENABLED

**Описание:** Использовать webhook вместо polling

**Тип:** Boolean

**По умолчанию:** `false`

**Пример:**
```env
TELEGRAM_WEBHOOK_ENABLED=false
```

**Требования для webhook:**
- Публичный домен (например: bot.example.com)
- SSL сертификат (Let's Encrypt)
- nginx для HTTPS

См. [docs/WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)

---

### TELEGRAM_WEBHOOK_URL

**Описание:** URL для webhook (только если TELEGRAM_WEBHOOK_ENABLED=true)

**Тип:** String

**Пример:**
```env
TELEGRAM_WEBHOOK_URL=https://bot.example.com/webhook/telegram
```

---

### TELEGRAM_WEBHOOK_PORT

**Описание:** Порт для webhook сервера

**Тип:** Integer

**По умолчанию:** `8443`

**Пример:**
```env
TELEGRAM_WEBHOOK_PORT=8443
```

---

## API Configuration

### API_HOST

**Описание:** IP адрес для прослушивания FastAPI

**Тип:** String

**По умолчанию:** `0.0.0.0` (все интерфейсы)

**Примеры:**
```env
# Все интерфейсы (рекомендуется для Docker)
API_HOST=0.0.0.0

# Только localhost
API_HOST=127.0.0.1
```

---

### API_PORT

**Описание:** Порт FastAPI сервера

**Тип:** Integer

**По умолчанию:** `8080`

**Пример:**
```env
API_PORT=8080
```

---

### API_ENABLE_FEEDBACK_BY_DEFAULT

**Описание:** Включать feedback по умолчанию для всех запросов

**Тип:** Boolean

**По умолчанию:** `false`

**Пример:**
```env
API_ENABLE_FEEDBACK_BY_DEFAULT=false
```

**Рекомендация:** `false` - клиенты явно запрашивают feedback через `enable_feedback=true`

---

## Security Configuration

### Telegram Bot Security

#### RATE_LIMIT_ENABLED

**Описание:** Включить rate limiting для бота

**Тип:** Boolean

**По умолчанию:** `true`

**Пример:**
```env
RATE_LIMIT_ENABLED=true
```

---

#### RATE_LIMIT_REQUESTS_PER_MINUTE

**Описание:** Максимум запросов в минуту на пользователя

**Тип:** Integer

**По умолчанию:** `5`

**Пример:**
```env
RATE_LIMIT_REQUESTS_PER_MINUTE=5
```

---

#### RATE_LIMIT_REQUESTS_PER_HOUR

**Описание:** Максимум запросов в час на пользователя

**Тип:** Integer

**По умолчанию:** `20`

**Пример:**
```env
RATE_LIMIT_REQUESTS_PER_HOUR=20
```

---

#### WHITELIST_USERS_ENABLED

**Описание:** Включить whitelist пользователей (личные сообщения)

**Тип:** Boolean

**По умолчанию:** `false`

**Пример:**
```env
WHITELIST_USERS_ENABLED=false
```

---

#### WHITELIST_USERS

**Описание:** Список разрешенных Telegram User IDs (через запятую)

**Тип:** String (comma-separated integers)

**По умолчанию:** пусто (все разрешены)

**Пример:**
```env
WHITELIST_USERS=123456789,987654321,555666777
```

**Важно:** User IDs всегда положительные числа

---

#### WHITELIST_GROUPS_ENABLED

**Описание:** Включить whitelist групп

**Тип:** Boolean

**По умолчанию:** `false`

**Пример:**
```env
WHITELIST_GROUPS_ENABLED=false
```

---

#### WHITELIST_GROUPS

**Описание:** Список разрешенных Telegram Chat IDs (через запятую)

**Тип:** String (comma-separated negative integers)

**По умолчанию:** пусто (все разрешены)

**Пример:**
```env
WHITELIST_GROUPS=-1001234567890,-1009876543210
```

**Важно:** Group IDs всегда отрицательные, начинаются с `-100`

---

### API Security

#### API_REQUIRE_AUTH

**Описание:** Требовать API ключ для доступа к API

**Тип:** Boolean

**По умолчанию:** `false`

**Пример:**
```env
API_REQUIRE_AUTH=true
```

**Рекомендация:** `true` для production

---

#### API_KEY

**Описание:** API ключ для аутентификации

**Тип:** String

**По умолчанию:** пусто

**Пример:**
```env
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Генерация:**
```bash
openssl rand -hex 32
```

**Важно:**
- Минимум 32 символа
- Случайный и секретный
- Не коммитьте в Git

---

#### API_ALLOWED_IPS

**Описание:** Whitelist IP адресов (через запятую)

**Тип:** String (comma-separated IPs)

**По умолчанию:** пусто (все разрешены)

**Пример:**
```env
API_ALLOWED_IPS=127.0.0.1,192.168.1.100,10.0.0.5
```

**Важно:** Используйте IP адреса, не hostname

---

#### API_RATE_LIMIT_ENABLED

**Описание:** Включить rate limiting для API

**Тип:** Boolean

**По умолчанию:** `true`

**Пример:**
```env
API_RATE_LIMIT_ENABLED=true
```

---

#### API_RATE_LIMIT_REQUESTS_PER_MINUTE

**Описание:** Максимум запросов в минуту с одного IP

**Тип:** Integer

**По умолчанию:** `10`

**Пример:**
```env
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10
```

---

#### API_RATE_LIMIT_REQUESTS_PER_HOUR

**Описание:** Максимум запросов в час с одного IP

**Тип:** Integer

**По умолчанию:** `100`

**Пример:**
```env
API_RATE_LIMIT_REQUESTS_PER_HOUR=100
```

---

## Application Configuration

### DEBUG

**Описание:** Режим отладки

**Тип:** Boolean

**По умолчанию:** `false`

**Пример:**
```env
DEBUG=false
```

**Влияние:**
- `true` - подробные логи, traceback в ответах API
- `false` - минимальные логи, скрытие внутренних ошибок

**Рекомендация:** `false` в production

---

### LOG_LEVEL

**Описание:** Уровень логирования

**Тип:** String

**По умолчанию:** `INFO`

**Доступные уровни:**
- `DEBUG` - все логи (очень подробно)
- `INFO` - информационные сообщения (рекомендуется)
- `WARNING` - только предупреждения и ошибки
- `ERROR` - только ошибки
- `CRITICAL` - только критические ошибки

**Пример:**
```env
LOG_LEVEL=INFO
```

---

## Metrics Configuration

### METRICS_ENABLED

**Описание:** Включить Prometheus метрики

**Тип:** Boolean

**По умолчанию:** `true`

**Пример:**
```env
METRICS_ENABLED=true
```

**Endpoint:** `/metrics`

**Метрики:**
- `rag_queries_total` - Всего запросов
- `rag_query_duration_seconds` - Время обработки
- `rag_feedback_total` - Обратная связь
- `openai_api_calls_total` - Вызовы OpenAI API
- `openai_tokens_used_total` - Использовано токенов
- `vector_search_duration_seconds` - Время векторного поиска

---

## Примеры конфигураций

### Локальная разработка

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.0
MAX_TOKENS=1000

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=dev_password
VECTOR_TABLE=openai_231225

# RAG
CONTEXT_WINDOW=7
TOP_K_RESULTS=15
RERANK_TOP_K=5
QUERY_EXPANSION_ENABLED=true

# Telegram Bot
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=dev_bot
TELEGRAM_ENABLE_FEEDBACK=true
TELEGRAM_WEBHOOK_ENABLED=false

# API
API_HOST=127.0.0.1
API_PORT=8080
API_ENABLE_FEEDBACK_BY_DEFAULT=false

# Security (минимальная)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=10
RATE_LIMIT_REQUESTS_PER_HOUR=50
WHITELIST_USERS_ENABLED=false
WHITELIST_GROUPS_ENABLED=false
API_REQUIRE_AUTH=false
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=20
API_RATE_LIMIT_REQUESTS_PER_HOUR=200

# Application
DEBUG=true
LOG_LEVEL=DEBUG
METRICS_ENABLED=true
```

---

### Production (Polling)

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.0
MAX_TOKENS=1000

# PostgreSQL
DB_HOST=pgdb
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=STRONG_PASSWORD_HERE
VECTOR_TABLE=openai_231225

# RAG
CONTEXT_WINDOW=7
TOP_K_RESULTS=15
RERANK_TOP_K=5
QUERY_EXPANSION_ENABLED=true

# Telegram Bot
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=prod_bot
TELEGRAM_ENABLE_FEEDBACK=true
TELEGRAM_WEBHOOK_ENABLED=false

# API
API_HOST=0.0.0.0
API_PORT=8080
API_ENABLE_FEEDBACK_BY_DEFAULT=false

# Security (полная)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=20
WHITELIST_USERS_ENABLED=false
WHITELIST_GROUPS_ENABLED=true
WHITELIST_GROUPS=-1001234567890,-1009876543210
API_REQUIRE_AUTH=true
API_KEY=GENERATED_SECURE_KEY_HERE
API_ALLOWED_IPS=
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=20
API_RATE_LIMIT_REQUESTS_PER_HOUR=500

# Application
DEBUG=false
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

---

### Production (Webhook)

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.0
MAX_TOKENS=1000

# PostgreSQL
DB_HOST=pgdb
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=STRONG_PASSWORD_HERE
VECTOR_TABLE=openai_231225

# RAG
CONTEXT_WINDOW=7
TOP_K_RESULTS=15
RERANK_TOP_K=5
QUERY_EXPANSION_ENABLED=true

# Telegram Bot (Webhook)
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=prod_bot
TELEGRAM_ENABLE_FEEDBACK=true
TELEGRAM_WEBHOOK_ENABLED=true
TELEGRAM_WEBHOOK_URL=https://bot.example.com/webhook/telegram
TELEGRAM_WEBHOOK_PORT=8443

# API
API_HOST=0.0.0.0
API_PORT=8080
API_ENABLE_FEEDBACK_BY_DEFAULT=false

# Security
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=20
WHITELIST_USERS_ENABLED=false
WHITELIST_GROUPS_ENABLED=true
WHITELIST_GROUPS=-1001234567890,-1009876543210
API_REQUIRE_AUTH=true
API_KEY=GENERATED_SECURE_KEY_HERE
API_ALLOWED_IPS=
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=20
API_RATE_LIMIT_REQUESTS_PER_HOUR=500

# Application
DEBUG=false
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

---

## Применение изменений

После изменения `.env`:

```bash
# Быстрый способ (рекомендуется)
./reload-config.sh

# Или конкретный сервис
./reload-config.sh bot  # Только бот
./reload-config.sh api  # Только API

# Вручную через docker-compose
cd docker
docker-compose up -d --force-recreate --no-build
```

**Важно:** НЕ используйте `docker-compose restart` - он не подхватывает изменения в `.env`!

---

## Проверка конфигурации

### Проверка переменных окружения

```bash
# Посмотреть переменные в контейнере
docker exec rag_bot env | grep -E "OPENAI|TELEGRAM|RATE"
docker exec rag_api env | grep -E "API_|OPENAI"

# Проверить логи запуска
docker logs rag_bot --tail 50 | grep -E "enabled|configured"
docker logs rag_api --tail 50 | grep -E "enabled|configured"
```

### Проверка подключения к БД

```bash
# Из контейнера API
docker exec rag_api python -c "from src.core.db import get_db_pool; import asyncio; asyncio.run(get_db_pool())"
```

### Проверка OpenAI API

```bash
# Из контейнера
docker exec rag_api python -m src.cli test-rag "Тестовый вопрос"
```

---

## См. также

- [Usage Guide](USAGE.md) - Использование CLI, API, Telegram Bot
- [Security Guide](SECURITY.md) - Настройка безопасности
- [Monitoring Guide](MONITORING.md) - Prometheus метрики и логи
- [Webhook Setup](WEBHOOK_SETUP.md) - Настройка webhook режима

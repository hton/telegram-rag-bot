# Telegram RAG Bot

Python реализация RAG (Retrieval-Augmented Generation) бота для Telegram с использованием OpenAI embeddings и GPT-4o-mini.

## 📑 Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [RAG Pipeline](#rag-pipeline)
- [Установка](#установка)
  - [Требования](#требования)
  - [Быстрый старт с Docker](#быстрый-старт-с-docker)
  - [Изменение конфигурации (.env)](#изменение-конфигурации-env)
  - [Обновление Docker контейнеров](#обновление-docker-контейнеров)
  - [Webhook режим (Production)](#webhook-режим-production)
  - [Локальная разработка](#локальная-разработка)
- [Использование](#использование)
  - [CLI Команды](#cli-команды)
  - [API Endpoints](#api-endpoints)
  - [Telegram Bot](#telegram-bot)
- [Безопасность](#безопасность)
  - [Telegram Bot Security](#telegram-bot-security)
  - [API Security](#api-security)
- [Конфигурация](#конфигурация)
- [Структура проекта](#структура-проекта)
- [Мониторинг](#мониторинг)
  - [Prometheus Metrics](#prometheus-metrics)
  - [Логи](#логи)
- [Разработка](#разработка)
  - [Запуск тестов](#запуск-тестов)
  - [Форматирование кода](#форматирование-кода)
  - [Создание миграции](#создание-миграции)
- [Troubleshooting](#troubleshooting)
- [Лицензия](#лицензия)
- [Автор](#автор)

## Возможности

- 🤖 **RAG Pipeline**: Полный цикл поиска и генерации ответов на основе векторной базы данных
- 🔍 **Query Expansion**: Автоматическое расширение запросов для лучшей обработки аббревиатур и технических терминов
- 📱 **Telegram Bot**: Интерактивный бот с поддержкой обратной связи
- 🌐 **REST API**: HTTP API для интеграции с другими системами
- 🔒 **Security**: Комплексная защита бота и API (whitelist, rate limiting, API key auth)
- 💾 **Chat Memory**: Контекст диалога для более релевантных ответов
- 📊 **Analytics**: Метрики и статистика использования
- 🐳 **Docker**: Готовые образы для развертывания
- 📈 **Prometheus**: Мониторинг и метрики

## Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TELEGRAM RAG BOT ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐                    ┌──────────────────────────┐
│    TELEGRAM BOT         │                    │      REST API            │
├─────────────────────────┤                    ├──────────────────────────┤
│  Middleware:            │                    │  Middleware:             │
│  - Logging              │                    │  - APIKey Auth           │
│  - Typing Indicator     │                    │  - IP Whitelist          │
│  - User/Group Whitelist │                    │  - Rate Limiting         │
│  - Rate Limiting        │                    │                          │
│    (5/min, 20/hr)       │                    │  Endpoints:              │
│                         │                    │  - /api/v1/query         │
│  Features:              │                    │  - /api/v1/feedback      │
│  - Mention detection    │                    │  - /api/v1/admin/*       │
│  - Feedback buttons     │                    │  - /health, /metrics     │
│  - Webhook/Polling      │                    │                          │
└───────────┬─────────────┘                    └───────────┬──────────────┘
            │                                              │
            └──────────────────┬───────────────────────────┘
                               │
                               ▼
                   ┌───────────────────────┐
                   │   QUERY SERVICE       │
                   │  (Orchestration)      │
                   │                       │
                   │  • Chat Memory Mgmt   │
                   │  • Query Logging      │
                   │  • Metrics Tracking   │
                   │  • Feedback Handling  │
                   └──────────┬────────────┘
                              │
                              ▼
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃            RAG PIPELINE (6 Steps)               ┃
        ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
        ┃                                                 ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 0: Query Expansion (optional)        │  ┃
        ┃  │ • Expand abbreviations (ЗК→Закрытый       │  ┃
        ┃  │   Контур, ЕКП→Единый Комплект             │  ┃
        ┃  │   Поставки)                               │  ┃
        ┃  │ • Add synonyms and technical terms        │  ┃
        ┃  │ • Model: GPT-4o-mini                      │  ┃
        ┃  └──────────────┬────────────────────────────┘  ┃
        ┃                 │ ~1-2s                          ┃
        ┃                 ▼                                ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 1: Embedding                         │  ┃
        ┃  │ • Model: text-embedding-ada-002           │  ┃
        ┃  │ • Dimensions: 1536                        │  ┃
        ┃  │ • Converts query → vector                 │  ┃
        ┃  └──────────────┬────────────────────────────┘  ┃
        ┃                 │ ~1-2s                          ┃
        ┃                 ▼                                ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 2: Vector Search                     │  ┃
        ┃  │ • PostgreSQL + pgvector                   │  ┃
        ┃  │ • Cosine similarity search                │  ┃
        ┃  │ • Retrieve top 15 chunks                  │  ┃
        ┃  │ • IVFFlat index for performance           │  ┃
        ┃  └──────────────┬────────────────────────────┘  ┃
        ┃                 │ ~0.1s                          ┃
        ┃                 ▼                                ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 3: LLM Reranking                     │  ┃
        ┃  │ • Model: GPT-4o-mini                      │  ┃
        ┃  │ • Selects top 5 most relevant sources     │  ┃
        ┃  │ • Groups by source_path                   │  ┃
        ┃  │ • Deterministic ranking                   │  ┃
        ┃  └──────────────┬────────────────────────────┘  ┃
        ┃                 │ ~3-4s                          ┃
        ┃                 ▼                                ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 4: Fetch Full Documents              │  ┃
        ┃  │ • Retrieve complete docs from DB          │  ┃
        ┃  │ • Context window expansion                │  ┃
        ┃  │ • Fetch surrounding chunks                │  ┃
        ┃  └──────────────┬────────────────────────────┘  ┃
        ┃                 │ ~0.1s                          ┃
        ┃                 ▼                                ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 5: Aggregate Context                 │  ┃
        ┃  │ • Combine documents                       │  ┃
        ┃  │ • Format for LLM consumption              │  ┃
        ┃  │ • Add metadata and structure              │  ┃
        ┃  └──────────────┬────────────────────────────┘  ┃
        ┃                 │ ~0.01s                         ┃
        ┃                 ▼                                ┃
        ┃  ┌───────────────────────────────────────────┐  ┃
        ┃  │ Step 6: Generate Answer                   │  ┃
        ┃  │ • Model: GPT-4o-mini                      │  ┃
        ┃  │ • With aggregated context                 │  ┃
        ┃  │ • With chat history (3 msgs)              │  ┃
        ┃  │ • Temperature: 0.0 (deterministic)        │  ┃
        ┃  └───────────────────────────────────────────┘  ┃
        ┃                 │ ~7-10s                         ┃
        ┗━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                          │
                          ▼
    ┌──────────────────────────────────────────────────────────┐
    │                 DATA & MONITORING LAYER                   │
    ├──────────────────────────────────────────────────────────┤
    │                                                          │
    │  ┌─────────────────────┐    ┌──────────────────────┐    │
    │  │   PostgreSQL        │    │   Prometheus         │    │
    │  ├─────────────────────┤    ├──────────────────────┤    │
    │  │ Tables:             │    │ Metrics:             │    │
    │  │ • openai_221225     │    │ • Query counts       │    │
    │  │   (vectors+pgvector)│    │ • Duration stats     │    │
    │  │ • query_logs        │    │ • Feedback ratings   │    │
    │  │   (analytics)       │    │ • OpenAI API calls   │    │
    │  │ • chat_history      │    │ • Token usage        │    │
    │  │   (memory)          │    │ • Vector search      │    │
    │  │ • feedback          │    │ • Active users       │    │
    │  │   (ratings)         │    │                      │    │
    │  │                     │    │ Persistence:         │    │
    │  │ Indexes:            │    │ • Init from DB       │    │
    │  │ • ivfflat (vector)  │    │   on startup         │    │
    │  │ • source_path       │    │ • Survive restarts   │    │
    │  └─────────────────────┘    └──────────────────────┘    │
    │                                                          │
    └──────────────────────────────────────────────────────────┘

                  ┌──────────────────────────┐
                  │    External Services     │
                  ├──────────────────────────┤
                  │ • OpenAI API             │
                  │   - text-embedding-ada-002│
                  │   - gpt-4o-mini          │
                  │                          │
                  │ • Telegram Bot API       │
                  │   - Polling/Webhook      │
                  └──────────────────────────┘

Key Features:
  • Query Expansion for abbreviations (Russian context)
  • Deterministic RAG (temperature=0.0)
  • Chat memory (3 message context window)
  • Multi-layer security (whitelist, rate limiting, auth)
  • Prometheus metrics with DB persistence
  • Feedback collection (👍👌👎)

Performance: ~10-11s total (optimized from ~23s, 55% improvement)
```

## RAG Pipeline

0. **Query Expansion** (опционально) → Расширение запроса для лучшей обработки аббревиатур (ЗК→Закрытый Контур, ЕКП→Единый Комплект Поставки)
1. **Embedding** → OpenAI text-embedding-ada-002 (1536 dimensions)
2. **Vector Search** → PostgreSQL + pgvector (top 15 results, cosine similarity)
3. **Reranking** → GPT-4o-mini (select top 5 sources)
4. **Fetch Full Documents** → Retrieve complete docs from PostgreSQL by source_path
5. **Aggregate Context** → Combine and format documents for LLM
6. **Answer Generation** → GPT-4o-mini with chat history (temperature=0.0, max_tokens=1000)

## Установка

### Требования

- Python 3.11+
- PostgreSQL с расширением pgvector
- OpenAI API ключ
- Telegram Bot Token

### Быстрый старт с Docker

1. **Клонируйте репозиторий**
```bash
cd telegram-rag-bot
```

2. **Настройте переменные окружения**
```bash
cp config/.env.example .env
# Отредактируйте .env файл
```

3. **Запустите сервисы (режим polling)**
```bash
cd docker
docker-compose up -d
```

> 📘 **Для продакшн окружения:** См. [Настройка Webhook режима](docs/WEBHOOK_SETUP.md) для работы через HTTPS с nginx

### Изменение конфигурации (.env)

**Важно:** При изменении параметров в `.env` файле **НЕ нужно пересобирать образы**!

Но нужно **пересоздать контейнеры**, чтобы они подхватили новые переменные окружения.

**Способ 1: Удобный скрипт (рекомендуется)**
```bash
# Из корня проекта
./reload-config.sh          # Пересоздать все сервисы
./reload-config.sh bot      # Только бот
./reload-config.sh api      # Только API
```

**Способ 2: Docker Compose напрямую**
```bash
cd docker

# Пересоздать все сервисы с новыми env переменными
docker-compose up -d --force-recreate --no-build

# Или только конкретный сервис
docker-compose up -d --force-recreate --no-build bot
docker-compose up -d --force-recreate --no-build api
```

**❌ НЕ используйте `docker-compose restart`** - он не подхватывает изменения в .env!

**Почему нужно пересоздание?**
- Docker загружает переменные окружения **при создании контейнера**, а не при запуске процесса
- `restart` просто перезапускает процесс в существующем контейнере
- `up -d --force-recreate` создаёт новый контейнер с новыми env переменными

**Что происходит:**
- ✅ Docker Compose читает `.env` файл
- ✅ Контейнеры **пересоздаются** с новыми переменными окружения
- ✅ Python приложение получает обновлённую конфигурацию при старте
- ⚡ Время: ~5-10 секунд (без пересборки образов)

**Примеры изменений, не требующих rebuild:**
- Изменение API ключей (OpenAI, Telegram)
- Включение/выключение whitelist или rate limiting
- Изменение лимитов запросов (MAX_TOKENS, RATE_LIMIT_*)
- Изменение параметров RAG (TOP_K, CONTEXT_WINDOW, TEMPERATURE)
- Включение/выключение Query Expansion
- Изменение уровня логирования

**Когда нужен rebuild (`--build`):**
- Изменился код приложения (Python файлы)
- Обновлены зависимости (requirements.txt)
- Изменился Dockerfile

**Проверка изменений:**
```bash
# Посмотреть логи после перезапуска
docker-compose logs -f bot
docker-compose logs -f api

# Проверить что новые настройки применились
docker logs rag_bot --tail 20
docker logs rag_api --tail 20
```

### Обновление Docker контейнеров

Когда вы обновили код в репозитории (git pull, новый коммит и т.д.), вам нужно обновить запущенные контейнеры без потери данных:

**1. Быстрое обновление БЕЗ перезакачки образов (рекомендуется):**
```bash
cd docker

# Пересобрать и перезапустить одной командой
# Использует кэш Docker, пересобирает только измененные слои
docker-compose up -d --build
```

**2. Обновление с пересборкой конкретного сервиса:**
```bash
cd docker

# Пересобрать только API (с использованием кэша)
docker-compose build api
docker-compose up -d api

# Или только бота
docker-compose build bot
docker-compose up -d bot
```

**3. Полная пересборка БЕЗ кэша (если нужно обновить базовые образы):**
```bash
cd docker

# ВНИМАНИЕ: будет скачивать базовые образы заново!
docker-compose build --no-cache

# Перезапустить контейнеры
docker-compose up -d
```

**4. Обновление с остановкой:**
```bash
cd docker

# Остановить и удалить контейнеры (данные в volumes сохраняются!)
docker-compose down

# Пересобрать образы с кэшем
docker-compose build

# Запустить заново
docker-compose up -d
```

**5. Проверка статуса после обновления:**
```bash
# Посмотреть запущенные контейнеры
docker-compose ps

# Посмотреть логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f bot

# Проверить health check API
curl http://localhost:8080/health
```

**6. Применение миграций БД после обновления:**
```bash
# Если были изменения в схеме БД, примените миграции
docker-compose exec api python -m src.cli migrate-up

# Или зайдите в контейнер
docker-compose exec api bash
python -m src.cli migrate-up
exit
```

**Важно:**
- ✅ **Данные в PostgreSQL сохраняются** - они хранятся в Docker volume `db_storage`
- ✅ **Логи сохраняются** - они в директории `../logs` на хосте
- ✅ **Кэш Docker** - по умолчанию используется для ускорения сборки
- ⚠️ При использовании `docker-compose down -v` будут **удалены все volumes** (включая БД!)
- ⚠️ Флаг `--no-cache` скачивает и пересобирает всё заново (используйте только если нужно обновить базовые образы)

### Webhook режим (Production)

Для продакшн окружения рекомендуется использовать **webhook режим** вместо polling:

**Преимущества webhook:**
- ⚡ Мгновенные ответы (без задержки)
- 💰 Меньше нагрузки на сервер
- 📈 Лучшая масштабируемость

**Требования:**
- Публичный домен (например: `bot.example.com`)
- SSL сертификат (Let's Encrypt)
- Nginx для HTTPS

**📘 Подробная инструкция:** [docs/WEBHOOK_SETUP.md](docs/WEBHOOK_SETUP.md)

Включает:
- Пошаговую настройку nginx
- Получение SSL сертификата
- Регистрацию webhook в Telegram
- Troubleshooting

### Локальная разработка

1. **Создайте виртуальное окружение**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. **Установите зависимости**
```bash
pip install -r requirements.txt
```

3. **Настройте .env**
```bash
cp config/.env.example .env
# Отредактируйте .env
```

4. **Запустите PostgreSQL** (с pgvector)
```bash
cd docker
docker-compose -f docker-compose.dev.yaml up -d
```

5. **Инициализируйте БД**
```bash
python -m src.cli init
```

6. **Примените миграции**
```bash
alembic upgrade head
```

7. **Запустите бота**
```bash
# Telegram Bot (polling)
python -m src.cli run-bot

# FastAPI
python -m src.cli run-api

# Оба сервиса (в разных терминалах)
```

## Использование

### CLI Команды

```bash
# Запустить Telegram бота
python -m src.cli run-bot --polling

# Запустить FastAPI сервер
python -m src.cli run-api --host 0.0.0.0 --port 8080

# Инициализировать БД
python -m src.cli init

# Создать миграцию
python -m src.cli migrate -m "migration message"

# Применить миграции
python -m src.cli migrate-up

# Откатить миграции
python -m src.cli migrate-down

# Тест RAG pipeline
python -m src.cli test-rag "Как установить платформу?"
```

### API Endpoints

**Query API:**
```bash
# Задать вопрос
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Что такое ЕКП?",
    "enable_memory": true,
    "enable_feedback": false
  }'

# Отправить обратную связь
curl -X POST http://localhost:8080/api/v1/query/feedback/{query_id} \
  -H "Content-Type: application/json" \
  -d '{"rating": "good"}'
```

**Admin API:**
```bash
# Статистика
curl http://localhost:8080/api/v1/admin/stats?days=30

# Статистика обратной связи
curl http://localhost:8080/api/v1/admin/feedback/stats?days=30

# Популярные запросы
curl http://localhost:8080/api/v1/admin/queries/popular?limit=10

# Метрики производительности
curl http://localhost:8080/api/v1/admin/performance?days=7
```

**Health Checks:**
```bash
# Базовый health check
curl http://localhost:8080/health

# Readiness check
curl http://localhost:8080/health/ready

# Liveness check
curl http://localhost:8080/health/live
```

**Prometheus Metrics:**
```bash
curl http://localhost:8080/metrics
```

#### Отправка фидбека через API

API поддерживает сбор обратной связи для улучшения качества ответов. Фидбек помогает идентифицировать "хорошие" ответы для будущего использования в Q&A кэше.

**1. Получение query_id**

При отправке запроса включите `enable_feedback=true` для получения feedback_url:

```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "question": "Как установить платформу?",
    "enable_feedback": true
  }'
```

**Ответ:**
```json
{
  "query_id": "343162dc-a6b3-430c-acf6-72c8380a1429",
  "answer": "Полный ответ с инструкциями...",
  "sources": ["https://..."],
  "feedback_enabled": true,
  "feedback_url": "/api/v1/query/feedback/343162dc-a6b3-430c-acf6-72c8380a1429",
  "processing_time_ms": 10234.5,
  "timestamp": "2025-12-26T03:56:00Z"
}
```

**2. Отправка фидбека**

Endpoint: `POST /api/v1/query/feedback/{query_id}`

**Допустимые значения rating:**
- `"good"` - хороший ответ (👍)
- `"notbad"` - нормальный ответ (👌)
- `"bad"` - плохой ответ (👎)

**Пример 1: Положительный фидбек**
```bash
curl -X POST http://localhost:8080/api/v1/query/feedback/343162dc-a6b3-430c-acf6-72c8380a1429 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "rating": "good"
  }'
```

**Пример 2: Негативный фидбек с комментарием**
```bash
curl -X POST http://localhost:8080/api/v1/query/feedback/343162dc-a6b3-430c-acf6-72c8380a1429 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "rating": "bad",
    "comment": "Ответ не содержит информацию о версии 2025.10"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Feedback saved successfully",
  "query_id": "343162dc-a6b3-430c-acf6-72c8380a1429",
  "rating": "good"
}
```

**3. Хранение фидбека**

Фидбек сохраняется в двух таблицах PostgreSQL:
- `feedback` - детальная информация (query_id, rating, comment, created_at)
- `query_logs` - поле feedback для быстрой аналитики

**4. Пример на Python**

```python
import requests

API_URL = "http://localhost:8080/api/v1"
API_KEY = "your-api-key"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Отправить вопрос
response = requests.post(
    f"{API_URL}/query",
    headers=headers,
    json={
        "question": "Как настроить multipath?",
        "enable_feedback": True
    }
)

data = response.json()
query_id = data["query_id"]

# Отправить фидбек
feedback = requests.post(
    f"{API_URL}/query/feedback/{query_id}",
    headers=headers,
    json={
        "rating": "good",
        "comment": "Очень подробный ответ с примерами команд"
    }
)
```

**Настройки в .env:**
```bash
# Фидбек по умолчанию выключен (нужно явно включать в запросе)
API_ENABLE_FEEDBACK_BY_DEFAULT=false
```

### Telegram Bot

1. Найдите бота в Telegram: `@your_bot_username`
2. Упомяните бота в сообщении:
   ```
   @your_bot_username Как установить платформу в закрытом контуре?
   ```
3. Оцените ответ кнопками 👍👌👎

**Команды:**
- `/start` - Начать работу
- `/help` - Справка

## Безопасность

### Telegram Bot Security

Бот защищен от спама и несанкционированного использования:

- 🛡️ **Rate Limiting** - Ограничение частоты запросов (5/мин, 20/час по умолчанию)
- 👥 **User Whitelist** - Белый список пользователей для личных сообщений
- 💬 **Group Whitelist** - Белый список групп для использования бота

**Настройка в `.env`:**
```env
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=20

# User Whitelist (пусто = все разрешены)
WHITELIST_USERS_ENABLED=true
WHITELIST_USERS=123456789,987654321

# Group Whitelist (пусто = все разрешены)
WHITELIST_GROUPS_ENABLED=true
WHITELIST_GROUPS=-1001234567890,-1009876543210
```

📖 **Подробная документация:** [docs/SECURITY.md](docs/SECURITY.md)

---

### API Security

REST API защищен от несанкционированного доступа и злоупотреблений:

- 🔐 **API Key Authentication** - Аутентификация по ключу в заголовке `X-API-Key`
- 🌐 **IP Whitelist** - Ограничение доступа по IP адресам
- ⏱️ **Rate Limiting** - Защита от спама (10/мин, 100/час по умолчанию)

**Настройка в `.env`:**
```env
# API Key Authentication
API_REQUIRE_AUTH=true
API_KEY=your-secret-api-key-here  # openssl rand -hex 32

# IP Whitelist (пусто = все разрешены)
API_ALLOWED_IPS=127.0.0.1,192.168.1.100

# Rate Limiting
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10
API_RATE_LIMIT_REQUESTS_PER_HOUR=100
```

**Использование с API Key:**
```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"question": "Что такое n8n?"}'
```

📖 **Подробная документация:** [docs/API_SECURITY.md](docs/API_SECURITY.md)

---

## Конфигурация

### Основные параметры (.env)

```env
# OpenAI
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.0
MAX_TOKENS=1000

# PostgreSQL
DB_HOST=pgdb
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=your_password
VECTOR_TABLE=openai_221225

# RAG Configuration
CONTEXT_WINDOW=3                # Количество сообщений в истории
TOP_K_RESULTS=15               # Начальный поиск
RERANK_TOP_K=5                 # После reranking
QUERY_EXPANSION_ENABLED=true   # Расширение запросов для аббревиатур

# Telegram Bot
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=your_bot
TELEGRAM_ENABLE_FEEDBACK=true

# Bot Security
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=20
WHITELIST_USERS_ENABLED=false
WHITELIST_USERS=
WHITELIST_GROUPS_ENABLED=false
WHITELIST_GROUPS=

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_ENABLE_FEEDBACK_BY_DEFAULT=false

# API Security
API_REQUIRE_AUTH=false
API_KEY=
API_ALLOWED_IPS=
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10
API_RATE_LIMIT_REQUESTS_PER_HOUR=100

# Application
DEBUG=false
LOG_LEVEL=INFO

# Metrics
METRICS_ENABLED=true
```

📖 **Полное описание параметров:**
- [Безопасность Telegram Bot](docs/SECURITY.md)
- [Безопасность API](docs/API_SECURITY.md)
- [Настройка Webhook](docs/WEBHOOK_SETUP.md)

## Структура проекта

```
telegram-rag-bot/
├── src/
│   ├── api/              # FastAPI приложение
│   │   ├── middleware/   # API middleware (auth, rate limit, IP whitelist)
│   │   ├── routes/       # API endpoints
│   │   └── schemas/      # API schemas
│   ├── bot/              # Telegram bot
│   │   ├── handlers/     # Message handlers
│   │   └── middleware/   # Bot middleware (security, logging)
│   ├── core/             # Ядро (config, db, logging)
│   ├── models/           # SQLAlchemy модели
│   ├── rag/              # RAG pipeline
│   │   ├── prompts.py    # Промпты для RAG (v2.0 - русские)
│   │   └── query_expander.py  # Расширение запросов
│   ├── services/         # Бизнес-логика
│   ├── schemas/          # Pydantic схемы
│   ├── cli.py            # CLI команды
│   └── main.py           # Entry point
├── docs/                 # Документация
│   ├── SECURITY.md       # Безопасность Telegram Bot
│   ├── API_SECURITY.md   # Безопасность API
│   └── WEBHOOK_SETUP.md  # Настройка webhook
├── alembic/              # Миграции БД
├── config/               # Конфигурация
├── docker/               # Docker файлы
├── tests/                # Тесты
├── .env                  # Переменные окружения
└── README.md
```

## Мониторинг

### Prometheus Metrics

Метрики доступны на `/metrics`:

- `rag_queries_total` - Всего запросов
- `rag_query_duration_seconds` - Время обработки
- `rag_feedback_total` - Обратная связь
- `openai_api_calls_total` - Вызовы OpenAI API
- `openai_tokens_used_total` - Использовано токенов
- `vector_search_duration_seconds` - Время векторного поиска

### Логи

Логи сохраняются в `logs/`:
- `app_YYYY-MM-DD.log` - Все логи
- `error_YYYY-MM-DD.log` - Только ошибки

## Разработка

### Запуск тестов

```bash
pytest tests/
```

### Форматирование кода

```bash
black src/
ruff check src/
```

### Создание миграции

```bash
python -m src.cli migrate -m "add new table"
alembic upgrade head
```

## Troubleshooting

### Проблема: "No module named 'src'"

**Решение:**
```bash
export PYTHONPATH=/path/to/telegram-rag-bot:$PYTHONPATH
```

### Проблема: "Database connection refused"

**Решение:**
Проверьте что PostgreSQL запущен и доступен:
```bash
docker-compose -f docker/docker-compose.dev.yaml ps
```

### Проблема: "OpenAI API key not found"

**Решение:**
Убедитесь что `.env` файл создан и содержит `OPENAI_API_KEY`

## Лицензия

MIT

## Автор

Telegram RAG Bot - Python реализация RAG агента для Telegram

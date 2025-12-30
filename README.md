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
- [Документация](#документация)
- [Лицензия](#лицензия)

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

## Документация

### 📘 Руководства пользователя

- **[Usage Guide](docs/USAGE.md)** - Использование Telegram Bot, REST API, и CLI команд
- **[API Documentation](docs/API.md)** - Полная документация REST API с примерами
- **[Security Guide](docs/SECURITY.md)** - Настройка безопасности Telegram Bot и API
- **[Configuration Guide](docs/CONFIGURATION.md)** - Все параметры конфигурации (.env)

### 🔧 Руководства администратора

- **[Monitoring Guide](docs/MONITORING.md)** - Prometheus метрики и логирование
- **[Cost Analysis](docs/COST_ANALYSIS.md)** - Расчет стоимости использования OpenAI API
- **[RAG Quality](docs/RAG_QUALITY.md)** - Качество ответов RAG системы и результаты тестирования
- **[Webhook Setup](docs/WEBHOOK_SETUP.md)** - Настройка webhook режима для production
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Решение распространённых проблем

### 👨‍💻 Руководства разработчика

- **[Development Guide](docs/DEVELOPMENT.md)** - Локальная разработка, тесты, миграции

### 🚀 Быстрые ссылки

| Задача | Документация |
|--------|--------------|
| Запустить бота | [Usage Guide](docs/USAGE.md#telegram-bot) |
| Использовать API | [API Documentation](docs/API.md) |
| Настроить безопасность | [Security Guide](docs/SECURITY.md) |
| Изменить конфигурацию | [Configuration Guide](docs/CONFIGURATION.md) |
| Настроить мониторинг | [Monitoring Guide](docs/MONITORING.md) |
| Рассчитать стоимость | [Cost Analysis](docs/COST_ANALYSIS.md) |
| Проверить качество ответов | [RAG Quality](docs/RAG_QUALITY.md) |
| Решить проблему | [Troubleshooting Guide](docs/TROUBLESHOOTING.md) |
| Разработка | [Development Guide](docs/DEVELOPMENT.md) |

## Лицензия

MIT

---

**Telegram RAG Bot** - Python реализация RAG агента для Telegram с использованием OpenAI embeddings и GPT-4o-mini.

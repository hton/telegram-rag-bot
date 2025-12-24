# Telegram RAG Bot

Python реализация RAG (Retrieval-Augmented Generation) бота для Telegram с использованием OpenAI embeddings и GPT-4o-mini.

## Возможности

- 🤖 **RAG Pipeline**: Полный цикл поиска и генерации ответов на основе векторной базы данных
- 📱 **Telegram Bot**: Интерактивный бот с поддержкой обратной связи
- 🌐 **REST API**: HTTP API для интеграции с другими системами
- 💾 **Chat Memory**: Контекст диалога для более релевантных ответов
- 📊 **Analytics**: Метрики и статистика использования
- 🐳 **Docker**: Готовые образы для развертывания
- 📈 **Prometheus**: Мониторинг и метрики

## Архитектура

```
┌─────────────────┐     ┌──────────────────┐
│  Telegram Bot   │────▶│   QueryService   │
└─────────────────┘     └──────────────────┘
                                │
┌─────────────────┐             │
│   REST API      │────────────▶│
└─────────────────┘             │
                                ▼
                        ┌──────────────────┐
                        │   RAG Pipeline   │
                        └──────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────┐  ┌──────────────┐
        │   Embedder   │ │Retriever │  │  Generator   │
        │  (OpenAI)    │ │(pgvector)│  │  (OpenAI)    │
        └──────────────┘ └──────────┘  └──────────────┘
```

## RAG Pipeline

1. **Embedding** → OpenAI text-embedding-ada-002 (1536 dimensions)
2. **Vector Search** → PostgreSQL + pgvector (top 15 results)
3. **Reranking** → GPT-4o-mini (select top 5 sources)
4. **Context Retrieval** → Fetch full documents
5. **Answer Generation** → GPT-4o-mini with context

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

3. **Запустите сервисы**
```bash
cd docker
docker-compose up -d
```

### Обновление Docker контейнеров

Когда вы обновили код в репозитории (git pull, новый коммит и т.д.), вам нужно обновить запущенные контейнеры без потери данных:

**1. Обновление без остановки сервисов (zero-downtime):**
```bash
cd docker

# Пересобрать образы с новым кодом
docker-compose build --no-cache

# Перезапустить контейнеры с новыми образами
# (старые контейнеры остановятся автоматически)
docker-compose up -d
```

**2. Обновление с остановкой (если нужно):**
```bash
cd docker

# Остановить и удалить контейнеры (данные в volumes сохраняются!)
docker-compose down

# Пересобрать образы
docker-compose build --no-cache

# Запустить заново
docker-compose up -d
```

**3. Обновление конкретного сервиса:**
```bash
cd docker

# Пересобрать только API сервис
docker-compose build --no-cache api

# Перезапустить только API
docker-compose up -d api

# Или только бота
docker-compose build --no-cache bot
docker-compose up -d bot
```

**4. Проверка статуса после обновления:**
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

**5. Применение миграций БД после обновления:**
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
- ⚠️ При использовании `docker-compose down -v` будут **удалены все volumes** (включая БД!)
- ⚠️ Флаг `--no-cache` заставляет Docker пересобрать образ с нуля

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

## Конфигурация

### Основные параметры (.env)

```env
# OpenAI
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4o-mini

# PostgreSQL
DB_HOST=pgdb
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=your_password
VECTOR_TABLE=openai_221225

# RAG
CONTEXT_WINDOW=3          # Количество сообщений в истории
TOP_K_RESULTS=15         # Начальный поиск
RERANK_TOP_K=5           # После reranking

# Telegram
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=your_bot
TELEGRAM_ENABLE_FEEDBACK=true

# API
API_HOST=0.0.0.0
API_PORT=8080
API_ENABLE_FEEDBACK_BY_DEFAULT=false
```

## Структура проекта

```
telegram-rag-bot/
├── src/
│   ├── api/              # FastAPI приложение
│   ├── bot/              # Telegram bot
│   ├── core/             # Ядро (config, db, logging)
│   ├── models/           # SQLAlchemy модели
│   ├── rag/              # RAG pipeline
│   ├── services/         # Бизнес-логика
│   ├── schemas/          # Pydantic схемы
│   ├── cli.py            # CLI команды
│   └── main.py           # Entry point
├── alembic/              # Миграции БД
├── config/               # Конфигурация
├── docker/               # Docker файлы
├── tests/                # Тесты
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

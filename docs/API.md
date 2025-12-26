# API Documentation

REST API для Telegram RAG Bot предоставляет HTTP endpoints для интеграции с внешними системами.

## Содержание

- [Query API](#query-api)
  - [Отправка запроса](#отправка-запроса)
  - [Отправка фидбека](#отправка-фидбека)
- [Admin API](#admin-api)
  - [Статистика](#статистика)
  - [Популярные запросы](#популярные-запросы)
  - [Метрики производительности](#метрики-производительности)
- [Health Checks](#health-checks)
- [Prometheus Metrics](#prometheus-metrics)
- [Безопасность API](#безопасность-api)
- [Примеры интеграции](#примеры-интеграции)

---

## Query API

### Отправка запроса

**Endpoint:** `POST /api/v1/query`

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: YOUR_API_KEY` (если включена аутентификация)

**Request Body:**
```json
{
  "question": "Что такое ЕКП?",
  "enable_memory": true,
  "enable_feedback": false
}
```

**Параметры:**
- `question` (required) - Текст вопроса
- `enable_memory` (optional, default: true) - Использовать историю диалога
- `enable_feedback` (optional, default: false) - Включить возможность отправки фидбека

**Response:**
```json
{
  "query_id": "343162dc-a6b3-430c-acf6-72c8380a1429",
  "answer": "Полный ответ с инструкциями...",
  "sources": ["https://www.ispsystem.ru/docs/..."],
  "feedback_enabled": true,
  "feedback_url": "/api/v1/query/feedback/343162dc-a6b3-430c-acf6-72c8380a1429",
  "processing_time_ms": 10234.5,
  "timestamp": "2025-12-26T03:56:00Z"
}
```

**Пример curl:**
```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "question": "Что такое ЕКП?",
    "enable_memory": true,
    "enable_feedback": true
  }'
```

---

### Отправка фидбека

API поддерживает сбор обратной связи для улучшения качества ответов. Фидбек помогает идентифицировать "хорошие" ответы для будущего использования в Q&A кэше.

**Endpoint:** `POST /api/v1/query/feedback/{query_id}`

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: YOUR_API_KEY` (если включена аутентификация)

**Request Body:**
```json
{
  "rating": "good",
  "comment": "Очень подробный ответ с примерами команд"
}
```

**Параметры:**
- `rating` (required) - Оценка ответа:
  - `"good"` - хороший ответ (👍)
  - `"notbad"` - нормальный ответ (👌)
  - `"bad"` - плохой ответ (👎)
- `comment` (optional) - Текстовый комментарий

**Response:**
```json
{
  "status": "success",
  "message": "Feedback saved successfully",
  "query_id": "343162dc-a6b3-430c-acf6-72c8380a1429",
  "rating": "good"
}
```

#### Пошаговая инструкция

**Шаг 1: Получение query_id**

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

**Шаг 2: Отправка положительного фидбека**

```bash
curl -X POST http://localhost:8080/api/v1/query/feedback/343162dc-a6b3-430c-acf6-72c8380a1429 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "rating": "good"
  }'
```

**Шаг 3: Отправка негативного фидбека с комментарием**

```bash
curl -X POST http://localhost:8080/api/v1/query/feedback/343162dc-a6b3-430c-acf6-72c8380a1429 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "rating": "bad",
    "comment": "Ответ не содержит информацию о версии 2025.10"
  }'
```

#### Хранение фидбека

Фидбек сохраняется в двух таблицах PostgreSQL:
- `feedback` - детальная информация (query_id, rating, comment, created_at)
- `query_logs` - поле feedback для быстрой аналитики

Данные используются для:
- Идентификации качественных ответов для Q&A кэша
- Анализа проблемных запросов
- Улучшения RAG pipeline
- Мониторинга качества сервиса

---

## Admin API

### Статистика

**Endpoint:** `GET /api/v1/admin/stats`

**Query Parameters:**
- `days` (optional, default: 30) - Период статистики в днях

**Пример:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8080/api/v1/admin/stats?days=30"
```

**Response:**
```json
{
  "total_queries": 1523,
  "unique_users": 47,
  "avg_response_time_ms": 10234.5,
  "period_days": 30
}
```

---

### Статистика обратной связи

**Endpoint:** `GET /api/v1/admin/feedback/stats`

**Query Parameters:**
- `days` (optional, default: 30) - Период статистики в днях

**Пример:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8080/api/v1/admin/feedback/stats?days=30"
```

**Response:**
```json
{
  "total_feedback": 342,
  "ratings": {
    "good": 245,
    "notbad": 67,
    "bad": 30
  },
  "satisfaction_rate": 0.716,
  "period_days": 30
}
```

---

### Популярные запросы

**Endpoint:** `GET /api/v1/admin/queries/popular`

**Query Parameters:**
- `limit` (optional, default: 10) - Количество запросов

**Пример:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8080/api/v1/admin/queries/popular?limit=10"
```

**Response:**
```json
{
  "queries": [
    {
      "question": "Как установить платформу?",
      "count": 45,
      "avg_rating": "good"
    },
    {
      "question": "Что такое ЕКП?",
      "count": 38,
      "avg_rating": "good"
    }
  ]
}
```

---

### Метрики производительности

**Endpoint:** `GET /api/v1/admin/performance`

**Query Parameters:**
- `days` (optional, default: 7) - Период анализа в днях

**Пример:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8080/api/v1/admin/performance?days=7"
```

**Response:**
```json
{
  "avg_total_time_ms": 10234.5,
  "avg_embedding_time_ms": 1245.3,
  "avg_search_time_ms": 123.4,
  "avg_rerank_time_ms": 3456.7,
  "avg_generation_time_ms": 5409.1,
  "period_days": 7
}
```

---

## Health Checks

### Базовый health check

**Endpoint:** `GET /health`

Проверяет базовую доступность сервиса.

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-26T03:56:00Z"
}
```

---

### Readiness check

**Endpoint:** `GET /health/ready`

Проверяет готовность сервиса к обработке запросов (подключение к БД, OpenAI API).

```bash
curl http://localhost:8080/health/ready
```

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "openai": "ok"
  }
}
```

---

### Liveness check

**Endpoint:** `GET /health/live`

Проверяет что процесс работает.

```bash
curl http://localhost:8080/health/live
```

**Response:**
```json
{
  "status": "alive"
}
```

---

## Prometheus Metrics

**Endpoint:** `GET /metrics`

Экспортирует метрики в формате Prometheus.

```bash
curl http://localhost:8080/metrics
```

**Доступные метрики:**
- `rag_queries_total` - Всего запросов
- `rag_query_duration_seconds` - Время обработки запроса
- `rag_feedback_total` - Количество отзывов по рейтингу
- `openai_api_calls_total` - Вызовы OpenAI API (по типу: embedding, completion)
- `openai_tokens_used_total` - Использовано токенов (по типу)
- `vector_search_duration_seconds` - Время векторного поиска

Подробнее: [docs/MONITORING.md](MONITORING.md)

---

## Безопасность API

REST API защищен от несанкционированного доступа и злоупотреблений:

- 🔐 **API Key Authentication** - Аутентификация по ключу в заголовке `X-API-Key`
- 🌐 **IP Whitelist** - Ограничение доступа по IP адресам
- ⏱️ **Rate Limiting** - Защита от спама (10/мин, 100/час по умолчанию)

### Настройка в .env

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

### Использование с API Key

```bash
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"question": "Что такое n8n?"}'
```

### Генерация безопасного API ключа

```bash
# Linux/macOS
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

Подробнее: [docs/SECURITY.md](SECURITY.md)

---

## Примеры интеграции

### Python

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
answer = data["answer"]
sources = data["sources"]

print(f"Answer: {answer}")
print(f"Sources: {sources}")

# Отправить фидбек
feedback = requests.post(
    f"{API_URL}/query/feedback/{query_id}",
    headers=headers,
    json={
        "rating": "good",
        "comment": "Очень подробный ответ с примерами команд"
    }
)

print(f"Feedback status: {feedback.json()['status']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8080/api/v1';
const API_KEY = 'your-api-key';

const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
};

// Отправить вопрос
async function askQuestion() {
    const response = await axios.post(
        `${API_URL}/query`,
        {
            question: 'Как настроить multipath?',
            enable_feedback: true
        },
        { headers }
    );

    const { query_id, answer, sources } = response.data;
    console.log('Answer:', answer);
    console.log('Sources:', sources);

    // Отправить фидбек
    await axios.post(
        `${API_URL}/query/feedback/${query_id}`,
        {
            rating: 'good',
            comment: 'Очень подробный ответ'
        },
        { headers }
    );

    console.log('Feedback sent successfully');
}

askQuestion().catch(console.error);
```

### cURL

```bash
#!/bin/bash

API_URL="http://localhost:8080/api/v1"
API_KEY="your-api-key"

# Отправить вопрос и получить query_id
response=$(curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "question": "Как настроить multipath?",
    "enable_feedback": true
  }')

# Извлечь query_id из ответа
query_id=$(echo $response | jq -r '.query_id')
answer=$(echo $response | jq -r '.answer')

echo "Answer: $answer"
echo "Query ID: $query_id"

# Отправить фидбек
curl -X POST "${API_URL}/query/feedback/${query_id}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "rating": "good",
    "comment": "Отличный ответ!"
  }'
```

---

## Коды ошибок

### 400 Bad Request
Некорректный запрос (отсутствуют обязательные поля, неверный формат).

```json
{
  "detail": "Field 'question' is required"
}
```

### 401 Unauthorized
Отсутствует или неверный API ключ.

```json
{
  "detail": "Invalid API key"
}
```

### 403 Forbidden
IP адрес не в whitelist.

```json
{
  "detail": "Access denied: IP not whitelisted"
}
```

### 429 Too Many Requests
Превышен лимит запросов (rate limiting).

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds"
}
```

### 404 Not Found
Запрашиваемый ресурс не найден (например, query_id для фидбека).

```json
{
  "detail": "Query not found"
}
```

### 500 Internal Server Error
Внутренняя ошибка сервера.

```json
{
  "detail": "Internal server error"
}
```

---

## Настройки фидбека

### В .env файле

```env
# Фидбек по умолчанию выключен (нужно явно включать в запросе)
API_ENABLE_FEEDBACK_BY_DEFAULT=false
```

Если установить `API_ENABLE_FEEDBACK_BY_DEFAULT=true`, то `enable_feedback` будет включен для всех запросов по умолчанию.

---

## См. также

- [Использование](USAGE.md) - CLI команды и Telegram Bot
- [Безопасность](SECURITY.md) - Настройка безопасности API и Telegram
- [Мониторинг](MONITORING.md) - Prometheus метрики и логи
- [Конфигурация](CONFIGURATION.md) - Все параметры .env файла

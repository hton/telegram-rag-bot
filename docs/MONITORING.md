# Monitoring Guide

Руководство по мониторингу Telegram RAG Bot с помощью Prometheus метрик и логов.

## Содержание

- [Prometheus Metrics](#prometheus-metrics)
  - [Доступ к метрикам](#доступ-к-метрикам)
  - [Доступные метрики](#доступные-метрики)
  - [Персистентность метрик](#персистентность-метрик)
- [Логирование](#логирование)
  - [Структура логов](#структура-логов)
  - [Просмотр логов](#просмотр-логов)
  - [Фильтрация логов](#фильтрация-логов)
- [Интеграция с Grafana](#интеграция-с-grafana)
- [Alerting](#alerting)
- [Примеры запросов](#примеры-запросов)

---

## Prometheus Metrics

### Доступ к метрикам

Метрики доступны на endpoint `/metrics` API сервера.

**URL:** `http://localhost:8080/metrics`

**Пример:**
```bash
curl http://localhost:8080/metrics
```

**Включение/выключение:**
```env
METRICS_ENABLED=true
```

---

### Доступные метрики

#### rag_queries_total

**Тип:** Counter

**Описание:** Общее количество обработанных запросов

**Labels:**
- `source` - источник запроса (`telegram`, `api`)
- `status` - статус ответа (`success`, `error`)

**Пример:**
```
rag_queries_total{source="telegram",status="success"} 1523
rag_queries_total{source="api",status="success"} 342
rag_queries_total{source="telegram",status="error"} 12
```

**Использование:**
```promql
# Всего запросов
sum(rag_queries_total)

# Запросы из Telegram
sum(rag_queries_total{source="telegram"})

# Процент ошибок
sum(rate(rag_queries_total{status="error"}[5m]))
/
sum(rate(rag_queries_total[5m])) * 100
```

---

#### rag_query_duration_seconds

**Тип:** Histogram

**Описание:** Время обработки запроса (полный pipeline)

**Buckets:** 1, 5, 10, 15, 20, 30, 60 seconds

**Labels:**
- `source` - источник запроса (`telegram`, `api`)

**Метрики:**
- `rag_query_duration_seconds_bucket` - распределение по buckets
- `rag_query_duration_seconds_sum` - сумма всех времен
- `rag_query_duration_seconds_count` - количество запросов

**Использование:**
```promql
# Среднее время обработки (последние 5 минут)
rate(rag_query_duration_seconds_sum[5m])
/
rate(rag_query_duration_seconds_count[5m])

# 95-й перцентиль
histogram_quantile(0.95,
  rate(rag_query_duration_seconds_bucket[5m])
)

# 99-й перцентиль
histogram_quantile(0.99,
  rate(rag_query_duration_seconds_bucket[5m])
)
```

---

#### rag_feedback_total

**Тип:** Counter

**Описание:** Количество отзывов по рейтингу

**Labels:**
- `rating` - рейтинг (`good`, `notbad`, `bad`)
- `source` - источник (`telegram`, `api`)

**Пример:**
```
rag_feedback_total{rating="good",source="telegram"} 245
rag_feedback_total{rating="notbad",source="telegram"} 67
rag_feedback_total{rating="bad",source="telegram"} 30
```

**Использование:**
```promql
# Общее количество фидбека
sum(rag_feedback_total)

# Процент положительных оценок
sum(rag_feedback_total{rating="good"})
/
sum(rag_feedback_total) * 100

# Satisfaction rate (good / total)
sum(rate(rag_feedback_total{rating="good"}[1h]))
/
sum(rate(rag_feedback_total[1h]))
```

---

#### openai_api_calls_total

**Тип:** Counter

**Описание:** Количество вызовов OpenAI API

**Labels:**
- `call_type` - тип вызова (`embedding`, `completion`, `query_expansion`, `reranking`)
- `model` - модель (`text-embedding-ada-002`, `gpt-4o-mini`)
- `status` - статус (`success`, `error`)

**Пример:**
```
openai_api_calls_total{call_type="embedding",model="text-embedding-ada-002",status="success"} 1523
openai_api_calls_total{call_type="completion",model="gpt-4o-mini",status="success"} 1523
openai_api_calls_total{call_type="reranking",model="gpt-4o-mini",status="success"} 1523
```

**Использование:**
```promql
# Всего вызовов OpenAI
sum(openai_api_calls_total)

# Вызовы по типу
sum by (call_type) (rate(openai_api_calls_total[5m]))

# Процент ошибок OpenAI API
sum(rate(openai_api_calls_total{status="error"}[5m]))
/
sum(rate(openai_api_calls_total[5m])) * 100
```

---

#### openai_tokens_used_total

**Тип:** Counter

**Описание:** Количество использованных токенов OpenAI

**Labels:**
- `token_type` - тип токенов (`prompt`, `completion`)
- `call_type` - тип вызова (`embedding`, `completion`, `query_expansion`, `reranking`)

**Пример:**
```
openai_tokens_used_total{token_type="prompt",call_type="completion"} 234567
openai_tokens_used_total{token_type="completion",call_type="completion"} 123456
```

**Использование:**
```promql
# Всего токенов
sum(openai_tokens_used_total)

# Токены в час
sum(rate(openai_tokens_used_total[1h]) * 3600)

# Стоимость (gpt-4o-mini: $0.15/$0.60 per 1M tokens)
(
  sum(rate(openai_tokens_used_total{token_type="prompt"}[1h])) * 0.00000015
  +
  sum(rate(openai_tokens_used_total{token_type="completion"}[1h])) * 0.00000060
) * 3600
```

---

#### vector_search_duration_seconds

**Тип:** Histogram

**Описание:** Время векторного поиска в PostgreSQL

**Buckets:** 0.01, 0.05, 0.1, 0.5, 1.0, 2.0 seconds

**Использование:**
```promql
# Среднее время поиска
rate(vector_search_duration_seconds_sum[5m])
/
rate(vector_search_duration_seconds_count[5m])

# 95-й перцентиль
histogram_quantile(0.95,
  rate(vector_search_duration_seconds_bucket[5m])
)
```

---

### Персистентность метрик

Метрики **сохраняются в PostgreSQL** и восстанавливаются при перезапуске.

**Таблицы:**
- `query_logs` - логи запросов с метриками
- `feedback` - фидбек пользователей

**При старте сервиса:**
- Счетчики инициализируются из `query_logs` и `feedback`
- Метрики переживают рестарты контейнеров
- История доступна для анализа за любой период

**Проверка:**
```bash
# Посмотреть метрики до рестарта
curl http://localhost:8080/metrics | grep rag_queries_total

# Перезапустить API
docker-compose restart api

# Проверить что метрики сохранились
curl http://localhost:8080/metrics | grep rag_queries_total
```

---

## Логирование

### Структура логов

Логи сохраняются в директории `logs/`:

```
logs/
├── app_2025-12-26.log      # Все логи (INFO и выше)
├── error_2025-12-26.log    # Только ошибки (ERROR и выше)
├── app_2025-12-25.log      # Предыдущие дни
└── error_2025-12-25.log
```

**Формат лога:**
```
2025-12-26 12:34:56,789 | INFO | src.services.query_service:145 | Query processed in 10.23s
2025-12-26 12:35:02,123 | ERROR | src.rag.rag_service:89 | OpenAI API error: rate limit exceeded
```

**Поля:**
- Timestamp (с миллисекундами)
- Уровень (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Модуль и строка кода
- Сообщение

---

### Просмотр логов

#### Docker контейнеры (рекомендуется)

```bash
# Все логи бота (последние 100 строк)
docker logs rag_bot --tail 100

# Следить за логами в реальном времени
docker logs rag_bot -f

# Логи API
docker logs rag_api -f

# Логи всех сервисов
docker-compose logs -f
```

---

#### Файлы логов

```bash
# Последние записи из app лога
tail -f logs/app_$(date +%Y-%m-%d).log

# Только ошибки
tail -f logs/error_$(date +%Y-%m-%d).log

# Последние 50 строк
tail -50 logs/app_$(date +%Y-%m-%d).log

# Поиск по тексту
grep "OpenAI API error" logs/app_*.log
```

---

### Фильтрация логов

#### По уровню

```bash
# Только ERROR и CRITICAL
docker logs rag_api | grep -E "ERROR|CRITICAL"

# Только WARNING и выше
docker logs rag_api | grep -E "WARNING|ERROR|CRITICAL"
```

---

#### По компоненту

```bash
# RAG pipeline
docker logs rag_api | grep "rag_service"

# Query service
docker logs rag_api | grep "query_service"

# OpenAI API вызовы
docker logs rag_api | grep "openai"

# Database
docker logs rag_api | grep -E "db|postgres|pgvector"
```

---

#### По типу события

```bash
# Rate limiting
docker logs rag_bot | grep "Rate limit"

# Whitelist блокировки
docker logs rag_bot | grep "Whitelist"

# Feedback события
docker logs rag_bot | grep -i "feedback"

# Запросы пользователей
docker logs rag_bot | grep "Query:"
```

---

### Настройка уровня логирования

В `.env`:
```env
# DEBUG - очень подробно (для разработки)
LOG_LEVEL=DEBUG

# INFO - стандартный уровень (рекомендуется)
LOG_LEVEL=INFO

# WARNING - только предупреждения и ошибки
LOG_LEVEL=WARNING

# ERROR - только ошибки
LOG_LEVEL=ERROR
```

После изменения:
```bash
./reload-config.sh
```

---

## Интеграция с Grafana

### Добавление Prometheus data source

1. Откройте Grafana (http://localhost:3000)
2. Configuration → Data Sources → Add data source
3. Выберите Prometheus
4. URL: `http://prometheus:9090`
5. Save & Test

---

### Пример dashboard

**Создание dashboard:**

1. Create → Dashboard → Add new panel
2. Выберите Prometheus data source
3. Добавьте запросы (см. примеры ниже)

**Основные панели:**

#### Requests per minute
```promql
sum(rate(rag_queries_total[1m]))
```

#### Average response time
```promql
rate(rag_query_duration_seconds_sum[5m])
/
rate(rag_query_duration_seconds_count[5m])
```

#### Success rate
```promql
sum(rate(rag_queries_total{status="success"}[5m]))
/
sum(rate(rag_queries_total[5m])) * 100
```

#### Feedback satisfaction
```promql
sum(rag_feedback_total{rating="good"})
/
sum(rag_feedback_total) * 100
```

#### OpenAI tokens per hour
```promql
sum(rate(openai_tokens_used_total[1h]) * 3600)
```

---

## Alerting

### Prometheus Alert Rules

Создайте файл `prometheus/alerts.yml`:

```yaml
groups:
  - name: rag_bot_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(rag_queries_total{status="error"}[5m]))
          /
          sum(rate(rag_queries_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Slow response time
      - alert: SlowResponseTime
        expr: |
          rate(rag_query_duration_seconds_sum[5m])
          /
          rate(rag_query_duration_seconds_count[5m]) > 20
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time"
          description: "Average response time is {{ $value }}s"

      # Low satisfaction rate
      - alert: LowSatisfactionRate
        expr: |
          sum(rate(rag_feedback_total{rating="good"}[1h]))
          /
          sum(rate(rag_feedback_total[1h])) < 0.5
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "Low satisfaction rate"
          description: "Only {{ $value | humanizePercentage }} positive feedback"

      # OpenAI API errors
      - alert: OpenAIAPIErrors
        expr: |
          sum(rate(openai_api_calls_total{status="error"}[5m])) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "OpenAI API errors detected"
          description: "{{ $value }} errors per second"
```

---

## Примеры запросов

### Анализ производительности

```promql
# Среднее время по шагам RAG pipeline
# (требует добавления метрик для каждого шага)
avg by (step) (rate(rag_step_duration_seconds[5m]))

# Топ-10 самых медленных запросов (из логов)
topk(10, rag_query_duration_seconds)

# Процент запросов быстрее 10 секунд
sum(rate(rag_query_duration_seconds_bucket{le="10"}[5m]))
/
sum(rate(rag_query_duration_seconds_count[5m])) * 100
```

---

### Анализ использования

```promql
# Активные пользователи (за последний час)
count(count by (user_id) (
  rate(rag_queries_total[1h]) > 0
))

# Запросы по источнику
sum by (source) (rate(rag_queries_total[5m]))

# Пиковая нагрузка (запросов в минуту)
max_over_time(sum(rate(rag_queries_total[1m]))[1h:1m])
```

---

### Анализ качества

```promql
# Распределение фидбека
sum by (rating) (rag_feedback_total)

# Тренд satisfaction rate (за последние 24 часа)
sum(increase(rag_feedback_total{rating="good"}[1h]))
/
sum(increase(rag_feedback_total[1h]))

# Процент запросов с фидбеком
sum(rag_feedback_total) / sum(rag_queries_total) * 100
```

---

### Анализ стоимости

```promql
# Токены за последние 24 часа
sum(increase(openai_tokens_used_total[24h]))

# Стоимость за час (gpt-4o-mini)
(
  sum(rate(openai_tokens_used_total{token_type="prompt"}[1h])) * 0.00000015
  +
  sum(rate(openai_tokens_used_total{token_type="completion"}[1h])) * 0.00000060
) * 3600

# Средняя стоимость на запрос
sum(increase(openai_tokens_used_total[1h])) * 0.0000003
/
sum(increase(rag_queries_total[1h]))
```

---

## Troubleshooting

### Метрики не обновляются

**Проблема:** `/metrics` показывает старые значения

**Решение:**
1. Проверьте что `METRICS_ENABLED=true` в `.env`
2. Перезапустите API: `./reload-config.sh api`
3. Проверьте логи: `docker logs rag_api | grep -i metric`

---

### Логи не пишутся

**Проблема:** Файлы в `logs/` пустые или отсутствуют

**Решение:**
1. Проверьте права на директорию `logs/`:
   ```bash
   ls -la logs/
   chmod 777 logs/  # временно для диагностики
   ```
2. Проверьте что контейнер примонтировал volume:
   ```bash
   docker inspect rag_api | grep logs
   ```
3. Проверьте логи в stdout:
   ```bash
   docker logs rag_api
   ```

---

### Prometheus не scrape метрики

**Проблема:** Prometheus не собирает метрики с `/metrics`

**Решение:**
1. Проверьте доступность endpoint:
   ```bash
   curl http://localhost:8080/metrics
   ```
2. Проверьте конфигурацию Prometheus:
   ```yaml
   scrape_configs:
     - job_name: 'rag_api'
       static_configs:
         - targets: ['rag_api:8080']
   ```
3. Проверьте targets в Prometheus UI:
   http://localhost:9090/targets

---

## См. также

- [Configuration Guide](CONFIGURATION.md) - Настройка METRICS_ENABLED и LOG_LEVEL
- [API Documentation](API.md) - Endpoint /metrics
- [Troubleshooting](TROUBLESHOOTING.md) - Решение проблем с мониторингом

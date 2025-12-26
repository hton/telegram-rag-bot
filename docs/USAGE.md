# Usage Guide

Руководство по использованию Telegram RAG Bot через различные интерфейсы.

## Содержание

- [CLI Команды](#cli-команды)
  - [Управление ботом и API](#управление-ботом-и-api)
  - [Управление базой данных](#управление-базой-данных)
  - [Тестирование](#тестирование)
- [Telegram Bot](#telegram-bot)
  - [Начало работы](#начало-работы)
  - [Команды бота](#команды-бота)
  - [Использование в группах](#использование-в-группах)
  - [Обратная связь](#обратная-связь)
- [REST API](#rest-api)
- [Режимы работы](#режимы-работы)
  - [Polling режим](#polling-режим)
  - [Webhook режим](#webhook-режим)

---

## CLI Команды

### Управление ботом и API

#### Запуск Telegram бота

**Polling режим** (для разработки и небольших нагрузок):

```bash
python -m src.cli run-bot --polling
```

**Webhook режим** (для production):

```bash
python -m src.cli run-bot
```

> **Note:** Webhook режим требует настройки HTTPS. См. [docs/WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)

#### Запуск FastAPI сервера

```bash
python -m src.cli run-api --host 0.0.0.0 --port 8080
```

**Параметры:**
- `--host` - IP адрес для прослушивания (default: 0.0.0.0)
- `--port` - Порт (default: 8080)

**Примеры:**

```bash
# Запуск на localhost только
python -m src.cli run-api --host 127.0.0.1 --port 8080

# Запуск на всех интерфейсах
python -m src.cli run-api --host 0.0.0.0 --port 8000
```

---

### Управление базой данных

#### Инициализация базы данных

Создание начальной структуры БД:

```bash
python -m src.cli init
```

Эта команда:
- Создает необходимые таблицы (если не существуют)
- Создает расширение pgvector
- Создает индексы для векторного поиска

#### Создание миграции

Создание новой миграции Alembic:

```bash
python -m src.cli migrate -m "описание изменений"
```

**Примеры:**

```bash
python -m src.cli migrate -m "add feedback table"
python -m src.cli migrate -m "add index on query_logs"
```

#### Применение миграций

Применить все неприменённые миграции:

```bash
python -m src.cli migrate-up
```

Или используйте Alembic напрямую:

```bash
alembic upgrade head
```

#### Откат миграций

Откатить последнюю миграцию:

```bash
python -m src.cli migrate-down
```

Или используйте Alembic:

```bash
# Откатить 1 миграцию
alembic downgrade -1

# Откатить до конкретной ревизии
alembic downgrade <revision_id>

# Откатить все миграции
alembic downgrade base
```

---

### Тестирование

#### Тест RAG pipeline

Протестировать RAG pipeline с произвольным вопросом:

```bash
python -m src.cli test-rag "Как установить платформу?"
```

Эта команда:
- Выполняет полный RAG pipeline
- Показывает каждый шаг (embedding, search, reranking, generation)
- Выводит финальный ответ и источники
- Показывает время обработки

**Пример вывода:**

```
[INFO] Query: Как установить платформу?
[INFO] Step 0: Query Expansion... (1.2s)
[INFO] Expanded query: Как установить платформу ISPsystem в закрытом контуре...
[INFO] Step 1: Embedding... (1.5s)
[INFO] Step 2: Vector Search... (0.1s)
[INFO] Found 15 candidates
[INFO] Step 3: Reranking... (3.4s)
[INFO] Selected 5 sources
[INFO] Step 4: Fetch documents... (0.1s)
[INFO] Step 5: Aggregate context... (0.01s)
[INFO] Step 6: Generate answer... (7.2s)

Answer:
<краткий ответ>
...

Sources:
1. https://www.ispsystem.ru/docs/...
2. https://www.ispsystem.ru/docs/...

Total time: 10.5s
```

---

## Telegram Bot

### Начало работы

1. **Найдите бота в Telegram**

   Используйте username бота из переменной `BOT_USERNAME` в `.env`:

   ```
   @your_bot_username
   ```

2. **Запустите бота**

   Отправьте команду `/start`:

   ```
   /start
   ```

   Бот отправит приветственное сообщение и инструкции по использованию.

3. **Задайте вопрос**

   Упомяните бота в сообщении (обязательно!):

   ```
   @your_bot_username Как установить платформу в закрытом контуре?
   ```

   > **Важно:** Бот реагирует только на сообщения с упоминанием (@mention). Это сделано для корректной работы в группах.

---

### Команды бота

- `/start` - Начать работу с ботом, показать приветствие
- `/help` - Показать справку по использованию

---

### Использование в группах

#### Добавление бота в группу

1. Добавьте бота в группу через настройки группы
2. Дайте боту права на чтение сообщений (по умолчанию)
3. Упомяните бота в сообщении с вопросом

**Пример в группе:**

```
@your_bot_username Что такое ЕКП?
```

#### Настройка whitelist для групп

Для защиты от несанкционированного использования настройте whitelist групп в `.env`:

```env
WHITELIST_GROUPS_ENABLED=true
WHITELIST_GROUPS=-1001234567890,-1009876543210
```

**Как получить ID группы:**

1. Добавьте бота в группу
2. Напишите сообщение с упоминанием бота
3. Проверьте логи бота:

```bash
docker logs rag_bot | grep "Group ID"
```

Или используйте бот [@userinfobot](https://t.me/userinfobot):
1. Добавьте @userinfobot в группу
2. Бот пришлет ID группы

Подробнее: [docs/SECURITY.md](SECURITY.md)

---

### Обратная связь

После получения ответа бот показывает кнопки для оценки качества:

- 👍 **Хороший ответ** - Ответ полностью решил проблему
- 👌 **Нормальный ответ** - Ответ частично полезен
- 👎 **Плохой ответ** - Ответ не помог

**Отключение feedback:**

Чтобы отключить кнопки обратной связи, установите в `.env`:

```env
TELEGRAM_ENABLE_FEEDBACK=false
```

**Зачем нужен feedback?**

- Идентификация качественных ответов для Q&A кэша
- Анализ проблемных запросов
- Улучшение RAG pipeline
- Мониторинг качества сервиса

Данные фидбека хранятся в PostgreSQL и доступны через Admin API и Prometheus метрики.

---

## REST API

Для использования REST API см. подробную документацию:

**[docs/API.md](API.md)**

Краткий пример:

```bash
# Задать вопрос
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "question": "Что такое ЕКП?",
    "enable_memory": true,
    "enable_feedback": true
  }'

# Отправить фидбек
curl -X POST http://localhost:8080/api/v1/query/feedback/{query_id} \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"rating": "good"}'
```

---

## Режимы работы

### Polling режим

**Описание:**
- Бот периодически опрашивает Telegram API на наличие новых сообщений
- Подходит для разработки и небольших нагрузок
- Не требует HTTPS и публичного домена

**Преимущества:**
- ✅ Простая настройка
- ✅ Работает за NAT/firewall
- ✅ Не требует SSL сертификат

**Недостатки:**
- ❌ Задержка в ответах (polling interval)
- ❌ Дополнительная нагрузка на сервер
- ❌ Не рекомендуется для production

**Запуск:**

```bash
python -m src.cli run-bot --polling
```

Или в Docker:

```yaml
# docker-compose.yaml
services:
  bot:
    environment:
      - TELEGRAM_WEBHOOK_ENABLED=false
```

---

### Webhook режим

**Описание:**
- Telegram отправляет события на ваш HTTPS endpoint
- Рекомендуется для production
- Требует публичный домен и SSL сертификат

**Преимущества:**
- ✅ Мгновенные ответы (без задержки)
- ✅ Меньше нагрузки на сервер
- ✅ Лучшая масштабируемость

**Недостатки:**
- ❌ Требует публичный домен (например: bot.example.com)
- ❌ Требует SSL сертификат (Let's Encrypt)
- ❌ Требует настройку nginx

**Настройка:**

См. подробную инструкцию: **[docs/WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)**

Краткие шаги:

1. Получите SSL сертификат (Let's Encrypt)
2. Настройте nginx для проксирования на бота
3. Установите переменные в `.env`:

```env
TELEGRAM_WEBHOOK_ENABLED=true
TELEGRAM_WEBHOOK_URL=https://bot.example.com/webhook/telegram
TELEGRAM_WEBHOOK_PORT=8443
```

4. Запустите бота:

```bash
python -m src.cli run-bot
```

Бот автоматически зарегистрирует webhook в Telegram API.

---

## Примеры сценариев

### Сценарий 1: Локальная разработка

```bash
# 1. Запустите PostgreSQL
cd docker
docker-compose -f docker-compose.dev.yaml up -d

# 2. Примените миграции
cd ..
alembic upgrade head

# 3. Запустите бота в polling режиме
python -m src.cli run-bot --polling

# 4. В другом терминале - запустите API
python -m src.cli run-api
```

---

### Сценарий 2: Production развертывание

```bash
# 1. Клонируйте репозиторий
git clone <repo-url>
cd telegram-rag-bot

# 2. Настройте .env
cp config/.env.example .env
nano .env  # Отредактируйте конфигурацию

# 3. Запустите все сервисы через Docker
cd docker
docker-compose up -d

# 4. Проверьте логи
docker-compose logs -f

# 5. Проверьте health check
curl http://localhost:8080/health
```

---

### Сценарий 3: Обновление после git pull

```bash
# 1. Получите последние изменения
git pull origin main

# 2. Пересоберите и перезапустите контейнеры
cd docker
docker-compose up -d --build

# 3. Примените миграции (если есть)
docker-compose exec api python -m src.cli migrate-up

# 4. Проверьте статус
docker-compose ps
docker-compose logs -f
```

---

## Troubleshooting

### Бот не отвечает на сообщения

**Проблема:** Бот не реагирует на вопросы в Telegram.

**Решение:**

1. Проверьте что вы упомянули бота (@mention):
   ```
   @your_bot_username Вопрос?
   ```

2. Проверьте whitelist пользователей/групп в `.env`:
   ```env
   WHITELIST_USERS_ENABLED=false  # или добавьте свой ID
   WHITELIST_GROUPS_ENABLED=false  # или добавьте ID группы
   ```

3. Проверьте логи бота:
   ```bash
   docker logs rag_bot --tail 50
   ```

4. Проверьте что бот запущен:
   ```bash
   docker ps | grep rag_bot
   ```

---

### Rate limiting заблокировал запросы

**Проблема:** Получаете ошибку "Rate limit exceeded".

**Решение:**

1. Подождите окончания периода блокировки (1 минута или 1 час)

2. Увеличьте лимиты в `.env`:
   ```env
   RATE_LIMIT_REQUESTS_PER_MINUTE=10  # было 5
   RATE_LIMIT_REQUESTS_PER_HOUR=50    # было 20
   ```

3. Пересоздайте контейнер:
   ```bash
   ./reload-config.sh bot
   ```

---

### API возвращает 401 Unauthorized

**Проблема:** REST API отклоняет запросы с ошибкой 401.

**Решение:**

1. Проверьте что передаёте API ключ:
   ```bash
   curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8080/api/v1/query
   ```

2. Проверьте что ключ совпадает с `.env`:
   ```env
   API_KEY=your-secret-api-key-here
   ```

3. Или отключите аутентификацию:
   ```env
   API_REQUIRE_AUTH=false
   ```

---

## См. также

- [API Documentation](API.md) - Подробная документация REST API
- [Security](SECURITY.md) - Настройка безопасности
- [Configuration](CONFIGURATION.md) - Все параметры .env
- [Monitoring](MONITORING.md) - Логи и метрики
- [Troubleshooting](TROUBLESHOOTING.md) - Решение проблем

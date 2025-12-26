# Troubleshooting Guide

Решение распространённых проблем Telegram RAG Bot.

## Содержание

- [Установка и запуск](#установка-и-запуск)
- [База данных](#база-данных)
- [OpenAI API](#openai-api)
- [Telegram Bot](#telegram-bot)
- [REST API](#rest-api)
- [Docker](#docker)
- [RAG Pipeline](#rag-pipeline)
- [Производительность](#производительность)

---

## Установка и запуск

### "No module named 'src'"

**Проблема:** Python не находит модуль `src`

**Решение:**

1. Убедитесь что запускаете команды из корня проекта:
   ```bash
   cd telegram-rag-bot
   python -m src.cli run-bot
   ```

2. Добавьте корень проекта в PYTHONPATH:
   ```bash
   export PYTHONPATH=/path/to/telegram-rag-bot:$PYTHONPATH
   ```

3. Или установите проект в editable режиме:
   ```bash
   pip install -e .
   ```

---

### "ModuleNotFoundError: No module named 'X'"

**Проблема:** Отсутствует зависимость

**Решение:**

```bash
# Убедитесь что виртуальное окружение активировано
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Переустановите зависимости
pip install -r requirements.txt

# Или конкретный пакет
pip install <package-name>
```

---

### ".env file not found"

**Проблема:** Файл .env не найден

**Решение:**

1. Создайте .env из шаблона:
   ```bash
   cp config/.env.example .env
   ```

2. Отредактируйте .env:
   ```bash
   nano .env
   ```

3. Убедитесь что файл в корне проекта (не в `config/`):
   ```bash
   ls -la .env
   ```

---

## База данных

### "Database connection refused"

**Проблема:** Не удаётся подключиться к PostgreSQL

**Решение:**

1. Проверьте что PostgreSQL запущен:
   ```bash
   docker-compose -f docker/docker-compose.dev.yaml ps
   ```

2. Проверьте параметры подключения в .env:
   ```env
   DB_HOST=localhost  # или pgdb для Docker
   DB_PORT=5432
   DB_NAME=pgdb
   DB_USER=pguser
   DB_PASSWORD=your_password
   ```

3. Проверьте доступность порта:
   ```bash
   telnet localhost 5432
   # или
   nc -zv localhost 5432
   ```

4. Посмотрите логи PostgreSQL:
   ```bash
   docker logs pgdb
   ```

---

### "relation 'table_name' does not exist"

**Проблема:** Таблица не существует в БД

**Решение:**

1. Примените миграции:
   ```bash
   alembic upgrade head
   ```

2. Или инициализируйте БД:
   ```bash
   python -m src.cli init
   ```

3. Проверьте текущую ревизию:
   ```bash
   alembic current
   alembic history
   ```

---

### "extension 'vector' does not exist"

**Проблема:** Расширение pgvector не установлено

**Решение:**

1. Подключитесь к PostgreSQL:
   ```bash
   docker exec -it pgdb psql -U pguser -d pgdb
   ```

2. Создайте расширение:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   \dx  -- Проверить установленные расширения
   \q
   ```

3. Или используйте CLI:
   ```bash
   python -m src.cli init
   ```

---

### "FATAL: password authentication failed"

**Проблема:** Неверный пароль PostgreSQL

**Решение:**

1. Проверьте DB_PASSWORD в .env
2. Убедитесь что пароль совпадает с docker-compose.yaml:
   ```yaml
   environment:
     POSTGRES_PASSWORD: your_password
   ```

3. Пересоздайте контейнер с новым паролем:
   ```bash
   docker-compose down -v  # ВНИМАНИЕ: удалит данные!
   docker-compose up -d
   ```

---

## OpenAI API

### "OpenAI API key not found"

**Проблема:** API ключ отсутствует или неверный

**Решение:**

1. Убедитесь что `.env` содержит `OPENAI_API_KEY`:
   ```bash
   grep OPENAI_API_KEY .env
   ```

2. Проверьте что ключ начинается с `sk-proj-` или `sk-`:
   ```env
   OPENAI_API_KEY=sk-proj-...
   ```

3. Получите новый ключ на https://platform.openai.com/api-keys

4. Перезапустите сервис после изменения:
   ```bash
   ./reload-config.sh
   ```

---

### "Rate limit exceeded" (OpenAI)

**Проблема:** Превышен лимит запросов OpenAI API

**Решение:**

1. Проверьте лимиты на https://platform.openai.com/account/limits

2. Подождите несколько минут

3. Увеличьте tier на OpenAI (добавьте средства на баланс)

4. Уменьшите частоту запросов:
   ```env
   RATE_LIMIT_REQUESTS_PER_MINUTE=3  # было 5
   ```

---

### "Model 'gpt-4' not available"

**Проблема:** Модель недоступна для вашего аккаунта

**Решение:**

1. Используйте доступную модель:
   ```env
   LLM_MODEL=gpt-4o-mini  # вместо gpt-4
   ```

2. Проверьте доступные модели на https://platform.openai.com/docs/models

3. Запросите доступ к GPT-4 (если нужно):
   https://platform.openai.com/account/limits

---

### "Insufficient funds" (OpenAI)

**Проблема:** Недостаточно средств на балансе OpenAI

**Решение:**

1. Пополните баланс на https://platform.openai.com/account/billing

2. Проверьте текущее использование:
   https://platform.openai.com/usage

3. Настройте usage limits чтобы избежать перерасхода

---

## Telegram Bot

### Бот не отвечает на сообщения

**Проблема:** Бот не реагирует в Telegram

**Решение:**

1. Проверьте что вы упоминаете бота (@mention):
   ```
   @your_bot_username Как установить платформу?
   ```

2. Проверьте whitelist пользователей/групп:
   ```env
   WHITELIST_USERS_ENABLED=false  # или добавьте свой ID
   WHITELIST_GROUPS_ENABLED=false  # или добавьте ID группы
   ```

3. Проверьте логи бота:
   ```bash
   docker logs rag_bot --tail 100
   ```

4. Убедитесь что бот запущен:
   ```bash
   docker ps | grep rag_bot
   ```

5. Проверьте TELEGRAM_BOT_TOKEN:
   ```bash
   # Проверьте токен через Telegram API
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

---

### "Rate limit exceeded" (Telegram Bot)

**Проблема:** Превышен лимит запросов к боту

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

### "Access denied" в группе

**Проблема:** Бот не отвечает в Telegram группе

**Решение:**

1. Проверьте WHITELIST_GROUPS:
   ```env
   WHITELIST_GROUPS_ENABLED=false  # или добавьте ID группы
   ```

2. Узнайте ID группы:
   ```bash
   # Упомяните бота в группе, затем:
   docker logs rag_bot | grep "Group ID"
   ```

3. Добавьте ID в whitelist:
   ```env
   WHITELIST_GROUPS=-1001234567890,-1009876543210
   ```

4. Убедитесь что бот имеет права читать сообщения в группе

---

### Webhook не работает

**Проблема:** Webhook режим не получает события

**Решение:**

1. Проверьте что webhook зарегистрирован:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```

2. Убедитесь что URL доступен по HTTPS:
   ```bash
   curl https://bot.example.com/webhook/telegram
   ```

3. Проверьте SSL сертификат:
   ```bash
   openssl s_client -connect bot.example.com:443
   ```

4. Посмотрите логи nginx:
   ```bash
   tail -f /var/log/nginx/error.log
   ```

См. [docs/WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) для подробной настройки.

---

## REST API

### "401 Unauthorized"

**Проблема:** API отклоняет запросы

**Решение:**

1. Проверьте что передаёте API ключ:
   ```bash
   curl -H "X-API-Key: YOUR_KEY" http://localhost:8080/api/v1/query
   ```

2. Проверьте что ключ совпадает с `.env`:
   ```env
   API_KEY=your-secret-api-key-here
   ```

3. Или отключите аутентификацию:
   ```env
   API_REQUIRE_AUTH=false
   ```

4. Перезапустите API:
   ```bash
   ./reload-config.sh api
   ```

---

### "403 Access denied"

**Проблема:** IP адрес заблокирован

**Решение:**

1. Узнайте ваш IP:
   ```bash
   curl ifconfig.me
   ```

2. Добавьте в API_ALLOWED_IPS:
   ```env
   API_ALLOWED_IPS=127.0.0.1,<YOUR_IP>
   ```

3. Или разрешите все IP:
   ```env
   API_ALLOWED_IPS=
   ```

4. Перезапустите API:
   ```bash
   ./reload-config.sh api
   ```

---

### "429 Too Many Requests"

**Проблема:** Превышен rate limit API

**Решение:**

1. Подождите время указанное в `retry_after`

2. Увеличьте лимиты:
   ```env
   API_RATE_LIMIT_REQUESTS_PER_MINUTE=20  # было 10
   API_RATE_LIMIT_REQUESTS_PER_HOUR=200   # было 100
   ```

3. Перезапустите API:
   ```bash
   ./reload-config.sh api
   ```

---

### "Connection refused" к API

**Проблема:** Не удаётся подключиться к API

**Решение:**

1. Проверьте что API запущен:
   ```bash
   docker ps | grep rag_api
   ```

2. Проверьте порт:
   ```bash
   curl http://localhost:8080/health
   ```

3. Посмотрите логи API:
   ```bash
   docker logs rag_api
   ```

4. Проверьте API_HOST и API_PORT в .env:
   ```env
   API_HOST=0.0.0.0
   API_PORT=8080
   ```

---

## Docker

### "Cannot connect to Docker daemon"

**Проблема:** Docker не запущен или нет прав

**Решение:**

1. Запустите Docker:
   ```bash
   sudo systemctl start docker
   ```

2. Добавьте пользователя в группу docker:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker  # или перелогиньтесь
   ```

3. Проверьте статус Docker:
   ```bash
   docker info
   ```

---

### "Port is already allocated"

**Проблема:** Порт уже занят другим процессом

**Решение:**

1. Найдите процесс на порту:
   ```bash
   sudo lsof -i :8080
   # или
   sudo netstat -tlnp | grep 8080
   ```

2. Остановите процесс:
   ```bash
   sudo kill <PID>
   ```

3. Или измените порт в .env:
   ```env
   API_PORT=8081  # вместо 8080
   ```

---

### "No space left on device"

**Проблема:** Закончилось место на диске

**Решение:**

1. Очистите неиспользуемые образы и контейнеры:
   ```bash
   docker system prune -a
   ```

2. Удалите старые volumes:
   ```bash
   docker volume prune
   ```

3. Проверьте использование диска:
   ```bash
   docker system df
   df -h
   ```

---

### Контейнер постоянно перезапускается

**Проблема:** Контейнер в статусе "Restarting"

**Решение:**

1. Посмотрите логи контейнера:
   ```bash
   docker logs rag_bot --tail 100
   docker logs rag_api --tail 100
   ```

2. Проверьте переменные окружения:
   ```bash
   docker exec rag_bot env | grep -E "OPENAI|TELEGRAM"
   ```

3. Остановите автоперезапуск:
   ```bash
   docker update --restart=no <container_id>
   ```

4. Запустите вручную для диагностики:
   ```bash
   docker start rag_bot && docker logs -f rag_bot
   ```

---

## RAG Pipeline

### Низкое качество ответов

**Проблема:** RAG возвращает нерелевантные ответы

**Решение:**

1. Проверьте векторную базу:
   ```sql
   SELECT COUNT(*) FROM openai_231225;
   ```

2. Включите Query Expansion:
   ```env
   QUERY_EXPANSION_ENABLED=true
   ```

3. Увеличьте TOP_K_RESULTS:
   ```env
   TOP_K_RESULTS=20  # было 15
   ```

4. Проверьте HNSW index:
   ```sql
   -- Пересоздать индекс с лучшими параметрами
   DROP INDEX idx_embedding;
   CREATE INDEX idx_embedding ON openai_231225
   USING hnsw (embedding vector_cosine_ops)
   WITH (m = 32, ef_construction = 128);
   ```

5. Проверьте температуру:
   ```env
   TEMPERATURE=0.0  # детерминированные ответы
   ```

---

### "No relevant documents found"

**Проблема:** Векторный поиск не находит документы

**Решение:**

1. Проверьте что база не пустая:
   ```sql
   SELECT COUNT(*) FROM openai_231225;
   ```

2. Проверьте embedding модель:
   ```env
   EMBEDDING_MODEL=text-embedding-ada-002
   ```

3. Уменьшите порог similarity (если есть)

4. Проверьте индекс:
   ```sql
   \d openai_231225
   SELECT * FROM pg_indexes WHERE tablename = 'openai_231225';
   ```

---

### Медленные ответы

**Проблема:** RAG pipeline работает слишком медленно (>20s)

**Решение:**

1. Проверьте индекс на векторах:
   ```sql
   -- Должен быть HNSW индекс
   \d openai_231225
   ```

2. Уменьшите TOP_K_RESULTS:
   ```env
   TOP_K_RESULTS=10  # было 15
   ```

3. Отключите Query Expansion:
   ```env
   QUERY_EXPANSION_ENABLED=false
   ```

4. Проверьте логи на узкие места:
   ```bash
   docker logs rag_api | grep "duration"
   ```

5. Оптимизируйте PostgreSQL:
   ```sql
   VACUUM ANALYZE openai_231225;
   ```

---

## Производительность

### Высокая нагрузка на CPU

**Проблема:** Контейнеры потребляют много CPU

**Решение:**

1. Ограничьте ресурсы в docker-compose.yaml:
   ```yaml
   services:
     api:
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 2G
   ```

2. Уменьшите параллелизм:
   ```env
   # Уменьшите количество workers
   API_WORKERS=2  # если добавите эту опцию
   ```

3. Мониторьте производительность:
   ```bash
   docker stats
   ```

---

### Высокое потребление памяти

**Проблема:** Контейнеры используют много RAM

**Решение:**

1. Ограничьте memory в docker-compose.yaml

2. Уменьшите CONTEXT_WINDOW:
   ```env
   CONTEXT_WINDOW=3  # было 7
   ```

3. Проверьте утечки памяти:
   ```bash
   docker stats rag_api
   ```

4. Перезапустите контейнеры периодически (cron)

---

### Большие логи

**Проблема:** Логи занимают много места

**Решение:**

1. Настройте ротацию логов Docker:
   ```json
   // /etc/docker/daemon.json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

2. Очистите старые логи:
   ```bash
   truncate -s 0 /var/lib/docker/containers/*/*-json.log
   ```

3. Уменьшите LOG_LEVEL:
   ```env
   LOG_LEVEL=WARNING  # было INFO
   ```

---

## Получение помощи

Если проблема не решена:

1. Соберите диагностическую информацию:
   ```bash
   # Версии
   docker --version
   python --version

   # Логи
   docker logs rag_bot --tail 200 > bot_logs.txt
   docker logs rag_api --tail 200 > api_logs.txt

   # Конфигурация (удалите секреты!)
   cat .env | grep -v "KEY\|TOKEN\|PASSWORD" > config.txt

   # Docker состояние
   docker ps -a > docker_ps.txt
   docker-compose ps > compose_ps.txt
   ```

2. Проверьте документацию:
   - [Usage Guide](USAGE.md)
   - [Configuration Guide](CONFIGURATION.md)
   - [Security Guide](SECURITY.md)
   - [Monitoring Guide](MONITORING.md)
   - [Development Guide](DEVELOPMENT.md)

3. Создайте issue на GitHub с:
   - Описанием проблемы
   - Шагами для воспроизведения
   - Ожидаемым поведением
   - Логами (без секретов!)
   - Версиями ПО

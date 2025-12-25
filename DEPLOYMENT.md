# Руководство по развертыванию в продакшн

Подробная инструкция по развертыванию Telegram RAG Bot на VPS с настройкой webhook, SSL и домена.

---

## Содержание

1. [Подготовка сервера](#1-подготовка-сервера)
2. [Настройка домена и SSL](#2-настройка-домена-и-ssl)
3. [Настройка Telegram Webhook](#3-настройка-telegram-webhook)
4. [Запуск в продакшн](#4-запуск-в-продакшн)
5. [API: Подробное руководство](#5-api-подробное-руководство)

---

## 1. Подготовка сервера

### Требования

- VPS с Ubuntu 20.04+ / AlmaLinux 8+
- Минимум 2GB RAM, 2 CPU cores
- Белый IP-адрес
- Домен, направленный на IP сервера

### Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose -y

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Клонирование проекта

```bash
cd /opt
git clone https://github.com/hton/telegram-rag-bot.git
cd telegram-rag-bot
```

---

## 2. Настройка домена и SSL

### 2.1. Настройка DNS

Добавьте A-запись в DNS настройках вашего домена:

```
A    bot.yourdomain.com    →    123.45.67.89 (IP вашего сервера)
A    api.yourdomain.com    →    123.45.67.89
```

Дождитесь распространения DNS (обычно 5-30 минут):
```bash
dig bot.yourdomain.com
```

### 2.2. Установка Nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 2.3. Настройка Nginx для API и Webhook

Создайте конфигурацию Nginx:

```bash
sudo nano /etc/nginx/sites-available/telegram-rag-bot
```

Вставьте следующую конфигурацию:

```nginx
# API сервер
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL сертификаты (будут настроены через certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://localhost:8080;
        access_log off;
    }

    # Prometheus metrics
    location /metrics {
        proxy_pass http://localhost:8080;

        # Опционально: ограничить доступ
        # allow 127.0.0.1;
        # deny all;
    }
}

# Telegram Webhook
server {
    listen 80;
    server_name bot.yourdomain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name bot.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/bot.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Telegram webhook endpoint
    location /webhook/telegram {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Telegram требует быстрого ответа
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/telegram-rag-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.4. Получение SSL сертификатов (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификатов для API домена
sudo certbot --nginx -d api.yourdomain.com

# Получение сертификатов для Webhook домена
sudo certbot --nginx -d bot.yourdomain.com
```

При запросе введите:
- Email для уведомлений
- Согласие с условиями (Yes)
- Redirect HTTP to HTTPS (Yes)

Проверка автообновления сертификатов:
```bash
sudo certbot renew --dry-run
```

---

## 3. Настройка Telegram Webhook

### 3.1. Настройка переменных окружения

Отредактируйте `.env` файл:

```bash
cd /opt/telegram-rag-bot
cp config/.env.example .env
nano .env
```

Установите следующие параметры для webhook:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=your_bot_username
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://bot.yourdomain.com
WEBHOOK_PATH=/webhook/telegram
TELEGRAM_ENABLE_FEEDBACK=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080

# OpenAI (обязательно!)
OPENAI_API_KEY=sk-proj-...

# PostgreSQL
DB_HOST=pgdb
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=secure_password_here
VECTOR_TABLE=openai_221225

# RAG Configuration
CONTEXT_WINDOW=3
TOP_K_RESULTS=15
RERANK_TOP_K=5
QUERY_EXPANSION_ENABLED=true
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4o-mini

# Security Configuration - Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=5
RATE_LIMIT_REQUESTS_PER_HOUR=20

# Security Configuration - Whitelist (пусто = все разрешены)
WHITELIST_USERS_ENABLED=false
WHITELIST_USERS=
WHITELIST_GROUPS_ENABLED=false
WHITELIST_GROUPS=

# API Security
API_REQUIRE_AUTH=false
API_KEY=
API_ALLOWED_IPS=
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10
API_RATE_LIMIT_REQUESTS_PER_HOUR=100
```

### 3.2. Запуск с Docker Compose

Убедитесь, что `docker-compose.yaml` настроен правильно:

```bash
cd docker
cat docker-compose.yaml
```

Запустите сервисы:

```bash
docker-compose up -d
```

Проверьте статус:

```bash
docker-compose ps
docker-compose logs -f api
docker-compose logs -f bot
```

### 3.3. Установка Webhook в Telegram

**Способ 1: Через Telegram Bot API**

```bash
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
WEBHOOK_URL="https://bot.yourdomain.com/webhook/telegram"

curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"${WEBHOOK_URL}\",
    \"max_connections\": 40,
    \"allowed_updates\": [\"message\", \"callback_query\"]
  }"
```

**Способ 2: Автоматически при запуске бота**

Бот автоматически установит webhook при запуске, если `WEBHOOK_ENABLED=true` в `.env`.

**Проверка webhook:**

```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

Ожидаемый ответ:
```json
{
  "ok": true,
  "result": {
    "url": "https://bot.yourdomain.com/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40,
    "allowed_updates": ["message", "callback_query"]
  }
}
```

### 3.4. Удаление Webhook (переход на polling)

```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook"
```

---

## 4. Запуск в продакшн

### 4.1. Docker Compose (рекомендуется)

**docker/docker-compose.yaml** уже настроен для продакшн:

```yaml
version: '3.8'

services:
  pgdb:
    image: ankane/pgvector
    container_name: rag_pgdb
    restart: unless-stopped
    environment:
      - POSTGRES_USER=pguser
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=pgdb
    volumes:
      - db_storage:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pguser -d pgdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: rag_api
    restart: unless-stopped
    env_file:
      - ../.env
    ports:
      - "8080:8080"
    depends_on:
      pgdb:
        condition: service_healthy
    command: python -m src.cli run-api --host 0.0.0.0 --port 8080
    volumes:
      - ../logs:/app/logs

  bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: rag_bot
    restart: unless-stopped
    env_file:
      - ../.env
    depends_on:
      - pgdb
      - api
    command: python -m src.cli run-bot
    volumes:
      - ../logs:/app/logs

volumes:
  db_storage:
```

Запуск:

```bash
cd /opt/telegram-rag-bot/docker
docker-compose up -d
```

### 4.2. Системный сервис (альтернатива)

Если не используете Docker, создайте systemd сервисы:

**API сервис:**

```bash
sudo nano /etc/systemd/system/telegram-rag-api.service
```

```ini
[Unit]
Description=Telegram RAG Bot API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/telegram-rag-bot
Environment="PATH=/opt/telegram-rag-bot/venv/bin"
ExecStart=/opt/telegram-rag-bot/venv/bin/python -m src.cli run-api --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bot сервис:**

```bash
sudo nano /etc/systemd/system/telegram-rag-bot.service
```

```ini
[Unit]
Description=Telegram RAG Bot
After=network.target telegram-rag-api.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/telegram-rag-bot
Environment="PATH=/opt/telegram-rag-bot/venv/bin"
ExecStart=/opt/telegram-rag-bot/venv/bin/python -m src.cli run-bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервисов:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-rag-api
sudo systemctl enable telegram-rag-bot
sudo systemctl start telegram-rag-api
sudo systemctl start telegram-rag-bot

# Проверка статуса
sudo systemctl status telegram-rag-api
sudo systemctl status telegram-rag-bot

# Просмотр логов
sudo journalctl -u telegram-rag-api -f
sudo journalctl -u telegram-rag-bot -f
```

### 4.3. Мониторинг

**Проверка работоспособности:**

```bash
# Health check
curl https://api.yourdomain.com/health

# API endpoint
curl https://api.yourdomain.com/api/v1/health/ready

# Метрики Prometheus
curl https://api.yourdomain.com/metrics
```

**Настройка Prometheus (опционально):**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'telegram-rag-bot'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

---

## 5. API: Подробное руководство

### 5.1. Базовый запрос

```bash
curl -X POST https://api.yourdomain.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Как установить VMmanager?",
    "user_id": "user123",
    "enable_memory": true,
    "enable_feedback": true
  }'
```

**Ответ:**

```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "# Установка VMmanager\n\nДля установки VMmanager необходимо:\n1. Подготовить сервер...",
  "sources": [
    "https://www.ispsystem.ru/docs/vmmanager/installation",
    "https://www.ispsystem.ru/docs/vmmanager/setup"
  ],
  "processing_time_ms": 2547.3,
  "timestamp": "2024-12-24T10:30:00Z"
}
```

### 5.2. Запрос с отключенной памятью

```bash
curl -X POST https://api.yourdomain.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Как настроить SSL?",
    "enable_memory": false,
    "enable_feedback": false
  }'
```

### 5.3. Отправка feedback

```bash
# Получите query_id из предыдущего ответа
QUERY_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST "https://api.yourdomain.com/api/v1/query/feedback/${QUERY_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": "good"
  }'
```

Доступные rating значения:
- `"good"` - 👍 Хороший ответ
- `"notbad"` - 👌 Нормальный ответ
- `"bad"` - 👎 Плохой ответ

### 5.4. Admin API

**Статистика использования:**

```bash
curl https://api.yourdomain.com/api/v1/admin/stats?days=30
```

**Ответ:**

```json
{
  "total_queries": 1547,
  "unique_users": 234,
  "avg_processing_time_ms": 2340.5,
  "queries_by_source": {
    "telegram": 1200,
    "api": 347
  },
  "period_days": 30
}
```

**Статистика feedback:**

```bash
curl https://api.yourdomain.com/api/v1/admin/feedback/stats?days=7
```

**Популярные запросы:**

```bash
curl https://api.yourdomain.com/api/v1/admin/queries/popular?limit=10
```

**Метрики производительности:**

```bash
curl https://api.yourdomain.com/api/v1/admin/performance?days=7
```

### 5.5. Интеграция с вашим приложением

**Python пример:**

```python
import requests

API_URL = "https://api.yourdomain.com/api/v1"

def ask_question(question: str, user_id: str = None):
    response = requests.post(
        f"{API_URL}/query",
        json={
            "question": question,
            "user_id": user_id,
            "enable_memory": True,
            "enable_feedback": True
        }
    )
    return response.json()

def send_feedback(query_id: str, rating: str):
    response = requests.post(
        f"{API_URL}/query/feedback/{query_id}",
        json={"rating": rating}
    )
    return response.json()

# Использование
result = ask_question("Как установить VMmanager?", user_id="user123")
print(result["answer"])

# Отправить feedback
send_feedback(result["query_id"], "good")
```

**JavaScript пример:**

```javascript
const API_URL = 'https://api.yourdomain.com/api/v1';

async function askQuestion(question, userId = null) {
  const response = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: question,
      user_id: userId,
      enable_memory: true,
      enable_feedback: true
    })
  });
  return await response.json();
}

async function sendFeedback(queryId, rating) {
  const response = await fetch(`${API_URL}/query/feedback/${queryId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rating: rating })
  });
  return await response.json();
}

// Использование
const result = await askQuestion("Как установить VMmanager?", "user123");
console.log(result.answer);

// Отправить feedback
await sendFeedback(result.query_id, "good");
```

### 5.6. Аутентификация (опционально)

Если хотите защитить API ключом, добавьте в `.env`:

```env
API_REQUIRE_AUTH=true
API_KEY=your_secret_api_key_here
```

Использование с API ключом:

```bash
curl -X POST https://api.yourdomain.com/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secret_api_key_here" \
  -d '{
    "question": "Ваш вопрос"
  }'
```

---

## Troubleshooting

### Webhook не работает

**Проверка 1: Nginx доступен**
```bash
curl -I https://bot.yourdomain.com/webhook/telegram
# Должен вернуть 405 Method Not Allowed (это нормально)
```

**Проверка 2: SSL сертификат валидный**
```bash
openssl s_client -connect bot.yourdomain.com:443 -servername bot.yourdomain.com
```

**Проверка 3: Webhook установлен**
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

**Проверка 4: Логи бота**
```bash
docker-compose logs -f bot
# или
sudo journalctl -u telegram-rag-bot -f
```

### API возвращает 502 Bad Gateway

Проверьте что API сервер запущен:
```bash
docker-compose ps
curl http://localhost:8080/health
```

Проверьте логи Nginx:
```bash
sudo tail -f /var/log/nginx/error.log
```

### База данных недоступна

```bash
docker-compose logs pgdb
docker exec -it rag_pgdb psql -U pguser -d pgdb -c "SELECT 1;"
```

---

## Обновление приложения

```bash
cd /opt/telegram-rag-bot

# Скачать обновления
git pull

# Пересобрать и перезапустить
cd docker
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Применить миграции
docker-compose exec api python -m src.cli migrate-up
```

---

## Безопасность

### Рекомендации:

1. **Firewall:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

2. **Обновление системы:**
```bash
sudo apt update && sudo apt upgrade -y
```

3. **Мониторинг логов:**
```bash
# Следите за подозрительной активностью
sudo tail -f /var/log/nginx/access.log
docker-compose logs -f
```

4. **Бекапы базы данных:**
```bash
# Создание бекапа
docker exec rag_pgdb pg_dump -U pguser pgdb > backup_$(date +%Y%m%d).sql

# Восстановление
docker exec -i rag_pgdb psql -U pguser pgdb < backup_20241224.sql
```

---

## Готово! 🎉

Ваш Telegram RAG Bot теперь работает в продакшн с:
- ✅ SSL сертификатами
- ✅ Webhook для Telegram
- ✅ REST API на домене
- ✅ Мониторингом и логами
- ✅ Автоматическим перезапуском

**Полезные ссылки:**
- API: https://api.yourdomain.com/api/v1/query
- Metrics: https://api.yourdomain.com/metrics
- Health: https://api.yourdomain.com/health
- Bot: @your_bot_username в Telegram

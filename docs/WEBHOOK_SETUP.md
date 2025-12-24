# Настройка Webhook режима для Telegram бота

## 📋 Что вам понадобится

1. ✅ Публичный домен (например: `bot.example.com`)
2. ✅ Сервер с публичным IP
3. ✅ SSL сертификат (Let's Encrypt - бесплатно)

## 🚀 Пошаговая инструкция

### Шаг 1: Настройка домена

1. Добавьте A-запись для вашего домена:
   ```
   bot.example.com → IP_вашего_сервера
   ```

2. Проверьте что домен доступен:
   ```bash
   ping bot.example.com
   ```

### Шаг 2: Получение SSL сертификата

Используем Certbot (Let's Encrypt):

```bash
# Установка certbot
sudo apt update
sudo apt install certbot

# Получение сертификата (порт 80 должен быть свободен)
sudo certbot certonly --standalone -d bot.example.com

# Сертификаты будут в:
# /etc/letsencrypt/live/bot.example.com/fullchain.pem
# /etc/letsencrypt/live/bot.example.com/privkey.pem
```

### Шаг 3: Настройка конфигурации

1. **Отредактируйте `docker/nginx/nginx.conf`:**
   ```nginx
   # Замените your-domain.com на ваш реальный домен
   server_name bot.example.com;

   ssl_certificate /etc/letsencrypt/live/bot.example.com/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/bot.example.com/privkey.pem;
   ```

2. **Обновите `.env`:**
   ```env
   WEBHOOK_ENABLED=true
   WEBHOOK_URL=https://bot.example.com
   WEBHOOK_PATH=/webhook/telegram
   ```

### Шаг 4: Запуск с nginx

```bash
cd docker

# Остановить текущую конфигурацию (polling режим)
docker-compose down

# Запустить с nginx (webhook режим)
docker-compose -f docker-compose.webhook.yaml up -d
```

### Шаг 5: Настройка webhook в Telegram

Зарегистрируйте webhook URL в Telegram:

```bash
# Получите ваш TELEGRAM_BOT_TOKEN из .env
TOKEN="your_bot_token_here"
WEBHOOK_URL="https://bot.example.com/webhook/telegram"

# Установите webhook
curl -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${WEBHOOK_URL}\"}"

# Проверьте статус webhook
curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
```

Ответ должен быть:
```json
{
  "ok": true,
  "result": {
    "url": "https://bot.example.com/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### Шаг 6: Проверка работы

1. **Проверьте логи nginx:**
   ```bash
   docker logs rag_nginx
   ```

2. **Проверьте логи API:**
   ```bash
   docker logs rag_api
   ```

3. **Отправьте сообщение боту в Telegram**

4. **Проверьте что webhook работает:**
   ```bash
   # Должны быть POST запросы от Telegram
   docker exec rag_nginx tail -f /var/log/nginx/telegram_bot_access.log
   ```

## 🔄 Возврат к polling режиму

Если нужно вернуться к polling:

```bash
cd docker

# Остановить webhook режим
docker-compose -f docker-compose.webhook.yaml down

# Удалить webhook из Telegram
curl -X POST "https://api.telegram.org/bot${TOKEN}/deleteWebhook"

# Вернуть настройки в .env
# WEBHOOK_ENABLED=false

# Запустить polling режим
docker-compose up -d
```

## 📊 Мониторинг

### Проверка статуса сервисов:
```bash
docker-compose -f docker-compose.webhook.yaml ps
```

### Просмотр логов:
```bash
# Все сервисы
docker-compose -f docker-compose.webhook.yaml logs -f

# Только nginx
docker logs -f rag_nginx

# Только API
docker logs -f rag_api
```

### Health check:
```bash
curl https://bot.example.com/health
```

## ⚠️ Troubleshooting

### Проблема: Telegram не может подключиться к webhook

**Решение:**
1. Проверьте что порт 443 открыт:
   ```bash
   sudo ufw status
   sudo ufw allow 443/tcp
   ```

2. Проверьте SSL сертификат:
   ```bash
   curl -v https://bot.example.com/webhook/telegram
   ```

3. Проверьте что домен резолвится правильно:
   ```bash
   nslookup bot.example.com
   ```

### Проблема: SSL сертификат истёк

**Решение:**
```bash
# Обновление сертификата
sudo certbot renew

# Перезапуск nginx
docker restart rag_nginx
```

### Проблема: Бот не отвечает

**Решение:**
1. Проверьте логи API:
   ```bash
   docker logs rag_api --tail=50
   ```

2. Проверьте что webhook зарегистрирован:
   ```bash
   curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
   ```

3. Проверьте nginx конфигурацию:
   ```bash
   docker exec rag_nginx nginx -t
   ```

## 🎯 Преимущества webhook режима

После настройки вы получите:

- ⚡ Мгновенные ответы (без задержки polling)
- 💰 Меньше нагрузки на сервер
- 📈 Лучшая масштабируемость
- 🔒 Безопасность через HTTPS

## 📚 Дополнительные ресурсы

- [Telegram Bot API - Webhooks](https://core.telegram.org/bots/api#setwebhook)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Configuration](https://nginx.org/en/docs/)

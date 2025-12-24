#!/bin/bash
# Скрипт для быстрой перезагрузки конфигурации из .env без пересборки образов

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Перезагрузка конфигурации из .env${NC}"
echo ""

# Проверка что .env существует
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден в корне проекта${NC}"
    echo "Создайте .env файл перед перезагрузкой конфигурации"
    exit 1
fi

# Переход в директорию docker
cd docker

# Определяем какие сервисы перезапустить
SERVICES="${1:-}"

if [ -z "$SERVICES" ]; then
    echo -e "${YELLOW}Перезапуск всех сервисов...${NC}"
    docker-compose restart
    echo ""
    echo -e "${GREEN}✅ Все сервисы перезапущены${NC}"
else
    echo -e "${YELLOW}Перезапуск сервисов: $SERVICES${NC}"
    docker-compose restart $SERVICES
    echo ""
    echo -e "${GREEN}✅ Сервисы перезапущены: $SERVICES${NC}"
fi

echo ""
echo -e "${BLUE}📋 Статус сервисов:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}📝 Последние логи (проверьте что настройки применились):${NC}"
echo ""

if [ -z "$SERVICES" ] || echo "$SERVICES" | grep -q "bot"; then
    echo -e "${YELLOW}=== Telegram Bot ===${NC}"
    docker logs rag_bot --tail 10 2>&1 | grep -E "Whitelist|Rate limiting|enabled|Starting" || true
    echo ""
fi

if [ -z "$SERVICES" ] || echo "$SERVICES" | grep -q "api"; then
    echo -e "${YELLOW}=== API ===${NC}"
    docker logs rag_api --tail 10 2>&1 | grep -E "Whitelist|Rate limiting|API Key|enabled|Starting" || true
    echo ""
fi

echo -e "${GREEN}✨ Готово!${NC}"
echo ""
echo "Для просмотра полных логов:"
echo "  docker-compose logs -f bot"
echo "  docker-compose logs -f api"

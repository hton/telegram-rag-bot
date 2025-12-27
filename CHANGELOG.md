# Changelog

## [1.0.0] - 2025-12-27

### Added
#### RAG Pipeline
- 6-step processing pipeline (Query Expansion → Embedding → Vector Search → Reranking → Prompt → Generation)
- Query Expansion для аббревиатур (ЗК, ЕКП и т.д.)
- HNSW индексация для быстрого векторного поиска

#### Telegram Bot
- Интерактивный бот с кнопками обратной связи (👍👌👎)
- Команды /start и /help
- Rate limiting (запросов/мин, запросов/час)
- User/Group whitelist

#### REST API
- Endpoints: /api/v1/query, /api/v1/feedback, /api/v1/admin/*
- API Key authentication
- IP Whitelist protection
- Rate limiting

#### Chat Memory
- Контекст диалога (N сообщений)
- Оптимизация токенов (полные ответы в БД, краткие в GPT)
- Персистентность в PostgreSQL

#### Monitoring
- Prometheus метрики с персистентностью
- Отслеживание токенов OpenAI
- Статистика запросов

#### Infrastructure
- Docker развертывание (3 конфигурации: standard, webhook, dev)
- PostgreSQL + pgvector
- Webhook support для production

#### Documentation
- Модульная документация (9 файлов в docs/)
- README с архитектурой
- Deployment guide
- API reference

### Performance
- Оптимизированный RAG pipeline: 10-11s (было 23s, улучшение 55%)
- Эффективное управление токенами

### Security
- Комплексная защита: API Key + IP Whitelist + Rate Limiting
- User/Group whitelist для бота
- Безопасная конфигурация через .env

### Fixed
- Markdown парсинг в командах /start и /help
- Экранирование подчеркивания в BOT_USERNAME
- HTML форматирование сообщений

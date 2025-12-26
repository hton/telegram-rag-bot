# Development Guide

Руководство для разработчиков Telegram RAG Bot.

## Содержание

- [Локальная разработка](#локальная-разработка)
- [Запуск тестов](#запуск-тестов)
- [Форматирование кода](#форматирование-кода)
- [Управление базой данных](#управление-базой-данных)
  - [Создание миграции](#создание-миграции)
  - [Применение миграций](#применение-миграций)
  - [Откат миграций](#откат-миграций)
- [Структура проекта](#структура-проекта)
- [Coding Standards](#coding-standards)
- [Git Workflow](#git-workflow)
- [Debugging](#debugging)

---

## Локальная разработка

### Требования

- Python 3.11+
- PostgreSQL с расширением pgvector
- OpenAI API ключ
- Telegram Bot Token

---

### Настройка окружения

**1. Клонирование репозитория**

```bash
git clone <repo-url>
cd telegram-rag-bot
```

**2. Создание виртуального окружения**

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Установка зависимостей**

```bash
pip install -r requirements.txt
```

**4. Настройка .env**

```bash
cp config/.env.example .env
nano .env  # Отредактируйте параметры
```

**Минимальная конфигурация для разработки:**
```env
OPENAI_API_KEY=sk-proj-...
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=dev_bot

DB_HOST=localhost
DB_PORT=5432
DB_NAME=pgdb
DB_USER=pguser
DB_PASSWORD=dev_password

DEBUG=true
LOG_LEVEL=DEBUG
```

**5. Запуск PostgreSQL**

```bash
cd docker
docker-compose -f docker-compose.dev.yaml up -d
```

Этот файл запускает только PostgreSQL (без бота и API).

**6. Инициализация БД**

```bash
python -m src.cli init
```

**7. Применение миграций**

```bash
alembic upgrade head
```

---

### Запуск сервисов локально

**Telegram Bot (polling режим):**

```bash
python -m src.cli run-bot --polling
```

**FastAPI сервер:**

```bash
python -m src.cli run-api --host 127.0.0.1 --port 8080
```

**Оба сервиса (в разных терминалах):**

Terminal 1:
```bash
python -m src.cli run-bot --polling
```

Terminal 2:
```bash
python -m src.cli run-api
```

---

## Запуск тестов

### Pytest

**Запуск всех тестов:**

```bash
pytest tests/
```

**С покрытием кода:**

```bash
pytest tests/ --cov=src --cov-report=html
```

Отчет будет в `htmlcov/index.html`

**Запуск конкретного теста:**

```bash
pytest tests/test_query_service.py
pytest tests/test_query_service.py::test_process_query
```

**С выводом print:**

```bash
pytest tests/ -s
```

**Verbose режим:**

```bash
pytest tests/ -v
```

---

### Структура тестов

```
tests/
├── conftest.py              # Фикстуры pytest
├── test_query_service.py    # Тесты query service
├── test_rag_service.py      # Тесты RAG pipeline
├── test_chat_memory.py      # Тесты chat memory
├── test_api/                # API тесты
│   ├── test_query_endpoint.py
│   └── test_feedback_endpoint.py
└── test_bot/                # Bot тесты
    ├── test_handlers.py
    └── test_middleware.py
```

---

### Написание тестов

**Пример теста:**

```python
import pytest
from src.services.query_service import QueryService

@pytest.fixture
async def query_service():
    """Create QueryService instance for testing"""
    service = QueryService()
    yield service
    # cleanup if needed

async def test_process_query(query_service):
    """Test query processing"""
    result = await query_service.process_query(
        question="Что такое ЕКП?",
        session_id="test_session",
        enable_memory=False
    )

    assert result is not None
    assert "answer" in result
    assert "sources" in result
    assert len(result["sources"]) > 0
```

---

## Форматирование кода

### Black

**Форматирование всего кода:**

```bash
black src/
```

**Проверка без изменений:**

```bash
black src/ --check
```

**Только конкретная директория:**

```bash
black src/services/
```

**Настройки:** см. `pyproject.toml`

---

### Ruff

**Проверка всего кода:**

```bash
ruff check src/
```

**Автоисправление:**

```bash
ruff check src/ --fix
```

**Настройки:** см. `pyproject.toml` или `.ruff.toml`

---

### Pre-commit hook (рекомендуется)

**Установка:**

```bash
pip install pre-commit
pre-commit install
```

**Файл `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
```

**Запуск вручную:**

```bash
pre-commit run --all-files
```

Теперь black и ruff будут запускаться автоматически перед каждым коммитом.

---

## Управление базой данных

### Создание миграции

**Через CLI:**

```bash
python -m src.cli migrate -m "описание изменений"
```

**Через Alembic напрямую:**

```bash
alembic revision -m "описание изменений"
```

**Автогенерация миграции (из моделей SQLAlchemy):**

```bash
alembic revision --autogenerate -m "описание изменений"
```

**Файл миграции создается в:** `alembic/versions/`

**Пример:**

```bash
python -m src.cli migrate -m "add user_stats table"
```

Создаст файл: `alembic/versions/abc123_add_user_stats_table.py`

---

### Применение миграций

**Применить все неприменённые миграции:**

```bash
python -m src.cli migrate-up
```

**Или через Alembic:**

```bash
alembic upgrade head
```

**Применить до конкретной ревизии:**

```bash
alembic upgrade abc123
```

**Применить следующую миграцию:**

```bash
alembic upgrade +1
```

---

### Откат миграций

**Откатить последнюю миграцию:**

```bash
python -m src.cli migrate-down
```

**Или через Alembic:**

```bash
alembic downgrade -1
```

**Откатить до конкретной ревизии:**

```bash
alembic downgrade abc123
```

**Откатить все миграции:**

```bash
alembic downgrade base
```

---

### История миграций

**Посмотреть текущую ревизию:**

```bash
alembic current
```

**Посмотреть историю:**

```bash
alembic history
```

**Verbose режим:**

```bash
alembic history --verbose
```

---

### Проверка миграций

**Проверить pending миграции:**

```bash
alembic show head
alembic current
```

Если отличаются - есть неприменённые миграции.

**Dry-run (без применения):**

```bash
alembic upgrade head --sql
```

Показывает SQL который будет выполнен, но не применяет изменения.

---

## Структура проекта

```
telegram-rag-bot/
├── src/
│   ├── api/              # FastAPI приложение
│   │   ├── middleware/   # API middleware (auth, rate limit, IP whitelist)
│   │   ├── routes/       # API endpoints
│   │   │   ├── query.py
│   │   │   ├── admin.py
│   │   │   └── health.py
│   │   └── schemas/      # Pydantic schemas для API
│   │
│   ├── bot/              # Telegram bot
│   │   ├── handlers/     # Message handlers
│   │   │   ├── message_handler.py
│   │   │   └── feedback_handler.py
│   │   └── middleware/   # Bot middleware (security, logging)
│   │       ├── security.py
│   │       └── rate_limit.py
│   │
│   ├── core/             # Ядро приложения
│   │   ├── config.py     # Конфигурация (Settings)
│   │   ├── db.py         # Database connection pool
│   │   └── logging.py    # Логирование
│   │
│   ├── models/           # SQLAlchemy модели
│   │   ├── query_log.py
│   │   ├── chat_history.py
│   │   └── feedback.py
│   │
│   ├── rag/              # RAG pipeline
│   │   ├── prompts.py           # Промпты для RAG (v2.0 - русские)
│   │   ├── query_expander.py    # Query expansion
│   │   ├── embedding_service.py # Embeddings
│   │   ├── vector_search.py     # Vector search
│   │   ├── reranker.py          # LLM reranking
│   │   └── rag_service.py       # Main RAG orchestration
│   │
│   ├── services/         # Бизнес-логика
│   │   ├── query_service.py     # Query orchestration
│   │   ├── chat_memory.py       # Chat history
│   │   └── feedback_service.py  # Feedback handling
│   │
│   ├── schemas/          # Pydantic схемы (shared)
│   │   ├── query.py
│   │   └── feedback.py
│   │
│   ├── cli.py            # CLI команды
│   └── main.py           # Entry point
│
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   ├── env.py
│   └── script.py.mako
│
├── config/               # Конфигурационные файлы
│   └── .env.example      # Шаблон .env
│
├── docker/               # Docker конфигурация
│   ├── docker-compose.yaml      # Production
│   ├── docker-compose.dev.yaml  # Development (только DB)
│   ├── Dockerfile.bot
│   └── Dockerfile.api
│
├── docs/                 # Документация
│   ├── API.md
│   ├── USAGE.md
│   ├── SECURITY.md
│   ├── CONFIGURATION.md
│   ├── MONITORING.md
│   ├── DEVELOPMENT.md
│   ├── TROUBLESHOOTING.md
│   └── WEBHOOK_SETUP.md
│
├── tests/                # Тесты
│   ├── conftest.py
│   ├── test_query_service.py
│   └── ...
│
├── logs/                 # Логи (создаётся автоматически)
│   ├── app_YYYY-MM-DD.log
│   └── error_YYYY-MM-DD.log
│
├── .env                  # Environment variables (не в Git)
├── .gitignore
├── requirements.txt      # Python зависимости
├── pyproject.toml        # Black, Ruff конфигурация
├── alembic.ini           # Alembic конфигурация
└── README.md
```

---

## Coding Standards

### Python Style

- **PEP 8** - базовый стиль
- **Black** - форматирование (line length 100)
- **Ruff** - линтинг
- **Type hints** - везде где возможно

**Пример:**

```python
from typing import Optional, Dict, Any

async def process_query(
    question: str,
    session_id: str,
    enable_memory: bool = True
) -> Dict[str, Any]:
    """Process user query through RAG pipeline.

    Args:
        question: User question text
        session_id: Unique session identifier
        enable_memory: Whether to use chat history

    Returns:
        Dict with answer, sources, and metadata

    Raises:
        ValueError: If question is empty
        OpenAIError: If OpenAI API fails
    """
    if not question.strip():
        raise ValueError("Question cannot be empty")

    # Implementation...
    return {
        "answer": "...",
        "sources": [...],
        "query_id": "..."
    }
```

---

### Docstrings

**Google style:**

```python
def function_name(param1: str, param2: int) -> bool:
    """Short one-line summary.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

---

### Именование

- **Переменные и функции:** `snake_case`
- **Классы:** `PascalCase`
- **Константы:** `UPPER_SNAKE_CASE`
- **Private методы:** `_leading_underscore`

---

### Async/await

- Используйте `async`/`await` для IO операций
- Не блокируйте event loop sync кодом
- Используйте `asyncio.gather()` для параллельных операций

**Пример:**

```python
async def fetch_multiple_documents(doc_ids: List[str]) -> List[Document]:
    """Fetch multiple documents in parallel"""
    tasks = [fetch_document(doc_id) for doc_id in doc_ids]
    return await asyncio.gather(*tasks)
```

---

## Git Workflow

### Branching Strategy

- `main` - production branch (защищён)
- `develop` - development branch
- `feature/*` - новые функции
- `fix/*` - исправления багов
- `hotfix/*` - срочные исправления для production

**Пример:**

```bash
# Новая функция
git checkout -b feature/add-query-cache

# Исправление бага
git checkout -b fix/telegram-rate-limiting

# Hotfix
git checkout -b hotfix/openai-api-timeout
```

---

### Commit Messages

**Формат:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - новая функция
- `fix:` - исправление бага
- `docs:` - документация
- `style:` - форматирование
- `refactor:` - рефакторинг
- `test:` - тесты
- `chore:` - обслуживание (dependencies, build, etc.)

**Примеры:**

```bash
git commit -m "feat(rag): add query expansion for abbreviations"
git commit -m "fix(bot): rate limiting not applied in groups"
git commit -m "docs(api): add feedback endpoint documentation"
```

---

### Pull Requests

**Перед созданием PR:**

1. Обновите ветку от main:
   ```bash
   git checkout main
   git pull
   git checkout feature/my-feature
   git rebase main
   ```

2. Запустите тесты:
   ```bash
   pytest tests/
   ```

3. Проверьте форматирование:
   ```bash
   black src/ --check
   ruff check src/
   ```

4. Обновите документацию если нужно

**PR Description Template:**

```markdown
## Описание
Краткое описание изменений

## Изменения
- [ ] Добавлена функция X
- [ ] Исправлен баг Y
- [ ] Обновлена документация

## Testing
Как протестировать изменения

## Screenshots (если UI)

## Checklist
- [ ] Тесты пройдены
- [ ] Код отформатирован (black, ruff)
- [ ] Документация обновлена
- [ ] .env.example обновлён (если новые переменные)
```

---

## Debugging

### VS Code

**launch.json:**

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Bot",
            "type": "python",
            "request": "launch",
            "module": "src.cli",
            "args": ["run-bot", "--polling"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        },
        {
            "name": "Run API",
            "type": "python",
            "request": "launch",
            "module": "src.cli",
            "args": ["run-api"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/.env"
        },
        {
            "name": "Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

---

### PyCharm

1. Run → Edit Configurations
2. Add New Configuration → Python
3. Script path: `src/cli.py`
4. Parameters: `run-bot --polling` (или `run-api`)
5. Working directory: корень проекта
6. Environment variables: load from `.env`

---

### Logging для debugging

```python
import logging

logger = logging.getLogger(__name__)

# В коде
logger.debug(f"Processing query: {question}")
logger.info(f"Found {len(results)} candidates")
logger.warning(f"Slow response time: {duration}s")
logger.error(f"OpenAI API error: {error}")
```

**Установите LOG_LEVEL=DEBUG** в `.env` для подробных логов.

---

### IPython REPL

Для быстрого тестирования:

```bash
pip install ipython

# Запустить REPL с импортами
ipython
```

```python
In [1]: from src.services.query_service import QueryService
In [2]: import asyncio
In [3]: service = QueryService()
In [4]: result = asyncio.run(service.process_query("Test query", "test_session"))
In [5]: print(result)
```

---

## См. также

- [Usage Guide](USAGE.md) - CLI команды
- [Configuration Guide](CONFIGURATION.md) - Параметры .env
- [Troubleshooting](TROUBLESHOOTING.md) - Решение проблем

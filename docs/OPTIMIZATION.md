# Оптимизация производительности RAG системы

## 📊 Текущая производительность

**Среднее время ответа:** 5-16 секунд

### Breakdown по этапам (типичный запрос):
```
Step 1: Embedding          ~1-2 сек  (OpenAI API)
Step 2: Vector Search      ~0.1 сек  (pgvector - быстрый)
Step 3: Reranking          ~3-4 сек  (GPT-4o-mini API)
Step 4: Fetch Documents    ~0.1 сек  (PostgreSQL)
Step 5: Aggregate Context  ~0.01 сек (Python - быстрый)
Step 6: Generate Answer    ~7-10 сек (GPT-4o-mini API)
────────────────────────────────────
TOTAL                      ~12-17 сек
```

**Узкие места:**
1. 🐌 **Answer Generation** (7-10 сек) - 60-70% времени
2. 🐌 **Reranking** (3-4 сек) - 20-30% времени
3. ⚡ Остальное (0.2 сек) - 1-2% времени

## 🚀 Стратегии оптимизации

### 1. Streaming ответов (Quick Win!) ⭐

**Что:** Отправлять ответ пользователю по мере генерации, а не ждать полного ответа

**Текущее:**
```
Пользователь ждет 12 сек → Получает полный ответ
```

**С streaming:**
```
Пользователь ждет 3-4 сек → Начинает видеть ответ → Полный ответ за 12 сек
```

**Эффект:** Perceived latency уменьшается с 12 сек до 3-4 сек! 🎉

**Реализация:**
```python
# src/rag/generator.py
async def generate_answer_stream(self, question, context):
    response = await self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=self.temperature,
        max_tokens=self.max_tokens,
        stream=True,  # ← Включить streaming
    )

    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

**Приоритет:** 🔥 ВЫСОКИЙ (легко реализовать, большой эффект)

---

### 2. Параллельное выполнение (Medium Win)

**Что:** Выполнять независимые операции параллельно

**Возможности:**
```python
# Можно выполнять параллельно:
await asyncio.gather(
    self.embedder.embed_query(question),  # API call
    self.memory_service.get_history(user_id)  # DB query
)

# Нельзя параллелить (зависимые шаги):
embedding → vector_search → reranking → answer
```

**Эффект:** Экономия 0.5-1 сек

**Приоритет:** 🟡 СРЕДНИЙ (требует рефакторинга)

---

### 3. Оптимизация промптов (Quick Win)

**Что:** Уменьшить количество токенов в промптах

**Текущие промпты:** 3000-8000 токенов
**Цель:** 1500-4000 токенов

**Как:**
- Сократить system prompt
- Убрать дубликаты в документах
- Использовать только релевантные части текста

**Пример:**
```python
# Было:
context = full_document  # 5000 токенов

# Стало:
context = relevant_chunks[:3]  # 2000 токенов
```

**Эффект:** Уменьшение времени на 20-30%

**Приоритет:** 🟡 СРЕДНИЙ (требует тестирования качества)

---

### 4. Кэширование эмбеддингов (Medium Win)

**Что:** Сохранять эмбеддинги популярных вопросов

**Реализация:**
```python
# Redis или in-memory cache
cached_embedding = await cache.get(f"emb:{question}")
if cached_embedding:
    return cached_embedding

embedding = await openai.embed(question)
await cache.set(f"emb:{question}", embedding, ttl=3600)
```

**Эффект:** Экономия 1-2 сек для повторяющихся вопросов

**Приоритет:** 🟡 СРЕДНИЙ (нужен Redis)

---

### 5. Уменьшение reranking (Big Win) ⭐

**Что:** Сделать reranking опциональным или упростить

**Варианты:**

**A) Использовать более быструю модель для reranking:**
```python
# Было: gpt-4o-mini (~3 сек)
# Стало: gpt-3.5-turbo (~1 сек)
```

**B) Убрать reranking совсем:**
```python
# Использовать только vector search результаты
# Взять top 5 документов напрямую
top_docs = retrieved_docs[:5]
```

**C) Reranking только для длинных списков:**
```python
if len(retrieved_docs) > 10:
    # Делать reranking
else:
    # Взять все документы
```

**Эффект:** Экономия 3-4 сек (но может снизить качество)

**Приоритет:** 🔴 НИЗКИЙ (влияет на качество ответов)

---

### 6. Индексы в PostgreSQL (Small Win)

**Что:** Оптимизировать SQL запросы

**Текущие индексы:**
```sql
CREATE INDEX ON openai_221225 USING ivfflat (embedding vector_cosine_ops);
```

**Добавить:**
```sql
-- Индекс для fetch_full_documents
CREATE INDEX idx_source_path ON openai_221225(source_path);
CREATE INDEX idx_source_path_position ON openai_221225(source_path, position);
```

**Эффект:** Экономия 50-100ms

**Приоритет:** 🟢 ВЫСОКИЙ (легко, без рисков)

---

### 7. Connection Pooling (Small Win)

**Что:** Переиспользовать соединения с БД и API

**Реализация:**
```python
# PostgreSQL - уже есть через SQLAlchemy
# OpenAI - добавить client pooling
```

**Эффект:** Экономия 100-200ms

**Приоритет:** 🟢 ВЫСОКИЙ (легко)

---

### 8. Batch processing для multiple queries

**Что:** Обрабатывать несколько запросов параллельно

**Реализация:**
```python
# Если приходит несколько вопросов от разных пользователей
results = await asyncio.gather(*[
    pipeline.run(q) for q in questions
])
```

**Эффект:** Лучшее использование ресурсов

**Приоритет:** 🟡 СРЕДНИЙ (для высокой нагрузки)

---

## 🎯 Рекомендуемый план оптимизации

### Phase 1: Quick Wins (1-2 дня)
1. ✅ **Streaming ответов** - уменьшит perceived latency на 70%
2. ✅ **Индексы в БД** - экономия 50-100ms
3. ✅ **Connection pooling** - экономия 100-200ms

**Итого:** Perceived latency: 12 сек → 3-4 сек

### Phase 2: Medium Wins (3-5 дней)
1. ⚡ **Оптимизация промптов** - экономия 20-30%
2. ⚡ **Параллельное выполнение** - экономия 0.5-1 сек
3. ⚡ **Кэширование** (опционально) - для популярных запросов

**Итого:** Total latency: 12 сек → 7-8 сек

### Phase 3: Advanced (опционально)
1. 🔬 **A/B тестирование** - reranking vs без reranking
2. 🔬 **Модели** - эксперименты с разными моделями
3. 🔬 **Мониторинг** - автоматическая оптимизация

---

## 📈 Метрики для отслеживания

```python
# Добавить в код
metrics = {
    "total_time": 12000,  # ms
    "embedding_time": 1500,
    "vector_search_time": 100,
    "reranking_time": 3500,
    "fetch_docs_time": 100,
    "aggregate_time": 10,
    "generation_time": 8000,
    "tokens_used": 5000,
    "cache_hit": False,
}
```

---

## 🧪 Тестирование

### Benchmark скрипт:
```python
import time
import asyncio

async def benchmark():
    questions = [
        "Что такое ЕКП?",
        "Как установить платформу?",
        # ... еще 10 вопросов
    ]

    times = []
    for q in questions:
        start = time.time()
        await pipeline.run(q)
        times.append(time.time() - start)

    print(f"Average: {sum(times)/len(times):.2f}s")
    print(f"P50: {sorted(times)[len(times)//2]:.2f}s")
    print(f"P95: {sorted(times)[int(len(times)*0.95)]:.2f}s")
```

---

## 🎁 Бонус: Webhook режим

После перехода на webhook (см. docs/WEBHOOK_SETUP.md):
- Убирается задержка polling (1-2 сек)
- Мгновенное получение сообщений

**Итого с webhook + streaming:**
```
Пользователь пишет → 0.1 сек → Начинает видеть ответ
```

Вместо текущих 12 секунд ожидания! 🚀

---

## 📞 Поддержка

Вопросы по оптимизации? Создайте issue в репозитории.

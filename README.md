# ZAgent

[![CI](https://github.com/faddey/zagent/actions/workflows/ci.yml/badge.svg)](https://github.com/faddey/zagent/actions/workflows/ci.yml)

ZAgent — это CLI (launcher) для запуска AI-агентов в изолированном Docker-контейнере (runtime).

Идея проекта: launcher устанавливается на хост-машину разработчика и управляет запусками, а runtime живет
внутри контейнера и безопасно выполняет поставленную агенту задачу в подготовленном workspace.

## Пакеты

```text
packages/runtime/    # код, который запускается внутри контейнера
packages/launcher/   # будущий host-side CLI/API для управления запусками
contracts/           # файловые контракты и JSON Schema
docker/              # Dockerfile и compose для локального запуска
examples/            # примеры workspace и .zagent окружения
docs/                # архитектурные заметки и формат конфигов
```

`runtime` и `launcher` не импортируют друг друга. Они общаются через файлы:

- `.zagent/run.yaml` - описание конкретного запуска;
- `.zagent/` - окружение агента, prompts, rules и skills;
- `.zagent/artifacts/<run_id>/` - результаты запуска;
- `contracts/` - стабильные схемы этих файлов.

## Как работает runtime

Runtime делает один запуск:

1. читает `.zagent/run.yaml`;
2. сканирует фиксированную структуру `.zagent/`;
3. собирает prompt, rules и skills;
4. создает AG2 assistant и runtime tool executor;
5. дает агенту tools, например `shell` и `files`;
6. пишет трассировку и результат в `.zagent/artifacts/<run_id>/`.

Основные файлы результата:

```text
chat.jsonl      # сообщения
events.jsonl    # lifecycle события
tools.jsonl     # вызовы tools
state.json      # текущее/финальное состояние
result.json     # итоговый результат
summary.md      # краткое резюме
```

## Использование CLI (Launcher)

Основной поток работы с агентами идет через host-side CLI `zagent`:

- `zagent init` — инициализирует настройки (`.zagent/`) в рабочей директории.
- `zagent run` — собирает задачу и запускает runtime-контейнер для ее выполнения.

Детальная архитектура CLI описана в `docs/launcher.md`.

### Локальный запуск примеров (Docker Compose)

Пока CLI находится в активной разработке, примеры можно запускать напрямую через `docker compose`:

Runtime image содержит `npx` и `uvx`, чтобы позже можно было запускать local
stdio MCP servers без пересборки образа для каждого MCP.

Workspace:

```text
examples/workspaces/fastapi-app/
```

Внутри него лежат:

```text
.zagent/
```

Запуск:

```bash
export OLLAMA_API_KEY=ollama
docker compose build runtime
docker compose run --rm runtime
```

Проверка wiring без обращения к LLM:

```bash
docker compose run --rm runtime run --run-spec /workspace/.zagent/run.yaml --dry-run
```

## Playwright MCP пример

Для проверки браузерного MCP есть отдельный образ с Chromium:

```bash
docker compose -f compose.playwright.yml build runtime-playwright
docker compose -f compose.playwright.yml run --rm runtime-playwright
```

Workspace примера:

```text
examples/workspaces/playwright-research/
```

В этом примере MCP server запускается внутри runtime-контейнера через
`playwright-mcp`, а результаты агент складывает в `/workspace/research`.

## Python Bugfix пример

Отдельный workspace с небольшим сломанным Python-проектом и вложенным git repo:

```bash
docker compose -f compose.bugfix.yml build runtime-bugfix
docker compose -f compose.bugfix.yml run --rm runtime-bugfix
```

Задача сформулирована коротко: агент должен сам найти причину по коду и тестам,
исправить баг, запустить проверки и сделать commit внутри workspace.

## Разработка

```bash
uv sync --all-packages --group dev
uv run --all-packages ruff check .
uv run --all-packages mypy packages/runtime/src packages/launcher/src
uv run --package zagent-launcher pytest packages/launcher -q
uv run --package zagent-runtime pytest packages/runtime -q
```

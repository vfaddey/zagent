# ZAgent

ZAgent - платформа для запуска coding-агента в контейнере.

Идея проекта: launcher живет на хосте и управляет запуском, а runtime живет
внутри контейнера и выполняет одну задачу агента в подготовленном workspace.

## Пакеты

```text
packages/runtime/    # код, который запускается внутри контейнера
packages/launcher/   # будущий host-side CLI/API для управления запусками
contracts/           # файловые контракты и JSON Schema
docker/              # Dockerfile и compose для локального запуска
examples/            # примеры workspace и .agent окружения
```

`runtime` и `launcher` не импортируют друг друга. Они общаются через файлы:

- `run.yaml` - описание конкретного запуска;
- `.agent/config.yaml` - окружение агента, prompts, rules, skills;
- `.agent/artifacts/<run_id>/` - результаты запуска;
- `contracts/` - стабильные схемы этих файлов.

## Как работает runtime

Runtime делает один запуск:

1. читает `run.yaml`;
2. читает `.agent/config.yaml`;
3. собирает prompt, rules и skills;
4. создает AG2 assistant и runtime tool executor;
5. дает агенту tools, например `shell` и `files`;
6. пишет трассировку и результат в `.agent/artifacts/<run_id>/`.

Основные файлы результата:

```text
chat.jsonl      # сообщения
events.jsonl    # lifecycle события
tools.jsonl     # вызовы tools
state.json      # текущее/финальное состояние
result.json     # итоговый результат
summary.md      # краткое резюме
```

## Локальный запуск

Сейчас пример запускается через root `compose.yml`.

Workspace:

```text
examples/workspaces/fastapi-app/
```

Внутри него лежат:

```text
run.yaml
.agent/
```

Запуск:

```bash
export OLLAMA_API_KEY=ollama
docker compose build runtime
docker compose run --rm runtime
```

Проверка wiring без обращения к LLM:

```bash
docker compose run --rm runtime run --run-spec /workspace/run.yaml --dry-run
```

## Разработка

```bash
uv sync --all-packages --group dev
uv run --all-packages ruff check .
uv run --all-packages mypy packages/runtime/src packages/launcher/src
uv run --all-packages pytest -q
```

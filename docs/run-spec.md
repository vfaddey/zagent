# `.zagent/run.yaml`

`.zagent/run.yaml` описывает один запуск агента.

Этот файл отвечает на вопросы:

- какую задачу выполнить;
- какой LLM endpoint использовать;
- где находится workspace;
- где лежит `.zagent`, если используется нестандартный путь;
- какие tools доступны;
- какие политики безопасности применяются.

## Пример

```yaml
run_id: fastapi-app-smoke
mode: task

task:
  title: Создать FastAPI приложение для учета книг
  prompt_file: prompts/task.md
  workspace: /workspace

model:
  provider: openai_compatible
  model: gemma4:e4b
  api_base: http://10.139.2.217:11435/v1
  api_key_env: OLLAMA_API_KEY
  timeout_seconds: 300

runtime:
  image: zagent-runtime:local
  workdir: /workspace
  max_turns: 50

tools:
  builtin:
    - shell
    - files
  custom: []
  enable_mcp: false

policy:
  network: restricted
  git_push: false
  writable_paths:
    - /workspace
```

## Поля

`run_id` - уникальный id запуска. Используется для директории artifacts:

```text
.zagent/artifacts/<run_id>/
```

`mode` - тип задачи. Сейчас поддерживаются:

```text
fix
research
task
```

`task.title` - короткое название задачи.

Задача должна задавать ровно один источник prompt:

- `task.prompt` - inline-текст задачи;
- `task.prompt_file` - путь к файлу с prompt, относительно директории
  `run.yaml`.

`task.workspace` - путь к workspace внутри runtime-контейнера. В compose это
обычно `/workspace`.

`model.provider` - тип model provider. Сейчас используется
`openai_compatible`.

`model.model` - имя модели, которое будет передано provider-у.

`model.api_base` - base URL OpenAI-compatible endpoint.

`model.api_key_env` - имя переменной окружения, из которой runtime возьмет
token. Сам token не пишется в `run.yaml`.

`model.timeout_seconds` - timeout одного обращения к LLM. Полезно для локальных
OpenAI-compatible моделей, которые отвечают медленнее облачных API.

`agent_env.path` - опциональный путь к окружению агента внутри контейнера.
Если секция не указана, runtime использует `.zagent` относительно
`task.workspace`. Для стандартного `task.workspace: /workspace` это дает
`/workspace/.zagent`.

`runtime.image` - runtime Docker image. Нужен launcher-у.

`runtime.workdir` - рабочая директория внутри контейнера.

`runtime.max_turns` - верхняя граница количества ходов AG2 conversation.
Это страховка, а не основной сигнал завершения.

Финальный marker не настраивается в `run.yaml`. Runtime всегда использует
`ZAGENT_DONE` как стабильный внешний сигнал завершения.

`tools.builtin` - список встроенных tools. Сейчас в примере используются:

```text
shell
files
```

Также доступны AG2-native tools:

```text
apply_patch
web_search
image_generation
```

Они передаются в AG2 как `built_in_tools` и требуют provider, совместимый с
OpenAI Responses API. Например, `web_search` не является локальным runtime tool
и может не работать с Ollama-compatible endpoint, если endpoint не поддерживает
Responses API built-in tools.

Важно: `web_search` не регистрируется как executor function. Если модель
пытается вызвать function tool с именем `web_search` или `google_search`, значит
provider не использовал Responses built-in tool, и задаче нужен fallback через
обычные runtime/MCP tools.

`tools.custom` - список будущих custom tools.

`tools.enable_mcp` - включает или выключает MCP capabilities.

`policy.network` - политика сети. Сейчас поле фиксирует намерение политики,
полное enforcement поведение будет расширяться.

`policy.git_push` - разрешен ли `git push`. По умолчанию должен быть `false`.

`policy.writable_paths` - список путей, куда tools могут писать.

## Что важно

`.zagent/run.yaml` должен описывать только конкретный запуск. Общие правила,
skills и prompts лежат в фиксированной структуре `.zagent/`.

Для Docker Compose текущий рабочий пример лежит здесь:

```text
examples/workspaces/fastapi-app/.zagent/run.yaml
```

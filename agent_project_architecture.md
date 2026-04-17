# Архитектура проекта агента-помощника

## 1. Назначение проекта

Проект представляет собой универсальный Python runtime для контейнерного агента-помощника, который запускается внутри подготовленного окружения и выполняет прикладные задачи.

Основные сценарии применения:

- исправление некритичных багов по задачам с доски;
- проведение ресерча;
- выполнение пользовательских задач внутри заранее подготовленного контейнера.

Ключевая идея: **агент запускается как основной Python-процесс внутри контейнера**, а все необходимые параметры передаются ему извне через конфиг запуска и смонтированное окружение.

---

## 2. Базовые требования

Система должна поддерживать:

- подключение MCP;
- передачу окружения перед запуском;
- передачу файлов, правил, промптов, скиллов и секретов;
- настройку LLM provider, модели и токенов;
- подключение built-in tools;
- расширение кастомными tool-плагинами;
- возможность в будущем запускать два контейнера с общей папкой;
- получение полного чата и трассировки выполнения во время работы и после завершения;
- возможность обновлять образ runtime без переработки внутренней архитектуры.

---

## 3. Архитектурный принцип

Проект делится на две логические части:

1. **Launcher** — внешний управляющий слой в виде CLI и/или Python-библиотеки, который принимает входной запрос и запускает runtime-контейнер.
2. **Runtime** — внутренний Python-процесс внутри контейнера, который читает конфиг, загружает окружение и выполняет задачу через агента.

Launcher не является обязательным отдельным Docker-контейнером. Базовая модель — host-side CLI/library, которая управляет контейнерным runtime через Docker или совместимый container runtime. Отдельная упаковка launcher в контейнер может появиться позже как deployment-вариант, но не должна быть частью core-архитектуры.

То есть модель работы следующая:

- снаружи формируется `run.yaml`;
- внутрь контейнера монтируется папка `.zagent`;
- внутренний runtime считывает `run.yaml` и `.zagent`;
- после этого собирается runtime context, инициализируются LLM/tools/MCP и запускается агент.

---

## 4. Модель конфигурации

Используются два независимых источника конфигурации.

### 4.1. Внешний конфиг запуска `run.yaml`

Этот файл отвечает на вопрос: **как запустить агента именно в этом запуске**.

Он содержит:

- идентификатор запуска;
- режим выполнения;
- описание задачи;
- модель и провайдера;
- runtime image;
- опциональный путь к `.zagent`, если он отличается от `.zagent` внутри workspace;
- включение built-in/custom/MCP tools;
- policy ограничения.

Пример:

```yaml
run_id: fix-123
mode: fix

task:
  title: Fix pagination bug
  prompt: >
    Tester found a non-critical pagination issue in the reports page.
  workspace: /workspace

model:
  provider: openai_compatible
  model: gpt-5
  api_base: https://example.com/v1
  api_key_env: OPENAI_API_KEY
  timeout_seconds: 120

runtime:
  image: ghcr.io/your-org/agent-runtime:0.1.0
  workdir: /workspace
  max_turns: 20

tools:
  builtin:
    - shell
    - files
    - apply_patch
  custom: []
  enable_mcp: true

policy:
  network: restricted
  git_push: false
  writable_paths:
    - /workspace
```

### 4.2. Внутреннее окружение `.zagent`

Эта папка отвечает на вопрос: **как агент должен работать внутри уже подготовленного окружения**.

В ней лежат:

- prompts;
- rules;
- skills;
- MCP-конфиги;
- дополнительные входные файлы;
- secrets;
- runtime artifacts.

Пример структуры:

```text
.zagent/
├── run.yaml
├── prompts/
│   ├── system.md
│   ├── developer.md
│   └── task.md
├── rules/
│   ├── global.md
│   └── repo.md
├── skills/
│   ├── python.md
│   ├── gitlab.md
│   └── research.md
├── mcp/
│   └── servers.yaml
├── files/
│   ├── input.txt
│   └── extra_context.md
├── secrets/
│   └── env.list
└── artifacts/
```

Окружение определяется жесткой структурой: `prompts/system.md`,
`prompts/developer.md`, `rules/**/*.md`, `skills/**/*.md`, `mcp/servers.yaml`
и `files/**`.

### 4.3. Разделение ответственности

Граница должна быть жесткой:

- `run.yaml` — orchestration-конфиг запуска;
- `.zagent` — runtime-окружение агента.

Это позволяет:

- переиспользовать `.zagent` между разными запусками;
- автоматически генерировать `run.yaml` извне;
- не смешивать внешний orchestration и внутреннюю логику выполнения.

---

## 5. Целевая структура репозитория

Рекомендуемая структура строится как monorepo/workspace с двумя независимыми Python-дистрибутивами:

- `zagent-runtime` — код, который устанавливается в runtime-образ и выполняет задачу внутри контейнера;
- `zagent-launcher` — host-side CLI/Python-библиотека, которая запускает runtime-контейнер и читает артефакты;
- `contracts/` — файловые контракты и схемы, но не импортируемый Python-пакет.

Runtime и launcher не должны импортировать код друг друга. Их связь идет через стабильные внешние контракты: `.zagent/run.yaml`, структура `.zagent`, runtime artifacts и JSON Schema.

```text
agent-project/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── Makefile
├── contracts/
│   ├── run-spec.schema.json
│   ├── artifacts.schema.json
│   └── README.md
├── docker/
│   ├── runtime.Dockerfile
│   └── compose.dev.yaml
├── examples/
│   └── workspaces/
│       └── example/
│           ├── .zagent/
│           │   ├── run.yaml
│           │   ├── prompts/
│           │   ├── rules/
│           │   ├── skills/
│           │   ├── mcp/
│           │   └── files/
│           └── ...
├── packages/
│   ├── runtime/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── src/
│   │   │   └── zagent_runtime/
│   │   │       ├── __init__.py
│   │   │       ├── domain/
│   │   │       ├── application/
│   │   │       ├── infrastructure/
│   │   │       └── presentation/
│   │   └── tests/
│   │       ├── unit/
│   │       └── integration/
│   └── launcher/
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/
│       │   └── zagent_launcher/
│       │       ├── __init__.py
│       │       ├── domain/
│       │       ├── application/
│       │       ├── infrastructure/
│       │       └── presentation/
│       └── tests/
│           ├── unit/
│           └── integration/
├── tests/
│   └── e2e/
└── docs/
    ├── architecture.md
    ├── project-structure.md
    ├── run-spec.md
    ├── agent-env.md
    └── plugin-system.md
```

Корневой `pyproject.toml` управляет workspace, общими dev-зависимостями и инструментами качества. Пакеты `packages/runtime/pyproject.toml` и `packages/launcher/pyproject.toml` управляют только своими runtime-зависимостями.

Runtime-зависимости не должны попадать в launcher. Например, AG2, MCP-клиенты и LLM SDK нужны `zagent-runtime`, но не нужны `zagent-launcher`. Launcher должен зависеть только от библиотек для CLI, Docker/container runtime orchestration, чтения YAML/JSON и валидации внешних контрактов.

---

## 6. Слои приложения

### 6.1. `domain/`

Содержит только сущности предметной области.

Примеры моделей:

- `RunSpec`
- `AgentEnv`
- `TaskSpec`
- `ModelSpec`
- `PolicySpec`
- `ToolSpec`
- `RunResult`
- `RunState`
- `ChatMessage`
- `RunEvent`
- `ToolEvent`

В этом слое не должно быть:

- AG2;
- Docker;
- YAML parser;
- MCP client logic;
- файловой инфраструктуры.

### 6.2. `application/`

Содержит сценарии работы системы.

Примеры use case модулей:

- `bootstrap.py`
- `load_run_spec.py`
- `load_agent_env.py`
- `build_runtime_context.py`
- `register_tools.py`
- `register_mcp.py`
- `create_agent.py`
- `execute_task.py`
- `collect_result.py`

### 6.3. `infrastructure/`

Содержит конкретные реализации.

Подсистемы:

- `config/` — чтение и валидация YAML;
- `runtime/` — работа с workspace, env vars, artifacts;
- `llm/` — factory провайдеров и адаптеры моделей;
- `ag2/` — интеграция AG2;
- `mcp/` — registry и client factory;
- `tools/` — built-in и custom tools;
- `prompts/` — загрузка и сборка prompt fragments;
- `security/` — secrets, policies, approvals;
- `observability/` — запись чата, событий и состояния.

### 6.4. `launcher/`

Внешний слой управления запуском.

В MVP launcher является Python CLI и библиотекой, которые выполняются вне runtime-контейнера. Его ответственность — подготовить запуск, вызвать container runtime и читать артефакты выполнения. Он не должен требовать собственного Docker-образа.

Его задача:

- принять внешний запрос;
- определить mount points;
- собрать docker command;
- передать переменные окружения;
- стартовать runtime-контейнер;
- при необходимости читать live state и артефакты.

### 6.5. `presentation/`

Точка входа внутрь контейнера.

Содержит:

- `main.py`;
- CLI parsing;
- старт bootstrap-процесса;
- возврат exit code.

---

## 7. Внутренняя структура пакетов

```text
packages/
├── runtime/
│   └── src/
│       └── zagent_runtime/
│           ├── __init__.py
│           ├── domain/
│           │   ├── __init__.py
│           │   ├── run/
│           │   │   ├── spec.py
│           │   │   ├── state.py
│           │   │   └── result.py
│           │   ├── task/
│           │   │   └── spec.py
│           │   ├── model/
│           │   │   └── spec.py
│           │   ├── agent_env/
│           │   │   └── spec.py
│           │   ├── policy/
│           │   │   └── spec.py
│           │   ├── tools/
│           │   │   ├── spec.py
│           │   │   └── events.py
│           │   └── observability/
│           │       ├── chat.py
│           │       └── events.py
│           ├── application/
│           │   ├── __init__.py
│           │   ├── bootstrap.py
│           │   ├── load_run_spec.py
│           │   ├── load_agent_env.py
│           │   ├── runtime_context.py
│           │   ├── build_runtime_context.py
│           │   ├── register_tools.py
│           │   ├── register_mcp.py
│           │   ├── create_agent.py
│           │   ├── execute_task.py
│           │   └── collect_result.py
│           ├── infrastructure/
│           │   ├── __init__.py
│           │   ├── config/
│           │   ├── runtime/
│           │   ├── llm/
│           │   ├── ag2/
│           │   ├── mcp/
│           │   ├── tools/
│           │   ├── prompts/
│           │   ├── security/
│           │   ├── observability/
│           │   ├── di/
│           │   └── logging/
│           └── presentation/
│               ├── __init__.py
│               ├── cli.py
│               └── main.py
└── launcher/
    └── src/
        └── zagent_launcher/
            ├── __init__.py
            ├── domain/
            │   ├── __init__.py
            │   ├── run_request.py
            │   ├── container_spec.py
            │   ├── mount_spec.py
            │   ├── launch_result.py
            │   └── artifact_ref.py
            ├── application/
            │   ├── __init__.py
            │   ├── prepare_run.py
            │   ├── start_run.py
            │   ├── read_run_state.py
            │   ├── read_run_trace.py
            │   └── collect_run_result.py
            ├── infrastructure/
            │   ├── __init__.py
            │   ├── config/
            │   ├── containers/
            │   │   ├── base.py
            │   │   ├── docker_runner.py
            │   │   ├── command_builder.py
            │   │   └── mount_builder.py
            │   ├── artifacts/
            │   │   ├── reader.py
            │   │   └── tailer.py
            │   └── logging/
            └── presentation/
                ├── __init__.py
                ├── cli.py
                └── api.py
```

Зависимости между слоями направлены внутрь:

- `domain` не зависит ни от чего внутри проекта;
- `application` зависит только от `domain` и абстрактных портов;
- `infrastructure` реализует порты и зависит от внешних библиотек;
- `presentation` связывает CLI/API с application use cases.

Между `zagent_runtime` и `zagent_launcher` нет Python-import зависимостей. Если нужен общий контракт, он выносится в `contracts/` как JSON Schema или markdown-спецификация, а не как общий Python-модуль.

Application use cases оформляются классами, а не module-level функциями. Зависимости передаются через конструктор и собираются в Dishka IoC container. Ручной wiring внутри use case файлов не допускается.

Runtime bootstrap является единой точкой application lifecycle для одного run:

- загрузить `run.yaml` и `.zagent`;
- открыть наблюдаемость через `RunObserverPort`;
- создать agent session;
- выполнить задачу через `AgentBackendRunner`;
- записать `result.json` и `summary.md`;
- завершить `state.json` и `events.jsonl` финальным статусом.

Подмена реализаций делается только на уровне Dishka providers. Базовый набор provider-ов содержит общие use cases, config loaders, prompt builder, observability и runtime-native tools. Отдельный execution provider выбирает backend:

- `Ag2RuntimeProvider` связывает `AgentFactory` и `AgentBackendRunner` с AG2;
- `DryRunRuntimeProvider` связывает те же порты с dry-run реализациями без обращения к LLM.

### 7.1. Управление зависимостями

Рекомендуемая модель — `uv` workspace:

- один `uv.lock` в корне репозитория;
- корневой `pyproject.toml` описывает workspace, dev tooling и общие dependency groups;
- `packages/runtime/pyproject.toml` описывает только зависимости runtime;
- `packages/launcher/pyproject.toml` описывает только зависимости launcher;
- workspace members не зависят друг от друга через Python imports.

Корневой `pyproject.toml`:

```toml
[project]
name = "zagent-workspace"
version = "0.1.0"
requires-python = ">=3.12,<3.14"

[tool.uv]
package = false

[tool.uv.workspace]
members = [
  "packages/runtime",
  "packages/launcher",
]

[dependency-groups]
dev = [
  "pytest>=8",
  "pytest-asyncio>=0.24",
  "ruff>=0.8",
  "mypy>=1.13",
]
```

`packages/runtime/pyproject.toml`:

```toml
[project]
name = "zagent-runtime"
version = "0.1.0"
requires-python = ">=3.12,<3.14"
dependencies = [
  "ag2[openai,mcp]>=0.11.5,<0.12",
  "dishka>=1.6,<2",
  "pydantic>=2",
  "pyyaml>=6",
  "typer>=0.15",
]

[project.scripts]
zagent-runtime = "zagent_runtime.presentation.cli:main"
```

`packages/launcher/pyproject.toml`:

```toml
[project]
name = "zagent-launcher"
version = "0.1.0"
requires-python = ">=3.12,<3.14"
dependencies = [
  "pydantic>=2",
  "pyyaml>=6",
  "typer>=0.15",
  "rich>=13",
]

[project.scripts]
zagent = "zagent_launcher.presentation.cli:main"
```

Если позже появится реальная необходимость в общем коде, допустим третий пакет `zagent-contracts`, но это должно быть осознанное решение. Для MVP лучше держать контракты файловыми, чтобы runtime и launcher оставались независимо заменяемыми.

---

## 8. AG2 как основной orchestration layer

AG2 используется как базовый фреймворк для управления агентом.

AG2 отвечает за:

- создание и конфигурацию агента;
- orchestration взаимодействия с LLM;
- интеграцию tools;
- интеграцию MCP;
- маршрутизацию prompt context;
- возможное расширение до multi-agent схем.

При этом AG2 **не должен быть ядром всего проекта**. Ядром проекта должен оставаться собственный runtime contract.

Правильное разделение:

- **AG2** — engine agent orchestration;
- **наш проект** — runtime platform.

Это позволит в будущем:

- менять образы без перепроектирования;
- расширять тулы и политики;
- поддержать dual-container execution;
- при необходимости заменить orchestration framework.

---

## 9. Runtime context

После загрузки `run.yaml` и `.zagent` должен собираться единый `RuntimeContext`.

Он содержит:

- `RunSpec`;
- `AgentEnv`;
- resolved prompts;
- активные rules;
- активные skills;
- LLM config;
- tool registry;
- MCP registry;
- workspace paths;
- policy settings;
- observer/tracing components.

Именно `RuntimeContext` передается в фабрику агента и исполняющий слой.

Главный пайплайн:

```text
BootstrapRun
  -> BuildRuntimeContext
  -> CreateAgent
  -> ExecuteTask
  -> CollectResult
```

Внутри `CreateAgent` собирается backend-neutral часть agent session:

```text
RuntimeContext -> ToolRegistry/McpRegistry -> PromptBuilder -> AgentFactory
```

`AgentBackendRunner` обязан запускать agent workflow с ограничением `runtime.max_turns`. Для AG2 это значение передается как `max_turns`; практически оно ограничивает длину conversational workflow, а не является переносимым доменным понятием конкретного provider API.

Финальное сообщение должно нормализоваться runtime-слоем: если agent не вернул
`ZAGENT_DONE`, executor добавляет его сам. Marker не настраивается через
`run.yaml`, чтобы внешний сигнал завершения оставался стабильным.

---

## 10. Подсистема tools

Должны поддерживаться три класса расширений:

### 10.1. Built-in tools

Предустановленные runtime-инструменты:

- `shell`
- `files`
- `apply_patch`
- `web_search`
- `image_generation`

Domain-модель не должна знать, какой framework реализует конкретный built-in tool. Поэтому `ToolKind` содержит только предметные категории вроде `builtin`, `custom`, `mcp`; тип вроде `ag2_builtin` не используется.

В infrastructure допускается backend mapping. Для MVP часть built-in tools может исполняться через AG2 native tools:

- `apply_patch` -> AG2 `apply_patch`;
- `web_search` -> AG2 `web_search`;
- `image_generation` -> AG2 `image_generation`.

Остальные built-in capabilities остаются runtime-controlled:

- `files`;
- `shell`.

Git не выделяется в отдельный toolkit. Агент выполняет `git status`, `git diff`,
`git add`, `git commit` и другие операции через `shell`, чтобы не создавать
неполный параллельный API поверх штатного CLI.

Так runtime contract остается стабильным, а AG2 остается заменяемой инфраструктурной реализацией.

### 10.2. Custom tools

Пользовательские Python-инструменты, подключаемые через plugin loader.

Рекомендуемый контракт:

```python
class ToolProvider(Protocol):
    name: str

    def get_tool_specs(self) -> list[ToolSpec]:
        ...
```

### 10.3. MCP-backed capabilities

Инструменты и возможности, приходящие из MCP-серверов.

Важно не ограничивать MCP только tool calls. Внутренняя capability model должна допускать:

- tools;
- prompts;
- resources.

Поэтому слой MCP следует интегрировать через отдельный adapter/registry.

---

## 11. Plugin system

Плагины не должны иметь произвольный доступ ко всему приложению.

Рекомендуемый контракт:

```python
class Plugin(Protocol):
    def register_tools(self, registry):
        ...

    def register_prompts(self, registry):
        ...

    def register_profiles(self, registry):
        ...

    def register_hooks(self, registry):
        ...
```

Это позволит расширять систему контролируемо и отделять contrib-расширения от ядра runtime.

---

## 12. Трассировка, чат и наблюдаемость

Требование: весь чат агента должен быть доступен:

- во время выполнения;
- после завершения запуска.

Но хранить нужно не только чат. Для полноценной отладки нужен **полный run trace**.

### 12.1. Структура runtime artifacts

Рекомендуемая структура:

```text
.zagent/
└── artifacts/
    └── run/
        ├── state.json
        ├── chat.jsonl
        ├── events.jsonl
        ├── tools.jsonl
        ├── summary.md
        ├── result.json
        └── logs/
            └── runtime.log
```

### 12.2. Назначение файлов

#### `chat.jsonl`

Хранит диалоговые сообщения:

- system;
- user/task;
- assistant.

Пример:

```json
{"ts":"2026-04-14T12:00:01Z","role":"system","content":"You are a coding agent..."}
{"ts":"2026-04-14T12:00:05Z","role":"user","content":"Fix pagination bug"}
{"ts":"2026-04-14T12:00:10Z","role":"assistant","content":"I will inspect the repository and tests first."}
```

#### `tools.jsonl`

Хранит вызовы инструментов и их результаты.

Пример:

```json
{"ts":"2026-04-14T12:00:15Z","tool":"shell","status":"started","args":{"command":"pytest -q"}}
{"ts":"2026-04-14T12:00:22Z","tool":"shell","status":"finished","exit_code":1,"stdout":"...","stderr":""}
```

#### `events.jsonl`

Хранит высокоуровневые runtime-события.

Пример:

```json
{"ts":"2026-04-14T12:00:00Z","event":"run_started","run_id":"fix-123"}
{"ts":"2026-04-14T12:00:03Z","event":"agent_initialized"}
{"ts":"2026-04-14T12:00:09Z","event":"task_execution_started"}
{"ts":"2026-04-14T12:02:45Z","event":"run_finished","status":"success"}
```

#### `state.json`

Хранит текущее состояние run и перезаписывается во время работы.

Пример:

```json
{
  "run_id": "fix-123",
  "status": "running",
  "phase": "executing_tools",
  "started_at": "2026-04-14T12:00:00Z",
  "updated_at": "2026-04-14T12:01:18Z",
  "last_message_index": 7,
  "last_tool_call": "shell",
  "artifacts": []
}
```

### 12.3. Почему JSONL

Формат `jsonl` выбран потому что:

- можно писать события построчно;
- удобно читать файл во время работы;
- не нужно хранить весь trace в памяти;
- частичное повреждение файла не ломает весь лог;
- удобно строить `tail -f` или SSE/WebSocket streaming.

### 12.4. Подсистема observability

Рекомендуемые компоненты:

```python
class ChatWriter: ...
class EventWriter: ...
class ToolTraceWriter: ...
class StateStore: ...
class RunPaths: ...
```

И фасад:

```python
class RunObserver:
    def on_run_started(self, ...): ...
    def on_message(self, ...): ...
    def on_tool_started(self, ...): ...
    def on_tool_finished(self, ...): ...
    def on_phase_changed(self, ...): ...
    def on_run_finished(self, ...): ...
```

Все AG2/runtime события должны идти через `RunObserver`.

### 12.5. Redaction

Перед записью в trace-файлы должна выполняться очистка секретов.

Нужен отдельный компонент:

```python
class SecretRedactor:
    def redact_text(self, value: str) -> str: ...
    def redact_mapping(self, data: dict) -> dict: ...
```

### 12.6. Ограничение размера

Необходимо сразу заложить лимиты:

- max message size;
- max stdout/stderr capture size;
- max total trace size per run.

При обрезке вывода должны ставиться признаки вроде:

```json
{"stdout_truncated": true, "stdout_preview": "..."}
```

---

## 13. Внешний интерфейс launcher

Launcher предоставляет внешний интерфейс управления runtime. В MVP это CLI и Python API, а HTTP API можно добавить позже поверх тех же операций.

Launcher не должен читать внутреннюю память процесса runtime. Он должен работать через container runtime и смонтированные артефакты.

Минимально должны поддерживаться операции:

- запуск нового run;
- чтение `state.json`;
- чтение `chat.jsonl`;
- чтение `events.jsonl`;
- чтение `tools.jsonl`;
- получение итогового результата и summary.

То есть будущий HTTP API можно строить поверх модели:

- `POST /runs`
- `GET /runs/{id}/state`
- `GET /runs/{id}/chat`
- `GET /runs/{id}/events`
- `GET /runs/{id}/tools`
- `GET /runs/{id}/result`

На первом этапе CLI/Python API может быть очень тонким и фактически только преобразовывать входной запрос в запуск runtime-контейнера и читать файлы runtime trace.

---

## 14. Dual-container режим на будущее

Хотя первая версия может запускать только один runtime-контейнер, архитектура должна заранее поддерживать расширение до двух runtime-контейнеров.

Модель:

- `primary container` — основной агентный runtime;
- `worker container` — опциональный sidecar для отдельных действий;
- `shared workspace volume` — общая папка для обмена файлами.

Это нужно для будущих сценариев, где:

- один runtime-контейнер выполняет orchestration;
- второй контейнер содержит другой SDK/toolchain;
- взаимодействие идет через файлы в shared volume.

Поэтому runtime abstractions не должны предполагать, что контейнер всегда только один.

---

## 15. Git-first модель для fix-задач

Для задач исправления кода git должен быть центральной сущностью workflow, но не
отдельным runtime toolkit.

Рекомендуемое поведение:

- работа только внутри git-репозитория;
- фиксация before/after состояния;
- diff как основной итоговый артефакт;
- optional patch file;
- optional local commit;
- `push` запрещен по умолчанию.

Это делает работу агента reviewable и безопаснее для первой версии.
Git-операции выполняются через `shell`, а runtime policy ограничивает опасные
действия вроде `push`.

---

## 16. Политики и безопасность

Policy слой должен разделяться минимум на следующие категории:

- `execution policy` — какие команды можно выполнять;
- `filesystem policy` — куда можно писать;
- `network policy` — какой сетевой доступ разрешен;
- `tool policy` — какие инструменты доступны;
- `approval policy` — какие действия требуют подтверждения;
- `secret policy` — какие секреты доступны и в каком виде.

Это особенно важно для:

- shell tools;
- git операций через shell;
- MCP tools;
- внешних сетевых вызовов.

---

## 17. Минимальный MVP

Для первой версии рекомендуется зафиксировать следующий scope:

- один runtime-контейнер;
- host-side launcher как CLI/Python-библиотека без обязательного отдельного образа;
- один AG2 agent;
- built-in tools: `shell`, `files`, `apply_patch`;
- MCP support через registry;
- `.zagent` как базовое runtime-окружение;
- `run.yaml` как внешний контракт запуска;
- обязательный tracing через `chat.jsonl`, `events.jsonl`, `tools.jsonl`, `state.json`;
- output artifacts: `summary.md`, `result.json`, `patch.diff` при необходимости;
- запрет на `git push`, merge и опасные действия по умолчанию.

---

## 18. Рекомендуемые первые модули для реализации

Если двигаться поэтапно, в первую очередь стоит реализовать:

```text
pyproject.toml
contracts/run-spec.schema.json

packages/runtime/pyproject.toml
packages/runtime/src/zagent_runtime/domain/run/spec.py
packages/runtime/src/zagent_runtime/domain/run/state.py
packages/runtime/src/zagent_runtime/domain/run/result.py
packages/runtime/src/zagent_runtime/domain/agent_env/spec.py
packages/runtime/src/zagent_runtime/domain/task/spec.py
packages/runtime/src/zagent_runtime/domain/model/spec.py
packages/runtime/src/zagent_runtime/domain/policy/spec.py
packages/runtime/src/zagent_runtime/domain/tools/spec.py
packages/runtime/src/zagent_runtime/domain/observability/chat.py
packages/runtime/src/zagent_runtime/application/runtime_context.py
packages/runtime/src/zagent_runtime/application/bootstrap.py
packages/runtime/src/zagent_runtime/application/build_runtime_context.py
packages/runtime/src/zagent_runtime/application/create_agent.py
packages/runtime/src/zagent_runtime/application/execute_task.py
packages/runtime/src/zagent_runtime/application/collect_result.py
packages/runtime/src/zagent_runtime/application/observe_run.py
packages/runtime/src/zagent_runtime/infrastructure/config/yaml_loader.py
packages/runtime/src/zagent_runtime/infrastructure/config/loaders.py
packages/runtime/src/zagent_runtime/infrastructure/config/path_resolver.py
packages/runtime/src/zagent_runtime/infrastructure/di/providers.py
packages/runtime/src/zagent_runtime/infrastructure/di/container.py
packages/runtime/src/zagent_runtime/infrastructure/ag2/agent_factory.py
packages/runtime/src/zagent_runtime/infrastructure/ag2/run_executor.py
packages/runtime/src/zagent_runtime/infrastructure/prompts/prompt_builder.py
packages/runtime/src/zagent_runtime/infrastructure/runtime/result_writer.py
packages/runtime/src/zagent_runtime/infrastructure/runtime/dry_run.py
packages/runtime/src/zagent_runtime/infrastructure/tools/registry.py
packages/runtime/src/zagent_runtime/infrastructure/mcp/registry.py
packages/runtime/src/zagent_runtime/infrastructure/observability/run_observer.py
packages/runtime/src/zagent_runtime/presentation/cli.py

packages/launcher/pyproject.toml
packages/launcher/src/zagent_launcher/domain/run_request.py
packages/launcher/src/zagent_launcher/domain/container_spec.py
packages/launcher/src/zagent_launcher/application/prepare_run.py
packages/launcher/src/zagent_launcher/application/start_run.py
packages/launcher/src/zagent_launcher/infrastructure/containers/base.py
packages/launcher/src/zagent_launcher/infrastructure/containers/docker_runner.py
packages/launcher/src/zagent_launcher/infrastructure/artifacts/reader.py
packages/launcher/src/zagent_launcher/presentation/cli.py
```

Этого достаточно, чтобы собрать первый работающий прототип.

---

## 19. Ключевые классы

На уровне концепции стоит сразу заложить следующие сущности.

Runtime:

```python
class RunSpec: ...
class AgentEnv: ...
class RuntimeContext: ...
class BootstrapRun: ...
class ToolRegistry: ...
class McpRegistry: ...
class PromptBuilder: ...
class AgentFactory: ...
class AgentBackendRunner: ...
class ChatWriter: ...
class EventWriter: ...
class ToolTraceWriter: ...
class StateStore: ...
class RunObserverPort: ...
class RunObserver: ...
```

Launcher:

```python
class RunRequest: ...
class ContainerSpec: ...
class MountSpec: ...
class LaunchResult: ...
class ArtifactRef: ...
class ContainerRunner: ...
class DockerRunner: ...
class ArtifactReader: ...
class RunTailer: ...
```

---

## 20. Итоговый вывод

Рекомендуемая архитектура строится вокруг следующих принципов:

- контейнерный runtime является центром системы;
- AG2 используется как orchestration engine, но не как ядро всей платформы;
- `.zagent` является стабильным внутренним окружением агента;
- `run.yaml` является внешним контрактом запуска;
- launcher отвечает только за host-side orchestration и старт runtime-контейнера;
- runtime отвечает за выполнение задачи;
- observability должна быть встроена с самого начала;
- расширяемость достигается через tools, plugins, MCP и profile-like окружение;
- архитектура должна заранее допускать dual-container runtime mode, но MVP может быть с одним runtime-контейнером.

Такой подход дает:

- изоляцию;
- воспроизводимость;
- расширяемость;
- наблюдаемость;
- управляемую интеграцию с внешними системами.

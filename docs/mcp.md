# MCP

ZAgent будет поддерживать два типа MCP servers:

- remote MCP: `sse` и `streamable_http`;
- local MCP: `stdio`, запускаемый внутри runtime-контейнера.

## Remote MCP

Remote MCP проще всего поддерживать и эксплуатировать. Сервер уже запущен
отдельно, а runtime подключается к нему по URL.

Пример `.zagent/mcp/servers.yaml`:

```yaml
servers:
  - name: docs
    enabled: true
    transport: streamable_http
    url: http://mcp-docs:8080/mcp
```

Для локальной разработки такие MCP удобно запускать отдельными services в
`compose.yml`.

## Local MCP

Local MCP запускается как процесс внутри runtime-контейнера.

Базовый runtime image содержит:

- `npx` через `nodejs` и `npm`;
- `uvx` через `uv`;
- `git`, `curl`, `ca-certificates`.

Этого достаточно для большинства stdio MCP servers, которые запускаются через
`npx` или `uvx`.

Пример `.zagent/mcp/servers.yaml`:

```yaml
servers:
  - name: filesystem
    enabled: true
    transport: stdio
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - /workspace

  - name: python-docs
    enabled: true
    transport: stdio
    command: uvx
    args:
      - some-python-mcp-server
```

## Системные зависимости

Базовый образ не должен включать тяжелую системную обвязку для всех возможных
MCP servers.

Например, `playwright-mcp` может требовать Chromium и browser dependencies. Для
таких случаев лучше делать отдельный Dockerfile или profile-image:

```dockerfile
FROM zagent-runtime:local

RUN npx playwright install --with-deps chromium
```

Так базовый runtime остается небольшим, а проекты с особыми требованиями явно
описывают свою среду.

## Формат servers.yaml

```yaml
servers:
  - name: filesystem
    enabled: true
    transport: stdio
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - /workspace
    environment_env:
      API_KEY: FILESYSTEM_MCP_API_KEY

  - name: docs
    enabled: true
    transport: streamable_http
    url: http://mcp-docs:8080/mcp
    headers_env:
      Authorization: MCP_AUTH_HEADER
    timeout_seconds: 30
    read_timeout_seconds: 300
```

Поддерживаемые `transport`:

- `stdio`;
- `sse`;
- `streamable_http` или `streamable-http`.

Секреты лучше передавать через `environment_env` и `headers_env`: ключ слева
попадает в MCP server, значение справа является именем переменной окружения
runtime-контейнера.

## Что реализовано в runtime

Runtime уже:

1. читает `.zagent/mcp/servers.yaml`, если в `run.yaml` включен `tools.enable_mcp`;
2. валидирует `stdio`, `sse`, `streamable_http`;
3. открывает MCP sessions через AG2/MCP SDK;
4. создает AG2 toolkit через `create_toolkit`;
5. регистрирует MCP tools на `zagent_assistant` и `zagent_runtime_executor`;
6. пишет подключение, ошибки и отключение MCP servers в `events.jsonl`;
7. пишет вызовы MCP tools в `tools.jsonl` в формате `mcp:<server>.<tool>`;
8. закрывает MCP sessions после завершения run.

## Что осталось улучшить

Следующие задачи:

1. добавить e2e-проверку с реальным stdio MCP server через `npx`;
2. добавить отдельный пример для remote MCP через `sse` или `streamable_http`.

Runtime installs должны быть отдельной opt-in политикой. По умолчанию мы
разрешаем запуск через уже доступные `npx` и `uvx`, а дополнительные системные
пакеты добавляются через Dockerfile.

# Python Clean Architecture Skill

## Назначение

Применяй этот skill для Python задач, где нужно создать или изменить backend
приложение. Работай небольшими проверяемыми шагами и держи код простым.

## Обязательный порядок работы

1. Прочитай `run.yaml` и уточни цель задачи.
2. Осмотри текущую структуру workspace перед изменениями.
3. Составь короткую внутреннюю схему слоев и файлов.
4. Вноси изменения инкрементально.
5. Запусти тесты или минимальную проверку запуска.
6. В финальном ответе перечисли измененные файлы и результат проверок.

## Архитектура

Пиши по Clean Architecture:

- `domain` содержит сущности, value objects и repository interfaces;
- `application` содержит use cases и не зависит от FastAPI, SQLite или HTTP;
- `infrastructure` содержит SQLite implementation, настройки хранения и внешние адаптеры;
- `presentation` содержит FastAPI routes, DTO/request/response модели и HTTP mapping.

Зависимости должны быть направлены внутрь:

- presentation зависит от application;
- infrastructure реализует interfaces из domain/application;
- domain не импортирует FastAPI, sqlite3, pydantic, httpx или pytest.

## SOLID

- Single Responsibility: один модуль или класс отвечает за одну причину изменения.
- Open/Closed: use cases должны работать через interfaces, чтобы хранилище можно было заменить.
- Liskov: repository implementations должны соблюдать один контракт.
- Interface Segregation: не создавай толстые interfaces для одной таблицы.
- Dependency Inversion: use cases зависят от abstractions, а не от SQLite.

## FastAPI и SQLite

- Не размещай SQL-запросы в route handlers.
- Не смешивай HTTP ошибки с domain logic.
- Для SQLite используй стандартный `sqlite3`, если задача не просит ORM.
- Инициализацию таблиц вынеси в infrastructure.
- Для тестов используй временный файл базы или `:memory:` с управляемым lifecycle.

## Тестирование

- Покрывай публичное HTTP поведение через `fastapi.testclient.TestClient`.
- Проверяй успешные сценарии и ошибки.
- Тесты должны быть повторяемыми и не зависеть от старого состояния базы.
- Если проверку запустить нельзя, явно напиши причину и что было проверено вместо этого.

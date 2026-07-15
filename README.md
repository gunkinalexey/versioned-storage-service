# Versioned Storage Service

Небольшой FastAPI-сервис для хранения версионируемых наборов данных. Метаданные и состояния версий сохраняются в SQL-базе, а содержимое файлов — в S3-совместимом объектном хранилище.

Сервис может использоваться для хранения конфигураций, результатов расчётов и других артефактов, для которых важны проверка целостности, история изменений и получение актуальной версии.

## Возможности

- создание черновой версии коллекции;
- сохранение манифеста файлов;
- потоковая загрузка файлов в S3 с проверкой SHA-256;
- потоковое скачивание файлов без загрузки целого объекта в память;
- дополнительные endpoints для передачи небольших файлов в base64;
- запрет публикации неполной версии;
- переключение текущей версии и перевод предыдущей в `outdated`;
- запрет изменения опубликованной версии.

## Структура

- `routes` — тонкие FastAPI endpoints;
- `endpoint_handlers` — обработка операций и логирование;
- `database.AsyncClient` — работа с метаданными и состояниями версий;
- `storage.StorageClient` — потоковая работа с S3-совместимым хранилищем;
- `error_handler` и `exceptions` — единый формат доменных ошибок;
- `tests/test_integration.py` — независимые интеграционные тесты основных и ошибочных сценариев с изолированным тестовым хранилищем.

## Запуск через Docker Compose

Для запуска API, MinIO и SQLite достаточно одной команды:

```bash
docker compose up --build
```

После запуска доступны:

- Swagger UI: `http://localhost:8000/docs`;
- healthcheck: `http://localhost:8000/api/v1/health`;
- MinIO Console: `http://localhost:9001`.

По умолчанию Compose использует локальные демонстрационные credentials. Их можно
переопределить через `.env`:

```bash
cp .env.example .env
# Указать S3_ACCESS_KEY и S3_SECRET_KEY.
docker compose up --build
```

Остановить сервисы:

```bash
docker compose down
```

Удалить сервисы вместе с локальными данными:

```bash
docker compose down -v
```

## Запуск без Docker Compose

MinIO можно запустить отдельно, а приложение — через Poetry:

```bash
cp .env.example .env
poetry install
poetry run uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000
```

## Потоковая передача файла

Основные endpoints работают с бинарным body. Параметры загружаемого элемента передаются в заголовках, а содержимое запроса направляется в S3 по мере получения.

```bash
FILE_PATH=example.bin
FILE_HASH=$(sha256sum "$FILE_PATH" | cut -d ' ' -f 1)
FILE_SIZE=$(wc -c < "$FILE_PATH")

curl -X POST http://localhost:8000/api/v1/data \
  -H "Content-Type: application/octet-stream" \
  -H "Content-Length: $FILE_SIZE" \
  -H "X-File-Hash: $FILE_HASH" \
  -H "X-Collection-UUID: COLLECTION_UUID" \
  -H "X-Version-UUID: VERSION_UUID" \
  -H "X-Item-UUID: ITEM_UUID" \
  --data-binary "@$FILE_PATH"
```

Скачивание:

```bash
curl -G http://localhost:8000/api/v1/data \
  --data-urlencode "collection_uuid=COLLECTION_UUID" \
  --data-urlencode "version_uuid=VERSION_UUID" \
  --data-urlencode "item_uuid=ITEM_UUID" \
  --output example.bin
```

Для небольших данных также доступны `POST /api/v1/data_b64` и `GET /api/v1/data_b64`.

## Проверки

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy src
```

SQLite используется только для автономного примера и хранит метаданные. Бинарные данные в базу не записываются.

install:
	poetry install

run:
	poetry run uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000

test:
	poetry run pytest

check:
	poetry run ruff check .
	poetry run mypy src


docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-clean:
	docker compose down -v

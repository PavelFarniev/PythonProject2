# Контрольная работа №3

В репозитории собраны простые решения для заданий:

- `6.1`
- `6.2`
- `6.3`
- `6.4`
- `6.5`
- `7.1`
- `8.1`

Задание `8.2` намеренно не реализовано по условию.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Запуск

Формат запуска у всех заданий одинаковый:

```bash
uvicorn task_6_1.main:app --reload
```

Замените `task_6_1` на нужную директорию:

- `task_6_1`
- `task_6_2`
- `task_6_3`
- `task_6_4`
- `task_6_5`
- `task_7_1`
- `task_8_1`

Для `8.1` сначала создайте таблицу:

```bash
python -m task_8_1.init_db
uvicorn task_8_1.main:app --reload
```

## Переменные окружения

Используются такие переменные:

- `MODE` для задания `6.3` (`DEV` или `PROD`)
- `DOCS_USER` для задания `6.3`
- `DOCS_PASSWORD` для задания `6.3`
- `JWT_SECRET` для заданий `6.4`, `6.5`, `7.1`

## Проверка эндпоинтов

### 6.1

```bash
curl -i -u admin:admin123 http://127.0.0.1:8000/login
curl -i -u admin:wrong http://127.0.0.1:8000/login
```

### 6.2

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"correctpass"}'

curl -u user1:correctpass http://127.0.0.1:8000/login
curl -i -u user1:wrongpass http://127.0.0.1:8000/login
```

### 6.3

```bash
curl -i -u admin:admin123 http://127.0.0.1:8000/docs
curl -i http://127.0.0.1:8000/openapi.json
```

Для PROD-режима:

```bash
MODE=PROD uvicorn task_6_3.main:app --reload
curl -i http://127.0.0.1:8000/docs
```

### 6.4

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"securepassword123"}'
```

После получения токена:

```bash
curl http://127.0.0.1:8000/protected_resource \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6.5

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}'

curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}'
```

### 7.1

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"boss","password":"adminpass","role":"admin"}'

curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"boss","password":"adminpass"}'
```

С токеном можно проверять доступ:

```bash
curl http://127.0.0.1:8000/protected_resource \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X POST http://127.0.0.1:8000/admin/resource \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8.1

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"12345"}'
```

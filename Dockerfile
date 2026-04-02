FROM python:3.12-slim

# Системные зависимости для psycopg2-binary и Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Копируем файлы зависимостей отдельно (кэширование слоёв Docker)
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости + gunicorn
RUN uv pip install --system --no-cache -r pyproject.toml \
    && uv pip install --system --no-cache gunicorn

# Копируем весь проект
COPY . .

# Собираем статику
RUN SECRET_KEY=build-placeholder DEBUG=false \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120"]

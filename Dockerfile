# TASHKENT PROFNASTIL SERVIS — Django catalog site
FROM python:3.12-slim

# Faster, cleaner Python in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps: postgres client libs + gettext (for makemessages/compilemessages).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        gettext \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first to leverage Docker layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source.
COPY . .

# Entrypoint waits for the DB, runs migrations + collectstatic, then exec's CMD.
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

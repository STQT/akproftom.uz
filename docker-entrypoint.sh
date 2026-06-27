#!/usr/bin/env sh
set -e

# Wait for PostgreSQL to accept connections before doing anything that needs it.
if [ "$DB_ENGINE" = "postgres" ]; then
    echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
    until python -c "import socket,sys; s=socket.socket(); s.settimeout(2); \
        s.connect(('${DB_HOST:-db}', int('${DB_PORT:-5432}'))); s.close()" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL is up."
fi

# Apply migrations and gather static files (idempotent — safe on every start).
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"

#!/bin/sh

echo "Waiting for Redis..."

while ! nc -z redis 6379; do
  sleep 1
done

echo "Redis started"

python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
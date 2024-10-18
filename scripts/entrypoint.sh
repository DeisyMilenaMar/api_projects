#!/bin/bash
set -e

# Wait for the database to be ready
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done

>&2 echo "Postgres is up - executing command"

# Run migrations
python manage.py migrate

# Collect static files only if using the production settings.
if [ "$DJANGO_SETTINGS_MODULE" = "api.config.settings.prod" ]; then
    python manage.py collectstatic --noinput --clear
fi

# Execute the command passed to the entrypoint
exec "$@"

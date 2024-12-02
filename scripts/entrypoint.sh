#!/bin/bash
set -e

# Wait for the database to be ready
until PGPASSWORD="$POSTGRES_DB_PASSWORD" psql -h "$POSTGRES_DB_HOST" -U "$POSTGRES_DB_USER" -d "$POSTGRES_DB_NAME" -c '\q'; do
    >&2 echo "Postgres is unavailable - sleeping"
    sleep 1
done

>&2 echo "Postgres is up - executing command"

# Run migrations
python manage.py migrate --settings=api.config.settings.base

# Collect static files only if using the production settings.
# if [ "$DJANGO_SETTINGS_MODULE" = "api.config.settings.base" ]; then
#     python manage.py collectstatic --noinput --clear
# fi

# Execute the command passed to the entrypoint
exec "$@"

#!/bin/bash
set -e  # Detener el script si ocurre algún error

# Cargar las variables de entorno desde el archivo .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Verificar y crear la base de datos principal
PSQL="psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U postgres"

# Crear el usuario si no existe
if ! $PSQL -tc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_USER'" | grep -q 1; then
    $PSQL -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"
else
    echo "User '$POSTGRES_USER' already exists."
fi

# Crear la base de datos si no existe
if ! $PSQL -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1; then
    $PSQL -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"
else
    echo "Database '$POSTGRES_DB' already exists."
fi

echo "Database '$POSTGRES_DB' and user '$POSTGRES_USER' created or already exist."

#!/bin/bash

set -e  # Stop the script if any error occurs

# Load environment variables from the .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Function to check if all required database variables are defined
check_db_vars() {
    local prefix="$1"
    local required_vars=(
        "${prefix}_DB_NAME"
        "${prefix}_DB_USER"
        "${prefix}_DB_PASSWORD"
        "${prefix}_DB_HOST"
        "${prefix}_DB_PORT"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: Environment variable $var is not defined."
            return 1
        fi
    done
    return 0
}

# Create function to check and create database and user
create_db_and_user() {
    local db_name="$1"
    local db_user="$2"
    local db_password="$3"
    local db_host="$4"
    local db_port="$5"

    echo "Creating database '$db_name' and user '$db_user'..."

    PSQL="psql -h $db_host -p $db_port -U postgres"

    # Create user if it does not exist
    if ! $PSQL -tc "SELECT 1 FROM pg_roles WHERE rolname='$db_user'" | grep -q 1; then
        $PSQL -c "CREATE USER $db_user WITH PASSWORD '$db_password';"
    else
        echo "User '$db_user' already exists."
    fi

    # Create database if it does not exist
    if ! $PSQL -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        $PSQL -c "CREATE DATABASE $db_name OWNER $db_user;"
    else
        echo "Database '$db_name' already exists."
    fi

    echo "Database '$db_name' and user '$db_user' created or already exist."
}

# Create main database
if check_db_vars "POSTGRES"; then
    create_db_and_user "$POSTGRES_DB" "$POSTGRES_USER" "$POSTGRES_PASSWORD" "$POSTGRES_HOST" "$POSTGRES_PORT"
else
    echo "Error: Failed to create main database variables."
    exit 1
fi

# Create database for Binance Trader API
if check_db_vars "BINANCE_TRADER_API"; then
    create_db_and_user "$BINANCE_TRADER_API_DB_NAME" "$BINANCE_TRADER_API_DB_USER" "$BINANCE_TRADER_API_DB_PASSWORD" "$BINANCE_TRADER_API_DB_HOST" "$BINANCE_TRADER_API_DB_PORT"
else
    echo "Error: Failed to create Binance Trader API database variables."
    exit 1
fi

echo "All databases and users are set up."

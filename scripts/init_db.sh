#!/bin/bash
# Initialize database script

set -e

echo "=== Initializing Database ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing migrations"

# Run Alembic migrations
alembic upgrade head

echo "Database initialized successfully!"

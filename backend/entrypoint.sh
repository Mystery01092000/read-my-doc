#!/bin/sh
set -e

# Run database migrations before starting the application
echo "Running database migrations..."
alembic upgrade head

# Start the application
exec "$@"

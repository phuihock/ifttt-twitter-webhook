#!/bin/bash
# Script to apply database migrations

echo "Applying database migrations..."

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
    echo "Error: migrations directory not found"
    exit 1
fi

# Check if migration script exists
if [ ! -f "migrations/apply_migration.py" ]; then
    echo "Error: migration script not found"
    exit 1
fi

# Run the migration
python migrations/apply_migration.py

if [ $? -eq 0 ]; then
    echo "Database migrations applied successfully!"
else
    echo "Error applying database migrations!"
    exit 1
fi
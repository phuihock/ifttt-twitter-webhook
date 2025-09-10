#!/bin/bash
# Script to apply database migrations

echo "Applying database migrations..."

# Load configuration to get database path
CONFIG_FILE="config/config.json"
DB_PATH="data/tweets.db"

# Check if config file exists and try to read database path
if [ -f "$CONFIG_FILE" ]; then
    # Try to extract database path from config (simple approach)
    if command -v jq >/dev/null 2>&1; then
        CONFIG_DB_PATH=$(jq -r '.database.path // "data/tweets.db"' "$CONFIG_FILE" 2>/dev/null)
        if [ "$CONFIG_DB_PATH" != "null" ] && [ -n "$CONFIG_DB_PATH" ]; then
            DB_PATH="$CONFIG_DB_PATH"
        fi
    else
        # Fallback to default if jq not available
        echo "Note: jq not available, using default database path"
    fi
fi

echo "Database path: $DB_PATH"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Database file $DB_PATH does not exist. Nothing to migrate."
    exit 0
fi

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
echo "Applying migration script..."
python migrations/apply_migration.py

if [ $? -eq 0 ]; then
    echo "Database migrations applied successfully!"
else
    echo "Error applying database migrations!"
    exit 1
fi
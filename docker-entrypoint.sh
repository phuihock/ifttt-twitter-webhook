#!/bin/bash
set -e

# Default values
USER_ID=${USER_ID:-1000}
USER_NAME=${USER_NAME:-app}
GROUP_ID=${GROUP_ID:-1000}
GROUP_NAME=${GROUP_NAME:-appgroup}

# If running as root, create/modify user
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, setting up user $USER_NAME with UID:$USER_ID GID:$GROUP_ID"

    # Create group if it doesn't exist
    if ! getent group $GROUP_NAME >/dev/null 2>&1; then
        groupadd -g $GROUP_ID $GROUP_NAME 2>/dev/null || true
    fi

    # Create user if it doesn't exist
    if ! id -u $USER_NAME >/dev/null 2>&1; then
        useradd --create-home --shell /bin/bash --uid $USER_ID --gid $GROUP_ID $USER_NAME 2>/dev/null || true
    fi

    # Ensure user owns the application directory
    chown -R $USER_NAME:$GROUP_NAME /app

    # Switch to the application user
    exec gosu $USER_NAME "$@"
else
    echo "Not running as root, executing as current user $(id -u):$(id -g)"
    exec "$@"
fi
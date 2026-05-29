#!/usr/bin/env bash
set -e

SERVER="root@vlthub.ru"
REMOTE_DIR="/var/www/vlthub"
BUILD_DIR="app/.output/public"

echo "=== Building frontend ==="
cd "$(dirname "$0")/.."
npm run build

echo "=== Copying to server ==="
rsync -avz --delete "$BUILD_DIR/" "$SERVER:$REMOTE_DIR/"

echo "=== Reloading Apache ==="
ssh "$SERVER" "sudo systemctl reload apache2"

echo "=== Done ==="

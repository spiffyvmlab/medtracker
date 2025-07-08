#!/bin/bash

set -e

IMAGE_NAME="medtracker-app:latest"
APP_DIR="$(dirname "$0")/app"

echo "Building Docker image '$IMAGE_NAME' from $APP_DIR ..."
docker build -t "$IMAGE_NAME" "$APP_DIR"

echo "Build complete."
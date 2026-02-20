#!/usr/bin/env bash

set -e

echo "Building the Docker image..."
docker build -t rust-builder-general tools/rust-builder/general

echo "Running the Docker container..."
docker run --rm -v "$(pwd)":/app rust-builder-general bash -c "cd /app && ./tools/rust-builder/general/build.sh"

echo "Building MacOS Docker image..."
docker build -t rust-builder-osx tools/rust-builder/osx

echo "Running MacOS Docker container..."
docker run --rm -v "$(pwd)":/app rust-builder-osx bash -c "cd /app && ./tools/rust-builder/osx/build.sh"

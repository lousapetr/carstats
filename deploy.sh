#!/bin/bash
# Run this on the Oracle Cloud VM to deploy the latest committed code.
set -euo pipefail
cd "$(dirname "$0")"

git pull
docker compose up -d --build
docker compose ps

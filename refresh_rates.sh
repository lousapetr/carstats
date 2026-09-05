#!/bin/bash
# Refresh currency exchange rates from the CNB daily fixing.
# Run this on the Oracle Cloud VM, manually or via cron (see README).
set -euo pipefail
cd "$(dirname "$0")"

docker compose exec -T app python -m scripts.refresh_exchange_rates

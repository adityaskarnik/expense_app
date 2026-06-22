#!/usr/bin/env bash
set -euo pipefail

# Only tear down resources for this compose project (avoid deleting unrelated containers/images).
sudo docker compose down --remove-orphans --volumes
sudo docker compose up --build
#!/bin/bash
set -a
source <hermes-home>/profiles/<profile>/home/.hermes/.env
set +a
export ALLOWED_TELEGRAM_USER_ID=8666597030
exec /usr/bin/python3 <hermes-telegram-artifacts>/scripts/kanban-proxy.py
#!/bin/bash
set -a
source /root/.hermes/profiles/indigo/home/.hermes/.env
set +a
export ALLOWED_TELEGRAM_USER_ID=8666597030
exec /usr/bin/python3 /root/hermes-telegram-artifacts/scripts/kanban-proxy.py

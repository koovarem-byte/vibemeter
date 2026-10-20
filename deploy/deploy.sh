#!/usr/bin/env bash
# Запускается НА MAC из папки проекта: ./deploy/deploy.sh IP_СЕРВЕРА
# Копирует закоммиченный код ветки fix/launch (без .env и базы) и запускает настройку сервера.
set -euo pipefail

SERVER=${1:?"Укажи IP сервера: ./deploy/deploy.sh 1.2.3.4"}
BRANCH=${BRANCH:-fix/launch}

cd "$(dirname "$0")/.."
echo "== Копирую код ветки $BRANCH на $SERVER"
git archive --format=tar "$BRANCH" | ssh "root@$SERVER" "mkdir -p /opt/vibemeter && tar -x -C /opt/vibemeter"

echo "== Настраиваю сервер"
ssh -t "root@$SERVER" "bash /opt/vibemeter/deploy/setup_server.sh"

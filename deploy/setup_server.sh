#!/usr/bin/env bash
# Запускается НА СЕРВЕРЕ (Ubuntu 22.04/24.04) от root.
# Повторный запуск безопасен: обновляет зависимости и перезапускает бота.
set -euo pipefail

APP=/opt/vibemeter
ENV_DIR=/etc/vibemeter
ENV_FILE=$ENV_DIR/env

echo "== Проверяю доступ к Telegram API"
code=$(curl -s -o /dev/null -m 15 -w "%{http_code}" https://api.telegram.org/ || true)
if [ "$code" = "000" ]; then
    echo "!! api.telegram.org недоступен с этого сервера. Бот здесь работать не будет."
    exit 1
fi
echo "   ok (HTTP $code)"

echo "== Ставлю Python"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip >/dev/null
python3 --version

echo "== Пользователь и папки"
id vibemeter >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin vibemeter
mkdir -p "$APP" "$ENV_DIR"

echo "== Зависимости"
[ -d "$APP/venv" ] || python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install -q --upgrade pip
"$APP/venv/bin/pip" install -q -r "$APP/requirements.txt"
chown -R vibemeter:vibemeter "$APP"

if [ ! -f "$ENV_FILE" ]; then
    echo "== Секреты (ввод не отображается на экране, это нормально)"
    read -rsp "Вставь BOT_TOKEN и нажми Enter: " BOT_TOKEN; echo
    read -rsp "Вставь DATABASE_URL и нажми Enter: " DATABASE_URL; echo
    read -rp  "Введи ADMIN_ID и нажми Enter: " ADMIN_ID
    umask 077
    {
        printf 'BOT_TOKEN="%s"\n' "$BOT_TOKEN"
        printf 'DATABASE_URL="%s"\n' "$DATABASE_URL"
        printf 'ADMIN_ID="%s"\n' "$ADMIN_ID"
    } > "$ENV_FILE"
    unset BOT_TOKEN DATABASE_URL
    chown root:vibemeter "$ENV_FILE"
    chmod 640 "$ENV_FILE"
    echo "   сохранено в $ENV_FILE"
else
    echo "== Секреты уже есть в $ENV_FILE (чтобы заменить: удали файл и запусти скрипт снова)"
fi

echo "== Служба systemd"
cp "$APP/deploy/vibemeter.service" /etc/systemd/system/vibemeter.service
systemctl daemon-reload
systemctl enable vibemeter >/dev/null
systemctl restart vibemeter
sleep 8
systemctl --no-pager --lines=0 status vibemeter | head -5
echo
echo "== Последние строки лога"
journalctl -u vibemeter -n 15 --no-pager | grep -vE '[0-9]{8,10}:[A-Za-z0-9_-]{30,}' || true

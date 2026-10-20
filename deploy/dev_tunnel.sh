#!/bin/bash
# Временный HTTPS для Mini App, пока нет VPS.
# Держит туннель localhost.run к боту (порт 8080), после обрыва переподключается
# и каждый новый адрес сам ставит на кнопку «Вайбометр». Остановить: Ctrl+C.

cd "$(dirname "$0")/.." || exit 1
trap 'echo; echo "Туннель остановлен"; exit 0' INT

while true; do
    ssh -tt -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
        -o StrictHostKeyChecking=accept-new \
        -R 80:localhost:8080 nokey@localhost.run 2>&1 |
    while IFS= read -r line; do
        url=$(printf '%s' "$line" | grep -o 'https://[a-z0-9]*\.lhr\.life' | head -1)
        if [ -n "$url" ] && [ "$url" != "$last" ]; then
            last="$url"
            echo "🌐 Новый адрес: $url"
            .venv/bin/python deploy/set_webapp_url.py "$url"
        fi
    done
    echo "Туннель упал, переподключаюсь через 5 секунд…"
    sleep 5
done

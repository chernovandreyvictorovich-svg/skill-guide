#!/bin/bash
# Снимает launchd-агент автообновления. Сам гид и данные остаются.
set -euo pipefail
LABEL="com.skill-guide.autoupdate"
DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"
launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
rm -f "$DEST"
echo "[skill-guide] автообновление снято. Ручной запуск ./update.sh по-прежнему работает."

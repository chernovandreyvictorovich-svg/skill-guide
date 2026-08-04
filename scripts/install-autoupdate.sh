#!/bin/bash
# Ставит launchd-агент автообновления: гид пересобирается сам при установке/удалении скиллов.
#
# ВНИМАНИЕ (macOS): launchd-агент НЕ сможет читать ~/Documents без «Full Disk Access».
# По умолчанию автообновление уже работает через SessionStart-хук Claude — этот launchd
# нужен, только если хочешь пересборку и вне сессий Claude. Тогда выдай Full Disk Access
# процессу /bin/bash в Системные настройки → Приватность → Полный доступ к диску.
set -euo pipefail
LABEL="com.skill-guide.autoupdate"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # корень проекта
DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$HOME/.codex/skills"   # чтобы WatchPath существовал

# генерируем plist под текущую машину из шаблона (без хардкода путей в репозитории)
sed -e "s#__LABEL__#${LABEL}#g" \
    -e "s#__PROJECT_DIR__#${DIR}#g" \
    -e "s#__HOME__#${HOME}#g" \
    "$DIR/launchd/skillguide.plist.tmpl" > "$DEST"

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$DEST"
launchctl enable "gui/$(id -u)/${LABEL}"

echo "[skill-guide] автообновление установлено ($LABEL)"
echo "[skill-guide] логи: $DIR/data/update.log"

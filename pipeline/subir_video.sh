#!/usr/bin/env bash
# Sube un mp4 al repo público en la rama "video" (rama huérfana que se REEMPLAZA en cada subida,
# así el repo no crece) y escribe la URL pública raw. vidIQ copia el vídeo, así que no hace falta conservarlo.
# Uso: bash pipeline/subir_video.sh ruta/video.mp4 nombre
set -euo pipefail
SRC="$(realpath "$1")"; NAME="$2"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
URL="$(git -C "$REPO" remote get-url origin)"
TMP="$(mktemp -d)"; cd "$TMP"
git init -q -b video && git remote add origin "$URL"
git config user.email "${GIT_EMAIL:-bot@olimpia.fits}"; git config user.name "${GIT_NAME:-Olimpia Bot}"
cp "$SRC" "$NAME.mp4"; git add "$NAME.mp4"; git commit -qm "Reel $NAME"
for i in 1 2 3 4; do git push -q -f origin video >/dev/null 2>&1 || true
  [ "$(git ls-remote origin refs/heads/video | cut -f1)" = "$(git rev-parse HEAD)" ] && break; sleep $((2**i)); done
[ "$(git ls-remote origin refs/heads/video | cut -f1)" = "$(git rev-parse HEAD)" ] || { echo "ERROR: push falló"; exit 1; }
RAW="https://raw.githubusercontent.com/cayetanoguerra08-commits/kdkd/video/$NAME.mp4"
for i in $(seq 1 12); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -I "$RAW"); [ "$code" = 200 ] && break; sleep 5; done
[ "$code" = 200 ] || { echo "ERROR: la URL raw no responde ($code)"; exit 1; }
echo "$RAW"

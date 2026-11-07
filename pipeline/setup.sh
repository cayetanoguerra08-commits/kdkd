#!/usr/bin/env bash
# Prepara todo lo necesario para renderizar un Reel. Seguro de ejecutar varias veces.
# Uso: bash pipeline/setup.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE="${KOKORO_DIR:-/mnt/project-files/pipeline-cache/kokoro}"
mkdir -p "$CACHE" 2>/dev/null || CACHE="$DIR/.kokoro"; mkdir -p "$CACHE"

python3 -c "import kokoro_onnx, soundfile" 2>/dev/null || \
  pip install -q --disable-pip-version-check kokoro-onnx soundfile 2>&1 | tail -2

REL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "$CACHE/$f" ] || [ "$(stat -c%s "$CACHE/$f")" -lt 20000000 ]; then
    echo "descargando $f ..."
    for i in 1 2 3; do curl -fsSL --retry 3 -o "$CACHE/$f.part" "$REL/$f" && mv "$CACHE/$f.part" "$CACHE/$f" && break; sleep $((i*3)); done
  fi
done

command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg; }
[ -f /usr/share/fonts/opentype/inter/Inter-Black.otf ] || apt-get install -y -qq fonts-inter >/dev/null 2>&1 || true
echo "KOKORO_DIR=$CACHE"
echo "OK setup"

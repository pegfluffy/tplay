#!/data/data/com.termux/files/usr/bin/bash
set -eu
: "${PREFIX:=${PREFIX:-/data/data/com.termux/files/usr}}"
BASE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
mkdir -p "$PREFIX/bin"
install -m 755 "$BASE/tplay/tplay.py" "$PREFIX/bin/tplay"
install -m 755 "$BASE/tpav/tpav.py" "$PREFIX/bin/tpav"
echo "Instalado: tplay e tpav em $PREFIX/bin"
echo "Dependências: pkg install termux-api ffmpeg vlc"

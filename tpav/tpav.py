#!/usr/bin/env python3
"""TPAV — frontend simples para VLC."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.1"

def main():
    parser = argparse.ArgumentParser(
        prog="tpav",
        description="TPAV — reproduz vídeos usando VLC; áudio ligado por padrão."
    )
    parser.add_argument("--version", action="version", version=f"TPAV {VERSION}")
    parser.add_argument("-n", "--no-audio", action="store_true",
                        help="Desativar o áudio do vídeo")
    parser.add_argument("file", help="Arquivo de vídeo")
    args = parser.parse_args()

    media = Path(args.file).expanduser()
    if not media.is_file():
        parser.error(f"arquivo não encontrado: {media}")

    vlc = shutil.which("cvlc") or shutil.which("vlc")
    if not vlc:
        print("tpav: VLC não encontrado. Instale com: pkg install vlc", file=sys.stderr)
        return 127

    cmd = [vlc, "--play-and-exit", "--no-video-title-show"]
    if args.no_audio:
        cmd.append("--no-audio")
    cmd.append(str(media.resolve()))
    try:
        return subprocess.run(cmd, check=False).returncode
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        print(f"tpav: não foi possível iniciar VLC: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""TPlay — player de áudio para Termux."""
from __future__ import annotations
import argparse
import configparser
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.3.1"
AUDIO_EXTS = {".mp3", ".ogg", ".oga", ".wav", ".m4a", ".aac", ".flac", ".opus", ".wma"}
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "tplay"
PLAYLIST_DIR = CONFIG_DIR / "playlists"
CONFIG_FILE = CONFIG_DIR / "config.ini"

def run(args, capture=False):
    try:
        return subprocess.run(args, check=False, text=True,
                              stdout=subprocess.PIPE if capture else None,
                              stderr=subprocess.PIPE if capture else None)
    except FileNotFoundError:
        return None

def config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PLAYLIST_DIR.mkdir(parents=True, exist_ok=True)
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE)
    if not c.has_section("player"):
        c["player"] = {"backend": "auto", "volume": "100"}
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            c.write(f)
    return c

def backend():
    choice = config().get("player", "backend", fallback="auto").lower()
    if choice in ("auto", "termux") and shutil.which("termux-media-player"):
        return "termux"
    if choice in ("auto", "pygame") and importlib_available("pygame"):
        return "pygame"
    if choice == "termux":
        raise RuntimeError("termux-media-player não encontrado. Instale termux-api.")
    if choice == "pygame":
        raise RuntimeError("pygame não instalado. Execute: pip install pygame")
    raise RuntimeError("Nenhum backend disponível. Instale termux-api ou pygame.")

def importlib_available(name):
    import importlib.util
    return importlib.util.find_spec(name) is not None

def pygame_module():
    import pygame
    return pygame

def play_file(path):
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")
    b = backend()
    if b == "termux":
        result = run(["termux-media-player", "play", str(p)])
        if result is None or result.returncode:
            raise RuntimeError("Falha ao iniciar termux-media-player.")
    else:
        pg = pygame_module()
        pg.mixer.init()
        pg.mixer.music.load(str(p))
        pg.mixer.music.play()
    print(f"TPlay: reproduzindo {p}")

def control(action):
    b = backend()
    if b == "termux":
        result = run(["termux-media-player", action])
        if result is None:
            raise RuntimeError("termux-media-player não encontrado.")
        if result.returncode:
            raise RuntimeError(f"Comando {action} falhou.")
    else:
        pg = pygame_module()
        if not pg.mixer.get_init():
            print("Nenhuma sessão pygame ativa neste processo.")
            return
        {"pause": pg.mixer.music.pause, "resume": pg.mixer.music.unpause,
         "stop": pg.mixer.music.stop}[action]()
    print(f"TPlay: {action}")

def show_status():
    if shutil.which("termux-media-player"):
        r = run(["termux-media-player", "info"], capture=True)
        if r:
            print((r.stdout or r.stderr or "Sem informações.").strip())
    else:
        print("Status detalhado disponível com termux-media-player (Termux:API).")

def metadata(path):
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(p)
    if shutil.which("ffprobe"):
        r = run(["ffprobe", "-v", "error", "-show_entries",
                 "format=duration:format_tags=title,artist,album",
                 "-of", "json", str(p)], capture=True)
        if r and r.returncode == 0:
            data = json.loads(r.stdout or "{}")
            fmt = data.get("format", {})
            tags = fmt.get("tags", {})
            print(f"Título: {tags.get('title', p.stem)}")
            print(f"Artista: {tags.get('artist', 'Desconhecido')}")
            print(f"Álbum: {tags.get('album', 'Desconhecido')}")
            try:
                print(f"Duração: {int(float(fmt.get('duration', 0)))} s")
            except (ValueError, TypeError):
                pass
            return
    print(f"Arquivo: {p.name}")
    print("Instale ffmpeg para ler metadados: pkg install ffmpeg")

def playlist_path(name):
    safe = Path(name).name
    if not safe or safe in (".", ".."):
        raise ValueError("Nome de playlist inválido.")
    return PLAYLIST_DIR / (safe if safe.endswith(".m3u") else safe + ".m3u")

def playlist_add(name, directory="."):
    target = playlist_path(name)
    folder = Path(directory).expanduser()
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    existing = set()
    if target.exists():
        existing = {line.strip() for line in target.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")}
    added = []
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            value = str(p.resolve())
            if value not in existing:
                added.append(value)
    with target.open("a", encoding="utf-8") as f:
        for item in added:
            f.write(item + "\n")
    print(f"{len(added)} arquivo(s) adicionado(s) em {target}")

def playlist_list():
    items = sorted(PLAYLIST_DIR.glob("*.m3u"))
    if not items:
        print("Nenhuma playlist criada.")
    for p in items:
        count = sum(1 for x in p.read_text(encoding="utf-8").splitlines()
                    if x.strip() and not x.startswith("#"))
        print(f"{p.stem}: {count} faixa(s)")

def playlist_play(name):
    p = playlist_path(name)
    if not p.exists():
        raise FileNotFoundError(f"Playlist não encontrada: {p}")
    tracks = [x.strip() for x in p.read_text(encoding="utf-8").splitlines()
              if x.strip() and not x.startswith("#")]
    if not tracks:
        raise RuntimeError("Playlist vazia.")
    # A API do Termux reproduz uma faixa por chamada; toca a primeira e informa
    # claramente que a fila automática não é suportada pelo backend.
    play_file(tracks[0])
    if len(tracks) > 1:
        print(f"Playlist contém {len(tracks)} faixas. Backend atual inicia a primeira; use um backend com fila para sequência automática.")

def set_volume(value):
    value = max(0, min(100, int(value)))
    c = config()
    c.set("player", "volume", str(value))
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        c.write(f)
    if shutil.which("termux-volume"):
        run(["termux-volume", "music", str(value)])
    print(f"Volume solicitado: {value}%")

def build_parser():
    p = argparse.ArgumentParser(prog="tplay", description="TPlay — player de áudio para Termux")
    p.add_argument("--version", action="version", version=f"TPlay {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("play", help="Reproduzir áudio"); q.add_argument("file")
    for name in ("stop", "pause", "resume"):
        sub.add_parser(name, help=f"{name.capitalize()} reprodução")
    sub.add_parser("home", help="Mostrar ajuda")
    sub.add_parser("status", help="Estado do player")
    sub.add_parser("now", help="Faixa atual (quando o backend fornece)")
    q = sub.add_parser("info", help="Metadados de um arquivo"); q.add_argument("file")
    q = sub.add_parser("volume", help="Definir volume"); q.add_argument("value", type=int)
    q = sub.add_parser("playlist", help="Gerenciar playlists")
    q.add_argument("name", nargs="?")
    q.add_argument("-a", "--add", action="store_true", help="Adicionar áudio da pasta atual")
    q.add_argument("--list", action="store_true")
    sub.add_parser("about", help="Sobre o TPlay")
    return p

def main():
    args = build_parser().parse_args()
    try:
        if args.command == "play": play_file(args.file)
        elif args.command in ("stop", "pause", "resume"): control(args.command)
        elif args.command == "home": build_parser().print_help()
        elif args.command == "status": show_status()
        elif args.command == "now": show_status()
        elif args.command == "info": metadata(args.file)
        elif args.command == "volume": set_volume(args.value)
        elif args.command == "playlist":
            if args.list: playlist_list()
            elif args.add:
                if not args.name: raise ValueError("Informe o nome: tplay playlist -a favoritos")
                playlist_add(args.name)
            elif args.name: playlist_play(args.name)
            else: playlist_list()
        elif args.command == "about":
            print(f"TPlay {VERSION} — player de áudio para Termux.")
            print(f"Configuração: {CONFIG_FILE}")
            print(f"Playlists: {PLAYLIST_DIR}")
    except (OSError, ValueError, RuntimeError) as e:
        print(f"tplay: erro: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

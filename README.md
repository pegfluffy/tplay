# TPlay + TPAV — reconstrução corrigida

Pacote reconstruído a partir das especificações recuperadas das conversas. **Não é uma cópia byte a byte do código perdido**: é uma implementação nova, compatível com Termux e organizada para evolução.

## Conteúdo

- `tplay/`: player de áudio para Termux, usando `termux-media-player` quando disponível e `pygame` como alternativa.
- `tpav/`: player de vídeo que controla o VLC; o áudio fica ligado por padrão.
- `install.sh`: instala os comandos `tplay` e `tpav` em `$PREFIX/bin`.

## Instalação no Termux

```sh
pkg update
pkg install python termux-api ffmpeg
# Para TPAV:
pkg install vlc
# Opcional: backend alternativo do TPlay
pip install pygame

unzip tplay_tpav_rebuild.zip
cd tplay_tpav_rebuild
bash install.sh
```

O app **Termux:API** também precisa estar instalado no Android para usar `termux-media-player`.

## TPlay

```sh
tplay play music.mp3
tplay pause
tplay resume
tplay stop
tplay home
tplay status
tplay now
tplay info music.mp3
tplay volume 70
tplay playlist -a favoritos
tplay playlist favoritos
tplay playlist --list
tplay about
```

As playlists ficam em `~/.config/tplay/playlists/`. Configuração em
`~/.config/tplay/config.ini`. O comando `playlist -a NOME` adiciona os arquivos
de áudio da pasta atual à playlist (sem duplicar caminhos).

O `termux-media-player` mantém a reprodução no serviço do Termux:API. Para
comandos de pause/resume/stop/volume, o backend precisa estar disponível.
`info` usa `ffprobe` se instalado.

## TPAV

```sh
tpav video.mp4
tpav "video com espaços.mp4"
tpav --no-audio video.mp4
tpav --version
```

TPAV usa VLC (`cvlc` ou `vlc`) em modo de terminal. Áudio é habilitado por
padrão; `--no-audio` desativa a faixa de áudio. `--` pode ser usado antes do
nome do arquivo para evitar que um nome iniciado por hífen seja interpretado
como opção.

## Observações

- Não requer root.
- O instalador não altera arquivos pessoais.
- Para remover, apague `tplay` e `tpav` de `$PREFIX/bin` e a pasta
  `~/.config/tplay` se também quiser remover configurações/playlists.

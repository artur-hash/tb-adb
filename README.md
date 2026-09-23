# tb-adb

Lista players NovaStar Taurus (TBs) na rede e liga/desliga o ADB via Wi-Fi/LAN — sem precisar do ViPlex e sem cabo.

## Como funciona

```
login REST (https :16674) -> liga o SSH (dropbear :1212) -> ssh root -> setprop adbd -> adb connect :5555
```

1. Faz login na API do player (`/terminal/core/v1/login`) com o SN e a senha da TB.
2. Pela API, desliga e religa o serviço SSH (o ciclo OFF→ON é necessário depois de um reboot).
3. Entra via SSH e liga o `adbd` em TCP na porta 5555.
4. Roda `adb connect <ip>:5555`.

## Requisitos

- Linux (veja [Limitações](#limitações))
- Python 3 (só biblioteca padrão, sem `pip install`)
- Cliente OpenSSH (`ssh`)
- `adb` (`sudo pacman -S android-tools` / `sudo apt install adb`)

## Instalação

```sh
git clone https://github.com/artur-hash/tb-adb.git
cd tb-adb
ln -s "$PWD/tb-adb" ~/.local/bin/tb-adb   # ~/.local/bin precisa estar no PATH
```

## Uso

```sh
tb-adb                      # menu interativo
tb-adb list                 # lista TBs (gateways + IPs já cadastrados)
tb-adb list --deep          # varre as sub-redes /24 locais procurando a porta 16674
tb-adb on  192.168.3.52     # liga o ADB e conecta
tb-adb off 192.168.3.52     # desliga o ADB
tb-adb shell 192.168.3.52   # shell SSH na TB
```

Na primeira vez que usar um IP, o script pede o **SN** (etiqueta do aparelho) e a **senha** de conexão (padrão `123456`) e salva em `~/.config/tb-adb/devices.json`.

> Esse arquivo guarda SNs e senhas das suas TBs — ele fica fora do repositório e não deve ser compartilhado.

### Senhas SSH

A senha do SSH pode ser diferente da de conexão. O script tenta, em ordem, e memoriza a que funcionar:

- senha salva anteriormente para aquele IP
- senha de conexão da TB
- `novastar2008` (fixa nos players rk356x/rk3328, ex.: T40 com Android 11)
- `123456`

## Problemas comuns

**`ConnectionRefusedError` / `Connection refused` logo no login**
O serviço da TB na porta 16674 ainda não subiu — normal logo depois de ligar/reiniciar a TB. Espere 1–2 minutos e tente de novo. Não é preciso cabo se a TB responde ao ping.

**`The handshake operation timed out` / `Connection reset by peer`**
Mesma causa: o serviço está no meio da inicialização.

**Via cabo USB**
Com a TB ligada por USB, ela aparece como gateway da interface USB (normalmente `192.168.42.129`) e o `tb-adb list` encontra sozinho.

## Limitações

Hoje funciona só no Linux:

- `ssh_run` usa `setsid -w` e um helper `#!/bin/sh` como `SSH_ASKPASS` — não existe no macOS nem no Windows.
- A descoberta usa `ip route` / `ip addr`; fora do Linux, o `list` só mostra IPs já cadastrados.
- `do_connect` usa `which adb`.

No Windows, dá para usar pelo **WSL**.

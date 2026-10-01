# tb-adb

Lista players NovaStar Taurus (TBs) na rede e liga/desliga o ADB via Wi-Fi/LAN — sem precisar do ViPlex e sem cabo. Funciona no Linux, macOS e Windows.

## Como funciona

```
busca UDP (como o ViPlex) -> login REST (https :16674) -> liga o SSH (dropbear :1212) -> ssh -> setprop adbd -> adb connect :5555
```

1. **Busca.** Manda o mesmo pedido UDP de 24 bytes que o ViPlex manda (portas 16601/16611), em unicast pra cada IP das sub-redes /24 locais (e pros gateways, já que a TB por USB vira o gateway da interface) e também em broadcast. A TB responde por unicast com um JSON (SN, nome, modelo, plataforma, tela). **Não precisa de login** — é assim que o `list` já mostra SN e nome sem senha nenhuma. Uma TB que não responder ao UDP ainda é achada pela varredura TCP da porta 16674, só com `list --deep` (mais lenta).

   Com um firewall local (ufw, firewalld, Windows Defender) ligado, respostas a um pedido em **broadcast** costumam ser descartadas pelo conntrack (ele não associa a resposta de um IP qualquer a um pedido mandado pra `255.255.255.255`). Por isso a busca manda o pedido também em **unicast** pra cada IP candidato — essas respostas passam pelo firewall normalmente.
2. Faz login na API do player (`/terminal/core/v1/login`) com o SN (achado na busca) e a senha da TB. Se o serviço da TB ainda estiver subindo (logo depois de ligar/reiniciar), espera até 120 s.
3. Pela API, desliga e religa o serviço SSH (o ciclo OFF→ON é necessário depois de um reboot).
4. Entra via SSH e liga o `adbd` em TCP na porta 5555.
5. Roda `adb connect <ip>:5555`.

## Requisitos

| | Linux | macOS | Windows |
|---|---|---|---|
| Python 3 | ✅ | ✅ | ✅ ([python.org](https://www.python.org/downloads/)) |
| SSH | cliente OpenSSH (`ssh`) | já vem no sistema | `pip install "paramiko<4"` |
| `adb` | `sudo pacman -S android-tools` / `sudo apt install adb` | `brew install android-platform-tools` | `winget install Google.PlatformTools` |

No Linux/macOS o script usa só a biblioteca padrão do Python — sem `pip install`.

> **Por que `paramiko<4` no Windows?** O dropbear das TBs só aceita host key `ssh-rsa` (SHA-1) — a `ecdsa` dele está quebrada. O paramiko 4+ removeu o `ssh-rsa`.

## Instalação

**Linux / macOS**

```sh
git clone https://github.com/artur-hash/tb-adb.git ~/code/tb-adb
ln -s ~/code/tb-adb/tb-adb ~/.local/bin/tb-adb   # ~/.local/bin precisa estar no PATH
```

**Windows**

```bat
git clone https://github.com/artur-hash/tb-adb.git %USERPROFILE%\tb-adb
pip install "paramiko<4"
```

Depois coloque a pasta `%USERPROFILE%\tb-adb` no PATH — o `tb-adb.cmd` permite rodar `tb-adb ...` direto no terminal. Sem mexer no PATH: `python tb-adb on 192.168.3.52` de dentro da pasta.

## Uso

```sh
tb-adb                          # menu interativo
tb-adb list                     # busca UDP (como o ViPlex): gateways + IPs cadastrados + sub-redes /24 locais
tb-adb list --deep              # busca UDP + varredura TCP da porta 16674 (acha o que não respondeu ao UDP)
tb-adb on  192.168.3.52         # liga o ADB e conecta (aceita IP)
tb-adb on  25A22N000000741      # ... ou SN
tb-adb on  Taurus-00000741      # ... ou aliasName (nome que aparece no ViPlex)
tb-adb on  00000741             # ... ou um sufixo único do SN/nome
tb-adb off 192.168.3.52         # desliga o ADB
tb-adb shell 192.168.3.52       # shell SSH na TB
tb-adb shell 192.168.3.52 "getprop ro.product.model"   # roda um comando
```

`on`, `off` e `shell` aceitam `--wait S` (segundos esperando o serviço da TB subir; padrão 120). Um alvo que não é IP é resolvido pela busca UDP; se ficar ambíguo (o sufixo bater em mais de uma TB) ou não achar nada, o erro lista as TBs candidatas.

O cadastro (`~/.config/tb-adb/devices.json`) é **por SN**, não por IP — assim uma TB não perde o cadastro quando troca de IP (USB, DHCP). Na primeira vez que uma TB é usada, o script já sabe o **SN** e o **nome** pela própria busca (sem pedir nada). Pra senha, tenta logar com a salva anteriormente; se a TB recusar (SN/senha errados), tenta as **senhas padrão do cadastro** e depois a `123456`; só se todas forem recusadas é que pergunta a senha no terminal.

As senhas padrão ficam numa lista `default_passwords` no próprio `devices.json`, nunca no código (o repositório é público). Serve para TBs novas, que ainda estão com a senha de fábrica:

```json
{"version": 2, "default_passwords": ["<senha de fábrica da NovaStar>"], "devices": {}}
``` Um erro de rede (TB desligada, fora do alcance) não entra nesse ciclo — ele aparece na hora, sem tentar as outras senhas à toa. O `last_ip` (o IP que funcionou da última vez) é salvo a cada operação bem-sucedida, só pra acelerar a próxima busca.

> Esse arquivo guarda SNs e senhas das suas TBs — ele fica fora do repositório, é gravado com permissão `0600` (só o dono lê) e não deve ser compartilhado. Um cadastro antigo (chave por IP) é convertido para o formato por SN automaticamente na primeira gravação; antes disso, o arquivo antigo é copiado para `devices.json.bak`.

No Windows, o `shell` interativo usa o `ssh.exe` do sistema e mostra a senha para você digitar.

### Senhas SSH

A senha do SSH pode ser diferente da de conexão. O script tenta, em ordem, e memoriza a que funcionar:

- senha salva anteriormente para aquele IP
- senha de conexão da TB
- `novastar2008` (fixa nos players rk356x/rk3328, ex.: T40 com Android 11)
- `123456`

### Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `TB_ADB_DEBUG=1` | mostra o traceback completo em vez da mensagem curta de erro |
| `TB_ADB_SSH=openssh` / `paramiko` | força o backend de SSH (ex.: testar o caminho do Windows no Linux) |

## Problemas comuns

**`servico da TB ainda nao respondeu (... Connection refused)`**
O serviço da TB na porta 16674 ainda não subiu — normal logo depois de ligar/reiniciar a TB. O script espera sozinho até 120 s. Se estourar o tempo, confira se a TB está ligada e na mesma rede (`ping <ip>`). Não é preciso cabo se a TB responde ao ping.

**`TB em <ip> nao respondeu a busca`**
Logo após reiniciar, a TB pode demorar um pouco para responder à busca UDP. Se o cadastro já tiver essa TB com esse IP como último conhecido, o script usa o SN dela automaticamente (sem perguntar); só pede os dados se não achar (ou achar mais de uma) correspondência.

**`sn not match` / `credenciais invalidas para <ip>`**
A TB recusou o SN/senha. Isso normalmente se resolve sozinho: o script já tenta a senha salva e depois a padrão (`123456`) antes de perguntar. Se aparecer esse erro é porque a senha digitada na hora também foi recusada — confira a etiqueta da TB e tente de novo, ou corrija/apague a entrada em `~/.config/tb-adb/devices.json` (chave = SN).

**`paramiko X nao suporta ssh-rsa`**
Instale uma versão compatível: `pip install "paramiko<4"`.

**Via cabo USB**
Com a TB ligada por USB, ela aparece como gateway da interface USB (normalmente `192.168.42.129`) e o `tb-adb list` encontra sozinho.

## Testado

- Linux (Arch) + TB T2-4G (rk312x): `list`, `on`, `off`, `shell` (interativo e com comando) usando o ssh do sistema; `on` e `off` usando paramiko 3.5.1 (o backend do Windows).
- Busca UDP: testada ao vivo numa rede com 10 TBs (T2, T10Plus, T20Plus, T40, T60) atrás do ViPlex — `list` (sem `--deep`) achou as 10 em poucos segundos, todas por UDP.
- macOS e Windows: a descoberta de rede foi testada com saídas de exemplo de `netstat`/`ifconfig` e `route print` (inclusive Windows em português). Ainda falta rodar numa máquina macOS/Windows de verdade — se você testar, conte numa issue.

## Contribuindo

Issues e pull requests são bem-vindos — veja o [CONTRIBUTING.md](CONTRIBUTING.md). Relatos de teste em outros modelos de TB e no macOS/Windows ajudam muito.

## Aviso

Projeto independente, sem vínculo com a NovaStar. Use apenas em players que você administra. As senhas no código são os padrões de fábrica dos players; se as suas TBs usam outras, o script pergunta e guarda localmente.

## Licença

[MIT](LICENSE)

# Contribuindo com o tb-adb

Contribuições são bem-vindas: correções, suporte a outros modelos de TB, melhorias no macOS/Windows, documentação.

## Reportando um problema

Abra uma [issue](https://github.com/artur-hash/tb-adb/issues) com:

- modelo da TB (ex.: T2-4G, T40) e, se souber, a versão do Android/firmware
- seu sistema (Linux/macOS/Windows) e a versão do Python
- o comando que rodou e a saída completa com `TB_ADB_DEBUG=1`, por exemplo:
  ```sh
  TB_ADB_DEBUG=1 tb-adb on 192.168.x.x
  ```

**Antes de colar a saída, apague o SN e as senhas da sua TB.** Nunca anexe o `~/.config/tb-adb/devices.json`.

## Enviando uma mudança

1. Faça um fork e crie uma branch.
2. Faça a mudança e teste numa TB de verdade sempre que possível.
3. Abra um pull request dizendo **o que** mudou, **por quê** e **em qual modelo de TB/sistema** você testou.

### Princípios do projeto

- **Um arquivo só.** O `tb-adb` é um script único, fácil de copiar e rodar.
- **Só biblioteca padrão no Linux/macOS.** A única dependência externa é o `paramiko<4`, e só no Windows.
- **Sem dados reais no repositório.** Nada de SNs, senhas das suas TBs, IPs de clientes ou tokens, nem em código, nem em teste, nem em commit.
- **Comentários e mensagens em português, sem acentos no código** (evita problema de encoding em terminais do Windows).

### Testando

```sh
python3 -m py_compile tb-adb                                  # sintaxe
tb-adb list && tb-adb on <ip> && tb-adb off <ip>              # fluxo completo numa TB

# caminho do Windows (paramiko) rodando no Linux/macOS:
pip install "paramiko<4"
TB_ADB_SSH=paramiko python3 tb-adb on <ip>
```

Para mudanças na descoberta de rede (`_net_linux`, `_net_mac`, `_net_win`), teste as funções com a saída real dos comandos (`ip`, `netstat`/`ifconfig`, `route print`) do sistema em questão e cole um exemplo no PR.

## Licença

Ao contribuir, você concorda que sua contribuição será licenciada sob a [licença MIT](LICENSE) do projeto.

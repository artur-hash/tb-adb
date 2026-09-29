# Testes de unidade do tb-adb (so as funcoes puras: parse_avon, migrate_registry,
# resolve_target). Carrega o script sem extensao via SourceFileLoader.
import json
import struct
import unittest
from importlib.machinery import SourceFileLoader

tbadb = SourceFileLoader("tbadb", "tb-adb").load_module()


def avon_reply(payload: dict, garbage: bytes = b"") -> bytes:
    """Monta uma resposta AVON valida: cabecalho de 24 bytes + JSON + lixo opcional."""
    body = json.dumps(payload).encode("utf-8")
    header = (
        b"AVON"
        + b"\xff\xff\xff\xff"
        + b"\x55\x88"
        + b"\x01\x00"
        + b"\x00\x00\x00\x00"
        + struct.pack("<I", len(body))
        + b"\x00\x00\x00\x00"
    )
    return header + body + garbage


REAL_TB2 = {
    "aliasName": "T2-4G_10015909", "encodeType": 0, "ftpPort": 16602, "height": 256,
    "key": "novaStar", "logined": False, "loginedUsernames": [""], "modelId": 38411,
    "platform": "rk312x", "privacy": True, "productName": "T2-4G", "rotation": 0,
    "sn": "2ZTA53831N2A10015909", "syssetFtpPort": 16604, "syssetTcpPort": 16607,
    "tcpPort": 16606, "terminalEntrancePortHttps": 16674,
    "terminalEntrancePortWebSocket": 16675, "width": 192,
}


class TestParseAvon(unittest.TestCase):
    def test_resposta_real_da_tb2(self):
        info = tbadb.parse_avon(avon_reply(REAL_TB2))
        self.assertIsNotNone(info)
        self.assertEqual(info["sn"], "2ZTA53831N2A10015909")
        self.assertEqual(info["aliasName"], "T2-4G_10015909")
        self.assertEqual(info["productName"], "T2-4G")
        self.assertEqual(info["width"], 192)
        self.assertEqual(info["height"], 256)

    def test_lixo_depois_do_json_e_ignorado(self):
        info = tbadb.parse_avon(avon_reply(REAL_TB2, garbage=b"\x00\x01lixolixolixo"))
        self.assertIsNotNone(info)
        self.assertEqual(info["sn"], "2ZTA53831N2A10015909")

    def test_cabecalho_errado_devolve_none(self):
        data = avon_reply(REAL_TB2)
        ruim = b"XXXX" + data[4:]
        self.assertIsNone(tbadb.parse_avon(ruim))

    def test_tamanho_maior_que_os_dados_devolve_none(self):
        data = bytearray(avon_reply(REAL_TB2))
        data[16:20] = struct.pack("<I", 999999)
        self.assertIsNone(tbadb.parse_avon(bytes(data)))

    def test_json_quebrado_devolve_none(self):
        header = (
            b"AVON" + b"\xff\xff\xff\xff" + b"\x55\x88" + b"\x01\x00" + b"\x00\x00\x00\x00"
        )
        body = b"{nao e json valido"
        data = header + struct.pack("<I", len(body)) + b"\x00\x00\x00\x00" + body
        self.assertIsNone(tbadb.parse_avon(data))

    def test_dados_curtos_demais_devolvem_none(self):
        self.assertIsNone(tbadb.parse_avon(b"AVON"))


OLD_REGISTRY = {
    "192.169.238.95": {"sn": "25A22N000000741", "password": "senhaA", "name": ""},
    "192.169.185.230": {"sn": "25A22N000000741", "password": "senhaA", "ssh_password": "novastar2008"},
    "192.169.4.60": {"sn": "25A22N000000741"},
    "192.168.3.54": {"sn": "25A22N000000741", "name": "TB40-Recepcao"},
    "192.168.3.52": {"sn": "2ZTA53831N2A10015909", "password": "senhaB", "name": "TB2-Sala"},
}


class TestMigrateRegistry(unittest.TestCase):
    def test_agrupa_por_sn_e_usa_last_ip_da_192_168(self):
        novo = tbadb.migrate_registry(OLD_REGISTRY)
        self.assertEqual(novo["version"], 2)
        devs = novo["devices"]
        self.assertEqual(len(devs), 2)
        t40 = devs["25A22N000000741"]
        self.assertEqual(t40["last_ip"], "192.168.3.54")

    def test_senhas_sao_preservadas(self):
        novo = tbadb.migrate_registry(OLD_REGISTRY)
        t40 = novo["devices"]["25A22N000000741"]
        self.assertEqual(t40["password"], "senhaA")
        self.assertEqual(t40["ssh_password"], "novastar2008")
        self.assertEqual(t40["name"], "TB40-Recepcao")
        t2 = novo["devices"]["2ZTA53831N2A10015909"]
        self.assertEqual(t2["password"], "senhaB")
        self.assertEqual(t2["last_ip"], "192.168.3.52")

    def test_formato_v2_passa_intacto(self):
        v2 = {"version": 2, "devices": {"SN1": {"password": "x", "last_ip": "192.168.1.1"}}}
        self.assertEqual(tbadb.migrate_registry(v2), v2)

    def test_registro_vazio(self):
        self.assertEqual(tbadb.migrate_registry({}), {"version": 2, "devices": {}})

    def test_entrada_sem_sn_e_ignorada(self):
        novo = tbadb.migrate_registry({"192.168.3.1": {"password": "x"}})
        self.assertEqual(novo["devices"], {})


FOUND = {
    "192.168.3.52": {"sn": "2ZTA53831N2A10015909", "aliasName": "TB2-Recepcao", "productName": "T2-4G"},
    "192.168.3.54": {"sn": "25A22N000000741", "aliasName": "Sala1-Deposito", "productName": "T40"},
    "192.168.3.60": {"sn": "25A22N000000999", "aliasName": "Sala2-Deposito", "productName": "T40"},
}


class TestResolveTarget(unittest.TestCase):
    def test_acha_por_ip(self):
        self.assertEqual(tbadb.resolve_target(FOUND, "192.168.3.54"), "192.168.3.54")

    def test_ip_nao_encontrado_passa_direto(self):
        # um IP e sempre um alvo valido, mesmo que a busca nao tenha achado a TB
        self.assertEqual(tbadb.resolve_target(FOUND, "192.168.3.99"), "192.168.3.99")

    def test_acha_por_sn_exato(self):
        self.assertEqual(tbadb.resolve_target(FOUND, "2ZTA53831N2A10015909"), "192.168.3.52")

    def test_acha_por_nome_exato(self):
        self.assertEqual(tbadb.resolve_target(FOUND, "Sala1-Deposito"), "192.168.3.54")

    def test_acha_por_sufixo_unico_do_sn(self):
        self.assertEqual(tbadb.resolve_target(FOUND, "00000741"), "192.168.3.54")

    def test_sufixo_ambiguo_gera_erro(self):
        # "Deposito" e sufixo do aliasName dos dois T40 (.54 e .60)
        with self.assertRaises(Exception):
            tbadb.resolve_target(FOUND, "Deposito")

    def test_sufixo_nao_encontrado_gera_erro(self):
        with self.assertRaises(Exception):
            tbadb.resolve_target(FOUND, "naoexiste")

    def test_erro_lista_candidatos(self):
        try:
            tbadb.resolve_target(FOUND, "Deposito")
        except Exception as e:
            msg = str(e)
            self.assertIn("192.168.3.54", msg)
            self.assertIn("192.168.3.60", msg)
        else:
            self.fail("deveria ter levantado erro de ambiguidade")


if __name__ == "__main__":
    unittest.main()

import copy
import unittest
import threading
from unittest.mock import patch
from app import create_app
from blockchain import Billetera, Cadena, Nodo, RECOMPENSA, crear_transaccion, hash_bloque, verificar_firma


class Pruebas(unittest.TestCase):
    def setUp(self):
        self.c = Cadena(1)
        self.b = Billetera()

    def registrar(self, equipo="Microscopio", accion="prestar", responsable="Ana"):
        tx = crear_transaccion(self.b, equipo, accion, responsable)
        self.c.registrar(tx, self.b.firmar(tx))
        return tx

    def minar(self):
        self.c.iniciar_mineria()
        self.c.esperar()

    def test_hash_determinista_y_minero_sellado(self):
        b = {"numero": 1, "minero": "Nodo 0", "nonce": 2}
        self.assertEqual(hash_bloque(b), hash_bloque(dict(reversed(list(b.items())))))
        self.assertEqual(hash_bloque(b), hash_bloque({**b, "hash": "ignorado"}))
        self.assertNotEqual(hash_bloque(b), hash_bloque({**b, "minero": "Nodo 1"}))

    def test_firma_ed25519_real_y_alterada(self):
        tx = crear_transaccion(self.b, "Equipo", "prestar", "Ana")
        firma = self.b.firmar(tx)
        self.assertTrue(verificar_firma(tx, firma))
        tx["contenido"]["equipo"] = "Otro"
        self.assertFalse(verificar_firma(tx, firma))
        self.assertFalse(verificar_firma({}, "xyz"))
        with self.assertRaises(ValueError):
            self.c.registrar(tx, firma)

    def test_tres_bloques_carrera_saldos_y_nonces(self):
        for i in range(3):
            self.registrar(f"Equipo {i}")
            self.minar()
            self.assertEqual(len(self.c.bloques), i + 2)
            self.assertEqual(sum(n.saldo for n in self.c.nodos), (i + 1) * RECOMPENSA)
            self.assertTrue(self.c.fin.is_set())
            self.assertTrue(all(not t.is_alive() for t in self.c.hilos))
            self.assertIsNone(self.c.pendiente)
            self.assertTrue(self.c.es_valida())
            for n in self.c.nodos:
                if n.nonce is not None:
                    self.assertEqual(n.nonce % 4, n.i)
                    self.assertEqual(n.nonce, n.i + (n.intentos - 1) * 4)

    def test_alteraciones_y_genesis(self):
        self.registrar(); self.minar()
        originales = copy.deepcopy(self.c.bloques)
        for campo, valor in [("hash", "f" * 64), ("firma", "0" * 128), ("hash_anterior", "f" * 64), ("numero", 8), ("minero", "Intruso")]:
            self.c.bloques = copy.deepcopy(originales)
            self.c.bloques[1][campo] = valor
            self.assertFalse(self.c.es_valida(), campo)
        self.c.bloques = copy.deepcopy(originales)
        self.c.bloques[1]["transaccion"]["contenido"]["equipo"] = "Alterado"
        self.assertFalse(self.c.es_valida())
        self.c.bloques = copy.deepcopy(originales)
        self.c.bloques[0]["hash_anterior"] = "f" * 64
        self.assertFalse(self.c.es_valida())

    def test_regla_prestamo_devolucion_y_autoria(self):
        self.registrar(); self.minar()
        with self.assertRaises(ValueError): self.registrar()
        otro = Billetera()
        tx = crear_transaccion(otro, "Microscopio", "devolver", "Ana")
        with self.assertRaises(ValueError): self.c.registrar(tx, otro.firmar(tx))
        self.registrar(accion="devolver"); self.minar()
        self.registrar(); self.minar()
        self.assertTrue(self.c.es_valida())

    def test_firma_invalida_rechazada_antes_de_minar(self):
        self.registrar()
        self.c.pendiente["firma"] = "0" * 128
        with self.assertRaises(ValueError): self.c.iniciar_mineria()
        self.assertFalse(self.c.estado["minando"])
        self.assertEqual(len(self.c.bloques), 1)

    def test_no_permite_segunda_carrera_ni_transaccion_durante_mineria(self):
        self.registrar()
        liberar = threading.Event()
        original = Nodo.minar
        def pausado(nodo, *args):
            liberar.wait(5)
            original(nodo, *args)
        with patch.object(Nodo, "minar", pausado):
            self.c.iniciar_mineria()
            try:
                with self.assertRaises(ValueError): self.c.iniciar_mineria()
                with self.assertRaises(ValueError): self.registrar("Otro")
            finally:
                liberar.set()
                self.c.esperar()
        self.assertEqual(len(self.c.bloques), 2)
        self.assertEqual(sum(n.saldo for n in self.c.nodos), RECOMPENSA)

    def test_contenido_invalido_y_devolucion_sin_prestamo(self):
        for equipo, accion in [("", "prestar"), ("Equipo", "inventada"), ("Equipo", "devolver")]:
            with self.assertRaises(ValueError): self.registrar(equipo, accion)
        self.assertIsNone(self.c.pendiente)

    def test_flask_flujo_y_alteracion(self):
        app = create_app(self.c)
        cliente = app.test_client()
        self.assertEqual(cliente.get("/").status_code, 200)
        from blockchain import PROPOSITO
        r = cliente.post("/transaccion", data={"usuario": "Cavazos", "proposito": PROPOSITO, "equipo": "Osciloscopio", "accion": "prestar", "responsable": "Cavazos"})
        self.assertEqual(r.status_code, 302)
        cliente.post("/minar"); self.c.esperar()
        self.assertTrue(cliente.get("/estado").json["valida"])
        cliente.post("/alterar")
        self.assertFalse(cliente.get("/estado").json["valida"])
        cliente.post("/restaurar")
        self.assertTrue(cliente.get("/estado").json["valida"])


if __name__ == "__main__":
    unittest.main()

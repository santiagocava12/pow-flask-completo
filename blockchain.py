"""Simulador educativo: Ed25519, SHA-256 y carrera de cuatro hilos."""
import copy
import hashlib
import json
import threading
import time
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization as ser
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

DIFICULTAD = 5
RECOMPENSA = 50
PROPOSITO = "Préstamos de equipo de laboratorio"


def serializar(d):
    return json.dumps(d, sort_keys=True).encode()


def sha256(d):
    return hashlib.sha256(serializar(d)).hexdigest()


def hash_bloque(b):
    return sha256({k: v for k, v in b.items() if k != "hash"})


class Billetera:
    def __init__(self):
        self.privada = Ed25519PrivateKey.generate()
        self.publica = self.privada.public_key().public_bytes(ser.Encoding.Raw, ser.PublicFormat.Raw).hex()

    def firmar(self, tx):
        return self.privada.sign(serializar(tx)).hex()


def verificar_firma(tx, firma):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(tx["remitente"])).verify(bytes.fromhex(firma), serializar(tx))
        return True
    except (InvalidSignature, ValueError, TypeError, KeyError, AttributeError):
        return False


def validar_regla(tx, bloques):
    if tx.get("proposito") != PROPOSITO:
        raise ValueError("El propósito no corresponde al registro de laboratorio.")
    c = tx.get("contenido")
    if not isinstance(c, dict) or set(c) != {"equipo", "accion", "responsable"}:
        raise ValueError("Se requieren equipo, acción y responsable.")
    if any(not isinstance(c[k], str) or not c[k].strip() or len(c[k]) > 100 for k in c):
        raise ValueError("Los campos deben tener entre 1 y 100 caracteres.")
    if c["accion"] not in ("prestar", "devolver"):
        raise ValueError("Acción no reconocida.")
    ultimo = None
    for b in bloques[1:]:
        previo = b["transaccion"]["contenido"]
        if previo["equipo"] == c["equipo"]:
            ultimo = b["transaccion"]
    ocupado = ultimo is not None and ultimo["contenido"]["accion"] == "prestar"
    if c["accion"] == "prestar" and ocupado:
        raise ValueError("Este equipo ya está prestado; primero debe devolverse.")
    if c["accion"] == "devolver":
        if not ocupado:
            raise ValueError("Este equipo no tiene un préstamo activo.")
        if ultimo["remitente"] != tx["remitente"] or ultimo["contenido"]["responsable"] != c["responsable"]:
            raise ValueError("Solo quien registró el préstamo puede registrar su devolución.")


class Nodo:
    def __init__(self, i, n):
        self.i, self.n = i, n
        self.nombre = f"Nodo {i}"
        self.saldo = self.intentos = 0
        self.ultimo = ""
        self.nonce = None

    def minar(self, bloque, cadena, fin, estado, candado, barrera):
        barrera.wait()
        nonce = self.i
        while not fin.is_set():
            bloque["nonce"] = nonce
            h = hash_bloque(bloque)
            with candado:
                self.intentos += 1
                self.ultimo, self.nonce = h, nonce
            if h.startswith("0" * cadena.dificultad):
                with candado:
                    if fin.is_set():
                        return
                    bloque["hash"] = h
                    cadena.bloques.append(copy.deepcopy(bloque))
                    self.saldo += RECOMPENSA
                    cadena.pendiente = None
                    estado["ganador"] = self.nombre
                    estado["segundos"] = time.perf_counter() - estado["inicio"]
                    fin.set()
                return
            nonce += self.n


class Cadena:
    def __init__(self, dificultad=DIFICULTAD):
        if type(dificultad) is not int or not 1 <= dificultad <= 6:
            raise ValueError("La dificultad debe estar entre 1 y 6.")
        self.dificultad = dificultad
        genesis = {"numero": 0, "nonce": 0, "transaccion": None, "firma": "", "hash_anterior": "0" * 64, "minero": "Génesis"}
        genesis["hash"] = hash_bloque(genesis)
        self.bloques = [genesis]
        self.pendiente = None
        self.nodos = [Nodo(i, 4) for i in range(4)]
        self.candado = threading.RLock()
        self.fin = threading.Event()
        self.hilos = []
        self.estado = {"minando": False, "ganador": None, "segundos": 0}

    def registrar(self, tx, firma):
        with self.candado:
            if self.estado["minando"] or self.pendiente:
                raise ValueError("Termina la transacción pendiente antes de registrar otra.")
            if not self.es_valida():
                raise ValueError("La cadena es inválida.")
            if not verificar_firma(tx, firma):
                raise ValueError("Firma inválida.")
            validar_regla(tx, self.bloques)
            self.pendiente = {"transaccion": copy.deepcopy(tx), "firma": firma}

    def iniciar_mineria(self):
        with self.candado:
            if self.estado["minando"]:
                raise ValueError("Ya hay una carrera en curso.")
            if not self.pendiente:
                raise ValueError("Primero registra una transacción.")
            if not self.es_valida():
                raise ValueError("La cadena es inválida.")
            tx, firma = self.pendiente["transaccion"], self.pendiente["firma"]
            if not verificar_firma(tx, firma):
                raise ValueError("Firma inválida: no se inicia la minería.")
            validar_regla(tx, self.bloques)
            self.fin.clear()
            self.estado.update(minando=True, ganador=None, segundos=0, inicio=time.perf_counter())
            barrera = threading.Barrier(len(self.nodos))
            self.hilos = []
            for nodo in self.nodos:
                nodo.intentos, nodo.ultimo, nodo.nonce = 0, "", None
                bloque = {"numero": len(self.bloques), "nonce": nodo.i, "transaccion": copy.deepcopy(tx), "firma": firma, "hash_anterior": self.bloques[-1]["hash"], "minero": nodo.nombre}
                self.hilos.append(threading.Thread(target=nodo.minar, args=(bloque, self, self.fin, self.estado, self.candado, barrera), daemon=True))
            for hilo in self.hilos:
                hilo.start()
            threading.Thread(target=self._esperar, args=(list(self.hilos),), daemon=True).start()

    def _esperar(self, hilos):
        for hilo in hilos:
            hilo.join()
        with self.candado:
            self.estado["minando"] = False

    def esperar(self):
        for hilo in self.hilos:
            hilo.join()
        with self.candado:
            self.estado["minando"] = False

    def es_valida(self):
        with self.candado:
            try:
                g = self.bloques[0]
                if g["numero"] != 0 or g["hash_anterior"] != "0" * 64 or g["hash"] != hash_bloque(g) or g["transaccion"] is not None or g["minero"] != "Génesis" or g["nonce"] != 0 or g["firma"] != "":
                    return False
                for i, b in enumerate(self.bloques[1:], 1):
                    if b["numero"] != i or type(b["nonce"]) is not int or b["nonce"] < 0 or b["minero"] not in [n.nombre for n in self.nodos]:
                        return False
                    if b["hash_anterior"] != self.bloques[i - 1]["hash"] or b["hash"] != hash_bloque(b) or not b["hash"].startswith("0" * self.dificultad):
                        return False
                    if not verificar_firma(b["transaccion"], b["firma"]):
                        return False
                    validar_regla(b["transaccion"], self.bloques[:i])
                return True
            except (KeyError, TypeError, ValueError, IndexError, AttributeError):
                return False

    def resumen(self):
        with self.candado:
            return {"minando": self.estado["minando"], "ganador": self.estado["ganador"], "segundos": self.estado["segundos"], "dificultad": self.dificultad, "valida": self.es_valida(), "nodos": [{"nombre": n.nombre, "intentos": n.intentos, "ultimo": n.ultimo, "nonce": n.nonce, "saldo": n.saldo} for n in self.nodos]}


def crear_transaccion(billetera, equipo, accion, responsable):
    return {"proposito": PROPOSITO, "remitente": billetera.publica, "contenido": {"equipo": equipo.strip(), "accion": accion, "responsable": responsable.strip()}, "hora": datetime.now(timezone.utc).isoformat()}

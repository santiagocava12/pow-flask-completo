"""Mediciones reales de carreras, incluye los cuatro hilos y su sincronización."""
import argparse
import csv
import json
import platform
import statistics
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blockchain import Billetera, Cadena, crear_transaccion


def ejecutar(repeticiones):
    filas = []
    for dificultad in (3, 4, 5):
        for repeticion in range(1, repeticiones + 1):
            c, b = Cadena(dificultad), Billetera()
            tx = crear_transaccion(b, "Microscopio", "prestar", "Prueba")
            c.registrar(tx, b.firmar(tx))
            inicio = time.perf_counter()
            c.iniciar_mineria(); c.esperar()
            segundos = time.perf_counter() - inicio
            assert c.es_valida()
            filas.append({"dificultad": dificultad, "repeticion": repeticion, "segundos": segundos, "intentos": sum(n.intentos for n in c.nodos), "ganador": c.estado["ganador"], "nonce": c.bloques[-1]["nonce"], "hash": c.bloques[-1]["hash"]})
            print(f"D={dificultad}, prueba {repeticion}: {segundos:.3f} s", flush=True)
    destino = Path(__file__).resolve().parents[1] / "output"
    destino.mkdir(exist_ok=True)
    with (destino / "mediciones.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys()); w.writeheader(); w.writerows(filas)
    resumen = {"entorno": {"python": platform.python_version(), "sistema": platform.platform(), "procesador": platform.processor(), "nodos": 4, "repeticiones": repeticiones}, "resultados": [{"dificultad": d, "promedio_s": statistics.mean(f["segundos"] for f in filas if f["dificultad"] == d), "min_s": min(f["segundos"] for f in filas if f["dificultad"] == d), "max_s": max(f["segundos"] for f in filas if f["dificultad"] == d), "promedio_intentos": statistics.mean(f["intentos"] for f in filas if f["dificultad"] == d)} for d in (3, 4, 5)]}
    (destino / "mediciones.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--repeticiones", type=int, default=5)
    args = parser.parse_args()
    if args.repeticiones < 1: parser.error("Usa al menos una repetición.")
    ejecutar(args.repeticiones)

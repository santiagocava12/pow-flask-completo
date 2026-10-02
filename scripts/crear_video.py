"""Video de 180 s con capturas reales de la app y subtítulos (sin audio).
Las carreras se resumen en segmentos de 15 s; no representa su duración real.
"""
import copy
import io
import json
import logging
import sys
import threading
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from blockchain import Cadena
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as BrowserTimeout
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
TMP = ROOT / "tmp" / "video"
TMP.mkdir(parents=True, exist_ok=True)


def ejecutar():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    cadena = Cadena(5)
    app = create_app(cadena)
    server = make_server("127.0.0.1", 5051, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    escenas = []
    evidencia = []
    def capturar(page):
        for intento in range(4):
            try:
                return page.screenshot(timeout=10000, animations="disabled")
            except BrowserTimeout:
                if intento == 3:
                    raise
                page.wait_for_load_state("domcontentloaded")
    def escena(frames, segundos, titulo, subtitulo):
        escenas.append((frames, segundos, titulo, subtitulo))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
            page.goto("http://127.0.0.1:5051")
            page.screenshot(path=str(OUT / "interfaz.png"), full_page=True)
            escena([capturar(page)], 15, "Préstamos de equipo de laboratorio", "Demostración automatizada de la app real · Ed25519 + SHA-256 · Sin audio")
            escena([capturar(page)], 10, "Un registro que impide préstamos duplicados", "Cada transacción contiene propósito, remitente, contenido y hora. La llave privada la firma.")
            for i, equipo in enumerate(("Microscopio 01", "Osciloscopio 02", "Multímetro 03"), 1):
                page.evaluate("window.scrollTo(0,0)")
                page.locator('[name="equipo"]').fill(equipo)
                page.locator('[name="responsable"]').fill("Cavazos")
                page.get_by_role("button", name="Firmar transacción").click()
                escena([capturar(page)], 8, f"Bloque {i}: transacción firmada", f"Se registra el préstamo de {equipo}. La firma se verifica antes de iniciar la carrera.")
                page.get_by_role("button", name="Iniciar carrera de minería").click()
                page.get_by_role("heading", name="3. Nodos en vivo").scroll_into_view_if_needed()
                capturas = [capturar(page)]
                while cadena.resumen()["minando"]:
                    time.sleep(.3)
                    page.get_by_role("heading", name="3. Nodos en vivo").scroll_into_view_if_needed()
                    capturas.append(capturar(page))
                page.reload()
                page.get_by_role("heading", name="3. Nodos en vivo").scroll_into_view_if_needed()
                estado = cadena.resumen()
                evidencia.append({"bloque": copy.deepcopy(cadena.bloques[-1]), "estado": estado})
                escena(capturas, 15, f"Carrera {i}: cuatro hilos prueban nonces", f"Captura resumida a 15 s. Duración real: {estado['segundos']:.3f} s. Cada nodo recorre i + 4k.")
                escena([capturar(page)], 12, f"Ganador: {estado['ganador']} · recompensa: 50", f"Total repartido: {sum(n['saldo'] for n in estado['nodos'])} unidades. Los cuatro hilos ya terminaron.")
                print(f"Video: bloque {i}, {estado['ganador']}, {estado['segundos']:.3f} s", flush=True)
            page.get_by_role("heading", name="4. Cadena", exact=False).scroll_into_view_if_needed()
            escena([capturar(page)], 15, "Tres bloques minados y enlazados", "Cada hash_anterior coincide con el hash del bloque previo. El minero también queda sellado.")
            page.get_by_role("button", name="Alterar bloque 1").click()
            assert not cadena.es_valida()
            escena([capturar(page)], 20, "Alteración detectada: cadena inválida", "Se cambió el contenido del bloque 1. Ya no coincide su hash y la firma tampoco verifica.")
            page.get_by_role("button", name="Restaurar copia original").click()
            assert cadena.es_valida()
            escena([capturar(page)], 15, "Copia original restaurada: cadena válida", "La demo termina con tres bloques, 150 unidades repartidas y todas las carreras detenidas.")
            browser.close()
        (OUT / "evidencia_video.json").write_text(json.dumps({"tipo": "capturas de app real, carreras resumidas, sin audio", "bloques": evidencia, "alteracion_detectada": True, "restauracion_valida": True}, ensure_ascii=False, indent=2), encoding="utf-8")
        assert sum(e[1] for e in escenas) == 180
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 25)
        small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 19)
        writer = imageio_ffmpeg.write_frames(str(OUT / "demostracion_pow.mp4"), (1280, 832), fps=10, codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", output_params=["-crf", "24", "-movflags", "+faststart"])
        writer.send(None)
        guion = []
        inicio = 0
        for frames, segundos, titulo, subtitulo in escenas:
            guion.append(f"{inicio:03d}-{inicio+segundos:03d} s | {titulo}\n{subtitulo}\n")
            for j in range(segundos * 10):
                frame = Image.open(io.BytesIO(frames[min(len(frames)-1, j * len(frames) // (segundos * 10))])).convert("RGB")
                lienzo = Image.new("RGB", (1280, 832), "#101820")
                lienzo.paste(frame, (0, 0))
                d = ImageDraw.Draw(lienzo)
                d.rectangle((0,720,1280,832), fill="#09151e")
                d.text((28,735), titulo, font=font, fill="#72e2b8")
                d.text((28,775), subtitulo, font=small, fill="white")
                writer.send(lienzo.tobytes())
            inicio += segundos
        writer.close()
        (OUT / "guion_video.txt").write_text("\n".join(guion), encoding="utf-8")
        print("Video listo: 180 s, 1280x832, 10 fps, subtitulado.", flush=True)
    finally:
        server.shutdown()


if __name__ == "__main__":
    ejecutar()

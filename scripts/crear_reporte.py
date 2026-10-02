"""Reporte de dos páginas a partir de las mediciones reales guardadas."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
datos = json.loads((ROOT / "output" / "mediciones.json").read_text(encoding="utf-8"))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloLocal", fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=colors.HexColor("#163b37"), spaceAfter=15))
styles.add(ParagraphStyle(name="SeccionLocal", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=colors.HexColor("#163b37"), spaceBefore=15, spaceAfter=7))
styles.add(ParagraphStyle(name="TextoLocal", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=7, alignment=TA_LEFT))
styles.add(ParagraphStyle(name="NotaLocal", fontName="Helvetica", fontSize=9, leading=12.5, textColor=colors.HexColor("#52656a"), spaceAfter=8))
contenido = []
def p(text): contenido.append(Paragraph(text, styles["TextoLocal"]))
def h(text): contenido.append(Paragraph(text, styles["SeccionLocal"]))

contenido.append(Paragraph("Simulador de Proof of Work", styles["TituloLocal"]))
contenido.append(Paragraph("Fundamentos de Blockchain · Trabajo intermedio · 1 de octubre de 2026", styles["NotaLocal"]))
h("Propósito: préstamos de equipo de laboratorio")
p("La aplicación registra préstamos y devoluciones de equipos como microscopios, osciloscopios y multímetros. Cada movimiento guarda el equipo, la acción y el responsable. El remitente es la llave pública de quien firma; la transacción también contiene el propósito y la hora en UTC. Así se puede revisar quién autorizó cada movimiento y detectar cambios posteriores en el registro.")
p("La regla propia del proyecto impide prestar un equipo que ya tiene un préstamo activo. Para devolverlo, deben coincidir la llave que firmó el préstamo y el nombre del responsable. Esta regla se comprueba al registrar la transacción, antes de minar y al validar la cadena. Una firma correcta demuestra autoría, pero por sí sola no garantiza que un préstamo sea permitido.")
h("Decisiones de diseño")
p("Cada billetera genera una llave privada Ed25519. La llave pública y la firma se representan en hexadecimal. La firma cubre la transacción completa serializada con json.dumps(..., sort_keys=True). La llave privada permanece en el servidor. La aplicación vuelve a verificar la firma antes de lanzar los mineros y rechaza firmas alteradas.")
p("Un bloque contiene numero, nonce, transaccion, firma, hash_anterior, minero y hash. SHA-256 se calcula con todos los campos excepto hash. La serialización ordenada permite recalcularlo de manera determinista. El campo minero queda incluido para que cambiar al destinatario de la recompensa invalide el hash. El génesis tiene número cero, hash anterior de 64 ceros y hash calculado; no exige firma ni minería porque no registra una transacción.")
p("La carrera usa cuatro hilos en el mismo proceso. El nodo i recorre los nonces i + 4k: por ejemplo, el nodo 1 prueba 1, 5, 9 y 13. Cada nodo trabaja sobre una copia propia del bloque, con su nombre como minero. Aunque los rangos de nonces son disjuntos, los nodos no calculan el mismo mensaje porque su campo minero es diferente.")
p("Un Event compartido señala el fin de la carrera. Un RLock protege la elección del ganador: dentro del candado se comprueba otra vez si alguien ya ganó, se agrega un único bloque, se acreditan 50 unidades y se retira la transacción pendiente. El estado minando pasa a falso cuando todos los hilos han terminado. Esto evita mostrar una carrera finalizada mientras aún se ejecuta algún trabajador.")
h("Interfaz y alcance")
p("Flask ofrece las rutas /, /transaccion, /minar y /estado. La página consulta el estado cada 300 ms para mostrar intentos, último hash, nonce y saldo por nodo. Al terminar, recarga la cadena y marca al ganador con un trofeo. Las billeteras, los saldos y la cadena viven en memoria; reiniciar el servidor crea un estado nuevo. Es un simulador local sin red P2P ni dinero real.")
contenido.append(PageBreak())
contenido.append(Paragraph("Mediciones y validación", styles["TituloLocal"]))
h("Método de medición")
p(f"Se ejecutaron {datos['entorno']['repeticiones']} carreras independientes para cada dificultad, con cuatro nodos, Python {datos['entorno']['python']} y Windows 11. Cada carrera generó una billetera y una transacción nuevas. Se usó time.perf_counter desde el inicio de la minería hasta terminar los cuatro hilos. La firma se hizo antes del cronómetro y la cadena se verificó después. Los valores originales y el entorno se guardan en mediciones.csv y mediciones.json.")
filas = [["Dificultad", "Carreras", "Promedio (s)", "Mín. / máx. (s)", "Intentos promedio"]]
for r in datos["resultados"]:
    filas.append([str(r["dificultad"]), str(datos["entorno"]["repeticiones"]), f"{r['promedio_s']:.3f}", f"{r['min_s']:.3f} / {r['max_s']:.3f}", f"{r['promedio_intentos']:,.1f}"])
tabla = Table(filas, colWidths=[65, 53, 90, 115, 132], repeatRows=1)
tabla.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#163b37")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTNAME", (0,1), (-1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 9), ("TOPPADDING", (0,0), (-1,-1), 11), ("BOTTOMPADDING", (0,0), (-1,-1), 11), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#edf4f2"), colors.white]), ("LINEBELOW", (0,0), (-1,0), .5, colors.HexColor("#163b37"))]))
contenido.append(tabla)
contenido.append(Spacer(1, 9))
contenido.append(Paragraph("Intentos = suma de hashes probados por los cuatro nodos, incluido el hash ganador. El tiempo incluye coordinación y finalización de los hilos.", styles["NotaLocal"]))
h("Por qué cada cero multiplica el trabajo esperado por 16")
p("Un dígito hexadecimal puede tomar 16 valores. Si los resultados de SHA-256 se modelan como uniformes, la probabilidad de que un hash comience con d ceros es p = 16<super>-d</super>. El número de intentos hasta el primer éxito tiene distribución geométrica y su media es 1/p = 16<super>d</super>. Por eso se esperan 4,096 intentos para d = 3; 65,536 para d = 4; y 1,048,576 para d = 5. Agregar un cero divide la probabilidad por 16 y multiplica por 16 los intentos esperados.")
p("El factor describe una expectativa, no una duración fija. En esta muestra, el promedio de tiempo creció aproximadamente 21.69 veces de 3 a 4 y 9.65 veces de 4 a 5. Cinco carreras son pocas para estimar con precisión una variable de tanta dispersión. También intervienen la carga del equipo, el costo de serializar, la coordinación y el GIL de CPython: cuatro hilos no garantizan cuatro veces más velocidad. Los resultados medidos se conservan tal como ocurrieron.")
h("Pruebas y demostración")
p("Las pruebas automatizadas comprueban la firma Ed25519 real, el rechazo de firmas modificadas, la serialización determinista, el campo minero sellado, el encadenamiento y la regla de préstamos. Una secuencia de tres bloques verifica que solo se reparta una recompensa por carrera, que el total llegue a 150 y que todos los hilos se detengan. Se comprueba que cada nonce observado pertenece al rango del nodo correspondiente.")
p("La prueba obligatoria altera el contenido de un bloque minado sin cambiar su firma ni su hash: es_valida() devuelve falso. También se prueban cambios en hash, firma, hash anterior, número y minero. La interfaz incluye Alterar bloque 1 y Restaurar copia original para repetir la demostración. El video muestra tres carreras reales, sus ganadores y saldos, la cadena inválida tras una alteración y su restauración. Tiene subtítulos, sin audio; las carreras están resumidas y sus tiempos reales se indican en pantalla.")
contenido.append(Paragraph("Fuente de requisitos: guia_pow.pdf, Dr. José de Jesús Ángel Ángel, Facultad de Ingeniería, Universidad Anáhuac México, pp. 1-3. Código, mediciones y capturas: ejecución local del proyecto.", styles["NotaLocal"]))

def pie(canvas, doc):
    canvas.setStrokeColor(colors.HexColor("#b9cbc5")); canvas.line(48, 42, A4[0]-48, 42)
    canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#52656a"))
    canvas.drawString(48, 29, "Préstamos de laboratorio | Proof of Work")
    canvas.drawRightString(A4[0]-48, 29, f"{doc.page} / 2")

SimpleDocTemplate(str(OUT / "reporte_pow.pdf"), pagesize=A4, rightMargin=48, leftMargin=48, topMargin=43, bottomMargin=54, title="Simulador de Proof of Work - Préstamos de laboratorio", author="Proyecto de Fundamentos de Blockchain").build(contenido, onFirstPage=pie, onLaterPages=pie)
pdf = pdfium.PdfDocument(str(OUT / "reporte_pow.pdf"))
assert len(pdf) == 2, f"El reporte debe tener 2 páginas, tiene {len(pdf)}"
tmp = ROOT / "tmp" / "pdfs"; tmp.mkdir(parents=True, exist_ok=True)
for i in range(len(pdf)):
    pdf[i].render(scale=1.5).to_pil().save(tmp / f"reporte-{i+1}.png")
print("Reporte generado y renderizado: 2 páginas.")

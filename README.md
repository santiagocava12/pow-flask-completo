# Simulador de Proof of Work con Flask

Actividad realizada a partir de `guia_pow.pdf`. Propósito: préstamos de equipo de laboratorio.

## Ejecutar en Windows

Desde PowerShell, dentro de esta carpeta:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abrir http://127.0.0.1:5000. El entorno local ya está instalado. Si se copia el proyecto a otra computadora:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

En macOS/Linux: `python3 -m venv .venv`, `./.venv/bin/python -m pip install -r requirements.txt` y `./.venv/bin/python app.py`. Crear un entorno nuevo, sin copiar la carpeta `.venv` de Windows.

## Demostración

1. Elegir usuario, equipo, acción y responsable. Pulsar **Firmar transacción**.
2. Pulsar **Iniciar carrera de minería**. La tabla muestra intentos, nonce y hash cada 300 ms.
3. El ganador aparece con un trofeo y recibe 50 unidades. Registrar otros dos equipos y repetir: habrá tres bloques minados, además del génesis.
4. Intentar prestar un equipo ocupado: se rechaza. Para devolverlo, usar el mismo usuario que firmó y el mismo responsable.
5. Pulsar **Alterar bloque 1**: la cadena se reporta inválida. **Restaurar copia original** recupera el estado previo para continuar.

Cuatro nodos usan nonces `i + 4k`. Cada uno mina su propia copia con distinto campo `minero`. Un `Event` detiene la carrera y un `RLock` protege el ganador, la incorporación del bloque y la recompensa. El estado deja de indicar minería solo después de terminar los cuatro hilos.

## Archivos y entregables

- `blockchain.py`: billeteras Ed25519, SHA-256, génesis, nodos, minería, reglas y validación.
- `app.py` y `templates/index.html`: Flask y la interfaz.
- `requirements.txt`: dependencias necesarias para ejecutar la aplicación.
- `tests/test_simulador.py`: pruebas del funcionamiento, las firmas, reglas y alteraciones.
- [Reporte en PDF](output/pdf/reporte_pow.pdf): dos páginas con mediciones reales.
- [Reporte editable en Word](output/reporte_pow.docx): el mismo contenido y la tabla de mediciones en formato editable.
- [Video de demostración](output/demostracion_pow.mp4): tres minutos con capturas reales y subtítulos; sin audio. Las carreras están resumidas a segmentos de 15 segundos y su tiempo real aparece indicado.
- `output/mediciones.csv` y `output/mediciones.json`: cinco carreras por dificultad, resultados y entorno.
- `output/evidencia_video.json`: bloques, hashes, firmas, saldos y resultado de la prueba de alteración usada en el video.
- `output/guion_video.txt`: contenido y tiempos del video.

## Pruebas y mediciones

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/benchmark.py --repeticiones 5
```

El benchmark usa cuatro hilos y transacciones nuevas por carrera. Mide desde el inicio de la minería hasta que todos los hilos terminan. Los resultados cambian entre ejecuciones.

Para regenerar el reporte/video, instalar `requirements-dev.txt`. El video usa Microsoft Edge instalado en Windows; si no está disponible, adaptar `channel` o instalar el navegador de Playwright. Ejecutar `scripts/crear_reporte.py` y `scripts/crear_video.py`.

## Límites del simulador

Estado en memoria: reiniciar genera billeteras, saldos y cadena nuevos. Las llaves privadas permanecen en el servidor, nunca se muestran en la página. Las recompensas son unidades simuladas; los préstamos no transfieren dinero. El génesis tiene hash calculado pero no requiere Proof of Work ni firma. No hay red P2P, persistencia, autenticación ni consenso entre computadoras. El servidor de desarrollo usa `debug=True, use_reloader=False` y solo escucha en localhost.

Los cuatro hilos cumplen el ejercicio de concurrencia; en CPython el GIL y el candado de actualización pueden limitar el rendimiento. No representan cuatro núcleos minando en paralelo ni un sistema de producción.

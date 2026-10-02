# Simulador de Proof of Work con Flask

Aplicación web para registrar préstamos de equipo de laboratorio mediante transacciones firmadas con Ed25519. Cuatro nodos compiten por minar cada bloque; el ganador recibe 50 unidades y la página muestra la cadena y su validez.

## Requisitos

- Python 3.12, que es la versión probada para este proyecto.
- Un navegador web.
- Conexión a internet para instalar las dependencias la primera vez.

`requirements.txt` incluye las dependencias de la aplicación: Flask y cryptography. Pip instala también sus dependencias automáticamente. No se necesita una base de datos, llaves externas, servicios de pago ni archivos adicionales.

## Descargar el proyecto

En GitHub, pulsa **Code > Download ZIP** y extrae el archivo. Abre una terminal dentro de la carpeta extraída, donde están `app.py` y `requirements.txt`.

También puedes descargarlo con Git:

```bash
git clone https://github.com/santiagocava12/pow-flask-completo.git
cd pow-flask-completo
```

## Ejecutar en Windows

En PowerShell, dentro de la carpeta del proyecto:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Si Windows no reconoce `python`, prueba `py -3.12 --version` y crea el entorno con `py -3.12 -m venv .venv`. Los dos comandos siguientes no cambian.

## Ejecutar en macOS o Linux

En Terminal, dentro de la carpeta del proyecto:

```bash
python3 --version
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python app.py
```

Comprueba que `python3` corresponde a Python 3.12. Cada computadora debe crear su propio entorno `.venv`.

## Abrir y usar la aplicación

Cuando la terminal muestre `Running on http://127.0.0.1:5000`, abre esa dirección en el navegador:

**http://127.0.0.1:5000**

Mantén la terminal abierta mientras uses la aplicación.

1. Selecciona el usuario que firma y escribe el equipo y el responsable.
2. Elige **Prestar** y pulsa **Firmar transacción**.
3. Pulsa **Iniciar carrera de minería**. La tabla actualiza los intentos, los nonces y los hashes de los cuatro nodos cada 300 ms.
4. Al terminar, el ganador aparece con un trofeo, recibe 50 unidades y el bloque se agrega a la cadena.
5. Repite con otros equipos para minar más bloques. Un equipo ocupado no puede prestarse otra vez.
6. Para registrar una devolución, selecciona **Devolver** y usa el mismo usuario, equipo y responsable del préstamo.
7. Después de minar un bloque, pulsa **Alterar bloque 1** para comprobar que la cadena se vuelve inválida. **Restaurar copia original** recupera el estado previo.

Para detener el servidor, pulsa **Ctrl+C** en la terminal.

## Volver a abrirlo

Las dependencias se instalan una sola vez por entorno. En las siguientes ocasiones basta con abrir la terminal en la carpeta del proyecto y ejecutar:

Windows:

```powershell
.\.venv\Scripts\python.exe app.py
```

macOS o Linux:

```bash
./.venv/bin/python app.py
```

## Archivos del repositorio

```text
pow-flask-completo/
├── app.py
├── blockchain.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

`blockchain.py` contiene las billeteras, las firmas, los nodos, la minería y la validación. `app.py` contiene el servidor Flask y `templates/index.html` contiene la interfaz.

## Problemas comunes

- **Python no se reconoce:** instala Python 3.12 y vuelve a abrir la terminal. En Windows también puedes usar el lanzador `py -3.12` para crear el entorno.
- **No se encuentra requirements.txt o app.py:** entra en la carpeta extraída del proyecto antes de ejecutar los comandos.
- **ModuleNotFoundError:** instala las dependencias con el comando indicado para tu sistema y ejecuta la aplicación con el Python de `.venv`.
- **El puerto 5000 está ocupado:** detén otra instancia del simulador o el programa que esté usando ese puerto antes de volver a iniciar.
- **La página no abre:** comprueba que el servidor sigue ejecutándose y abre `http://127.0.0.1:5000` en la misma computadora.

## Cómo se guarda la información

La aplicación guarda los bloques, las billeteras y los saldos en memoria. Al reiniciar el servidor, se genera una cadena nueva. Las recompensas son unidades simuladas. Los cuatro mineros funcionan en hilos dentro del mismo proceso; no se necesita una segunda computadora. El servidor solo escucha en la computadora local y se ejecuta con `debug=True, use_reloader=False` para evitar duplicar el estado con el recargador.

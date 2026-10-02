"""Ejecutar con .venv/Scripts/python app.py. Estado didáctico en memoria."""
import copy
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from blockchain import Billetera, Cadena, PROPOSITO, crear_transaccion


def create_app(cadena=None):
    app = Flask(__name__)
    app.secret_key = "simulador-local-educativo"
    cadena = cadena or Cadena()
    billeteras = {nombre: Billetera() for nombre in ("Cavazos", "Emilio", "Profesor")}
    app.config.update(CADENA=cadena, BILLETERAS=billeteras)

    @app.get("/")
    def index():
        with cadena.candado:
            return render_template("index.html", estado=cadena.resumen(), bloques=copy.deepcopy(cadena.bloques), pendiente=copy.deepcopy(cadena.pendiente), usuarios=billeteras, proposito=PROPOSITO)

    @app.post("/transaccion")
    def transaccion():
        try:
            usuario = request.form.get("usuario", "")
            if usuario not in billeteras or request.form.get("proposito") != PROPOSITO:
                raise ValueError("Usuario o propósito no reconocido.")
            tx = crear_transaccion(billeteras[usuario], request.form.get("equipo", ""), request.form.get("accion", ""), request.form.get("responsable", ""))
            cadena.registrar(tx, billeteras[usuario].firmar(tx))
            flash("Transacción firmada con Ed25519 y lista para minar.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("index"))

    @app.post("/minar")
    def minar():
        try:
            cadena.iniciar_mineria()
        except ValueError as e:
            flash(str(e), "error")
        return redirect(url_for("index"))

    @app.get("/estado")
    def estado():
        return jsonify(cadena.resumen())

    @app.post("/alterar")
    def alterar():
        with cadena.candado:
            if cadena.estado["minando"] or len(cadena.bloques) < 2:
                flash("Mina un bloque y espera a que termine la carrera.", "error")
            elif not app.config.get("RESPALDO"):
                app.config["RESPALDO"] = copy.deepcopy(cadena.bloques)
                cadena.bloques[1]["transaccion"]["contenido"]["equipo"] = "EQUIPO ALTERADO"
                flash("Contenido del bloque 1 alterado: comprueba que la cadena es inválida.", "error")
        return redirect(url_for("index"))

    @app.post("/restaurar")
    def restaurar():
        with cadena.candado:
            respaldo = app.config.pop("RESPALDO", None)
            if respaldo:
                cadena.bloques = respaldo
                flash("Se restauró la copia original de la demostración.", "ok")
        return redirect(url_for("index"))

    return app


app = create_app()
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=5000)

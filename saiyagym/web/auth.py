"""Inicio/cierre de sesion, redireccion por rol y perfil."""
from __future__ import annotations
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .. import servicios
from ..db.gateway import AppError
from ..security.decorators import ADMIN, CLIENTE, ENTRENADOR, login_required, usuario_actual
from ..services import validators
from ..services.auth_service import hash_clave
from .helpers import aplicar, mi_id

bp = Blueprint("auth", __name__)

INICIO_POR_ROL = {ADMIN: "admin.inicio", ENTRENADOR: "entrenador.inicio", CLIENTE: "cliente.inicio"}


def _destino_seguro(destino: str | None) -> bool:
    """Evita redirecciones abiertas: solo rutas internas."""
    if not destino:
        return False
    p = urlparse(destino)
    return not p.netloc and not p.scheme and destino.startswith("/") and not destino.startswith("//")


@bp.route("/")
def raiz():
    u = usuario_actual()
    if not u:
        return redirect(url_for("auth.login"))
    return redirect(url_for(INICIO_POR_ROL[u["rol"]]))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if usuario_actual():
        return redirect(url_for("auth.raiz"))
    correo = ""
    if request.method == "POST":
        correo = (request.form.get("correo") or "").strip()
        clave = request.form.get("clave") or ""
        if not correo or not clave:
            flash("Ingrese su correo y su contrasena.", "error")
        else:
            try:
                u = servicios().auth.autenticar(correo, clave, request.remote_addr or "?")
            except AppError as e:
                flash(e.mensaje, "error")
            else:
                destino = request.form.get("siguiente")
                session.clear()                     # nueva sesion al autenticar (evita fijacion de sesion)
                session.permanent = True
                session["usuario"] = {
                    "id": int(u["usuid"]), "nombre": u["usunombre"], "apellido": u["usuapellido"],
                    "correo": u["usucorreo"], "rol": u["rolnombre"],
                }
                if _destino_seguro(destino):
                    return redirect(destino)
                return redirect(url_for("auth.raiz"))
    return render_template("auth/login.html", correo=correo,
                           siguiente=request.args.get("siguiente", ""))


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Sesion cerrada. Hasta pronto.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    s = servicios()
    datos = s.usuarios.obtener(mi_id())
    errores = {}
    if request.method == "POST":
        actual = request.form.get("actual") or ""
        nueva = request.form.get("nueva") or ""
        repetir = request.form.get("repetir") or ""
        completo = s.usuarios.obtener_por_correo(datos["usucorreo"])
        from werkzeug.security import check_password_hash
        if not check_password_hash(completo["usucontrasena"], actual):
            errores["actual"] = "La contrasena actual no es correcta."
        msg = validators.validar_clave(nueva)
        if msg:
            errores["nueva"] = msg
        if nueva != repetir:
            errores["repetir"] = "Las contrasenas no coinciden."
        if not errores:
            if aplicar(lambda: s.usuarios.cambiar_contrasena(mi_id(), hash_clave(nueva)),
                       "Contrasena actualizada."):
                return redirect(url_for("auth.perfil"))
    return render_template("auth/perfil.html", datos=datos, errores=errores)

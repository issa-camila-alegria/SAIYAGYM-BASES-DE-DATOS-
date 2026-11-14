"""Control de acceso: autenticacion y restriccion por rol (RN-03, RN-04, seccion 3.2)."""
from __future__ import annotations
from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

ADMIN, ENTRENADOR, CLIENTE = "ADMINISTRADOR", "ENTRENADOR", "CLIENTE"


def usuario_actual() -> dict | None:
    return session.get("usuario")


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not usuario_actual():
            flash("Inicie sesion para continuar.", "info")
            return redirect(url_for("auth.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def roles_required(*roles):
    """Permite el acceso solo a los roles indicados; los demas reciben 403."""
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(*args, **kwargs):
            if usuario_actual()["rol"] not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador

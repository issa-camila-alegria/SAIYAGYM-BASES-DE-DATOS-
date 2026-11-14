"""Proteccion CSRF: token por sesion que debe acompanar cada formulario POST."""
from __future__ import annotations
import hmac
import secrets

from flask import abort, request, session


def token() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def verificar() -> None:
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        enviado = request.form.get("csrf_token", "")
        esperado = session.get("csrf", "")
        if not esperado or not hmac.compare_digest(enviado, esperado):
            abort(400, description="Formulario vencido o invalido. Recargue la pagina e intente de nuevo.")

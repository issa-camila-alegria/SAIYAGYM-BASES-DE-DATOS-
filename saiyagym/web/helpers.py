"""Utilidades compartidas por los controladores."""
from __future__ import annotations
from flask import abort, flash, session

from .. import servicios
from ..db.gateway import AppError


def mi_id() -> int:
    return session["usuario"]["id"]


def aplicar(operacion, mensaje_ok: str) -> bool:
    """Ejecuta una operacion de BD; muestra exito o el mensaje de la regla de negocio violada."""
    try:
        operacion()
    except AppError as e:
        flash(e.mensaje, "error")
        return False
    flash(mensaje_ok, "ok")
    return True


def entero_o_404(valor) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        abort(404)


def exigir_cliente_de(entrenador_id: int, cliente_id: int) -> None:
    """RN-04: el entrenador solo accede a clientes que ya tiene asignados."""
    if not servicios().usuarios.es_cliente_de(entrenador_id, cliente_id):
        abort(403)

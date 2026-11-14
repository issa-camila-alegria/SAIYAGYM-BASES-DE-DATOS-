"""Diccionario de datos dentro de la aplicacion (solo administrador).
Muestra tablas, columnas, restricciones, indices, procedimientos y codigo fuente
consultando las vistas USER_* de Oracle a traves de PKG_DICCIONARIO."""
from __future__ import annotations
import re

from flask import Blueprint, abort, render_template

from .. import servicios
from ..security.decorators import ADMIN, roles_required

bp = Blueprint("diccionario", __name__, url_prefix="/diccionario")
_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_$#]{0,29}$")
_TIPOS_FUENTE = {"PACKAGE", "PACKAGE BODY", "PROCEDURE", "FUNCTION", "TRIGGER"}


def _ident(valor: str) -> str:
    if not _IDENT.match(valor):
        abort(404)
    return valor.upper()


@bp.route("/")
@roles_required(ADMIN)
def indice():
    s = servicios().diccionario
    return render_template("diccionario/indice.html", tablas=s.tablas(),
                           objetos=s.procedimientos(), secuencias=s.secuencias())


@bp.route("/tabla/<nombre>")
@roles_required(ADMIN)
def tabla(nombre):
    t = _ident(nombre)
    s = servicios().diccionario
    columnas = s.columnas(t)
    if not columnas:
        abort(404)
    return render_template("diccionario/tabla.html", tabla=t, columnas=columnas,
                           restricciones=s.restricciones(t), indices=s.indices(t))


@bp.route("/objeto/<nombre>/<path:tipo>")
@roles_required(ADMIN)
def objeto(nombre, tipo):
    n = _ident(nombre)
    t = tipo.upper()
    if t not in _TIPOS_FUENTE:
        abort(404)
    s = servicios().diccionario
    codigo = s.codigo(n, t)
    if not codigo:
        abort(404)
    return render_template("diccionario/objeto.html", nombre=n, tipo=t, codigo=codigo,
                           subprogramas=s.subprogramas(n) if t == "PACKAGE" else [])

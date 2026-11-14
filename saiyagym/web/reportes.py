"""Informes REP-01 a REP-09, restringidos por rol (matriz de permisos, seccion 3.2)."""
from __future__ import annotations
import csv
import io

from flask import Blueprint, Response, abort, render_template

from .. import servicios
from ..security.decorators import ADMIN, CLIENTE, ENTRENADOR, login_required, usuario_actual
from .helpers import mi_id

bp = Blueprint("reportes", __name__, url_prefix="/reportes")

# codigo -> (titulo, descripcion, funcion del paquete, roles permitidos, como se limita por rol)
INFORMES = {
    "REP-01": ("Clientes con membresía vencida", "Quienes no tienen otra membresía activa o pendiente: candidatos a renovar.",
               "rep01_membresias_vencidas", {ADMIN}, None),
    "REP-02": ("Pagos pendientes y anulados", "Pagos cuyo estado no es PAGADO.",
               "rep02_pagos_pendientes_anulados", {ADMIN}, None),
    "REP-03": ("Saldo por membresía", "Valor pactado, total pagado y saldo por cobrar.",
               "rep03_saldo_membresias", {ADMIN}, None),
    "REP-04": ("Total pagado por cliente", "Pagos confirmados, de mayor a menor.",
               "rep04_total_pagado_cliente", {ADMIN}, None),
    "REP-05": ("Ranking de asistencia", "Asistencias por cliente, primera y última visita.",
               "rep05_ranking_asistencia", {ADMIN, ENTRENADOR}, "entrenador"),
    "REP-06": ("Rachas de asistencia", "Racha actual (vigente o interrumpida) y mejor racha histórica.",
               "rep06_rachas", {ADMIN, ENTRENADOR, CLIENTE}, "entrenador_o_cliente"),
    "REP-07": ("Rutinas asignadas por entrenador", "Asignaciones por entrenador y estado.",
               "rep07_asignaciones_entrenador", {ADMIN, ENTRENADOR}, "entrenador"),
    "REP-08": ("Rutinas sin asignar o sin ejercicios", "Rutinas que aún no se pueden o no se han asignado.",
               "rep08_rutinas_sin_asignar", {ADMIN, ENTRENADOR}, "entrenador"),
    "REP-09": ("Ventas por tipo de membresía", "Cantidad vendida y valor promedio, mínimo y máximo.",
               "rep09_ventas_membresia", {ADMIN}, None),
}


def _permitidos(rol: str) -> dict:
    return {k: v for k, v in INFORMES.items() if rol in v[3]}


@bp.route("/")
@login_required
def indice():
    return render_template("reportes/indice.html", informes=_permitidos(usuario_actual()["rol"]))


def _consultar(codigo):
    """Valida el rol y ejecuta el informe. Devuelve (codigo, titulo, descripcion, filas)."""
    u = usuario_actual()
    informe = INFORMES.get(codigo.upper())
    if informe is None:
        abort(404)
    if u["rol"] not in informe[3]:
        abort(403)
    titulo, descripcion, funcion, _, alcance = informe
    params = ()
    if u["rol"] == ENTRENADOR and alcance:
        params = (mi_id(),)                       # solo SUS clientes / SUS rutinas
    elif u["rol"] == CLIENTE and alcance == "entrenador_o_cliente":
        params = (None, mi_id())                  # solo el propio
    elif u["rol"] == ADMIN and alcance == "entrenador_o_cliente":
        params = (None, None)
    return codigo.upper(), titulo, descripcion, servicios().reportes.ejecutar(funcion, *params)


@bp.route("/<codigo>")
@login_required
def ver(codigo):
    codigo, titulo, descripcion, filas = _consultar(codigo)
    columnas = list(filas[0].keys()) if filas else []
    return render_template("reportes/ver.html", codigo=codigo, titulo=titulo,
                           descripcion=descripcion, filas=filas, columnas=columnas)


@bp.route("/<codigo>/csv")
@login_required
def descargar(codigo):
    """Exporta el informe a CSV (separador ; y BOM para que Excel respete las tildes)."""
    codigo, _, _, filas = _consultar(codigo)
    salida = io.StringIO()
    if filas:
        w = csv.writer(salida, delimiter=";")
        w.writerow([c.replace("_", " ") for c in filas[0]])
        for f in filas:
            w.writerow(["" if v is None else v for v in f.values()])
    return Response("\ufeff" + salida.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={codigo}.csv"})

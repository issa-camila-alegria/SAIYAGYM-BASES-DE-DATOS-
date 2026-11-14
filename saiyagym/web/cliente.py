"""Modulo del CLIENTE: solo ve su propia informacion (RN-03).
El identificador del cliente SIEMPRE sale de la sesion, nunca de la URL ni del formulario."""
from __future__ import annotations
import calendar
from datetime import date, timedelta
from flask import Blueprint, abort, flash, redirect, render_template, url_for

from .. import servicios
from ..security.decorators import CLIENTE, roles_required
from .helpers import aplicar, entero_o_404, mi_id

bp = Blueprint("cliente", __name__, url_prefix="/cliente")
solo_cliente = roles_required(CLIENTE)

HITOS = (3, 7, 14, 30)
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def _dia(a):
    return a.date() if hasattr(a, "date") else a


def _semana(asistencias):
    """Ultimos 7 dias (el de hoy al final) marcando en cuales asistio."""
    hoy = date.today()
    fechas = {_dia(a["asifecha"]) for a in asistencias}
    return [dict(etiqueta=DIAS[d.weekday()], numero=d.day, asistio=d in fechas, hoy=d == hoy)
            for d in (hoy - timedelta(days=i) for i in range(6, -1, -1))]


def _calendario(asistencias):
    """Cuadricula del mes actual: lista de semanas con (numero, asistio, hoy) o None para huecos."""
    hoy = date.today()
    fechas = {_dia(a["asifecha"]) for a in asistencias}
    celdas = [None] * date(hoy.year, hoy.month, 1).weekday()
    ultimo = calendar.monthrange(hoy.year, hoy.month)[1]
    for n in range(1, ultimo + 1):
        d = date(hoy.year, hoy.month, n)
        celdas.append(dict(numero=n, asistio=d in fechas, hoy=d == hoy))
    return celdas, sum(1 for c in celdas if c and c["asistio"]), ultimo


def _siguiente_hito(racha: int) -> int:
    return next((h for h in HITOS if racha < h), HITOS[-1])


@bp.route("/")
@solo_cliente
def inicio():
    s = servicios()
    yo = mi_id()
    racha = s.asistencias.racha_actual(yo)
    estado = s.asistencias.estado_racha(yo)
    meta = _siguiente_hito(racha if estado == "VIGENTE" else 0)
    historial = s.asistencias.consultar(yo)
    return render_template(
        "cliente/inicio.html", semana=_semana(historial),
        total_asistencias=len(historial),
        membresia=s.membresias.vigente(yo),
        racha=racha, estado=estado, mejor=s.asistencias.mejor_racha(yo),
        meta=meta, hoy=s.asistencias.asistio_hoy(yo),
        logros=s.asistencias.logros(yo),
        rutinas=[a for a in s.rutinas.asignaciones(None, yo) if a["asirutestado"] == "ACTIVA"],
        pagos=s.pagos.consultar(None, yo)[:3],
        ultimas=s.asistencias.consultar(yo)[:5])


@bp.route("/asistencia", methods=["POST"])
@solo_cliente
def registrar_asistencia():
    aplicar(lambda: servicios().asistencias.registrar(mi_id()), "Asistencia registrada. Buen entrenamiento.")
    return redirect(url_for("cliente.inicio"))


@bp.route("/asistencias")
@solo_cliente
def asistencias():
    s = servicios()
    yo = mi_id()
    historial = s.asistencias.consultar(yo)
    celdas, del_mes, dias_mes = _calendario(historial)
    return render_template("cliente/asistencias.html", lista=historial, celdas=celdas, del_mes=del_mes,
                           dias_mes=dias_mes, cabeceras=[d[0].upper() for d in DIAS],
                           rachas=s.asistencias.historial_rachas(yo), logros=s.asistencias.logros(yo),
                           racha=s.asistencias.racha_actual(yo), mejor=s.asistencias.mejor_racha(yo),
                           estado=s.asistencias.estado_racha(yo))


@bp.route("/membresias")
@solo_cliente
def membresias():
    s = servicios()
    return render_template("cliente/membresias.html", lista=s.membresias.adquiridas(mi_id()),
                           catalogo=s.membresias.tipos(solo_activas=True))


@bp.route("/pagos")
@solo_cliente
def pagos():
    return render_template("cliente/pagos.html", lista=servicios().pagos.consultar(None, mi_id()))


@bp.route("/rutinas")
@solo_cliente
def rutinas():
    return render_template("cliente/rutinas.html",
                           lista=servicios().rutinas.asignaciones(None, mi_id()))


@bp.route("/rutinas/<id_>")
@solo_cliente
def rutina_detalle(id_):
    """Detalle de una rutina ASIGNADA al cliente (si no es suya: 403)."""
    s = servicios()
    asi_id = entero_o_404(id_)
    propia = next((a for a in s.rutinas.asignaciones(None, mi_id()) if a["asirutid"] == asi_id), None)
    if propia is None:
        abort(403)
    return render_template("cliente/rutina_detalle.html", asignacion=propia,
                           lineas=s.rutinas.ejercicios_de_rutina(propia["rutid"]))

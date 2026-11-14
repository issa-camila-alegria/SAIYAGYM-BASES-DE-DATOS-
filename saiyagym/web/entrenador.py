"""Modulo del ENTRENADOR: sus clientes, ejercicios, rutinas y asignaciones."""
from __future__ import annotations
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .. import servicios
from ..db.gateway import AppError
from ..security.decorators import ENTRENADOR, roles_required
from ..services import validators
from .helpers import aplicar, entero_o_404, exigir_cliente_de, mi_id

bp = Blueprint("entrenador", __name__, url_prefix="/entrenador")
solo_entrenador = roles_required(ENTRENADOR)
NIVELES_OP = [(n, n.capitalize()) for n in validators.NIVELES]


@bp.route("/")
@solo_entrenador
def inicio():
    s = servicios()
    yo = mi_id()
    asist = s.reportes.serie("graf_asistencia_diaria", 14, yo)
    return render_template("entrenador/inicio.html",
                           asistencia=[(f["etiqueta"], float(f["valor"] or 0), bool(f.get("actual"))) for f in asist],
                           ranking=s.reportes.ejecutar("rep05_ranking_asistencia", yo)[:5],
                           clientes=s.usuarios.clientes_de_entrenador(yo),
                           rutinas=s.rutinas.rutinas(yo),
                           asignaciones=[a for a in s.rutinas.asignaciones(yo) if a["asirutestado"] == "ACTIVA"])


# ---------------------------------------------------------------- clientes
@bp.route("/clientes")
@solo_entrenador
def clientes():
    return render_template("entrenador/clientes.html",
                           lista=servicios().usuarios.clientes_de_entrenador(mi_id()))


@bp.route("/clientes/<id_>")
@solo_entrenador
def cliente_detalle(id_):
    s = servicios()
    cli_id = entero_o_404(id_)
    exigir_cliente_de(mi_id(), cli_id)             # RN-04
    return render_template(
        "entrenador/cliente_detalle.html",
        cliente=s.usuarios.obtener(cli_id),
        asignaciones=s.rutinas.asignaciones(None, cli_id),
        asistencias=s.asistencias.consultar(cli_id)[:10],
        racha=s.asistencias.racha_actual(cli_id), estado=s.asistencias.estado_racha(cli_id),
        mejor=s.asistencias.mejor_racha(cli_id), logros=s.asistencias.logros(cli_id))


# --------------------------------------------------------------- ejercicios
@bp.route("/ejercicios")
@solo_entrenador
def ejercicios():
    s = servicios()
    grupo = request.args.get("grupo") or None
    return render_template("entrenador/ejercicios.html", lista=s.rutinas.ejercicios(grupo),
                           grupos=s.rutinas.grupos_musculares(), grupo=grupo or "")


@bp.route("/ejercicios/nuevo", methods=["GET", "POST"])
@solo_entrenador
def ejercicio_nuevo():
    s = servicios()
    errores = {}
    if request.method == "POST":
        r = validators.ejercicio(request.form)
        errores = r.errores
        if r.ok and aplicar(lambda: s.rutinas.insertar_ejercicio(r.datos), "Ejercicio creado."):
            return redirect(url_for("entrenador.ejercicios"))
    return render_template("entrenador/ejercicio_form.html", modo="nuevo", form=request.form,
                           errores=errores, niveles=NIVELES_OP, grupos=s.rutinas.grupos_musculares())


@bp.route("/ejercicios/<id_>/editar", methods=["GET", "POST"])
@solo_entrenador
def ejercicio_editar(id_):
    s = servicios()
    eje_id = entero_o_404(id_)
    actual = s.rutinas.ejercicio(eje_id)
    if actual is None:
        flash("El ejercicio no existe.", "error")
        return redirect(url_for("entrenador.ejercicios"))
    form = {"nombre": actual["ejenombre"], "descripcion": actual["ejedescripcion"] or "",
            "grupo": actual["ejegrupomuscular"], "nivel": actual["ejeniveldificultad"]}
    errores = {}
    if request.method == "POST":
        form = request.form
        r = validators.ejercicio(form)
        errores = r.errores
        if r.ok and aplicar(lambda: s.rutinas.actualizar_ejercicio(eje_id, r.datos), "Ejercicio actualizado."):
            return redirect(url_for("entrenador.ejercicios"))
    return render_template("entrenador/ejercicio_form.html", modo="editar", form=form, errores=errores,
                           niveles=NIVELES_OP, grupos=s.rutinas.grupos_musculares())


@bp.route("/ejercicios/<id_>/eliminar", methods=["POST"])
@solo_entrenador
def ejercicio_eliminar(id_):
    aplicar(lambda: servicios().rutinas.eliminar_ejercicio(entero_o_404(id_)), "Ejercicio eliminado.")
    return redirect(url_for("entrenador.ejercicios"))


# ----------------------------------------------------------------- rutinas
@bp.route("/rutinas")
@solo_entrenador
def rutinas():
    s = servicios()
    ver = request.args.get("ver", "mias")
    lista = s.rutinas.rutinas(mi_id() if ver == "mias" else None)
    return render_template("entrenador/rutinas.html", lista=lista, ver=ver, yo=mi_id())


@bp.route("/rutinas/nueva", methods=["GET", "POST"])
@solo_entrenador
def rutina_nueva():
    errores = {}
    if request.method == "POST":
        r = validators.rutina(request.form)
        errores = r.errores
        if r.ok:
            try:
                nuevo = servicios().rutinas.insertar_rutina(mi_id(), r.datos)
            except AppError as e:
                flash(e.mensaje, "error")
            else:
                flash("Rutina creada. Ahora agrega sus ejercicios.", "ok")
                return redirect(url_for("entrenador.rutina_detalle", id_=nuevo))
    return render_template("entrenador/rutina_form.html", modo="nueva", form=request.form,
                           errores=errores, niveles=NIVELES_OP)


@bp.route("/rutinas/<id_>")
@solo_entrenador
def rutina_detalle(id_):
    s = servicios()
    rut_id = entero_o_404(id_)
    rutina = s.rutinas.rutina(rut_id)
    if rutina is None:
        abort(404)
    lineas = s.rutinas.ejercicios_de_rutina(rut_id)
    usados = {l["ejeid"] for l in lineas}
    disponibles = [e for e in s.rutinas.ejercicios() if e["ejeid"] not in usados]
    return render_template("entrenador/rutina_detalle.html", rutina=rutina, lineas=lineas,
                           disponibles=[(e["ejeid"], f'{e["ejenombre"]} · {e["ejegrupomuscular"]}') for e in disponibles], propia=rutina["rutentrenadorid"] == mi_id(),
                           errores={}, form={})


@bp.route("/rutinas/<id_>/editar", methods=["GET", "POST"])
@solo_entrenador
def rutina_editar(id_):
    s = servicios()
    rut_id = entero_o_404(id_)
    rutina = s.rutinas.rutina(rut_id)
    if rutina is None:
        abort(404)
    if rutina["rutentrenadorid"] != mi_id():
        abort(403)
    form = {"nombre": rutina["rutnombre"], "objetivo": rutina["rutobjetivo"],
            "nivel": rutina["rutnivel"], "descripcion": rutina["rutdescripcion"] or ""}
    errores = {}
    if request.method == "POST":
        form = request.form
        r = validators.rutina(form)
        errores = r.errores
        if r.ok and aplicar(lambda: s.rutinas.actualizar_rutina(rut_id, mi_id(), r.datos), "Rutina actualizada."):
            return redirect(url_for("entrenador.rutina_detalle", id_=rut_id))
    return render_template("entrenador/rutina_form.html", modo="editar", form=form, errores=errores,
                           niveles=NIVELES_OP, rutina=rutina)


@bp.route("/rutinas/<id_>/eliminar", methods=["POST"])
@solo_entrenador
def rutina_eliminar(id_):
    if aplicar(lambda: servicios().rutinas.eliminar_rutina(entero_o_404(id_), mi_id()), "Rutina eliminada."):
        return redirect(url_for("entrenador.rutinas"))
    return redirect(url_for("entrenador.rutina_detalle", id_=id_))


@bp.route("/rutinas/<id_>/ejercicios", methods=["POST"])
@solo_entrenador
def rutina_agregar_ejercicio(id_):
    rut_id = entero_o_404(id_)
    r = validators.linea_rutina(request.form)
    if not r.ok:
        flash(next(iter(r.errores.values())), "error")
    else:
        d = r.datos
        aplicar(lambda: servicios().rutinas.agregar_ejercicio(
            rut_id, mi_id(), d["eje_id"], d["series"], d["repeticiones"], d["descanso"]),
            "Ejercicio agregado a la rutina.")
    return redirect(url_for("entrenador.rutina_detalle", id_=rut_id))


@bp.route("/rutinas/<id_>/lineas/<linea>/actualizar", methods=["POST"])
@solo_entrenador
def linea_actualizar(id_, linea):
    rut_id = entero_o_404(id_)
    r = validators.linea_rutina(request.form, con_ejercicio=False)
    if not r.ok:
        flash(next(iter(r.errores.values())), "error")
    else:
        d = r.datos
        aplicar(lambda: servicios().rutinas.actualizar_linea(
            entero_o_404(linea), mi_id(), d["series"], d["repeticiones"], d["descanso"]),
            "Ejercicio actualizado.")
    return redirect(url_for("entrenador.rutina_detalle", id_=rut_id))


@bp.route("/rutinas/<id_>/lineas/<linea>/quitar", methods=["POST"])
@solo_entrenador
def linea_quitar(id_, linea):
    aplicar(lambda: servicios().rutinas.quitar_ejercicio(entero_o_404(linea), mi_id()),
            "Ejercicio quitado de la rutina.")
    return redirect(url_for("entrenador.rutina_detalle", id_=entero_o_404(id_)))


# ------------------------------------------------------------ asignaciones
@bp.route("/asignaciones")
@solo_entrenador
def asignaciones():
    return render_template("entrenador/asignaciones.html",
                           lista=servicios().rutinas.asignaciones(mi_id()))


@bp.route("/asignaciones/nueva", methods=["GET", "POST"])
@solo_entrenador
def asignacion_nueva():
    s = servicios()
    errores = {}
    if request.method == "POST":
        r = validators.asignacion(request.form)
        errores = r.errores
        if r.ok:
            d = r.datos
            if aplicar(lambda: s.rutinas.asignar(mi_id(), d["cliente_id"], d["rut_id"]), "Rutina asignada."):
                return redirect(url_for("entrenador.asignaciones"))
    clientes = [(c["usuid"], f'{c["usunombre"]} {c["usuapellido"]}')
                for c in s.usuarios.consultar("CLIENTE") if c["usuestado"] == "ACTIVO"]
    # solo rutinas con al menos un ejercicio (RN-07)
    rutinas = [(r["rutid"], f'{r["rutnombre"]} · {r["rutnivel"].capitalize()} · {r["entrenador"]}')
               for r in s.rutinas.rutinas() if r["numejercicios"] > 0]
    return render_template("entrenador/asignacion_form.html", clientes=clientes, rutinas=rutinas,
                           form=request.form if request.method == "POST" else
                           {"cliente_id": request.args.get("cliente", ""), "rut_id": request.args.get("rutina", "")},
                           errores=errores)


@bp.route("/asignaciones/<id_>/cerrar", methods=["POST"])
@solo_entrenador
def asignacion_cerrar(id_):
    estado = request.form.get("estado")
    aplicar(lambda: servicios().rutinas.cerrar_asignacion(entero_o_404(id_), mi_id(), estado),
            "Asignacion finalizada." if estado == "FINALIZADA" else "Asignacion cancelada.")
    return redirect(request.referrer or url_for("entrenador.asignaciones"))

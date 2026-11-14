"""Modulo del ADMINISTRADOR: usuarios, membresias, pagos y consultas generales."""
from __future__ import annotations
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import servicios
from ..security.decorators import ADMIN, roles_required
from ..services import validators
from ..services.formatters import moneda
from ..services.auth_service import hash_clave
from .helpers import aplicar, entero_o_404, mi_id

bp = Blueprint("admin", __name__, url_prefix="/admin")
solo_admin = roles_required(ADMIN)


def _barras(filas, resaltar="actual"):
    """Convierte filas de pkg_reportes.graf_* en (etiqueta, valor, resaltar) para el macro barras()."""
    return [(f["etiqueta"], float(f["valor"] or 0), bool(f.get(resaltar))) for f in filas]


@bp.route("/")
@solo_admin
def inicio():
    s = servicios()
    r = s.reportes
    return render_template(
        "admin/inicio.html", resumen=r.resumen_general(),
        por_pagar=r.ejecutar("rep03_saldo_membresias")[:6],
        vencidas=r.ejecutar("rep01_membresias_vencidas")[:6],
        recaudo=_barras(r.serie("graf_recaudo_mensual", 6)),
        asistencia=_barras(r.serie("graf_asistencia_diaria", 14)),
        estados=[(f["etiqueta"], int(f["valor"])) for f in r.serie("graf_membresias_estado")],
        ventas=[(f["etiqueta"], int(f["valor"])) for f in r.serie("graf_ventas_tipo")],
        entrenadores=[(f["etiqueta"], int(f["valor"])) for f in r.serie("graf_clientes_entrenador")],
        ranking=r.ejecutar("rep05_ranking_asistencia", None)[:5])


# ---------------------------------------------------------------- usuarios
@bp.route("/usuarios")
@solo_admin
def usuarios():
    rol = request.args.get("rol") or None
    buscar = (request.args.get("q") or "").strip() or None
    lista = servicios().usuarios.consultar(rol, buscar)
    return render_template("admin/usuarios.html", lista=lista, rol=rol or "", q=buscar or "")


def _roles_validos() -> dict[int, str]:
    return {int(r["rolid"]): r["rolnombre"] for r in servicios().usuarios.roles()}


@bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@solo_admin
def usuario_nuevo():
    s = servicios()
    roles = _roles_validos()
    r = None
    if request.method == "POST":
        r = validators.usuario(request.form, con_clave=True, roles_validos=set(roles))
        if r.ok:
            d = r.datos
            if aplicar(lambda: s.usuarios.insertar(d, hash_clave(d["clave"])), "Usuario creado."):
                return redirect(url_for("admin.usuarios"))
    return render_template("admin/usuario_form.html", modo="nuevo", roles=roles,
                           form=request.form if r else {}, errores=r.errores if r else {})


@bp.route("/usuarios/<id_>/editar", methods=["GET", "POST"])
@solo_admin
def usuario_editar(id_):
    s = servicios()
    usu_id = entero_o_404(id_)
    actual = s.usuarios.obtener(usu_id) or None
    if actual is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for("admin.usuarios"))
    errores, form = {}, {
        "identificacion": actual["usuidentificacion"], "nombre": actual["usunombre"],
        "apellido": actual["usuapellido"], "correo": actual["usucorreo"],
        "telefono": actual["usutelefono"] or "",
    }
    if request.method == "POST":
        form = request.form
        r = validators.usuario(form, con_clave=False)
        errores = r.errores
        if r.ok and aplicar(lambda: s.usuarios.actualizar(usu_id, r.datos), "Datos actualizados."):
            return redirect(url_for("admin.usuarios"))
    return render_template("admin/usuario_form.html", modo="editar", actual=actual,
                           form=form, errores=errores, roles={})


@bp.route("/usuarios/<id_>/estado", methods=["POST"])
@solo_admin
def usuario_estado(id_):
    usu_id = entero_o_404(id_)
    nuevo = request.form.get("estado")
    if usu_id == mi_id() and nuevo == "INACTIVO":
        flash("No puedes desactivar tu propia cuenta.", "error")
    else:
        aplicar(lambda: servicios().usuarios.cambiar_estado(usu_id, nuevo),
                "Usuario activado." if nuevo == "ACTIVO" else "Usuario desactivado.")
    return redirect(request.referrer or url_for("admin.usuarios"))


@bp.route("/usuarios/<id_>/clave", methods=["POST"])
@solo_admin
def usuario_clave(id_):
    usu_id = entero_o_404(id_)
    nueva = request.form.get("clave") or ""
    msg = validators.validar_clave(nueva)
    if msg:
        flash(msg, "error")
    else:
        aplicar(lambda: servicios().usuarios.cambiar_contrasena(usu_id, hash_clave(nueva)),
                "Contrasena restablecida.")
    return redirect(url_for("admin.usuario_editar", id_=usu_id))


@bp.route("/usuarios/<id_>/eliminar", methods=["POST"])
@solo_admin
def usuario_eliminar(id_):
    usu_id = entero_o_404(id_)
    if usu_id == mi_id():
        flash("No puedes eliminar tu propia cuenta.", "error")
    else:
        aplicar(lambda: servicios().usuarios.eliminar(usu_id), "Usuario eliminado.")
    return redirect(url_for("admin.usuarios"))


# -------------------------------------------------------------- membresias
@bp.route("/membresias")
@solo_admin
def membresias():
    return render_template("admin/membresias.html", tipos=servicios().membresias.tipos())


@bp.route("/membresias/nueva", methods=["GET", "POST"])
@solo_admin
def membresia_nueva():
    errores = {}
    if request.method == "POST":
        r = validators.tipo_membresia(request.form)
        errores = r.errores
        if r.ok and aplicar(lambda: servicios().membresias.insertar_tipo(r.datos), "Membresia creada."):
            return redirect(url_for("admin.membresias"))
    return render_template("admin/membresia_form.html", modo="nueva", form=request.form, errores=errores)


@bp.route("/membresias/<id_>/editar", methods=["GET", "POST"])
@solo_admin
def membresia_editar(id_):
    s = servicios()
    mem_id = entero_o_404(id_)
    tipo = s.membresias.tipo(mem_id)
    if tipo is None:
        flash("La membresia no existe.", "error")
        return redirect(url_for("admin.membresias"))
    form = {"nombre": tipo["memnombre"], "duracion": tipo["memduracion"], "precio": int(tipo["memprecio"]),
            "descripcion": tipo["memdescripcion"] or "", "estado": tipo["memestado"]}
    errores = {}
    if request.method == "POST":
        form = request.form
        r = validators.tipo_membresia(form)
        errores = r.errores
        if r.ok and aplicar(lambda: s.membresias.actualizar_tipo(mem_id, r.datos), "Membresia actualizada."):
            return redirect(url_for("admin.membresias"))
    return render_template("admin/membresia_form.html", modo="editar", form=form, errores=errores, tipo=tipo)


@bp.route("/membresias/<id_>/eliminar", methods=["POST"])
@solo_admin
def membresia_eliminar(id_):
    aplicar(lambda: servicios().membresias.eliminar_tipo(entero_o_404(id_)), "Membresia eliminada.")
    return redirect(url_for("admin.membresias"))


# ------------------------------------------------------ membresias adquiridas
@bp.route("/adquiridas")
@solo_admin
def adquiridas():
    s = servicios()
    cliente = request.args.get("cliente")
    usu_id = int(cliente) if cliente and cliente.isdigit() else None
    return render_template("admin/adquiridas.html", lista=s.membresias.adquiridas(usu_id),
                           clientes=s.usuarios.consultar("CLIENTE"), cliente=usu_id)


@bp.route("/adquiridas/nueva", methods=["GET", "POST"])
@solo_admin
def adquirida_nueva():
    s = servicios()
    errores = {}
    if request.method == "POST":
        r = validators.adquisicion(request.form)
        errores = r.errores
        if r.ok:
            d = r.datos
            if aplicar(lambda: s.membresias.adquirir(d["usu_id"], d["mem_id"], d["inicio"]),
                       "Membresia registrada. Queda PENDIENTE hasta recibir un pago confirmado."):
                return redirect(url_for("admin.adquiridas"))
    clientes = [(c["usuid"], f'{c["usunombre"]} {c["usuapellido"]}')
                for c in s.usuarios.consultar("CLIENTE") if c["usuestado"] == "ACTIVO"]
    tipos = [(t["memid"], f'{t["memnombre"]} · {t["memduracion"]} dias · {moneda(t["memprecio"])}')
             for t in s.membresias.tipos(solo_activas=True)]
    form = request.form if request.method == "POST" else {"inicio": date.today().isoformat()}
    return render_template("admin/adquirida_form.html", clientes=clientes, tipos=tipos,
                           form=form, errores=errores)


@bp.route("/adquiridas/<id_>/eliminar", methods=["POST"])
@solo_admin
def adquirida_eliminar(id_):
    aplicar(lambda: servicios().membresias.eliminar_adquirida(entero_o_404(id_)), "Registro eliminado.")
    return redirect(url_for("admin.adquiridas"))


@bp.route("/estados/actualizar", methods=["POST"])
@solo_admin
def actualizar_estados():
    n = servicios().membresias.actualizar_estados()
    flash(f"Estados actualizados: {n} membresia(s) modificada(s)." if n else
          "Todo estaba al dia: no hubo cambios de estado.", "ok")
    return redirect(request.referrer or url_for("admin.inicio"))


# ------------------------------------------------------------------- pagos
@bp.route("/pagos")
@solo_admin
def pagos():
    estado = request.args.get("estado") or None
    if estado not in (None, "PAGADO", "PENDIENTE", "ANULADO"):
        estado = None
    return render_template("admin/pagos.html", lista=servicios().pagos.consultar(estado), estado=estado or "")


@bp.route("/pagos/nuevo", methods=["GET", "POST"])
@solo_admin
def pago_nuevo():
    s = servicios()
    errores = {}
    if request.method == "POST":
        r = validators.pago(request.form)
        errores = r.errores
        if r.ok:
            d = r.datos
            if aplicar(lambda: s.pagos.registrar(d["cli_mem_id"], d["valor"], d["metodo"], d["estado"]),
                       "Pago registrado."):
                return redirect(url_for("admin.pagos"))
    pendientes = [(m["climemid"], f'{m["cliente"]} · {m["memnombre"]} · saldo {moneda(m["saldo"])}')
                  for m in s.membresias.adquiridas() if m["saldo"] and m["saldo"] > 0]
    preseleccion = request.args.get("cm", "")
    return render_template("admin/pago_form.html", modo="nuevo", membresias=pendientes,
                           form=request.form if request.method == "POST" else {"cli_mem_id": preseleccion},
                           errores=errores, metodos=[(m, m.capitalize()) for m in validators.METODOS_PAGO])


@bp.route("/pagos/<id_>/editar", methods=["GET", "POST"])
@solo_admin
def pago_editar(id_):
    s = servicios()
    pag_id = entero_o_404(id_)
    pago = s.pagos.obtener(pag_id)
    if pago is None:
        flash("El pago no existe.", "error")
        return redirect(url_for("admin.pagos"))
    form = {"valor": int(pago["pagvalor"]), "metodo": pago["pagmetodo"]}
    errores = {}
    if request.method == "POST":
        form = request.form
        r = validators.pago(form, con_destino=False)
        errores = r.errores
        if r.ok and aplicar(lambda: s.pagos.actualizar(pag_id, r.datos["valor"], r.datos["metodo"]),
                            "Pago actualizado."):
            return redirect(url_for("admin.pagos"))
    return render_template("admin/pago_form.html", modo="editar", pago=pago, form=form,
                           errores=errores, metodos=[(m, m.capitalize()) for m in validators.METODOS_PAGO], membresias=[])


@bp.route("/pagos/<id_>/estado", methods=["POST"])
@solo_admin
def pago_estado(id_):
    nuevo = request.form.get("estado")
    aplicar(lambda: servicios().pagos.cambiar_estado(entero_o_404(id_), nuevo),
            "Pago confirmado." if nuevo == "PAGADO" else "Pago anulado.")
    return redirect(request.referrer or url_for("admin.pagos"))


@bp.route("/pagos/<id_>/eliminar", methods=["POST"])
@solo_admin
def pago_eliminar(id_):
    aplicar(lambda: servicios().pagos.eliminar(entero_o_404(id_)), "Pago eliminado.")
    return redirect(url_for("admin.pagos"))


# ------------------------------------- consultas (el administrador solo consulta)
@bp.route("/ejercicios")
@solo_admin
def ejercicios():
    return render_template("admin/ejercicios.html", lista=servicios().rutinas.ejercicios())


@bp.route("/rutinas")
@solo_admin
def rutinas():
    return render_template("admin/rutinas.html", lista=servicios().rutinas.rutinas())


@bp.route("/rutinas/<id_>")
@solo_admin
def rutina_detalle(id_):
    s = servicios()
    rut_id = entero_o_404(id_)
    rutina = s.rutinas.rutina(rut_id)
    if rutina is None:
        flash("La rutina no existe.", "error")
        return redirect(url_for("admin.rutinas"))
    return render_template("admin/rutina_detalle.html", rutina=rutina,
                           lineas=s.rutinas.ejercicios_de_rutina(rut_id))


@bp.route("/asignaciones")
@solo_admin
def asignaciones():
    return render_template("admin/asignaciones.html", lista=servicios().rutinas.asignaciones())


@bp.route("/asistencia")
@solo_admin
def asistencia():
    s = servicios()
    cliente = request.args.get("cliente")
    clientes = s.usuarios.consultar("CLIENTE")
    usu_id = int(cliente) if cliente and cliente.isdigit() else None
    datos = None
    if usu_id:
        datos = {
            "lista": s.asistencias.consultar(usu_id),
            "racha": s.asistencias.racha_actual(usu_id),
            "estado": s.asistencias.estado_racha(usu_id),
            "mejor": s.asistencias.mejor_racha(usu_id),
            "logros": s.asistencias.logros(usu_id),
            "rachas": s.asistencias.historial_rachas(usu_id),
        }
    return render_template("admin/asistencia.html", clientes=clientes, cliente=usu_id, datos=datos)

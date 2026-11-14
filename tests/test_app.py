"""Pruebas de humo de la aplicacion con la pasarela falsa (sin Oracle)."""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from fake_gateway import FakeGateway
from saiyagym import create_app

CLAVE = "Saiya2026*"


@pytest.fixture()
def gw():
    return FakeGateway()


@pytest.fixture()
def app(gw):
    a = create_app(gateway=gw)
    a.config.update(TESTING=True)
    return a


def token(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def entrar(app, correo):
    c = app.test_client()
    t = token(c.get("/login").get_data(as_text=True))
    r = c.post("/login", data={"correo": correo, "clave": CLAVE, "csrf_token": t})
    assert r.status_code == 302, r.get_data(as_text=True)[:300]
    return c


def post(c, url, ruta_token="/perfil", **datos):
    t = token(c.get(ruta_token).get_data(as_text=True))
    return c.post(url, data={**datos, "csrf_token": t})


ADMIN, ENT, CLI = "laura.gomez@saiyagym.com", "carlos.mendoza@saiyagym.com", "mateo.herrera@gmail.com"


def test_login_redirige_por_rol(app):
    assert entrar(app, ADMIN).get("/").headers["Location"].endswith("/admin/")
    assert entrar(app, ENT).get("/").headers["Location"].endswith("/entrenador/")
    assert entrar(app, CLI).get("/").headers["Location"].endswith("/cliente/")


def test_login_invalido_y_inactivo(app):
    c = app.test_client()
    t = token(c.get("/login").get_data(as_text=True))
    r = c.post("/login", data={"correo": ADMIN, "clave": "mala", "csrf_token": t})
    assert r.status_code == 200 and "incorrectos" in r.get_data(as_text=True)
    r = c.post("/login", data={"correo": "santiago.ibarra@hotmail.com", "clave": CLAVE, "csrf_token": t})
    assert "inactiva" in r.get_data(as_text=True)


def test_bloqueo_por_intentos(app):
    c = app.test_client()
    t = token(c.get("/login").get_data(as_text=True))
    for _ in range(6):
        r = c.post("/login", data={"correo": ADMIN, "clave": "mala", "csrf_token": t})
    assert "Demasiados intentos" in r.get_data(as_text=True)


def test_sin_csrf_se_rechaza(app):
    c = app.test_client()
    assert c.post("/login", data={"correo": ADMIN, "clave": CLAVE}).status_code == 400


def test_redireccion_abierta_bloqueada(app):
    c = app.test_client()
    t = token(c.get("/login").get_data(as_text=True))
    r = c.post("/login", data={"correo": ADMIN, "clave": CLAVE, "csrf_token": t, "siguiente": "https://malo.com"})
    assert r.status_code == 302 and not r.headers["Location"].startswith("http")   # no sale del sitio


def test_rutas_exigen_sesion(app):
    r = app.test_client().get("/admin/usuarios")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


@pytest.mark.parametrize("ruta", [
    "/admin/", "/admin/usuarios", "/admin/usuarios?rol=CLIENTE&q=ma", "/admin/usuarios/nuevo", "/admin/usuarios/4/editar",
    "/admin/membresias", "/admin/membresias/nueva", "/admin/membresias/1/editar", "/admin/adquiridas",
    "/admin/adquiridas/nueva", "/admin/pagos", "/admin/pagos?estado=PENDIENTE", "/admin/pagos/nuevo?cm=2",
    "/admin/pagos/2/editar", "/admin/ejercicios", "/admin/rutinas", "/admin/rutinas/1", "/admin/asignaciones",
    "/admin/asistencia", "/admin/asistencia?cliente=4", "/reportes/", "/reportes/REP-01", "/reportes/REP-03",
    "/reportes/REP-06", "/reportes/REP-09", "/diccionario/", "/diccionario/tabla/USUARIO",
    "/diccionario/objeto/PKG_PAGO/PACKAGE", "/perfil"])
def test_paginas_admin(app, ruta):
    r = entrar(app, ADMIN).get(ruta)
    assert r.status_code == 200, ruta
    assert "SAIYAGYM" in r.get_data(as_text=True)


@pytest.mark.parametrize("ruta", [
    "/entrenador/", "/entrenador/clientes", "/entrenador/clientes/4", "/entrenador/ejercicios", "/entrenador/ejercicios/nuevo",
    "/entrenador/ejercicios/1/editar", "/entrenador/rutinas", "/entrenador/rutinas?ver=todas", "/entrenador/rutinas/nueva",
    "/entrenador/rutinas/1", "/entrenador/rutinas/1/editar", "/entrenador/rutinas/2", "/entrenador/asignaciones",
    "/entrenador/asignaciones/nueva", "/reportes/", "/reportes/REP-05", "/reportes/REP-08"])
def test_paginas_entrenador(app, ruta):
    assert entrar(app, ENT).get(ruta).status_code == 200, ruta


@pytest.mark.parametrize("ruta", [
    "/cliente/", "/cliente/asistencias", "/cliente/membresias", "/cliente/pagos", "/cliente/rutinas",
    "/cliente/rutinas/1", "/reportes/", "/reportes/REP-06"])
def test_paginas_cliente(app, ruta):
    assert entrar(app, CLI).get(ruta).status_code == 200, ruta


def test_restricciones_por_rol(app):
    cli, ent, adm = entrar(app, CLI), entrar(app, ENT), entrar(app, ADMIN)
    for ruta in ("/admin/", "/admin/usuarios", "/entrenador/", "/diccionario/", "/reportes/REP-01"):
        assert cli.get(ruta).status_code == 403, ruta
    for ruta in ("/admin/pagos", "/cliente/", "/diccionario/", "/reportes/REP-03", "/reportes/REP-09"):
        assert ent.get(ruta).status_code == 403, ruta
    for ruta in ("/entrenador/rutinas", "/cliente/", "/entrenador/clientes"):
        assert adm.get(ruta).status_code == 403, ruta


def test_entrenador_solo_ve_sus_clientes(app):
    ent = entrar(app, ENT)                    # entrenador 2: cliente 4 si, cliente 5 no
    assert ent.get("/entrenador/clientes/4").status_code == 200
    assert ent.get("/entrenador/clientes/5").status_code == 403


def test_cliente_solo_ve_su_rutina(app):
    cli = entrar(app, CLI)                    # Mateo (4): asignacion 1 suya, 2 de Sofia
    assert cli.get("/cliente/rutinas/1").status_code == 200
    assert cli.get("/cliente/rutinas/2").status_code == 403


def test_informes_por_rol_usan_su_id(app, gw):
    entrar(app, ENT).get("/reportes/REP-05")
    assert ("pkg_reportes.rep05_ranking_asistencia", (2,)) in gw.llamadas
    entrar(app, CLI).get("/reportes/REP-06")
    assert ("pkg_reportes.rep06_rachas", (None, 4)) in gw.llamadas


def test_validaciones_de_formulario(app, gw):
    c = entrar(app, ADMIN)
    r = post(c, "/admin/usuarios/nuevo", ruta_token="/admin/usuarios/nuevo", identificacion="12", nombre="X",
             apellido="1", correo="mal", telefono="123", rol_id="3", clave="abc")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    for msg in ("5 y 15 digitos", "nombre valido", "correo electronico valido", "celular de 10", "al menos 8"):
        assert msg in html, msg
    assert not any(n == "pkg_usuario.insertar" for n, _ in gw.llamadas)


def test_crear_usuario_llama_paquete(app, gw):
    c = entrar(app, ADMIN)
    r = post(c, "/admin/usuarios/nuevo", ruta_token="/admin/usuarios/nuevo", identificacion="1099000001",
             nombre="Ana", apellido="Perez", correo="ana@x.co", telefono="3201234567", rol_id="3", clave="Clave2026x")
    assert r.status_code == 302
    llamada = next(p for n, p in gw.llamadas if n == "pkg_usuario.insertar")
    assert llamada[5].startswith("pbkdf2:")        # se envia el hash, no la clave


def test_error_de_regla_de_negocio_se_muestra(app, gw):
    gw.falla_con["pkg_pago.registrar"] = "El pago ($ 100.000) supera el saldo pendiente ($ 45.000)."
    c = entrar(app, ADMIN)
    r = post(c, "/admin/pagos/nuevo", ruta_token="/admin/pagos/nuevo", cli_mem_id="2", valor="100000",
             metodo="EFECTIVO", estado="PAGADO")
    assert r.status_code == 200 and "supera el saldo" in r.get_data(as_text=True)


def test_cliente_registra_asistencia_con_su_id(app, gw):
    c = entrar(app, CLI)
    # intento de suplantar: el id viene de la sesion, no del formulario
    post(c, "/cliente/asistencia", ruta_token="/cliente/", usu_id="5")
    assert ("pkg_asistencia.registrar", (4,)) in gw.llamadas


def test_entrenador_modifica_con_su_id(app, gw):
    c = entrar(app, ENT)
    post(c, "/entrenador/asignaciones/1/cerrar", ruta_token="/entrenador/asignaciones", estado="FINALIZADA")
    assert ("pkg_rutina.cerrar_asignacion", (1, 2, "FINALIZADA")) in gw.llamadas


def test_no_se_puede_desactivar_a_si_mismo(app, gw):
    c = entrar(app, ADMIN)
    post(c, "/admin/usuarios/1/estado", ruta_token="/admin/usuarios", estado="INACTIVO")
    assert not any(n == "pkg_usuario.cambiar_estado" for n, _ in gw.llamadas)


def test_cabeceras_y_logout(app):
    c = entrar(app, ADMIN)
    r = c.get("/admin/")
    assert r.headers["X-Frame-Options"] == "DENY" and "default-src 'self'" in r.headers["Content-Security-Policy"]
    assert "style=" not in r.get_data(as_text=True).replace("style-src", "")   # compatible con la CSP
    post(c, "/logout", ruta_token="/perfil")
    assert c.get("/admin/").status_code == 302


def test_404(app):
    assert entrar(app, ADMIN).get("/admin/usuarios/abc/editar").status_code == 404
    assert entrar(app, ADMIN).get("/diccionario/tabla/NOEXISTE").status_code == 404
    assert entrar(app, ADMIN).get("/diccionario/tabla/x;drop").status_code == 404


def test_descarga_csv_con_bom_y_rol(app):
    c = entrar(app, ADMIN)
    r = c.get("/reportes/REP-01/csv")
    assert r.status_code == 200 and r.mimetype == "text/csv"
    assert r.get_data(as_text=True).startswith("﻿")
    assert "attachment" in r.headers["Content-Disposition"]
    assert entrar(app, CLI).get("/reportes/REP-01/csv").status_code in (403, 404)


def test_tableros_con_graficos_sin_estilos_en_linea(app):
    for correo, ruta in ((ADMIN, "/admin/"), (ENT, "/entrenador/"), (CLI, "/cliente/")):
        html = entrar(app, correo).get(ruta).get_data(as_text=True)
        assert "<svg" in html or "progress" in html or "sy-" in html
        assert ' style="' not in html          # la CSP prohibe estilos en linea


def test_calendario_del_cliente(app):
    r = entrar(app, CLI).get("/cliente/asistencias")
    assert r.status_code == 200

"""
SAIYAGYM - aplicacion web (Flask + Oracle).

Arquitectura por capas:
    web/            -> controladores (blueprints) y vistas
    services/       -> reglas de aplicacion: autenticacion, validacion, formatos
    repositories/   -> acceso a datos: solo llaman paquetes PL/SQL (PKG_*)
    db/             -> pasarela a Oracle (pool, manejo de errores ORA-20xxx)
    security/       -> control de acceso por rol y proteccion CSRF
    templates/      -> pagina maestra (base.html) y vistas por rol
    static/         -> estilos y scripts
"""
from __future__ import annotations
import os
from datetime import timedelta
from types import SimpleNamespace

from flask import Flask, render_template, request, session, url_for

from .config import Config
from .db.gateway import AppError, Gateway
from .repositories.asistencia_repo import AsistenciaRepo
from .repositories.membresia_repo import MembresiaRepo
from .repositories.pago_repo import PagoRepo
from .repositories.reporte_repo import DiccionarioRepo, ReporteRepo
from .repositories.rutina_repo import RutinaRepo
from .repositories.usuario_repo import UsuarioRepo
from .security import csrf
from .security.decorators import usuario_actual
from .services import formatters
from .services.auth_service import AuthService


def construir_servicios(gateway) -> SimpleNamespace:
    usuarios = UsuarioRepo(gateway)
    cfg = Config
    return SimpleNamespace(
        gateway=gateway,
        usuarios=usuarios,
        membresias=MembresiaRepo(gateway),
        pagos=PagoRepo(gateway),
        rutinas=RutinaRepo(gateway),
        asistencias=AsistenciaRepo(gateway),
        reportes=ReporteRepo(gateway),
        diccionario=DiccionarioRepo(gateway),
        auth=AuthService(usuarios, cfg.LOGIN_MAX_INTENTOS, cfg.LOGIN_BLOQUEO_SEGUNDOS),
    )


def create_app(gateway=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.permanent_session_lifetime = timedelta(minutes=app.config["SESSION_MINUTES"])

    if app.config["PRODUCCION"]:
        if app.config["SECRET_KEY"].startswith("dev-solo"):
            raise RuntimeError("En produccion defina SAIYA_SECRET_KEY con una clave larga y aleatoria.")
        from werkzeug.middleware.proxy_fix import ProxyFix   # detras del proxy HTTPS del hosting
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    cfg = {k: app.config[k] for k in ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN", "ORACLE_SCHEMA",
                                       "ORACLE_CONFIG_DIR", "ORACLE_WALLET_DIR", "ORACLE_WALLET_PASSWORD")}
    app.extensions["saiya"] = construir_servicios(gateway or Gateway(cfg))

    # -- filtros y globales de plantilla ----------------------------------
    app.jinja_env.filters.update(
        moneda=formatters.moneda, moneda_corta=formatters.moneda_corta, fecha=formatters.fecha, fecha_larga=formatters.fecha_larga,
        fecha_input=formatters.fecha_input, clase_estado=formatters.clase_estado,
    )
    app.jinja_env.globals.update(csrf_token=csrf.token, iniciales=formatters.iniciales)

    def estatico(ruta: str) -> str:
        """URL de un estatico con ?v=<fecha de modificacion> para no servir copias viejas del navegador."""
        try:
            version = int(os.path.getmtime(os.path.join(app.static_folder, ruta)))
        except OSError:
            version = 0
        return url_for("static", filename=ruta, v=version)

    app.jinja_env.globals.update(estatico=estatico)

    @app.context_processor
    def contexto():
        return {"usuario": usuario_actual(), "endpoint": request.endpoint or ""}

    # -- seguridad --------------------------------------------------------
    @app.before_request
    def proteger():
        csrf.verificar()

    @app.after_request
    def cabeceras(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'")
        if request.endpoint and request.endpoint != "static":
            resp.headers["Cache-Control"] = "no-store"
        return resp

    # -- blueprints -------------------------------------------------------
    from .web import admin, auth, cliente, diccionario, entrenador, reportes
    for modulo in (auth, admin, entrenador, cliente, reportes, diccionario):
        app.register_blueprint(modulo.bp)

    # -- errores ----------------------------------------------------------
    @app.errorhandler(AppError)
    def error_app(e):
        return render_template("errors/error.html", titulo="No se pudo completar",
                               mensaje=e.mensaje, codigo=""), 400

    @app.errorhandler(403)
    def prohibido(e):
        return render_template("errors/error.html", titulo="Acceso restringido",
                               mensaje="Tu rol no tiene permiso para ver esta pagina.", codigo=403), 403

    @app.errorhandler(404)
    def no_encontrado(e):
        return render_template("errors/error.html", titulo="No encontramos esa pagina",
                               mensaje="Revisa el enlace o vuelve al inicio.", codigo=404), 404

    @app.errorhandler(400)
    def solicitud_invalida(e):
        return render_template("errors/error.html", titulo="Solicitud no valida",
                               mensaje=getattr(e, "description", "La solicitud no es valida."),
                               codigo=400), 400

    @app.errorhandler(500)
    def error_interno(e):
        return render_template("errors/error.html", titulo="Algo salio mal",
                               mensaje="Ocurrio un error inesperado. Intenta de nuevo.", codigo=500), 500

    return app


def servicios() -> SimpleNamespace:
    from flask import current_app
    return current_app.extensions["saiya"]

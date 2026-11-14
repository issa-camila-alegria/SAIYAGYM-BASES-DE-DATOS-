"""Configuracion de la aplicacion (variables de entorno o archivo .env)."""
from __future__ import annotations
import os
from pathlib import Path


def _cargar_env() -> None:
    """Lee un archivo .env sencillo (CLAVE=valor) sin dependencias externas."""
    ruta = Path(__file__).resolve().parent.parent / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip())


_cargar_env()


class Config:
    SECRET_KEY = os.environ.get("SAIYA_SECRET_KEY", "dev-solo-para-desarrollo-cambiar")
    ORACLE_USER = os.environ.get("SAIYA_ORACLE_USER", "saiya_app")
    ORACLE_PASSWORD = os.environ.get("SAIYA_ORACLE_PASSWORD", "App#2026")
    ORACLE_DSN = os.environ.get("SAIYA_ORACLE_DSN", "localhost:1521/XEPDB1")
    ORACLE_SCHEMA = os.environ.get("SAIYA_ORACLE_SCHEMA", "SAIYAGYM")
    # Oracle Autonomous Database (nube): carpeta con tnsnames.ora / ewallet.pem y clave de la wallet.
    # Si no se definen, la conexion es la local de siempre.
    ORACLE_CONFIG_DIR = os.environ.get("SAIYA_ORACLE_CONFIG_DIR") or None
    ORACLE_WALLET_DIR = os.environ.get("SAIYA_ORACLE_WALLET_DIR") or None
    ORACLE_WALLET_PASSWORD = os.environ.get("SAIYA_ORACLE_WALLET_PASSWORD") or None
    # Publicacion en internet: SAIYA_PRODUCCION=1 exige clave secreta propia y cookies solo-HTTPS
    PRODUCCION = os.environ.get("SAIYA_PRODUCCION") == "1"
    SESSION_COOKIE_SECURE = PRODUCCION
    SESSION_MINUTES = int(os.environ.get("SAIYA_SESSION_MINUTES", "60"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Intentos de inicio de sesion fallidos antes de bloquear temporalmente
    LOGIN_MAX_INTENTOS = 5
    LOGIN_BLOQUEO_SEGUNDOS = 300

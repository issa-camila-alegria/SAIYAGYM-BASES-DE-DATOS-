"""Diagnostico del login: usa la MISMA ruta que la app (saiya_app -> PKG_USUARIO).
Uso (con el entorno virtual activo, dentro de 05_Aplicacion):
    python diagnostico_login.py laura.gomez@saiyagym.com "Saiya2026*"
"""
from __future__ import annotations
import sys
from werkzeug.security import check_password_hash

from saiyagym.config import Config
from saiyagym.db.gateway import Gateway

correo = sys.argv[1] if len(sys.argv) > 1 else "laura.gomez@saiyagym.com"
clave = sys.argv[2] if len(sys.argv) > 2 else "Saiya2026*"

gw = Gateway({k: getattr(Config, k) for k in dir(Config) if k.isupper()})
print("Usuario Oracle :", Config.ORACLE_USER, "->", Config.ORACLE_DSN)
try:
    fila = gw.fila("pkg_usuario.obtener_por_correo", correo)
except Exception as e:  # noqa: BLE001
    print("ERROR al consultar la base de datos:", e)
    sys.exit(1)
if not fila:
    print("RESULTADO: la base de datos NO devolvio ningun usuario con ese correo.")
    sys.exit(2)
print("Usuario encontrado:", fila["usunombre"], fila["usuapellido"], "| estado:", fila["usuestado"], "| rol:", fila["rolnombre"])
h = fila["usucontrasena"]
print("Largo del hash :", len(h))
print("Clave correcta :", check_password_hash(h, clave))

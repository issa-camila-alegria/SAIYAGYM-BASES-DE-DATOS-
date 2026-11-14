"""Autenticacion: verificacion de contrasenas (hash) y proteccion contra fuerza bruta."""
from __future__ import annotations
import threading
import time

from werkzeug.security import check_password_hash, generate_password_hash

from ..db.gateway import AppError
from ..repositories.usuario_repo import UsuarioRepo


def hash_clave(clave: str) -> str:
    """PBKDF2-SHA256 con sal aleatoria (nunca se guarda la clave en texto plano)."""
    return generate_password_hash(clave, method="pbkdf2:sha256:260000")


class AuthService:
    def __init__(self, usuarios: UsuarioRepo, max_intentos: int, bloqueo_s: int):
        self.usuarios = usuarios
        self.max_intentos = max_intentos
        self.bloqueo_s = bloqueo_s
        self._fallos: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    # -- limite de intentos ---------------------------------------------
    def _recientes(self, clave: str) -> list[float]:
        ahora = time.time()
        vigentes = [t for t in self._fallos.get(clave, []) if ahora - t < self.bloqueo_s]
        self._fallos[clave] = vigentes
        return vigentes

    def bloqueado(self, clave: str) -> bool:
        with self._lock:
            return len(self._recientes(clave)) >= self.max_intentos

    def _registrar_fallo(self, clave: str) -> None:
        with self._lock:
            self._recientes(clave).append(time.time())

    def _limpiar(self, clave: str) -> None:
        with self._lock:
            self._fallos.pop(clave, None)

    # -- inicio de sesion -----------------------------------------------
    def autenticar(self, correo: str, clave: str, origen: str) -> dict:
        """Devuelve el usuario si las credenciales son validas; AppError si no."""
        llave = f"{origen}|{correo.lower()}"
        if self.bloqueado(llave):
            raise AppError("Demasiados intentos fallidos. Espere unos minutos e intente de nuevo.")
        usuario = self.usuarios.obtener_por_correo(correo)
        # Mismo mensaje para correo inexistente o clave incorrecta (no revela cuentas)
        if not usuario or not check_password_hash(usuario["usucontrasena"], clave):
            self._registrar_fallo(llave)
            raise AppError("Correo o contrasena incorrectos.")
        if usuario["usuestado"] != "ACTIVO":
            raise AppError("Su cuenta esta inactiva. Comuniquese con el administrador del gimnasio.")
        self._limpiar(llave)
        return usuario

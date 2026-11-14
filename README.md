# SAIYAGYM – Aplicación web (Componente 3)

Aplicación Flask + `python-oracledb` sobre Oracle 18c. **Todo el acceso a datos pasa por procedimientos y funciones de los paquetes `PKG_*`**; la aplicación no ejecuta SQL propio.

## Requisitos
- Python 3.10+
- Base de datos instalada (ver `../README.md`) y usuario `saiya_app` creado

## Puesta en marcha
```bash
cd 05_Aplicacion
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # ajuste DSN, clave y secreto
python run.py                                           # http://127.0.0.1:5000
```
Pruebas (no requieren Oracle, usan un gateway simulado): `pip install pytest && python -m pytest tests -q`

## Usuarios de demostración (contraseña `Saiya2026*`)
| Rol | Correo |
|---|---|
| Administrador | laura.gomez@saiyagym.com |
| Entrenador | carlos.mendoza@saiyagym.com, andrea.ruiz@saiyagym.com |
| Cliente | mateo.herrera@gmail.com (y los demás clientes de `DATOS.sql`) |

## Arquitectura (capas)
```
saiyagym/
  web/            Blueprints por rol (auth, admin, entrenador, cliente, reportes, diccionario)
  services/       Validadores de formato, formateadores, autenticación
  repositories/   Un repositorio por paquete PKG_*; solo llaman procedimientos
  db/gateway.py   Pool oracledb, esquema SAIYAGYM, traducción ORA-20xxx -> mensajes
  security/       Decoradores de rol y protección CSRF
  templates/      Página maestra (base.html) y vistas por rol
  static/         CSS y JS (sin estilos ni scripts en línea: CSP estricta)
tests/            72 pruebas (roles, aislamiento de datos, CSRF, validaciones)
```

## Seguridad
- Contraseñas con PBKDF2-SHA256; bloqueo de 5 minutos tras 5 intentos fallidos.
- Sesión regenerada al iniciar sesión; token CSRF en todo POST; redirección `next` validada.
- Cabeceras de seguridad y CSP `default-src 'self'`.
- Restricción por rol en cada ruta (`roles_required`) **y** en los paquetes de base de datos (un entrenador solo ve sus clientes y edita sus rutinas; el cliente solo ve lo propio, su id sale de la sesión).
- La cuenta `saiya_app` solo tiene `CREATE SESSION` y `EXECUTE` sobre los paquetes `PKG_*`.

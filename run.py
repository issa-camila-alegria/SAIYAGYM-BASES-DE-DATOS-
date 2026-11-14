"""Punto de entrada de SAIYAGYM.  Uso:  python run.py"""
from __future__ import annotations
from saiyagym import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

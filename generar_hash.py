"""Genera los datos de login para los secrets. Ejecutar una vez: python generar_hash.py
Copiá lo que imprime en la sección [auth] de .streamlit/secrets.toml (o en los secrets de la app).
"""
import getpass
import secrets

from auth import hashear

usuario = input("Usuario: ").strip()
clave = getpass.getpass("Contraseña nueva: ")
confirmar = getpass.getpass("Repetí la contraseña: ")
if clave != confirmar:
    raise SystemExit("Las contraseñas no coinciden.")
if len(clave) < 10:
    raise SystemExit("Usá una contraseña de al menos 10 caracteres.")

salt = secrets.token_hex(16)
print("\n[auth]")
print(f'usuario = "{usuario}"')
print(f'salt = "{salt}"')
print(f'password_hash = "{hashear(clave, salt)}"')

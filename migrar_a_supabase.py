"""Copia los datos de astech.db (la base SQLite de tu PC) a la base de Supabase.

Cómo se usa (desde la carpeta del proyecto):
    1. Tener la cadena de conexión en .streamlit/secrets.toml como [db] url = "..."
       (o en la variable de entorno DATABASE_URL).
    2. python migrar_a_supabase.py

Es seguro correrlo más de una vez: lo que ya existe en Supabase no se duplica.
Las fotos de la carpeta imagenes/ también se suben a la base.
"""
import sqlite3
from pathlib import Path

import amway_db
import db
import presupuesto_db

ORIGEN = Path(__file__).parent / "astech.db"
CARPETA_FOTOS = Path(__file__).parent / "imagenes"

# En este orden, para respetar las claves entre tablas
TABLAS = [
    "clientes", "productos", "operaciones", "operacion_items",
    "pres_meses", "pres_ingresos", "pres_fijos", "pres_suscripciones", "pres_gastos",
    "amway_asociados", "amway_registros", "amway_productos",
]


def columnas_destino(con, tabla):
    filas = con.execute(
        "SELECT column_name AS c FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = ?", (tabla,)
    ).fetchall()
    return {f["c"] for f in filas}


def copiar_tabla(origen, con, tabla):
    existe = origen.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabla,)).fetchone()
    if not existe:
        print(f"  {tabla}: no está en astech.db, se saltea")
        return 0
    cols_origen = [f[1] for f in origen.execute(f"PRAGMA table_info({tabla})").fetchall()]
    cols = [c for c in cols_origen if c in columnas_destino(con, tabla)]
    filas = origen.execute(f"SELECT {', '.join(cols)} FROM {tabla}").fetchall()
    marcadores = ", ".join("?" for _ in cols)
    copiadas = 0
    for fila in filas:
        cur = con.execute(
            f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({marcadores}) ON CONFLICT DO NOTHING",
            tuple(fila),
        )
        copiadas += cur.rowcount
    print(f"  {tabla}: {len(filas)} en astech.db, {copiadas} nuevas en Supabase")
    return copiadas


def ajustar_contadores(con, tabla):
    """Para que los próximos registros nuevos no choquen con los ids copiados."""
    con.execute(
        f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) "
        f"FROM {tabla}"
    )


def subir_fotos(origen, con):
    filas = origen.execute("SELECT DISTINCT imagen FROM productos WHERE imagen IS NOT NULL AND imagen <> ''").fetchall()
    subidas = 0
    for (nombre,) in filas:
        archivo = CARPETA_FOTOS / nombre
        if archivo.exists():
            db.guardar_imagen_bytes(nombre, archivo.read_bytes())
            subidas += 1
        else:
            print(f"  foto no encontrada en imagenes/: {nombre}")
    print(f"  fotos subidas: {subidas} de {len(filas)}")


def main():
    if not ORIGEN.exists():
        raise SystemExit(f"No encontré {ORIGEN}")

    print("Creando tablas en Supabase (si no existen)...")
    db.crear_tablas()
    presupuesto_db.crear_tablas()
    amway_db.crear_tablas()

    origen = sqlite3.connect(ORIGEN)
    con = db.conectar()
    try:
        print("Copiando datos:")
        for tabla in TABLAS:
            copiar_tabla(origen, con, tabla)
        con.commit()

        print("Subiendo fotos:")
        subir_fotos(origen, con)

        for tabla in TABLAS:
            ajustar_contadores(con, tabla)
        con.commit()
        print("Listo.")
    finally:
        con.close()
        origen.close()


if __name__ == "__main__":
    main()

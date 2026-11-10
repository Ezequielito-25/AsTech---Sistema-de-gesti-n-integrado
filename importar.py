"""Importación masiva de productos desde una planilla (CSV o Excel)."""
import io
from pathlib import Path

import pandas as pd
import streamlit as st

import db

COLUMNAS_REQUERIDAS = ["descripcion", "precio_ars", "precio_usd"]
COLUMNA_OPCIONAL = "imagen"
# Carpeta con las fotos en tu PC, desde donde se suben a la base al importar
CARPETA_FOTOS = Path(__file__).parent / "imagenes"


def plantilla_csv():
    """Devuelve una plantilla CSV de ejemplo para descargar."""
    df = pd.DataFrame([
        {"descripcion": "Memoria RAM 8GB DDR4", "precio_ars": 25000, "precio_usd": 25, "imagen": ""},
        {"descripcion": "Disco SSD 480GB", "precio_ars": 45000, "precio_usd": 45, "imagen": ""},
    ])
    return df.to_csv(index=False).encode("utf-8-sig")


def leer_planilla(archivo):
    """Lee el archivo subido (CSV o Excel) y devuelve un DataFrame."""
    if archivo.name.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(archivo.getvalue()), sep=None, engine="python")
    return pd.read_excel(io.BytesIO(archivo.getvalue()))


def importar_productos(df):
    """Valida el DataFrame y guarda los productos. Devuelve (cargados, errores)."""
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltan:
        return 0, [f"Faltan columnas obligatorias: {', '.join(faltan)}"]

    cargados, errores = 0, []
    for i, fila in df.iterrows():
        num_fila = i + 2  # +2: encabezado y numeración desde 1
        descripcion = str(fila["descripcion"]).strip() if pd.notna(fila["descripcion"]) else ""
        if not descripcion or descripcion.lower() == "nan":
            errores.append(f"Fila {num_fila}: falta la descripción (no se cargó).")
            continue
        try:
            ars = float(fila["precio_ars"]) if pd.notna(fila["precio_ars"]) else 0.0
            usd = float(fila["precio_usd"]) if pd.notna(fila["precio_usd"]) else 0.0
        except (TypeError, ValueError):
            errores.append(f"Fila {num_fila} ({descripcion}): precio inválido (no se cargó).")
            continue

        imagen = None
        if COLUMNA_OPCIONAL in df.columns and pd.notna(fila[COLUMNA_OPCIONAL]):
            nombre = str(fila[COLUMNA_OPCIONAL]).strip()
            ruta_local = CARPETA_FOTOS / nombre if nombre else None
            if ruta_local and ruta_local.exists():
                imagen = db.guardar_imagen_bytes(nombre, ruta_local.read_bytes())
            elif nombre:
                errores.append(f"Fila {num_fila} ({descripcion}): no encontré la imagen '{nombre}' en la carpeta imagenes de tu PC (se cargó sin foto).")

        db.agregar_producto(descripcion, ars, usd, imagen)
        cargados += 1
    return cargados, errores


def render_importador():
    """Muestra la sección de importación dentro de la página de Productos."""
    with st.expander("📥 Importar productos desde una planilla (Excel o CSV)", expanded=False):
        st.markdown(
            "Armá una planilla con estas columnas:\n\n"
            "- **descripcion** (obligatoria)\n"
            "- **precio_ars** (obligatoria)\n"
            "- **precio_usd** (obligatoria)\n"
            "- **imagen** (opcional): nombre del archivo de la foto, copiada en la carpeta `imagenes`"
        )
        st.download_button("⬇️ Descargar plantilla de ejemplo (CSV)", data=plantilla_csv(),
                           file_name="plantilla_productos.csv", mime="text/csv")

        archivo = st.file_uploader("Subir planilla", type=["csv", "xlsx", "xls"], key="import_archivo")
        if archivo is not None:
            try:
                df = leer_planilla(archivo)
            except ImportError:
                st.error("Para leer Excel hace falta instalar una librería. En la terminal ejecutá: "
                         "python -m pip install openpyxl  (o subí la planilla en formato CSV).")
                return
            except Exception as e:
                st.error(f"No pude leer el archivo: {e}")
                return

            st.write(f"Se encontraron **{len(df)}** filas. Vista previa:")
            st.dataframe(df.head(10), use_container_width=True, hide_index=True)

            if st.button("Cargar todos los productos", type="primary", key="btn_importar"):
                cargados, errores = importar_productos(df)
                if cargados:
                    st.success(f"Se cargaron {cargados} productos.")
                for e in errores:
                    st.warning(e)

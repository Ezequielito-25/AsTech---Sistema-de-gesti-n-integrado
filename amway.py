"""Apartado Amway: catálogo de productos, ventas mensuales, búsqueda y edición de personas,
asociados y resumen anual. Es independiente de la tienda y de 'Mi presupuesto personal'."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import amway_db as adb

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _config_tabla(df):
    """Columnas de la tabla mensual. La de producto muestra el catálogo para elegir."""
    cfg = {
        "nombre": st.column_config.TextColumn("Nombre y apellido", required=True),
        "telefono": st.column_config.TextColumn("Teléfono / contacto"),
        "direccion": st.column_config.TextColumn("Dirección"),
        "fecha": st.column_config.DateColumn("Fecha de compra", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor de compra", min_value=0, step=100, format="$%.0f"),
        "puntos": st.column_config.NumberColumn("Puntos", min_value=0, step=1),
    }
    usados = [v for v in df["descripcion"].dropna().unique().tolist() if str(v).strip()]
    opciones = sorted(set(adb.nombres_productos_amway()) | set(usados), key=str.lower)
    if opciones:
        cfg["descripcion"] = st.column_config.SelectboxColumn(
            "Producto comprado", options=opciones, width="large",
            help="Elegí un producto del catálogo. Si no está, cargalo en la sección 🧴 Catálogo.")
    else:
        cfg["descripcion"] = st.column_config.TextColumn("Producto comprado", width="large")
    return cfg


def _opciones_producto(actual):
    """Lista de productos del catálogo, con el valor actual incluido aunque ya no esté en el catálogo."""
    opciones = [""] + adb.nombres_productos_amway()
    actual = actual or ""
    if actual and actual not in opciones:
        opciones.append(actual)
    return opciones, opciones.index(actual)


# ---------------------------------------------------------------- VENTAS DEL MES
def _metricas(tipo, anio, mes):
    t = adb.totales(tipo, anio, mes)
    c1, c2, c3 = st.columns(3)
    c1.metric("Compras cargadas", t["filas"])
    c2.metric("Total ventas", f"$ {t['ventas']:,.0f}")
    c3.metric("Total de puntos", f"{t['puntos']:,.0f}")


def _tabla_mes(tipo, anio, mes):
    """Tabla editable del mes (como una hoja de la planilla)."""
    df = adb.listar(tipo, anio, mes).drop(columns=["numero"])
    with st.form(f"form_amway_{tipo}_{anio}_{mes}"):
        st.caption("Podés editar cualquier celda, agregar filas o borrarlas. Después tocá Guardar.")
        editado = st.data_editor(df, num_rows="dynamic", hide_index=True, use_container_width=True,
                                 column_config=_config_tabla(df), key=f"ed_amway_{tipo}_{anio}_{mes}")
        guardar = st.form_submit_button("💾 Guardar", type="primary")
    if guardar:
        adb.reemplazar(tipo, anio, mes, editado)
        st.success("Guardado.")
        st.rerun()
    _metricas(tipo, anio, mes)


def _ventas_del_mes():
    hoy = date.today()
    c1, c2 = st.columns([1, 2])
    anio = int(c1.number_input("Año", min_value=2020, max_value=2100, value=hoy.year, step=1,
                               key="amway_anio"))
    mes = c2.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1,
                       format_func=lambda m: MESES[m - 1], key="amway_mes")

    tab_cli, tab_aso = st.tabs(["🛒 Clientes (compras)", "👥 Asociados (equipo)"])
    with tab_cli:
        st.caption("Personas que solo compran productos.")
        _tabla_mes("cliente", anio, mes)
    with tab_aso:
        st.caption("Compras de los asociados. Las altas nuevas se registran en la sección 🤝 Asociados.")
        _tabla_mes("asociado", anio, mes)


# ---------------------------------------------------------------- BUSCAR Y EDITAR PERSONAS
def _editar_persona(g, tipo):
    """Edición de una persona: sus datos (en todas sus compras) y cada compra por separado."""
    ids = [c["id"] for c in g["compras"]]
    base = ids[0]

    with st.form(f"form_persona_{tipo}_{base}"):
        st.markdown("**Datos de la persona** (se cambian en todas sus compras)")
        c1, c2 = st.columns(2)
        p_nombre = c1.text_input("Nombre y apellido", value=g["nombre"], key=f"pn_{tipo}_{base}")
        p_tel = c2.text_input("Teléfono / contacto", value=g["telefono"] or "", key=f"pt_{tipo}_{base}")
        p_dir = st.text_input("Dirección", value=g["direccion"] or "", key=f"pdir_{tipo}_{base}")
        if st.form_submit_button("Guardar datos de la persona", type="primary"):
            if not p_nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                adb.actualizar_persona(ids, p_nombre, p_tel, p_dir)
                st.success("Datos actualizados en todas sus compras.")

    st.markdown("**Compras**")
    for c in g["compras"]:
        cid = c["id"]
        st.markdown(f"---\n**{MESES[c['mes'] - 1]} {c['anio']}** · {c['descripcion'] or 'sin producto'}")
        with st.form(f"form_compra_{cid}"):
            c1, c2 = st.columns(2)
            fecha_val = date.fromisoformat(c["fecha"]) if c["fecha"] else date.today()
            f_fecha = c1.date_input("Fecha de compra", value=fecha_val, format="DD/MM/YYYY",
                                    key=f"cf_{cid}")
            opciones_p, idx = _opciones_producto(c["descripcion"])
            f_desc = c2.selectbox("Producto comprado", opciones_p, index=idx, key=f"cd_{cid}")
            c3, c4 = st.columns(2)
            f_valor = c3.number_input("Valor de compra ($)", min_value=0.0, step=100.0,
                                      value=float(c["valor"]), key=f"cv_{cid}")
            f_pts = c4.number_input("Puntos", min_value=0.0, step=1.0,
                                    value=float(c["puntos"]), key=f"cp_{cid}")
            b1, b2 = st.columns(2)
            guardar = b1.form_submit_button("Guardar esta compra", type="primary")
            borrar = b2.form_submit_button("Eliminar esta compra")
        if guardar:
            adb.actualizar_compra(cid, f_fecha, f_desc.strip(), f_valor, f_pts)
            st.success("Compra actualizada.")
        if borrar:
            adb.eliminar_compra(cid)
            st.rerun()


def _buscar_personas():
    texto = st.text_input("🔎 Buscar persona", placeholder="Nombre o número de teléfono",
                          key="amway_buscar")
    tipo_txt = st.radio("Buscar en", ["Clientes", "Asociados"], horizontal=True, key="amway_tipo_busq")
    tipo = "cliente" if tipo_txt == "Clientes" else "asociado"

    personas = adb.buscar_personas(tipo, texto)
    if not personas:
        st.info("No encontré personas con esa búsqueda.")
        return
    st.caption(f"{len(personas)} resultado(s)")
    for g in personas[:50]:
        titulo = (f"{g['nombre']} · {g['telefono'] or 'sin teléfono'} · "
                  f"$ {g['total_valor']:,.0f} · {g['total_puntos']:,.0f} pts")
        with st.expander(titulo):
            _editar_persona(g, tipo)


# ---------------------------------------------------------------- CATÁLOGO DE PRODUCTOS
def _catalogo():
    from amway_catalogo_web import CATALOGO_WEB

    st.markdown("Cargá tus productos Amway con su descripción, beneficios y precios. Después los elegís "
                "en la columna de producto de cada compra.")

    with st.expander(f"📥 Cargar el catálogo oficial de amway.com.ar ({len(CATALOGO_WEB)} fichas)"):
        st.markdown("Trae los productos de Soluciones, Nutrición, Belleza, Cuidado Personal y Hogar, "
                    "con accesorios. Los tonos de una misma línea van en una sola ficha. "
                    "No duplica lo que ya tengas cargado.")
        ya = {adb._normalizar(n) for n in adb.nombres_productos_amway()}
        vista = pd.DataFrame([{
            "Categoría": it["categoria"],
            "Producto": it["nombre"],
            "Precio cliente (ARS)": it.get("precio_cliente"),
            "Beneficios": len(it.get("beneficios", [])),
            "Ya cargado": "Sí" if adb._normalizar(it["nombre"]) in ya else "No",
        } for it in CATALOGO_WEB])
        st.dataframe(vista, hide_index=True, use_container_width=True,
                     column_config={"Precio cliente (ARS)": st.column_config.NumberColumn(format="$ %.2f")})
        st.caption("El sitio muestra un solo precio. El de empresario queda vacío: completalo editando "
                   "cada producto. Los precios pueden cambiar en el sitio.")
        pendientes = int((vista["Ya cargado"] == "No").sum())
        if st.button(f"Cargar {pendientes} producto(s) nuevos", type="primary",
                     disabled=pendientes == 0, key="btn_importar_web"):
            cargados, omitidos = adb.importar_catalogo_web(CATALOGO_WEB)
            st.success(f"Se cargaron {cargados} productos. Se omitieron {len(omitidos)} que ya existían.")

    with st.form("form_producto_amway", clear_on_submit=True):
        nombre = st.text_input("Nombre del producto *")
        descripcion = st.text_area("Descripción")
        beneficios = st.text_area("Beneficios")
        pa1, pa2 = st.columns(2)
        precio_cli_nuevo = pa1.number_input("Precio para cliente (ARS)", min_value=0.0, step=100.0, value=0.0)
        precio_emp_nuevo = pa2.number_input("Precio para empresario (ARS)", min_value=0.0, step=100.0, value=0.0)
        guardar = st.form_submit_button("Agregar al catálogo", type="primary")
    if guardar:
        if not nombre.strip():
            st.error("El nombre es obligatorio.")
        elif not adb.agregar_producto_amway(nombre, descripcion, beneficios,
                                            precio_cliente=precio_cli_nuevo or None,
                                            precio_empresario=precio_emp_nuevo or None):
            st.error("Ya existe un producto con ese nombre.")
        else:
            st.success("Producto agregado al catálogo.")

    texto = st.text_input("🔎 Buscar producto", placeholder="Nombre, descripción o beneficio",
                          key="cat_buscar")
    productos = adb.listar_productos_amway(texto)
    if not productos:
        st.info("No hay productos que coincidan." if texto.strip() else "Todavía no cargaste productos.")
        return
    st.caption(f"{len(productos)} producto(s)")
    for p in productos:
        pid = p["id"]
        with st.expander(p["nombre"]):
            if p.get("categoria"):
                st.caption(f"Categoría: {p['categoria']}")
            if p["descripcion"]:
                st.markdown(f"**Descripción:** {p['descripcion']}")
            if p["beneficios"]:
                st.markdown(f"**Beneficios:**\n{p['beneficios']}")
            pr_cli = p.get("precio_cliente")
            pr_emp = p.get("precio_empresario")
            st.markdown(f"**Precio cliente:** {'$ {:,.2f}'.format(pr_cli) if pr_cli else 'sin precio'}  ·  "
                        f"**Precio empresario:** {'$ {:,.2f}'.format(pr_emp) if pr_emp else 'sin cargar'}")
            with st.form(f"form_cat_{pid}"):
                n = st.text_input("Nombre", value=p["nombre"], key=f"cn_{pid}")
                d = st.text_area("Descripción", value=p["descripcion"] or "", key=f"cdsc_{pid}")
                b = st.text_area("Beneficios", value=p["beneficios"] or "", key=f"cb_{pid}")
                pc1, pc2 = st.columns(2)
                pcli = pc1.number_input("Precio para cliente (ARS)", min_value=0.0, step=100.0,
                                        value=float(pr_cli or 0), key=f"cpc_{pid}")
                pemp = pc2.number_input("Precio para empresario (ARS)", min_value=0.0, step=100.0,
                                        value=float(pr_emp or 0), key=f"cpe_{pid}")
                c1, c2 = st.columns(2)
                guardar_p = c1.form_submit_button("Guardar cambios", type="primary")
                borrar_p = c2.form_submit_button("Eliminar producto")
            if guardar_p:
                if not n.strip():
                    st.error("El nombre es obligatorio.")
                elif not adb.actualizar_producto_amway(pid, n, d, b,
                                                       precio_cliente=pcli or None,
                                                       precio_empresario=pemp or None):
                    st.error("Ya existe otro producto con ese nombre.")
                else:
                    st.success("Producto actualizado.")
            if borrar_p:
                adb.eliminar_producto_amway(pid)
                st.rerun()


# ---------------------------------------------------------------- ASOCIADOS
def _df_fichas():
    filas = adb.listar_asociados()
    if not filas:
        return pd.DataFrame(columns=["id", "nombre", "telefono", "email", "direccion",
                                     "fecha_alta", "patrocinador", "notas", "creado"])
    df = pd.DataFrame(filas)
    df["fecha_alta"] = pd.to_datetime(df["fecha_alta"]).dt.date
    return df


def _registrar_asociado():
    st.markdown("Cargá los datos de la persona que se asoció. Al guardar, también queda anotada "
                "en la tabla de compras del mes de su alta.")
    opciones_p = [""] + adb.nombres_productos_amway()
    with st.form("form_alta_asociado", clear_on_submit=True):
        st.markdown("**Datos personales**")
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre y apellido *")
        telefono = c2.text_input("Teléfono / WhatsApp (con código de área)")
        c3, c4 = st.columns(2)
        email = c3.text_input("Email")
        fecha = c4.date_input("Fecha de alta *", value=date.today(), format="DD/MM/YYYY")
        direccion = st.text_input("Dirección")
        patrocinador = st.text_input("¿Quién lo invitó? (patrocinador)")
        notas = st.text_area("Notas (opcional)")
        st.markdown("**Primera compra (opcional)**")
        producto = st.selectbox("Producto", opciones_p)
        c5, c6 = st.columns(2)
        valor = c5.number_input("Valor de compra ($)", min_value=0.0, step=100.0)
        puntos = c6.number_input("Puntos", min_value=0.0, step=1.0)
        guardar = st.form_submit_button("Registrar asociado", type="primary")
    if guardar:
        if not nombre.strip():
            st.error("El nombre es obligatorio.")
        else:
            adb.alta_asociado(nombre, telefono, email, direccion, fecha, patrocinador, notas,
                              valor, puntos, producto=producto or None)
            st.success(f"Asociado registrado: {nombre.strip()}. Quedó anotado en "
                       f"{MESES[fecha.month - 1]} {fecha.year}.")


def _estadisticas_altas():
    df = _df_fichas()
    if df.empty:
        st.info("Todavía no hay asociados registrados.")
        return

    hoy = date.today()
    fechas = pd.to_datetime(df["fecha_alta"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Altas hoy", int((df["fecha_alta"] == hoy).sum()))
    c2.metric("Altas este mes", int(((fechas.dt.year == hoy.year) & (fechas.dt.month == hoy.month)).sum()))
    c3.metric("Altas este año", int((fechas.dt.year == hoy.year).sum()))
    c4.metric("Total de asociados", len(df))

    st.subheader("Altas por mes")
    anio = int(st.number_input("Año", min_value=2020, max_value=2100, value=hoy.year, step=1,
                               key="aso_anio_stats"))
    por_mes = fechas[fechas.dt.year == anio].dt.month.value_counts().reindex(range(1, 13), fill_value=0)
    tabla_mes = pd.DataFrame({"Mes": MESES, "Nuevos asociados": por_mes.values})
    st.bar_chart(tabla_mes.set_index("Mes"))
    st.dataframe(tabla_mes, hide_index=True, use_container_width=True)

    st.subheader("Altas por día")
    rango = st.date_input("Período", value=(hoy - timedelta(days=29), hoy), format="DD/MM/YYYY",
                          key="aso_periodo")
    if isinstance(rango, tuple) and len(rango) == 2:
        desde, hasta = rango
    else:
        desde = hasta = rango[0] if isinstance(rango, tuple) else rango
    dias = [d.date() for d in pd.date_range(desde, hasta)]
    conteo = df[(df["fecha_alta"] >= desde) & (df["fecha_alta"] <= hasta)]["fecha_alta"].value_counts()
    tabla_dia = pd.DataFrame({"Día": dias, "Nuevos asociados": [int(conteo.get(d, 0)) for d in dias]})
    st.caption(f"Total del período: {int(tabla_dia['Nuevos asociados'].sum())} asociado(s)")
    st.bar_chart(tabla_dia.set_index("Día"))
    st.dataframe(tabla_dia, hide_index=True, use_container_width=True)

    st.subheader("¿Quiénes se asociaron un día?")
    dia_sel = st.date_input("Día", value=hoy, format="DD/MM/YYYY", key="aso_dia")
    del_dia = df[df["fecha_alta"] == dia_sel]
    if del_dia.empty:
        st.info("Ese día no hubo altas.")
    else:
        st.dataframe(del_dia[["nombre", "telefono", "patrocinador"]].rename(columns={
            "nombre": "Nombre", "telefono": "Teléfono", "patrocinador": "Patrocinador"}),
            hide_index=True, use_container_width=True)

    st.subheader("Altas por año")
    por_anio = fechas.dt.year.value_counts().sort_index()
    st.dataframe(pd.DataFrame({"Año": por_anio.index, "Nuevos asociados": por_anio.values}),
                 hide_index=True, use_container_width=True)


def _lista_asociados():
    if st.button("🔄 Importar asociados que ya están en las tablas mensuales",
                 help="Crea la ficha de quienes figuran en 'Asociados' de algún mes y todavía no tienen ficha."):
        creados = adb.importar_asociados_existentes()
        st.success(f"Se crearon {creados} fichas nuevas.")

    texto = st.text_input("🔎 Buscar asociado", placeholder="Nombre o teléfono", key="aso_buscar_ficha")
    fichas = adb.buscar_asociados(texto)
    if not fichas:
        st.info("No hay asociados que coincidan.")
        return
    st.caption(f"{len(fichas)} asociado(s)")
    for a in fichas[:80]:
        titulo = f"{a['nombre']} · {a['telefono'] or 'sin teléfono'} · alta {a['fecha_alta']}"
        with st.expander(titulo):
            aid = a["id"]
            with st.form(f"form_ficha_{aid}"):
                c1, c2 = st.columns(2)
                n = c1.text_input("Nombre y apellido", value=a["nombre"], key=f"fn_{aid}")
                t = c2.text_input("Teléfono / WhatsApp", value=a["telefono"] or "", key=f"ft_{aid}")
                c3, c4 = st.columns(2)
                e = c3.text_input("Email", value=a["email"] or "", key=f"fe_{aid}")
                f_alta = c4.date_input("Fecha de alta", value=date.fromisoformat(a["fecha_alta"]),
                                       format="DD/MM/YYYY", key=f"fa_{aid}")
                d = st.text_input("Dirección", value=a["direccion"] or "", key=f"fd_{aid}")
                p = st.text_input("Patrocinador", value=a["patrocinador"] or "", key=f"fp_{aid}")
                no = st.text_area("Notas", value=a["notas"] or "", key=f"fno_{aid}")
                if st.form_submit_button("Guardar cambios", type="primary"):
                    if not n.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        adb.actualizar_asociado(aid, n, t, e, d, p, no, f_alta)
                        st.success("Ficha actualizada.")


def _asociados():
    tab_reg, tab_est, tab_lista = st.tabs(["➕ Registrar asociado", "📈 Estadísticas de altas",
                                           "🗂️ Lista y edición"])
    with tab_reg:
        _registrar_asociado()
    with tab_est:
        _estadisticas_altas()
    with tab_lista:
        _lista_asociados()


# ---------------------------------------------------------------- RESUMEN ANUAL
def _resumen():
    anio = int(st.number_input("Año", min_value=2020, max_value=2100, value=date.today().year,
                               step=1, key="amway_anio_resumen"))
    df = pd.DataFrame(adb.resumen_anio(anio))
    df["mes"] = df["mes"].map(lambda m: MESES[m - 1])
    df = df.rename(columns={
        "mes": "Mes", "ventas_clientes": "Ventas clientes", "puntos_clientes": "Puntos clientes",
        "ventas_asociados": "Ventas asociados", "puntos_asociados": "Puntos asociados"})
    st.dataframe(df, hide_index=True, use_container_width=True, column_config={
        "Ventas clientes": st.column_config.NumberColumn(format="$%.0f"),
        "Ventas asociados": st.column_config.NumberColumn(format="$%.0f"),
    })
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas clientes del año", f"$ {df['Ventas clientes'].sum():,.0f}")
    c2.metric("Puntos clientes del año", f"{df['Puntos clientes'].sum():,.0f}")
    c3.metric("Ventas asociados del año", f"$ {df['Ventas asociados'].sum():,.0f}")
    c4.metric("Puntos asociados del año", f"{df['Puntos asociados'].sum():,.0f}")
    st.subheader("Puntos por mes")
    st.bar_chart(df.set_index("Mes")[["Puntos clientes", "Puntos asociados"]])


# ---------------------------------------------------------------- PUNTO DE ENTRADA
def render():
    """Se llama desde app.py cuando está elegida la sección Amway."""
    adb.crear_tablas()
    st.title("🌿 Amway")
    seccion = st.radio("Amway", ["📅 Ventas del mes", "🔎 Buscar y editar personas", "🤝 Asociados",
                                 "🧴 Catálogo", "📊 Resumen anual"],
                       horizontal=True, label_visibility="collapsed", key="amway_seccion")
    st.markdown("---")
    if seccion == "📅 Ventas del mes":
        _ventas_del_mes()
    elif seccion == "🔎 Buscar y editar personas":
        _buscar_personas()
    elif seccion == "🤝 Asociados":
        _asociados()
    elif seccion == "🧴 Catálogo":
        _catalogo()
    else:
        _resumen()

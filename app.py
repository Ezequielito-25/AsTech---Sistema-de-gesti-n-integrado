"""AsTech - Sistema de gestión de la tienda y servicio técnico.
Ejecutar con:  streamlit run app.py
"""
from datetime import date, timedelta
import re

import pandas as pd
import streamlit as st

import db
from presupuesto import generar_presupuesto
from importar import render_importador
import mi_presupuesto
import amway
import auth
import estilo

st.set_page_config(page_title="AsTech - Gestión", page_icon="🖥️", layout="wide")
auth.exigir_login()  # nada de la app se muestra sin ingresar
estilo.aplicar()
db.crear_tablas()

st.sidebar.title("🖥️ AsTech")
seccion = st.sidebar.radio(
    "Menú",
    ["📦 Productos", "👤 Clientes y operaciones", "📊 Estadísticas", "🧾 Presupuestos",
     "💰 Mi presupuesto personal", "🌿 Amway"],
)
st.sidebar.caption(f"Hoy: {date.today():%d/%m/%Y}")
auth.boton_cerrar_sesion()


def limpiar_wp(numero):
    """Deja solo dígitos para poder armar el link de WhatsApp."""
    return re.sub(r"\D", "", numero or "")


# =====================================================================
# 1. PRODUCTOS
# =====================================================================
if seccion == "📦 Productos":
    st.title("📦 Cargar productos")
    render_importador()

    with st.form("form_producto", clear_on_submit=True):
        descripcion = st.text_input("Descripción del producto *")
        numero_serie = st.text_input("Número de serie (opcional)")
        c1, c2 = st.columns(2)
        precio_ars = c1.number_input("Precio en pesos (ARS)", min_value=0.0, step=100.0)
        precio_usd = c2.number_input("Precio en dólares (USD)", min_value=0.0, step=1.0)
        imagen = st.file_uploader("Imagen del producto", type=["png", "jpg", "jpeg", "webp"])
        if st.form_submit_button("Guardar producto", type="primary"):
            if not descripcion.strip():
                st.error("La descripción es obligatoria.")
            else:
                nombre_img = db.guardar_imagen(imagen)
                db.agregar_producto(descripcion.strip(), precio_ars, precio_usd, nombre_img,
                                    numero_serie=numero_serie.strip())
                st.success("Producto guardado.")

    st.subheader("Catálogo")
    busqueda_p = st.text_input("🔎 Buscar producto", placeholder="Nombre o número de serie",
                               key="buscar_producto")
    productos = db.buscar_productos(busqueda_p)
    if not productos:
        if busqueda_p.strip():
            st.info("No encontré productos con esa búsqueda.")
        else:
            st.info("Todavía no hay productos cargados.")
    for p in productos:
        col_img, col_txt = st.columns([1, 4])
        foto = db.leer_imagen(p["imagen"])
        if foto:
            col_img.image(foto, width=120)
        col_txt.markdown(
            f"**{p['descripcion']}**  \n"
            f"Serie: {p['numero_serie'] or 'sin número de serie'}  \n"
            f"ARS $ {p['precio_ars']:,.2f} · USD {p['precio_usd']:,.2f}  \n"
            f"Cargado el {date.fromisoformat(p['creado'][:10]):%d/%m/%Y}"
        )
        with col_txt.expander("Ver historial y editar"):
            ventas = db.ventas_de_producto(p["id"])
            if ventas:
                st.markdown("**Ventas de este producto**")
                st.dataframe(pd.DataFrame(ventas).rename(columns={
                    "fecha": "Fecha", "cliente": "Cliente", "telefono_wp": "WhatsApp",
                    "cantidad": "Cant.", "precio_ars": "Precio ARS", "precio_usd": "Precio USD"}),
                    hide_index=True, use_container_width=True)
            else:
                st.caption("Todavía no se vendió este producto.")

            with st.form(f"form_editar_producto_{p['id']}"):
                st.markdown("**Editar producto**")
                e_desc = st.text_input("Descripción *", value=p["descripcion"], key=f"pd_{p['id']}")
                e_serie = st.text_input("Número de serie", value=p["numero_serie"] or "",
                                        key=f"ps_{p['id']}")
                c1, c2 = st.columns(2)
                e_ars = c1.number_input("Precio ARS", min_value=0.0, step=100.0,
                                        value=float(p["precio_ars"]), key=f"par_{p['id']}")
                e_usd = c2.number_input("Precio USD", min_value=0.0, step=1.0,
                                        value=float(p["precio_usd"]), key=f"pusd_{p['id']}")
                e_img = st.file_uploader("Cambiar imagen (opcional)",
                                         type=["png", "jpg", "jpeg", "webp"], key=f"pi_{p['id']}")
                if st.form_submit_button("Guardar cambios del producto", type="primary"):
                    if not e_desc.strip():
                        st.error("La descripción es obligatoria.")
                    else:
                        nombre_img = db.guardar_imagen(e_img) if e_img else p["imagen"]
                        db.actualizar_producto(p["id"], e_desc.strip(), e_ars, e_usd,
                                               e_serie.strip(), nombre_img)
                        st.success("Producto actualizado.")

# =====================================================================
# 2. CLIENTES Y OPERACIONES
# =====================================================================
elif seccion == "👤 Clientes y operaciones":
    st.title("👤 Clientes y operaciones")
    tab_buscar, tab_nuevo, tab_op, tab_pago = st.tabs(
        ["Buscar y editar", "Cliente nuevo", "Registrar compra o reparación", "Registrar pago"]
    )

    # ---- Buscar y editar clientes y sus operaciones ----
    with tab_buscar:
        aviso = st.session_state.pop("aviso_eliminado", None)
        if aviso:
            st.success(aviso)
        busqueda = st.text_input("🔎 Buscar cliente",
                                 placeholder="Apellido, nombre o número de WhatsApp",
                                 key="buscar_cliente")
        resultados = db.buscar_clientes(busqueda)
        if not resultados:
            if busqueda.strip():
                st.info("No encontré clientes con esa búsqueda.")
            else:
                st.info("Todavía no hay clientes cargados.")
        else:
            opciones_b = {f"{c['nombre']} · {c['telefono_wp'] or 'sin WhatsApp'}": c for c in resultados}
            elegido = st.selectbox(f"Clientes encontrados ({len(resultados)})",
                                   list(opciones_b.keys()), key="cliente_a_editar")
            cli = opciones_b[elegido]

            with st.form(f"form_editar_cliente_{cli['id']}"):
                st.markdown("**Datos del cliente**")
                e_nombre = st.text_input("Nombre y apellido *", value=cli["nombre"])
                c1, c2 = st.columns(2)
                e_wp = c1.text_input("WhatsApp (con código de área)", value=cli["telefono_wp"] or "")
                e_email = c2.text_input("Email", value=cli["email"] or "")
                e_dir = st.text_input("Dirección", value=cli["direccion"] or "")
                if st.form_submit_button("Guardar datos del cliente", type="primary"):
                    if not e_nombre.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        db.actualizar_cliente(cli["id"], e_nombre.strip(), limpiar_wp(e_wp),
                                              e_email.strip(), e_dir.strip())
                        st.success("Datos del cliente guardados.")

            st.markdown("**Operaciones de este cliente**")
            ops = db.operaciones_de_cliente(cli["id"])
            if not ops:
                st.info("Este cliente todavía no tiene operaciones.")
            for op in ops:
                etiqueta = "Venta" if op["tipo"] == "venta" else "Reparación"
                with st.expander(f"#{op['id']} · {etiqueta} · {op['fecha']} · ARS $ {op['monto_ars']:,.0f}"):
                    with st.form(f"form_op_{op['id']}"):
                        f_fecha = st.date_input("Fecha de la visita o compra",
                                                value=date.fromisoformat(op["fecha"]),
                                                format="DD/MM/YYYY", key=f"fop_{op['id']}")
                        f_desc = st.text_area("Descripción", value=op["descripcion"] or "",
                                              key=f"fdesc_{op['id']}")
                        if st.form_submit_button("Guardar fecha y descripción"):
                            db.actualizar_operacion(op["id"], f_fecha, f_desc.strip())
                            st.success("Operación actualizada.")

            st.markdown("---")
            st.markdown("**Eliminar cliente**")
            n_ops = db.contar_operaciones_cliente(cli["id"])
            if n_ops:
                st.warning(f"Este cliente tiene {n_ops} operación(es) cargada(s). Si lo eliminás, "
                           "también se borran esas operaciones con sus montos y pagos.")
            confirmar = st.checkbox("Entiendo que esta acción no se puede deshacer",
                                    key=f"conf_del_{cli['id']}")
            if st.button("🗑️ Eliminar cliente", disabled=not confirmar, key=f"del_{cli['id']}"):
                db.eliminar_cliente(cli["id"])
                st.session_state["aviso_eliminado"] = f"Cliente eliminado: {cli['nombre']}."
                st.rerun()
            st.caption("Antes de borrar se guarda una copia de los datos del cliente en la base (tabla clientes_eliminados).")


    # ---- Cliente nuevo ----
    with tab_nuevo:
        with st.form("form_cliente", clear_on_submit=True):
            nombre = st.text_input("Nombre y apellido *")
            c1, c2 = st.columns(2)
            wp = c1.text_input("WhatsApp (con código de área, ej: 5492915123456)")
            email = c2.text_input("Email")
            direccion = st.text_input("Dirección")
            if st.form_submit_button("Guardar cliente", type="primary"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    db.agregar_cliente(nombre.strip(), limpiar_wp(wp), email, direccion)
                    st.success("Cliente guardado.")

    # ---- Registrar operación ----
    with tab_op:
        clientes = db.listar_clientes()
        if not clientes:
            st.info("Primero cargá un cliente.")
        else:
            opciones = {f"{c['nombre']} ({c['telefono_wp'] or 'sin WhatsApp'})": c["id"] for c in clientes}
            tipo_txt = st.radio("¿Qué trae el cliente?",
                                ["Compra de producto", "Reparación / servicio técnico"],
                                horizontal=True)
            tipo = "venta" if tipo_txt.startswith("Compra") else "reparacion"
            cliente_sel = st.selectbox("Cliente", list(opciones.keys()))
            fecha = st.date_input("Fecha de visita o compra", value=date.today())

            if tipo == "venta":
                productos = db.listar_productos()
                nombres = {f"{p['descripcion']}": p for p in productos}
                elegidos = st.multiselect("Productos vendidos", list(nombres.keys()))
                items = []
                for nom in elegidos:
                    p = nombres[nom]
                    cant = st.number_input(f"Cantidad de {nom}", min_value=1, value=1, step=1,
                                           key=f"cant_{p['id']}")
                    items.append({"producto_id": p["id"], "descripcion": nom, "cantidad": int(cant),
                                  "precio_ars": p["precio_ars"], "precio_usd": p["precio_usd"]})
                total_ars = sum(i["precio_ars"] * i["cantidad"] for i in items)
                total_usd = sum(i["precio_usd"] * i["cantidad"] for i in items)
                descripcion = ""
                st.write(f"**Total:** ARS $ {total_ars:,.2f} · USD {total_usd:,.2f}")
            else:
                items = []
                descripcion = st.text_area("Descripción del problema / trabajo a realizar")
                c1, c2 = st.columns(2)
                total_ars = c1.number_input("Precio del servicio (ARS)", min_value=0.0, step=100.0)
                total_usd = c2.number_input("Precio del servicio (USD)", min_value=0.0, step=1.0)

            st.markdown("**Pago recibido en el momento**")
            c1, c2 = st.columns(2)
            pago_ars = c1.number_input("Pagado en ARS", min_value=0.0, step=100.0, key="pa_op")
            pago_usd = c2.number_input("Pagado en USD", min_value=0.0, step=1.0, key="pu_op")

            if st.button("Guardar operación", type="primary"):
                cliente_id = opciones[cliente_sel]
                db.registrar_operacion(
                    tipo, cliente_id, fecha, descripcion or None,
                    total_ars, total_usd, min(pago_ars, total_ars), min(pago_usd, total_usd),
                    items=items,
                )
                saldo_ars = total_ars - min(pago_ars, total_ars)
                saldo_usd = total_usd - min(pago_usd, total_usd)
                st.success(f"{'Venta' if tipo == 'venta' else 'Reparación'} registrada.")
                if saldo_ars > 0 or saldo_usd > 0:
                    st.warning(f"Queda debiendo: ARS $ {saldo_ars:,.2f} · USD {saldo_usd:,.2f}")

    # ---- Pagos de deudas ----
    with tab_pago:
        df = db.listar_operaciones()
        pendientes = df[(df["deuda_ars"] > 0.005) | (df["deuda_usd"] > 0.005)] if not df.empty else df
        if pendientes.empty:
            st.info("No hay operaciones con deuda.")
        else:
            etiquetas = {
                f"#{r.id} · {r.fecha} · {r.cliente} · debe ARS {r.deuda_ars:,.2f} / USD {r.deuda_usd:,.2f}": r.id
                for r in pendientes.itertuples()
            }
            op_sel = st.selectbox("Operación", list(etiquetas.keys()))
            c1, c2 = st.columns(2)
            p_ars = c1.number_input("Pago en ARS", min_value=0.0, step=100.0, key="pa_pago")
            p_usd = c2.number_input("Pago en USD", min_value=0.0, step=1.0, key="pu_pago")
            if st.button("Registrar pago"):
                db.registrar_pago(etiquetas[op_sel], p_ars, p_usd)
                st.success("Pago registrado.")

# =====================================================================
# 3. ESTADÍSTICAS
# =====================================================================
elif seccion == "📊 Estadísticas":
    st.title("📊 Estadísticas")
    vista = st.radio("Período", ["Diario", "Mensual"], horizontal=True)

    if vista == "Diario":
        dia = st.date_input("Día", value=date.today())
        desde, hasta = dia, dia
    else:
        hoy = date.today()
        c1, c2 = st.columns(2)
        anio = c1.number_input("Año", min_value=2020, max_value=2100, value=hoy.year, step=1)
        mes = c2.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1,
                           format_func=lambda m: f"{m:02d}")
        desde = date(int(anio), int(mes), 1)
        hasta = (date(int(anio) + (mes == 12), (mes % 12) + 1, 1) - timedelta(days=1))

    ops = db.listar_operaciones(desde, hasta)
    ventas = ops[ops["tipo"] == "venta"] if not ops.empty else ops
    reparaciones = ops[ops["tipo"] == "reparacion"] if not ops.empty else ops
    deudores = db.clientes_deudores()
    if not ops.empty:
        ops_deuda = ops[(ops["deuda_ars"] > 0.005) | (ops["deuda_usd"] > 0.005)]
        clientes_con_deuda = ops_deuda["cliente"].nunique()
    else:
        clientes_con_deuda = 0

    st.subheader("Resumen del período")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ventas", len(ventas))
    m2.metric("Reparaciones", len(reparaciones))
    m3.metric("Clientes distintos", ops["cliente"].nunique() if not ops.empty else 0)
    m4.metric("Clientes deudores (período)", clientes_con_deuda)

    m5, m6 = st.columns(2)
    m5.metric("Facturado ARS", f"$ {ops['monto_ars'].sum():,.2f}" if not ops.empty else "$ 0")
    m6.metric("Facturado USD", f"US$ {ops['monto_usd'].sum():,.2f}" if not ops.empty else "US$ 0")

    st.subheader("Clientes deudores (total, todas las fechas)")
    if deudores.empty:
        st.success("No hay clientes con deuda pendiente. 🎉")
    else:
        st.dataframe(deudores.rename(columns={
            "cliente": "Cliente", "telefono_wp": "WhatsApp",
            "operaciones_pendientes": "Operaciones pendientes",
            "deuda_ars": "Debe ARS", "deuda_usd": "Debe USD"}),
            use_container_width=True, hide_index=True)

    st.subheader("Detalle de operaciones del período")
    if ops.empty:
        st.info("No hubo operaciones en este período.")
    else:
        st.dataframe(ops.rename(columns={
            "id": "N°", "tipo": "Tipo", "fecha": "Fecha", "cliente": "Cliente",
            "descripcion": "Descripción", "monto_ars": "Monto ARS", "monto_usd": "Monto USD",
            "pagado_ars": "Pagado ARS", "pagado_usd": "Pagado USD",
            "deuda_ars": "Debe ARS", "deuda_usd": "Debe USD", "telefono_wp": "WhatsApp"}),
            use_container_width=True, hide_index=True)

# =====================================================================
# 4. PRESUPUESTOS
# =====================================================================
elif seccion == "🧾 Presupuestos":
    st.title("🧾 Presupuesto en PDF")
    st.caption("Armá el presupuesto, descargalo y mandalo por WhatsApp.")

    clientes = db.listar_clientes()
    opciones = {f"{c['nombre']} ({c['telefono_wp'] or 'sin WhatsApp'})": c for c in clientes}
    if opciones:
        cliente_sel = st.selectbox("Cliente", ["(sin cliente cargado)"] + list(opciones.keys()))
        cliente = opciones.get(cliente_sel, {"nombre": "Consumidor final", "telefono_wp": ""})
    else:
        st.info("No hay clientes cargados. Podés hacer el presupuesto a nombre de un nombre libre:")
        cliente = {"nombre": st.text_input("Nombre del cliente"), "telefono_wp": st.text_input("WhatsApp")}

    st.subheader("Productos")
    productos = db.listar_productos()
    nombres = {p["descripcion"]: p for p in productos}
    elegidos = st.multiselect("Productos", list(nombres.keys()))
    items = []
    for nom in elegidos:
        p = nombres[nom]
        c1, c2, c3 = st.columns([4, 1, 2])
        c1.write(nom)
        cant = c2.number_input("Cant.", min_value=1, value=1, step=1, key=f"pres_cant_{p['id']}")
        precio_ars = c3.number_input("Precio ARS", min_value=0.0, value=float(p["precio_ars"]),
                                     step=100.0, key=f"pres_pa_{p['id']}")
        items.append({"descripcion": nom, "cantidad": int(cant), "precio_ars": precio_ars,
                      "precio_usd": p["precio_usd"], "imagen": p["imagen"]})

    st.subheader("Servicio técnico")
    servicios = []
    cant_serv = st.number_input("Cantidad de servicios a presupuestar", min_value=0, max_value=10, value=0)
    for i in range(int(cant_serv)):
        c1, c2, c3 = st.columns([4, 2, 2])
        desc = c1.text_input("Descripción del servicio", key=f"sv_d_{i}")
        sa = c2.number_input("ARS", min_value=0.0, step=100.0, key=f"sv_a_{i}")
        su = c3.number_input("USD", min_value=0.0, step=1.0, key=f"sv_u_{i}")
        if desc.strip():
            servicios.append({"descripcion": desc.strip(), "precio_ars": sa, "precio_usd": su})

    notas = st.text_area("Observaciones (opcional)", placeholder="Ej: incluye mano de obra, garantía 30 días…")

    if items or servicios:
        pdf = generar_presupuesto(cliente, items, servicios, notas)
        nombre_archivo = f"presupuesto_{cliente['nombre'].replace(' ', '_')}.pdf"
        st.download_button("⬇️ Descargar presupuesto PDF", data=pdf,
                           file_name=nombre_archivo, mime="application/pdf", type="primary")

        wp = limpiar_wp(cliente.get("telefono_wp", ""))
        mensaje = (f"Hola {cliente['nombre']}! Te paso el presupuesto de AsTech. "
                   f"Cualquier consulta, avisame.")
        if wp:
            from urllib.parse import quote
            st.markdown(f"[📲 Abrir WhatsApp de {cliente['nombre']}]"
                        f"(https://wa.me/{wp}?text={quote(mensaje)})  \n"
                        "_Después de abrirlo, adjuntá el PDF descargado._")
    else:
        st.info("Agregá al menos un producto o un servicio para generar el presupuesto.")

# =====================================================================
# 5. MI PRESUPUESTO (finanzas personales, misma base de datos)
# =====================================================================
elif seccion == "💰 Mi presupuesto personal":
    st.title("💰 Mi presupuesto personal")
    mi_presupuesto.render()

# =====================================================================
# 6. AMWAY (emprendimiento: clientes y asociados, separado del resto)
# =====================================================================
elif seccion == "🌿 Amway":
    amway.render()

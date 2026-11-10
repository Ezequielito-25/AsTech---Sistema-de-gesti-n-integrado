"""Pantalla 'Mi presupuesto' dentro de AsTech: ingresos, ahorro primero, gastos y barras de progreso."""
from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import presupuesto_db as pdb

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
NOMBRE_CAT = {"Necesidad": "Necesidades", "Deseo": "Deseos", "Ahorro": "Ahorro extra"}
AZUL = colors.HexColor("#1F3A5F")


def _money(valor):
    return f"$ {valor:,.0f}"


def _col_dia(label):
    return st.column_config.NumberColumn(label, min_value=1, max_value=31, step=1)


def _col_monto(label="Monto ($)"):
    return st.column_config.NumberColumn(label, min_value=0, step=100, format="$%.0f")


def _barra(gastado, presupuesto, etiqueta, es_meta=False):
    ratio = gastado / presupuesto if presupuesto > 0 else 0.0
    st.progress(min(ratio, 1.0), text=f"{etiqueta}: {_money(gastado)} de {_money(presupuesto)} ({ratio:.0%})")
    if es_meta:
        if ratio >= 1:
            st.success("¡Meta cumplida!")
        else:
            st.info(f"Te faltan {_money(presupuesto - gastado)} para la meta")
    elif presupuesto > 0 and gastado > presupuesto:
        st.error(f"Te pasaste por {_money(gastado - presupuesto)}")
    elif ratio >= 0.8:
        st.warning("Cuidado: ya usaste más del 80%")
    else:
        st.success("Vas bien")


def _tabla_pdf(filas, anchos):
    t = Table(filas, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _pdf_resumen(anio, mes, r, gastos_df):
    """Resumen del mes en PDF, con el mismo estilo que los presupuestos de la tienda."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title=f"Presupuesto {MESES[mes - 1]} {anio}")
    est = getSampleStyleSheet()
    normal = est["Normal"]
    historia = [
        Paragraph("<b>AsTech</b> — Presupuesto mensual", normal),
        Spacer(1, 6),
        Paragraph(f"{MESES[mes - 1]} {anio}", est["Title"]),
    ]
    objetivo = r["cfg"].get("objetivo")
    if objetivo:
        historia.append(Paragraph(f"<b>Objetivo:</b> {escape(objetivo)}", normal))
    historia.append(Spacer(1, 10))

    historia.append(_tabla_pdf([
        ["Concepto", "Monto"],
        ["Ingresos", _money(r["ingresos"])],
        ["Ahorro (primero)", _money(r["ahorro"])],
        ["Gastos fijos", _money(r["fijos"])],
        ["Suscripciones", _money(r["subs"])],
        ["Libre para gastar", _money(r["libre"])],
    ], [12 * cm, 5 * cm]))
    historia.append(Spacer(1, 10))

    historia.append(_tabla_pdf(
        [["Categoría", "Presupuesto", "Gastado"]]
        + [[NOMBRE_CAT[c], _money(r["presupuesto"][c]), _money(r["gastado"][c])] for c in pdb.CATEGORIAS],
        [8 * cm, 4.5 * cm, 4.5 * cm]))

    if not gastos_df.empty:
        historia.append(Spacer(1, 10))
        historia.append(Paragraph("<b>Gastos del mes</b>", normal))
        historia.append(Spacer(1, 4))
        filas = [["Fecha", "Concepto", "Categoría", "Monto"]]
        for fila in gastos_df.itertuples(index=False):
            filas.append([fila.fecha.strftime("%d/%m/%Y"), escape(str(fila.concepto)),
                          fila.categoria, _money(fila.monto)])
        historia.append(_tabla_pdf(filas, [2.8 * cm, 7.5 * cm, 3.2 * cm, 3.5 * cm]))

    doc.build(historia)
    return buffer.getvalue()


# ---------------------------------------------------------------- PANTALLA MES
def _pantalla_mes(anio, mes):
    cfg = pdb.obtener_config(anio, mes)

    with st.form(f"form_mes_{anio}_{mes}"):
        objetivo = st.text_input("🎯 Mi objetivo del mes", value=cfg["objetivo"] or "")
        c1, c2, c3, c4 = st.columns(4)
        ahorro_pct = c1.number_input("% a ahorrar primero", min_value=0, max_value=100,
                                     value=int(round(cfg["ahorro_pct"] * 100)), step=1)
        pct_nec = c2.number_input("% necesidades (de lo libre)", min_value=0, max_value=100,
                                  value=int(round(cfg["pct_necesidades"] * 100)), step=1)
        pct_des = c3.number_input("% deseos (de lo libre)", min_value=0, max_value=100,
                                  value=int(round(cfg["pct_deseos"] * 100)), step=1)
        pct_aho = c4.number_input("% ahorro extra (de lo libre)", min_value=0, max_value=100,
                                  value=int(round(cfg["pct_ahorro_extra"] * 100)), step=1)

        st.subheader("Ingresos")
        ing = st.data_editor(
            pdb.listar_df("ingresos", anio, mes), num_rows="dynamic", hide_index=True,
            key=f"ed_ing_{anio}_{mes}",
            column_config={"concepto": "Concepto", "dia": _col_dia("Día"), "monto": _col_monto()},
        )
        st.subheader("Gastos fijos")
        fij = st.data_editor(
            pdb.listar_df("fijos", anio, mes), num_rows="dynamic", hide_index=True,
            key=f"ed_fij_{anio}_{mes}",
            column_config={"concepto": "Concepto", "vence_dia": _col_dia("Vence el día"), "monto": _col_monto()},
        )
        st.subheader("Suscripciones (aparte)")
        sub = st.data_editor(
            pdb.listar_df("suscripciones", anio, mes), num_rows="dynamic", hide_index=True,
            key=f"ed_sub_{anio}_{mes}",
            column_config={"servicio": "Servicio", "cobra_dia": _col_dia("Cobra el día"), "monto": _col_monto()},
        )
        guardar = st.form_submit_button("💾 Guardar mes", type="primary")

    if guardar:
        if pct_nec + pct_des + pct_aho != 100:
            st.warning("Los porcentajes de reparto tienen que sumar 100%. Revisalos.")
        pdb.guardar_config(anio, mes, objetivo.strip() or None, ahorro_pct / 100,
                           pct_nec / 100, pct_des / 100, pct_aho / 100)
        pdb.reemplazar_tabla("ingresos", anio, mes, ing)
        pdb.reemplazar_tabla("fijos", anio, mes, fij)
        pdb.reemplazar_tabla("suscripciones", anio, mes, sub)
        st.success("Mes guardado.")

    if st.button("📋 Copiar fijos y suscripciones del mes anterior", key=f"copiar_{anio}_{mes}"):
        pdb.copiar_recurrentes(anio, mes)
        st.rerun()

    r = pdb.resumen_mes(anio, mes)
    st.subheader("¿Cuánto me queda?")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos", _money(r["ingresos"]))
    c2.metric("Comprometido", _money(r["comprometido"]), help="Ahorro + fijos + suscripciones")
    c3.metric("Libre para gastar", _money(r["libre"]))
    if r["libre"] < 0:
        st.error("Te estás pasando: revisá fijos o ahorro.")
    else:
        st.success("Vas dentro del presupuesto.")

    st.subheader("Mi mes de un vistazo")
    for etiqueta, valor in [("Ahorro", r["ahorro"]), ("Fijos", r["fijos"]),
                            ("Suscripciones", r["subs"]), ("Libre", max(r["libre"], 0))]:
        ratio = valor / r["ingresos"] if r["ingresos"] else 0.0
        st.progress(min(max(ratio, 0.0), 1.0), text=f"{etiqueta}: {ratio:.0%} de tus ingresos")

    st.subheader("Reparto de lo libre")
    st.table(pd.DataFrame([
        {"Categoría": NOMBRE_CAT[c], "% del libre": f"{pct:.0%}", "Presupuesto": _money(r["presupuesto"][c])}
        for c, pct in [("Necesidad", r["cfg"]["pct_necesidades"]),
                       ("Deseo", r["cfg"]["pct_deseos"]),
                       ("Ahorro", r["cfg"]["pct_ahorro_extra"])]
    ]))

    st.download_button(
        "📄 Descargar resumen del mes (PDF)",
        data=_pdf_resumen(anio, mes, r, pdb.listar_gastos_df(anio, mes)),
        file_name=f"presupuesto_{MESES[mes - 1]}_{anio}.pdf",
        mime="application/pdf",
        key=f"pdf_{anio}_{mes}",
    )


# ---------------------------------------------------------------- PANTALLA DÍA A DÍA
def _pantalla_dia(anio, mes):
    desde, hasta = pdb.rango_mes(anio, mes)

    with st.form(f"form_gastos_{anio}_{mes}"):
        gastos = st.data_editor(
            pdb.listar_gastos_df(anio, mes), num_rows="dynamic", hide_index=True,
            key=f"ed_gastos_{anio}_{mes}",
            column_config={
                "fecha": st.column_config.DateColumn("Fecha", min_value=desde, max_value=hasta,
                                                     format="DD/MM/YYYY"),
                "concepto": "Concepto",
                "categoria": st.column_config.SelectboxColumn("Categoría", options=pdb.CATEGORIAS,
                                                              required=True),
                "monto": _col_monto(),
            },
        )
        guardar = st.form_submit_button("💾 Guardar gastos", type="primary")

    if guardar:
        omitidos = pdb.reemplazar_gastos(anio, mes, gastos)
        if omitidos:
            st.warning(f"{omitidos} gasto(s) tenían una fecha fuera de {MESES[mes - 1]} y no se guardaron.")
        else:
            st.success("Gastos guardados.")

    r = pdb.resumen_mes(anio, mes)
    st.subheader("¿Cómo venís?")
    c1, c2, c3 = st.columns(3)
    for col, cat in zip((c1, c2, c3), pdb.CATEGORIAS):
        with col:
            _barra(r["gastado"][cat], r["presupuesto"][cat], NOMBRE_CAT[cat], es_meta=(cat == "Ahorro"))

    libre_restante = r["libre"] - r["total_gastado"]
    st.metric("Libre restante", _money(libre_restante))
    if libre_restante < 0:
        st.error("Te pasaste del libre del mes.")


# ---------------------------------------------------------------- PANTALLA AÑO
def _pantalla_anio(anio):
    meta = st.number_input("Meta de ahorro anual ($)", min_value=0, value=3000000, step=100000,
                           key=f"meta_{anio}")
    filas = []
    for m in range(1, 13):
        r = pdb.resumen_mes(anio, m)
        hay_datos = r["ingresos"] > 0
        quedo_ratio = max(0.0, min(r["quedo"] / r["ingresos"], 1.0)) if hay_datos else None
        filas.append({
            "Mes": MESES[m - 1],
            "Ingresos": r["ingresos"],
            "Ahorro": r["ahorro"],
            "Fijos": r["fijos"],
            "Suscripciones": r["subs"],
            "Día a día": r["total_gastado"],
            "Me quedó": r["quedo"] if hay_datos else None,
            "% que me quedó": quedo_ratio,
        })
    df = pd.DataFrame(filas)

    st.subheader("Meta de ahorro")
    _barra(df["Ahorro"].sum(), meta, "Ahorro del año", es_meta=True)

    st.subheader("Mes a mes")
    st.dataframe(
        df, hide_index=True,
        column_config={
            "Ingresos": _col_monto("Ingresos"), "Ahorro": _col_monto("Ahorro"),
            "Fijos": _col_monto("Fijos"), "Suscripciones": _col_monto("Suscripciones"),
            "Día a día": _col_monto("Día a día"), "Me quedó": _col_monto("Me quedó"),
            "% que me quedó": st.column_config.ProgressColumn(
                "% que me quedó", min_value=0, max_value=1, format="percent"),
        },
    )
    st.subheader("Lo que me quedó por mes")
    st.bar_chart(df.set_index("Mes")[["Me quedó"]].fillna(0))


# ---------------------------------------------------------------- PUNTO DE ENTRADA
def render():
    """Se llama desde app.py cuando está elegida la sección 'Mi presupuesto'."""
    pdb.crear_tablas()
    hoy = date.today()
    c1, c2 = st.columns([1, 2])
    anio = int(c1.number_input("Año", min_value=2020, max_value=2100, value=hoy.year, step=1,
                               key="pm_anio"))
    mes = c2.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1,
                       format_func=lambda m: MESES[m - 1], key="pm_mes")

    tab_mes, tab_dia, tab_anio = st.tabs(["🗓️ Mes", "💸 Día a día", "📈 Año"])
    with tab_mes:
        _pantalla_mes(anio, mes)
    with tab_dia:
        _pantalla_dia(anio, mes)
    with tab_anio:
        _pantalla_anio(anio)

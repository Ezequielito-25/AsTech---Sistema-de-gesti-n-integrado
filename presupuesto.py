"""Genera presupuestos en PDF (productos y/o servicio técnico) con ReportLab."""
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from db import leer_imagen

NOMBRE_EMPRESA = "AsTech"
SUBTITULO = "Tienda Informática y Servicio Técnico"
VALIDEZ_DIAS = 7


def _fmt(valor, moneda):
    if moneda == "ARS":
        return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_presupuesto(cliente, items, servicios, notas="", moneda_principal="ARS"):
    """
    cliente: dict con nombre, telefono_wp, etc.
    items: lista de dicts {descripcion, cantidad, precio_ars, precio_usd, imagen}
    servicios: lista de dicts {descripcion, precio_ars, precio_usd}  (servicio técnico)
    Devuelve los bytes del PDF listos para descargar o enviar.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title=f"Presupuesto AsTech - {cliente['nombre']}")
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("t", parent=estilos["Title"], textColor=colors.HexColor("#1F3A5F"))
    normal = ParagraphStyle("n", parent=estilos["Normal"], fontSize=10, leading=13)
    pequeno = ParagraphStyle("p", parent=normal, fontSize=8.5, textColor=colors.grey)
    azul = colors.HexColor("#1F3A5F")

    historia = [
        Paragraph(f"<b>{NOMBRE_EMPRESA}</b> — {SUBTITULO}", normal),
        Spacer(1, 6),
        Paragraph("PRESUPUESTO", titulo),
        Paragraph(f"<b>Fecha:</b> {date.today():%d/%m/%Y} &nbsp;&nbsp; "
                  f"<b>Válido por:</b> {VALIDEZ_DIAS} días", normal),
        Spacer(1, 4),
        Paragraph(f"<b>Cliente:</b> {cliente['nombre']}", normal),
    ]
    if cliente.get("telefono_wp"):
        historia.append(Paragraph(f"<b>WhatsApp:</b> {cliente['telefono_wp']}", normal))
    historia.append(Spacer(1, 12))

    total_ars = total_usd = 0.0

    # ---------- Productos ----------
    if items:
        historia.append(Paragraph("<b>Productos</b>", normal))
        historia.append(Spacer(1, 4))
        filas = [["Imagen", "Descripción", "Cant.", "Precio unit.", "Subtotal"]]
        for it in items:
            sub_ars = it["precio_ars"] * it["cantidad"]
            sub_usd = it["precio_usd"] * it["cantidad"]
            total_ars += sub_ars
            total_usd += sub_usd
            img_cell = ""
            datos_img = leer_imagen(it.get("imagen"))
            if datos_img:
                img_cell = Image(BytesIO(datos_img), width=1.6 * cm, height=1.6 * cm, kind="proportional")
            precio_unit = (f"{_fmt(it['precio_ars'], 'ARS')}<br/>{_fmt(it['precio_usd'], 'USD')}")
            subtotal = (f"{_fmt(sub_ars, 'ARS')}<br/>{_fmt(sub_usd, 'USD')}")
            filas.append([img_cell, Paragraph(it["descripcion"], normal), str(it["cantidad"]),
                          Paragraph(precio_unit, normal), Paragraph(subtotal, normal)])
        historia.append(_tabla(filas, [2.2 * cm, 7.0 * cm, 1.5 * cm, 3.3 * cm, 3.4 * cm], azul))
        historia.append(Spacer(1, 12))

    # ---------- Servicio técnico ----------
    if servicios:
        historia.append(Paragraph("<b>Servicio técnico</b>", normal))
        historia.append(Spacer(1, 4))
        filas = [["Descripción", "Precio"]]
        for sv in servicios:
            total_ars += sv["precio_ars"]
            total_usd += sv["precio_usd"]
            precio = f"{_fmt(sv['precio_ars'], 'ARS')}<br/>{_fmt(sv['precio_usd'], 'USD')}"
            filas.append([Paragraph(sv["descripcion"], normal), Paragraph(precio, normal)])
        historia.append(_tabla(filas, [12.0 * cm, 5.0 * cm], azul))
        historia.append(Spacer(1, 12))

    # ---------- Totales ----------
    historia.append(_tabla(
        [["TOTAL ARS", _fmt(total_ars, "ARS")], ["TOTAL USD", _fmt(total_usd, "USD")]],
        [12.0 * cm, 5.0 * cm], azul, encabezado=False, negrita_ultima=False))
    historia.append(Spacer(1, 14))

    if notas:
        historia.append(Paragraph(f"<b>Observaciones:</b> {notas}", normal))
        historia.append(Spacer(1, 8))
    historia.append(Paragraph(
        "Precios expresados en pesos y dólares. Los valores pueden variar según cotización "
        "vigente al momento de la compra. Presupuesto sin compromiso de compra.", pequeno))

    doc.build(historia)
    return buffer.getvalue()


def _tabla(filas, anchos, color, encabezado=True, negrita_ultima=False):
    t = Table(filas, colWidths=anchos, repeatRows=1 if encabezado else 0)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT") if len(anchos) == 5 else ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if encabezado:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    else:
        estilo += [("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                   ("ALIGN", (1, 0), (1, -1), "RIGHT")]
    t.setStyle(TableStyle(estilo))
    return t

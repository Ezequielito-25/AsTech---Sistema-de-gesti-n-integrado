"""Estilo visual de AsTech: verde pastel suave, barra lateral verde oscura y tarjetas claras.
Todos los textos que van sobre fondo claro llevan color oscuro explícito, así nunca quedan blancos sobre blanco."""
import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --acento: #8FD3AE;
    --acento-2: #B5E5CB;
    --acento-texto: #2F7D5B;
    --tinta: #1F3B2D;
    --tinta-suave: #5E7A6C;
    --fondo: #F3F8F5;
    --tarjeta: #FFFFFF;
    --borde: #DDEBE3;
}

html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

[data-testid="stApp"] {
    background:
        radial-gradient(1100px 520px at 100% -10%, #E2F4EA 0%, transparent 60%),
        radial-gradient(900px 480px at -10% 110%, #F1F8E9 0%, transparent 55%),
        var(--fondo);
    color: var(--tinta);
}

.block-container {
    padding-top: 2.2rem;
    max-width: 1200px;
}

/* ---------- Textos sobre fondo claro: siempre oscuros ---------- */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label p,
[data-testid="stExpander"] summary p,
[data-testid="stAlert"] p,
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"],
[data-testid="stTab"] {
    color: var(--tinta) !important;
}
[data-testid="stCaptionContainer"] p {
    color: var(--tinta-suave) !important;
}

/* Menús desplegables y listas de opciones */
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] ul,
[role="listbox"] {
    background: var(--tarjeta) !important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"],
[role="listbox"] li {
    background: var(--tarjeta) !important;
    color: var(--tinta) !important;
}
[data-baseweb="popover"] li:hover,
[role="listbox"] li:hover {
    background: #EEF8F2 !important;
}

/* Área para subir archivos */
[data-testid="stFileUploader"] section {
    background: #F7FBF9 !important;
    border: 1.5px dashed var(--borde) !important;
    border-radius: 14px !important;
}
[data-testid="stFileUploader"] section *,
[data-testid="stFileUploader"] small {
    color: var(--tinta) !important;
}

/* ---------- Barra lateral verde oscura ---------- */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    background: linear-gradient(180deg, #1C3A2E 0%, #2B5443 100%) !important;
    border-right: none;
}
/* Textos de la barra lateral: estos selectores tienen más peso que las reglas generales,
   si no el texto oscuro de las pestañas y los radios se pinta encima del verde */
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label div,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #E8F5EE !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #E8F5EE !important;
}
[data-testid="stSidebar"] h1 {
    font-weight: 800;
    letter-spacing: -0.02em;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 8px 12px;
    border-radius: 10px;
    transition: background 0.2s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] button {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 10px !important;
    color: #E8F5EE !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.12);
}

/* ---------- Títulos ---------- */
h1 {
    font-weight: 800 !important;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #2F7D5B, #5DB386);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
}
h2, h3 {
    color: #2A5D47 !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}

/* ---------- Tarjetas de métricas ---------- */
[data-testid="stMetric"] {
    background: var(--tarjeta);
    border: 1px solid var(--borde);
    border-left: 4px solid var(--acento);
    border-radius: 16px;
    padding: 14px 18px;
    box-shadow: 0 4px 14px rgba(31, 59, 45, 0.06);
}
[data-testid="stMetricValue"] {
    font-weight: 800;
}

/* ---------- Botones ---------- */
button[kind^="primary"] {
    background: linear-gradient(135deg, var(--acento), var(--acento-2)) !important;
    border: none !important;
    border-radius: 12px !important;
    color: var(--tinta) !important;
    font-weight: 700;
    box-shadow: 0 6px 16px rgba(143, 211, 174, 0.45);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
button[kind^="primary"] p {
    color: var(--tinta) !important;
}
button[kind^="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(143, 211, 174, 0.6);
}
button[kind="secondary"], button[kind="secondaryFormSubmit"] {
    background: var(--tarjeta) !important;
    border: 1px solid var(--borde) !important;
    border-radius: 12px !important;
    color: var(--tinta) !important;
    font-weight: 600;
}
button[kind="secondary"] p, button[kind="secondaryFormSubmit"] p {
    color: var(--tinta) !important;
}

/* ---------- Campos de texto y listas ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
    border-radius: 12px !important;
    border-color: var(--borde) !important;
    background: var(--tarjeta) !important;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    color: var(--tinta) !important;
    background: transparent !important;
}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--acento) !important;
    box-shadow: 0 0 0 3px rgba(143, 211, 174, 0.35) !important;
}

/* ---------- Pestañas ---------- */
[data-baseweb="tab-list"] {
    gap: 6px;
}
button[data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600;
}
button[data-baseweb="tab"] p {
    color: var(--tinta-suave) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: #E6F4EC;
}
button[data-baseweb="tab"][aria-selected="true"] p {
    color: var(--acento-texto) !important;
}
[data-baseweb="tab-highlight"] {
    background: var(--acento) !important;
}
[data-baseweb="tab-border"] {
    display: none;
}

/* ---------- Formularios, desplegables, tablas y avisos ---------- */
[data-testid="stForm"] {
    background: var(--tarjeta);
    border: 1px solid var(--borde);
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 4px 14px rgba(31, 59, 45, 0.05);
}
[data-testid="stExpander"] {
    background: var(--tarjeta);
    border: 1px solid var(--borde) !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 10px rgba(31, 59, 45, 0.05);
    overflow: hidden;
}
[data-testid="stExpander"] summary p {
    font-weight: 600;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(31, 59, 45, 0.05);
}
[data-testid="stAlert"] {
    border-radius: 14px;
}
hr {
    border-color: var(--borde) !important;
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        transition: none !important;
        animation: none !important;
    }
}
"""


def aplicar():
    """Aplica el estilo a la página actual. Llamarla después de exigir_login()."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

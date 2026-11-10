"""Login de AsTech. La contraseña nunca queda en el código: se guarda como hash PBKDF2 en los secrets."""
import hashlib
import hmac
import time

import streamlit as st

MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300
ITERACIONES = 200_000


def hashear(clave, salt_hex):
    """Devuelve el hash PBKDF2-SHA256 de la clave con el salt dado (en hexadecimal)."""
    return hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"),
                               bytes.fromhex(salt_hex), ITERACIONES).hex()


def _config():
    """Lee el usuario, el salt y el hash desde la sección [auth] de los secrets."""
    try:
        a = st.secrets["auth"]
        return str(a["usuario"]), str(a["salt"]), str(a["password_hash"])
    except Exception:
        return None


def exigir_login():
    """Corta la ejecución de la app hasta que el usuario ingrese correctamente."""
    cfg = _config()
    if cfg is None:
        st.error("Falta configurar el login: agregá la sección [auth] en los secrets de la app.")
        st.stop()

    if st.session_state.get("autenticado"):
        return

    usuario_ok, salt, hash_ok = cfg
    st.title("🔒 AsTech · Ingreso")

    bloqueado_hasta = st.session_state.get("bloqueado_hasta", 0)
    if time.time() < bloqueado_hasta:
        restan = int(bloqueado_hasta - time.time())
        st.error(f"Demasiados intentos. Esperá {restan} segundos.")
        st.stop()

    with st.form("form_login"):
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Entrar", type="primary")

    if entrar:
        ok_usuario = hmac.compare_digest(usuario.strip().encode("utf-8"), usuario_ok.encode("utf-8"))
        ok_clave = hmac.compare_digest(hashear(clave, salt), hash_ok)
        if ok_usuario and ok_clave:
            st.session_state["autenticado"] = True
            st.session_state["intentos"] = 0
            st.rerun()

        intentos = st.session_state.get("intentos", 0) + 1
        st.session_state["intentos"] = intentos
        if intentos >= MAX_INTENTOS:
            st.session_state["bloqueado_hasta"] = time.time() + BLOQUEO_SEGUNDOS
            st.session_state["intentos"] = 0
            st.error(f"Demasiados intentos. Esperá {BLOQUEO_SEGUNDOS // 60} minutos.")
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()


def boton_cerrar_sesion():
    """Botón en la barra lateral para salir sin cerrar el navegador."""
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

import os
import json
import time
import platform
import streamlit as st
import paho.mqtt.client as paho

# 1. Configuración de página
st.set_page_config(
    page_title="CyberControl MQTT | Wokwi Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos Cyberpunk / Neón (CSS)
st.markdown("""
    <style>
    /* Fondo oscuro cibernético */
    .stApp {
        background-color: #0A0E17 !important;
        color: #E2E8F0 !important;
    }
    #MainMenu, footer, header {visibility: hidden;}

    /* Título principal con resplandor cian */
    .neon-title {
        font-size: 2.3rem;
        font-weight: 900;
        text-align: center;
        color: #00F0FF;
        text-shadow: 0 0 10px #00F0FF, 0 0 20px #00F0FF;
        margin-bottom: 0.5rem;
    }

    /* Subtítulos en azul neón */
    .cyan-sub-title {
        color: #00F0FF !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        text-shadow: 0 0 8px rgba(0, 240, 255, 0.6) !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* FORZAR BARRA LATERAL OSCURA Y NEÓN */
    section[data-testid="stSidebar"] {
        background-color: #121722 !important;
        border-right: 2px solid #00F0FF !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #00F0FF !important;
        font-weight: bold !important;
        text-shadow: 0 0 5px rgba(0, 240, 255, 0.5) !important;
    }

    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: #1A2232 !important;
        border: 1px solid #00F0FF !important;
        border-radius: 8px !important;
        padding: 10px !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #90CDF4 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #00FF66 !important;
        font-weight: bold !important;
    }

    /* Sliders */
    div[data-testid="stSlider"] {
        background-color: #1A2232 !important;
        padding: 12px !important;
        border-radius: 8px !important;
        border: 1px solid #00F0FF !important;
    }

    /* Botones Neón */
    div.stButton > button {
        width: 100%;
        background: transparent !important;
        color: #00FF66 !important;
        border: 2px solid #00FF66 !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.2) !important;
        transition: all 0.3s ease-in-out !important;
    }

    div.stButton > button:hover {
        background-color: #00FF66 !important;
        color: #0A0E17 !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.8) !important;
    }

    /* Estado de Lámpara Neón */
    .lamp-on {
        background-color: #122820;
        border: 2px solid #00FF66;
        color: #00FF66;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.5);
    }

    .lamp-off {
        background-color: #201218;
        border: 2px solid #FF007F;
        color: #FF007F;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.3);
    }

    .info-card {
        background: #181E2A;
        border: 1px solid #00F0FF;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Inicialización de estado de sesión (Historial y Contadores)
if "lamp_state" not in st.session_state:
    st.session_state.lamp_state = "OFF"
if "on_count" not in st.session_state:
    st.session_state.on_count = 0
if "off_count" not in st.session_state:
    st.session_state.off_count = 0
if "servo_angle" not in st.session_state:
    st.session_state.servo_angle = 0.0
if "action_history" not in st.session_state:
    st.session_state.action_history = []

# Configuración MQTT Broker
broker = "157.230.214.127"
port = 1883

def send_mqtt_message(client_id, topic, payload_dict):
    """Función auxiliar para publicar mensajes MQTT hacia Wokwi."""
    try:
        client = paho.Client(client_id)
        client.connect(broker, port)
        message = json.dumps(payload_dict)
        client.publish(topic, message)
        client.disconnect()
        return True
    except Exception as e:
        st.error(f"❌ Error de conexión MQTT: {e}")
        return False

# --- BARRA LATERAL (INFORMACIÓN Y MÉTRICAS) ---
with st.sidebar:
    st.markdown('<div class="cyan-sub-title">⚙️ Estado del Sistema</div>', unsafe_allow_html=True)
    st.write(f"**Python:** `v{platform.python_version()}`")
    st.write(f"**Broker MQTT:** `{broker}:{port}`")
    st.write("**Target Simulación:** Wokwi ESP32 / Arduino")

    st.markdown("---")
    st.markdown('<div class="cyan-sub-title">📊 Contadores de Uso</div>', unsafe_allow_html=True)
    st.metric("Encendidos (ON)", f"{st.session_state.on_count} veces")
    st.metric("Apagados (OFF)", f"{st.session_state.off_count} veces")
    st.metric("Ángulo Servo Activo", f"{st.session_state.servo_angle}°")

    st.markdown("---")
    if st.button("🗑️ Limpiar Historial"):
        st.session_state.on_count = 0
        st.session_state.off_count = 0
        st.session_state.action_history = []
        st.rerun()

# --- ENCABEZADO PRINCIPAL ---
st.markdown('<h1 class="neon-title">⚡ CYBERCONTROL PARA AMIGOS MQTT: WOKWI STUDIO 🤖</h1>', unsafe_allow_html=True)

st.markdown("""
    <div class="info-card">
        <p style="margin:0;">
            🌐 Panel de telemetría e interactividad inalámbrica. Controla la <strong>Lámpara Neón</strong> y la posición del <strong>Servomotor Palanca</strong> enviando tramas JSON al Broker MQTT.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- SECCIÓN 1: CONTROL DE LÁMPARA (ACTUADOR ON/OFF) ---
st.markdown('<div class="cyan-sub-title">💡 1. Control de Lámpara Neón (Tópico: miguel_1)</div>', unsafe_allow_html=True)

col_lamp_ctrl, col_lamp_status = st.columns([2, 1])

with col_lamp_ctrl:
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("⚡ ENCENDER LÁMPARA (ON)", type="primary"):
            if send_mqtt_message("BotonMelo_ON", "miguel_1", {"Act1": "ON"}):
                st.session_state.lamp_state = "ON"
                st.session_state.on_count += 1
                timestamp = time.strftime("%H:%M:%S")
                st.session_state.action_history.insert(0, f"[{timestamp}] 💡 Lámpara ENCENDIDA (ON)")
                st.rerun()

    with col_btn2:
        if st.button("🔴 APAGAR LÁMPARA (OFF)"):
            if send_mqtt_message("BotonMelo_OFF", "miguel_1", {"Act1": "OFF"}):
                st.session_state.lamp_state = "OFF"
                st.session_state.off_count += 1
                timestamp = time.strftime("%H:%M:%S")
                st.session_state.action_history.insert(0, f"[{timestamp}] 🔴 Lámpara APAGADA (OFF)")
                st.rerun()

with col_lamp_status:
    if st.session_state.lamp_state == "ON":
        st.markdown('<div class="lamp-on">💡 LÁMPARA ENCENDIDA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="lamp-off">🔴 LÁMPARA APAGADA</div>', unsafe_allow_html=True)

# --- SECCIÓN 2: CONTROL DE SERVOMOTOR (PALANCA ANALÓGICA) ---
st.markdown("---")
st.markdown('<div class="cyan-sub-title">🎛️ 2. Palanca de Ángulo para Servomotor (Tópico: miguel_2)</div>', unsafe_allow_html=True)

col_servo_slider, col_servo_btn = st.columns([3, 1])

with col_servo_slider:
    servo_val = st.slider(
        "Ajusta el ángulo o posición de la palanca (0.0° a 180.0°):",
        min_value=0.0,
        max_value=180.0,
        value=float(st.session_state.servo_angle),
        step=1.0
    )

with col_servo_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 ENVIAR ÁNGULO"):
        if send_mqtt_message("GIT-HUB_Servo", "miguel_2", {"Analog": float(servo_val)}):
            st.session_state.servo_angle = servo_val
            timestamp = time.strftime("%H:%M:%S")
            st.session_state.action_history.insert(0, f"[{timestamp}] ⚙️ Servomotor posicionado a {servo_val}°")
            st.success(f"Posición {servo_val}° enviada a Wokwi")
            st.rerun()

# --- SECCIÓN 3: HISTORIAL EN TIEMPO REAL ---
st.markdown("---")
st.markdown('<div class="cyan-sub-title">📜 3. Historial de Acciones y Telemetría</div>', unsafe_allow_html=True)

if st.session_state.action_history:
    for act in st.session_state.action_history[:8]:  # Muestra los últimos 8 registros
        st.markdown(f"- `{act}`")
else:
    st.info("💡 Aún no se han realizado acciones en esta sesión.")





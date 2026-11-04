import streamlit as st
import time
import random
import pandas as pd

st.set_page_config(page_title="Carrera de Pelotas Pro", page_icon="🏁", layout="centered")

# 1. Definir los corredores, sus mecánicas y multiplicadores de pago
# mov: lista de posibles avances por "turno" para definir su personalidad
corredores = {
    "Rojo": {"emoji": "🔴", "perfil": "Temerario (Acelera o se frena)", "mov": [0, 0, 4, 5], "pago": 5},
    "Azul": {"emoji": "🔵", "perfil": "Constante (Lento pero seguro)", "mov": [2, 2, 3, 3], "pago": 2},
    "Verde": {"emoji": "🟢", "perfil": "Caótico (Puede retroceder o volar)", "mov": [-1, 0, 3, 6], "pago": 6},
    "Amarillo": {"emoji": "🟡", "perfil": "Equilibrado (Ritmo normal)", "mov": [1, 2, 3, 4], "pago": 3}
}
distancia_meta = 40

# 2. Inicializar la memoria
if "saldo" not in st.session_state:
    st.session_state.saldo = 1000
if "fase" not in st.session_state:
    st.session_state.fase = "apuestas"

st.title("🏁 Gran Derbi: Edición Extrema")

# Marcador superior
col_saldo, _ = st.columns([1, 2])
col_saldo.metric("💰 Tu Saldo", f"{st.session_state.saldo} 🪙")
st.divider()

# --- FASE 1: APUESTAS ---
if st.session_state.fase == "apuestas":
    st.subheader("Estadísticas de los Corredores")
    
    # Mostrar tabla de cuotas para que el jugador decida su estrategia
    df_stats = pd.DataFrame({
        "Corredor": [f"{v['emoji']} {k}" for k, v in corredores.items()],
        "Estilo de Carrera": [v['perfil'] for v in corredores.values()],
        "Premio": [f"x{v['pago']}" for v in corredores.values()]
    })
    st.table(df_stats)
    
    st.subheader("Haz tu apuesta")
    col1, col2 = st.columns(2)
    with col1:
        apuesta_color = st.selectbox("Elige a tu campeón:", list(corredores.keys()))
    with col2:
        cantidad = st.number_input("Cantidad a apostar:", min_value=10, max_value=st.session_state.saldo, value=min(50, st.session_state.saldo), step=10)
    
    if st.button("🚦 ¡Arrancar Carrera!", type="primary", use_container_width=True):
        if cantidad > st.session_state.saldo:
            st.error("No tienes suficiente saldo.")
        else:
            st.session_state.saldo -= cantidad
            st.session_state.apuesta_actual = apuesta_color
            st.session_state.cantidad_apostada = cantidad
            st.session_state.fase = "carrera"
            st.rerun()

# --- FASE 2: ANIMACIÓN Y COMENTARISTA ---
elif st.session_state.fase == "carrera":
    st.subheader("¡La carrera está en marcha!")
    
    # Contenedores vacíos que actualizaremos en el bucle
    comentarista = st.empty()
    pista_animacion = st.empty()
    
    posiciones = {c: 0 for c in corredores}
    ganadores = []
    
    eventos = [
        "¡Qué derrape en la curva!",
        "La tensión se puede cortar con un cuchillo.",
        "¡Un espectador ha tirado un vaso de agua a la pista!",
        "¡Se pisan los talones!",
        "Los motores están al rojo vivo."
    ]
    
    while not ganadores:
        # Generar comentarios aleatorios
        if random.random() < 0.3: # 30% de probabilidad de nuevo comentario
            comentarista.info(f"🎙️ **Comentarista:** {random.choice(eventos)}")
            
        # Dibujar pista
        html_pista = "<div style='font-family: monospace; font-size: 20px; background-color: #1E1E1E; color: white; padding: 20px; border-radius: 10px;'>"
        for color, datos in corredores.items():
            pos = max(0, posiciones[color]) # Evitar que por retroceder rompa el HTML
            espacios = "&nbsp;" * pos
            restantes = "-" * max(0, (distancia_meta - pos))
            html_pista += f"<div style='margin-bottom: 10px;'>{datos['emoji']} | {espacios}💨{restantes} 🏁</div>"
        html_pista += "</div>"
        
        pista_animacion.markdown(html_pista, unsafe_allow_html=True)
        
        # Calcular nuevos movimientos basados en su personalidad (lista de probabilidades)
        for color in corredores:
            avance = random.choice(corredores[color]["mov"])
            posiciones[color] += avance
            
            # Comentarios especiales según el avance
            if avance == 6:
                comentarista.success(f"🎙️ **Comentarista:** ¡El {color} ha metido el turbo! ¡Increíble aceleración!")
            elif avance == -1:
                comentarista.error(f"🎙️ **Comentarista:** ¡Oh no! El {color} ha tropezado y pierde terreno.")
                
            if posiciones[color] >= distancia_meta:
                ganadores.append(color)
                
        time.sleep(0.3) # Un poco más lento para poder leer los comentarios
        
    st.session_state.posiciones_finales = posiciones
    st.session_state.ganador_carrera = ganadores[0] 
    st.session_state.fase = "resultado"
    st.rerun()

# --- FASE 3: RESULTADOS ---
elif st.session_state.fase == "resultado":
    ganador = st.session_state.ganador_carrera
    st.subheader(f"🏁 ¡El ganador es el {ganador} {corredores[ganador]['emoji']}!")
    
    # Dibujar pista final
    html_pista = "<div style='font-family: monospace; font-size: 20px; background-color: #1E1E1E; color: white; padding: 20px; border-radius: 10px;'>"
    for color, datos in corredores.items():
        pos = min(st.session_state.posiciones_finales[color], distancia_meta)
        pos = max(0, pos)
        espacios = "&nbsp;" * pos
        restantes = "-" * (distancia_meta - pos)
        html_pista += f"<div style='margin-bottom: 10px;'>{datos['emoji']} | {espacios}💨{restantes} 🏁</div>"
    html_pista += "</div>"
    st.markdown(html_pista, unsafe_allow_html=True)
    
    # Calcular premios
    apostado = st.session_state.apuesta_actual
    cantidad = st.session_state.cantidad_apostada
    multiplicador = corredores[apostado]["pago"]
    
    if ganador == apostado:
        premio = cantidad * multiplicador
        st.session_state.saldo += premio
        st.success(f"🏆 ¡Acertaste! El multiplicador del {ganador} era x{multiplicador}. Ganas **{premio} 🪙**.")
        st.balloons()
    else:
        st.error(f"❌ Fallaste. Perdiste tu apuesta de **{cantidad} 🪙**. (Habías apostado al {apostado}).")
        
    if st.session_state.saldo <= 0:
        st.error("Bancarrota. Te has quedado sin monedas.")
        if st.button("Pedir rescate al banco (Reiniciar)"):
            st.session_state.saldo = 1000
            st.session_state.fase = "apuestas"
            st.rerun()
    else:
        st.write("")
        if st.button("🔄 Ir a la siguiente carrera", type="primary"):
            st.session_state.fase = "apuestas"
            st.rerun()
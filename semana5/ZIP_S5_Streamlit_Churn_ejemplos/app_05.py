import streamlit as st
import streamlit.components.v1 as components
from model import predict

# Configuración con el favicon
st.set_page_config(page_title="S5 · Churn sintético", page_icon="icon.png", layout="centered")

# 1. Inicializar el estado de la sesión
if "first_run_completed" not in st.session_state:
    st.session_state.first_run_completed = False

if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "tenure": 2,
        "spend": 95.0,
        "calls": 4,
        "annual": False,
        "simulate_error": False
    }

st.title("¿Qué cliente podría darse de baja?")

# 2. Función para renderizar el formulario
def render_form(location):
    simulate_error = location.checkbox("Demo docente: provocar un error de contrato", value=st.session_state.form_data["simulate_error"])
    with location.form("churn_form"):
        tenure = st.number_input("Antigüedad (meses)", min_value=0, max_value=120, value=st.session_state.form_data["tenure"], step=1)
        spend = st.number_input("Gasto mensual (EUR)", min_value=0.0, max_value=300.0, value=st.session_state.form_data["spend"], step=1.0)
        calls = st.number_input("Llamadas a soporte", min_value=0, max_value=20, value=st.session_state.form_data["calls"], step=1)
        annual = st.checkbox("Contrato anual", value=st.session_state.form_data["annual"])
        
        submitted = st.form_submit_button("Calcular riesgo")
        
        if submitted:
            st.session_state.form_data = {
                "tenure": tenure,
                "spend": spend,
                "calls": calls,
                "annual": annual,
                "simulate_error": simulate_error
            }
            st.session_state.first_run_completed = True
            st.rerun()

# 3. Función para dibujar las cajas grises de los KPIs
def kpi_box(title, value):
    return f"""
    <div style="background-color: rgba(128, 128, 128, 0.15); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid rgba(128, 128, 128, 0.2);">
        <div style="font-size: 0.9em; opacity: 0.8; margin-bottom: 5px; font-weight: bold;">{title}</div>
        <div style="font-size: 1.6em; font-weight: bold;">{value}</div>
    </div>
    """

# 4. Lógica principal de visualización
if not st.session_state.first_run_completed:
    render_form(st)
    st.info("Completa el formulario y pulsa Calcular riesgo.")
else:
    st.sidebar.header("Modificar Parámetros")
    render_form(st.sidebar)
    
    # --- Botón para Descargar como PDF (Casi blanco) ---
    st.sidebar.markdown("---")
    
    components.html(
        """
        <button onclick="window.parent.print()" style="
            background-color: #f8f9fa; 
            color: #31333f; 
            border: 1px solid #d4d4d8; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            width: 100%;
            font-size: 16px;
            font-weight: 600;
            font-family: sans-serif;
            transition: all 0.2s;
        " onmouseover="this.style.backgroundColor='#e9ecef'" onmouseout="this.style.backgroundColor='#f8f9fa'">
            🖨️ Guardar como PDF
        </button>
        """,
        height=50
    )
    # -------------------------------------------------
    
    data = st.session_state.form_data
    
    # 5. Mostrar KPIs en cajas HTML
    col1, col2, col3, col4 = st.columns(4)
    
    col1.markdown(kpi_box("Antigüedad", f"{data['tenure']} ms"), unsafe_allow_html=True)
    col2.markdown(kpi_box("Gasto", f"{data['spend']} €"), unsafe_allow_html=True)
    col3.markdown(kpi_box("Llamadas", f"{data['calls']}"), unsafe_allow_html=True)
    
    contrato_str = "Sí" if data['annual'] else "No"
    col4.markdown(kpi_box("Anual", contrato_str), unsafe_allow_html=True)
    
    st.write("") 
    st.divider()
    
    # 6. Cálculo del riesgo y resultado
    values = {
        "tenure_months": data["tenure"], 
        "monthly_spend_eur": data["spend"],
        "support_calls": data["calls"], 
        "has_annual_contract": data["annual"]
    }
    
    if data["simulate_error"]:
        values["tenure_months"] = -1
        
    try:
        result = predict(**values)
    except ValueError:
        st.error("No se pudo calcular el riesgo. Revisa los datos e inténtalo de nuevo en la barra lateral.")
    else:
        st.subheader(result["label"])
        st.write(result["explanation"])
        
        risk_score = result['risk_score'] 
        risk_percentage = risk_score * 100
        
        hue = int((1 - risk_score) * 120)
        color = f"hsl({hue}, 100%, 45%)"
        
        st.markdown(f"### Riesgo estimado: **{risk_percentage:.0f}%**")
        
        progress_bar_html = f"""
        <div style="width: 100%; background-color: #e6e6e6; border-radius: 10px; margin-top: 10px;">
            <div style="width: {risk_percentage}%; background-color: {color}; height: 25px; border-radius: 10px; transition: width 0.5s ease-in-out, background-color 0.5s ease-in-out;">
            </div>
        </div>
        """
        st.markdown(progress_bar_html, unsafe_allow_html=True)
import streamlit as st

st.set_page_config(
    page_title="Calculadora de Transferencia de Calor",
    layout="wide",
    page_icon="🔥"
)

st.title("🔥 Calculadora de Transferencia de Calor")
st.markdown("""
Seleccione el modo de análisis:
""")

# Mapeo de opciones a páginas
page_mapping = {
    "Placa Plana (Convección)": "pages/flujo_paralelo_placa_plana.py",
    "Flujo Externo Cilindros (Convección)": "pages/flujo_externo_cilindro.py",
    "Flujo Interno Cilindros (Convección)": "pages/flujo_interno_cilindro.py",
    "Conducción Unidimensional": "pages/conduccion_unidimensional.py"
}

option = st.radio(
    "Modo de operación:",
    list(page_mapping.keys()),
    horizontal=True,
    index=None
)

if option:
    st.switch_page(page_mapping[option])  
else:
    st.info("Seleccione una opción del menú superior")

with st.expander("ℹ️ Instrucciones"):
    st.markdown("""
    ### Modos disponibles:
    1. **Convección**:
       - Placa plana (flujo externo)
       - Cilindros (flujo externo)
       - Flujo interno en tubos
    2. **Conducción 1D**:
       - Análisis unidimensional estacionario
       - Sistemas compuestos (paredes, cilindros, esferas)
    """)
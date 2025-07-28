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

option = st.radio(
    "Modo de operación:",
    [
        "Placa Plana (Convección)",
        "Flujo Externo Cilindros",
        "Flujo Interno Cilindros",
        "Conducción 1D"  # Nueva opción
    ],
    horizontal=True,
    index=None
)

if option:
    if option == "Placa Plana (Convección)":
        st.switch_page("pages/paraflow.py")
    elif option == "Flujo Externo Cilindros":
        st.switch_page("pages/exterflow.py")
    elif option == "Flujo Interno Cilindros":
        st.switch_page("pages/interflow.py")
    elif option == "Conducción 1D":
        st.switch_page("pages/conduc.py")  # Nuevo módulo
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
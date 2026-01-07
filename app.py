import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Lista Usuarios Maxplayer", page_icon="📊", layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📊 Lista de Usuarios Maxplayer")

try:
    API_TOKEN = st.secrets["API_TOKEN"]
except:
    st.error("⚠️ Falta API_TOKEN en secrets.toml")
    st.stop()

URL_API_MAXPLAYER = "https://api.maxplayer.tv/v3/api/public/users"

def obtener_lista_usuarios_maxplayer():
    try:
        headers = {"Api-Token": API_TOKEN, "Accept": "application/json"}
        res = requests.get(URL_API_MAXPLAYER, headers=headers, timeout=10)
        data = res.json()
        usuarios = data.get('data', []) if isinstance(data, dict) else data
        
        lista_final = []
        
        for cliente in usuarios:
            listas = cliente.get('lists', [])
            if listas:
                iptv = listas[0].get('iptv_info', {})
                u_iptv = iptv.get('username')
                p_iptv = iptv.get('password')
                fqdn = iptv.get('fqdn', 'N/A')
                
                lista_final.append({
                    "Usuario Maxplayer": cliente.get('username'),
                    "Username": u_iptv,
                    "Password": p_iptv,
                    "DNS/Dominio": fqdn
                })
        
        return pd.DataFrame(lista_final) if lista_final else None
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Cargar datos
if st.button("⬇️ Cargar Lista", type="primary"):
    with st.spinner("Obteniendo usuarios..."):
        df = obtener_lista_usuarios_maxplayer()
        if df is not None:
            st.session_state['df_usuarios'] = df
        else:
            st.error("No se pudieron obtener los usuarios.")

# Mostrar datos si existen
if 'df_usuarios' in st.session_state:
    df = st.session_state['df_usuarios'].copy()
    
    # Selector de dominio
    dominios = sorted(df['DNS/Dominio'].unique().tolist())
    dominios_filter = ["Todos"] + dominios
    
    col1, col2 = st.columns([2, 2])
    with col1:
        dominio_seleccionado = st.selectbox("🌐 Filtrar por Dominio:", dominios_filter)
    
    with col2:
        busqueda = st.text_input("🔍 Buscar usuario:", placeholder="Usuario, Username, Password...")
    
    # Filtrar por dominio
    if dominio_seleccionado != "Todos":
        df = df[df['DNS/Dominio'] == dominio_seleccionado]
    
    # Filtrar por búsqueda
    if busqueda:
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    # Agregar numeración
    df.insert(0, "Nº", range(1, len(df) + 1))
    
    # Mostrar tabla
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Descargar CSV
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"usuarios_maxplayer_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.info(f"📊 Total: {len(df)} usuarios")

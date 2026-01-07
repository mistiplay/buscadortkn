import streamlit as st
import requests
import pandas as pd

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
                
                lista_final.append({
                    "Usuario Maxplayer": cliente.get('username'),
                    "Username": u_iptv,
                    "Password": p_iptv
                })
        
        return pd.DataFrame(lista_final) if lista_final else None
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

if st.button("⬇️ Cargar Lista", type="primary"):
    with st.spinner("Obteniendo usuarios..."):
        df = obtener_lista_usuarios_maxplayer()
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name="usuarios_maxplayer.csv",
                mime="text/csv"
            )
        else:
            st.error("No se pudieron obtener los usuarios.")

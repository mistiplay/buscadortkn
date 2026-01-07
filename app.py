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
                host_base = f"http://{iptv.get('fqdn')}:{iptv.get('port')}"
                
                lista_final.append({
                    "Nº": "",
                    "Usuario Maxplayer": cliente.get('username'),
                    "Username": u_iptv,
                    "Password": p_iptv,
                    "DNS/Dominio": fqdn,
                    "host": host_base
                })
        
        return pd.DataFrame(lista_final) if lista_final else None
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def obtener_detalles_usuario(host, username, password):
    try:
        url = f"{host}/player_api.php?username={username}&password={password}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            info = data.get('user_info', {})
            ts = info.get('exp_date')
            
            fecha = "Ilimitada"
            if ts and str(ts) != 'null':
                fecha = datetime.fromtimestamp(int(ts)).strftime('%d/%m/%Y')
            
            conexiones = f"{info.get('active_cons', 0)}/{info.get('max_connections', 0)}"
            estado = "✅ Activa" if info.get('status') == 'Active' else "❌ Inactiva"
            
            return {
                "Estado": estado,
                "Vence": fecha,
                "Conexiones": conexiones
            }
        else:
            return {"Estado": "Error", "Vence": "-", "Conexiones": "-"}
    except:
        return {"Estado": "Error", "Vence": "-", "Conexiones": "-"}

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
    
    # Filtros
    col_filt1, col_filt2 = st.columns([2, 2])
    
    dominios = sorted(df['DNS/Dominio'].unique().tolist())
    dominios_filter = ["Todos"] + dominios
    
    with col_filt1:
        dominio_seleccionado = st.selectbox("🌐 Filtrar por Dominio:", dominios_filter)
    
    with col_filt2:
        busqueda = st.text_input("🔍 Buscar usuario:", placeholder="Usuario, Username, Password...")
    
    # Aplicar filtros
    if dominio_seleccionado != "Todos":
        df = df[df['DNS/Dominio'] == dominio_seleccionado]
    
    if busqueda:
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    # Agregar numeración
    df['Nº'] = range(1, len(df) + 1)
    
    # Layout: Tabla izquierda + Detalles derecha
    col_tabla, col_detalles = st.columns([2, 1])
    
    with col_tabla:
        st.subheader("👥 Usuarios")
        
        if len(df) == 0:
            st.warning("No hay usuarios que coincidan.")
        else:
            # Tabla con botones
            for idx, row in df.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([0.3, 1, 1, 1, 1, 0.5])
                
                with col1:
                    st.write(f"**{row['Nº']}**")
                with col2:
                    st.code(row['Usuario Maxplayer'], language="text")
                with col3:
                    st.code(row['Username'], language="text")
                with col4:
                    st.code(row['Password'], language="text")
                with col5:
                    st.write(row['DNS/Dominio'])
                with col6:
                    if st.button(f"ℹ️", key=f"btn_{idx}", use_container_width=True):
                        st.session_state['selected_user'] = idx
    
    with col_detalles:
        st.subheader("📊 Detalles")
        
        if 'selected_user' in st.session_state:
            idx = st.session_state['selected_user']
            row = df.iloc[idx]
            
            st.write(f"**Usuario:** {row['Usuario Maxplayer']}")
            
            with st.spinner("Cargando..."):
                detalles = obtener_detalles_usuario(row['host'], row['Username'], row['Password'])
            
            st.metric("Estado", detalles.get("Estado", "Error"))
            st.metric("Vencimiento", detalles.get("Vence", "Error"))
            st.metric("Conexiones", detalles.get("Conexiones", "Error"))
            
            if st.button("✕ Cerrar"):
                st.session_state.pop('selected_user', None)
                st.rerun()
        else:
            st.info("Selecciona un usuario para ver detalles")
    
    st.divider()
    
    # Descargar CSV
    df_display = df.drop('host', axis=1)
    csv = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"usuarios_maxplayer_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.info(f"📊 Total: {len(df)} usuarios")

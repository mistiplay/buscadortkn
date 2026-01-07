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

# Estilos personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1.5rem;
        letter-spacing: -0.02em;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #374151;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .user-card {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .detail-metric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 600;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1f2937;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 Lista de Usuarios Maxplayer</h1>', unsafe_allow_html=True)

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
                    "Usuario Maxplayer": cliente.get('username'),
                    "Username": u_iptv,
                    "Password": p_iptv,
                    "DNS/Dominio": fqdn,
                    "host": host_base
                })
        
        return pd.DataFrame(lista_final) if lista_final else None
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def obtener_detalles_usuario(host, username, password):
    """Obtiene vencimiento y conexiones del servidor IPTV"""
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
            return {"Estado": "⚠️ Error", "Vence": "-", "Conexiones": "-"}
    except:
        return {"Estado": "⚠️ Error", "Vence": "-", "Conexiones": "-"}

# Cargar datos
col_btn, col_space = st.columns([1, 5])
with col_btn:
    if st.button("⬇️ Cargar Lista", type="primary", use_container_width=True):
        with st.spinner("Obteniendo usuarios de Maxplayer..."):
            df = obtener_lista_usuarios_maxplayer()
            if df is not None:
                st.session_state['df_usuarios'] = df
            else:
                st.error("❌ No se pudieron obtener los usuarios.")

# Mostrar datos si existen
if 'df_usuarios' in st.session_state:
    df = st.session_state['df_usuarios'].copy()
    
    # Filtros
    st.markdown('<h2 class="section-header">🔍 Filtros</h2>', unsafe_allow_html=True)
    col_filt1, col_filt2 = st.columns([2, 2])
    
    dominios = sorted(df['DNS/Dominio'].unique().tolist())
    dominios_filter = ["🌐 Todos"] + [f"🌐 {d}" for d in dominios]
    
    with col_filt1:
        dominio_seleccionado = st.selectbox("Filtrar por Dominio:", dominios_filter, key="sel_dominio")
    
    with col_filt2:
        busqueda = st.text_input("🔍 Buscar usuario:", placeholder="Usuario, Username, Password, DNS...")
    
    # Aplicar filtros
    if dominio_seleccionado != "🌐 Todos":
        dominio_limpio = dominio_seleccionado.replace("🌐 ", "")
        df = df[df['DNS/Dominio'] == dominio_limpio]
    
    if busqueda:
        mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    # Agregar numeración
    df.insert(0, "Nº", range(1, len(df) + 1))
    
    # Mostrar usuarios
    st.markdown('<h2 class="section-header">👥 Usuarios</h2>', unsafe_allow_html=True)
    
    if len(df) == 0:
        st.warning("⚠️ No hay usuarios que coincidan con los filtros.")
    else:
        for idx, row in df.iterrows():
            with st.expander(f"**Nº {row['Nº']}** • {row['Usuario Maxplayer']} • {row['DNS/Dominio']}", expanded=False):
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.markdown("**👤 Usuario Maxplayer**")
                    st.code(row['Usuario Maxplayer'], language="text")
                
                with col2:
                    st.markdown("**🔑 Username IPTV**")
                    st.code(row['Username'], language="text")
                
                with col3:
                    st.markdown("**🔐 Password IPTV**")
                    st.code(row['Password'], language="text")
                
                st.markdown("---")
                
                # Botón para cargar detalles
                if st.button(f"📊 Cargar Detalles", key=f"detail_btn_{idx}", use_container_width=True):
                    st.session_state[f'load_detail_{idx}'] = True
                
                # Mostrar detalles si se cargan
                if st.session_state.get(f'load_detail_{idx}', False):
                    with st.spinner("⏳ Consultando servidor IPTV..."):
                        detalles = obtener_detalles_usuario(row['host'], row['Username'], row['Password'])
                    
                    col_det1, col_det2, col_det3 = st.columns(3)
                    
                    with col_det1:
                        st.markdown('<div class="detail-metric">', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-label">Estado</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-value">{detalles.get("Estado", "Error")}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col_det2:
                        st.markdown('<div class="detail-metric">', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-label">Vencimiento</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-value">📅 {detalles.get("Vence", "Error")}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col_det3:
                        st.markdown('<div class="detail-metric">', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-label">Conexiones</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-value">🔗 {detalles.get("Conexiones", "Error")}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if st.button(f"✕ Cerrar Detalles", key=f"close_detail_{idx}", use_container_width=True):
                        st.session_state[f'load_detail_{idx}'] = False
                        st.rerun()
    
    st.divider()
    
    # Descargar CSV
    st.markdown('<h2 class="section-header">📥 Exportar</h2>', unsafe_allow_html=True)
    df_display = df.drop('host', axis=1)
    csv = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"usuarios_maxplayer_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.info(f"📊 **Total: {len(df)} usuarios** | 🌐 Dominio: {dominio_seleccionado}")

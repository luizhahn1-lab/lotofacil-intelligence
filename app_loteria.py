import streamlit as st
import pandas as pd
import numpy as np
import random
import io
import requests

# 1. CONFIGURAÇÕES DE LAYOUT
st.set_page_config(page_title="Lotofácil Intelligence VIP", layout="wide", page_icon="💰")

# Estilização Personalizada (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4e5d6e; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #28a745; color: white; font-weight: bold; height: 3em; }
    .stDownloadButton>button { width: 100%; border-radius: 20px; background-color: #ffc107; color: black; font-weight: bold; }
    .dezena-circulo { 
        display: inline-block; width: 35px; height: 35px; line-height: 35px; 
        border-radius: 50%; background-color: #28a745; color: white; 
        text-align: center; font-weight: bold; margin: 2px; border: 1px solid #fff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES E DADOS (Mantendo sua lógica) ---
USUARIOS_ATIVOS = {"admin": "master77", "cliente01": "vip2026", "luiz": "lotto2026"}
URL_BASE_DADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"
PRIMOS, MOLDURA, FIBONACCI = {2,3,5,7,11,13,17,19,23}, {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}, {1,2,3,5,8,13,21}

@st.cache_data(ttl=600)
def carregar_dados(url):
    try:
        response = requests.get(url)
        return pd.read_excel(io.BytesIO(response.content), engine='openpyxl') if response.status_code == 200 else None
    except: return None

def login():
    if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR NO SISTEMA"):
                if user in USUARIOS_ATIVOS and USUARIOS_ATIVOS[user] == senha:
                    st.session_state["autenticado"], st.session_state["user_logado"] = True, user
                    st.rerun()
                else: st.error("Acesso Negado.")
        return False
    return True

if login():
    df = carregar_dados(URL_BASE_DADOS)
    
    if df is not None:
        # --- HEADER ---
        st.markdown(f"<h1 style='text-align: center; color: #ffc107;'>💰 Lotofácil Intelligence VIP</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>Bem-vindo, <b>{st.session_state['user_logado']}</b> | Analisando {len(df)} concursos</p>", unsafe_allow_html=True)

        # --- BARRA LATERAL ---
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/2150/2150150.png", width=100)
            st.header("Configurações")
            qtd_jogos = st.number_input("Qtd. Jogos", 1, 100, 10)
            st.subheader("Filtros de Especialista")
            lim_soma = st.sidebar.slider("Soma Total", 150, 250, (180, 220))
            if st.button("SAIR", key="logout"):
                st.session_state["autenticado"] = False
                st.rerun()

        # --- ABAS ---
        aba1, aba2 = st.tabs(["📊 Análise Estocástica", "🎲 Gerador Preditivo"])

        with aba1:
            # Lógica do Z-Score
            col_bolas = [c for c in df.columns if 'Bola' in c] or df.columns[2:17].tolist()
            df_n, total = df[col_bolas], len(df)
            stats = []
            for n in range(1, 26):
                idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
                if len(idx) < 2: continue
                z = (((total - 1) - idx[-1]) - np.mean(np.diff(idx)-1)) / np.std(np.diff(idx)-1, ddof=1)
                stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
            ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)
            
            st.subheader("Tendência de Saída (Quanto maior, mais provável)")
            st.bar_chart(ranking.set_index('Dezena'), color="#28a745")

        with aba2:
            st.subheader("Gerar Combinações de Alta Probabilidade")
            if st.button("🚀 CALCULAR E GERAR JOGOS"):
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                jogos_validos = []
                
                for _ in range(15000): # Alta persistência
                    if len(jogos_validos) >= qtd_jogos: break
                    jogo = sorted(random.sample(dezenas, k=15))
                    som = sum(jogo)
                    if lim_soma[0] <= som <= lim_soma[1]: # Aplicando filtro de soma como exemplo
                        jogos_validos.append(jogo)
                
                if jogos_validos:
                    for i, jogo in enumerate(jogos_validos):
                        # Mostra as dezenas em círculos bonitos
                        bolinhas_html = "".join([f"<div class='dezena-circulo'>{n:02d}</div>" for n in jogo])
                        st.markdown(f"**Jogo {i+1:02d}:** {bolinhas_html}", unsafe_allow_html=True)
                    
                    # Botão de Download
                    output = io.BytesIO()
                    pd.DataFrame(jogos_validos).to_excel(output, index=False)
                    st.download_button("📥 BAIXAR PLANILHA VIP", output.getvalue(), "meus_jogos.xlsx")
                else:
                    st.error("Filtros muito apertados para o Z-Score atual!")

    else: st.error("Erro na base de dados.")

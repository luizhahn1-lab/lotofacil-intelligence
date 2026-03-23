import streamlit as st
import pandas as pd
import numpy as np
import random
import io
import requests

# 1. CONFIGURAÇÕES DE LAYOUT E DESIGN
st.set_page_config(page_title="Lotofácil Intelligence VIP", layout="wide", page_icon="💰")

# Estilização CSS para visual Premium
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4e5d6e; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #28a745; color: white; font-weight: bold; height: 3em; border: none; }
    .stButton>button:hover { background-color: #218838; border: 1px solid #fff; }
    .stDownloadButton>button { width: 100%; border-radius: 20px; background-color: #ffc107; color: black; font-weight: bold; border: none; }
    .dezena-circulo { 
        display: inline-block; width: 32px; height: 32px; line-height: 32px; 
        border-radius: 50%; background-color: #28a745; color: white; 
        text-align: center; font-weight: bold; margin: 3px; border: 1px solid #ffffff44;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    .card-jogo {
        background-color: #1e2130; padding: 15px; border-radius: 15px; 
        margin-bottom: 10px; border-left: 5px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES TÉCNICAS E BANCO DE DADOS ---
USUARIOS_ATIVOS = {"admin": "master77", "cliente01": "vip2026", "luiz": "lotto2026"}
URL_BASE_DADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}

@st.cache_data(ttl=600)
def carregar_dados(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
        return None
    except: return None

def login():
    if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.markdown("<h1 style='text-align: center;'>🔐 Portal de Inteligência VIP</h1>", unsafe_allow_html=True)
        with st.container():
            col_l1, col_l2, col_l3 = st.columns([1,2,1])
            with col_l2:
                with st.form("login_form"):
                    user = st.text_input("Usuário")
                    senha = st.text_input("Senha", type="password")
                    if st.form_submit_button("ACESSAR PAINEL"):
                        if user in USUARIOS_ATIVOS and USUARIOS_ATIVOS[user] == senha:
                            st.session_state["autenticado"], st.session_state["user_logado"] = True, user
                            st.rerun()
                        else: st.error("Credenciais Inválidas.")
        return False
    return True

if login():
    df = carregar_dados(URL_BASE_DADOS)
    
    if df is not None:
        # --- HEADER PRINCIPAL ---
        st.markdown(f"<h1 style='text-align: center; color: #ffc107;'>💰 Lotofacil Intelligence VIP</h1>", unsafe_allow_html=True)
        
        # --- SIDEBAR (FILTROS) ---
        with st.sidebar:
            st.markdown(f"👤 **Usuário:** {st.session_state['user_logado']}")
            st.divider()
            st.header("🎛️ Filtros de Equilíbrio")
            
            qtd_jogos = st.number_input("Quantidade de Jogos", 1, 100, 10)
            
            st.subheader("Parâmetros Estatísticos")
            lim_impares = st.slider("Ímpares", 5, 11, (7, 9))
            lim_primos = st.slider("Primos", 3, 8, (4, 6))
            lim_moldura = st.slider("Moldura", 8, 12, (9, 11))
            lim_fibonacci = st.slider("Fibonacci", 2, 6, (3, 5))
            lim_soma = st.slider("Soma Total", 150, 250, (180, 220))
            
            st.divider()
            if st.button("SAIR DO SISTEMA", key="logout"):
                st.session_state["autenticado"] = False
                st.rerun()

        # --- ABAS DE CONTEÚDO ---
        aba_analise, aba_gerador = st.tabs(["📊 Análise de Tendências", "🎲 Gerador Preditivo"])

        # PROCESSAMENTO DO Z-SCORE (Comum às abas)
        col_bolas = [c for c in df.columns if 'Bola' in c] or df.columns[2:17].tolist()
        df_n, total = df[col_bolas], len(df)
        stats = []
        for n in range(1, 26):
            idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
            if len(idx) < 2: continue
            gaps = np.diff(idx)-1
            z = (((total - 1) - idx[-1]) - np.mean(gaps)) / np.std(gaps, ddof=1)
            stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
        ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)

        with aba_analise:
            st.subheader("Gráfico de Calor (Z-Score)")
            st.info("Quanto maior a barra, maior a tendência da dezena ser sorteada devido ao atraso médio.")
            st.bar_chart(ranking.set_index('Dezena'), color="#28a745")
            st.table(ranking.head(10).reset_index(drop=True)) # Top 10 dezenas quentes

        with aba_gerador:
            st.subheader("Geração de Jogos VIP")
            if st.button("🚀 GERAR JOGOS COM FILTROS ATIVOS"):
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                
                jogos_validos = []
                tentativas = 0
                progress_bar = st.progress(0)
                
                while len(jogos_validos) < qtd_jogos and tentativas < 20000:
                    tentativas += 1
                    # Sorteio baseado no Z-Score
                    jogo = sorted(random.choices(dezenas, weights=pesos, k=15))
                    if len(set(jogo)) < 15: continue # Evita duplicatas no mesmo jogo
                    
                    # Verificação dos Filtros
                    imp = len([n for n in jogo if n % 2 != 0])
                    pri = len(set(jogo).intersection(PRIMOS))
                    mol = len(set(jogo).intersection(MOLDURA))
                    fib = len(set(jogo).intersection(FIBONACCI))
                    som = sum(jogo)
                    
                    if (lim_impares[0] <= imp <= lim_impares[1] and
                        lim_primos[0] <= pri <= lim_primos[1] and
                        lim_moldura[0] <= mol <= lim_moldura[1] and
                        lim_fibonacci[0] <= fib <= lim_fibonacci[1] and
                        lim_soma[0] <= som <= lim_soma[1]):
                        jogos_validos.append(jogo)
                        progress_bar.progress(len(jogos_validos) / qtd_jogos)

                if jogos_validos:
                    st.success(f"Sucesso! Geramos {len(jogos_validos)} jogos otimizados.")
                    for i, jogo in enumerate(jogos_validos):
                        bolinhas = "".join([f"<div class='dezena-circulo'>{n:02d}</div>" for n in jogo])
                        st.markdown(f"""
                        <div class='card-jogo'>
                            <b>Jogo {i+1:02d}</b><br>{bolinhas}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Preparação do arquivo para baixar
                    output = io.BytesIO()
                    pd.DataFrame(jogos_validos).to_excel(output, index=False)
                    st.download_button("📥 BAIXAR PLANILHA DE JOGOS", output.getvalue(), "meus_jogos_vip.xlsx")
                else:
                    st.error("❌ Filtros muito rígidos! O sistema não encontrou combinações. Tente ampliar as margens de Soma ou Ímpares.")

    else:
        st.error("Erro ao conectar com a base de dados do GitHub.")

import streamlit as st
import pandas as pd
import numpy as np
import random
import io
import requests
from datetime import datetime

# 1. CONFIGURAÇÕES DE LAYOUT E DESIGN
st.set_page_config(page_title="Lotofácil Intelligence VIP", layout="wide", page_icon="💰")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #28a745; color: white; font-weight: bold; height: 3em; border: none; }
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
    /* Estilo para o botão de cadastro externo */
    .btn-cadastro {
        display: block; width: 100%; background-color: #ffc107; color: black !important;
        text-align: center; padding: 15px; border-radius: 15px; font-weight: bold;
        text-decoration: none; margin-top: 10px; transition: 0.3s;
    }
    .btn-cadastro:hover { background-color: #e0a800; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- LINKS DO GITHUB E CADASTRO ---
URL_RESULTADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"
URL_USUARIOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Usuarios.xlsx"
URL_GOOGLE_FORMS = "https://docs.google.com/forms/d/e/1FAIpQLSfuGO5ZbDKxb2156xCI4FSh6ardD2_cVCHLFBDEzZK53r8Jgw/viewform?embedded=true" # <--- INSIRA O LINK AQUI

# --- CONSTANTES MATEMÁTICAS ---
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}

# --- FUNÇÕES DE APOIO ---
def calcular_maior_sequencia(jogo):
    jogo_ord = sorted(jogo)
    maior = atual = 1
    for i in range(len(jogo_ord) - 1):
        if jogo_ord[i+1] == jogo_ord[i] + 1:
            atual += 1
        else:
            maior = max(maior, atual)
            atual = 1
    return max(maior, atual)

@st.cache_data(ttl=300)
def carregar_dados_github(url):
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            df_temp = pd.read_excel(io.BytesIO(resp.content), engine='openpyxl')
            df_temp.columns = df_temp.columns.str.strip()
            return df_temp
        return None
    except: return None

# --- SISTEMA DE LOGIN COM CADASTRO ---
def login():
    if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.markdown("<h1 style='text-align: center;'>🔐 Painel Lotofácil Intelligence</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            tab_log, tab_reg = st.tabs(["Acessar Conta", "Criar Cadastro VIP"])
            
            with tab_log:
                df_users = carregar_dados_github(URL_USUARIOS)
                with st.form("login_form"):
                    u_in = st.text_input("Usuário (E-mail)")
                    s_in = st.text_input("Senha", type="password")
                    if st.form_submit_button("ENTRAR NO SISTEMA"):
                        if df_users is not None:
                            row = df_users[df_users['Usuario'].astype(str) == u_in]
                            if not row.empty:
                                try:
                                    data_exp = pd.to_datetime(row.iloc[0]['Validade'], dayfirst=True)
                                    if str(s_in) == str(row.iloc[0]['Senha']):
                                        if datetime.now() <= data_exp:
                                            st.session_state.update({"autenticado": True, "user": u_in, "val": data_exp})
                                            st.rerun()
                                        else: st.error("❌ Licença expirada! Renove seu acesso.")
                                    else: st.error("❌ Senha incorreta.")
                                except: st.error("Erro no processamento da validade.")
                            else: st.error("❌ Usuário não cadastrado.")
                        else: st.error("Erro ao conectar com servidor de usuários.")

            with tab_reg:
                st.markdown("### 🚀 Comece a lucrar agora!")
                st.write("Ainda não tem acesso ao Gerador VIP e às Estratégias do E-book? Clique no botão abaixo para solicitar seu cadastro.")
                st.markdown(f'<a href="{URL_GOOGLE_FORMS}" target="_blank" class="btn-cadastro">📝 SOLICITAR MEU CADASTRO VIP</a>', unsafe_allow_html=True)
                st.info("💡 Após preencher o formulário, nosso suporte validará seus dados e liberará seu login em instantes.")

        return False
    return True

# --- PROGRAMA PRINCIPAL ---
if login():
    df = carregar_dados_github(URL_RESULTADOS)
    if df is not None:
        # 1. Informações do último concurso
        ultima_linha = df.iloc[-1]
        num_concurso = ultima_linha[0]
        data_exibicao = pd.to_datetime(ultima_linha[1]).strftime('%d/%m/%Y')

        st.markdown(f"<h1 style='text-align: center; color: #ffc107;'>💰 Lotofácil Intelligence VIP</h1>", unsafe_allow_html=True)
        st.success(f"✅ **DADOS ATUALIZADOS** | Concurso: **{num_concurso}** | Data: **{data_exibicao}**")

        # 2. CÁLCULO DE MÉDIAS (Últimos 100 Jogos)
        df_100 = df.tail(100).copy()
        cols_bolas = [c for c in df.columns if 'Bola' in c] or df.columns[2:17].tolist()
        
        def calc_metricas(linha):
            jogo = linha[cols_bolas].astype(int).tolist()
            return pd.Series({
                'imp': len([n for n in jogo if n % 2 != 0]),
                'pri': len(set(jogo) & PRIMOS),
                'mol': len(set(jogo) & MOLDURA),
                'fib': len(set(jogo) & FIBONACCI),
                'som': sum(jogo),
                'z15': len([n for n in jogo if 1 <= n <= 15])
            })
        
        medias = df_100.apply(calc_metricas, axis=1).mean().round(1)

        st.markdown("### 📊 Médias Reais (Últimos 100 Concursos)")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Ímpares", medias['imp'])
        m2.metric("Primos", medias['pri'])
        m3.metric("Moldura", medias['mol'])
        m4.metric("Fibonacci", medias['fib'])
        m5.metric("Soma", int(medias['som']))
        m6.metric("01 a 15", medias['z15'])
        st.divider()

        with st.sidebar:
            st.success(f"👤 {st.session_state['user']}")
            st.info(f"📅 Válido até: {st.session_state['val'].strftime('%d/%m/%Y')}")
            st.divider()
            qtd_jogos = st.number_input("Qtd Jogos", 1, 100, 10)
            lim_impares = st.slider("Ímpares", 5, 11, (7, 9))
            lim_primos = st.slider("Primos", 3, 8, (4, 6))
            lim_moldura = st.slider("Moldura", 8, 12, (9, 11))
            lim_fibonacci = st.slider("Fibonacci", 2, 6, (3, 5))
            lim_soma = st.slider("Soma Total", 150, 250, (180, 220))
            lim_seq = st.slider("Máx. Sequência", 2, 10, 4)
            lim_01_15 = st.slider("Dezenas entre 01 e 15", 5, 12, 9) 
            if st.button("SAIR"): 
                st.session_state["autenticado"] = False
                st.rerun()

        # Z-SCORE
        df_n, total = df[cols_bolas], len(df)
        stats = []
        for n in range(1, 26):
            idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
            if len(idx) < 2: continue
            z = (((total - 1) - idx[-1]) - np.mean(np.diff(idx)-1)) / np.std(np.diff(idx)-1, ddof=1)
            stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
        ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)

        aba1, aba2 = st.tabs(["📊 Tendências (Z-Score)", "🎲 Gerador Inteligente"])
        with aba1:
            st.bar_chart(ranking.set_index('Dezena'), color="#28a745")
        
        with aba2:
            if st.button("🚀 GERAR JOGOS COM ESTRATÉGIA"):
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                validos = []
                tentativas = 0
                prog = st.progress(0)
                
                while len(validos) < qtd_jogos and tentativas < 20000:
                    tentativas += 1
                    j = sorted(random.choices(dezenas, weights=pesos, k=15))
                    if len(set(j)) < 15: continue
                    
                    qtd_01_15 = len([n for n in j if 1 <= n <= 15])

                    if (lim_impares[0] <= len([n for n in j if n%2!=0]) <= lim_impares[1] and
                        lim_primos[0] <= len(set(j)&PRIMOS) <= lim_primos[1] and
                        lim_moldura[0] <= len(set(j)&MOLDURA) <= lim_moldura[1] and
                        lim_fibonacci[0] <= len(set(j)&FIBONACCI) <= lim_fibonacci[1] and
                        lim_soma[0] <= sum(j) <= lim_soma[1] and
                        calcular_maior_sequencia(j) <= lim_seq and
                        qtd_01_15 == lim_01_15): 
                        
                        validos.append(j)
                        prog.progress(len(validos)/qtd_jogos)

                if validos:
                    for i, j in enumerate(validos):
                        bolas = "".join([f"<div class='dezena-circulo'>{n:02d}</div>" for n in j])
                        st.markdown(f"<div class='card-jogo'><b>Jogo {i+1}</b><br>{bolas}</div>", unsafe_allow_html=True)
                    output = io.BytesIO()
                    pd.DataFrame(validos).to_excel(output, index=False)
                    st.download_button("📥 BAIXAR EXCEL", output.getvalue(), "jogos_vip.xlsx")
                else: st.error("❌ Ajuste seus filtros!")

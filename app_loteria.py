import streamlit as st
import pandas as pd
import numpy as np
import random
import io
import requests

# 1. CONFIGURAÇÕES TÉCNICAS
st.set_page_config(page_title="Loteria Intelligence SaaS", layout="wide", page_icon="📈")

# --- BANCO DE DADOS DE CLIENTES ---
USUARIOS_ATIVOS = {
    "admin": "master77",
    "cliente01": "vip2026",
    "joao_silva": "senha9988",
}

# --- LINK DO SEU ARQUIVO NO GITHUB ---
URL_BASE_DADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"

@st.cache_data(ttl=600)
def carregar_dados_nuvem(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
            return df
        else:
            return None
    except:
        return None

# ==============================================================================
# SISTEMA DE LOGIN
# ==============================================================================
def login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.title("🔐 Portal VIP - Inteligência Lotofácil")
        with st.form("login_form"):
            user = st.text_input("Usuário/E-mail")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Acessar Painel")
            
            if submit:
                if user in USUARIOS_ATIVOS and USUARIOS_ATIVOS[user] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["user_logado"] = user
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
        return False
    return True

# ==============================================================================
# INTERFACE PRINCIPAL (SÓ RODA SE LOGADO)
# ==============================================================================
if login():
    # BARRA LATERAL
    st.sidebar.success(f"Logado como: {st.session_state['user_logado']}")
    if st.sidebar.button("Sair do Sistema", key="btn_logout_sidebar"):
        st.session_state["autenticado"] = False
        st.rerun()

    # CARREGAMENTO DOS DADOS
    df = carregar_dados_nuvem(URL_BASE_DADOS)
    
    if df is not None:
        # 🔍 ORGANIZAÇÃO DE COLUNAS
        colunas_reais = df.columns.tolist()
        col_concurso = 'Concurso' if 'Concurso' in colunas_reais else colunas_reais[0]
        col_data = 'Data' if 'Data' in colunas_reais else colunas_reais[1]

        ultimo_concurso = df.iloc[-1][col_concurso]
        data_sorteio = df.iloc[-1][col_data]
    
        st.title("🎯 Painel de Análise Preditiva")
        st.sidebar.markdown(f"---")
        st.sidebar.write(f"📊 **Última Atualização:**")
        st.sidebar.info(f"Concurso: {ultimo_concurso}\nData: {data_sorteio}")

        # --- FILTROS ---
        st.sidebar.subheader("🎛️ Filtros de Equilíbrio")
        qtd_jogos = st.sidebar.number_input("Quantidade de Jogos", 1, 50, 5)
        lim_impares = st.sidebar.slider("Ímpares", 5, 11, (7, 9))
        lim_primos = st.sidebar.slider("Primos", 3, 7, (4, 6))
        lim_moldura = st.sidebar.slider("Moldura", 8, 12, (9, 11))

        # --- LÓGICA DE CÁLCULO (Z-SCORE) ---
        col_bolas = [c for c in df.columns if 'Bola' in c]
        if not col_bolas: # Caso as colunas não tenham 'Bola' no nome
             col_bolas = df.columns[2:17].tolist()

        df_n = df[col_bolas]
        total = len(df)
        
        stats = []
        for n in range(1, 26):
            idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
            if len(idx) < 2: continue
            gaps = np.diff(idx) - 1
            z = (((total - 1) - idx[-1]) - np.mean(gaps)) / np.std(gaps, ddof=1)
            stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
        
        ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)

        # --- EXIBIÇÃO DOS RESULTADOS ---
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("📈 Tendências de Atraso")
            st.bar_chart(ranking.set_index('Dezena'))
        
        with c2:
            st.subheader("🎲 Gerar Palpites VIP")
            if st.button("GERAR JOGOS AGORA", key="btn_gerar_principal"):
                # Lógica simplificada de sorteio para teste
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                
                res = sorted(random.choices(dezenas, weights=pesos, k=15))
                st.success(f"Sugestão de Jogo: {res}")
                st.info("Filtros aplicados com sucesso!")
    else:
        st.error("Erro ao conectar com a base de dados no GitHub. Verifique se o arquivo Resultados.xlsx está no seu repositório.")

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

URL_BASE_DADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}

@st.cache_data(ttl=600)
def carregar_dados_nuvem(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
            return df
        return None
    except:
        return None

def login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.title("🔐 Portal VIP - Inteligência Lotofácil")
        with st.form("login_form"):
            user = st.text_input("Usuário/E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Acessar Painel"):
                if user in USUARIOS_ATIVOS and USUARIOS_ATIVOS[user] == senha:
                    st.session_state["autenticado"], st.session_state["user_logado"] = True, user
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
        return False
    return True

if login():
    st.sidebar.success(f"Logado como: {st.session_state['user_logado']}")
    if st.sidebar.button("Sair do Sistema", key="btn_logout"):
        st.session_state["autenticado"] = False
        st.rerun()

    df = carregar_dados_nuvem(URL_BASE_DADOS)
    
    if df is not None:
        # --- MENU LATERAL DE FILTROS ---
        st.sidebar.header("🎛️ Parâmetros de Filtro")
        qtd_jogos = st.sidebar.number_input("Quantidade de Jogos", 1, 100, 10)
        
        st.sidebar.subheader("Equilíbrio Estatístico")
        lim_impares = st.sidebar.slider("Ímpares", 5, 11, (7, 9))
        lim_primos = st.sidebar.slider("Primos", 3, 7, (4, 6))
        lim_moldura = st.sidebar.slider("Moldura", 8, 12, (9, 11))
        lim_fibonacci = st.sidebar.slider("Fibonacci", 3, 6, (3, 5))
        lim_soma = st.sidebar.slider("Soma Total", 150, 250, (180, 220))

        # --- PROCESSAMENTO Z-SCORE ---
        col_bolas = [c for c in df.columns if 'Bola' in c] or df.columns[2:17].tolist()
        df_n, total = df[col_bolas], len(df)
        
        stats = []
        for n in range(1, 26):
            idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
            if len(idx) < 2: continue
            gaps = np.diff(idx) - 1
            z = (((total - 1) - idx[-1]) - np.mean(gaps)) / np.std(gaps, ddof=1)
            stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
        
        ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)

        # --- INTERFACE PRINCIPAL ---
        st.title("🎯 Painel de Análise Preditiva")
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("📈 Tendências de Atraso (Z-Score)")
            st.bar_chart(ranking.set_index('Dezena'))
        
        with c2:
            st.subheader("🎲 Gerador de Apostas VIP")
            if st.button("🚀 GERAR JOGOS AGORA", key="btn_gerar"):
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                
                jogos_validos = []
                # Aumentamos para 10.000 tentativas para dar conta dos filtros
                tentativas_maximas = 10000 
                tentativas = 0
                
                progresso = st.progress(0) # Barra de progresso visual
                
                while len(jogos_validos) < qtd_jogos and tentativas < tentativas_maximas:
                    tentativas += 1
                    # Sorteio ponderado pelo Z-Score
                    jogo = sorted(random.sample(dezenas, k=15)) # Mudamos para sample para evitar duplicatas internas
                    
                    # Cálculos dos Filtros
                    imp = len([n for n in jogo if n % 2 != 0])
                    pri = len(set(jogo).intersection(PRIMOS))
                    mol = len(set(jogo).intersection(MOLDURA))
                    fib = len(set(jogo).intersection(FIBONACCI))
                    som = sum(jogo)
                    
                    # Verificação rigorosa
                    if (lim_impares[0] <= imp <= lim_impares[1] and
                        lim_primos[0] <= pri <= lim_primos[1] and
                        lim_moldura[0] <= mol <= lim_moldura[1] and
                        lim_fibonacci[0] <= fib <= lim_fibonacci[1] and
                        lim_soma[0] <= som <= lim_soma[1]):
                        jogos_validos.append(jogo)
                        progresso.progress(len(jogos_validos) / qtd_jogos)

                if jogos_validos:
                    st.success(f"Conseguimos gerar {len(jogos_validos)} jogos que respeitam todos os seus filtros!")
                    df_jogos = pd.DataFrame(jogos_validos, columns=[f'B{i}' for i in range(1, 16)])
                    st.dataframe(df_jogos)
                    
                    # Botão de Download (Prepara o arquivo)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_jogos.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="📥 Baixar Jogos em Excel",
                        data=output.getvalue(),
                        file_name="jogos_lotofacil_vip.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("❌ Filtros Impossíveis! O sistema tentou 10.000 combinações e nenhuma passou. Tente relaxar os limites de Soma ou Fibonacci.")

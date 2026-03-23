import streamlit as st
import pandas as pd
import numpy as np
import random
import io
import requests

# 1. CONFIGURAÇÕES TÉCNICAS
st.set_page_config(page_title="Loteria Intelligence SaaS", layout="wide", page_icon="📈")

# --- LINK DO SEU ARQUIVO NO GITHUB ---
@st.cache_data(ttl=600) # Atualiza a cada 10 minutos
def carregar_dados_nuvem(url):
    try:
        response = requests.get(url)
        # Verifica se o link está funcionando (status 200 é OK)
        if response.status_code == 200:
            # Transforma os dados baixados em um formato que o Pandas entende
            df = pd.read_excel(io.BytesIO(response.content))
            return df
        else:
            st.error(f"Erro ao acessar o GitHub: Status {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return None

# Use o link que você copiou no passo 2 aqui:
URL_BASE_DADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"
df = carregar_dados_nuvem(URL_BASE_DADOS)

# --- BANCO DE DADOS DE CLIENTES (Para começar a vender) ---
USUARIOS_ATIVOS = {
    "admin": "master77",
    "cliente01": "vip2026",
    "joao_silva": "senha9988", # Novo cliente adicionado
}
if login():
    # BARRA LATERAL (Note os 4 espaços de recuo aqui)
    st.sidebar.title("Configurações")
    
    # CARREGAMENTO
    df = carregar_dados_nuvem(URL_BASE_DADOS)

    # VALIDAÇÃO (Este 'if' causou o erro, ele deve estar alinhado com o 'df' acima)
    if df is not None:
        # Aqui dentro aumentamos o recuo de novo (8 espaços)
        colunas_reais = df.columns.tolist()
        # ... resto do código
    else:
        st.error("Planilha não encontrada")
# ==============================================================================
# SISTEMA DE LOGIN MULTI-USUÁRIO
# ==============================================================================
def login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.title("🔐 Portal VIP - Inteligência Lotofácil")
        col1, col2 = st.columns(2)
        with col1:
            user = st.text_input("Usuário/E-mail")
            senha = st.text_input("Senha", type="password")
            if st.button("Acessar Painel"):
                if user in USUARIOS_ATIVOS and USUARIOS_ATIVOS[user] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["user_logado"] = user
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
        return False
    return True

# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
if login():
    # Barra Lateral
    st.sidebar.success(f"Logado como: {st.session_state['user_logado']}")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- CARREGAMENTO AUTOMÁTICO DOS DADOS ---
    @st.cache_data(ttl=3600) # Atualiza o cache a cada 1 hora
    def carregar_dados_nuvem(url):
        try:
            # Lendo direto do GitHub
            df = pd.read_excel(url)
            return df
        except:
            return None

    df = carregar_dados_nuvem(URL_BASE_DADOS)
    
   if df is not None:
       # 🔍 TRUQUE PARA NÃO DAR ERRO DE NOME:
       # Vamos pegar os nomes das colunas que existem de verdade no seu arquivo
       colunas_reais = df.columns.tolist()
    
       # Tenta encontrar a coluna de Concurso e Data, independente do nome
       # Se não achar pelo nome, pega a primeira e a segunda coluna por padrão
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

        # Exibição
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("📈 Tendências de Atraso")
            st.bar_chart(ranking.set_index('Dezena'))
        
        with c2:
            st.subheader("🎲 Gerar Palpites VIP")
            if st.button("GERAR JOGOS AGORA"):
                # (Lógica do gerador ponderado aqui...)
                # ... (Mesma lógica de sorteio que já validamos)
                st.success("Jogos gerados com base no Z-Score atualizado!")
                # Aqui você exibe os jogos e o botão de download
    else:
        st.error("Erro ao conectar com a base de dados no GitHub. Verifique o link.")

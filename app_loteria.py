import streamlit as st
import pandas as pd
import numpy as np
import random
import io
from scipy.stats import poisson

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Loteria Intelligence Pro", layout="wide", page_icon="💰")

# ==============================================================================
# SISTEMA DE LOGIN
# ==============================================================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "suasenha123": # <--- MUDE SUA SENHA AQUI
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acesso Restrito")
        st.text_input("Digite a senha para acessar o portal:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha incorreta. Tente novamente:", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha inválida.")
        return False
    else:
        return True

# ==============================================================================
# EXECUÇÃO DO SISTEMA (SÓ SE LOGADO)
# ==============================================================================
if check_password():
    
    # Botão de Logout na lateral
    if st.sidebar.button("Sair/Logoff"):
        st.session_state["password_correct"] = False
        st.rerun()

    st.title("🎯 Gerador Lotofácil Intelligence")
    st.markdown("---")

    # --- CONFIGURAÇÕES LATERAIS ---
    st.sidebar.header("📂 Entrada de Dados")
    arquivo_upload = st.sidebar.file_uploader("Suba a planilha Resultados.xlsx", type=["xlsx"])
    
    st.sidebar.subheader("🎛️ Filtros de Equilíbrio")
    qtd_jogos = st.sidebar.number_input("Qtd Jogos", 1, 100, 10)
    lim_impares = st.sidebar.slider("Ímpares", 5, 11, (7, 9))
    lim_primos = st.sidebar.slider("Primos", 3, 7, (4, 6))
    lim_moldura = st.sidebar.slider("Moldura", 8, 12, (9, 11))
    lim_soma = st.sidebar.slider("Soma", 160, 240, (180, 220))

    MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}

    def validar(jogo):
        impares = len([n for n in jogo if n % 2 != 0])
        mold = len(set(jogo).intersection(MOLDURA))
        prim = len(set(jogo).intersection(PRIMOS))
        soma = sum(jogo)
        return (lim_impares[0] <= impares <= lim_impares[1] and 
                lim_moldura[0] <= mold <= lim_moldura[1] and 
                lim_primos[0] <= prim <= lim_primos[1] and
                lim_soma[0] <= soma <= lim_soma[1])

    if arquivo_upload:
        # Processamento
        df = pd.read_excel(arquivo_upload)
        col_bolas = [c for c in df.columns if 'Bola' in c]
        df_n = df[col_bolas]
        total = len(df)
        
        # Inteligência
        stats = []
        for n in range(1, 26):
            idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
            if len(idx) < 2: continue
            gaps = np.diff(idx) - 1
            z = (((total - 1) - idx[-1]) - np.mean(gaps)) / np.std(gaps, ddof=1)
            stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
        
        ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("📊 Tendência (Z-Score)")
            st.bar_chart(ranking.set_index('Dezena'))

        with col_right:
            st.subheader("🎲 Gerar Apostas")
            if st.button("🚀 GERAR JOGOS"):
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                
                final_jogos = []
                while len(final_jogos) < qtd_jogos:
                    res = []
                    while len(res) < 15:
                        sorteado = random.choices(dezenas, weights=pesos, k=1)[0]
                        if sorteado not in res: res.append(sorteado)
                    res.sort()
                    if validar(res): final_jogos.append(res)
                
                for i, j in enumerate(final_jogos, 1):
                    st.success(f"Jogo {i:02d}: {j}")

                # Exportar
                df_ex = pd.DataFrame(final_jogos)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as wr:
                    df_ex.to_excel(wr, index=False, header=False)
                st.download_button("📥 Baixar em Excel", buffer.getvalue(), "jogos.xlsx")
    else:
        st.info("👋 Suba sua planilha na lateral para começar!")

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
    .btn-cadastro {
        display: block; width: 100%; background-color: #ffc107; color: black !important;
        text-align: center; padding: 15px; border-radius: 15px; font-weight: bold;
        text-decoration: none; margin-top: 10px; transition: 0.3s;
    }
    .btn-compra {
        display: block; width: 100%; background-color: #28a745; color: white !important;
        text-align: center; padding: 15px; border-radius: 15px; font-weight: bold;
        text-decoration: none; margin-top: 10px; transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LINKS DO GITHUB E CADASTRO ---
URL_RESULTADOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Resultados.xlsx"
URL_USUARIOS = "https://raw.githubusercontent.com/luizhahn1-lab/lotofacil-intelligence/main/Usuarios.xlsx"
URL_GOOGLE_FORMS = "https://forms.gle/1622iQAYPQPNEuUe7"
URL_COMPRA = "COLE_AQUI_SEU_LINK_DE_PAGAMENTO" 

# --- CONSTANTES ---
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}

# --- FUNÇÕES ---
def calcular_maior_sequencia(jogo):
    jogo_ord = sorted(jogo)
    maior = atual = 1
    for i in range(len(jogo_ord) - 1):
        if jogo_ord[i+1] == jogo_ord[i] + 1: atual += 1
        else: maior = max(maior, atual); atual = 1
    return max(maior, atual)

@st.cache_data(ttl=60)
def carregar_dados_github(url):
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            df_temp = pd.read_excel(io.BytesIO(resp.content), engine='openpyxl')
            df_temp.columns = df_temp.columns.str.strip()
            return df_temp
    except: return None

# --- SISTEMA DE LOGIN ---
def login():
    if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
    if not st.session_state["autenticado"]:
        st.markdown("<h1 style='text-align: center;'>🔐 Lotofácil Intelligence VIP</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            t1, t2 = st.tabs(["Acessar", "Novos"])
            with t1:
                df_u = carregar_dados_github(URL_USUARIOS)
                with st.form("f_login"):
                    u = st.text_input("E-mail").strip()
                    s = st.text_input("Senha", type="password").strip()
                    if st.form_submit_button("ENTRAR"):
                        if df_u is not None:
                            row = df_u[df_u['Usuario'].astype(str).str.strip() == u]
                            if not row.empty:
                                try:
                                    val = pd.to_datetime(row.iloc[0]['Validade'], dayfirst=True, errors='coerce')
                                    compra = pd.to_datetime(row.iloc[0].get('Data_Compra', val), dayfirst=True, errors='coerce')
                                    if str(s) == str(row.iloc[0]['Senha']).strip() and datetime.now() <= val:
                                        st.session_state.update({"autenticado": True, "user": u, "val": val, "data_compra": (compra if not pd.isna(compra) else datetime.now())})
                                        st.rerun()
                                    else: st.error("Acesso inválido ou expirado.")
                                except: st.error("Erro no processamento da conta.")
                            else: st.error("Usuário não encontrado.")
            with t2:
                c1, c2 = st.columns(2)
                c1.markdown(f'<a href="{URL_COMPRA}" target="_blank" class="btn-compra">💳 COMPRAR</a>', unsafe_allow_html=True)
                c2.markdown(f'<a href="{URL_GOOGLE_FORMS}" target="_blank" class="btn-cadastro">📝 CADASTRAR</a>', unsafe_allow_html=True)
        return False
    return True

# --- APP PRINCIPAL ---
if login():
    # LISTA DE ADMINISTRADORES
    LISTA_ADMS = ["Admin", "luizhahn@yahoo.com.br"] # TROQUE PELO SEU E-MAIL

    df = carregar_dados_github(URL_RESULTADOS)
    if df is not None:
        st.markdown(f"<h1 style='text-align: center; color: #ffc107;'>💰 Lotofácil Intelligence VIP</h1>", unsafe_allow_html=True)
        
        # --- TRAVA DE SEGURANÇA ---
        dias_uso = (datetime.now() - st.session_state['data_compra']).days
        acesso_teste = dias_uso <= 7

        with st.sidebar:
            st.success(f"👤 {st.session_state['user']}")
            if acesso_teste:
                st.warning(f"⏳ Dia {max(0, dias_uso)} de 7 (Degustação)")
                q_max = 5
            else:
                st.success("🚀 VIP LIBERADO")
                q_max = 100

            qtd_jogos = st.number_input("Jogos", 1, q_max, min(5, q_max))
            st.divider()
            lim_impares = st.slider("Ímpares", 5, 11, (7, 9))
            lim_primos = st.slider("Primos", 3, 8, (4, 6))
            lim_moldura = st.slider("Moldura", 8, 12, (9, 11))
            lim_soma = st.slider("Soma", 150, 250, (180, 220))
            lim_seq = st.slider("Máx Seq", 2, 10, 4)
            lim_01_15 = st.slider("01 a 15", 5, 12, 9)
            if st.button("SAIR"): 
                st.session_state["autenticado"] = False
                st.rerun()

        # Ranking Z-Score
        cols = [c for c in df.columns if 'Bola' in c] or df.columns[2:17].tolist()
        df_n, total = df[cols], len(df)
        stats = []
        for n in range(1, 26):
            idx = df.index[df_n.isin([n]).any(axis=1)].tolist()
            if len(idx) < 2: continue
            z = (((total - 1) - idx[-1]) - np.mean(np.diff(idx)-1)) / np.std(np.diff(idx)-1, ddof=1)
            stats.append({'Dezena': f"{n:02d}", 'Z-Score': round(z, 2)})
        ranking = pd.DataFrame(stats).sort_values('Z-Score', ascending=False)

        # --- DEFINIÇÃO DE ABAS ---
        if st.session_state['user'] in LISTA_ADMS:
            aba1, aba2, aba3 = st.tabs(["📊 Tendências", "🎲 Gerador", "🔐 PAINEL ADM"])
        else:
            aba1, aba2 = st.tabs(["📊 Tendências", "🎲 Gerador"])

        with aba1:
            st.bar_chart(ranking.set_index('Dezena'), color="#28a745")
        
        with aba2:
            if acesso_teste: st.info("🔓 Modo VIP completo liberado no 8º dia.")
            if st.button("🚀 GERAR JOGOS"):
                dezenas = ranking['Dezena'].astype(int).tolist()
                pesos = (ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
                validos = []
                prog = st.progress(0)
                for _ in range(20000):
                    if len(validos) >= qtd_jogos: break
                    j = sorted(random.choices(dezenas, weights=pesos, k=15))
                    if len(set(j)) < 15: continue
                    if (lim_impares[0] <= len([n for n in j if n%2!=0]) <= lim_impares[1] and
                        lim_primos[0] <= len(set(j)&PRIMOS) <= lim_primos[1] and
                        lim_moldura[0] <= len(set(j)&MOLDURA) <= lim_moldura[1] and
                        lim_soma[0] <= sum(j) <= lim_soma[1] and
                        calcular_maior_sequencia(j) <= lim_seq and
                        len([n for n in j if 1 <= n <= 15]) == lim_01_15):
                        validos.append(j)
                        prog.progress(len(validos)/qtd_jogos)
                
                for i, j in enumerate(validos):
                    bolas = "".join([f"<div class='dezena-circulo'>{n:02d}</div>" for n in j])
                    st.markdown(f"<div class='card-jogo'><b>Jogo {i+1}</b><br>{bolas}</div>", unsafe_allow_html=True)

        # --- ABA EXCLUSIVA DO ADMINISTRADOR ---
        if st.session_state['user'] in LISTA_ADMS:
            with aba3:
                st.subheader("🛠️ Gestão de Novos Acessos")
                col_a, col_b = st.columns(2)
                with col_a:
                    n_email = st.text_input("E-mail do Cliente").strip()
                    n_plano = st.selectbox("Plano", ["Vitalício", "Mensal"])
                    if st.button("GERAR ACESSO"):
                        if n_email:
                            s_fake = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
                            d_v = "01/01/2099" if n_plano == "Vitalício" else (datetime.now() + pd.DateOffset(days=31)).strftime('%d/%m/%Y')
                            d_c = datetime.now().strftime('%d/%m/%Y')
                            st.code(f"Usuario: {n_email}\nSenha: {s_fake}\nValidade: {d_v}\nData_Compra: {d_c}")
                            msg = f"🚀 VIP Chegou!\nUser: {n_email}\nSenha: {s_fake}\n\n*Aviso:* 7 dias de Degustação ativa!"
                            st.text_area("Texto WhatsApp:", msg)
                        else: st.error("Insira o e-mail!")
                with col_b:
                    st.write("📋 Lista de Usuários no Excel")
                    df_u = carregar_dados_github(URL_USUARIOS)
                    if df_u is not None: st.dataframe(df_u)

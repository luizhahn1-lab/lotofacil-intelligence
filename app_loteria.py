import streamlit as st
import pandas as pd
import numpy as np
import random
from scipy.stats import poisson
import io

# Configurações Visuais do Site
st.set_page_config(page_title="Loteria Intelligence Pro", layout="wide", page_icon="💰")

st.title("🎯 Sistema de Inteligência Lotofácil")
st.markdown("---")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("📂 Configurações de Dados")
arquivo_upload = st.sidebar.file_uploader("Suba o arquivo Resultados.xlsx", type=["xlsx"])

st.sidebar.subheader("🎛️ Ajuste dos Filtros")
qtd_jogos = st.sidebar.number_input("Quantos jogos deseja gerar?", min_value=1, max_value=100, value=10)

# Novos Sliders Dinâmicos
lim_impares = st.sidebar.slider("Quantidade de Ímpares", 5, 11, (7, 9))
lim_moldura = st.sidebar.slider("Quantidade na Moldura", 8, 12, (9, 11))
lim_primos = st.sidebar.slider("Quantidade de Primos", 3, 7, (4, 6)) # <--- NOVO FILTRO
lim_soma = st.sidebar.slider("Faixa de Soma Total", 160, 240, (180, 220))

# Definição dos Grupos de Números
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}

# Função Mestra de Validação (O Funil)
def validar_jogo(jogo):
    impares = len([n for n in jogo if n % 2 != 0])
    moldura = len(set(jogo).intersection(MOLDURA))
    primos = len(set(jogo).intersection(PRIMOS))
    soma = sum(jogo)
    
    # Verifica se o jogo atende a TODOS os critérios selecionados na lateral
    check = (
        lim_impares[0] <= impares <= lim_impares[1] and 
        lim_moldura[0] <= moldura <= lim_moldura[1] and 
        lim_primos[0] <= primos <= lim_primos[1] and
        lim_soma[0] <= soma <= lim_soma[1]
    )
    return check

# --- CORPO DO SISTEMA ---
if arquivo_upload:
    # Processamento dos Dados
    df = pd.read_excel(arquivo_upload)
    colunas_bolas = [col for col in df.columns if 'Bola' in col]
    df_num = df[colunas_bolas]
    total_concursos = len(df)
    
    # Cálculo de Inteligência (Z-Score)
    estatisticas = []
    for n in range(1, 26):
        indices = df.index[df_num.isin([n]).any(axis=1)].tolist()
        if len(indices) < 2: continue
        gaps = np.diff(indices) - 1
        media_gaps = np.mean(gaps)
        desvio_gaps = np.std(gaps, ddof=1)
        atraso_atual = (total_concursos - 1) - indices[-1]
        
        z_score = (atraso_atual - media_gaps) / desvio_gaps if desvio_gaps > 0 else 0
        estatisticas.append({'Dezena': f"{n:02d}", 'Z-Score': round(z_score, 2)})
    
    df_ranking = pd.DataFrame(estatisticas).sort_values('Z-Score', ascending=False)

    # Layout em Colunas
    col_dash, col_gerador = st.columns([1, 1])

    with col_dash:
        st.subheader("📊 Gráfico de Tendências")
        st.bar_chart(df_ranking.set_index('Dezena'))
        st.write("O **Z-Score** mostra o quanto uma dezena está 'atrasada' em relação à média dela. Valores altos (acima de 2.0) são fortes candidatas.")

    with col_gerador:
        st.subheader("🎲 Gerador de Apostas")
        if st.button("🚀 GERAR JOGOS COM FILTROS"):
            # Preparação do Sorteio Ponderado
            dezenas_lista = df_ranking['Dezena'].astype(int).tolist()
            # Damos um peso base de 3 para todos, somado ao Z-Score para priorizar atrasados
            pesos_lista = (df_ranking['Z-Score'] + 3).clip(lower=0.1).tolist()
            
            jogos_aprovados = []
            tentativas_seguranca = 0
            
            while len(jogos_aprovados) < qtd_jogos and tentativas_seguranca < 20000:
                tentativas_seguranca += 1
                
                # Sorteio ponderado
                pool = random.choices(dezenas_lista, weights=pesos_lista, k=40)
                sorteio_unico = sorted(list(set(pool)))[:15]
                
                # Se o sorteio não deu 15 números (por causa do set), completa
                while len(sorteio_unico) < 15:
                    extra = random.choice(dezenas_lista)
                    if extra not in sorteio_unico:
                        sorteio_unico.append(extra)
                sorteio_unico.sort()
                
                # Validação no Funil
                if validar_jogo(sorteio_unico):
                    jogos_aprovados.append(sorteio_unico)
            
            # Exibição dos resultados
            if jogos_aprovados:
                for i, jogo in enumerate(jogos_aprovados, 1):
                    st.success(f"Jogo {i:02d}: {jogo}")
                
                # Botão de Exportação para Excel
                df_export = pd.DataFrame(jogos_aprovados)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, header=False)
                
                st.download_button(
                    label="📥 Baixar Jogos Gerados (Excel)",
                    data=buffer.getvalue(),
                    file_name="jogos_inteligentes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Não foi possível gerar jogos com esses filtros. Tente abrir mais as margens!")

else:
    st.info("👈 Por favor, carregue sua planilha 'Resultados.xlsx' na barra lateral para começar a análise.")
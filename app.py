import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Futebol Local", page_icon="⚽", layout="wide")

# Nome do arquivo que será salvo na pasta do seu computador
ARQUIVO_DADOS = "banco_de_dados_futebol.csv"

# --- FUNÇÕES DE PERSISTÊNCIA ---
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        df = pd.read_csv(ARQUIVO_DADOS)
        # Limpeza para garantir que o pandas leia corretamente
        df.columns = [str(c).strip() for c in df.columns]
        return df
    else:
        # Se o arquivo não existir, cria um novo com as colunas certas
        colunas = ["Quantidade", "Nome", "Telefone", "Data", "Pago", "Comprovante Pix", "Recebeu em Dinheiro", "Cadastro"]
        return pd.DataFrame(columns=colunas)

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

# Inicializa os dados
df = carregar_dados()

# --- INTERFACE MODERNA ---
st.title("⚽ Controle de Futebol (Modo Local)")
st.info(f"💾 Os dados estão sendo salvos em: {os.path.abspath(ARQUIVO_DADOS)}")

# --- CADASTRO (BARRA LATERAL) ---
with st.sidebar:
    st.header("Novo Atleta")
    with st.form("cadastro_form", clear_on_submit=True):
        nome = st.text_input("Nome do Jogador")
        tel = st.text_input("WhatsApp")
        data_j = st.date_input("Data do Jogo", datetime.now())
        
        if st.form_submit_button("✅ Cadastrar"):
            if nome:
                nova_linha = {
                    "Quantidade": len(df) + 1,
                    "Nome": nome,
                    "Telefone": tel,
                    "Data": data_j.strftime("%d/%m/%Y"),
                    "Pago": "Pendente",
                    "Comprovante Pix": "",
                    "Recebeu em Dinheiro": "Não",
                    "Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados(df)
                st.success("Salvo no computador!")
                st.rerun()

# --- GESTÃO DE PAGAMENTOS ---
tab1, tab2 = st.tabs(["⚡ Pendentes de Pagamento", "📋 Lista Geral de Atletas"])

with tab1:
    # Filtra quem ainda não pagou
    df['Pago'] = df['Pago'].fillna("Pendente").astype(str).str.strip()
    pendentes = df[df['Pago'].str.upper() != "SIM"]

    if not pendentes.empty:
        for index, row in pendentes.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.subheader(f"👤 {row['Nome']}")
                
                # Opção Dinheiro
                if c2.button("💵 Recebi Dinheiro", key=f"d_{index}"):
                    df.at[index, "Pago"] = "SIM"
                    df.at[index, "Recebeu em Dinheiro"] = "Sim"
                    salvar_dados(df)
                    st.rerun()
                
                # Opção Pix
                foto = c3.file_uploader("Subir Comprovante Pix", type=['png','jpg','jpeg'], key=f"f_{index}")
                if foto:
                    df.at[index, "Pago"] = "SIM"
                    df.at[index, "Comprovante Pix"] = foto.name
                    salvar_dados(df)
                    st.rerun()
                st.divider()
    else:
        st.success("🎉 Todos os atletas cadastrados estão com o pagamento em dia!")

with tab2:
    st.write("Abaixo estão todos os registros salvos no seu arquivo CSV:")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Botão extra para abrir o arquivo direto no Excel (opcional)
    if st.button("📂 Ver onde o arquivo está salvo"):
        st.write(os.path.abspath(ARQUIVO_DADOS))

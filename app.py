import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Gestão Futebol", layout="centered")

st.title("⚽ Controle de Pagamentos")

# LINK DA SUA PLANILHA
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1VlBmkuH1DVkcE779hKCnCX2kweK0zY41zhPkW9Y_qDQ/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_e_limpar_dados():
    # Lê a planilha
    data = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
    # MENTE DE PROGRAMADOR: Remove espaços vazios antes/depois dos nomes das colunas
    data.columns = data.columns.str.strip()
    return data

def atualizar_planilha(df_para_salvar):
    conn.update(spreadsheet=URL_PLANILHA, data=df_para_salvar)
    st.cache_data.clear()

# Tenta carregar os dados
try:
    df = carregar_e_limpar_dados()
except Exception as e:
    st.error("Erro ao ler a planilha. Verifique se os nomes das colunas na primeira linha do Google Sheets estão corretos.")
    st.stop()

# --- FORMULÁRIO DE CADASTRO ---
with st.expander("📝 Cadastrar Novo Atleta"):
    with st.form("form_atleta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome do Atleta")
        telefone = col2.text_input("Telefone")
        data_jogo = st.date_input("Data", datetime.now())
        
        if st.form_submit_button("Cadastrar Atleta"):
            if nome:
                nova_linha = pd.DataFrame([{
                    "Quantidade": len(df) + 1,
                    "Nome": nome,
                    "Telefone": telefone,
                    "Data": data_jogo.strftime("%d/%m/%Y"),
                    "Pago": "Pendente",
                    "Comprovante Pix": "",
                    "Recebeu em Dinheiro": "Não",
                    "Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
                }])
                df = pd.concat([df, nova_linha], ignore_index=True)
                atualizar_planilha(df)
                st.success(f"✅ {nome} cadastrado!")
                st.rerun()

st.divider()

# --- GESTÃO DE PAGAMENTOS ---
st.subheader("💸 Confirmar Recebimento")

# Verifica se a coluna 'Pago' existe antes de filtrar
if 'Pago' in df.columns:
    # Filtra pendentes (converte para string e remove espaços para evitar novos erros)
    df['Pago'] = df['Pago'].astype(str).str.strip()
    pendentes = df[df['Pago'].str.upper() != "SIM"]

    if not pendentes.empty:
        for index, row in pendentes.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([2, 1.5, 1])
                c1.write(f"**{row['Nome']}**")
                
                foto = c2.file_uploader("Pix", type=['png','jpg','jpeg'], key=f"f_{index}", label_visibility="collapsed")
                
                if c3.button("💵 Dinheiro", key=f"b_{index}"):
                    df.at[index, "Pago"] = "SIM"
                    df.at[index, "Recebeu em Dinheiro"] = "Sim"
                    atualizar_planilha(df)
                    st.rerun()
                
                if foto:
                    df.at[index, "Pago"] = "SIM"
                    df.at[index, "Comprovante Pix"] = foto.name
                    atualizar_planilha(df)
                    st.rerun()
                st.divider()
    else:
        st.info("Nenhum pagamento pendente!")
else:
    st.error("Coluna 'Pago' não encontrada na planilha. Verifique o cabeçalho no Google Sheets.")

# EXIBIR TABELA
with st.expander("📊 Tabela Completa"):
    st.dataframe(df)

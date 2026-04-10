import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestão Futebol", layout="centered")

st.title("⚽ Controle de Pagamentos")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1VlBmkuH1DVkcE779hKCnCX2kweK0zY41zhPkW9Y_qDQ/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_limpos():
    # Lê a planilha completa
    df_raw = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
    
    # MENTE DE PROGRAMADOR: Se a linha 1 for o título decorativo, 
    # vamos pular ela e usar a linha de baixo como cabeçalho
    if "TABELA DE PAGAMENTO" in str(df_raw.columns[0]).upper():
        # Define a primeira linha de dados como novo cabeçalho
        new_header = df_raw.iloc[0] 
        df_raw = df_raw[1:] 
        df_raw.columns = new_header
    
    # Limpa nomes das colunas (remove espaços e garante nomes limpos)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    
    # Remove linhas que estão totalmente vazias
    df_raw = df_raw.dropna(how='all')
    
    return df_raw

try:
    df = carregar_dados_limpos()
    
    # Lista de colunas que o app PRECISA ter
    colunas_obrigatorias = ['Quantidade', 'Nome', 'Telefone', 'Data', 'Pago']
    for col in colunas_obrigatorias:
        if col not in df.columns:
            st.error(f"⚠️ A coluna '{col}' não foi encontrada na linha 1 da planilha.")
            st.info("Dica: Verifique se a linha 1 do Google Sheets começa com 'Quantidade, Nome, Telefone...'")
            st.stop()

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.stop()

# --- FORMULÁRIO ---
with st.expander("📝 Cadastrar Novo Atleta"):
    with st.form("cadastro"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome")
        tel = c2.text_input("Telefone")
        data_j = st.date_input("Data", datetime.now())
        if st.form_submit_button("Salvar"):
            nova_linha = pd.DataFrame([{
                "Quantidade": len(df) + 1,
                "Nome": nome, "Telefone": tel, 
                "Data": data_j.strftime("%d/%m/%Y"),
                "Pago": "Pendente", "comprovante pix": "", 
                "Recebeu em dinheiro": "Não", "Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
            }])
            df_final = pd.concat([df, nova_linha], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, data=df_final)
            st.success("Salvo!")
            st.rerun()

st.divider()

# --- PAGAMENTOS ---
st.subheader("💸 Pendentes")
# Filtro robusto para 'Pago'
df['Pago'] = df['Pago'].fillna("Pendente").astype(str).str.strip()
pendentes = df[df['Pago'].str.upper() != "SIM"]

if not pendentes.empty:
    for index, row in pendentes.iterrows():
        with st.container():
            col_atleta, col_pix, col_cash = st.columns([2, 1.5, 1])
            col_atleta.write(f"**{row['Nome']}**")
            
            foto = col_pix.file_uploader("Pix", type=['png','jpg','jpeg'], key=f"p_{index}", label_visibility="collapsed")
            if col_cash.button("💵 Dinheiro", key=f"d_{index}"):
                df.at[index, "Pago"] = "SIM"
                df.at[index, "Recebeu em dinheiro"] = "Sim"
                conn.update(spreadsheet=URL_PLANILHA, data=df)
                st.rerun()
            
            if foto:
                df.at[index, "Pago"] = "SIM"
                df.at[index, "comprovante pix"] = foto.name
                conn.update(spreadsheet=URL_PLANILHA, data=df)
                st.rerun()
            st.divider()

with st.expander("📊 Ver Tudo"):
    st.dataframe(df)

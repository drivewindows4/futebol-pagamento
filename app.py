import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Gestão Futebol - Pix/Dinheiro", layout="centered")

st.title("⚽ Controle de Atletas")

# 1. LINK DA SUA PLANILHA
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1VlBmkuH1DVkcE779hKCnCX2kweK0zY41zhPkW9Y_qDQ/edit?usp=sharing"

# Estabelecendo conexão
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    # Lê a planilha (garante que não pegue cache antigo)
    return conn.read(spreadsheet=URL_PLANILHA, ttl=0)

def atualizar_planilha(df_atualizado):
    conn.update(spreadsheet=URL_PLANILHA, data=df_atualizado)
    st.cache_data.clear()

# Carregando os dados atuais
df = carregar_dados()

# --- FORMULÁRIO DE CADASTRO ---
with st.expander("📝 Cadastrar Novo Atleta", expanded=True):
    with st.form("form_atleta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome do Atleta")
        telefone = col2.text_input("Telefone")
        data_jogo = st.date_input("Data do Jogo", datetime.now())
        
        btn_cadastrar = st.form_submit_button("Cadastrar Atleta")
        
        if btn_cadastrar:
            if nome:
                # Cria a nova linha com a lógica de "Pendente"
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
                
                df_final = pd.concat([df, nova_linha], ignore_index=True)
                atualizar_planilha(df_final)
                st.success(f"✅ {nome} cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("O nome do atleta é obrigatório.")

st.divider()

# --- GESTÃO DE PAGAMENTOS (Aparece apenas quem não pagou) ---
st.subheader("💸 Confirmar Pagamentos")

# Filtrando quem ainda está pendente
pendentes = df[df['Pago'].str.upper() != "SIM"]

if not pendentes.empty:
    for index, row in pendentes.iterrows():
        with st.container():
            col_info, col_pix, col_cash = st.columns([2, 2, 1])
            
            col_info.write(f"**{row['Nome']}**\n{row['Data']}")
            
            # Botão Pix (Upload de arquivo)
            foto = col_pix.file_uploader("Pix", type=['png', 'jpg', 'jpeg'], key=f"file_{index}", label_visibility="collapsed")
            
            # Botão Recebeu em Dinheiro
            if col_cash.button("💵 Dinheiro", key=f"btn_{index}"):
                df.at[index, "Pago"] = "SIM"
                df.at[index, "Recebeu em Dinheiro"] = "Sim"
                atualizar_planilha(df)
                st.toast(f"Pagamento de {row['Nome']} confirmado!")
                st.rerun()
            
            # Se subir o arquivo, marca como pago automaticamente
            if foto:
                df.at[index, "Pago"] = "SIM"
                df.at[index, "Comprovante Pix"] = f"Recebido: {foto.name}"
                atualizar_planilha(df)
                st.toast(f"Pix de {row['Nome']} registrado!")
                st.rerun()
            st.divider()
else:
    st.info("Nenhum pagamento pendente no momento!")

# --- TABELA COMPLETA ---
with st.expander("📊 Ver Tabela Completa"):
    st.dataframe(df, use_container_width=True)

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Arena Pay - Supabase", page_icon="⚽", layout="wide")

# Credenciais do Supabase (Devem ser configuradas nos Secrets do Streamlit)
# Se estiver testando localmente, substitua pelas suas chaves
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FUNÇÕES DE BANCO DE DADOS ---
def fetch_data():
    response = supabase.table("atletas").select("*").order("id").execute()
    return pd.DataFrame(response.data)

def add_atleta(nome, tel, data):
    df_atual = fetch_data()
    novo_atleta = {
        "quantidade": len(df_atual) + 1,
        "nome": nome,
        "telefone": tel,
        "data_jogo": data.strftime("%d/%m/%Y"),
        "pago": "Pendente",
        "recebeu_dinheiro": "Não"
    }
    supabase.table("atletas").insert(novo_atleta).execute()

def update_pagamento(atleta_id, modo):
    if modo == "dinheiro":
        update = {"pago": "SIM", "recebeu_dinheiro": "Sim"}
    else:
        update = {"pago": "SIM", "comprovante_pix": "Anexado"}
    supabase.table("atletas").update(update).eq("id", atleta_id).execute()

# --- INTERFACE ---
st.title("⚽ Gestão de Atletas (Supabase)")

df = fetch_data()

# Aba lateral para cadastro
with st.sidebar:
    st.header("Novo Cadastro")
    with st.form("form_cadastro", clear_on_submit=True):
        nome = st.text_input("Nome")
        tel = st.text_input("WhatsApp")
        data = st.date_input("Data do Jogo", datetime.now())
        if st.form_submit_button("Cadastrar"):
            if nome:
                add_atleta(nome, tel, data)
                st.success("Cadastrado!")
                st.rerun()

# Listagem de Pendentes
st.subheader("💸 Pendentes")
if not df.empty:
    # Garante que a coluna existe e filtra
    pendentes = df[df['pago'] != "SIM"]
    
    for _, row in pendentes.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{row['nome']}**")
            
            if c2.button("💵 Dinheiro", key=f"d_{row['id']}"):
                update_pagamento(row['id'], "dinheiro")
                st.rerun()
                
            foto = c3.file_uploader("Pix", type=['jpg','png'], key=f"f_{row['id']}", label_visibility="collapsed")
            if foto:
                update_pagamento(row['id'], "pix")
                st.rerun()
            st.divider()
else:
    st.info("Nenhum atleta cadastrado.")

with st.expander("📊 Tabela Completa"):
    st.dataframe(df, use_container_width=True)

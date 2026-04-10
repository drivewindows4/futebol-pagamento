import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Arena Pay - Gestão de Futebol",
    page_icon="⚽",
    layout="wide"
)

# Estilo CSS para deixar a interface moderna
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007bff; color: white; }
    .status-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
URL = "https://docs.google.com/spreadsheets/d/1VlBmkuH1DVkcE779hKCnCX2kweK0zY41zhPkW9Y_qDQ/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # O segredo: header=1 faz o pandas ignorar a linha de título decorativo
    df = conn.read(spreadsheet=URL, ttl=0, header=1)
    df.columns = [str(c).strip() for c in df.columns] # Limpa nomes das colunas
    # Remove linhas vazias e garante que a coluna 'Pago' existe
    df = df.dropna(subset=['Quantidade'], how='all')
    if 'Pago' not in df.columns:
        st.error("Erro Crítico: Coluna 'Pago' não encontrada. Verifique a Linha 2 da Planilha.")
        st.stop()
    return df

try:
    df = get_data()
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    st.stop()

# --- BARRA LATERAL (CADASTRO) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/53/53283.png", width=80)
    st.header("⚽ Painel Administrativo")
    st.divider()
    
    with st.form("novo_atleta", clear_on_submit=True):
        st.subheader("Novo Cadastro")
        nome = st.text_input("Nome do Jogador")
        tel = st.text_input("WhatsApp")
        data_j = st.date_input("Data da Partida", datetime.now())
        
        if st.form_submit_button("✅ CADASTRAR ATLETA"):
            if nome:
                nova_linha = pd.DataFrame([{
                    "Quantidade": len(df) + 1,
                    "Nome": nome,
                    "Telefone": tel,
                    "Data": data_j.strftime("%d/%m/%Y"),
                    "Pago": "Pendente",
                    "comprovante pix": "",
                    "Recebeu em dinheiro": "Não",
                    "Cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
                }])
                df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
                conn.update(spreadsheet=URL, data=df_atualizado)
                st.toast(f"Atleta {nome} adicionado!", icon="🔥")
                st.rerun()

# --- CORPO DO APP ---
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("Gestão de Recebimentos")
with col_t2:
    total_pago = len(df[df['Pago'].astype(str).str.upper() == "SIM"])
    st.metric("Total Pagos", f"{total_pago}/{len(df)}")

tab1, tab2 = st.tabs(["⚡ Pendentes", "📋 Lista Geral"])

with tab1:
    # Limpeza rápida para garantir que o filtro funcione
    df['Pago'] = df['Pago'].fillna("Pendente").astype(str).str.strip()
    pendentes = df[df['Pago'].str.upper() != "SIM"]

    if not pendentes.empty:
        for index, row in pendentes.iterrows():
            with st.container():
                # Design de Card moderno
                st.markdown(f"""<div class="status-card"><b>Atleta:</b> {row['Nome']} | <b>Data:</b> {row['Data']}</div>""", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([2, 1, 1])
                
                foto = c1.file_uploader(f"Anexar Pix de {row['Nome']}", type=['png','jpg'], key=f"p_{index}")
                
                if c2.button("💵 Recebeu Dinheiro", key=f"d_{index}"):
                    df.at[index, "Pago"] = "SIM"
                    df.at[index, "Recebeu em dinheiro"] = "Sim"
                    conn.update(spreadsheet=URL, data=df)
                    st.rerun()
                
                if foto:
                    df.at[index, "Pago"] = "SIM"
                    df.at[index, "comprovante pix"] = foto.name
                    conn.update(spreadsheet=URL, data=df)
                    st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.success("🎉 Parabéns! Todos os atletas pagaram.")

with tab2:
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Pago": st.column_config.TextColumn("Status", help="SIM ou Pendente"),
            "Telefone": st.column_config.LinkColumn("WhatsApp")
        }
    )

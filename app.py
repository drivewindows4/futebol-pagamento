import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
from fpdf import FPDF

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Arena Baba Pro", page_icon="⚽", layout="wide")

# Link da sua planilha (O link que aparece no seu navegador)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1wsraZUP1iT0RGx8vv-7XfhNSSEy9VrExHvjSNm9rn2o/edit?gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê a planilha
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        
        # Se a planilha estiver vazia ou com erro, cria estrutura limpa
        if df.empty:
            return pd.DataFrame(columns=['Nome', 'Pagou', 'Data'])
        
        # --- LIMPEZA DE SEGURANÇA ---
        # Garante as colunas
        for c in ['Nome', 'Pagou', 'Data']:
            if c not in df.columns: df[c] = ""
            
        # Remove linhas onde o Nome está totalmente vazio (evita o erro do print)
        df = df.dropna(subset=['Nome'])
        df = df[df['Nome'].str.strip() != ""]
        
        # Converte Pagou para Booleano real
        df['Pagou'] = df['Pagou'].astype(str).str.upper().map({
            'TRUE': True, '1': True, '1.0': True, 'VERDADEIRO': True,
            'FALSE': False, '0': False, '0.0': False, 'FALSO': False, 'NAN': False
        }).fillna(False).astype(bool)
        
        return df[['Nome', 'Pagou', 'Data']]
    except:
        return pd.DataFrame(columns=['Nome', 'Pagou', 'Data'])

if "dados" not in st.session_state:
    st.session_state.dados = carregar_dados()

# 3. INTERFACE
st.title("⚽ Gestão Arena Baba")

df_atual = st.session_state.dados
c1, c2, c3 = st.columns(3)
c1.metric("👥 Total", len(df_atual))
c2.metric("✅ Pagos", int(df_atual['Pagou'].sum()))
c3.metric("❌ Faltam", len(df_atual) - int(df_atual['Pagou'].sum()))

st.divider()

# 4. EDITOR (Protegido contra células vazias)
st.subheader("📋 Lista de Controle")
df_editado = st.data_editor(
    df_atual,
    column_config={
        "Pagou": st.column_config.CheckboxColumn("Pago?", default=False),
        "Nome": st.column_config.TextColumn("Nome do Atleta"),
        "Data": st.column_config.TextColumn("Data", disabled=True)
    },
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic"
)

# 5. SALVAMENTO
if st.button("💾 Salvar na Nuvem", use_container_width=True):
    # Preenche datas vazias
    hoje = date.today().strftime("%d/%m/%Y")
    df_editado['Data'] = df_editado['Data'].replace("", hoje).fillna(hoje)
    
    # Envia para o Google
    conn.update(spreadsheet=URL_PLANILHA, data=df_editado)
    st.session_state.dados = df_editado
    st.success("✅ Salvo com sucesso!")
    st.rerun()

# 6. PDF
if st.button("📄 Exportar PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"BABA - {date.today().strftime('%d/%m/%Y')}", ln=True, align='C')
    for _, r in df_editado.iterrows():
        status = "PAGO" if r['Pagou'] else "FALTA"
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 10, f"{r['Nome']} - {status}".encode('latin-1', 'ignore').decode('latin-1'), ln=True)
    st.download_button("📥 Baixar PDF", bytes(pdf.output()), "baba.pdf", "application/pdf")

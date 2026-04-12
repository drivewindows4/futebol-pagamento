import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Arena Baba Pro", page_icon="⚽", layout="wide")

# Link da sua planilha (Certifique-se que está como EDITOR)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1wsraZUP1iT0RGx8vv-7XfhNSSEy9VrExHvjSNm9rn2o/edit?usp=sharing"

# 2. CONEXÃO E LIMPEZA DE DADOS
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_e_limpar_dados():
    try:
        # Lê os dados da planilha
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        
        # --- LIMPEZA CRÍTICA PARA EVITAR O ERRO ---
        # 1. Garante que as colunas existam
        for col in ['Nome', 'Pagou', 'Data']:
            if col not in df.columns:
                df[col] = ""
        
        # 2. Converte a coluna Pagou: tudo que não for True vira False (evita erro de tipo)
        df['Pagou'] = df['Pagou'].fillna(False).infer_objects(copy=False)
        df['Pagou'] = df['Pagou'].map({True: True, False: False, 'TRUE': True, 'FALSE': False, '1': True, '0': False}).fillna(False).astype(bool)
        
        # 3. Garante que Nome e Data sejam strings (texto)
        df['Nome'] = df['Nome'].fillna("").astype(str)
        df['Data'] = df['Data'].fillna("").astype(str)
        
        return df[['Nome', 'Pagou', 'Data']] # Retorna apenas as colunas necessárias
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['Nome', 'Pagou', 'Data'])

# Inicialização do Estado
if "dados" not in st.session_state:
    st.session_state.dados = carregar_e_limpar_dados()

# 3. CABEÇALHO E MÉTRICAS
st.title("⚽ Gestão Arena Baba")

df_atual = st.session_state.dados
total = len(df_atual)
pagos = int(df_atual['Pagou'].sum())
inadimplentes = total - pagos

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total Atletas", total)
col2.metric("✅ Pagos", pagos)
col3.metric("❌ Inadimplentes", inadimplentes)

st.divider()

# 4. EDITOR DE TABELA (AQUI MORA O ERRO)
st.subheader("📋 Lista de Presença")

# Usamos uma cópia limpa para o editor
df_para_editar = df_atual.copy()

df_editado = st.data_editor(
    df_para_editar,
    column_config={
        "Pagou": st.column_config.CheckboxColumn("Pago?", width="small", default=False),
        "Nome": st.column_config.TextColumn("Nome do Atleta", required=True),
        "Data": st.column_config.TextColumn("Data de Cadastro", disabled=True)
    },
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic" # Permite adicionar/remover
)

# 5. SALVAMENTO
if st.button("💾 Gravar Alterações na Nuvem", use_container_width=True):
    try:
        # Preenche a data para quem não tem (novos jogadores)
        hoje = date.today().strftime("%d/%m/%Y")
        df_editado['Data'] = df_editado['Data'].replace("", hoje).replace("nan", hoje)
        df_editado['Data'] = df_editado['Data'].fillna(hoje)
        
        # Atualiza no Google Sheets
        conn.update(spreadsheet=URL_PLANILHA, data=df_editado)
        st.session_state.dados = df_editado
        st.success("✅ Dados sincronizados com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# 6. EXPORTAR PDF
if st.button("📄 Gerar PDF para WhatsApp"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"LISTA BABA - {date.today().strftime('%d/%m/%Y')}", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 10, "DATA", 1)
    pdf.cell(90, 10, "NOME", 1)
    pdf.cell(60, 10, "STATUS", 1, 1)
    
    pdf.set_font("Helvetica", "", 10)
    for _, row in df_editado.iterrows():
        status = "PAGO" if row['Pagou'] else "FALTA"
        nome = str(row['Nome']).encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(40, 10, str(row['Data']), 1)
        pdf.cell(90, 10, nome, 1)
        pdf.cell(60, 10, status, 1, 1)
    
    pdf_bytes = bytes(pdf.output())
    st.download_button("📥 Baixar PDF", pdf_bytes, "baba.pdf", "application/pdf")

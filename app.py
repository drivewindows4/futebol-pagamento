import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Arena Baba Pro", page_icon="⚽", layout="wide")

# Link da sua planilha (Substitua pelo seu link real)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1wsraZUP1iT0RGx8vv-7XfhNSSEy9VrExHvjSNm9rn2o/edit?usp=sharing"

# 2. CONEXÃO E TRATAMENTO DE DADOS
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, ttl=0)
        # TRATAMENTO CRÍTICO: Garante que a coluna Pagou seja booleana para o Checkbox
        if 'Pagou' in df.columns:
            df['Pagou'] = df['Pagou'].astype(bool)
        else:
            df['Pagou'] = False
        return df
    except Exception:
        # Se a planilha estiver vazia, cria estrutura padrão
        return pd.DataFrame(columns=['Nome', 'Pagou', 'Data'])

# Inicialização do Estado
if "dados" not in st.session_state:
    st.session_state.dados = carregar_dados()

# 3. CABEÇALHO E MÉTRICAS
st.title("⚽ Gestão Arena Baba")

df_atual = st.session_state.dados
total = len(df_atual)
pagos = df_atual['Pagou'].sum()
inadimplentes = total - pagos

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total Atletas", total)
col2.metric("✅ Pagos", pagos)
col3.metric("❌ Inadimplentes", inadimplentes)

st.divider()

# 4. EDITOR DE TABELA (ADICIONAR/REMOVER/MARCAR)
st.subheader("📋 Lista de Presença")
st.caption("Dica: Use a última linha vazia para adicionar nomes. Para excluir, selecione a linha e aperte 'Delete'.")

df_editado = st.data_editor(
    df_atual,
    column_config={
        "Pagou": st.column_config.CheckboxColumn("Pago?", width="small"),
        "Nome": st.column_config.TextColumn("Nome do Atleta"),
        "Data": st.column_config.TextColumn("Data de Cadastro", disabled=True)
    },
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic" # Habilita o (+) para novos atletas
)

# 5. SALVAMENTO E SINCRONIZAÇÃO
if st.button("💾 Gravar Alterações na Nuvem", use_container_width=True):
    try:
        # Preenche datas vazias de novos atletas
        if 'Data' in df_editado.columns:
            df_editado['Data'] = df_editado['Data'].fillna(date.today().strftime("%d/%m/%Y"))
        
        # Atualiza o Google Sheets
        conn.update(spreadsheet=URL_PLANILHA, data=df_editado)
        st.session_state.dados = df_editado
        st.success("✅ Sincronizado com o Google Sheets!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# 6. EXPORTAÇÃO E EXTRAS
st.divider()
c_pdf, c_refresh = st.columns(2)

with c_pdf:
    if st.button("📄 Gerar PDF para WhatsApp", use_container_width=True):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, f"LISTA BABA - {date.today().strftime('%d/%m/%Y')}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(40, 10, "DATA", 1)
            pdf.cell(90, 10, "NOME", 1)
            pdf.cell(60, 10, "STATUS", 1, 1)
            
            pdf.set_font("Helvetica", "", 12)
            for _, row in df_editado.iterrows():
                status = "PAGO" if row['Pagou'] else "FALTA"
                nome = str(row['Nome']).encode('latin-1', 'ignore').decode('latin-1')
                pdf.cell(40, 10, str(row['Data']), 1)
                pdf.cell(90, 10, nome, 1)
                pdf.cell(60, 10, status, 1, 1)
            
            pdf_bytes = bytes(pdf.output())
            st.download_button("📥 Baixar PDF Agora", pdf_bytes, "baba.pdf", "application/pdf")
        except Exception as e:
            st.error("Erro ao gerar PDF. Verifique se há caracteres especiais.")

with c_refresh:
    if st.button("🔄 Atualizar Página", use_container_width=True):
        st.session_state.dados = carregar_dados()
        st.rerun()

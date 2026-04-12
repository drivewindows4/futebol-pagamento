import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Arena Baba Pro", page_icon="⚽", layout="wide")

# 2. INICIALIZAÇÃO DOS DADOS (Com todos os seus jogadores)
if 'lista_baba' not in st.session_state:
    dados_iniciais = [
        ["Rogério", True], ["Djavan", True], ["Fabrício", True], ["Robson", False],
        ["Daniel", True], ["cosme", True], ["Mendel", True], ["Raylan", True],
        ["caçulo", False], ["Sivaldo", True], ["carleilton", True], ["jai", True],
        ["modesto", False], ["Jeferson", True], ["João da Cruz", False],
        ["João Paulo", False], ["Dinho", True], ["Rodrigo", False], ["maciel", True],
        ["Cleverson", False], ["Leo", False], ["Eduardo bigode", False], ["Micael", False]
    ]
    df_init = pd.DataFrame(dados_iniciais, columns=['Nome', 'Pagou'])
    df_init['Data'] = date.today().strftime("%d/%m/%Y")
    st.session_state.lista_baba = df_init

# --- FUNÇÃO PARA GERAR O PDF (CORRIGIDA) ---
def gerar_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"RELATORIO BABA - {date.today().strftime('%d/%m/%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(40, 10, "DATA", 1, 0, 'C', True)
    pdf.cell(90, 10, "NOME", 1, 0, 'C', True)
    pdf.cell(60, 10, "STATUS", 1, 1, 'C', True)
    
    # Linhas dos Jogadores
    pdf.set_font("Helvetica", "", 12)
    for i, row in dataframe.iterrows():
        status = "PAGO" if row['Pagou'] else "FALTA"
        # Limpeza de acentos para evitar erro no PDF
        nome_limpo = str(row['Nome']).encode('latin-1', 'ignore').decode('latin-1')
        
        pdf.cell(40, 10, str(row['Data']), 1)
        pdf.cell(90, 10, nome_limpo, 1)
        pdf.cell(60, 10, status, 1, 1, 'C')
        
    return bytes(pdf.output())

# 3. BARRA LATERAL (GESTÃO)
with st.sidebar:
    st.header("⚙️ Gestão de Atletas")
    
    # Adicionar novo atleta
    with st.expander("➕ Adicionar Atleta"):
        novo_nome = st.text_input("Nome do Jogador")
        if st.button("Confirmar Cadastro"):
            if novo_nome:
                nova_linha = pd.DataFrame([[novo_nome, False, date.today().strftime("%d/%m/%Y")]], 
                                         columns=['Nome', 'Pagou', 'Data'])
                st.session_state.lista_baba = pd.concat([st.session_state.lista_baba, nova_linha], ignore_index=True)
                st.rerun()
    
    # Excluir atleta
    with st.expander("🗑️ Excluir Atleta"):
        nomes_atuais = st.session_state.lista_baba['Nome'].tolist()
        atleta_remover = st.selectbox("Escolha quem remover:", nomes_atuais)
        if st.button("Remover Permanentemente"):
            st.session_state.lista_baba = st.session_state.lista_baba[st.session_state.lista_baba['Nome'] != atleta_remover]
            st.rerun()

# 4. PAINEL PRINCIPAL
st.title("⚽ Controle de Pagamentos - Arena Baba")

# Métricas no Topo
df_atual = st.session_state.lista_baba
total = len(df_atual)
pagos = int(df_atual['Pagou'].sum())
faltam = total - pagos

c1, c2, c3 = st.columns(3)
c1.metric("👥 Total Atletas", total)
c2.metric("✅ Confirmados", pagos)
c3.metric("❌ Pendentes", faltam)

st.divider()

# Tabela Interativa
st.subheader("📋 Lista de Presença")
df_editado = st.data_editor(
    df_atual,
    column_config={
        "Pagou": st.column_config.CheckboxColumn("Pago?", width="small"),
        "Nome": st.column_config.TextColumn("Nome do Atleta"),
        "Data": st.column_config.TextColumn("Data", disabled=True)
    },
    hide_index=True,
    use_container_width=True
)
st.session_state.lista_baba = df_editado

st.divider()

# 5. BOTÃO DE DOWNLOAD PDF
st.subheader("📥 Exportar Relatório")

# Gerar os bytes do PDF
try:
    pdf_output = gerar_pdf(df_editado)
    
    st.download_button(
        label="📄 Baixar Lista em PDF (Para WhatsApp)",
        data=pdf_output,
        file_name=f"lista_baba_{date.today()}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
except Exception as e:
    st.error(f"Erro ao gerar o arquivo PDF: {e}")

st.info("💡 **Dica:** Após baixar o PDF no telemóvel, pode partilhá-lo diretamente no grupo do Baba!")

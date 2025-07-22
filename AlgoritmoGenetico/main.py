from algoritmo_genetico import algoritmo_genetico
from carregar_dados import carregar_dados
from common import st, px, pd, io, mp, ceil

# Evita bugs no paralelismo.
mp.set_start_method("spawn", force=True)

st.set_page_config(page_title="Distribuição Logística", layout="wide")
st.title("\U0001F4E6 Otimização de Distribuição de Produtos")

# Sidebar
with st.sidebar:
    st.header("⚙️ Parâmetros do Algoritmo Genético")
    tamanho_populacao = st.slider("Tamanho da População", 10, 200, 100, step=10)
    st.caption("**Tamanho da População**: número de possíveis soluções avaliadas a cada geração (quanto maior, mais variações testadas).")
    num_geracoes = st.slider("Número de Gerações", 10, 500, 200, step=10)
    st.caption("**Número de Gerações**: número de ciclos de evolução (mais gerações podem melhorar o resultado, mas aumentam o tempo de processamento).")
    taxa_mutacao = st.slider("Taxa de Mutação (%)", 0, 100, 50, step=1) / 100
    st.caption("**Taxa de Mutação**: chance de mudar aleatoriamente uma solução (ajuda a evitar que o algoritmo fique preso em soluções ruins).")
    
    st.markdown("---")

    st.header("\U0001F4C2 Upload dos Arquivos (opcional)")
    estoque_cd = st.file_uploader("Estoque CD", type="csv")
    capacidade_lojas = st.file_uploader("Capacidade das Lojas", type="csv")
    demanda = st.file_uploader("Demanda Semanal", type="csv")
    custos = st.file_uploader("Custo por Caminhão", type="csv")

DEFAULT_PATHS = {
    "estoque_cd": "archives/estoque_cd.csv",
    "capacidade_lojas": "archives/capacidade_lojas.csv",
    "demanda": "archives/demanda.csv",
    "custos": "archives/custo_por_caminhao.csv"
}

df_estoque, df_capacidade, df_demanda, df_custos, df_capacidade_raw = carregar_dados(
    estoque_cd if estoque_cd else DEFAULT_PATHS["estoque_cd"],
    capacidade_lojas if capacidade_lojas else DEFAULT_PATHS["capacidade_lojas"],
    demanda if demanda else DEFAULT_PATHS["demanda"],
    custos if custos else DEFAULT_PATHS["custos"]
)

# Memória temporária para persistência dos dados na hora de baixar o excel.
if "resultado" not in st.session_state:
    st.session_state.resultado = None
    st.session_state.custo_total = 0
    st.session_state.df_detalhes_custo = None

if st.button("\U0001F69B Executar Algoritmo Genético"):
    with st.spinner("Executando algoritmo genético..."):
        resultado, custo_total = algoritmo_genetico(
            df_estoque, df_capacidade, df_demanda, df_custos,
            tamanho_populacao=tamanho_populacao,
            num_geracoes=num_geracoes,
            taxa_mutacao=taxa_mutacao
        )
        
    st.session_state.resultado = resultado
    st.session_state.custo_total = custo_total
    
# Faz a verificação se a persistência está vazia (erro).
if st.session_state.resultado is not None:
    resultado = st.session_state.resultado
    custo_total = st.session_state.custo_total

    st.success("Otimização concluída!")

    # Cria uma lista sem os nomes: "Enviado_", "Completo_", "Produtos".
    colunas_envio = [col for col in resultado.columns if not col.startswith("Enviado_") and not col.startswith("Completo_") and col != "Produto"]
    # Cria uma lista com colunas que começam com "Enviado_" ou "Completo_".
    colunas_status = [col for col in resultado.columns if col.startswith("Enviado_") or col.startswith("Completo_")]

    # Tabela 1
    st.markdown("---")
    st.markdown("### 📦 Distribuição de Produtos")
    st.dataframe(resultado[["Produto"] + colunas_envio], use_container_width=True)
    st.caption("""
      A tabela mostra quantas unidades de cada produto foram enviadas para cada loja, sempre em múltiplos de 20 (uma caixa).  
      O envio considera a **demanda semanal da loja**, o **limite de armazenamento** e o **estoque disponível no centro de distribuição**.  
      Quando a demanda não é múltipla de 20, o valor pode ser arredondado para cima, desde que **não ultrapasse a capacidade da loja**.
    """)

    # Tabela 2
    st.markdown("---")
    st.markdown("### 🟢 Status de Entrega (Enviado e Completo)")
    st.dataframe(resultado[["Produto"] + colunas_status], use_container_width=True)
    st.caption("""
    - **Colunas `Enviado_<Loja>`**: Indica se o produto **foi enviado** para essa loja (`sim` ou `não`).
    - **Colunas `Completo_<Loja>`**: Indica se a **demanda total que o mercado quer do produto foi atendida** (`sim` ou `não`).
    - Os produtos são enviados **apenas em caixas de 20 unidades**.
    """)

    # Tabela 3
    st.markdown("---")
    st.markdown("### 🚛 Custos Logísticos por Loja")
    custo_total_final = 0
    dados_custo_loja = []
    for loja in colunas_envio:
        total_unidades = resultado[loja].sum()
        caixas = total_unidades // 20
        viagens = ceil(caixas / 50)
        custo_viagem = float(df_custos.loc[df_custos["Loja"] == loja, "CustoPorCaminhao"].values[0])
        custo_total_loja = viagens * custo_viagem
        custo_total_final = custo_total_final + custo_total_loja
        capacidade = int(df_capacidade_raw.loc[df_capacidade_raw["Loja"] == loja, "Capacidade"].values[0])


        dados_custo_loja.append({
            "Loja": loja,
            "Total de Unidades": total_unidades,
            "Capacidade": capacidade,
            "Caixas (20 unid)": caixas,
            "Nº de Viagens": viagens,
            "Custo por Viagem (R$)": custo_viagem,
            "Custo Total (R$)": custo_total_loja
        })

    df_detalhes_custo = pd.DataFrame(dados_custo_loja)
    st.dataframe(df_detalhes_custo, use_container_width=True)
    st.caption("""
      A tabela apresenta os custos de transporte por loja, incluindo o **total de unidades entregues**, **número de caixas** (20 unidades cada),  
      **número de viagens necessárias**, **custo por viagem** e o **custo total**.  
      Esses dados permitem avaliar **quais lojas geram maior gasto logístico** e **onde há oportunidades de otimização**.
    """)

    # Gráfico de custo por lojas.
    st.markdown("---")
    st.markdown("### \U0001F4B8 Custo Total por Loja")
    fig = px.bar(df_detalhes_custo, x="Loja", y="Custo Total (R$)", text_auto=".2s")
    st.plotly_chart(fig)

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        resultado[["Produto"] + colunas_envio].to_excel(writer, index=False, sheet_name="Distribuicao")
        resultado[["Produto"] + colunas_status].to_excel(writer, index=False, sheet_name="Status")
        df_detalhes_custo.to_excel(writer, index=False, sheet_name="Custos")
    excel_buffer.seek(0)
        
    st.success(f"### \U0001F4B0 Custo total: R$ {custo_total_final:,.2f}")

    # Adicionado colunas com os botões para ficar um ao lado do outro.
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📥 Baixar Resultado como Excel",
            data=excel_buffer.getvalue(),
            file_name="resultado_distribuicao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col2:
        if st.button("🔙 Voltar", use_container_width=True):
            st.session_state.resultado = None
            st.session_state.custo_total = 0
            st.session_state.df_detalhes_custo = None
            st.rerun()
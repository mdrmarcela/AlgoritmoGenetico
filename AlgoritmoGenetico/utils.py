CAPACIDADE_CAMINHAO = 1000
CAIXA_UNIDADES = 20

def normalizar_colunas(*dataframes):
    """
    Remove espaços dos nomes das colunas dos DataFrames.
    """
    for df in dataframes:
        df.columns = df.columns.str.strip()

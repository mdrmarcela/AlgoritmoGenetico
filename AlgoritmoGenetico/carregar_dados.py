from common import pd
from utils import normalizar_colunas

def carregar_dados(estoque_file, capacidade_file, demanda_file, custos_file):
    df_estoque = pd.read_csv(estoque_file)
    df_capacidade_raw = pd.read_csv(capacidade_file)
    df_demanda = pd.read_csv(demanda_file)
    df_custos = pd.read_csv(custos_file)

    normalizar_colunas(df_estoque, df_capacidade_raw, df_demanda, df_custos)

    lojas = df_capacidade_raw['Loja']
    capacidades = df_capacidade_raw['Capacidade']
    df_capacidade = pd.DataFrame([capacidades.values] * df_demanda.shape[0], columns=lojas)

    return df_estoque, df_capacidade, df_demanda.iloc[:, 1:], df_custos, df_capacidade_raw

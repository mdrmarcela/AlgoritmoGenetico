# AlgoritmoGenetico

Uma rede de supermercados possui um centro de distribuição (CD) onde são recebidos e ficam armazenados todos os produtos comprados por ela. Esta rede busca distribuir as mercadorias entre suas filiais visando evitar excesso de estoque em algumas unidades e falta em outras. A distribuição deve ser otimizada para minimizar custos logísticos e garantir que cada loja tenha produtos suficientes para atender à demanda prevista.

A rede de supermercado possui 10 filiais diferentes.
A rede de supermercados vende 50 produtos diferentes.
A quantidade de unidades em estoque no CD de cada produto está disponível no arquivo estoque_cd.csv.
A quantidade de unidades máxima que cada loja pode ter em estoque, considerando o seu espaço físico, está disponível em capacidade_lojas.csv.
O custo em reais para realizar uma viagem de caminhão entre o CD e uma loja está definido em custo_por_caminhao.csv.
A demanda semanal de unidades de cada produto, em cada uma das lojas, está especificada em demanda.csv.
Em cada viagem, um caminhão pode levar 1000 unidades independente do tipo do produto transportado.
Os produtos são alocados em caixas com 20 unidades cada e não podem ser abertas no CD, ou seja, a quantidade de unidades transportada deve ser sempre múltiplo de 20.
Resumão:

Há 50 tipos de produtos. Cada produto está dividido em caixas com 20 unidades.
Essa viagem vai ser feita semanalmente, juntamente com a demanda semanal de cada supermercado.
A capacidade do caminhão por viagem é 1000 unidades, ou seja, 50 caixas por viagem.
O caminhão faz somente a viagem para um supermercado por vez. Leva tudo que o supermercado precisa, caso a demanda do supermercado não for múltiplo de 20 (por causa da caixa), o caminhão, se o supermercado tiver capacidade, leva uma caixa a mais (faz isso somente se: o caminhão não precisar fazer a viagem novamente para aquele mercado por causa de 1 caixa).
Se faltar capacidade no supermercado para alguns tipos de produto, vai faltar mesmo, não tem o que fazer (avisar que faltou ou colocar 0 no produto enviado e colocar na variável enviado: não/sim), ou, também, se caso o produto não for com todas as unidades da demanda, deve avisar (completo: não/sim).
Se quiser, pode-se decidir haver mais caminhões, mas tem que ver se não vai custar de mais, se, por exemplo, faltar uma caixa em algum supermercado, não deve usar outro caminhão só por isso.
Caso a capacidade de cada mercado seja atingida em alguma semana, faltando alguns tipos de produto, deve-se priorizar esses tipos e quantidades faltantes na próxima semana.
O Algoritmo Genético deve realizar a programação das viagens a serem realizadas na semana para distribuir os produtos entre as lojas, de forma a minimizar custos logísticos, evitar rupturas de estoque (falta de produtos nas lojas) e excesso de mercadorias (para não gerar desperdício ou necessidade de promoções para liquidação).

Para rodar o projeto, digite no terminal:

streamlit run main.py
Para baixas as dependências do projeto, digite no terminal:

pip install -r requirements.txt

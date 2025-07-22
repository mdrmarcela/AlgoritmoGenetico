from common import np, random, pd, cf, time, os
from utils import CAPACIDADE_CAMINHAO, CAIXA_UNIDADES

# =========================
# 1. ALGORITMO GENÉTICO
# =========================

def algoritmo_genetico(df_estoque, df_capacidade, df_demanda, df_custos, tamanho_populacao, num_geracoes, taxa_mutacao):
    
    # Consegue o número de linhas do df_estoque.csv
    n_produtos = df_estoque.shape[0]
    
    # Consegue o número de colunas do df_capacidade.csv
    n_lojas = df_capacidade.shape[1]

    # Converte a coluna EstoqueDisponivel em array.
    estoque_cd = df_estoque['EstoqueDisponivel'].to_numpy()
    capacidade_lojas = df_capacidade
    demanda = df_demanda
    custo_caminhao = df_custos['CustoPorCaminhao'].to_numpy()

    populacao = inicializar_populacao(tamanho_populacao, n_produtos, n_lojas)

    # Escolhe o melhor executor para o paralelismo
    _, melhor_executor = benchmark_executor(populacao[:10], estoque_cd, capacidade_lojas, demanda, custo_caminhao)

    # Início do ciclo evolutivo do algoritmo genético.
    for i in range(num_geracoes):
        print(f"[GERAÇÃO {i+1}] Início")
        inicio = time.time()
        avaliacoes = fitness_paralela(populacao, estoque_cd, capacidade_lojas, demanda, custo_caminhao, melhor_executor)
        fim = time.time()
        print(f"[GERAÇÃO {i+1}] Tempo: {fim - inicio:.2f}s")
        
        num_filhos = calc_num_filhos(tamanho_populacao, taxa_mutacao, num_geracoes)
        
        # Percorre todos os elementos da lista avaliacoes e extrai apenas o valor de índice 0.
        aptidoes = [av[0] for av in avaliacoes]
        nova_populacao = []
        while len(nova_populacao) < tamanho_populacao:
            pai1 = selecao(populacao, aptidoes)
            pai2 = selecao(populacao, aptidoes)
            
            # Faz um while para que os pais não sejam os mesmos, evitando filhos redundantes no crossover
            while np.array_equal(pai2, pai1):
                pai2 = selecao(populacao, aptidoes)
                
            # Itera até a quantidades de filhos calculada
            for _ in range(num_filhos):
                filho = crossover(pai1, pai2)
                filho = mutacao(filho, taxa_mutacao)
            
                #  Criação da população da próxima geração.
                nova_populacao.append(filho)
                if len(nova_populacao) >= tamanho_populacao:
                    break
                
        populacao = nova_populacao
        print(f"[GERAÇÃO {i+1}] Fim\n")

    # Identificar o índice do melhor indivíduo (valor mínimo) em uma população com base nas suas aptidões (fitness).
    melhor_index = np.argmin(aptidoes)
    melhor_custo, melhor_solucao, enviado, completo = avaliacoes[melhor_index]

    resultado = pd.DataFrame(melhor_solucao, columns=df_demanda.columns)
    # Adiciona uma nova coluna chamada "Produto" com os valores de df_estoque['Produto'].
    resultado.insert(0, "Produto", df_estoque['Produto'])

    for loja in df_demanda.columns:
        # Retorna o índice da coluna correspondente à loja.
        idx = df_demanda.columns.get_loc(loja)
        resultado[f"Enviado_{loja}"] = enviado[:, idx]
        resultado[f"Completo_{loja}"] = completo[:, idx]

    return resultado, melhor_custo

def gerar_individuo(n_produtos, n_lojas):
    # Gera uma matriz aleatória com n_produtos linhas e n_lojas colunas, setado com 0-49 número * 20.
    return np.random.randint(0, 50, size=(n_produtos, n_lojas)) * CAIXA_UNIDADES

def inicializar_populacao(tamanho_populacao, n_produtos, n_lojas):
    # Gera uma lista com tamanho_populacao indivíduos.
    return [gerar_individuo(n_produtos, n_lojas) for _ in range(tamanho_populacao)]

def selecao(populacao, aptidoes):
    # Seleciona aleatoriamente 10 indivíduos da população, considerando tanto o indivíduo quanto sua aptidão.
    selecionados = random.choices(list(zip(populacao, aptidoes)), k=10)
    # Retorna o indivíduo com a menor aptidão entre os selecionados.
    return min(selecionados, key=lambda x: x[1])[0]

# Crossover híbrido, decide entre uniforme e por linha
def crossover(pai1, pai2):
    filho = np.zeros_like(pai1)
    
    # Cálculo da diversidade entre os pais
    diversidade = hamming(pai1, pai2)

    # Cálculo da taxa de variação para definir entre uniforme ou por linha
    taxa_uniforme = calc_taxa_uniforme(diversidade)
    
    for i in range(pai1.shape[0]):  # produto
        if random.random() < taxa_uniforme:
            # Crossover uniforme (gene a gene)
            for j in range(pai1.shape[1]):
                filho[i, j] = pai1[i, j] if random.random() < 0.5 else pai2[i, j]
        else:
            # Crossover por linha
            filho[i] = pai1[i] if random.random() < 0.5 else pai2[i]

    return filho

def mutacao(individuo, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i = random.randint(0, individuo.shape[0] - 1)
        j = random.randint(0, individuo.shape[1] - 1)
        individuo[i, j] += random.choice([-CAIXA_UNIDADES, CAIXA_UNIDADES])
        individuo[i, j] = max(0, individuo[i, j])
    return individuo


def fitness_paralela(populacao, estoque_cd, capacidade_lojas, demanda, custo_caminhao, executor_cls):
    print("\n[INFO] Iniciando fitness_paralela...")
    cap_lojas_np = capacidade_lojas.to_numpy()
    demanda_np = demanda.to_numpy()
    
    # Cria uma lista de tuplas com todos os argumentos necessários para calcular o fitness de cada indivíduo.
    args = [(ind, estoque_cd, cap_lojas_np, demanda_np, custo_caminhao) for ind in populacao]
    
    # Cria um executor com um número de workers igual ao número de núcleos da CPU.
    with executor_cls(max_workers=os.cpu_count()) as executor:
        print(f"[INFO] Executor usado: {executor_cls.__name__}")
        
        # Aplicar a função calcular_aptidao_parallel em paralelo para todos os indivíduos da população.
        resultados = list(executor.map(calcular_aptidao_parallel, args))
    print("[INFO] Finalizou execução paralela!\n")
    return resultados

def calcular_aptidao_parallel(args):
    # Desempacota a tupla.
    individuo, estoque_cd, capacidade_lojas, demanda, custo_caminhao = args
    return calcular_aptidao(individuo, estoque_cd, capacidade_lojas, demanda, custo_caminhao)

def calcular_aptidao(individuo, estoque_cd, capacidade_lojas, demanda, custo_caminhao):
    custo_total = 0
    penalidade = 0
    # Cria uma matriz com o mesmo formato do individuo, preenchida com a string "sim".
    completo = np.full(individuo.shape, "sim", dtype=object)
    enviado = np.full(individuo.shape, "sim", dtype=object)
    # Cria uma matriz com o mesmo formato do individuo, preenchida com zeros.
    individuo_final = np.zeros_like(individuo)

    # Extrai a capacidade das lojas.
    capacidade_total_lojas = capacidade_lojas[0]

    # for em loja até número de colunas da matriz individuo.
    for loja in range(individuo.shape[1]):
        carga_total = 0
        capacidade_restante = capacidade_total_lojas[loja]

        # for em produtos da loja até número de colunas da matriz individuo.
        for prod in range(individuo.shape[0]):
            demanda_loja = demanda[prod, loja]
            
            # Pula a iteração desse produto se a demanda for zero.
            if demanda_loja == 0:
                continue

            # Verifica quantas caixas são em comparação com a demanda arredondando.
            caixas = int(np.floor(demanda_loja / CAIXA_UNIDADES))
            sobra = demanda_loja % CAIXA_UNIDADES
            unidades_enviar = caixas * CAIXA_UNIDADES

            # Enviar uma caixa extra se sobra > 0 e ainda houver capacidade
            if sobra > 0 and unidades_enviar + CAIXA_UNIDADES <= demanda_loja + CAIXA_UNIDADES:
                unidades_enviar += CAIXA_UNIDADES

            # Verifica se ainda cabe na loja
            if carga_total + unidades_enviar > capacidade_restante:
                # Tenta enviar menos se a capacidade já estiver quase cheia
                maximo_enviar = capacidade_restante - carga_total
                # Verifica a quantidade de produtos que se pode enviar.
                maximo_enviar = (maximo_enviar // CAIXA_UNIDADES) * CAIXA_UNIDADES
                unidades_enviar = maximo_enviar

            # Faz a regra de penalidade caso as unidades_enviar sejam menor ou igual a 0.
            # Demanda indisponível no estoque ou Demanda inválida.
            if unidades_enviar <= 0:
                enviado[prod, loja] = "não"
                completo[prod, loja] = "não"
                penalidade += 50
                continue

            # Atualiza a matriz individuo_final preenchida com o valor de unidades_enviar para aquela loja e produto específicos.
            individuo_final[prod, loja] = unidades_enviar
            carga_total += unidades_enviar

            # Faz a regra de penalidade caso as unidades do produto for menor que a demanda pedida da loja.
            if unidades_enviar < demanda_loja:
                completo[prod, loja] = "não"
                penalidade += 30 * (demanda_loja - unidades_enviar)

        # Calcula a quantidade de viagens que será feita para aquela loja e produto específicos.
        viagens = np.ceil(carga_total / CAPACIDADE_CAMINHAO)
        
        # Custo total de todas as viagens.
        custo_total += viagens * custo_caminhao[loja]

    # Soma as quantidades enviadas de produtos para as lojas do CD.
    total_envio_cd = np.sum(individuo_final, axis=1)
    
    # Verifica se excedeu o estoque do CD de cada produto, se sim, add uma penalidade.
    excesso = np.maximum(total_envio_cd - estoque_cd, 0)
    penalidade += np.sum(excesso) * 100

    return custo_total + penalidade, individuo_final, enviado, completo


# =========================
# 4. BENCHMARKS E UTILITÁRIOS
# =========================

def fitness_com_tempo(populacao, estoque_cd, capacidade_lojas, demanda, custo_caminhao, executor_cls):
    inicio = time.time()
    resultado = fitness_paralela(populacao, estoque_cd, capacidade_lojas, demanda, custo_caminhao, executor_cls)
    fim = time.time()
    print(f"[INFO] Tempo com {executor_cls.__name__}: {fim - inicio:.2f}s")
    return resultado

# Teste de desempenho entre threads e processos para descobrir o mais rápido.
def benchmark_executor(populacao, estoque_cd, capacidade_lojas, demanda, custo_caminhao):
    def executar(executor_cls):
        inicio = time.time()
        # Chama a função fitness com a população de 10 indivíduos para decidir o melhor.
        resultados = fitness_paralela(populacao, estoque_cd, capacidade_lojas, demanda, custo_caminhao, executor_cls)
        duracao = time.time() - inicio
        return resultados, duracao

    print("\n[INFO] Realizando benchmark entre ThreadPool e ProcessPool...")
    resultados_thread, tempo_thread = executar(cf.ThreadPoolExecutor)
    print(f"[INFO] ThreadPoolExecutor levou {tempo_thread:.2f}s")

    resultados_process, tempo_process = executar(cf.ProcessPoolExecutor)
    print(f"[INFO] ProcessPoolExecutor levou {tempo_process:.2f}s")

    if tempo_thread <= tempo_process:
        print("[INFO] Usando ThreadPoolExecutor\n")
        return resultados_thread, cf.ThreadPoolExecutor
    else:
        print("[INFO] Usando ProcessPoolExecutor\n")
        return resultados_process, cf.ProcessPoolExecutor
    
# Verifica a diversidade genética dos pais
def hamming(pai1, pai2):
    # Conta quantos elementos são diferentes
    diferentes = np.sum(pai1 != pai2)
    total = pai1.size
    # Distância de Hamming de 0 a 1
    return diferentes / total

# Mapeia diversidade [0,1] para uma taxa uniforme [0.7, 0.3]
# Quanto mais parecidos os pais, maior a taxa de crossover uniforme
# Evitar valores extremos (<0 ou >1) com max e min
def calc_taxa_uniforme(diversidade):
    tu = 0.7 - (0.4 * diversidade)
    return max(0.1, min(0.9, tu))

# Determina a quantidade de filhos para gerar de acordo com as regras de diversidade
def calc_num_filhos(populacao_tamanho, taxa_mutacao, num_geracoes):
    if populacao_tamanho < 30:
        if taxa_mutacao < 10:
            return 4
        else:
            return 3
    elif populacao_tamanho < 100:
        if taxa_mutacao < 10:
            return 3
        else:
            return 2
    else:
        if taxa_mutacao > 50 or num_geracoes > 300:
            # Controle de crescimento e mutação forte
            return 1  
        else:
            return 2

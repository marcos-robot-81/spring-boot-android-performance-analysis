import aiohttp
import asyncio
import multiprocessing
import time
import csv
import os
import re
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIGURAÇÕES DO ESTUDO ---
URL_ALVO = "http://192.168.0.104:8000"  # Substitua pelo IP/Porta do seu celular
#URL_ALVO = "http://localhost:8000" # para test no vscode
TOTAL_REQUISICOES = 100000           # Quantidade total de requisições (X)
CONCORRENCIA_MAXIMA = 50000           # Quantas requisições simultâneas (threads leves)

async def fazer_requisicao(id_req: int, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """
    Faz uma única requisição GET e retorna os dados de tempo e status.
    """
    inicio_req = time.time()
    try:
        async with session.get(url, timeout=200) as response:
            # Lemos o corpo para garantir que a requisição foi concluída
            await response.read()
            fim_req = time.time()
            return {
                "id": id_req,
                "inicio": datetime.fromtimestamp(inicio_req).isoformat(),
                "duracao": fim_req - inicio_req,
                "status": response.status,
                "erro": ""
            }
    except Exception as e:
        fim_req = time.time()
        # Em testes de carga, timeouts e erros de conexão são comuns
        return {
            "id": id_req,
            "inicio": datetime.fromtimestamp(inicio_req).isoformat(),
            "duracao": fim_req - inicio_req,
            "status": 0,  # 0 representa erro de conexão/timeout
            "erro": str(e)
        }

async def main(proc_id=0, total_reqs=TOTAL_REQUISICOES, max_conc=CONCORRENCIA_MAXIMA, id_offset=0, nivel=0):
    print(f"--- Processo {proc_id} Iniciado (Nível {nivel}) ---")
    print(f"Alvo: {URL_ALVO}")
    print(f"Requisições (neste core): {total_reqs}")
    print(f"Concorrência (neste core): {max_conc}\n")

    inicio = time.time()
    
    # Connector limita o número de conexões TCP abertas
    connector = aiohttp.TCPConnector(limit=max_conc)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Fila de requisições
        queue = asyncio.Queue()
        for i in range(total_reqs):
            queue.put_nowait(id_offset + i + 1)
        
        resultados: List[Dict[str, Any]] = []

        async def worker():
            while True:
                try:
                    id_req = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                
                # Processa a requisição e só pega a próxima quando esta terminar
                resultado = await fazer_requisicao(id_req, session, URL_ALVO)
                resultados.append(resultado)
                
                # Feedback visual de progresso para acompanhar testes longos
                if len(resultados) % 500 == 0:
                    print(f"[Core {proc_id}] Nível {nivel}: {len(resultados)}/{total_reqs} reqs concluídas...")
                queue.task_done()

        # Cria workers limitados pela CONCORRENCIA_MAXIMA
        workers = [asyncio.create_task(worker()) for _ in range(max_conc)]
        
        # Aguarda todos os workers terminarem
        await asyncio.gather(*workers)

    fim = time.time()
    tempo_total = fim - inicio

    # --- SALVAR DADOS EM CSV ---
    nome_arquivo = f"dados_estudo_cientifico_{proc_id}.csv"
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_arquivo)
    
    with open(caminho_arquivo, mode='w', newline='', encoding='utf-8') as csvfile:
        campos = ["id", "inicio", "duracao", "status", "erro"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)
    
    print(f"Dados salvos em: {caminho_arquivo}")

    # --- ANÁLISE DOS DADOS ---
    sucessos = sum(1 for r in resultados if r['status'] == 200)
    erros = sum(1 for r in resultados if r['status'] == 0)
    outros_status = len(resultados) - sucessos - erros
    
    print(f"\n--- Resultados Processo {proc_id} ---")
    print(f"Tempo Total: {tempo_total:.2f} segundos")
    print(f"Taxa (RPS): {total_reqs / tempo_total:.2f} requisições/segundo")
    print(f"Sucessos (HTTP 200): {sucessos}")
    print(f"Falhas de Conexão: {erros}")
    print(f"Outros Códigos HTTP: {outros_status}")

def run_process(proc_id, total_reqs, max_conc, id_offset, nivel):
    """Função wrapper para rodar o asyncio dentro de um processo separado"""
    asyncio.run(main(proc_id, total_reqs, max_conc, id_offset, nivel))

def consolidar_resultados(num_cores, caminho_arquivo_final):
    print("\n--- Consolidando resultados ---")
    caminho_final = caminho_arquivo_final
    
    with open(caminho_final, mode='w', newline='', encoding='utf-8') as f_out:
        writer = None
        for i in range(num_cores):
            nome_parcial = f"dados_estudo_cientifico_{i}.csv"
            caminho_parcial = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_parcial)
            
            if os.path.exists(caminho_parcial):
                with open(caminho_parcial, mode='r', encoding='utf-8') as f_in:
                    reader = csv.DictReader(f_in)
                    if writer is None:
                        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
                        writer.writeheader()
                    for row in reader:
                        writer.writerow(row)
                os.remove(caminho_parcial) # Limpa os arquivos parciais para não acumular lixo
    
    print(f"Arquivo único gerado: {caminho_final}")

if __name__ == "__main__":
    # Detecta número de CPUs disponíveis
    num_cores = multiprocessing.cpu_count()
    print(f"Detectados {num_cores} núcleos. Iniciando modo multiprocessamento...")

    # --- LER CONFIGURAÇÕES DO ARQUIVO DE TEXTO ---
    caminho_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NivelDeTexte.txt")
    configs = []
    
    if os.path.exists(caminho_config):
        with open(caminho_config, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            # Regex para extrair Nivel, Total e Concorrencia
            # Procura por "nivel X", depois "TOTAL_REQUISICOES = Y", depois "CONCORRENCIA_MAXIMA = Z"
            padrao = re.compile(r"nivel\s+(\d+).*?TOTAL_REQUISICOES\s*=\s*(\d+).*?CONCORRENCIA_MAXIMA\s*=\s*(\d+)", re.IGNORECASE | re.DOTALL)
            matches = padrao.findall(conteudo)
            for m in matches:
                configs.append({
                    'nivel': int(m[0]),
                    'total': int(m[1]),
                    'conc': int(m[2])
                })
        print(f"Encontrados {len(configs)} níveis de teste no arquivo.")
    else:
        print("Arquivo NivelDeTexte.txt não encontrado. Usando configuração padrão do script.")
        configs.append({'nivel': 'Padrao', 'total': TOTAL_REQUISICOES, 'conc': CONCORRENCIA_MAXIMA})

    # --- LOOP DE AUTOMATIZAÇÃO ---
    for cfg in configs:
        nivel = cfg['nivel']
        total_reqs_atual = cfg['total']
        max_conc_atual = cfg['conc']
        
        # Cria pasta para o nível
        nome_pasta = f"nivel{nivel}"
        caminho_pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
        
        print(f"\n>>> EXECUTANDO NIVEL {nivel} | Reqs: {total_reqs_atual} | Conc: {max_conc_atual} <<<")
        
        inicio_global = time.time()

        # --- Distribuição de Carga Inteligente ---
        # Garante que a soma total seja exata e evita que cores fiquem com 0
        # quando a concorrência/requisições for menor que o número de cores.
        
        # 1. Define quantos cores realmente serão usados (não adianta usar 12 cores para 10 threads)
        cores_ativos = min(num_cores, max_conc_atual)
        
        # 2. Distribui requisições e concorrência apenas entre os ativos
        reqs_dist = [total_reqs_atual // cores_ativos] * num_cores
        conc_dist = [max_conc_atual // cores_ativos] * num_cores
        
        # Zera os que não serão usados (para garantir segurança nos loops abaixo)
        for i in range(cores_ativos, num_cores):
            reqs_dist[i] = 0
            conc_dist[i] = 0

        # 3. Distribui o resto da divisão entre os primeiros processos ativos
        for i in range(total_reqs_atual % cores_ativos):
            reqs_dist[i] += 1
        for i in range(max_conc_atual % cores_ativos):
            conc_dist[i] += 1

        processos = []
        offset_atual = 0
        for i in range(num_cores):
            # Pula processos que não têm trabalho a fazer (importante para níveis baixos)
            if reqs_dist[i] == 0 or conc_dist[i] == 0:
                continue
            p = multiprocessing.Process(target=run_process, args=(i, reqs_dist[i], conc_dist[i], offset_atual, nivel))
            p.start()
            processos.append(p)
            offset_atual += reqs_dist[i]
        
        for p in processos:
            p.join()
        
        fim_global = time.time()
        tempo_total_global = fim_global - inicio_global
        
        print(f"\n--- Nível {nivel} Finalizado ---")
        print(f"Tempo: {tempo_total_global:.2f}s | RPS: {total_reqs_atual / tempo_total_global:.2f}")
        
        caminho_csv_final = os.path.join(caminho_pasta, "resultado.csv")
        consolidar_resultados(num_cores, caminho_csv_final)
        
        # Pausa de 30s entre níveis para resfriamento e limpeza de conexões
        print("Aguardando 30 segundos antes de iniciar o próximo nível...")
        time.sleep(30)

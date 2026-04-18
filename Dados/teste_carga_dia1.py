import aiohttp
import asyncio
import multiprocessing
import time
import math
import csv
import os
import re
from datetime import datetime

# --- CONFIGURAÇÕES ---
#URL_ALVO = "http://localhost:8001/api/busca/marca/nome?nome=dell"
URL_ALVO = "http://192.168.0.107:8000/"   # URL para a qual os testes serão enviados

async def fazer_requisicoes(url, total_reqs, max_conc, start_id, proc_id):
    """
    Função assíncrona que executa as requisições HTTP e coleta métricas de id, tempo, duração e status.
    """
    connector = aiohttp.TCPConnector(limit=max_conc)
    resultados = []
    
    async with aiohttp.ClientSession(connector=connector) as session:
        queue = asyncio.Queue()
        for i in range(total_reqs):
            queue.put_nowait(start_id + i)
            
        concluidas = 0
        inicio_proc = time.time()
        # Mostra o progresso a cada 10% do total ou a cada 5000 requisições (o que for menor)
        passo_progresso = min(max(1, total_reqs // 10), 5000)

        async def disparar_req():
            nonlocal concluidas
            while True:
                try:
                    req_id = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                    
                inicio_req = time.time()
                iso_inicio = datetime.fromtimestamp(inicio_req).isoformat()
                
                try:
                    async with session.get(url, timeout=200) as response:

                        await response.read() # Garante a leitura completa
                        duracao = time.time() - inicio_req
                        resultados.append({
                            "id": req_id,
                            "inicio": iso_inicio,
                            "duracao": duracao,
                            "status": response.status,
                            "erro": ""
                        })
                except Exception as e:
                    duracao = time.time() - inicio_req
                    resultados.append({
                        "id": req_id,
                        "inicio": iso_inicio,
                        "duracao": duracao,
                        "status": 0, # 0 representa falha
                        "erro": str(e)
                    })
                queue.task_done()
                
                # --- CÁLCULO DE PROGRESSO E TEMPO RESTANTE ---
                concluidas += 1
                if concluidas % passo_progresso == 0 or concluidas == total_reqs:
                    decorrido = time.time() - inicio_proc
                    rps = concluidas / decorrido if decorrido > 0 else 0
                    restante = (total_reqs - concluidas) / rps if rps > 0 else 0
                    porcentagem = (concluidas / total_reqs) * 100
                    print(f"[Processo {proc_id}] {porcentagem:.0f}% ({concluidas}/{total_reqs}) | Tempo decorrido: {decorrido:.1f}s | Falta aprox: {restante:.1f}s")

        # Cria as tarefas limitadas pela concorrência máxima do processo
        tasks = [asyncio.create_task(disparar_req()) for _ in range(max_conc)]
        await asyncio.gather(*tasks)
        
    return resultados

def executar_processo(proc_id, url, total_reqs, max_conc, start_id, nivel, output_dir):
    """
    Wrapper síncrono que roda no processo separado, inicia o loop e salva dados parciais.
    """
    print(f"[Processo {proc_id}] Iniciado. Meta: {total_reqs} reqs | Conc: {max_conc}.")
    resultados = asyncio.run(fazer_requisicoes(url, total_reqs, max_conc, start_id, proc_id))
    
    # Salvar resultados parciais em um arquivo temporário
    tmp_file = os.path.join(output_dir, f"tmp_nivel_{nivel}_proc_{proc_id}.csv")
    with open(tmp_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "inicio", "duracao", "status", "erro"])
        writer.writeheader()
        writer.writerows(resultados)

def consolidar_resultados(output_dir, nivel, cores_ativos, caminho_final):
    """
    Junta todos os arquivos temporários em um só e os exclui.
    """
    with open(caminho_final, mode='w', newline='', encoding='utf-8') as f_out:
        writer = None
        for i in range(cores_ativos):
            tmp_file = os.path.join(output_dir, f"tmp_nivel_{nivel}_proc_{i}.csv")
            if os.path.exists(tmp_file):
                with open(tmp_file, mode='r', encoding='utf-8') as f_in:
                    reader = csv.DictReader(f_in)
                    if writer is None:
                        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
                        writer.writeheader()
                    for row in reader:
                        writer.writerow(row)
                os.remove(tmp_file)
    print(f"Resultados consolidados em: {caminho_final}")

def ler_configuracoes(caminho_txt):
    configs = []
    if os.path.exists(caminho_txt):
        with open(caminho_txt, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            padrao = re.compile(r"nivel\s+(\d+).*?TOTAL_REQUISICOES\s*=\s*(\d+).*?CONCORRENCIA_MAXIMA\s*=\s*(\d+)", re.IGNORECASE | re.DOTALL)
            matches = padrao.findall(conteudo)
            for m in matches:
                configs.append({
                    'nivel': int(m[0]),
                    'total': int(m[1]),
                    'conc': int(m[2])
                })
    return configs

def main():
    print("--- Iniciando Teste de Carga Assíncrono (Baseado em Níveis) ---")
    
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_config = os.path.join(diretorio_atual, "NivelDeTesteDia1.txt")
    
    configs = ler_configuracoes(caminho_config)
    if not configs:
        print(f"Erro: Arquivo '{caminho_config}' não encontrado ou formato inválido.")
        return
    
    total_cores = multiprocessing.cpu_count()
    # Calcula 80% dos cores, garantindo que use ao menos 1 core.
    cores_80_pct = max(1, math.floor(total_cores * 0.8))
    
    print(f"Detectado(s) {total_cores} núcleos de CPU disponíveis.")
    print(f"Utilizando 80% da capacidade: máximo de {cores_80_pct} processo(s) paralelo(s).\n")
    
    for cfg in configs:
        nivel = cfg['nivel']
        total_reqs = cfg['total']
        max_conc = cfg['conc']
        
        print(f"\n>>> EXECUTANDO NIVEL {nivel} | Reqs: {total_reqs} | Conc: {max_conc} <<<")
        
        # Ajusta caso a concorrência seja menor que os cores disponíveis (80%)
        cores_ativos = min(cores_80_pct, max_conc)
        
        # Distribuição de carga balanceada entre os processos ativos
        reqs_dist = [total_reqs // cores_ativos] * cores_ativos
        conc_dist = [max_conc // cores_ativos] * cores_ativos
        
        for i in range(total_reqs % cores_ativos): reqs_dist[i] += 1
        for i in range(max_conc % cores_ativos): conc_dist[i] += 1
            
        processos = []
        offset_id = 1 # IDs começam sempre a partir do número 1
        inicio_nivel = time.time()
        
        for i in range(cores_ativos):
            if reqs_dist[i] == 0 or conc_dist[i] == 0:
                continue
                
            p = multiprocessing.Process(
                target=executar_processo, 
                args=(i, URL_ALVO, reqs_dist[i], conc_dist[i], offset_id, nivel, diretorio_atual)
            )
            processos.append(p)
            p.start()
            offset_id += reqs_dist[i]
            
        for p in processos:
            p.join()
            
        tempo_gasto = time.time() - inicio_nivel
        rps = total_reqs / tempo_gasto if tempo_gasto > 0 else 0
        print(f"--- Nível {nivel} Concluído em {tempo_gasto:.2f}s | RPS: {rps:.2f} ---")
        
        # Gera o arquivo CSV do nível atual com o exato padrão solicitado
        caminho_csv_final = os.path.join(diretorio_atual, f"resultado_nivel_{nivel}.csv")
        consolidar_resultados(diretorio_atual, nivel, cores_ativos, caminho_csv_final)
        
        print("Aguardando 10 segundos para resfriamento antes do próximo nível...")
        time.sleep(10)
        
    print("\nTodos os níveis finalizaram o envio de carga com sucesso.")

if __name__ == '__main__':
    main()
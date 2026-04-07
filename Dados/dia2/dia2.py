import aiohttp
import asyncio
import time
import csv
import os
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIGURAÇÕES DO ESTUDO ---
#URL_ALVO = "http://192.168.1.104:8000"  # Substitua pelo IP/Porta do seu celular
URL_ALVO = "http://localhost:8000/api/busca/marca/nome?nome=dell" # para test no vscode
TOTAL_REQUISICOES = 10000           # Quantidade total de requisições (X)
CONCORRENCIA_MAXIMA = 2000        # Quantas requisições simultâneas (threads leves)

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

async def main():
    print(f"--- Iniciando Teste Científico ---")
    print(f"Alvo: {URL_ALVO}")
    print(f"Total de Requisições: {TOTAL_REQUISICOES}")
    print(f"Concorrência Máxima: {CONCORRENCIA_MAXIMA}\n")

    inicio = time.time()
    
    # Connector limita o número de conexões TCP abertas
    connector = aiohttp.TCPConnector(limit=CONCORRENCIA_MAXIMA)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Fila de requisições
        queue = asyncio.Queue()
        for i in range(TOTAL_REQUISICOES):
            queue.put_nowait(i + 1)
        
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
                queue.task_done()

        # Cria workers limitados pela CONCORRENCIA_MAXIMA
        workers = [asyncio.create_task(worker()) for _ in range(CONCORRENCIA_MAXIMA)]
        
        # Aguarda todos os workers terminarem
        await asyncio.gather(*workers)

    fim = time.time()
    tempo_total = fim - inicio

    # --- SALVAR DADOS EM CSV ---
    nome_arquivo = "dados_estudo_cientifico.csv"
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
    
    print(f"\n--- Resultados do Teste ---")
    print(f"Tempo Total: {tempo_total:.2f} segundos")
    print(f"Taxa (RPS): {TOTAL_REQUISICOES / tempo_total:.2f} requisições/segundo")
    print(f"Sucessos (HTTP 200): {sucessos}")
    print(f"Falhas de Conexão: {erros}")
    print(f"Outros Códigos HTTP: {outros_status}")

if __name__ == "__main__":
    # Executa o loop assíncrono
    asyncio.run(main())

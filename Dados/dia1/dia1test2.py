import aiohttp
import asyncio
import time
import csv
import os
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIGURAÇÕES DO TESTE DE RAMP-UP ---
URL_ALVO = "http://192.168.0.104:8000"  # IP do servidor alvo
# URL_ALVO = "http://localhost:8000"    # Para testes locais

CONCORRENCIA_INICIAL = 500
CONCORRENCIA_FINAL = 2000
DURACAO_TOTAL_MINUTOS = 60
TIMEOUT_REQUISICAO = 200  # 5 segundos para falhar rápido se o servidor travar

async def fazer_requisicao(id_req: int, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """
    Faz uma única requisição GET e retorna os dados.
    """
    inicio_req = time.time()
    try:
        async with session.get(url, timeout=TIMEOUT_REQUISICAO) as response:
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
        return {
            "id": id_req,
            "inicio": datetime.fromtimestamp(inicio_req).isoformat(),
            "duracao": fim_req - inicio_req,
            "status": 0,
            "erro": str(e)
        }

async def main():
    print(f"--- Iniciando Teste de Carga Progressivo (Ramp-up) ---")
    print(f"Alvo: {URL_ALVO}")
    print(f"Início: {CONCORRENCIA_INICIAL} threads")
    print(f"Fim: {CONCORRENCIA_FINAL} threads")
    print(f"Duração: {DURACAO_TOTAL_MINUTOS} minutos")
    
    # Cálculo do incremento por minuto
    diferenca = CONCORRENCIA_FINAL - CONCORRENCIA_INICIAL
    incremento_por_minuto = int(diferenca / DURACAO_TOTAL_MINUTOS)
    print(f"Taxa de crescimento: +{incremento_por_minuto} threads a cada minuto\n")

    inicio_teste = time.time()
    
    # Connector com limite alto para permitir o crescimento até 2000
    connector = aiohttp.TCPConnector(limit=CONCORRENCIA_FINAL + 100)
    
    resultados: List[Dict[str, Any]] = []
    stop_event = asyncio.Event()
    request_id_counter = 0
    id_lock = asyncio.Lock() # Para garantir IDs únicos entre as threads

    async with aiohttp.ClientSession(connector=connector) as session:

        # Função do trabalhador (Worker) que fica rodando infinitamente
        async def worker():
            nonlocal request_id_counter
            while not stop_event.is_set():
                async with id_lock:
                    request_id_counter += 1
                    meu_id = request_id_counter
                
                resultado = await fazer_requisicao(meu_id, session, URL_ALVO)
                resultados.append(resultado)
                # Pequena pausa para não travar o loop localmente se o servidor responder instantaneamente
                # await asyncio.sleep(0.01) 

        workers = []

        # --- LOOP PRINCIPAL DE 1 HORA ---
        for minuto in range(DURACAO_TOTAL_MINUTOS + 1):
            # Calcula quantos workers deveríamos ter agora
            if minuto == 0:
                meta_concorrencia = CONCORRENCIA_INICIAL
            else:
                meta_concorrencia = CONCORRENCIA_INICIAL + (incremento_por_minuto * minuto)
            
            # Garante que não passe do final (por arredondamento)
            if meta_concorrencia > CONCORRENCIA_FINAL:
                meta_concorrencia = CONCORRENCIA_FINAL

            # Adiciona novos workers se necessário
            atual = len(workers)
            necessario = meta_concorrencia - atual
            
            if necessario > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Minuto {minuto}: Subindo de {atual} para {meta_concorrencia} threads (+{necessario})...")
                for _ in range(necessario):
                    workers.append(asyncio.create_task(worker()))
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Minuto {minuto}: Mantendo {atual} threads.")

            # Aguarda 60 segundos (1 minuto) antes de subir a carga novamente
            # Se for o último minuto, apenas espera para coletar dados
            if minuto < DURACAO_TOTAL_MINUTOS:
                await asyncio.sleep(60)
            else:
                print("Tempo final atingido. Encerrando...")

        # Finaliza o teste
        stop_event.set()
        await asyncio.gather(*workers)

    tempo_total = time.time() - inicio_teste

    # --- SALVAR CSV ---
    nome_arquivo = "dados_rampup_500_2000.csv"
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_arquivo)
    
    print(f"\nSalvando dados em {nome_arquivo}...")
    with open(caminho_arquivo, mode='w', newline='', encoding='utf-8') as csvfile:
        campos = ["id", "inicio", "duracao", "status", "erro"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"Teste finalizado em {tempo_total:.2f} segundos.")
    print(f"Total de requisições: {len(resultados)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
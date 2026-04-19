import os
import pandas as pd
import glob

def main():
    # Define o diretório base como a pasta onde o script está localizado (Dados)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lista as subpastas disponíveis no diretório base
    subpastas = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith('.')]
    subpastas.sort()
    
    print("Pastas disponíveis para análise:")
    print("0. [Todas as pastas]")
    for i, pasta in enumerate(subpastas, 1):
        print(f"{i}. {pasta}")
        
    try:
        escolha = int(input("\nDigite o número correspondente à pasta que deseja analisar: "))
    except ValueError:
        print("Entrada inválida. Por favor, digite um número.")
        return
        
    if escolha == 0:
        target_dir = base_dir
    elif 1 <= escolha <= len(subpastas):
        target_dir = os.path.join(base_dir, subpastas[escolha - 1])
    else:
        print("Opção inválida. Encerrando.")
        return

    print(f"\nBuscando arquivos de resultado em: {target_dir}\n")

    # Usa glob para encontrar todos os arquivos de resultado recursivamente (entra em todas as pastas)
    search_pattern = os.path.join(target_dir, '**', 'resultado*.csv')
    arquivos = glob.glob(search_pattern, recursive=True)
    
    if not arquivos:
        print("Nenhum arquivo correspondente encontrado.")
        return

    # Ordena os arquivos pelo caminho para exibição agrupada por dia/nível
    arquivos.sort()
    
    print("-" * 130)
    print(f"{'Caminho do Arquivo':<50} | {'Média (s)':<12} | {'Respostas por Status (com porcentagem)'}")
    print("-" * 130)
    
    for arquivo in arquivos:
        try:
            df = pd.read_csv(arquivo)
            caminho_relativo = os.path.relpath(arquivo, base_dir)
            
            if 'duracao' in df.columns:
                media = df['duracao'].mean()
                
                status_str = "[Sem coluna 'status']"
                if 'status' in df.columns:
                    # Calcula a contagem de cada status
                    status_counts = df['status'].value_counts().to_dict()
                    total_respostas = sum(status_counts.values())
                    
                    # Formata os itens ordenando pela chave (código do status) e adiciona a porcentagem
                    if total_respostas > 0:
                        status_str = ", ".join([f"{int(k)}: {v} ({(v/total_respostas)*100:.1f}%)" for k, v in sorted(status_counts.items())])
                    else:
                        status_str = "0 respostas"
                    
                print(f"{caminho_relativo:<50} | {media:.4f} s   | {status_str}")
            else:
                print(f"{caminho_relativo:<50} | [Sem coluna 'duracao']")
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")
            
    print("-" * 130)

if __name__ == '__main__':
    main()
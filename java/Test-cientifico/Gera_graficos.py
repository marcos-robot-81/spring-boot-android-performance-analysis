
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import multiprocessing
from multiprocessing import cpu_count

def plot_db_files(file_path):
    """
    Gera gráficos de dispersão para os arquivos de dados do dispositivo.
    """
    try:
        print(f"Processando arquivo de DB: {file_path}")
        df = pd.read_csv(file_path)
        df['Data'] = pd.to_datetime(df['Data'])
        
        if 'Duracao' in df.columns:
            df['Duracao_ms'] = df['Duracao'].str.replace(' ms', '').astype(float)
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['Duracao_ms'], s=10, alpha=0.7)
            plt.xlabel('Data')
            plt.ylabel('Duração (ms)')
            plt.title('Duração vs. Data')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'duracao_vs_data.png'))
            plt.close()

        if 'RAM' in df.columns:
            df['RAM_MB'] = df['RAM'].apply(lambda x: float(x.split('MB')[0].strip()))
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['RAM_MB'], s=10, alpha=0.7)
            plt.xlabel('Data')
            plt.ylabel('RAM (MB)')
            plt.title('RAM vs. Data')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'ram_vs_data.png'))
            plt.close()

        if 'CPU Uso' in df.columns:
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['CPU Uso'], s=10, alpha=0.7, color='red')
            plt.xlabel('Data')
            plt.ylabel('CPU Uso (%)')
            plt.title('Uso de CPU vs. Data')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'cpu_vs_data.png'))
            plt.close()

        if 'Temperatura' in df.columns:
            df['Temp_Val'] = df['Temperatura'].astype(str).str.replace('°C', '').astype(float)
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['Temp_Val'], s=10, alpha=0.7, color='orange')
            plt.xlabel('Data')
            plt.ylabel('Temperatura (°C)')
            plt.title('Temperatura vs. Data')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'temperatura_vs_data.png'))
            plt.close()

        if 'RAM Delta' in df.columns:
            df['RAM_Delta_B'] = df['RAM Delta'].str.replace(' B', '').astype(float)
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['RAM_Delta_B'], s=10, alpha=0.7)
            plt.xlabel('Data')
            plt.ylabel('RAM Delta (B)')
            plt.title('RAM Delta vs. Data')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'ram_delta_vs_data.png'))
            plt.close()

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

def plot_subset_device_data(general_db_path, start_time, end_time, output_dir):
    """
    Filtra o arquivo de dados gerais pelo intervalo de tempo e gera gráficos no diretório do nível.
    """
    try:
        df = pd.read_csv(general_db_path)
        df['Data'] = pd.to_datetime(df['Data'], format='mixed')
        
        # Adiciona uma margem de segurança de 1 segundo
        margin = pd.Timedelta(seconds=1)
        
        # Tentativa 1: Tempo exato
        mask = (df['Data'] >= (start_time - margin)) & \
               (df['Data'] <= (end_time + margin))
        df_subset = df.loc[mask].copy()

        # Tentativa 2: Ajuste de fuso horário (+3h) se vazio (Ex: Resultado em Local, DB em UTC)
        if df_subset.empty:
            shift = pd.Timedelta(hours=3)
            mask = (df['Data'] >= (start_time + shift - margin)) & \
                   (df['Data'] <= (end_time + shift + margin))
            df_subset = df.loc[mask].copy()
            if not df_subset.empty:
                print(f"  [INFO] Ajuste de fuso horário (+3h) aplicado para {os.path.basename(output_dir)}")

        if df_subset.empty:
            return

        print(f"Gerando gráficos de dispositivo para o nível em: {output_dir}")

        if 'Duracao' in df_subset.columns:
            df_subset['Duracao_ms'] = df_subset['Duracao'].str.replace(' ms', '').astype(float)
            plt.figure(figsize=(12, 7))
            plt.scatter(df_subset['Data'], df_subset['Duracao_ms'], s=15, alpha=0.7, color='purple')
            plt.xlabel('Data')
            plt.ylabel('Duração (ms)')
            plt.title('Duração (Dispositivo) durante o Teste')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, 'nivel_dispositivo_duracao.png'))
            plt.close()

        if 'RAM' in df_subset.columns:
            df_subset['RAM_MB'] = df_subset['RAM'].apply(lambda x: float(x.split('MB')[0].strip()))
            plt.figure(figsize=(12, 7))
            plt.scatter(df_subset['Data'], df_subset['RAM_MB'], s=15, alpha=0.7, color='purple')
            plt.xlabel('Data')
            plt.ylabel('RAM (MB)')
            plt.title('Uso de RAM (Dispositivo) durante o Teste')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, 'nivel_dispositivo_ram.png'))
            plt.close()

        if 'CPU Uso' in df_subset.columns:
            plt.figure(figsize=(12, 7))
            plt.scatter(df_subset['Data'], df_subset['CPU Uso'], s=15, alpha=0.7, color='red')
            plt.xlabel('Data')
            plt.ylabel('CPU Uso (%)')
            plt.title('Uso de CPU (Dispositivo) durante o Teste')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, 'nivel_dispositivo_cpu.png'))
            plt.close()

        if 'Temperatura' in df_subset.columns:
            df_subset['Temp_Val'] = df_subset['Temperatura'].astype(str).str.replace('°C', '').astype(float)
            plt.figure(figsize=(12, 7))
            plt.scatter(df_subset['Data'], df_subset['Temp_Val'], s=15, alpha=0.7, color='orange')
            plt.xlabel('Data')
            plt.ylabel('Temperatura (°C)')
            plt.title('Temperatura (Dispositivo) durante o Teste')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, 'nivel_dispositivo_temperatura.png'))
            plt.close()

        if 'RAM Delta' in df_subset.columns:
            df_subset['RAM_Delta_B'] = df_subset['RAM Delta'].astype(str).str.replace(' B', '').astype(float)
            plt.figure(figsize=(12, 7))
            plt.scatter(df_subset['Data'], df_subset['RAM_Delta_B'], s=15, alpha=0.7, color='brown')
            plt.xlabel('Data')
            plt.ylabel('RAM Delta (B)')
            plt.title('Variação de RAM (Dispositivo) durante o Teste')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, 'nivel_dispositivo_ram_delta.png'))
            plt.close()

    except Exception as e:
        print(f"Erro ao gerar gráficos de subset do dispositivo: {e}")

def plot_resultado_files(file_path):
    """
    Gera gráficos de dispersão para os arquivos resultado.csv, com cores baseadas no status.
    """
    try:
        print(f"Processando arquivo de resultado: {file_path}")
        df = pd.read_csv(file_path)
        df['inicio'] = pd.to_datetime(df['inicio'], format='mixed')

        def get_color(status):
            if 200 <= status < 300: return 'green'
            elif 400 <= status < 500: return 'orange'
            elif 500 <= status < 600: return 'red'
            else: return 'gray'

        df['color'] = df['status'].apply(get_color)

        plt.figure(figsize=(15, 8))
        plt.scatter(df['inicio'], df['duracao'], c=df['color'], alpha=0.7, s=15)

        plt.xlabel('Início')
        plt.ylabel('Duração (s)')
        plt.title('Duração da Resposta vs. Início (por Status)')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
        plt.gcf().autofmt_xdate()
        plt.grid(True)

        legend_elements = [Line2D([0], [0], marker='o', color='w', label='2xx: Sucesso', markerfacecolor='green', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='4xx: Erro Cliente', markerfacecolor='orange', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='5xx: Erro Servidor', markerfacecolor='red', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='Outro', markerfacecolor='gray', markersize=10)]
        plt.legend(handles=legend_elements, title="Status", loc='upper right')

        plt.savefig(os.path.join(os.path.dirname(file_path), 'resultado_duracao_vs_inicio.png'))
        plt.close()

        # --- Lógica para buscar dados do dispositivo correspondentes a este período ---
        start_time = df['inicio'].min()
        end_time = df['inicio'].max()
        
        # Procura o arquivo dados_geral na pasta pai (pasta do dia)
        current_dir = os.path.dirname(file_path)
        dia_dir = os.path.dirname(current_dir) # Sobe um nível para a pasta 'diaX'
        
        for root, _, files in os.walk(dia_dir):
            for file in files:
                if 'dados_geral' in file and file.endswith('.csv'):
                    general_db_path = os.path.join(root, file)
                    plot_subset_device_data(general_db_path, start_time, end_time, current_dir)
                    break # Para após encontrar o primeiro arquivo correspondente

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

def plot_monitoramento_files(file_path):
    """
    Gera gráficos de dispersão para os arquivos db_monitoramento_nivel.csv.
    """
    try:
        print(f"Processando arquivo de monitoramento: {file_path}")
        df = pd.read_csv(file_path)
        date_col = None
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    temp_dates = pd.to_datetime(df[col], errors='coerce')
                    if temp_dates.notna().any():
                        date_col = col
                        df[date_col] = temp_dates
                        break
                except Exception:
                    continue
        
        if date_col:
            for col in df.columns:
                if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
                    plt.figure(figsize=(12, 7))
                    plt.scatter(df[date_col], df[col], s=10, alpha=0.7)
                    plt.xlabel(date_col)
                    plt.ylabel(col)
                    plt.title(f'{col} vs. {date_col}')
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
                    plt.gcf().autofmt_xdate()
                    plt.grid(True)
                    plt.savefig(os.path.join(os.path.dirname(file_path), f'monitoramento_{col}.png'))
                    plt.close()
    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

def process_file(file_path):
    """
    Função 'worker' que determina o tipo do arquivo e chama a função de plotagem apropriada.
    """
    file_name = os.path.basename(file_path)
    if 'dados_geral' in file_name:
        plot_db_files(file_path)
    elif file_name == 'resultado.csv':
        plot_resultado_files(file_path)
    elif file_name == 'db_monitoramento_nivel.csv':
        plot_monitoramento_files(file_path)

def main():
    """
    Função principal que percorre os diretórios, encontra os arquivos CSV
    e os processa em paralelo usando todos os núcleos da CPU.
    """
    print("Iniciando a geração de gráficos...")
    
    files_to_process = []
    for target_dir in ['dia1', 'dia2']:
        if not os.path.isdir(target_dir):
            print(f"Diretório '{target_dir}' não encontrado. Pulando.")
            continue
        for root, _, files in os.walk(target_dir):
            for file in files:
                if 'dados_geral' in file or file == 'resultado.csv' or file == 'db_monitoramento_nivel.csv':
                    files_to_process.append(os.path.join(root, file))

    if not files_to_process:
        print("Nenhum arquivo CSV para processar foi encontrado.")
        return

    print(f"Encontrados {len(files_to_process)} arquivos CSV para processar.")
    
    num_processes = cpu_count()
    print(f"Usando {num_processes} processos em paralelo.")
    
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(process_file, files_to_process)

    print("Geração de gráficos concluída.")

if __name__ == '__main__':
    main()

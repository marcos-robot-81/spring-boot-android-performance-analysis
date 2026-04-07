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
        print(f"Processando arquivo de DB (30 dias): {file_path}")
        df = pd.read_csv(file_path, on_bad_lines='skip')
        df['Data'] = pd.to_datetime(df['Data'])
        
        if 'Duracao' in df.columns:
            df['Duracao_ms'] = pd.to_numeric(df['Duracao'].astype(str).str.replace(' ms', ''), errors='coerce')
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['Duracao_ms'], s=10, alpha=0.7)
            plt.xlabel('Data')
            plt.ylabel('Duração (ms)')
            plt.title('Duração vs. Data (30 Dias)')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'duracao_vs_data_30d.png'))
            plt.close()

            # Gera uma segunda versão do gráfico removendo outliers (pontos muito fora da curva)
            Q1 = df['Duracao_ms'].quantile(0.25)
            Q3 = df['Duracao_ms'].quantile(0.75)
            IQR = Q3 - Q1
            limite_superior = Q3 + 3 * IQR # Multiplicador 3 foca apenas em anomalias extremas
            df_filtrado = df[df['Duracao_ms'] <= limite_superior]
            
            if not df_filtrado.empty:
                plt.figure(figsize=(12, 7))
                plt.scatter(df_filtrado['Data'], df_filtrado['Duracao_ms'], s=10, alpha=0.7)
                plt.xlabel('Data')
                plt.ylabel('Duração (ms)')
                plt.title('Duração vs. Data (30 Dias) - Sem Outliers')
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
                plt.gcf().autofmt_xdate()
                plt.grid(True)
                plt.savefig(os.path.join(os.path.dirname(file_path), 'duracao_vs_data_30d_sem_outliers.png'))
                plt.close()

        if 'RAM' in df.columns:
            df['RAM_MB'] = pd.to_numeric(df['RAM'].astype(str).apply(lambda x: x.split('MB')[0].strip()), errors='coerce')
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['RAM_MB'], s=10, alpha=0.7)
            plt.xlabel('Data')
            plt.ylabel('RAM (MB)')
            plt.title('RAM vs. Data (30 Dias)')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'ram_vs_data_30d.png'))
            plt.close()

        if 'CPU Uso' in df.columns:
            df['CPU Uso'] = pd.to_numeric(df['CPU Uso'], errors='coerce')
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['CPU Uso'], s=10, alpha=0.7, color='red')
            plt.xlabel('Data')
            plt.ylabel('CPU Uso (%)')
            plt.title('Uso de CPU vs. Data (30 Dias)')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'cpu_vs_data_30d.png'))
            plt.close()

        if 'Temperatura' in df.columns:
            df['Temp_Val'] = pd.to_numeric(df['Temperatura'].astype(str).str.replace('°C', ''), errors='coerce')
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['Temp_Val'], s=10, alpha=0.7, color='orange')
            plt.xlabel('Data')
            plt.ylabel('Temperatura (°C)')
            plt.title('Temperatura vs. Data (30 Dias)')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'temperatura_vs_data_30d.png'))
            plt.close()

        if 'RAM Delta' in df.columns:
            df['RAM_Delta_B'] = pd.to_numeric(df['RAM Delta'].astype(str).str.replace(' B', ''), errors='coerce')
            plt.figure(figsize=(12, 7))
            plt.scatter(df['Data'], df['RAM_Delta_B'], s=10, alpha=0.7)
            plt.xlabel('Data')
            plt.ylabel('RAM Delta (B)')
            plt.title('RAM Delta vs. Data (30 Dias)')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(os.path.dirname(file_path), 'ram_delta_vs_data_30d.png'))
            plt.close()

    except Exception as e:
        print(f"Erro ao processar arquivo DB {file_path}: {e}")

def plot_subset_device_data(general_db_path, start_time, end_time, output_dir):
    """
    Filtra o arquivo de dados gerais pelo intervalo de tempo e gera gráficos correspondentes.
    """
    try:
        df = pd.read_csv(general_db_path, on_bad_lines='skip')
        df['Data'] = pd.to_datetime(df['Data'], format='mixed')
        
        margin = pd.Timedelta(seconds=1)
        mask = (df['Data'] >= (start_time - margin)) & (df['Data'] <= (end_time + margin))
        df_subset = df.loc[mask].copy()

        if df_subset.empty:
            shift = pd.Timedelta(hours=3)
            mask = (df['Data'] >= (start_time + shift - margin)) & (df['Data'] <= (end_time + shift + margin))
            df_subset = df.loc[mask].copy()
            if not df_subset.empty:
                print(f"  [INFO] Ajuste de fuso horário (+3h) aplicado para subset.")

        if df_subset.empty:
            return

        print(f"Gerando gráficos de dispositivo de subset em: {output_dir}")

        if 'Duracao' in df_subset.columns:
            df_subset['Duracao_ms'] = pd.to_numeric(df_subset['Duracao'].astype(str).str.replace(' ms', ''), errors='coerce')
            plt.figure(figsize=(12, 7))
            plt.scatter(df_subset['Data'], df_subset['Duracao_ms'], s=15, alpha=0.7, color='purple')
            plt.title('Duração (Dispositivo) durante Teste')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.savefig(os.path.join(output_dir, 'subset_dispositivo_duracao.png'))
            plt.close()

        # Aqui é possível adicionar os recortes de CPU, RAM e Temperatura caso deseje expandir
        # ...

    except Exception as e:
        print(f"Erro ao gerar gráficos de subset: {e}")

def plot_resultado_files(file_path):
    """
    Gera gráficos de dispersão para os arquivos de resultado consolidados (ex: resultado.csv).
    """
    try:
        print(f"Processando arquivo de resultado: {file_path}")
        df = pd.read_csv(file_path, on_bad_lines='skip')
        df['inicio'] = pd.to_datetime(df['inicio'], format='mixed', errors='coerce')
        df['duracao'] = pd.to_numeric(df['duracao'], errors='coerce')
        df['status'] = pd.to_numeric(df['status'], errors='coerce').fillna(0)

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
        plt.title('Duração da Resposta vs. Início (Status) - 30 Dias')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
        plt.gcf().autofmt_xdate()
        plt.grid(True)

        legend_elements = [Line2D([0], [0], marker='o', color='w', label='2xx: Sucesso', markerfacecolor='green', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='4xx: Erro', markerfacecolor='orange', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='5xx: Falha Servidor', markerfacecolor='red', markersize=10),
                           Line2D([0], [0], marker='o', color='w', label='Outro', markerfacecolor='gray', markersize=10)]
        plt.legend(handles=legend_elements, title="Status", loc='upper right')

        plt.savefig(os.path.join(os.path.dirname(file_path), 'resultado_duracao_vs_inicio_30d.png'))
        plt.close()

        # Gera versão sem outliers (pontos muito fora da curva)
        Q1_res = df['duracao'].quantile(0.25)
        Q3_res = df['duracao'].quantile(0.75)
        IQR_res = Q3_res - Q1_res
        limite_superior_res = Q3_res + 3 * IQR_res
        df_res_filtrado = df[df['duracao'] <= limite_superior_res]

        if not df_res_filtrado.empty:
            plt.figure(figsize=(15, 8))
            plt.scatter(df_res_filtrado['inicio'], df_res_filtrado['duracao'], c=df_res_filtrado['color'], alpha=0.7, s=15)
            plt.xlabel('Início')
            plt.ylabel('Duração (s)')
            plt.title('Duração da Resposta vs. Início (Status) - 30 Dias - Sem Outliers')
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
            plt.gcf().autofmt_xdate()
            plt.grid(True)
            plt.legend(handles=legend_elements, title="Status", loc='upper right')
            plt.savefig(os.path.join(os.path.dirname(file_path), 'resultado_duracao_vs_inicio_30d_sem_outliers.png'))
            plt.close()

        # Busca dados base para gerar o subset de hardware relacionado
        start_time = df['inicio'].min()
        end_time = df['inicio'].max()
        
        current_dir = os.path.dirname(file_path)
        # Assume que o dado geral também está na pasta 'db' ou no próprio diretório
        for root, _, files in os.walk(current_dir):
            for file in files:
                if 'dados' in file.lower() and file.endswith('.csv'):
                    general_db_path = os.path.join(root, file)
                    plot_subset_device_data(general_db_path, start_time, end_time, current_dir)
                    break

    except Exception as e:
        print(f"Erro ao processar resultado {file_path}: {e}")

def plot_monitoramento_files(file_path):
    """
    Gera gráficos de dispersão genéricos para tabelas de monitoramento.
    """
    try:
        print(f"Processando arquivo de monitoramento: {file_path}")
        df = pd.read_csv(file_path, on_bad_lines='skip')
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
                    plt.title(f'{col} vs. {date_col} (30 Dias)')
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M:%S'))
                    plt.gcf().autofmt_xdate()
                    plt.grid(True)
                    plt.savefig(os.path.join(os.path.dirname(file_path), f'monitoramento_30d_{col}.png'))
                    plt.close()
    except Exception as e:
        print(f"Erro ao processar monitoramento {file_path}: {e}")

def process_file(file_path):
    """
    Worker que encaminha o arquivo para o parser/plotter correto baseado no nome.
    """
    file_name = os.path.basename(file_path).lower()
    
    # Direciona flexivelmente caso a nomenclatura varie nos scripts de 30 dias
    if 'dados' in file_name:
        plot_db_files(file_path)
    elif 'resultado' in file_name:
        plot_resultado_files(file_path)
    elif 'monitoramento' in file_name:
        plot_monitoramento_files(file_path)

def main():
    """
    Função principal que varre o diretório '30dias' em busca de relatórios csv
    de 30 dias gerados pelos scripts de carga.
    """
    print("Iniciando a geração de gráficos para o histórico de 30 dias...")
    
    target_dir = '30dias'
    if not os.path.isdir(target_dir):
        print(f"Erro: O diretório '{target_dir}' não foi encontrado na pasta atual.")
        print(f"Certifique-se de estar rodando este script no mesmo diretório em que a pasta '{target_dir}' se encontra.")
        return
        
    files_to_process = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.csv'):
                file_lower = file.lower()
                if 'dados' in file_lower or 'resultado' in file_lower or 'monitoramento' in file_lower:
                    files_to_process.append(os.path.join(root, file))

    if not files_to_process:
        print(f"Nenhum arquivo CSV correspondente foi encontrado na pasta '{target_dir}'.")
        return

    print(f"Encontrados {len(files_to_process)} arquivos CSV para processar.")
    
    num_processes = cpu_count()
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(process_file, files_to_process)

    print("Geração de gráficos de 30 dias concluída com sucesso.")

if __name__ == '__main__':
    main()
"""
╔═════════════════════════════╗
║        Module Utils         ║
╚═════════════════════════════╝
"""

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
from datetime import timedelta
from dotenv import load_dotenv
import openrouteservice
from geopy.geocoders import Nominatim
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import pandas as pd
import pandas_gbq
from google.oauth2 import service_account
from google.cloud import bigquery
import zipfile
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
import subprocess
import shutil
from pathlib import Path
import time
import pyautogui as aut
import os
import customtkinter as ctk
import tkinter as tk


class DataManagements:
    """
    WIP
    """

    def __init__(self):
        pass

    def get_route_distance_and_geocode(self, local_origem: str = None, local_destino: str = None):
        """
        ##################
        # Geolocalizaçao #
        ##################
        """
        geolocator = Nominatim(user_agent="geoapi")

        local_origem = "BR-163 KM 247"
        local_destino = "AV ALM MAXIMIANO FONSECA"

        # CRIAR CONDICIONAL SE O VALOR FOR O MESMO retorna 0
        origem = geolocator.geocode(local_origem)
        destino = geolocator.geocode(local_destino)

        coords_origem = (origem.latitude, origem.longitude)
        coords_destino = (destino.latitude, destino.longitude)
        print(f"Coordenadas de {local_origem}: {coords_origem}")
        print(f"Coordenadas de {local_destino}: {coords_destino}")

        ############################
        # Ferramenta de Roteamento #
        ############################

        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'configs', '.env')
        load_dotenv(dotenv_path=env_path)
        api_key = os.getenv('API_OPEN_ROUTE_SERVICE')
        client = openrouteservice.Client(key=api_key)

        # Calcular rota
        rota = client.directions(
            coordinates=[coords_origem[::-1], coords_destino[::-1]],  # ORS também usa (longitude, latitude)
            profile='driving-hgv',  # Transporte carga pesada
            format='geojson'
        )

        # Extraindo distância e duraçao
        distancia = rota['features'][0]['properties']['segments'][0]['distance'] / 1000
        duracao = rota['features'][0]['properties']['segments'][0]['duration'] / 3600

        print(f"Distância: {distancia:.2f} km")
        print(f"Tempo estimado: {duracao:.2f} horas")


    def agregation_data(self, data_set: str, columns: list):
        """
        Agrega dados de acordo com os parâmetros e cria novos registros onde o endereço de origem da viagem
        seguinte é o endereço de destino da viagem anterior, com base na placa e data de emissao.
        """
        # Definindo caminhos de arquivos para facilitar manutençao
        file_processed_data = os.path.join('..', 'data', 'processed')
        file_raw_data = os.path.join('..', 'data', 'raw', data_set)

        # Verifica se o arquivo existe antes de tentar abri-lo
        if not os.path.exists(file_raw_data):
            raise FileNotFoundError(f'O arquivo {file_raw_data} nao foi encontrado.')

        # Carrega os dados do arquivo JSON
        with open(file_raw_data, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Converte os dados em DataFrame e define as colunas
        df = pd.DataFrame(data)
        df.columns = columns
        df['data_emissao'] = pd.to_datetime(df['data_emissao'], errors='coerce').dt.tz_localize(None) - timedelta(hours=3)

        # Log de início do processamento
        start_time = datetime.now()
        print(f"Iniciando processamento...\nStart_Time: {start_time.strftime('%d/%m/%y %H:%M')}")

        # Inicializa uma lista para os novos registros
        new_records = []
        df = df.sort_values(by=['placa', 'data_emissao'])
        initial_record_count = len(df)
        print(f"Quantidade de registros inicialmente: {initial_record_count}")

        # Itera sobre cada placa
        for placa in df['placa'].unique():
            placa_df = df[df['placa'] == placa].reset_index(drop=True)

            # Itera sobre as viagens para a placa atual
            for index, row in placa_df.iterrows():
                if index > 0:  # Processa registros a partir do segundo índice
                    previous_row = placa_df.iloc[index - 1]
                    new_row = row.copy()

                    # Atualiza o endereço de origem com o destino do registro anterior
                    new_row['origem_endereco'] = previous_row['destino_endereco']
                    new_row['origem_cidade'] = previous_row['destino_cidade']

                    # Mantém o destino do registro atual
                    new_row['destino_endereco'] = row['origem_endereco']
                    new_row['destino_cidade'] = row['origem_cidade']

                    # Atualiza o id_documento para indicar a viagem associada
                    new_row['id_documento'] = "V-" + new_row['id_documento'].replace("C-", "")
                    new_records.append(new_row.to_dict())

                new_records.append(row.to_dict())

        # Converte Timestamps para string antes de salvar em JSON
        for record in new_records:
            if 'data_emissao' in record:
                record['data_emissao'] = record['data_emissao'].isoformat()
        new_records_df = pd.DataFrame(new_records)
        output_file = os.path.join(file_processed_data, 'data_agregation_empty_trip.parquet')
        new_records_df.to_parquet(output_file, engine='pyarrow', index=False)

        # Registro de tempo de execuçao
        end_time = datetime.now()
        execution_time = end_time - start_time
        print(f"Processamento concluído: {end_time.strftime('%d/%m/%y %H:%M')}\nTempo de Execuçao: {execution_time}")
        final_record_count = len(new_records)
        print(f"Total de Registros: {final_record_count}")
        records_included = final_record_count - initial_record_count
        print(f"Registros incluídos: {records_included}")

        return new_records

    def convert_to_parquet(self, filename: str, rename_columns: dict, column_types: dict = None):
        """
        Converte arquivos CSV ou XLSX para .parquet e ajusta os nomes dos cabeçalhos e as tipagens das colunas.

        Args:
            filename (str): Nome do arquivo (sem o caminho completo) localizado na pasta 'raw'.
            rename_columns (dict): Dicionário com os nomes das colunas como chaves e novos nomes como valores.
            column_types (dict): Dicionário com os nomes das colunas como chaves e tipos como valores.
        """
        # Diretorios de origem (raw) e destino (processed)
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        raw_path = os.path.join(base_path, 'raw', filename)
        processed_filename = os.path.splitext(filename)[0] + '.parquet'
        processed_path = os.path.join(base_path, 'processed', processed_filename)

        # Verifica a extensao do arquivo para determinar o formato
        file_extension = os.path.splitext(filename)[1].lower()

        # Carrega o arquivo com base na extensao
        if file_extension == '.csv':
            df = pd.read_csv(raw_path, delimiter=';', header=0, low_memory=False)
        elif file_extension == '.xlsx':
            df = pd.read_excel(raw_path)
        else:
            raise ValueError(f"Formato de arquivo '{file_extension}' nao suportado.")

        # Renomeia as colunas
        df.rename(columns=rename_columns, inplace=True)

        # Ajusta os tipos das colunas, se fornecido
        if column_types is not None:
            for col, col_type in column_types.items():
                if col in df.columns:
                    try:
                        if col_type == 'int':
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                        elif col_type == 'float':
                            df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
                        elif col_type == 'datetime':
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        else:
                            df[col] = df[col].astype(col_type)
                    except ValueError as e:
                        print(f"Erro ao converter a coluna {col} para {col_type}: {e}")

        # Salva o DataFrame em formato Parquet
        df.to_parquet(processed_filename)

        # Move o arquivo Parquet da pasta atual para a pasta 'processed'
        shutil.move(processed_filename, processed_path)

        # Remove o arquivo original da pasta 'raw'
        os.remove(raw_path)

        return processed_path

    def dataframe_to_parquet(self, data, name_parquet, ):
        """
        Salva um DataFrame em formato Parquet e retorna o caminho do arquivo salvo.

        Args:
           data (pd.DataFrame): O DataFrame a ser salvo.
           name_parquet (str): O nome do arquivo Parquet (exemplo: 'dados.parquet').

        Returns:
           str: Caminho completo do arquivo Parquet salvo.
        """
        # Define o caminho base
        base_path = os.path.abspath(os.path.dirname(__file__))
        parquet_file = os.path.abspath(os.path.join(base_path, '..', 'data', 'processed', name_parquet))
        os.makedirs(os.path.dirname(parquet_file), exist_ok=True)
        data.to_parquet(parquet_file, index=False)
        return parquet_file

    def unzip_file(self, full_path_zip):
        extract_dir = os.path.dirname(full_path_zip)

        with zipfile.ZipFile(full_path_zip, 'r') as zip:
            zip.extractall(extract_dir)

    def xlsx_to_parquet(self, file_path: str, rename_columns: dict, column_types: None, steps_to_header: int):
        """
        Converte um arquivo Sieg Nfe .xlsx para .parquet e ajusta os nomes dos cabeçaçhos e ordem,  as tipagens das colunas.

        Args:
            file_path (str): Caminho para o arquivo .xlsx.
            parquet_path (str): Caminho onde o arquivo .parquet será salvo.
            column_types (dict): Dicionário com os nomes das colunas como chaves e tipos como valores.

        Exemplo de uso:
            column_types = {
                'Data': 'datetime64[ns]',
                'Valor': 'float',
                'Quantidade': 'int'
            }
        """

        # Carregar o arquivo Excel
        df = pd.read_excel(file_path, skiprows=steps_to_header)
        df.rename(columns=rename_columns, inplace=True)
        df = df[list(rename_columns.values())]

        # Ajustar as tipagens das colunas conforme especificado
        try:
            for col, col_type in column_types.items():
                if col in df.columns:
                    df[col] = df[col].astype(col_type)
                else:
                    print(f"Coluna {col} não encontrada no arquivo.")
        except Exception as AttributeError:
            print('Tipagem não informada:', {AttributeError})

        # Definir o nome do arquivo .parquet
        parquet_filename = os.path.splitext(os.path.basename(file_path))[0] + '.parquet'

        # Caminho atual e o caminho para a pasta processed
        parquet_path = os.path.join(os.path.dirname(file_path), parquet_filename)
        processed_path = os.path.join(os.path.dirname(os.path.dirname(file_path)), 'processed', parquet_filename)

        # Converter para o formato Parquet
        df.to_parquet(parquet_path)
        # Mover o arquivo ja convertido para pasta processed
        print(df.dtypes)
        shutil.move(parquet_path, processed_path)
        return processed_path

    @staticmethod
    def folder_cleaning(folder, extension=None):
        pasta = folder
        arquivos = os.listdir(pasta)
        # Se nao existir a pasta ela e criada
        if not os.path.exists(folder):
            os.makedirs(folder)
            print("Pasta criada com sucesso!")
        else:
            print("A pasta já existe!.")
        # Limpa todos os arquivos da pasta
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(pasta, arquivo)
            if os.path.isfile(caminho_arquivo):
                if extension is None or arquivo.endswith(extension):
                    os.remove(caminho_arquivo)
        print(f'Pasta esvaziada{folder}')

    @staticmethod
    def unzip(folder_origin, folder_destiny):
        try:
            # Itera os arquivos da pasta
            for arquivo in os.listdir(folder_origin):
                caminho = os.path.join(folder_origin, arquivo)
                # Verifica se e um .zip
                if os.path.isfile(caminho) and arquivo.lower().endswith('.zip'):
                    print(f'Extraindo {arquivo} ...')
                    # Unzipa eles
                    with zipfile.ZipFile(caminho, 'r') as zip_ref:
                        zip_ref.extractall(folder_destiny)
                    print(f'{arquivo} extraido com sucesso !!!!')
                    # Deleta os zips
                    os.remove(caminho)
        except Exception as e:
            print(f'ATENÇÂO:\nOcorreu um erro na execução do metodo unzip.\n{e}')

    @staticmethod
    def serialization_dictionary_csv(matriz):
        dados = matriz
        if dados:
            csv_exists = os.path.isfile('serialization_dictionary.csv')
            colunas = list(dados[0].keys())
            with open('serialization_dictionary.csv', 'a', newline='') as arquivo_csv:
                escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=colunas)  # escritor de dicionarios
                if not csv_exists:
                    escritor_csv.writeheader()

                for linha in dados:
                    escritor_csv.writerow(linha)

    @staticmethod
    # Verifica os numeros de CTE presentes em um arquivo CSV de acordo com a chave retornando sem duplicidade.
    def check_existing_data_csv(filename, key):
        existing_data = set()
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_data.add(row[key])
        except FileNotFoundError:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
            pass
        return existing_data

    @staticmethod
    def get_last_record_from_serialization(filename, key):
        existing_data = set()
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_data.add(row[key])
        except FileNotFoundError:
            print('Arquivo de serialização não encontrado.')
        return existing_data

    @staticmethod
    def open_exe(path):
        caminho_do_arquivo = path
        try:
            with open(caminho_do_arquivo, 'r') as arquivo:
                conteudo = arquivo.read()
                time.sleep(10000)
                print(conteudo)
        except FileNotFoundError:
            print("O arquivo não foi encontrado.")
        except Exception as e:
            print("Ocorreu um erro:", e)

    @staticmethod
    def backward_validation_image_100porcent(image):
        attempt = 0
        accuracy = 0.95
        while attempt < 100:
            try:
                local = aut.locateCenterOnScreen(image, grayscale=False, confidence=accuracy)
                time.sleep(1)
                if local:
                    print(f'Encontrei {image} - {local} ☑️')
                    return local
            except Exception as e:
                attempt += 1
                accuracy -= 0.01
                print(f"Não encontrei {image} | Tentativa: {attempt}/100 | Acurácia:{accuracy}\n{e}")
                time.sleep(1)
        raise Exception("Imagem não encontrada após 100 tentativas. PROGRAMA FINALIZADO")

    # WIP: TENTAR MODULAR ESSE TIPO DE APLICAÇÃO SEM PRECISAR DAS BIBLIOTECAS
    # @staticmethod
    # def scroll_down_page(reference):
    #
    #     while True:  # Desce a pagina ate achar o elemento 1
    #         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #         time.sleep(2)
    #         # Por exemplo o ultimo numero de uma elemento na pagina ex: '//*[@id="grid"]/tbody/tr[last()]/td[3]'
    #         last_element_number = int(
    #             driver.find_element(By.XPATH, ).text)
    #         if last_element_number == 1:
    #             break

    @staticmethod
    def merge_csv(folder):
        # Diretório onde estão os arquivos CSV
        diretorio = folder

        # Lista para armazenar os DataFrames de cada arquivo CSV
        dataframes = []

        # Iterar sobre os arquivos no diretório
        for arquivo in os.listdir(diretorio):
            if arquivo.endswith('.csv'):
                caminho_arquivo = os.path.join(diretorio, arquivo)
                # Ler o arquivo CSV e adicionar ao lista de DataFrames
                try:
                    df = pd.read_csv(caminho_arquivo, encoding='latin1')
                    dataframes.append(df)
                except UnicodeDecodeError:
                    print(f"Erro ao ler o arquivo {caminho_arquivo}: não foi possível decodificar o conteúdo.")

        # Concatenar todos os DataFrames em um único DataFrame
        df_final = pd.concat(dataframes, ignore_index=True)

        # Salvar o DataFrame final em um único arquivo CSV
        df_final.to_csv('csv_concat.csv', index=False)

        print("Arquivo final criado com sucesso!")


class DatabaseConnector:
    """
    Classe responsável por gerenciar conexões com diversos bancos de dados,
    como BigQuery, SQL Server e MongoDB.
    """

    def __init__(self):
        pass

    def sql_to_parquet(self, instance, schema, user, password, name_parquet, query, start_date=None, end_date=None, chunk_size=100000):
        """
        Função para buscar dados de uma consulta SQL, processá-los em chunks e salvar em um arquivo Parquet.

        :param name_parquet: Nome do arquivo Parquet a ser gerado.
        :param query: Consulta SQL a ser executada.
        :param start_date: Data inicial para a consulta, formato 'YYYY-MM-DD'. Padrão é '2022-01-01'.
        :param end_date: Data final para a consulta, formato 'YYYY-MM-DD HH:MM:SS'. Padrão é o momento atual.
        :param chunk_size: Número de linhas processadas por vez. Padrão é 100.000.
        """

        # Criação da string de conexão
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'configs', '.env')
        load_dotenv(dotenv_path=env_path)
        instance = os.getenv(instance)
        schema = os.getenv(schema)
        user = os.getenv(user)
        password = os.getenv(password)
        connection_string = f'mssql+pyodbc://{user}:{password}@{instance}/{schema}?driver=ODBC+Driver+17+for+SQL+Server'
        engine = create_engine(connection_string)

        # Definindo as datas padrão
        start_date = start_date or '2022-01-01'
        end_date = end_date or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Definindo o arquivo Parquet
        base_path = os.path.abspath(os.path.dirname(__file__))  # Caminho absoluto do script
        parquet_file = os.path.abspath(os.path.join(base_path, '..', 'data', 'processed', name_parquet))

        total_rows = 0
        start_time = datetime.now()

        # Usando a conexão no contexto 'with' para garantir que seja fechada adequadamente
        with engine.connect() as connection:
            try:
                # Lendo os dados em chunks
                chunk_iter = pd.read_sql(query, connection, params=(start_date, end_date), chunksize=chunk_size)

                parquet_writer = None

                for i, chunk in enumerate(chunk_iter):
                    # Tratamento genérico das colunas
                    for column in chunk.columns:
                        # Preenchendo valores nulos com um padrão baseado no tipo
                        if chunk[column].dtype.kind in 'iuf':  # Numéricos
                            chunk[column] = chunk[column].fillna(0)
                        elif chunk[column].dtype.kind == 'O':  # Objetos (strings)
                            chunk[column] = chunk[column].fillna('')
                        elif chunk[column].dtype.kind == 'M':  # Datas
                            chunk[column] = pd.to_datetime(chunk[column], errors='coerce')

                    # Convertendo o chunk em uma tabela do PyArrow
                    start_time_chunk = datetime.now()
                    table = pa.Table.from_pandas(chunk)

                    # Escrevendo ou anexando ao arquivo Parquet
                    if parquet_writer is None:
                        parquet_writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')

                    parquet_writer.write_table(table)
                    total_rows += len(chunk)

                    # Prints técnicos
                    finish_time_chunk = datetime.now()
                    duration_chunk = finish_time_chunk - start_time_chunk
                    print(
                        f"\033[34m[INFO] Chunk {i + 1}: {len(chunk)} linhas processadas, Total: {total_rows} linhas, Duração: {duration_chunk}.\033[0m")
                    parquet_size = os.path.getsize(parquet_file)
                    print(f"\033[34mArquivo Parquet: {parquet_size / (1024 ** 2):.2f} MB (após chunk {i + 1})\033[0m")

                if parquet_writer:
                    parquet_writer.close()

            except Exception as e:
                print(f"\033[31m[CRITICAL] Ocorreu um erro:\n{e}\033[0m")

    def check_connect_sqlserver(self, instance, schema, user, password):
        """
        Testa a conexao com o SQL Server e retorna uma mensagem indicando o status.
        """
        try:
            # Carregar variáveis de ambiente
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'configs', '.env')
            load_dotenv(dotenv_path=env_path)

            # Configurações de conexao
            instance = os.getenv(instance)
            schema = os.getenv(schema)
            user = os.getenv(user)
            password = os.getenv(password)

            # String de conexao
            connection_string = f'mssql+pyodbc://{user}:{password}@{instance}/{schema}?driver=ODBC+Driver+17+for+SQL+Server'
            engine = create_engine(connection_string)

            # Teste de conexao abrindo e fechando imediatamente
            with engine.connect() as connection:
                pass
            return print("Conexao com o banco de dados SQL Server bem-sucedida.")

        except SQLAlchemyError as e:
            return print(f"Falha na conexao com o banco de dados:\n{e}")

    def get_bigquery_credentials(self):
        """
        Obtém as credenciais para o BigQuery.
        """
        return service_account.Credentials.from_service_account_file(
            self.service_account_lenarge_prod,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

    def bigquery_api(self, data, destination_table, schema, loading_behavior):
        """
        Insere dados no BigQuery.
        """
        credentials = self.get_bigquery_credentials()

        try:
            if data.endswith('.parquet'):
                dataframe = pd.read_parquet(data)
            elif data.endswith('.csv'):
                dataframe = pd.read_csv(data, delimiter=';', on_bad_lines='warn')
            else:
                raise ValueError("Formato de arquivo não suportado. Use .csv ou .parquet.")

            if dataframe.empty:
                print("O DataFrame está vazio após ler o arquivo.")
                return

            table_schema = [{"name": field.name, "type": field.field_type} for field in schema]

            pandas_gbq.to_gbq(
                dataframe,
                destination_table=destination_table,
                project_id=credentials.project_id,
                credentials=credentials,
                if_exists=loading_behavior
            )
            print(f'Dados enviados para o BigQuery com sucesso.\nTable: {destination_table}')

        except Exception as e:
            print(f'Ocorreu algum erro na inserção dos dados: {e}')

    def execute_query(self, query):
        """
        Executa query no BigQuery e retorna os resultados.
        """
        credentials = self.get_bigquery_credentials()

        try:
            df = pandas_gbq.read_gbq(query, project_id=credentials.project_id, credentials=credentials)
            return df
        except Exception as e:
            print(f"Erro ao executar a consulta: {e}")
            return None

    def execute_update(self, query):
        """
        Executa update no BigQuery.
        """
        credentials = self.get_bigquery_credentials()

        try:
            pandas_gbq.context.credentials = credentials
            pandas_gbq.context.project = credentials.project_id

            # O BigQuery exige `jobs` para executar operações como UPDATE ou DELETE.
            client = bigquery.Client(credentials=credentials, project=credentials.project_id)

            query_job = client.query(query)  # Cria o job para execução
            query_job.result()  # Aguarda a execução
            print("Consulta de atualização executada com sucesso.")
        except Exception as e:
            print(f"Erro ao executar a consulta de atualização: {e}")


class Integrations:
    """
    WIP
    """

    def __init__(self):
        pass

    def sheets_extract(self, oauth, id_sheets, range_sheets, token, scope):
        """
        wip doc
        """
        # Nao esquecer de criar a oauth(oauth) no google cloud.
        creds = None
        if os.path.exists(token):
            creds = Credentials.from_authorized_user_file(token, scope)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Se as credenciais nao existirem, criar novas
                flow = InstalledAppFlow.from_client_secrets_file(
                    oauth, scope
                )
                creds = flow.run_local_server(port=0)
                # Salvar as novas credenciais
                with open(token, "w") as token_file:
                    token_file.write(creds.to_json())

        # Construindo o serviço do Google Sheets
        service = build('sheets', 'v4', credentials=creds)

        if isinstance(range_sheets, list):
            result = {}
            for r in range_sheets:
                data = service.spreadsheets().values().get(spreadsheetId=id_sheets, range=r).execute()
                result[r] = data.get('values', [])
            return result
        else:
            result = service.spreadsheets().values().get(spreadsheetId=id_sheets, range=range_sheets).execute()

        # Verificando se foram encontrados dados
        if not result:
            print('Nenhum dado encontrado.')
        # else:
        # print(f'Dados estraidos com sucesso !!')

        return result.get('values', [])


    def sheets_insert(oauth, id_sheets, range_sheets, token, scope, data, coluna, filtro_coluna):
        """
        wip doc
        """
        # Autenticaçao
        creds = None
        if os.path.exists(token):
            creds = Credentials.from_authorized_user_file(token, scope)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(oauth, scope)
                creds = flow.run_local_server(port=0)
                with open(token, "w") as token_file:
                    token_file.write(creds.to_json())

        # Conectando ao serviço do Google Sheets
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Verifica se há dados
        if not data:
            # print("Nenhum dado encontrado para aplicar o filtro.")
            return

        # Assume a primeira linha como cabeçalho (nomes das colunas)
        header = data[0]  # Primeira linha é o cabeçalho
        rows = data[1:]  # Demais linhas sao os dados

        # Verifica se a coluna especificada existe
        if coluna not in header:
            # print(f"Coluna '{coluna}' nao encontrada.")
            return

        # Encontra o índice da coluna especificada
        coluna_index = header.index(coluna)

        # Normaliza filtro_coluna (remove espaços e coloca tudo em minúsculas)
        filtro_coluna_normalizado = filtro_coluna.strip().lower()

        # Filtra os dados baseados no valor do filtro_coluna, normalizando também os valores de cada linha
        filtered_rows = [
            row for row in rows
            if len(row) > coluna_index and filtro_coluna_normalizado in row[coluna_index].strip().lower()
        ]

        if not filtered_rows:
            # print(f"Nenhuma linha com o valor '{filtro_coluna}' na coluna '{coluna}'.")
            return

        # Prepara os dados filtrados para serem inseridos (inclui o cabeçalho)
        filtered_data = [header] + filtered_rows

        # Insere os dados filtrados na planilha
        request = sheet.values().update(
            spreadsheetId=id_sheets,
            range=range_sheets,
            valueInputOption="RAW",
            body={"values": filtered_data}
        ).execute()
        # print(f'{request.get("updatedCells")} células atualizadas com sucesso.')

class CrawlerManagements:
    """
    WIP
    """
    def __init__(self):
        self.driver = WebDriverSingleton.get_instance().get_driver()

    def validation_url(self, url: str, specific_check: str = None):
        """
        Valida se a URL foi carregada corretamente.
        :parameter specific_check: string opcional a ser verificada no conteúdo da página (case-sensitive).
        :parameter url: URL a ser acessada.
        """
        max_attempts = 50
        for attempt in range(1, max_attempts + 1):
            self.driver.get(url)
            time.sleep(2)

            page_source = self.driver.page_source

            # Verificação do `specific_check` apenas se for fornecido
            if specific_check:
                if specific_check in page_source:
                    print(
                        f"Página carregada com sucesso!\nURL: {url}\nCheck Específico: {specific_check}\nTentativa: {attempt}")
                    break
                elif "ERR_CONNECTION_RESET" in page_source:
                    print(f"Erro de conexão detectado: 'ERR_CONNECTION_RESET', tentativa {attempt}")
                    time.sleep(2)
                else:
                    self.driver.refresh()
                    time.sleep(5)
            else:
                print(f"Página carregada com sucesso sem check específico! URL: {url} Tentativa: {attempt}")
                break
        else:
            self.driver.quit()
            print("Não foi possível carregar a página após várias tentativas.")

    def validation_element(self, by_type, element, timeout):
        """
        Valida se o elemento foi selecionado corretamente.
        WIP: Implementando erros comuns de elemento.
        1 - Implementar espera de carregamento.
        """
        try:
            if by_type == "XPATH":
                found_element = WebDriverWait(self.driver, timeout).until(
                    ec.presence_of_element_located((By.XPATH, element)))
            elif by_type == "CLASS_NAME":
                found_element = WebDriverWait(self.driver, timeout).until(
                    ec.presence_of_element_located((By.CLASS_NAME, element)))
            elif by_type == "CSS_SELECTOR":
                found_element = WebDriverWait(self.driver, timeout).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, element)))
            elif by_type == "NAME":
                found_element = WebDriverWait(self.driver, timeout).until(
                    ec.presence_of_element_located((By.NAME, element)))
                print(f'Elemento encontrado:\n{element}')
            elif by_type == "ID":
                found_element = WebDriverWait(self.driver, timeout).until(
                    ec.presence_of_element_located((By.ID, element)))
            else:
                print(f"Tipo de localização não suportado: {by_type}")
                return None

            # Implementar mais possibilidades aqui
            if found_element.is_displayed() and found_element.is_enabled():
                return found_element
            else:
                print(f"Elemento encontrado, mas não está visível ou habilitado: {found_element}")
                time.sleep(2)
                return self.validation_element(by_type, element, timeout)
        except Exception as e:
            print(f"Elemento não encontrado ou ocorreu um timeout: {element}")
            time.sleep(2)
            return self.validation_element(by_type, element, timeout)
        except Exception as e:
            print(f"Elemento não encontrato, por algum problema: {element}")
            time.sleep(2)
            return self.validation_element(by_type, element, timeout)

    def monitor_download_directory(self, file_extension, timeout=1800):
        """
        Função que monitora o diretório de download padrão do sistema operacional
        para a presença de um arquivo com a extensão especificada.

        Args:
            file_extension (str): Extensão do arquivo a ser monitorado.
            timeout (int): Tempo máximo em segundos para esperar o arquivo aparecer.

        Returns:
            str: Diretorio de download do SO e nome do aruivo ou None se o arquivo não aparecer no tempo limite.
        """
        # Detecta o diretório de download padrão baseado no sistema operacional
        if os.name == "nt":  # Windows
            download_dir = os.path.join(os.getenv("USERPROFILE"), "Downloads")
        else:  # Linux/Mac
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Lista os arquivos no diretório de download
            files = [f for f in Path(download_dir).iterdir() if f.suffix == file_extension]
            if files:
                # Retorna o caminho do primeiro arquivo encontrado com a extensão especificada
                return str(files[0])
            time.sleep(1)
        return None

    def get_target_download_path(self, download_directory_file_name, current_dir, target_subpath):
        """
        Função que navega a partir do diretório atual (onde o script está sendo executado)
        até a pasta de destino desejada, baseada em um subcaminho específico, identifica
        a pasta de download do SO e move o arquivo para o destino.

        Args:
            current_dir (str): Diretório atual onde o código está sendo executado.
            target_subpath (str): O caminho relativo dentro do projeto, começando de onde está o facss_datastream.

        Returns:
            str: Caminho absoluto para o diretório de destino.
        """
        # Localiza o caminho até a pasta 'facss_datastream'
        if 'facss_datastream' in current_dir:
            base_dir = current_dir.split('facss_datastream')[0]  # Volta ao diretório base anterior a facss_datastream
        else:
            raise ValueError("A pasta 'facss_datastream' não foi encontrada no caminho atual.")

        # Junta o caminho base com o subcaminho desejado
        target_path = os.path.join(base_dir, 'facss_datastream', target_subpath)

        # Garante que o diretório existe, caso contrário, cria
        os.makedirs(target_path, exist_ok=True)

        if os.name == "nt":  # Windows
            download_dir = os.path.join(os.getenv("USERPROFILE"), "Downloads")
        else:  # Linux/Mac
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        download_folder = download_dir
        data_folder = target_path
        source_file_path = os.path.join(download_folder, download_directory_file_name)
        shutil.move(source_file_path, data_folder)

        return data_folder

    def quit_driver(self):
        """
        Função que sai do driver e fecha todos os navegadores utilizados, e extrai informaçoes do driver.
        :param file_name:
        :return:
        """
        if self.driver:

            try:
                self.driver.quit()
                time.sleep(0.5)
            except Exception as e:
                print(f"Erro ao fechar o driver: {e}")

        try:
            subprocess.call(["taskkill", "/F", "/IM", "undetected_chromedriver.exe"])
        except Exception as e:
            print(f"Erro ao tentar fechar o chromedriver: {e}")

class ImageRecognitionManagements:
    """
    WIP
    """
    def __init__(self):
        pass

    def find_image(image_path, max_attempts=15, initial_accuracy=0.95):
        """
        Procura uma imagem na tela com a precisao e número de tentativas especificados.
        """
        file_name = image_path.split("gui_targets")[-1][1:].split(".")[0]
        accuracy = initial_accuracy
        for attempt in range(max_attempts):
            try:
                location = aut.locateCenterOnScreen(image_path, confidence=accuracy)
                if location:
                    print(f'\033[32m[++ SUCESS]\nImagem {file_name} encontrada. Retornando: {location}\033[0m')
                    return location
            except Exception as e:
                print(
                    f'\033[33m[!! ERRO]\nImagem {file_name} nao encontrada.Reduzindo acuracia e tentando novamente: {accuracy}\033[0m')
                accuracy = max(accuracy - 0.01, 0.5)  # Reduz a precisao até o limite de 0.5
                time.sleep(1)
        raise FileNotFoundError(
            f"\033[31m[xx CRITICAL]\n Imagem {file_name} nao encontrada apos {max_attempts} tentativas.\033[0m")

    def click_image(image_path, offset_x=0, offset_y=0, behavior_click='left', amount_clicks=1):
        """
        Clica na posiçao especificada com um deslocamento opcional.
        """
        file_name = image_path.split("gui_targets")[-1][1:].split(".")[0]
        current = os.path.dirname(os.path.abspath(__file__))
        target_images_sasgc = os.path.abspath(os.path.join(current, '..', 'data', 'gui_targets', 'bot1'))
        path_gui_image = os.path.join(target_images_sasgc, image_path)
        location = find_image(path_gui_image)
        try:
            if location:
                x, y = location
                if behavior_click == 'left':
                    aut.click(x + offset_x, y + offset_y, clicks=amount_clicks)
                elif behavior_click == 'right':
                    aut.rightClick(x + offset_x, y + offset_y)
                else:
                    print('\033[34m[oo INFO]\nParametro incorreto, por gentileza informe rit ou left\033[0m')
                print(f"\033[32m[++ SUCESS]\nClique realizado em ({x + offset_x}, {y + offset_y})\033[0m")
        except Exception as e:
            print(f'\033[31m[xx CRITICAL]\nOcorreu um erro ao clicar na tela\033[0m')

    def check_image(image_path, max_attempts=30, initial_accuracy=0.95):
        """
        Verifica se uma imagem existe na tela com a precisao e número de tentativas especificados.

        :param image_path: O caminho da imagem a ser verificada.
        :param max_attempts: Número maximo de tentativas de verificaçao.
        :param initial_accuracy: Precisao inicial para a busca da imagem.
        :return: True se a imagem for encontrada, False caso contrario.
        """
        file_name = image_path.split("gui_targets")[-1][1:].split(".")[0]
        current = os.path.dirname(os.path.abspath(__file__))
        target_images_sasgc = os.path.abspath(os.path.join(current, '..', 'data', 'gui_targets', 'bot1'))
        accuracy = initial_accuracy
        for attempt in range(max_attempts):
            try:
                path_gui_image = os.path.join(target_images_sasgc, image_path)
                location = aut.locateCenterOnScreen(path_gui_image, confidence=accuracy)
                if location:
                    print(f'\033[32m[++ SUCESS]\nImagem {file_name} encontrada em {location} \033[0m')
                    return True
            except Exception as e:
                print(
                    f'\033[33m[!! ERRO]\nImagem {file_name} nao encontrada.Reduzindo acuracia e tentando novamente: {accuracy}\033[0m')
                accuracy = max(accuracy - 0.01, 0.5)  # Reduz a precisao até o limite de 0.5
                time.sleep(1)
        print(f'\033[35m[!o INFO]\n Imagem nao encontrada, retornando False\033[0m')
        return False  # Retorna False se a imagem nao for encontrada

    def atualizar_tempo(root, tempo_restante, label_tempo):
        """
        wip doc
        """
        minutos = tempo_restante // 60
        segundos = tempo_restante % 60
        label_tempo.configure(text="{:02d}:{:02d}".format(minutos, segundos))
        if tempo_restante > 0:
            root.after(1000, atualizar_tempo, root, tempo_restante - 1, label_tempo)

    def cronometro(segundos):
        """
        wip doc
        """
        tempo = segundos
        root = ctk.CTk()
        root.configure(bg="white")
        # root.iconbitmap('C:/Users/fabricio.lopes/Desktop/app_apresentacao/icon.ico')
        root.geometry("100x80+5+5")  # Tamanho e posiçao da janela
        root.title("FACCS")  # Definindo o título da janela

        label_tempo = tk.Label(root, text="", font=("Arial", 25), bg="black", fg="red")
        label_tempo.pack(padx=20, pady=20)

        atualizar_tempo(root, tempo, label_tempo)

        root.after(tempo * 1000, root.destroy)
        root.mainloop()
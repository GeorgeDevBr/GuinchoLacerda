import sqlite3
from typing import List, Union, Optional, Dict, Tuple
import os
import pickle
import datetime
from datetime import datetime, timedelta
import random

# Importações para integração com as APIs do Google
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Escopos de acesso para Google Drive e Sheets
ESCOPOS = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']


class BancoDados:
    """
    Classe para gerenciamento do banco de dados SQLite.
    Possui métodos para criar tabelas, inserir, ler, atualizar e deletar registros,
    além de obter dados e cadastrar um administrador padrão.
    """
    def __init__(self, nome_banco: str = "gestao_guinchos.db"):
        try:
            self.conexao = sqlite3.connect(nome_banco)
            self.cursor = self.conexao.cursor()
            self.criar_tabelas()
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")

    def criar_tabelas(self):
        """
        Cria as tabelas necessárias, se ainda não existirem.
        São criadas as tabelas: usuarios, transacoes, guinchos, servicos_guincho e anexos.
        Na tabela 'anexos' o campo 'tipo' identifica o tipo do anexo.
        """
        tabelas_sql = {
            "usuarios": '''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE,
                    senha TEXT,
                    tipo TEXT CHECK(tipo IN ('Administrador', 'Secretaria', 'Motorista')) NOT NULL,
                    cnh TEXT UNIQUE,
                    celular TEXT NOT NULL,
                    justificativa TEXT
                )''',
            "transacoes": '''
                CREATE TABLE IF NOT EXISTS transacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    valor REAL NOT NULL,
                    categoria TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    metodo_pagamento TEXT CHECK(metodo_pagamento IN ('Pix', 'Cartão', 'Dinheiro')) NOT NULL,
                    recebedor_id INTEGER NOT NULL,
                    secretaria_id INTEGER,
                    guincho_id INTEGER,
                    motorista_id INTEGER,
                    status TEXT CHECK(status IN ('Pago', 'Pendente', 'Parcelado')) NOT NULL,
                    FOREIGN KEY(recebedor_id) REFERENCES usuarios(id),
                    FOREIGN KEY(secretaria_id) REFERENCES usuarios(id),
                    FOREIGN KEY(guincho_id) REFERENCES guinchos(id),
                    FOREIGN KEY(motorista_id) REFERENCES usuarios(id)
                )''',
            "guinchos": '''
                CREATE TABLE IF NOT EXISTS guinchos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    placa TEXT UNIQUE NOT NULL,
                    modelo TEXT NOT NULL,
                    motorista_id INTEGER,
                    secretaria_id INTEGER NOT NULL,
                    disponivel BOOLEAN DEFAULT 1,
                    FOREIGN KEY(motorista_id) REFERENCES usuarios(id),
                    FOREIGN KEY(secretaria_id) REFERENCES usuarios(id)
                )''',
            "servicos_guincho": '''
                CREATE TABLE IF NOT EXISTS servicos_guincho (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_solicitacao TEXT NOT NULL,
                    guincho_id INTEGER NOT NULL,
                    tipo_solicitacao TEXT CHECK(tipo_solicitacao IN ('Particular', 'Seguradora')) NOT NULL,
                    protocolo TEXT,
                    origem TEXT NOT NULL,
                    destino TEXT NOT NULL,
                    status TEXT CHECK(status IN ('Em andamento', 'Finalizado', 'Cancelado')) NOT NULL,
                    FOREIGN KEY(guincho_id) REFERENCES guinchos(id)
                )''',
            "anexos": '''
                CREATE TABLE IF NOT EXISTS anexos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transacao_id INTEGER NOT NULL,
                    caminho TEXT NOT NULL,
                    tipo TEXT CHECK(tipo IN ('atestado', 'comprovante_guinchamento', 'nota_fiscal')) NOT NULL,
                    FOREIGN KEY(transacao_id) REFERENCES transacoes(id)
                )'''
        }
        try:
            for tabela, sql in tabelas_sql.items():
                self.cursor.execute(sql)
            self.conexao.commit()
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")

    def inserir(self, tabela: str, dados: dict):
        """
        Insere um registro na tabela informada.
        Para a tabela 'usuarios', verifica se o email ou a CNH já estão cadastrados.
        """
        try:
            if tabela == "usuarios":
                if "cnh" in dados and dados["cnh"] is not None:
                    self.cursor.execute("SELECT id FROM usuarios WHERE cnh = ?", (dados["cnh"],))
                    if self.cursor.fetchone():
                        print("Erro: CNH já cadastrada!")
                        return
                if "email" in dados and dados["email"] is not None:
                    self.cursor.execute("SELECT id FROM usuarios WHERE email = ?", (dados["email"],))
                    if self.cursor.fetchone():
                        print("Erro: Email já cadastrado!")
                        return
            colunas = ', '.join(dados.keys())
            placeholders = ', '.join(['?' for _ in dados])
            valores = tuple(dados.values())
            sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
            self.cursor.execute(sql, valores)
            self.conexao.commit()
        except Exception as e:
            print(f"Erro ao inserir dados na tabela {tabela}: {e}")

    def ler(self, tabela: str, filtros: Optional[Dict[str, str]] = None) -> List[Tuple]:
        """
        Lê registros da tabela informada.
        Se 'filtros' for fornecido (dicionário com chave=coluna e valor=termo), os filtros são aplicados com cláusula AND.
        """
        try:
            sql = f"SELECT * FROM {tabela}"
            parametros = []
            if filtros:
                condicoes = []
                for coluna, valor in filtros.items():
                    condicoes.append(f"{coluna} LIKE ?")
                    parametros.append(f"%{valor}%")
                sql += " WHERE " + " AND ".join(condicoes)
            self.cursor.execute(sql, tuple(parametros))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erro ao ler dados da tabela {tabela}: {e}")
            return []

    def atualizar(self, tabela: str, id_registro: int, novos_dados: dict):
        """
        Atualiza o registro identificado por 'id_registro' na tabela informada.
        """
        try:
            clausula_set = ', '.join([f"{chave} = ?" for chave in novos_dados.keys()])
            valores = tuple(novos_dados.values()) + (id_registro,)
            sql = f"UPDATE {tabela} SET {clausula_set} WHERE id = ?"
            self.cursor.execute(sql, valores)
            self.conexao.commit()
        except Exception as e:
            print(f"Erro ao atualizar dados na tabela {tabela}: {e}")

    def deletar(self, tabela: str, id_registro: int):
        """
        Deleta o registro identificado por 'id_registro' na tabela informada.
        """
        try:
            sql = f"DELETE FROM {tabela} WHERE id = ?"
            self.cursor.execute(sql, (id_registro,))
            self.conexao.commit()
        except Exception as e:
            print(f"Erro ao deletar registro na tabela {tabela}: {e}")

    def obter_dados(self, query: str, parametros: Optional[Union[tuple, list]] = None) -> Tuple[List[Tuple], List[str]]:
        """
        Executa uma query e retorna os registros e os nomes das colunas.
        """
        try:
            if parametros:
                self.cursor.execute(query, parametros)
            else:
                self.cursor.execute(query)
            registros = self.cursor.fetchall()
            colunas = [desc[0] for desc in self.cursor.description]
            return registros, colunas
        except Exception as e:
            print(f"Erro ao obter dados com query: {e}")
            return [], []

    def cadastrar_administrador(self):
        """
        Cadastra um usuário administrador padrão.
        """
        self.inserir("usuarios", {
            "nome": "Admin",
            "email": "admin@empresa.com",
            "senha": "admin123",
            "tipo": "Administrador",
            "cnh": None,
            "celular": "(11) 91234-5678",
            "justificativa": None
        })

    def fechar_conexao(self):
        """
        Fecha a conexão com o banco de dados.
        """
        self.conexao.close()


class GoogleDriveSheets:
    """
    Classe para integração com o Google Drive e Sheets utilizando uma conta de serviço.
    
    Configuração do Drive:
      - A estrutura de pastas e planilhas já existe.
      - São utilizadas três planilhas, cujos IDs já são conhecidos:
            • Funcionarios:  "155g1dbGvBF43aMFMDRI2GcOZOAKMvxggrsqmnpI0mas"
            • Guinchamento: "1i0qIzvZnTuYh4tl_pEU3wqYClRQa-SpQ-PvnylhsvBg"
            • Transacoes:   "1bJwnkS5Ui_FDOf0x8KZH19CNhTOR0zv3Ea-8E6UGVG4"
      
      Em cada uma dessas planilhas, para cada secretaria cadastrada (filial),
      uma nova aba será criada ou atualizada com os dados filtrados para aquela filial.
    """
    def __init__(self):
        self.creds = self.autenticar_service_account()
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        # IDs fixos das planilhas já existentes:
        self.planilha_funcionarios = "155g1dbGvBF43aMFMDRI2GcOZOAKMvxggrsqmnpI0mas"
        self.planilha_guinchamento = "1i0qIzvZnTuYh4tl_pEU3wqYClRQa-SpQ-PvnylhsvBg"
        self.planilha_transacoes = "1bJwnkS5Ui_FDOf0x8KZH19CNhTOR0zv3Ea-8E6UGVG4"

    def autenticar_service_account(self):
        """
        Realiza a autenticação com as APIs do Google utilizando a conta de serviço.
        É necessário possuir o arquivo JSON da conta de serviço (ex.: service_account.json).
        """
        from google.oauth2 import service_account
        return service_account.Credentials.from_service_account_file('GuinchoLacerda\lacerdaguinchos-8e2aeaf562ce.json', scopes=ESCOPOS)

    def atualizar_aba_filial(self, spreadsheet_id: str, nome_aba: str, cabecalhos: List[str], dados: List[Tuple]):
        """
        Atualiza (ou cria) uma aba na planilha indicada com os dados da filial.
        Se a aba com o nome da filial não existir, tenta criá-la; caso contrário, atualiza os valores.
        """
        try:
            req_aba = {"addSheet": {"properties": {"title": nome_aba}}}
            body = {"requests": [req_aba]}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
            print(f"Aba '{nome_aba}' criada na planilha {spreadsheet_id}.")
        except Exception as e:
            print(f"Aba '{nome_aba}' pode já existir. Atualizando dados.")

        valores = [cabecalhos] + [list(linha) for linha in dados]
        corpo = {"values": valores}
        intervalo = f"'{nome_aba}'!A1"
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=intervalo,
            valueInputOption="RAW", body=corpo).execute()
        print(f"Dados atualizados na aba '{nome_aba}' da planilha {spreadsheet_id}.")

    def exportar_dados_filiais(self, banco: BancoDados):
        """
        Exporta os dados de cada filial (secretaria) para as três planilhas:
          - Na planilha Funcionarios: exporta os dados do funcionário (a própria secretaria)
            e dos motoristas vinculados (através dos guinchos).
          - Na planilha Guinchamento: exporta os guinchos filtrados pela filial.
          - Na planilha Transacoes: exporta as transações filtradas pela filial.
        Cada filial gera uma nova aba (página) nas respectivas planilhas.
        """
        # Obter todas as secretarias (filiais)
        filiais = banco.ler("usuarios", {"tipo": "Secretaria"})
        if not filiais:
            print("Nenhuma secretaria (filial) encontrada.")
            return

        for filial in filiais:
            filial_id = filial[0]
            filial_nome = filial[1]
            print(f"Processando filial: {filial_nome} (ID: {filial_id})")

            # Dados Funcionários: inclui a própria secretaria e os motoristas vinculados via guinchos
            query_funcionarios = """
                SELECT * FROM usuarios 
                WHERE (tipo = 'Secretaria' AND id = ?) 
                OR (tipo = 'Motorista' AND id IN (
                    SELECT motorista_id FROM guinchos WHERE secretaria_id = ?
                ))
            """
            funcionarios, cabecalhos_funcionarios = banco.obter_dados(query_funcionarios, (filial_id, filial_id))

            # Dados Guinchos: filtrados pela filial
            query_guinchos = "SELECT * FROM guinchos WHERE secretaria_id = ?"
            guinchos, cabecalhos_guinchos = banco.obter_dados(query_guinchos, (filial_id,))

            # Dados Transacoes: filtrados pela filial
            query_transacoes = "SELECT * FROM transacoes WHERE secretaria_id = ?"
            transacoes, cabecalhos_transacoes = banco.obter_dados(query_transacoes, (filial_id,))

            # Atualiza (ou cria) a aba com os dados para a filial em cada planilha
            self.atualizar_aba_filial(self.planilha_funcionarios, filial_nome, cabecalhos_funcionarios, funcionarios)
            self.atualizar_aba_filial(self.planilha_guinchamento, filial_nome, cabecalhos_guinchos, guinchos)
            self.atualizar_aba_filial(self.planilha_transacoes, filial_nome, cabecalhos_transacoes, transacoes)


# Bloco de testes e simulação
if __name__ == "__main__":
    print("Inicializando banco de dados...")
    bd = BancoDados()
    bd.cadastrar_administrador()

    # Inserir secretarias (filiais)
    ids_secretarias = []
    for i in range(1, 4):
        bd.inserir("usuarios", {
            "nome": f"Secretaria{i}",
            "email": f"secretaria{i}@empresa.com",
            "senha": "senha123",
            "tipo": "Secretaria",
            "cnh": None,
            "celular": f"(11) 9{i}123-4567",
            "justificativa": None
        })
        ids_secretarias.append(bd.cursor.lastrowid)

    # Inserir motoristas e guinchos para cada secretaria
    print("Inserindo motoristas e guinchos para cada secretaria...")
    ids_motoristas = []
    ids_guinchos = []
    for id_secretaria in ids_secretarias:
        for j in range(1, 3):
            nome_motorista = f"Motorista{id_secretaria}{j}"
            cnh_motorista = f"{id_secretaria}{j}123456789"
            celular_motorista = f"(11) 9{id_secretaria}{j}123-4567"
            bd.inserir("usuarios", {
                "nome": nome_motorista,
                "email": f"{nome_motorista.lower()}@empresa.com",
                "senha": "senha",
                "tipo": "Motorista",
                "cnh": cnh_motorista,
                "celular": celular_motorista,
                "justificativa": None
            })
            ids_motoristas.append(bd.cursor.lastrowid)
            bd.inserir("guinchos", {
                "placa": f"PLACA{id_secretaria}{j}",
                "modelo": f"Modelo{id_secretaria}{j}",
                "motorista_id": ids_motoristas[-1],
                "secretaria_id": id_secretaria,
                "disponivel": 1
            })
            ids_guinchos.append(bd.cursor.lastrowid)

    # Inserir transações e serviços de guincho (exemplo simplificado)
    print("Inserindo transações e serviços de guincho...")
    data_atual = datetime(2025, 1, 1)
    data_final = datetime(2025, 1, 10)
    while data_atual <= data_final:
        for id_secretaria in ids_secretarias:
            for j in range(1, 3):
                for k in range(random.randint(0, 2)):
                    data_solicitacao = data_atual + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    valor_transacao = random.uniform(150.00, 500.00)
                    index_guincho = (id_secretaria - 1) * 2 + (j - 1)
                    if index_guincho < len(ids_motoristas):
                        id_motorista = ids_motoristas[index_guincho]
                        id_guincho = ids_guinchos[index_guincho]
                        bd.inserir("transacoes", {
                            "data": data_solicitacao.strftime("%Y-%m-%d %H:%M:%S"),
                            "valor": valor_transacao,
                            "categoria": "Serviço de Guincho",
                            "descricao": f"Serviço {id_secretaria}{j}{k}",
                            "metodo_pagamento": random.choice(["Pix", "Cartão", "Dinheiro"]),
                            "recebedor_id": 1,
                            "secretaria_id": id_secretaria,
                            "guincho_id": id_guincho,
                            "motorista_id": id_motorista,
                            "status": random.choice(["Pago", "Pendente", "Parcelado"])
                        })
                        bd.inserir("servicos_guincho", {
                            "data_solicitacao": data_solicitacao.strftime("%Y-%m-%d %H:%M:%S"),
                            "guincho_id": id_guincho,
                            "tipo_solicitacao": random.choice(["Particular", "Seguradora"]),
                            "protocolo": f"PROTO{id_secretaria}{j}{k}",
                            "origem": f"Origem{id_secretaria}{j}{k}",
                            "destino": f"Destino{id_secretaria}{j}{k}",
                            "status": random.choice(["Em andamento", "Finalizado", "Cancelado"])
                        })
        data_atual += timedelta(days=1)

    # Exportar os dados das filiais para as planilhas no Google Drive/Sheets
    print("Exportando dados das filiais para o Google Drive/Sheets...")
    gdrive = GoogleDriveSheets()
    gdrive.exportar_dados_filiais(bd)

    # Fechar conexão com o banco de dados
    bd.fechar_conexao()

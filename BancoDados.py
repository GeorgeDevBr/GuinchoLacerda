import sqlite3
from typing import List, Union, Optional, Dict, Tuple
import os

class BancoDados:
    """
    Gerencia o banco de dados SQLite, criando as tabelas necessárias e oferecendo
    métodos para inserir, ler, atualizar e deletar registros.
    """
    def __init__(self, nome_banco: str = "gestao_guinchos.db"):
        try:
            banco_existe = os.path.exists(nome_banco)
            self.conexao = sqlite3.connect(nome_banco)
            self.cursor = self.conexao.cursor()
            if not banco_existe:
                self.criar_tabelas()
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")

    def criar_tabelas(self):
        """
        Cria as tabelas:
          - usuarios
          - transacoes
          - guinchos
          - servicos_guincho
          - anexos
        A tabela 'anexos' possui um campo 'tipo' para identificar o tipo de anexo.
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
        Insere um registro na tabela especificada.
        Para 'usuarios', verifica se o email ou a CNH já existem.
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
        Retorna os registros da tabela, aplicando filtros (com AND) se fornecidos.
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
        Atualiza o registro identificado por 'id_registro' na tabela especificada.
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
        Deleta o registro de 'id_registro' da tabela.
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
        Cadastra o administrador padrão.
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
        Fecha a conexão com o banco.
        """
        self.conexao.close()


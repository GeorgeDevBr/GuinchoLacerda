import sqlite3

class BancoDeDados:
    def __init__(self, nome_banco="sistema_guinchos.db"):
        self.nome_banco = nome_banco
        self.conexao = sqlite3.connect(self.nome_banco)
        self.cursor = self.conexao.cursor()
        self.criar_tabelas()
    
    def criar_tabelas(self):
        tabelas = [
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cargo TEXT NOT NULL,
                senha TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS guinchos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modelo TEXT NOT NULL,
                placa TEXT NOT NULL UNIQUE,
                motorista TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                categoria TEXT NOT NULL,
                metodo_pagamento TEXT NOT NULL,
                responsavel TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS solicitacoes_guincho (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guincho_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                hora_saida TEXT,
                metodo_pagamento TEXT,
                tipo_solicitacao TEXT NOT NULL,
                protocolo TEXT,
                FOREIGN KEY(guincho_id) REFERENCES guinchos(id)
            )
            """
        ]
        
        for tabela in tabelas:
            self.cursor.execute(tabela)
        self.conexao.commit()
    
    # Métodos CRUD para Usuários
    def inserir_usuario(self, nome, cargo, senha):
        self.cursor.execute("INSERT INTO usuarios (nome, cargo, senha) VALUES (?, ?, ?)", (nome, cargo, senha))
        self.conexao.commit()
    
    def listar_usuarios(self):
        self.cursor.execute("SELECT * FROM usuarios")
        return self.cursor.fetchall()
    
    def atualizar_usuario(self, user_id, nome, cargo, senha):
        self.cursor.execute("UPDATE usuarios SET nome=?, cargo=?, senha=? WHERE id=?", (nome, cargo, senha, user_id))
        self.conexao.commit()
    
    def deletar_usuario(self, user_id):
        self.cursor.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        self.conexao.commit()

    # Métodos CRUD para Guinchos
    def inserir_guincho(self, modelo, placa, motorista):
        self.cursor.execute("INSERT INTO guinchos (modelo, placa, motorista) VALUES (?, ?, ?)", (modelo, placa, motorista))
        self.conexao.commit()
    
    def listar_guinchos(self):
        self.cursor.execute("SELECT * FROM guinchos")
        return self.cursor.fetchall()
    
    def atualizar_guincho(self, guincho_id, modelo, placa, motorista):
        self.cursor.execute("UPDATE guinchos SET modelo=?, placa=?, motorista=? WHERE id=?", (modelo, placa, motorista, guincho_id))
        self.conexao.commit()
    
    def deletar_guincho(self, guincho_id):
        self.cursor.execute("DELETE FROM guinchos WHERE id=?", (guincho_id,))
        self.conexao.commit()
    
    # Métodos CRUD para Transações
    def inserir_transacao(self, descricao, valor, data, categoria, metodo_pagamento, responsavel):
        self.cursor.execute("INSERT INTO transacoes (descricao, valor, data, categoria, metodo_pagamento, responsavel) VALUES (?, ?, ?, ?, ?, ?)", (descricao, valor, data, categoria, metodo_pagamento, responsavel))
        self.conexao.commit()
    
    def listar_transacoes(self):
        self.cursor.execute("SELECT * FROM transacoes")
        return self.cursor.fetchall()
    
    def atualizar_transacao(self, transacao_id, descricao, valor, data, categoria, metodo_pagamento, responsavel):
        self.cursor.execute("UPDATE transacoes SET descricao=?, valor=?, data=?, categoria=?, metodo_pagamento=?, responsavel=? WHERE id=?", (descricao, valor, data, categoria, metodo_pagamento, responsavel, transacao_id))
        self.conexao.commit()
    
    def deletar_transacao(self, transacao_id):
        self.cursor.execute("DELETE FROM transacoes WHERE id=?", (transacao_id,))
        self.conexao.commit()
    
    # Métodos CRUD para Solicitações de Guincho
    def inserir_solicitacao(self, guincho_id, status, hora_saida, metodo_pagamento, tipo_solicitacao, protocolo):
        self.cursor.execute("INSERT INTO solicitacoes_guincho (guincho_id, status, hora_saida, metodo_pagamento, tipo_solicitacao, protocolo) VALUES (?, ?, ?, ?, ?, ?)", (guincho_id, status, hora_saida, metodo_pagamento, tipo_solicitacao, protocolo))
        self.conexao.commit()
    
    def listar_solicitacoes(self):
        self.cursor.execute("SELECT * FROM solicitacoes_guincho")
        return self.cursor.fetchall()
    
    def atualizar_solicitacao(self, solicitacao_id, status, hora_saida, metodo_pagamento, tipo_solicitacao, protocolo):
        self.cursor.execute("UPDATE solicitacoes_guincho SET status=?, hora_saida=?, metodo_pagamento=?, tipo_solicitacao=?, protocolo=? WHERE id=?", (status, hora_saida, metodo_pagamento, tipo_solicitacao, protocolo, solicitacao_id))
        self.conexao.commit()
    
    def deletar_solicitacao(self, solicitacao_id):
        self.cursor.execute("DELETE FROM solicitacoes_guincho WHERE id=?", (solicitacao_id,))
        self.conexao.commit()
    
    def fechar_conexao(self):
        self.conexao.close()

# Teste inicial
if __name__ == "__main__":
    banco = BancoDeDados()
    banco.fechar_conexao()

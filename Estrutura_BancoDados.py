import sqlite3
from typing import List, Union

class BancoDados:
    def __init__(self, db_name="gestao_guinchos.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.criar_tabelas()
    
    def criar_tabelas(self):
        tabelas = {
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
                    FOREIGN KEY(transacao_id) REFERENCES transacoes(id)
                )'''
        }
        
        for tabela, sql in tabelas.items():
            self.cursor.execute(sql)
        self.conn.commit()
    
    def obter_colunas(self, tabela: str):
        self.cursor.execute(f"PRAGMA table_info({tabela})")
        return [col[1] for col in self.cursor.fetchall()]
    
    def inserir(self, tabela: str, dados: dict):
        if "cnh" in dados:
            self.cursor.execute("SELECT id FROM usuarios WHERE cnh = ?", (dados["cnh"],))
            if self.cursor.fetchone():
                print("Erro: CNH já cadastrada!")
                return
        
        colunas = ', '.join(dados.keys())
        valores = tuple(dados.values())
        placeholders = ', '.join(['?' for _ in dados])
        sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
        self.cursor.execute(sql, valores)
        self.conn.commit()
    
    def cadastrar_administrador(self):
        self.inserir("usuarios", {"nome": "Admin", "email": "admin@empresa.com", "senha": "admin123", "tipo": "Administrador", "cnh": None, "celular": "(11) 91234-5678", "justificativa": None})
    
    def ler(self, tabela: str, filtros: Union[List, None] = None):
        sql = f"SELECT * FROM {tabela}"
        colunas = self.obter_colunas(tabela)
        
        if filtros:
            condicoes = ' OR '.join([" OR ".join([f"{col} LIKE ?" for col in colunas]) for _ in filtros])
            valores = tuple(f"%{valor}%" for valor in filtros for _ in colunas)
            sql += f" WHERE {condicoes}"
            self.cursor.execute(sql, valores)
        else:
            self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def atualizar(self, tabela: str, id_registro: int, novos_dados: dict):
        set_clause = ', '.join([f"{chave} = ?" for chave in novos_dados])
        valores = tuple(novos_dados.values()) + (id_registro,)
        sql = f"UPDATE {tabela} SET {set_clause} WHERE id = ?"
        self.cursor.execute(sql, valores)
        self.conn.commit()
    
    def deletar(self, tabela: str, id_registro: int):
        sql = f"DELETE FROM {tabela} WHERE id = ?"
        self.cursor.execute(sql, (id_registro,))
        self.conn.commit()
    
    def fechar_conexao(self):
        self.conn.close()

# Testes
if __name__ == "__main__":
    import random
    from datetime import datetime, timedelta

    db = BancoDados()
    db.cadastrar_administrador()
    
    # Inserir secretárias
    secretarias = []
    for i in range(1, 6):
        db.inserir("usuarios", {"nome": f"Secretaria{i}", "email": f"secretaria{i}@empresa.com", "senha": "senha123", "tipo": "Secretaria", "cnh": None, "celular": f"(11) 9{i}123-4567", "justificativa": None})
        secretarias.append(db.cursor.lastrowid)
    
    # Inserir motoristas e guinchos para cada secretária
    print("Inserir motoristas e guinchos para cada secretária")
    motoristas = []
    guinchos = []
    for secretaria_id in secretarias:
        for j in range(1, 3):
            motorista_nome = f"Motorista{secretaria_id}{j}"
            motorista_cnh = f"{secretaria_id}{j}123456789"
            motorista_celular = f"(11) 9{secretaria_id}{j}123-4567"
            motorista_endereco = f"Rua {secretaria_id}{j}, Bairro {secretaria_id}{j}, Cidade {secretaria_id}{j}"
            db.inserir("usuarios", {"nome": motorista_nome, "email": None, "senha": None, "tipo": "Motorista", "cnh": motorista_cnh, "celular": motorista_celular, "justificativa": None})
            motoristas.append(db.cursor.lastrowid)
            db.inserir("guinchos", {"placa": f"PLACA{secretaria_id}{j}", "modelo": f"Modelo{secretaria_id}{j}", "motorista_id": motoristas[-1], "secretaria_id": secretaria_id, "disponivel": 1})
            guinchos.append(db.cursor.lastrowid)
    
    # Inserir transações e serviços de guincho ao longo de um ano
    print("Inserir transações e serviços de guincho ao longo de um ano")
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    current_date = start_date
    while current_date <= end_date:
        for secretaria_id in secretarias:
            print(f"Inserindo transações para Secretaria{secretaria_id}")
            for j in range(1, 3):
                for k in range(random.randint(0, 5)):
                    data_solicitacao = current_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    valor = random.uniform(150.00, 500.00)
                    guincho_index = (secretaria_id - 1) * 5 + (j - 1)
                    if guincho_index < len(motoristas):
                        motorista_id = motoristas[guincho_index]
                        guincho_id = guinchos[guincho_index]
                        db.inserir("transacoes", {"data": data_solicitacao.strftime("%Y-%m-%d %H:%M:%S"), "valor": valor, "categoria": "Serviço de Guincho", "descricao": f"Serviço {secretaria_id}{j}{k}", "metodo_pagamento": random.choice(["Pix", "Cartão", "Dinheiro"]), "recebedor_id": 1, "secretaria_id": secretaria_id, "guincho_id": guincho_id, "motorista_id": motorista_id, "status": random.choice(["Pago", "Pendente", "Parcelado"])})
                        db.inserir("servicos_guincho", {"data_solicitacao": data_solicitacao.strftime("%Y-%m-%d %H:%M:%S"), "guincho_id": guincho_id, "tipo_solicitacao": random.choice(["Particular", "Seguradora"]), "protocolo": f"PROTO{secretaria_id}{j}{k}", "origem": f"Origem{secretaria_id}{j}{k}", "destino": f"Destino{secretaria_id}{j}{k}", "status": random.choice(["Em andamento", "Finalizado", "Cancelado"])})
                        if random.choice([True, False]):
                            db.inserir("anexos", {"transacao_id": db.cursor.lastrowid, "caminho": f"/caminho/para/anexo{secretaria_id}{j}{k}.pdf"})
        current_date += timedelta(days=1)

    # Inserir despesas fixas mensais
    print("Inserir despesas fixas mensais")
    despesas_fixas = [
        {"categoria": "Aluguel", "descricao": "Aluguel do escritório", "valor": 5000.00},
        {"categoria": "Água", "descricao": "Conta de água", "valor": 300.00},
        {"categoria": "Luz", "descricao": "Conta de luz", "valor": 800.00},
        {"categoria": "Internet", "descricao": "Conta de internet", "valor": 200.00},
    ]
    for month in range(1, 13):
        print(f"Inserindo despesas fixas para o mês {month}")
        for despesa in despesas_fixas:
            data_despesa = datetime(2025, month, 1).strftime("%Y-%m-%d")
            db.inserir("transacoes", {"data": data_despesa, "valor": despesa["valor"], "categoria": despesa["categoria"], "descricao": despesa["descricao"], "metodo_pagamento": "Pix", "recebedor_id": 1, "status": "Pago"})
        for secretaria_id in secretarias:
            db.inserir("transacoes", {"data": data_despesa, "valor": 2500.00, "categoria": "Salário", "descricao": f"Salário Secretaria{secretaria_id}", "metodo_pagamento": "Pix", "recebedor_id": secretaria_id, "status": "Pago"})
        for motorista_id in motoristas:
            db.inserir("transacoes", {"data": data_despesa, "valor": 2500.00, "categoria": "Salário", "descricao": f"Salário Motorista{motorista_id}", "metodo_pagamento": "Pix", "recebedor_id": motorista_id, "status": "Pago"})

    # Inserir despesas pontuais
    print("Inserir despesas pontuais")
    despesas_pontuais = [
        {"data": "2025-02-15", "valor": 1200.00, "categoria": "Reparos", "descricao": "Reparo no veículo Guincho1", "metodo_pagamento": "Cartão", "recebedor_id": 1, "status": "Pago"},
        {"data": "2025-05-20", "valor": 800.00, "categoria": "Manutenção", "descricao": "Manutenção do escritório", "metodo_pagamento": "Dinheiro", "recebedor_id": 1, "status": "Pago"},
        {"data": "2025-08-10", "valor": 1500.00, "categoria": "Peças", "descricao": "Compra de peças para Guincho2", "metodo_pagamento": "Pix", "recebedor_id": 1, "status": "Pago"},
        {"data": "2025-03-10", "valor": 500.00, "categoria": "Despesas Médicas", "descricao": "Despesas médicas para Motorista1", "metodo_pagamento": "Pix", "recebedor_id": 1, "status": "Pago"},
        {"data": "2025-06-15", "valor": 700.00, "categoria": "Licenças", "descricao": "Licença de software", "metodo_pagamento": "Cartão", "recebedor_id": 1, "status": "Pago"},
        {"data": "2025-09-20", "valor": 1000.00, "categoria": "Propaganda", "descricao": "Campanha de marketing", "metodo_pagamento": "Dinheiro", "recebedor_id": 1, "status": "Pago"},
        # ... adicionar mais despesas pontuais ...
    ]
    for despesa in despesas_pontuais:
        db.inserir("transacoes", despesa)
    
    # Leitura de dados
    print("Leitura Geral de Usuarios:", db.ler("usuarios"))
    print("Leitura com Filtro de Usuarios:", db.ler("usuarios", ["João"]))
    print("Leitura Geral de Guinchos:", db.ler("guinchos"))
    print("Leitura Geral de Transacoes:", db.ler("transacoes"))
    print("Leitura Geral de Servicos Guincho:", db.ler("servicos_guincho"))
    print("Leitura Geral de Anexos:", db.ler("anexos"))
    
    # Atualização de dados
    print("Atualização de dados")
    db.atualizar("usuarios", 2, {"nome": "Maria Silva", "email": "maria.silva@email.com"})
    db.atualizar("guinchos", 1, {"disponivel": 0})
    
    # Deleção de dados
    # db.deletar("anexos", 1)
    
    db.fechar_conexao()

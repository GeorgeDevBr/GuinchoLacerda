import sqlite3

def create_database():
    conn = sqlite3.connect("gestao_guinchos.db")
    cursor = conn.cursor()
    
    # Tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('Administrador', 'Secretaria', 'Motorista')) NOT NULL,
            cnh TEXT UNIQUE
        )
    ''')
    
    # Tabela de Transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            metodo_pagamento TEXT CHECK(metodo_pagamento IN ('Pix', 'Cartão', 'Dinheiro')) NOT NULL,
            recebedor_id INTEGER NOT NULL,
            status TEXT CHECK(status IN ('Pago', 'Pendente', 'Parcelado')) NOT NULL,
            FOREIGN KEY(recebedor_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Tabela de Guinchos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guinchos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            modelo TEXT NOT NULL,
            motorista_id INTEGER,
            disponivel BOOLEAN DEFAULT 1,
            FOREIGN KEY(motorista_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Tabela de Serviços de Guincho
    cursor.execute('''
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
        )
    ''')
    
    # Tabela de Anexos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anexos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transacao_id INTEGER NOT NULL,
            caminho TEXT NOT NULL,
            FOREIGN KEY(transacao_id) REFERENCES transacoes(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados configurado com sucesso!")

if __name__ == "__main__":
    create_database()

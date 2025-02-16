# Autor: GEORGE SILVA ALVES - Versão atualizada
from datetime import datetime
from BancoDados import BancoDados
from GoogleDriveSheets import GoogleDriveSheets
import zipfile
import random
import os

if __name__ == "__main__":
    print("Inicializando banco de dados...")
    bd = BancoDados()
    
    # Cadastra o administrador (o método 'inserir' já evita duplicidade via email)
    bd.cadastrar_administrador()
    
    # Verifica se já existem secretárias cadastradas
    secretarias = bd.ler("usuarios", {"tipo": "Secretaria"})
    if not secretarias:
        print("Inserindo secretárias (filiais)...")
        for i in range(1, 11):
            bd.inserir("usuarios", {
                "nome": f"Secretaria{i}",
                "email": f"secretaria{i}@empresa.com",
                "senha": "senha123",
                "tipo": "Secretaria",
                "cnh": None,
                "celular": f"(11) 91{i:02d}34-5678",
                "justificativa": None
            })
        # Releitura para capturar os IDs recém-criados
        secretarias = bd.ler("usuarios", {"tipo": "Secretaria"})
    else:
        print("Secretárias já cadastradas. Pulando inserção.")

    # Para cada secretaria, garante que existam motoristas e guinchos vinculados
    print("Verificando motoristas e guinchos para as secretárias...")
    for secretaria in secretarias:
        secretaria_id = secretaria[0]
        # Verifica se já há algum guincho associado à secretaria
        guinchos_existentes = bd.ler("guinchos", {"secretaria_id": f"{secretaria_id}"})
        if not guinchos_existentes:
            for j in range(1, 6):
                nome_motorista = f"Motorista{secretaria_id}{j}"
                cnh_motorista = f"{secretaria_id}{j}123456789"
                bd.inserir("usuarios", {
                    "nome": nome_motorista,
                    "email": f"{nome_motorista.lower()}@empresa.com",
                    "senha": "senha",
                    "tipo": "Motorista",
                    "cnh": cnh_motorista,
                    "celular": f"(11) 9{secretaria_id}{j}123-4567",
                    "justificativa": None
                })
                # Captura o id do motorista recém-inserido
                motorista_id = bd.cursor.lastrowid
                bd.inserir("guinchos", {
                    "placa": f"PLACA{secretaria_id}{j}",
                    "modelo": f"Modelo{secretaria_id}{j}",
                    "motorista_id": motorista_id,
                    "secretaria_id": secretaria_id,
                    "disponivel": 1
                })
        else:
            print(f"Guinchos para a secretaria {secretaria_id} já existem. Pulando inserção.")

    # Inserção de transações e serviços de guinchamento (apenas se ainda não existirem)
    print("Verificando transações e serviços de guinchamento...")
    for secretaria in secretarias:
        secretaria_id = secretaria[0]
        # Verifica se já existe ao menos uma transação para esta secretaria
        transacoes_existentes = bd.ler("transacoes", {"secretaria_id": f"{secretaria_id}"})
        if not transacoes_existentes:
            for mes in range(1, 13):
                for dia in range(1, 29):  # Simplificação: 28 dias por mês
                    data_str = datetime(2025, mes, dia).strftime("%Y-%m-%d %H:%M:%S")
                    for k in range(1, 4):
                        # Observação: para fins de exemplo, usamos 'guincho_id' e 'motorista_id' fixos.
                        bd.inserir("transacoes", {
                            "data": data_str,
                            "valor": 200.0 + k,
                            "categoria": "Serviço de Guincho",
                            "descricao": f"Transação {k}",
                            "metodo_pagamento": "Pix",
                            "recebedor_id": 1,
                            "secretaria_id": secretaria_id,
                            "guincho_id": 1,  # Exemplo: assumindo guincho 1
                            "motorista_id": 2,  # Exemplo: assumindo motorista 2
                            "status": "Pago"
                        })
                        bd.inserir("servicos_guincho", {
                            "data_solicitacao": data_str,
                            "guincho_id": 1,  # Mesmo exemplo acima
                            "tipo_solicitacao": "Particular",
                            "protocolo": f"PROTO{k}",
                            "origem": f"Origem{k}",
                            "destino": f"Destino{k}",
                            "status": "Em andamento"
                        })
        else:
            print(f"Transações para a secretaria {secretaria_id} já existem. Pulando inserção.")

    # Inserção de despesas fixas (ex.: Aluguel) e variáveis (ex.: Manutenção)
    print("Verificando despesas fixas e variáveis...")
    for secretaria in secretarias:
        secretaria_id = secretaria[0]
        # Verifica se já existe uma despesa fixa (Aluguel) para esta secretaria
        despesa_fixa = bd.ler("transacoes", {"descricao": "Aluguel", "secretaria_id": f"{secretaria_id}"})
        if not despesa_fixa:
            for mes in range(1, 13):
                data_str = datetime(2025, mes, 1).strftime("%Y-%m-%d %H:%M:%S")
                # Despesa fixa
                bd.inserir("transacoes", {
                    "data": data_str,
                    "valor": 5000.0,
                    "categoria": "Despesa Fixa",
                    "descricao": "Aluguel",
                    "metodo_pagamento": "Boleto",
                    "recebedor_id": 1,
                    "secretaria_id": secretaria_id,
                    "guincho_id": None,
                    "motorista_id": None,
                    "status": "Pago"
                })
                # Despesas variáveis
                for _ in range(5):
                    bd.inserir("transacoes", {
                        "data": data_str,
                        "valor": random.uniform(100.0, 1000.0),
                        "categoria": "Despesa Variável",
                        "descricao": "Manutenção",
                        "metodo_pagamento": "Cartão",
                        "recebedor_id": 1,
                        "secretaria_id": secretaria_id,
                        "guincho_id": None,
                        "motorista_id": None,
                        "status": "Pago"
                    })
        else:
            print(f"Despesas para a secretaria {secretaria_id} já existem. Pulando inserção.")

    # Criação e registro de anexos simulados para cada secretaria
    print("Verificando e criando anexos simulados...")
    for secretaria in secretarias:
        secretaria_id = secretaria[0]
        nome_anexo = f"anexo_secretaria{secretaria_id}.txt"
        # Verifica se já existe um anexo com esse caminho
        anexo_existente = bd.ler("anexos", {"caminho": nome_anexo})
        if not anexo_existente:
            # Cria arquivo (vazio) para simular o anexo
            with open(nome_anexo, "w") as f:
                f.write("")  # Conteúdo vazio
            bd.inserir("anexos", {
                "transacao_id": 1,  # Exemplo: associando ao ID 1 de transação
                "caminho": nome_anexo,
                "tipo": "comprovante_guinchamento"
            })
        else:
            print(f"Anexo {nome_anexo} já existe. Pulando criação.")

    # Zipando os arquivos de anexos
    print("Zipando arquivos de anexos...")
    zip_filename = "anexos.zip"
    # Remove zip antigo, se existir, para evitar duplicidade
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for secretaria in secretarias:
            secretaria_id = secretaria[0]
            nome_anexo = f"anexo_secretaria{secretaria_id}.txt"
            if os.path.exists(nome_anexo):
                zipf.write(nome_anexo)
            else:
                print(f"Arquivo {nome_anexo} não encontrado.")

    # Exportação dos dados para o Google Drive/Sheets
    print("Exportando dados para o Google Drive/Sheets...")
    gdrive = GoogleDriveSheets()
    gdrive.exportar_dados(bd)

    bd.fechar_conexao()
    print("Processo concluído com sucesso!")

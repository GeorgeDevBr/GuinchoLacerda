# Autor: GEORGE SILVA ALVES
from datetime import datetime
from BancoDados import BancoDados
from GoogleDriveSheets import GoogleDriveSheets

# Bloco de testes e simulação
if __name__ == "__main__":
    print("Inicializando banco de dados...")
    bd = BancoDados()
    bd.cadastrar_administrador()

    # Inserir uma secretária (filial)
    bd.inserir("usuarios", {
        "nome": "Secretaria1",
        "email": "secretaria1@empresa.com",
        "senha": "senha123",
        "tipo": "Secretaria",
        "cnh": None,
        "celular": "(11) 91234-5678",
        "justificativa": None
    })

    # Inserir motoristas e guinchos para a secretária
    print("Inserindo motoristas e guinchos para a secretária...")
    secretarias = bd.ler("usuarios", {"tipo": "Secretaria"})
    if secretarias:
        secretaria_id = secretarias[0][0]  # Considera a primeira secretária
        for j in range(1, 5):
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
            # Insere um guincho vinculado a este motorista e à secretária
            bd.inserir("guinchos", {
                "placa": f"PLACA{secretaria_id}{j}",
                "modelo": f"Modelo{secretaria_id}{j}",
                "motorista_id": bd.cursor.lastrowid,
                "secretaria_id": secretaria_id,
                "disponivel": 1
            })

    # Inserir algumas transações e solicitações de guinchamento para simulação
    print("Inserindo transações e solicitações de guinchamento...")
    for k in range(1, 4):
        data_str = datetime(2025, 1, k).strftime("%Y-%m-%d %H:%M:%S")
        bd.inserir("transacoes", {
            "data": data_str,
            "valor": 200.0 + k,
            "categoria": "Serviço de Guincho",
            "descricao": f"Transação {k}",
            "metodo_pagamento": "Pix",
            "recebedor_id": 1,
            "secretaria_id": secretaria_id,
            "guincho_id": 1,  # Exemplo: assume que o guincho 1 pertence à secretária
            "motorista_id": 2,
            "status": "Pago"
        })
        bd.inserir("servicos_guincho", {
            "data_solicitacao": data_str,
            "guincho_id": 1,
            "tipo_solicitacao": "Particular",
            "protocolo": f"PROTO{k}",
            "origem": f"Origem{k}",
            "destino": f"Destino{k}",
            "status": "Em andamento"
        })

    # Simular anexos: cria um arquivo de texto vazio (com data/hora no nome) para representar um anexo
    print("Criando anexos simulados...")
    nome_anexo_original = "anexo_secretaria1.txt"
    with open(nome_anexo_original, "w") as f:
        f.write("")  # arquivo vazio
    # Insere um registro de anexo vinculado à transação de ID 1 (exemplo)
    bd.inserir("anexos", {
        "transacao_id": 1,
        "caminho": nome_anexo_original,
        "tipo": "comprovante_guinchamento"
    })

    # Exporta os dados para o Google Drive/Sheets (cria planilha global e planilha da filial com pastas e anexos)
    print("Exportando dados para o Google Drive/Sheets...")
    gdrive = GoogleDriveSheets()
    gdrive.exportar_dados(bd)

    bd.fechar_conexao()
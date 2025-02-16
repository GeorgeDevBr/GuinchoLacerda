# Importações para integração com as APIs do Google
from googleapiclient.discovery import build
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from GuinchoLacerda.classes.BancoDados import BancoDados
import os
import json

# Escopos de acesso para Google Drive e Sheets
ESCOPOS = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

class GoogleDriveSheets:
    """
    Integra com o Google Drive e Sheets utilizando conta de serviço.
    
    A estrutura será criada dinamicamente na pasta online “GuinchoLacerda” (cujo ID
    é fixo conforme o link fornecido). Nela serão salvos:
      - Uma planilha global “usuarios” com os dados de todos os usuários.
      - Para cada secretária (filial):
           • Uma pasta "Filial – [Nome da Secretaria]"
               - Dentro dela, uma planilha "Filial – [Nome da Secretaria] – Dados" com 2 abas:
                     - "Serviço de Guinchamento"
                     - "Transações"
               - Uma pasta "Anexos" para os arquivos de anexos.
    Além disso, as referências (IDs) geradas para cada filial serão salvas em um arquivo JSON
    para evitar buscas futuras e facilitar atualizações.
    """
    def __init__(self):
        self.creds = self.autenticar_service_account()
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        # ID fixo da pasta "GuinchoLacerda" (conforme link fornecido)
        self.id_pasta_principal = "1YXTazfxjcKE8rmv_nnF80pQZMIor8XKz"
        # Cria ou recupera a planilha global "usuarios"
        self.id_planilha_global = self.obter_ou_criar_planilha("usuarios", self.id_pasta_principal)
        # Carrega as referências salvas (se existirem)
        self.referencias = self.carregar_referencias()

    def autenticar_service_account(self):
        """
        Autentica com a conta de serviço usando o arquivo JSON (ex.: service_account.json).
        """
        from google.oauth2.service_account import Credentials
        return Credentials.from_service_account_file('../credenciais/lacerdaguinchos-8e2aeaf562ce.json', scopes=ESCOPOS)

    def carregar_referencias(self) -> Dict:
        """
        Carrega as referências de cada filial (pastas e planilhas) de um arquivo JSON.
        Se o arquivo não existir, retorna um dicionário vazio.
        """
        if os.path.exists("referencias_filial.json"):
            with open("referencias_filial.json", "r") as f:
                return json.load(f)
        else:
            return {}

    def salvar_referencias(self):
        """
        Salva o dicionário de referências no arquivo JSON.
        """
        with open("referencias_filial.json", "w") as f:
            json.dump(self.referencias, f)

    def obter_ou_criar_pasta(self, nome_pasta: str, id_pai: Optional[str]) -> str:
        """
        Verifica se a pasta com o nome especificado existe (dentro do pai, se informado).
        Se não existir, cria a pasta e retorna seu ID.
        """
        query = f"name = '{nome_pasta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if id_pai:
            query += f" and '{id_pai}' in parents"
        resultados = self.drive_service.files().list(q=query, fields="files(id)").execute()
        arquivos = resultados.get('files', [])
        if arquivos:
            return arquivos[0]['id']
        else:
            metadata = {'name': nome_pasta, 'mimeType': 'application/vnd.google-apps.folder'}
            if id_pai:
                metadata['parents'] = [id_pai]
            pasta = self.drive_service.files().create(body=metadata, fields='id').execute()
            return pasta.get('id')

    def obter_ou_criar_planilha(self, nome_planilha: str, id_pasta: str) -> str:
        """
        Verifica se a planilha com o nome informado existe na pasta; se não, cria-a.
        Retorna o ID da planilha.
        """
        query = f"name = '{nome_planilha}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false and '{id_pasta}' in parents"
        resultados = self.drive_service.files().list(q=query, fields="files(id)").execute()
        arquivos = resultados.get('files', [])
        if arquivos:
            return arquivos[0]['id']
        else:
            metadata = {
                'name': nome_planilha,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': [id_pasta]
            }
            planilha = self.drive_service.files().create(body=metadata, fields='id').execute()
            return planilha.get('id')

    def atualizar_planilha(self, spreadsheet_id: str, nome_aba: str, cabecalhos: List[str], dados: List[Tuple]):
        """
        Atualiza ou cria uma aba na planilha informada com os dados fornecidos.
        """
        try:
            req = {"addSheet": {"properties": {"title": nome_aba}}}
            body = {"requests": [req]}
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

    def upload_anexo_filial(self, id_pasta_anexos: str, caminho_arquivo: str):
        """
        Faz upload de um arquivo (anexo) para a pasta de anexos da filial.
        O nome do arquivo receberá a data e hora atuais para torná-lo único.
        """
        if not os.path.exists(caminho_arquivo):
            print(f"Arquivo {caminho_arquivo} não encontrado localmente.")
            return
        base, ext = os.path.splitext(os.path.basename(caminho_arquivo))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        novo_nome = f"{base}_{timestamp}{ext}"
        media = MediaFileUpload(caminho_arquivo, resumable=True)
        metadata = {
            'name': novo_nome,
            'parents': [id_pasta_anexos]
        }
        arquivo = self.drive_service.files().create(body=metadata, media_body=media, fields='id').execute()
        print(f"Anexo '{novo_nome}' enviado para a pasta 'Anexos' (ID: {id_pasta_anexos}).")

    def sincronizar_usuarios(self, banco: BancoDados):
        """
        Exporta todos os usuários para a planilha global “usuarios”.
        """
        usuarios, cabecalhos = banco.obter_dados("SELECT * FROM usuarios", None)
        self.atualizar_planilha(self.id_planilha_global, "Usuarios", cabecalhos, usuarios)
        link = f"https://docs.google.com/spreadsheets/d/{self.id_planilha_global}/edit"
        print(f"Planilha global de usuários disponível em: {link}")

    def sincronizar_filial(self, banco: BancoDados, secretaria: Tuple):
        """
        Para cada secretária (filial), cria ou recupera os seguintes itens:
          - Uma pasta "Filial – [Nome da Secretaria]" na pasta principal.
          - Uma planilha "Filial – [Nome da Secretaria] – Dados" com duas abas:
                • "Serviço de Guinchamento"
                • "Transações"
          - Uma pasta "Anexos" para os arquivos de anexos.
        As referências geradas são salvas para evitar buscas futuras.
        Em seguida, os dados são sincronizados e os anexos (se houver) são enviados.
        """
        secretaria_id = str(secretaria[0])
        secretaria_nome = secretaria[1]
        # Verifica se já existem referências salvas para esta secretaria
        if secretaria_id in self.referencias:
            refs = self.referencias[secretaria_id]
            id_pasta_filial = refs.get("id_pasta_filial")
            id_planilha_filial = refs.get("id_planilha_filial")
            id_pasta_anexos = refs.get("id_pasta_anexos")
            print(f"Referências carregadas para a secretária {secretaria_nome}.")
        else:
            # Cria a pasta da filial
            nome_pasta_filial = f"Filial - {secretaria_nome}"
            id_pasta_filial = self.obter_ou_criar_pasta(nome_pasta_filial, self.id_pasta_principal)
            # Cria a planilha da filial
            nome_planilha_filial = f"Filial - {secretaria_nome} - Dados"
            id_planilha_filial = self.obter_ou_criar_planilha(nome_planilha_filial, id_pasta_filial)
            # Cria a pasta de anexos
            id_pasta_anexos = self.obter_ou_criar_pasta("Anexos", id_pasta_filial)
            # Salva as referências para esta secretaria
            self.referencias[secretaria_id] = {
                "id_pasta_filial": id_pasta_filial,
                "id_planilha_filial": id_planilha_filial,
                "id_pasta_anexos": id_pasta_anexos
            }
            self.salvar_referencias()
            print(f"Referências salvas para a secretária {secretaria_nome}.")

        # Sincroniza a aba "Serviço de Guinchamento"
        query_servico = """
            SELECT sg.* FROM servicos_guincho sg
            JOIN guinchos g ON sg.guincho_id = g.id
            WHERE g.secretaria_id = ?
        """
        servicos, cabecalhos_servicos = banco.obter_dados(query_servico, (secretaria_id,))
        self.atualizar_planilha(id_planilha_filial, "Serviço de Guinchamento", cabecalhos_servicos, servicos)

        # Sincroniza a aba "Transações"
        query_transacoes = "SELECT * FROM transacoes WHERE secretaria_id = ?"
        transacoes, cabecalhos_transacoes = banco.obter_dados(query_transacoes, (secretaria_id,))
        self.atualizar_planilha(id_planilha_filial, "Transações", cabecalhos_transacoes, transacoes)

        # Sincroniza os anexos: seleciona os anexos das transações desta filial
        query_anexos = """
            SELECT a.* FROM anexos a
            JOIN transacoes t ON a.transacao_id = t.id
            WHERE t.secretaria_id = ?
        """
        anexos, cabecalhos_anexos = banco.obter_dados(query_anexos, (secretaria_id,))
        for anexo in anexos:
            # Estrutura: (id, transacao_id, caminho, tipo)
            _, _, caminho, _ = anexo
            self.upload_anexo_filial(id_pasta_anexos, caminho)

        link_filial = f"https://docs.google.com/spreadsheets/d/{id_planilha_filial}/edit"
        print(f"Filial '{secretaria_nome}' sincronizada:")
        print(f"  Pasta: {id_pasta_filial}")
        print(f"  Planilha: {id_planilha_filial} (Link: {link_filial})")
        print(f"  Pasta Anexos: {id_pasta_anexos}")

    def sincronizar_filiais(self, banco: BancoDados):
        """
        Percorre todas as secretárias (filiais) e sincroniza cada uma.
        """
        filiais = banco.ler("usuarios", {"tipo": "Secretaria"})
        if not filiais:
            print("Nenhuma secretaria (filial) encontrada para sincronização.")
            return
        for filial in filiais:
            self.sincronizar_filial(banco, filial)

    def exportar_dados(self, banco: BancoDados):
        """
        Sincroniza a planilha global de usuários e as planilhas de cada filial.
        """
        print("Sincronizando planilha global de usuários...")
        self.sincronizar_usuarios(banco)
        print("Sincronizando dados das filiais...")
        self.sincronizar_filiais(banco)
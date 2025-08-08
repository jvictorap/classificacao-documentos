from classes import Documento
from pathlib import Path
import shutil
import unicodedata
import json


def movedor_arquivos(arquivo:Path, caminho_destino:Path, nome_produtor:str=None):
    """
    Move arquivos de um diretório para outro, renomeando-os conforme necessário.
    """
    destinatario = caminho_destino / nome_produtor / 'DIRPF' / '2026' / 'EXTRATOS DO IMA'
    try:
        pasta_destino = caminho_destino / nome_produtor / 'DIRPF' / '2026' / 'EXTRATOS DO IMA' / arquivo.name
        # pasta_destino = Path(rf'\\DESKTOP-SP6JIVH\Users\User\Desktop\Arquivos Virtuais\CLIENTES\{tipo_produtor}\{nome_str}\DIRPF\2025\EXTRATOS DO IMA')
        destino = pasta_destino / arquivo.name
        destinatario.mkdir(parents=True, exist_ok=True)
        
        if not destino.exists():
            shutil.move(arquivo, pasta_destino)
        else:
            print(f"Arquivo {arquivo.name} já existe no destino.")
    except Exception as e:
        print(f'Erro: {e}')

def remover_acentos(texto):
    """
    Remove acentos de uma string.
    """
    return ''.join(
        char for char in unicodedata.normalize('NFD', texto)
        if unicodedata.category(char) != 'Mn'
    )


# Diretórios de fichas e produtores
diretorio_fichas = Path(r'C:\Users\User\Downloads\EXTRATOS DO IMA')
diretorio_produtor_empregador = Path(r'W:\CLIENTES\PRODUTOR RURAL EMPREGADOR')
diretorio_produtor_pequeno = Path(r'W:\CLIENTES\PRODUTOR RURAL PEQUENO')
lista_nomes_pastas = []

cont = cont_error = cont_arquivo = 0
for arquivo in diretorio_fichas.iterdir():
    if arquivo.suffix == '.pdf':
        cont_arquivo += 1
        print(f'Analisando arquivo: {arquivo.name}')
        
        # Inicializa e processa o documento
        documento = Documento(arquivo)
        texto_extraido = documento.extrair_texto_de_imagem()
        data_str_json = json.dumps(texto_extraido, indent=2)
    
        # Define o prompt e obtém a resposta da IA
        prompt = """
        Será passado um arquivo e eu preciso que você extraia o nome do produtor.
        Retorne apenas o nome, sem nenhuma informação adicional. Somente o nome!
        """
        resposta_ia = documento.resposta_ia(data_str_json, prompt)
        texto_com_acento  = str(resposta_ia.text).upper()  # Remove espaços e transforma em minúsculas
        texto_sem_acento = remover_acentos(texto_com_acento).strip().upper()   # Remove espaços e transforma em maiúsculo
        nome_str = texto_sem_acento 

        # Alterações para que haja compatibilidade com os nomes das pastas 
        if nome_str == 'AUREMIR PEREIRA SILVA':
            nome_str = 'AUREMIR PEREIRA DA SILVA'
        if nome_str == 'CLAUDIA RODRIGUES LIMA VILELA':
            nome_str = 'CLAUDIA LIMA VILELA DOHLER'
        if nome_str == 'EDCARLOS KRETLI DA SILVA':
            nome_str = 'EDICARLOS KRETLI DA SILVA'
        if nome_str == 'FILINTO DE SOUZA MACHADO NETO':
            nome_str = 'FILINTO MACHADO - NETÃO'

        print(f'Nome extraido da ficha: {nome_str}')

    lista_produtor_empregador = [pasta.name.upper() for pasta in diretorio_produtor_empregador.iterdir() if pasta.is_dir()]
    lista_produtor_pequeno = [pasta.name.upper() for pasta in diretorio_produtor_pequeno.iterdir() if pasta.is_dir()]

    if nome_str in lista_produtor_empregador:
        try:
            for pasta in diretorio_produtor_empregador.iterdir():
                if pasta.is_dir() and pasta.name.upper() == nome_str:
                    print(f'Pasta encontrada: {pasta.name}')
                    movedor_arquivos(arquivo, diretorio_produtor_empregador, nome_str)
                    cont += 1
        except Exception as e:
            print(f'Erro ao mover arquivo para produtor empregador: {e}')
            cont_error += 1
    elif nome_str in lista_produtor_pequeno:
        try:
            for pasta in diretorio_produtor_pequeno.iterdir():
                if pasta.is_dir() and pasta.name.upper() == nome_str:
                    print(f'Pasta encontrada: {pasta.name}')
                    movedor_arquivos(arquivo, diretorio_produtor_pequeno, nome_str)
                    cont += 1
        except Exception as e:
            print(f'Erro ao mover arquivo para produtor pequeno: {e}')
            cont_error += 1
    print('-'*140)    

print(f'Total de arquivos movidos: {cont}')
print(f'Total de erros ao mover arquivos: {cont_error}')
print(f'Total de arquivos analisados: {cont_arquivo}')
print('\nFIM DO PROGRAMA')


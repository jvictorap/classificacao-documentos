from classes import Documento
from pathlib import Path
import shutil
import unicodedata
import json


def remover_acentos(texto):
    """
    Remove acentos de uma string.
    """
    return ''.join(
        char for char in unicodedata.normalize('NFD', texto)
        if unicodedata.category(char) != 'Mn'
    )

diretorio_produtor_empregador = Path(r'W:\CLIENTES\PRODUTOR RURAL EMPREGADOR')
diretorio_produtor_pequeno = Path(r'W:\CLIENTES\PRODUTOR RURAL PEQUENO')
lista_nomes_pastas = []

cont = cont_error = cont_arquivo = 0
for pasta in diretorio_produtor_pequeno.iterdir():
    if pasta.is_dir():
        print("-"*90)
        print(f"Analisando pasta de {pasta.name}.\n")
        # print(pasta.name)
        caminho_pastas_extratos = Path(rf'W:\CLIENTES\PRODUTOR RURAL PEQUENO\{pasta.name}\DIRPF\2026\EXTRATOS DO IMA')
     
        try:
            for arquivo in caminho_pastas_extratos.iterdir():
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
                    print(f'Analisando arquivo: {pasta.name}')

                    pasta_atual = Path.cwd() / 'EXTRATOS'
                    nova_pasta = pasta_atual / nome_str
                    nova_pasta.mkdir(parents=True, exist_ok=True)
                    destino = nova_pasta / arquivo.name
                    if not destino.exists():
                        shutil.copy(arquivo, destino)
                    else:
                        print(f"O arquivo {arquivo.name} já existe em {nova_pasta}, não será copiado.")
        except Exception as e:
            print(f'Erro ao acessar {caminho_pastas_extratos}: {e}')



    
        
        


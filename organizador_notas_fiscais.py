from classes import Documento
from pathlib import Path
import json
import shutil


def gerar_nome_unico(destino: Path, base_nome: str):
    """
    Gera um caminho único adicionando _2, _3... caso o arquivo já exista.
    """
    novo_nome = destino / base_nome
    contador = 2
    while novo_nome.exists():
        # separa nome e extensão
        nome_stem = Path(base_nome).stem
        ext = Path(base_nome).suffix
        novo_nome = destino / f"{nome_stem}_{contador}{ext}"
        contador += 1
    return novo_nome

def apagar_arquivos_xml(caminho_pasta: Path):
    pasta = Path(caminho_pasta)
    for arquivo in pasta.iterdir():
        if arquivo.suffix.lower() == ".xml":  # corrigi a verificação
            try:
                print('-' * 100)
                print(f'Apagando arquivo: {arquivo.name}')
                arquivo.unlink()
            except Exception as e:
                print(f'Erro ao apagar o arquivo {arquivo.name}: {e}')
                continue

def organizar_notas_fiscais(caminho_pasta: Path):
    pasta = Path(caminho_pasta)

    
    if arquivo.suffix.lower().strip() == ".pdf":

        documento = Documento(arquivo)
        texto = documento.extrair_texto_de_imagem()
        data_list_str = json.dumps(texto, indent=2)

        prompt = f"""
        Você receberá um conjunto de dados da variável 'data_list_str'. Extraia os seguintes dados:
        Se o documento for uma NF-e, extraia:
        - num_nota
        - comprador
        - vendedor
        Se o documento for uma extrato, extraia:
        - nome_produtor

        retorno tudo em minúsculo, sem acentos e sem caracteres especiais.
        Se não encontrar algum dado, retorne None.
        Retorno no formato JSON com as chaves acima.
        {data_list_str}
        """

        resposta = documento.resposta_ia(texto, prompt)
        resposta_tratada = documento.tratar_dados(resposta)

        # Se for lista, pega o primeiro item, senão mantém
        if isinstance(resposta_tratada, list) and resposta_tratada:
            if resposta_tratada['tipo_doc'].lower() == 'nf-e':
                resposta_tratada = resposta_tratada[0]
                    
    return resposta_tratada

if __name__ == "__main__":
    # caminho = Path(input("Caminho da pasta: "))
    caminho = r'G:\.shortcut-targets-by-id\190_NRy6vixdDw-f1fzC4tNhceviV3-ir\EXTRATOS\CARIVALDO PEREIRA DOS SANTOS'
    apagar_arquivos_xml(caminho)

    ultima_pasta = Path(caminho).name
    print(ultima_pasta)
    for arquivo in Path(caminho).iterdir(): 
        if arquivo.suffix.lower().strip() == ".pdf":
            print("-"*100)
            print(f'Processando arquivo: {arquivo.name}')
            dados = organizar_notas_fiscais(arquivo)
            print(f'Dados extraídos: \n{dados}')
           
            if ultima_pasta.lower().strip() == str(dados['vendedor']).lower().strip():
                nova_pasta = Path(caminho) / 'RECEITAS'
                nova_pasta.mkdir(exist_ok=True, parents=True)
                novo_nome = nova_pasta / f"NF {dados['num_nota']}{dados['vendedor'].upper()} X {dados['comprador'].upper()}.pdf"
                destino = nova_pasta / novo_nome.name
                arquivo.rename(novo_nome)
                if novo_nome.exists():
                    print('Altrando nome do arquivo.')
                    shutil.move(arquivo, novo_nome)
                else:
                    print("Arquivo já existe/Duplicidade de nomes, gerando nome único...\n")
                    base_nome = f"NF {dados['num_nota']}-{dados['vendedor'].upper()} X {dados['comprador'].upper()}.pdf"
                    novo_nome = gerar_nome_unico(nova_pasta, base_nome)
                    destino = nova_pasta / novo_nome.name
                arquivo.rename(novo_nome)
            elif ultima_pasta.lower().strip() == str(dados['comprador']).lower().strip():
                nova_pasta = Path(caminho) / 'DESPESAS'
                nova_pasta.mkdir(exist_ok=True, parents=True)
                novo_nome = nova_pasta / f"NF {dados['num_nota']}-{dados['vendedor'].upper()} X {dados['comprador'].upper()}.pdf"
                destino = nova_pasta / novo_nome.name
                arquivo.rename(novo_nome)
                if novo_nome.exists():
                    print('Altrando nome do arquivo.')
                    shutil.move(arquivo, novo_nome)
                else:
                    print("Arquivo já existe/Duplicidade de nomes, gerando nome único...\n")
                    base_nome = f"NF {dados['num_nota']}-{dados['vendedor'].upper()} X {dados['comprador'].upper()}.pdf"
                    novo_nome = gerar_nome_unico(nova_pasta, base_nome)
                    destino = nova_pasta / novo_nome.name

            


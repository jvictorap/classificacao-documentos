from classes import Documento
from pathlib import Path
import json
import shutil
import re

"""
Script para organizar notas fiscais em pastas de RECEITAS e DESPESAS.
Extrai dados de PDFs usando OCR e IA, e move os arquivos para pastas apropriadas    
"""

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
        if arquivo.suffix.lower() == ".xml":
            try:
                print('-' * 100)
                print(f'Apagando arquivo: {arquivo.name}')
                arquivo.unlink()
            except Exception as e:
                print(f'Erro ao apagar o arquivo {arquivo.name}: {e}')
                continue


def limpar_nome(nome: str) -> str:
    """
    Remove espaços, acentos e caracteres inválidos para nomes de arquivos no Windows.
    """
    nome = nome.replace(" ", "_")  # troca espaços por _
    nome = re.sub(r'[\\/*?:"<>|]', "", nome)  # remove caracteres proibidos
    return nome


def organizar_notas_fiscais(arquivo: Path):
    if arquivo.suffix.lower().strip() == ".pdf":
        documento = Documento(arquivo)
        texto = documento.extrair_texto_de_imagem()
        data_list_str = json.dumps(texto, indent=2)

        prompt = f"""
        Você receberá um conjunto de dados da variável 'data_list_str'. Extraia os seguintes dados:
        Se o documento for uma NF-e, extraia:
        - operacao(compra ou venda)
        - num_nota
        - comprador (Nome completo)
        - vendedor (Nome completo)
        Se o documento for uma extrato, extraia:
        - nome_produtor

        retorno tudo em minúsculo, sem acentos e sem caracteres especiais.
        Se não encontrar algum dado, retorne None.
        Retorno no formato JSON com as chaves acima.
        {data_list_str}
        """

        resposta = documento.resposta_ia(texto, prompt)
        resposta_tratada = documento.tratar_dados(resposta)

        if isinstance(resposta_tratada, list) and resposta_tratada:
            if resposta_tratada[0].get('tipo_doc', '').lower() == 'nf-e':
                resposta_tratada = resposta_tratada[0]

        return resposta_tratada
    return None


if __name__ == "__main__":
    caminho = input("Caminho da pasta: ")

    apagar_arquivos_xml(Path(caminho))

    ultima_pasta = Path(caminho).name
    print(ultima_pasta)

    for arquivo in Path(caminho).iterdir():
        if arquivo.suffix.lower().strip() == ".pdf":
            print("-" * 100)
            print(f'Processando arquivo: {arquivo.name}')
            dados = organizar_notas_fiscais(arquivo)
            print(f'Dados extraídos: \n{dados}')

            if not dados:
                continue

            try:
                if str(dados['operacao']) == 'venda':
                    nova_pasta = Path(caminho) / 'RECEITAS'
                elif str(dados['operacao']) == 'compra':
                    nova_pasta = Path(caminho) / 'DESPESAS'
                else:
                    nova_pasta = Path(caminho) / limpar_nome(dados.get('operacao', 'OUTROS')).upper()

                nova_pasta.mkdir(exist_ok=True, parents=True)

                # Cria nome limpo do arquivo
                base_nome = f"NF_{dados['num_nota']}_{dados['vendedor'].upper()}_X_{dados['comprador'].upper()}.pdf"
                base_nome = limpar_nome(base_nome)
                novo_nome = gerar_nome_unico(nova_pasta, base_nome)

                shutil.move(str(arquivo), str(novo_nome))
                print(f"Arquivo movido para: {novo_nome}")

            except Exception as e:
                print(f'Erro ao processar o arquivo {arquivo.name}: {e}')
                continue



print(dados['vendedor'].upper())
print(dados['comprador'].upper())
print("Fim do Programa.")
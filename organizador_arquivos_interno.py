from classes import Documento
from pathlib import Path
import json
import shutil
import unicodedata

"""
Organizador de arquivos baseado em IA.
Funcionalidades:
- Extrai texto de imagens/PDFs.
- Usa IA para identificar e classificar documentos.
- Move e renomeia arquivos conforme regras definidas.   
- Gera logs de operações.
"""


# Função para remover acentos e padronizar
def normalize(texto: str) -> str:
    if not texto:
        return "NAO_IDENTIFICADO"
    return ''.join(
        char for char in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(char) != 'Mn'
    ).upper().strip()

# Diretórios principais
diretorio_produtor_empregador = Path(r'\\DESKTOP-SP6JIVH\Users\User\Desktop\Arquivos Virtuais\CLIENTES\PRODUTOR RURAL EMPREGADOR')
diretorio_produtor_pequeno = Path(r'\\DESKTOP-SP6JIVH\Users\User\Desktop\Arquivos Virtuais\CLIENTES\PRODUTOR RURAL PEQUENO')
pasta_atual = Path(r'\\Desktop-d6hoejd\scan')

# Listas de produtores normalizadas
lista_empregadores = [normalize(pasta.name) for pasta in diretorio_produtor_empregador.iterdir() if pasta.is_dir()]
lista_pequenos = [normalize(pasta.name) for pasta in diretorio_produtor_pequeno.iterdir() if pasta.is_dir()]

qtdade_arquivos = 0

# Loop principal
for arquivo in pasta_atual.iterdir():
    if arquivo.suffix.lower() in ('.pdf', '.jpg', '.docx', '.doc'):
        try:
            print('-'*100)
            print(f'Processando arquivo: {arquivo.name}')
            qtdade_arquivos += 1

            documento = Documento(arquivo)

            texto = documento.extrair_texto_de_imagem()
            data_list_str = json.dumps(texto, indent=2)

            prompt = f"""
                Você receberá uma lista chamada `data_list`, contendo todo tipo de arquivo. 
                Eu preciso que você extraia os seguintes campos de cada item:

                - tipo_documento
                - numero_documento
                - nome_empregador
                - cpf_cnpj_empregador
                - nome_cliente
                - cpf_cnpj_funcionario
                - competencia (no formato MM-AAAA)

                 OBSERVAÇÃO:
                - para recibos de salários/holerites retorne recibo_salario.
                Regras:
                - Tudo em minúsculas, sem acentos.
                - O resultado final deve ser JSON.
                - Se não encontrar um campo, retorne None.


                Dados extraídos:
                {data_list_str}
            """

            resposta = documento.resposta_ia(data_list_str, prompt)
            resposta_tratada = documento.tratar_dados(resposta)

            if isinstance(resposta_tratada, list) and resposta_tratada:
                resposta_tratada = resposta_tratada[0]

            print(f'Dados extraídos: \n{resposta_tratada}')
            

            # Normalizando valores extraídos
            tipo_documento = normalize(resposta_tratada.get('tipo_documento'))
            numero_documento = normalize(resposta_tratada.get('numero_documento'))
            nome_empregador = normalize(resposta_tratada.get('nome_empregador'))
            nome_cliente = normalize(resposta_tratada.get('nome_cliente'))
            competencia = normalize(resposta_tratada.get('competencia'))

            # 🔹 Regra especial: recibo de salário
            if tipo_documento == "RECIBO_SALARIO":
                nova_pasta = pasta_atual / nome_empregador
                nova_pasta.mkdir(exist_ok=True, parents=True)
                novo_nome = pasta_atual / f"RECIBO_{nome_cliente}_{competencia}{arquivo.suffix}"

            # 🔹 Empregadores
            elif nome_empregador in lista_empregadores:
                nova_pasta = pasta_atual / nome_empregador
                nova_pasta.mkdir(exist_ok=True, parents=True)
                novo_nome = pasta_atual / f"{tipo_documento}_{nome_cliente}_{competencia}{arquivo.suffix}"

            # 🔹 Pequenos produtores
            elif nome_cliente in lista_pequenos:
                nova_pasta = pasta_atual / nome_cliente
                nova_pasta.mkdir(exist_ok=True, parents=True)
                novo_nome = pasta_atual / f"{tipo_documento}_{nome_cliente}_{competencia}{arquivo.suffix}"

            # 🔹 Indefinidos
            else:
                nova_pasta = pasta_atual / "INDEFINIDO"
                nova_pasta.mkdir(exist_ok=True, parents=True)
                novo_nome = pasta_atual / f"{tipo_documento}_{numero_documento}_{nome_cliente}_{competencia}{arquivo.suffix}"
                        # Cria pasta de destino
            nova_pasta.mkdir(exist_ok=True, parents=True)

            # Renomeia
            print(f"Renomeando arquivo {arquivo.name} para {novo_nome.name}")
            arquivo.rename(novo_nome)

            # Copia para a pasta destino
            destino = nova_pasta / novo_nome.name
            if not destino.exists():
                shutil.move(novo_nome, destino)
            else:
                print(f"O arquivo {destino} já existe e não será copiado.")

        except Exception as e:
            print(f'Erro ao processar o arquivo {arquivo.name}: {e}')
    

print(f'Quantidade de arquivos processados: {qtdade_arquivos}')
print('FIM DO PROGRAMA')

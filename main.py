from classes import Documento
from pathlib import Path
import pandas as pd
import json
import shutil

# diretorio = Path(input('Pasta onde deve ser alterado os arquivos: '))
# diretorio = Path(r'\\DESKTOP-SP6JIVH\Users\User\Desktop\Arquivos Virtuais\CLIENTES\PRODUTOR RURAL EMPREGADOR\VALDENIR PINHEIRO CANGUSSU\DIRPF\2025\DESPESAS\CONTAS DE ENERGIA\3007191213')
diretorio = Path(input('Digite o path do diretório: '))
diretorio_produtor = Path(r'\\DESKTOP-SP6JIVH\Users\User\Desktop\Arquivos Virtuais\CLIENTES')
nome_planilha = 'ALOISIO'
# i_estadual = str(input("Informe a inscrição estadual: "))
i_estadual = '0'
lista_lancamentos = []
cont = 1
total = [i for i in diretorio.iterdir() if i.suffix in ('.pdf', '.jpg', '.docx', '.doc')]
print(F'TOTAL DE ITENS À SEREM ANALISADOS: {len(total)}.')

# Escolher onde será feito a verificação das pastas
esc_tipo_produtor = 's'
if esc_tipo_produtor in ['s', 'n']:
    if esc_tipo_produtor == 's':
        tipo_produtor = 'PRODUTOR RURAL EMPREGADOR' 
    elif esc_tipo_produtor == 'n':
        tipo_produtor = 'PRODUTOR RURAL PEQUENO'
base_destino = diretorio_produtor / tipo_produtor
for arquivo in diretorio.iterdir():
    if arquivo.suffix in ('.pdf', '.jpg', '.docx', '.doc'):
        try:
            print(f'Processando arquivo: {arquivo.name}')
            print(f'Arquivo {cont}/{len(total)}\n')
            cont += 1

            documento = Documento(arquivo)

            texto = documento.extrair_texto_de_imagem()
            data_list_str = json.dumps(texto, indent=2)


            prompt = f"""
                    Você receberá uma lista chamada `data_list`, contendo textos extraídos de imagens de comprovantes de pagamentos. 
                    Os valores monetários sempre estarão no formato brasileiro: 000.000.000,00.
                    Sua tarefa é analisar cada item da lista e extrair as seguintes informações padronizadas, formatando o resultado em JSON.

                    [CAMPOS PADRÃO – para todos os documentos]

                    Extraia e mostre os seguintes dados:
                    - nome_cliente: nome do cliente
                    - tipo_documento: (fgts/darf/DCTF WEB/tributos_federais/energia_eletrica/contrato/honorarios/DAE/NFSe)Qualquer outro documento que
                    nao esteja dentro desse escopo, classifique-o como 'nao_classificado'. Todos em 'minúsculos'
                    - cnpj_cpf_prestador: CNPJ ou CPF do prestador/fornecedor.
                    - numero_documento: Número ou identificador do documento.
                    - competencia: Formato "mm-aaaa". Para documentos do tipo "darf", utilize a **data de apuração** como competência.
                    - data_arrecadacao: Data de recebimento/pagamento(dd/mm/aaaa):
                    - valor_total(R$)(coloque no formato de moeda brasileira), exemplo: "R$ 1.234,56".     

                    [CAMPOS ADICIONAIS POR TIPO DE DOCUMENTO]
                    → FGTS:
                    - subtipo: "mensal" ou "rescisorio".

                    Se for energia eletrica adicione os seguintes campos:
                    → energia_eletrica:
                    - numero_instalacao: Número da instalação elétrica.
                    - classe: Classe de consumo.
                    - subclasse: Subclasse de consumo.
                    - nome_da_fazenda: Somente o nome da fazenda, sem números, barras ou outros caracteres.
                    - cnpj_cpf_prestador: CNPJ da fornecedora de energia.
                    - data_arrecadacao: Use a data do campo "vencimento" (formato "dd/mm/aaaa").

                    
                    → honorarios:
                    - valor_total: Deve ser apenas o valor dos honorários contábeis, **sem incluir outros valores** (ex: impostos, encargos, etc.).

                    → DAE:
                    - obs_nota_fiscal: Extraia o conteúdo do campo de observação que contenha a expressão "NOTA FISCAL".

                    → NFSe ou contrato:
                    - chave_acesso: Chave de acesso da nota.
                    - tipo_de_servico: Tipo de serviço prestado.
                    - nome_prestador: Nome do prestador.
                    - cnpj_cpf_prestador: CNPJ ou CPF do prestador.
                    - endereco_tomador: Endereço do tomador do serviço (somente o nome da rua, sem números ou caracteres especiais).
                    - n_nota: Número da nota fiscal.
                    - endereco_fazenda: Nome da fazenda onde o serviço foi prestado (sem números ou símbolos).
                    - vencimento: Considere como a data de pagamento (formato "dd/mm/aaaa").

                    → recibo:
                    - nome_prestador: Nome do prestador.
                    - tipo_de_servico: Tipo de serviço prestado.
                    - cnpj_cpf_prestador: CNPJ ou CPF do prestador.
                    - endereco_tomador: Endereço do tomador do serviço (sem números ou caracteres especiais).
                    - endereco_fazenda: Nome da fazenda onde o serviço foi prestado (apenas o nome).
                    - competencia: Utilize a data de arrecadação (formato "mm-aaaa").

                    ---

                    Regras adicionais:
                    - O resultado final deve ser um ou mais objetos JSON com todos os campos aplicáveis preenchidos.
                    - Não exiba o conteúdo da variável `data_list`.
                    - Não mostre nenhuma linha de código, apenas o JSON formatado.
                    - Se um campo não for encontrado, simplesmente omita-o do JSON (não coloque nulo ou vazio).

                    Dados extraídos:
                    {data_list_str}
            """
        
            resposta = documento.resposta_ia(data_list_str, prompt)
            resposta_tratada = documento.tratar_dados(resposta)
            if isinstance(resposta_tratada, list) and resposta_tratada:
                resposta_tratada = resposta_tratada[0]
            print(f'Dados extraídos: \n{resposta_tratada}')
            print('-'*128)
            # Definindo todos os atributos da classe.
            documento.definir_atributos(resposta_tratada)

            classe = resposta_tratada['classe'].lower()
            if documento.tipo_documento == 'nao_identificado':
                print("Arquivo não identificado. Acessar o prompt para ajustar as configurações e criar uma condição ")
            elif documento.tipo_documento == 'energia_eletrica' and classe == 'rural':
                cpf_cnpj = documento.cpf_cnpj_prestador
                tipo_documento = 'Nota Fiscal'
                historico = f'PAGAMENTO DE CONTA DE ENERGIA ELÉTRICA, N° DA NF3e: {documento.num_documento} NO VALOR DE {documento.valor} REAIS. COMPETÊNCIA: {documento.competencia}. INSTALAÇÃO: {resposta_tratada['numero_instalacao']}.'
                plano_contas = 'ÁGUA, LUZ, TELEFONE OU INTERNET'
                tipo_lancamento = 'Lançamento de Energia elétrica de '

            elif documento.tipo_documento == 'honorarios':
                tipo_documento = 'Folha de pagamento'
                historico = f'Pagamento de Honorários Contábeis à AC CONTABILIDADE LTDA: Competencia: {documento.competencia}.'
                plano_contas = 'SERVIÇOS TERCEIRIZADOS (CONTABILIDADE, AGRONOMO, VETERINÁRIO)'
                if documento.cpf_cnpj == None:
                    documento.cpf_cnpj = '23.931.886/0001-92'
                tipo_lancamento = 'Lançamento de honorários de '
                nome_planilha = resposta_tratada['nome_cliente']

            elif documento.tipo_documento == 'fgts':
                cpf_cnpj = '00.360.305/0001-04'
                nome_planilha = resposta_tratada['nome_cliente']
                tipo_lancamento = 'Lançamento de FGTS de '
                tipo_documento = 'Folha de pagamento'
                # Variáveis para a manipulção dos diretórios e renomeação do arquivo
                departamento = 'DEPARTAMENTO PESSOAL'
                n1 = 'ENCARGOS'
                n2 = 'FGTS'
                novo_nome = f'{tipo_documento} {resposta_tratada['competencia']}{extensao}'
                if arquivo.name == novo_nome:
                    nome_arquivo = arquivo.name
                if resposta_tratada['subtipo'] == 'rescisorio':
                    historico = f'PAGAMENTO DE FGTS RESCISÓRIO DE , NO VALOR DE R${documento.valor}, COMPETÊNCIA: {documento.competencia}, DOCUMENTO Nº: {documento.num_documento}.'
                    plano_contas = 'FGTS RESCISÓRIO'
                elif resposta_tratada['subtipo'] == 'mensal':
                    historico = f'PAGAMENTO DE FGTS MENSAL NO VALOR DE R${documento.valor}, COMPETÊNCIA: {documento.competencia}, DOCUMENTO Nº: {documento.num_documento}.'
                    plano_contas = 'FGTS MENSAL'
            
            elif documento.tipo_documento.lower() == 'dae':
                tipo_documento = 'Recibo'
                historico = f'Pagamento de ICMS referente a Venda de Madeira. observação: {resposta_tratada['obs_nota_fiscal'].lower()}.'
                plano_contas = 'ICMS'
                if documento.cpf_cnpj == None:
                    documento.cpf_cnpj = '23.931.886/0001-92'
                tipo_lancamento = 'Lançamento de ICMS de '

            elif documento.tipo_documento == 'NFSe' or documento.tipo_documento == 'contrato' or documento.tipo_documento == 'recibo':
                if documento.tipo_documento == 'contrato':
                    tipo_documento = 'Contrato'
                    historico = f'CONTRATO REFERENTE A PRESTAÇÃO DE SERVIÇOS POR {resposta_tratada['nome_prestador'].upper()}, CNPJ/CPF: {resposta_tratada['cnpj_cpf_prestador']}, NO VALOR DE {documento.valor} NA FAZENDA {resposta_tratada['endereco_fazenda']}.'
                    tipo = 'Contrato de prestação'
                elif documento.tipo_documento == 'recibo':
                    tipo_documento = 'recibo'
                    historico = f'RECIBO REFERENTE A PRESTAÇÃO DE SERVIÇOS de {resposta_tratada['tipo_de_servico'].upper()} por {resposta_tratada['nome_prestador'].upper()}, CNPJ/CPF: {resposta_tratada['cnpj_cpf_prestador']}, NO VALOR DE {documento.valor} NA FAZENDA {resposta_tratada['endereco_fazenda'].upper()}.'
                else:
                    if resposta_tratada.get('n_nota').startswith('0'):
                        resposta_tratada['n_nota'] = resposta_tratada['n_nota'].lstrip('0')
                    tipo_documento = 'Nota fiscal'
                    historico = f'NFSe nº {resposta_tratada['nome_cliente']} REFERENTE À {resposta_tratada['tipo_de_servico'].upper()} PRESTADOR POR {resposta_tratada['nome_prestador'].upper()}, CNPJ: {resposta_tratada['cnpj_cpf_prestador']}, NO VALOR DE {documento.valor} NA FAZENDA{resposta_tratada['cnpj_cpf_prestador']}.'
                documento.cpf_cnpj = resposta_tratada['cnpj_cpf_prestador']
                plano_contas = 'CUSTO COM SERVIÇOS DE BENFEITORIA E CONSTRUCOES (GALPOES, ESTRADAS, AÇUDE, ETC)'
                tipo_lancamento = 'Lançamento de notas-contratos de serviços de '


            dic_lancamento = {
            "valor": f'{documento.valor}',
            "tipo_documento": tipo_documento,
            "numero_documento": f'{documento.num_documento}',
            "cpf_cnpj": cpf_cnpj,
            "vencimento": f'{documento.data_arrecadacao}',
            "tipo_lancamento": 'Despesas de Custeio e Investimento',
            "i_estadual": f'{i_estadual}',
            "plano_contas": plano_contas,
            "historico": historico,
            "num_conta": 0,
            }
            dic_formatado = documento.lancamento_agronota(dic_lancamento)

            output_dir = Path('LANÇAMENTOS AGRONOTA')
            output_dir.mkdir(exist_ok=True, parents=True)
            cliente = resposta_tratada['nome_cliente']
            # Nome do arquivo Excel para o cliente
            cliente_file = output_dir / f"{cliente} - Lançamento Agronota.xlsx"

            # Verifica se o arquivo do cliente já existe
            if cliente_file.exists():
                df_existente = pd.read_excel(cliente_file, dtype=str)
                novo_df = pd.DataFrame([dic_formatado])
                df_atualizado = pd.concat([df_existente, novo_df], ignore_index=True)
            else:
                # Cria um DataFrame a partir do dicionário formatado
                df_atualizado = pd.DataFrame([dic_formatado])
            # Salva ou atualiza o arquivo Excel do cliente
            df_atualizado.to_excel(cliente_file, index=False)

            #######################################
            data = resposta_tratada['competencia']
            mes, ano = data.split("-")
            tipo_documento = resposta_tratada['tipo_documento'].upper()
            extensao = arquivo.suffix
            #Renomear arquivo
            arquivo.rename(arquivo.parent / novo_nome)
            print(novo_nome)
            if departamento == 'DEPARTAMENTO PESSOAL':
                destino_dp = base_destino / resposta_tratada['nome_cliente'] / departamento / n1 / n2 / ano
            elif departamento == 'DIRPF':
                destino_dp = base_destino / resposta_tratada['nome_cliente'] / departamento / n1 / n2 / n3

            destino_dp.mkdir(exist_ok=True, parents=True)
            n3=''
            try:
            #     extensao = arquivo.suffix
            #     if 'competencia' not in resposta_tratada:
            #         raise KeyError("A chave 'competencia' não existe em resposta_tratada.")
            #     if documento.tipo_documento == 'fgts':
            #         if resposta_tratada['subtipo'] == 'rescisorio':  
            #             renomear = f"{documento.tipo_documento.upper()} - RESCISÓRIO {resposta_tratada['competencia']}{extensao}" 
            #         elif resposta_tratada['subtipo'] == 'mensal': 
            #             renomear = f"{documento.tipo_documento.upper()} {resposta_tratada['competencia']}{extensao}" 
            #             pasta_cliente = Path(diretorio / cliente / 'FGTS')
            #     else:
            #         renomear = f"{resposta_tratada['competencia']}{extensao}"  

            #     if documento.tipo_documento == 'energia_eletrica': 
            #         renomear = f"{resposta_tratada['competencia']} - {resposta_tratada['numero_documento']}{extensao}"
            #         pasta_cliente = Path(diretorio / cliente / f'INSTALAÇÃO {resposta_tratada['numero_instalacao']}')
            #         pasta_cliente.mkdir(exist_ok=True, parents=True)
            #     else:
            #         pasta_cliente = Path(diretorio / cliente)
            #         pasta_cliente.mkdir(exist_ok=True)
                
            #     novo_nome = arquivo.with_name(renomear)
            #     arquivo.rename(novo_nome)

            #     origem = Path(diretorio / novo_nome.name)
            #     destino = Path(pasta_cliente / novo_nome.name)

            #     origem.rename(destino)
            # except Exception as e:
            #     print(f'Erro ao renomear/mover arquivo: {e}')
                origem = arquivo
                print(f'Operação realizada em: {destino_dp}')
                destino = destino_dp / novo_nome
                if not destino.exists():
                    shutil.copy(origem, destino)
                else:
                    print(f"Arquivo {arquivo.name} já existe no destino.")
            except Exception as e:
                print(e)
                
        except Exception as e:
            print(e)    
        
print(f'Quantidade de arquivos processados: {len(lista_lancamentos)}')
print('FIM DO PROGRAMA')
print('=-'*30)
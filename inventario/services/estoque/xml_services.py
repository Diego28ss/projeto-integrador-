import xmltodict
from django.db import transaction

@transaction.atomic
def processar_upload_xml(arquivo_xml):
    """
    Serviço que lê o ficheiro XML da NF-e, extrai os dados principais e
    deverá guardar na base de dados com o status 'Pendente'.
    """
    try:
        # Lê o ficheiro e converte o XML num dicionário Python
        conteudo = arquivo_xml.read()
        dados_dict = xmltodict.parse(conteudo)
        
        # O nó principal de uma NF-e chama-se 'nfeProc' e depois 'NFe' e 'infNFe'
        try:
            infNFe = dados_dict['nfeProc']['NFe']['infNFe']
        except KeyError:
            raise ValueError("O arquivo enviado não é um XML de NF-e válido ou autorizado.")

        # Extração do Cabeçalho e Fornecedor
        chave_acesso = infNFe['@Id'].replace('NFe', '')
        numero_nota = infNFe['ide']['nNF']
        serie_nota = infNFe['ide']['serie']
        data_emissao = infNFe['ide']['dhEmi'][:10] # Formato 'AAAA-MM-DD'
        
        fornecedor_nome = infNFe['emit']['xNome']
        fornecedor_cnpj = infNFe['emit']['CNPJ']
        
        valor_total = float(infNFe['total']['ICMSTot']['vNF'])

        return {
            "chave": chave_acesso,
            "numero": numero_nota,
            "fornecedor": fornecedor_nome,
            "total": valor_total
        }
        
    except Exception as e:
        raise ValueError(f"Falha ao ler os dados do XML: {str(e)}")
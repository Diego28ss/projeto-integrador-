import xmltodict
from django.db import transaction
from inventario.models.produtos.produto_models import Produtos

@transaction.atomic
def processar_upload_xml(arquivo_xml):
    """
    Serviço inteligente com RASTREADOR que lê o XML e printa no terminal
    exatamente o que está a acontecer nos bastidores da cascata de busca.
    """
    try:
        conteudo = arquivo_xml.read()
        dados_dict = xmltodict.parse(conteudo)
        
        try:
            infNFe = dados_dict['nfeProc']['NFe']['infNFe']
        except KeyError:
            raise ValueError("O arquivo enviado não é um XML de NF-e válido ou autorizado.")

        chave_acesso = infNFe['@Id'].replace('NFe', '')
        numero_nota = infNFe['ide']['nNF']
        fornecedor_nome = infNFe['emit']['xNome']
        valor_total = float(infNFe['total']['ICMSTot']['vNF'])

        itens_processados = []
        
        detalhes_xml = infNFe['det']
        if isinstance(detalhes_xml, dict):
            detalhes_xml = [detalhes_xml]
            
        print("\n" + "="*60)
        print(f"🔍 INICIANDO CASCATA DE BUSCA - NOTA: {numero_nota}")
        print("="*60)
            
        for det in detalhes_xml:
            prod = det['prod']
            
            codigo_fornecedor_xml = prod.get('cProd', '').strip()
            codigo_barras_xml = prod.get('cEAN', '').strip()
            descricao_xml = prod.get('xProd', '')
            qtd_xml = float(prod.get('qCom', '0'))
            
            if codigo_barras_xml.upper() == "SEM GTIN":
                codigo_barras_xml = ""
                
            produto_id_vinculado = None
            produto_nome_vinculado = None
            produto_cod_interno = None 
            
            print(f"\n🛒 Lendo XML -> Produto: {descricao_xml}")
            print(f"   -> cProd (XML): '{codigo_fornecedor_xml}' | cEAN (XML): '{codigo_barras_xml}'")
            
            # Tentativa 1: Buscar pelo Código do Fornecedor
            if codigo_fornecedor_xml:
                match = Produtos.objects.filter(cod_fornecedor__iexact=codigo_fornecedor_xml).first()
                if match:
                    produto_id_vinculado = match.id
                    produto_nome_vinculado = match.nome
                    produto_cod_interno = match.cod_interno
                    print(f"   ✅ SUCESSO: Encontrado na coluna 'cod_fornecedor' (ID: {match.id})")
            
            # Tentativa 2: Buscar pelo Código de Barras
            if not produto_id_vinculado and codigo_barras_xml:
                match = Produtos.objects.filter(cod_barras__iexact=codigo_barras_xml).first()
                if match:
                    produto_id_vinculado = match.id
                    produto_nome_vinculado = match.nome
                    produto_cod_interno = match.cod_interno
                    print(f"   ✅ SUCESSO: Encontrado na coluna 'cod_barras' (ID: {match.id})")
                    
            # Tentativa 3: Buscar pelo Código Interno (Muitas vezes o código foi salvo nesta coluna pelo usuário)
            if not produto_id_vinculado and codigo_fornecedor_xml:
                match = Produtos.objects.filter(cod_interno__iexact=codigo_fornecedor_xml).first()
                if match:
                    produto_id_vinculado = match.id
                    produto_nome_vinculado = match.nome
                    produto_cod_interno = match.cod_interno
                    print(f"   ✅ SUCESSO: Encontrado na coluna 'cod_interno' (ID: {match.id})")

            if not produto_id_vinculado:
                print("   ❌ FALHA: O produto não bateu com nenhuma coluna (Fornecedor, EAN ou Interno) no Banco de Dados.")
                
            itens_processados.append({
                'cProd': codigo_fornecedor_xml,
                'cEAN': codigo_barras_xml,
                'xProd': descricao_xml,
                'qCom': qtd_xml,
                'produto_vinculado_id': produto_id_vinculado,
                'produto_vinculado_nome': produto_nome_vinculado,
                'produto_vinculado_cod_interno': produto_cod_interno or '---',
                'status_vinculo': 'sucesso' if produto_id_vinculado else 'pendente'
            })

        print("="*60 + "\n")

        return {
            "chave": chave_acesso,
            "numero": numero_nota,
            "fornecedor": fornecedor_nome,
            "total": valor_total,
            "itens": itens_processados,
            "xml_puro": conteudo.decode('utf-8') if isinstance(conteudo, bytes) else conteudo
        }
        
    except Exception as e:
        raise ValueError(f"Falha ao processar os dados do XML: {str(e)}")
    
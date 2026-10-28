import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q
from inventario.models.produtos.produto_models import Produtos

def tela_conferencia_xml(request, chave):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    return render(request, 'inventario/conferencia_xml.html', {'chave': chave})

def api_buscar_produtos_xml(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'produtos': []})
    
    produtos = Produtos.objects.filter(
        Q(nome__icontains=query) | 
        Q(cod_interno__icontains=query) | 
        Q(cod_barras__icontains=query)
    ).filter(status='ATIVO')[:15]
    
    dados = [{
        'id': p.id, 
        'cod_interno': p.cod_interno or '---', 
        'nome': p.nome, 
        'estoque': p.estoque_atual
    } for p in produtos]
    
    return JsonResponse({'produtos': dados})

def api_vincular_produto_xml(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            produto = Produtos.objects.get(id=dados.get('produto_id'))
            
            # REGRA DE NEGÓCIO: Bloquear vínculo se o estoque for negativo
            if produto.estoque_atual < 0:
                return JsonResponse({
                    'status': 'erro', 
                    'mensagem': f'O produto "{produto.nome}" possui estoque negativo ({produto.estoque_atual}). Faça o ajuste de estoque no sistema antes de vinculá-lo.'
                })
            
            # Vincula o código do fornecedor da NF-e
            produto.cod_fornecedor = dados.get('cod_fornecedor')
            
            # Preenche NCM e CEST apenas se estiverem vazios no banco
            if not produto.ncm and dados.get('ncm'): 
                produto.ncm = dados.get('ncm')
            if not produto.cest and dados.get('cest'): 
                produto.cest = dados.get('cest')
                
            produto.save()
            return JsonResponse({'status': 'sucesso', 'cod_interno': produto.cod_interno, 'nome': produto.nome})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido'})

def api_cadastrar_produto_xml(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            # 1. Cria o produto com os dados que vieram da nota
            novo_produto = Produtos.objects.create(
                nome=dados.get('nome'),
                cod_barras=dados.get('cod_barras'),
                preco_custo=dados.get('preco_custo'),
                margem_lucro=dados.get('margem_lucro'),
                preco_venda=dados.get('preco_venda'),
                cod_fornecedor=dados.get('cod_fornecedor'),
                ncm=dados.get('ncm'),
                cest=dados.get('cest'),
                status='ATIVO',
                estoque_atual=0 # O estoque só sobe ao "Finalizar Entrada"
            )
            
            # 2. Regra de Negócio JB Tintas: cod_interno recebe o número do ID
            novo_produto.cod_interno = str(novo_produto.id)
            novo_produto.save()
            
            return JsonResponse({'status': 'sucesso', 'cod_interno': novo_produto.cod_interno, 'nome': novo_produto.nome})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido'})


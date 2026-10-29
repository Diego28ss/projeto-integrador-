import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q
from inventario.models.produtos.produto_models import Produtos
from inventario.models.clientes.cliente_models import Clientes
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.services.vendas import pdv_services
from inventario.services.clientes import pontos_services

def tela_pdv(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    produtos = Produtos.objects.exclude(status='INATIVO')
    vendedores = Usuarios.objects.all()
    clientes = Clientes.objects.all()

    context = {
        'produtos': produtos,
        'vendedores': vendedores,
        'vendedores_list': vendedores,
        'clientes': clientes,
        'pintores': clientes.filter(tipo__icontains='PINTOR'),
    }
    return render(request, 'inventario/pdv.html', context)

def api_consultar_pontos(request):
    cliente_id = request.GET.get('cliente_id')
    
    if cliente_id:
        try:
            cliente_id = int(cliente_id)
        except ValueError:
            cliente_id = None
            
    resultado = pontos_services.calcular_resgate_pontos(cliente_id)
    return JsonResponse(resultado)

def api_buscar_produtos(request):
    query = request.GET.get('q', '').strip()
    produtos = Produtos.objects.exclude(status='INATIVO')

    if query:
        palavras = query.split()
        for palavra in palavras:
            produtos = produtos.filter(
                Q(nome__icontains=palavra) |
                Q(cod_barras__icontains=palavra)
            )

    produtos = produtos[:50]
    resultados = [{'id': p.id, 'nome': p.nome, 'preco_venda': float(p.preco_venda), 'estoque_atual': p.estoque_atual, 'cod_barras': p.cod_barras or ''} for p in produtos]
    return JsonResponse({'produtos': resultados})

def api_salvar_venda(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            carrinho = dados.get('carrinho', [])
            status_venda = dados.get('status', 'VENDA')
            
            dados_venda = {
                'valor_total': dados.get('valor_final', 0),
                'valor_desconto': dados.get('desconto', 0),
                'vendedor': dados.get('vendedor', ''),
                'cliente_id': dados.get('cliente_id'),
                'indicante_id': dados.get('indicante_id'),
                'cupom_texto': json.dumps(carrinho)
            }

            venda_id = pdv_services.processar_nova_venda(
                dados_venda=dados_venda,
                carrinho=carrinho,
                status_venda=status_venda,
                # ATUALIZAÇÃO: Mudamos de int() para float() para aceitar os centavos perfeitamente!
                pontos_resgatados=float(dados.get('pontos_resgatados', 0.0)),
                valor_desconto_pontos=float(dados.get('valor_desconto_pontos', 0.0))
            )
            return JsonResponse({'status': 'sucesso', 'venda_id': venda_id})
            
        except ValueError as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
        except Exception as e:
            import traceback
            print(traceback.format_exc()) 
            return JsonResponse({'status': 'erro', 'mensagem': f'Erro interno: {str(e)}'})
            
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido.'})

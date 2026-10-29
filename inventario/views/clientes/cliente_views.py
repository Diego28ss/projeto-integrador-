from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from inventario.models.clientes.cliente_models import Clientes
from inventario.models.vendas.venda_models import ConfiguracaoPontos, Vendas
from inventario.services.clientes import cliente_services

def tela_consultar_clientes(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    query = request.GET.get('q', '')
    clientes = Clientes.objects.all()

    if query:
        clientes = clientes.filter(
            Q(nome__icontains=query) | Q(cpf__icontains=query) | Q(telefone__icontains=query)
        )

    context = {
        'clientes': clientes,
        'query': query,
        'conf_cliente': ConfiguracaoPontos.objects.filter(tipo_usuario='CLIENTE').first(),
        'conf_pintor': ConfiguracaoPontos.objects.filter(tipo_usuario='PINTOR').first()
    }
    return render(request, 'inventario/consultar_clientes.html', context)

def salvar_edicao_cliente(request):
    if request.method == 'POST':
        # Delega o salvamento pesado para o service
        cliente = cliente_services.salvar_dados_cliente(request.POST)
        messages.success(request, f"Ficha de {cliente.nome} salva com sucesso!")
    return redirect('tela_consultar_clientes')

def api_historico_cliente(request):
    # ATUALIZAÇÃO: Busca pelo ID do cliente
    cliente_id = request.GET.get('id')
    vendas = Vendas.objects.filter(cliente_id=cliente_id, status='VENDA').order_by('-id')
    historico = [{'id': v.id, 'data': v.data_venda.strftime('%d/%m/%Y %H:%M'), 'vendedor': v.vendedor, 'valor': float(v.valor_total)} for v in vendas]
    return JsonResponse({'historico': historico})

def excluir_cliente(request, id):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    try:
        cliente = Clientes.objects.get(id=id)
        cliente.delete()
    except Exception as e:
        print(f"Erro ao excluir cliente: {e}")
    return redirect('tela_consultar_clientes')

def api_extrato_pontos(request):
    cliente_id = request.GET.get('id')
    from inventario.models.clientes.cliente_models import HistoricoPontos
    
    registros = HistoricoPontos.objects.filter(cliente_id=cliente_id).order_by('-data_hora')
    extrato = []
    
    for r in registros:
        extrato.append({
            'data': r.data_hora.strftime('%d/%m/%Y %H:%M'),
            'tipo': r.tipo_operacao.replace('_', ' ').title(),
            'descricao': r.descricao,
            'pontos': r.pontos,
            'venda_id': r.venda_id if r.venda else None
        })
        
    return JsonResponse({'extrato': extrato})

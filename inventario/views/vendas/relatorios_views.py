import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from inventario.models.vendas.venda_models import Vendas
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.services.vendas import dashboard_services

def tela_relatorios(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    vendedor_filtro = request.GET.get('vendedor', '')
    status_filtro = request.GET.get('status', '')

    metricas = dashboard_services.obter_metricas_dashboard(vendedor_filtro, status_filtro)

    context = {
        'vendas': metricas['vendas_todas'],
        'vendedores': Usuarios.objects.all(),
        'filtros': {
            'vendedor': vendedor_filtro,
            'status': status_filtro,
        },
        'metricas': {
            'total_liquido': metricas['faturamento'],
            'qtd_vendas': metricas['qtd_vendas'],
            'qtd_orcamentos': metricas['qtd_orcamentos'],
            'ticket_medio': metricas['ticket_medio'],
        }
    }
    return render(request, 'inventario/relatorios.html', context)

def imprimir_cupom(request, id):
    venda = get_object_or_404(Vendas, id=id)

    try:
        carrinho = json.loads(venda.cupom_texto) if venda.cupom_texto else []
    except (ValueError, TypeError):
        carrinho = []

    subtotal_bruto = 0.0
    for item in carrinho:
        preco = float(item.get('preco', 0))
        qtd = int(item.get('qtd', 1))
        item['total_linha'] = preco * qtd
        subtotal_bruto += item['total_linha']

    contexto = {
        'venda': venda,
        'carrinho': carrinho,
        'itens': carrinho,
        'subtotal_bruto': subtotal_bruto
    }
    return render(request, 'inventario/cupom.html', contexto)

def imprimir_cupom_a4(request, id):
    venda = get_object_or_404(Vendas, id=id)

    try:
        carrinho = json.loads(venda.cupom_texto) if venda.cupom_texto else []
    except (ValueError, TypeError):
        carrinho = []

    subtotal_bruto = 0.0
    for item in carrinho:
        preco = float(item.get('preco', 0))
        qtd = int(item.get('qtd', 1))
        item['total_linha'] = preco * qtd
        subtotal_bruto += item['total_linha']

    contexto = {
        'venda': venda,
        'carrinho': carrinho,
        'itens': carrinho,
        'subtotal_bruto': subtotal_bruto
    }
    return render(request, 'inventario/cupom_a4.html', contexto)

def cancelar_venda(request):
    if request.method == 'POST':
        venda_id = request.POST.get('venda_id')
        login_auth = request.POST.get('login_autorizador', '').strip()
        senha_auth = request.POST.get('senha_autorizador', '').strip()
        motivo = request.POST.get('motivo', '').strip()

        autorizador = Usuarios.objects.filter(login=login_auth, senha=senha_auth).first()

        if autorizador:
            try:
                venda = Vendas.objects.get(id=venda_id)
                venda.status = 'CANCELADA'
                venda.save()
                messages.success(request, f"Venda #{venda_id} cancelada por {autorizador.login}. Motivo: {motivo}")
            except Exception as e:
                messages.error(request, f"Erro ao cancelar o documento: {e}")
        else:
            messages.error(request, "Cancelamento negado: Login ou Senha do autorizador estão incorretos.")

    return redirect('tela_relatorios')
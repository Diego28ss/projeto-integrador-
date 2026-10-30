import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from inventario.models.vendas.venda_models import Vendas
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.services.vendas import dashboard_services
from datetime import datetime
from django.utils import timezone

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

def tela_extrato_comissoes(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    # Se o link não enviou um vendedor específico, assume que é o usuário logado
    login_vendedor = request.GET.get('vendedor')
    if not login_vendedor:
        login_vendedor = request.session.get('usuario_logado')

    # RBAC: Se for Vendedor comum, ele só pode ver o próprio extrato!
    if request.session.get('perfil') != 'Administrador':
        if login_vendedor != request.session.get('usuario_logado'):
             messages.error(request, "Acesso Negado. Você só pode visualizar as suas próprias comissões.")
             return redirect('painel_principal')
    
    # Captura os filtros de mês e ano da URL
    mes_filtro = request.GET.get('mes')
    ano_filtro = request.GET.get('ano')

    # Se não mandou filtro, o padrão é o mês e o ano vigentes
    hoje = timezone.now()
    try:
        mes_atual = int(mes_filtro) if mes_filtro else hoje.month
        ano_atual = int(ano_filtro) if ano_filtro else hoje.year
    except ValueError:
        mes_atual, ano_atual = hoje.month, hoje.year

    # Puxa o objeto do usuário para sabermos qual o % de comissão
    vendedor_obj = get_object_or_404(Usuarios, login=login_vendedor)

    # O Filtro de Ouro: Vendas finalizadas, deste vendedor, neste mês e ano exatos
    vendas_mes = Vendas.objects.filter(
        vendedor=login_vendedor,
        status='VENDA',
        data_venda__year=ano_atual,
        data_venda__month=mes_atual
    ).order_by('data_venda')

    extrato_detalhado = []
    total_comissao_mes = 0.0

    for v in vendas_mes:
        # A economia total e o subtotal vêm da nota
        valor_liquido = float(v.valor_total)
        economia_total = float(v.valor_desconto)
        
        desc_pontos = float(v.valor_desconto_pontos)
        desc_comum = economia_total - desc_pontos

        subtotal = valor_liquido + economia_total
        
        # A comissão foi gravada nativamente na Fase 2
        comissao_gerada = float(v.valor_comissao)
        total_comissao_mes += comissao_gerada
        
        # Formata dados para exibição na tabela HTML
        extrato_detalhado.append({
            'cupom': v.id,
            'data': v.data_venda.strftime("%d/%m/%Y"),
            'cliente': v.cliente.nome if v.cliente else "BALCÃO",
            'indicante': v.indicante.nome if v.indicante else "-",
            'subtotal': subtotal,
            'desc_comum': desc_comum,
            'desc_pontos': desc_pontos,
            'liquido': valor_liquido,
            'comissao': comissao_gerada
        })
        
    context = {
        'vendedor': vendedor_obj,
        'extrato': extrato_detalhado,
        'mes_filtro': mes_atual,
        'ano_filtro': ano_atual,
        'total_comissao_mes': total_comissao_mes,
        'meses_range': range(1, 13) # Para gerar o <select> do HTML de 1 a 12
    }

    return render(request, 'inventario/extrato_comissoes.html', context)

def tela_relatorios_painel(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    
    return render(request, 'inventario/relatorios_painel.html')

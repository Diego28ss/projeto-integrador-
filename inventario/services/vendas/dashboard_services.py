from inventario.models.vendas.venda_models import Vendas
from inventario.models.usuarios.usuario_models import Usuarios
from django.db.models import Sum

def calcular_totais_colaboradores():
    lista_equipe = Usuarios.objects.all()

    for colaborador in lista_equipe:
        vendas_do_vendedor = Vendas.objects.filter(vendedor=colaborador.login, status='VENDA')

        total_vendido = 0.0
        for v in vendas_do_vendedor:
            try:
                total_vendido += float(v.valor_total)
            except (ValueError, TypeError):
                pass

        try:
            percentual_comissao = float(colaborador.comissao)
        except (ValueError, TypeError):
            percentual_comissao = 0.0

        comissao_a_pagar = (total_vendido * percentual_comissao) / 100

        colaborador.total_vendido = total_vendido
        colaborador.comissao_a_pagar = comissao_a_pagar

    return lista_equipe

def obter_metricas_dashboard(vendedor_filtro, status_filtro):
    vendas_todas = Vendas.objects.all().order_by('-id')

    if vendedor_filtro:
        vendas_todas = vendas_todas.filter(vendedor__iexact=vendedor_filtro)
    if status_filtro:
        vendas_todas = vendas_todas.filter(status=status_filtro)

    vendas_confirmadas = vendas_todas.filter(status='VENDA')
    orcamentos_todos = vendas_todas.filter(status='ORCAMENTO')

    resultado_soma = vendas_confirmadas.aggregate(total=Sum('valor_total'))
    faturamento = float(resultado_soma['total'] or 0.0)

    qtd_vendas = vendas_confirmadas.count()
    qtd_orcamentos = orcamentos_todos.count()
    ticket_medio = faturamento / qtd_vendas if qtd_vendas > 0 else 0.0

    return {
        'vendas_todas': vendas_todas,
        'faturamento': faturamento,
        'qtd_vendas': qtd_vendas,
        'qtd_orcamentos': qtd_orcamentos,
        'ticket_medio': ticket_medio,
    }
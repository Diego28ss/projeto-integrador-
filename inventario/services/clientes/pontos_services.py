from inventario.models.clientes.cliente_models import Clientes
from inventario.models.vendas.venda_models import ConfiguracaoPontos

def calcular_resgate_pontos(cliente_id):
    if not cliente_id:
        return {'pontos': 0, 'pontos_a_resgatar': 0, 'valor_desconto': 0.0, 'mensagem': 'Cliente não informado.'}

    cliente = Clientes.objects.filter(id=cliente_id).first()
    if not cliente:
        return {'pontos': 0, 'pontos_a_resgatar': 0, 'valor_desconto': 0.0, 'mensagem': 'Cliente não encontrado.'}

    if float(cliente.pontos) <= 0:
        return {
            'pontos': 0,
            'pontos_a_resgatar': 0,
            'valor_desconto': 0.0,
            'mensagem': 'Sem pontos acumulados.'
        }

    config = ConfiguracaoPontos.objects.first()
    divisor = float(config.divisor_resgate) if config else 100.0

    # ATUALIZAÇÃO: Garante que o JsonResponse consiga ler os decimais corretamente
    pontos_totais = float(cliente.pontos)
    valor_desconto = pontos_totais / divisor

    return {
        'pontos': round(pontos_totais, 2),
        'pontos_a_resgatar': round(pontos_totais, 2),
        'valor_desconto': round(valor_desconto, 2),
        'mensagem': f'Disponível: {pontos_totais:.2f} pts (R$ {valor_desconto:.2f})'
    }


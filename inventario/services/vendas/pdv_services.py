from django.db import transaction
from decimal import Decimal
from inventario.models.vendas.venda_models import Vendas, ConfiguracaoPontos
from inventario.models.produtos.produto_models import Produtos
from inventario.models.clientes.cliente_models import Clientes, HistoricoPontos
from inventario.models.usuarios.usuario_models import Usuarios

def processar_nova_venda(dados_venda, carrinho, status_venda, pontos_resgatados=0.0, valor_desconto_pontos=0.00):
    with transaction.atomic():
        cliente_id = dados_venda.get('cliente_id')
        indicante_id = dados_venda.get('indicante_id')
        vendedor_login = dados_venda.get('vendedor')
        
        valor_total = Decimal(str(dados_venda['valor_total']))

        # FASE 2: Calcular a comissão do vendedor sobre o valor líquido
        valor_comissao = Decimal('0.00')
        if vendedor_login and status_venda == 'VENDA':
            vendedor_obj = Usuarios.objects.filter(login=vendedor_login).first()
            if vendedor_obj:
                valor_comissao = vendedor_obj.calcular_comissao(valor_total)

        venda = Vendas.objects.create(
            valor_total=valor_total,
            valor_desconto=dados_venda['valor_desconto'],
            pontos_resgatados=pontos_resgatados,
            valor_desconto_pontos=valor_desconto_pontos,
            vendedor=vendedor_login,
            valor_comissao=valor_comissao, # Grava o valor da comissão na venda
            cliente_id=cliente_id,
            indicante_id=indicante_id,
            status=status_venda,
            cupom_texto=dados_venda['cupom_texto']
        )

        if status_venda == 'ORCAMENTO':
            return venda.id

        for item in carrinho:
            p_id = item.get('id') or item.get('produto_id')
            p_qtd = int(item.get('qtd', 0))

            if p_id and p_qtd > 0:
                produto = Produtos.objects.select_for_update().filter(id=p_id).first()
                if produto:
                    produto.estoque_atual -= p_qtd
                    produto.save()

        # -------------------------------------------------------------
        # 1. PROCESSAR RESGATE DE PONTOS
        # -------------------------------------------------------------
        if cliente_id and float(pontos_resgatados) > 0:
            cliente_obj = Clientes.objects.select_for_update().filter(id=cliente_id).first()
            if cliente_obj and float(cliente_obj.pontos) >= float(pontos_resgatados):
                cliente_obj.pontos = float(cliente_obj.pontos) - float(pontos_resgatados)
                cliente_obj.save()
                
                HistoricoPontos.objects.create(
                    cliente=cliente_obj,
                    venda=venda,
                    tipo_operacao='RESGATE',
                    pontos=-float(pontos_resgatados),
                    descricao=f"Resgate na Venda #{venda.id}"
                )

        # -------------------------------------------------------------
        # 2. GERAR NOVOS PONTOS
        # -------------------------------------------------------------
        if float(pontos_resgatados) == 0 and float(valor_desconto_pontos) == 0:
            
            valor_final_venda = float(dados_venda['valor_total'])

            if cliente_id:
                cliente_obj = Clientes.objects.select_for_update().filter(id=cliente_id).first()
                if cliente_obj:
                    config_cli = ConfiguracaoPontos.objects.filter(tipo_usuario='CLIENTE').first()
                    if config_cli:
                        novos_pontos = float(valor_final_venda) * float(config_cli.pontos_por_real)
                        if novos_pontos > 0:
                            cliente_obj.pontos = float(cliente_obj.pontos) + novos_pontos
                            cliente_obj.save()
                            
                            HistoricoPontos.objects.create(
                                cliente=cliente_obj,
                                venda=venda,
                                tipo_operacao='GANHO_CLIENTE',
                                pontos=novos_pontos,
                                descricao=f"Pontos de compra (Venda #{venda.id})"
                            )

            if indicante_id and indicante_id != cliente_id:
                pintor_obj = Clientes.objects.select_for_update().filter(id=indicante_id).first()
                if pintor_obj:
                    config_pin = ConfiguracaoPontos.objects.filter(tipo_usuario='PINTOR').first()
                    if config_pin:
                        pontos_indicacao = float(valor_final_venda) * float(config_pin.pontos_por_real)
                        if pontos_indicacao > 0:
                            pintor_obj.pontos = float(pintor_obj.pontos) + pontos_indicacao
                            pintor_obj.save()

                            nome_cliente = cliente_obj.nome if (cliente_id and cliente_obj) else "Cliente"
                            HistoricoPontos.objects.create(
                                cliente=pintor_obj,
                                venda=venda,
                                tipo_operacao='GANHO_INDICANTE',
                                pontos=pontos_indicacao,
                                descricao=f"Indicação da compra de {nome_cliente} (Venda #{venda.id})"
                            )

        return venda.id

def autorizar_cancelamento(venda_id, login_auth, senha_auth, motivo):
    autorizador = Usuarios.objects.filter(login=login_auth, senha=senha_auth).first()

    if autorizador:
        try:
            with transaction.atomic():
                venda = Vendas.objects.select_for_update().get(id=venda_id)
                
                if venda.status == 'CANCELADA':
                    return False, "Esta venda já está cancelada."
                    
                venda.status = 'CANCELADA'
                # Zera a comissão caso a venda seja cancelada
                venda.valor_comissao = Decimal('0.00') 
                venda.save()
                
                historicos = HistoricoPontos.objects.filter(venda=venda)
                
                for hist in historicos:
                    cliente = Clientes.objects.select_for_update().get(id=hist.cliente_id)
                    
                    if hist.pontos > 0:
                        cliente.pontos = max(0.0, float(cliente.pontos) - float(hist.pontos))
                        HistoricoPontos.objects.create(
                            cliente=cliente,
                            venda=venda,
                            tipo_operacao='ESTORNO_GANHO',
                            pontos=-hist.pontos,
                            descricao=f"motivo venda {venda.id} cancelada"
                        )
                        
                    elif hist.pontos < 0:
                        pontos_devolvidos = abs(float(hist.pontos))
                        cliente.pontos = float(cliente.pontos) + pontos_devolvidos
                        HistoricoPontos.objects.create(
                            cliente=cliente,
                            venda=venda,
                            tipo_operacao='ESTORNO_RESGATE',
                            pontos=pontos_devolvidos,
                            descricao=f"motivo estorno de pontos da venda {venda.id} cancelada"
                        )
                    
                    cliente.save()
                    
            return True, f"Venda #{venda_id} cancelada por {autorizador.login}. Motivo: {motivo}"
        except Exception as e:
            return False, f"Erro ao cancelar a venda: {str(e)}"

    return False, "Cancelamento Negado: Login ou Senha do autorizador incorretos."

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

    pontos_totais = float(cliente.pontos)
    valor_desconto = pontos_totais / divisor

    return {
        'pontos': round(pontos_totais, 2),
        'pontos_a_resgatar': round(pontos_totais, 2),
        'valor_desconto': round(valor_desconto, 2),
        'mensagem': f'Disponível: {pontos_totais:.2f} pts (R$ {valor_desconto:.2f})'
    }

from django.db import transaction
from inventario.models.vendas.venda_models import Vendas, ConfiguracaoPontos
from inventario.models.produtos.produto_models import Produtos
from inventario.models.clientes.cliente_models import Clientes, HistoricoPontos
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.models.vendas.venda_models import ConfiguracaoPontos


def processar_nova_venda(dados_venda, carrinho, status_venda, pontos_resgatados=0.0, valor_desconto_pontos=0.00):
    with transaction.atomic():
        cliente_id = dados_venda.get('cliente_id')
        indicante_id = dados_venda.get('indicante_id')

        venda = Vendas.objects.create(
            valor_total=dados_venda['valor_total'],
            valor_desconto=dados_venda['valor_desconto'],
            pontos_resgatados=pontos_resgatados,
            valor_desconto_pontos=valor_desconto_pontos,
            vendedor=dados_venda['vendedor'],
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
        if cliente_id and pontos_resgatados > 0:
            cliente_obj = Clientes.objects.select_for_update().filter(id=cliente_id).first()
            if cliente_obj and float(cliente_obj.pontos) >= pontos_resgatados:
                cliente_obj.pontos = float(cliente_obj.pontos) - pontos_resgatados
                cliente_obj.save()
                
                HistoricoPontos.objects.create(
                    cliente=cliente_obj,
                    venda=venda,
                    tipo_operacao='RESGATE',
                    pontos=-pontos_resgatados,
                    descricao=f"Resgate na Venda #{venda.id}"
                )

        # -------------------------------------------------------------
        # 2. GERAR NOVOS PONTOS
        # -------------------------------------------------------------
        if pontos_resgatados == 0 and valor_desconto_pontos == 0:
            
            valor_final_venda = float(dados_venda['valor_total'])

            if cliente_id:
                cliente_obj = Clientes.objects.select_for_update().filter(id=cliente_id).first()
                if cliente_obj:
                    config_cli = ConfiguracaoPontos.objects.filter(tipo_usuario='CLIENTE').first()
                    if config_cli:
                        # ATUALIZAÇÃO: Multiplicando decimais usando float para considerar os centavos
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
                        # ATUALIZAÇÃO: Mesma matemática fracionada aplicada ao Pintor
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

    if cliente.pontos <= 0:
        return {
            'pontos': 0,
            'pontos_a_resgatar': 0,
            'valor_desconto': 0.0,
            'mensagem': 'Sem pontos acumulados.'
        }

    # Busca a configuração para saber o divisor universal (ex: 100)
    config = ConfiguracaoPontos.objects.first()
    divisor = config.divisor_resgate if config else 100

    pontos_totais = cliente.pontos
    valor_desconto = pontos_totais / divisor

    return {
        'pontos': pontos_totais,
        'pontos_a_resgatar': pontos_totais,
        'valor_desconto': round(valor_desconto, 2),
        'mensagem': f'Disponível: {pontos_totais} pts (R$ {valor_desconto:.2f})'
    }

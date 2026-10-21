from django.db import transaction
from inventario.models.vendas.venda_models import Vendas, ConfiguracaoPontos
from inventario.models.produtos.produto_models import Produtos
from inventario.models.clientes.cliente_models import Clientes
from inventario.models.usuarios.usuario_models import Usuarios

def processar_nova_venda(dados_venda, carrinho, status_venda, pontos_resgatados):
    with transaction.atomic():
        venda = Vendas.objects.create(
            valor_total=dados_venda['valor_total'],
            valor_desconto=dados_venda['valor_desconto'],
            vendedor=dados_venda['vendedor'],
            cliente=dados_venda['cliente'],
            indicante=dados_venda['indicante'],
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

        nome_cliente = dados_venda.get('cliente')
        if nome_cliente:
            cliente_obj = Clientes.objects.filter(nome=nome_cliente).first()
            if cliente_obj:
                if pontos_resgatados > 0:
                    cliente_obj.pontos = max(0, cliente_obj.pontos - pontos_resgatados)

                config_cli = ConfiguracaoPontos.objects.filter(tipo_usuario='CLIENTE').first()
                if config_cli:
                    novos_pontos = int(float(dados_venda['valor_total']) * config_cli.pontos_por_real)
                    cliente_obj.pontos += novos_pontos
                cliente_obj.save()

        nome_indicante = dados_venda.get('indicante')
        if nome_indicante and nome_indicante != nome_cliente:
            pintor_obj = Clientes.objects.filter(nome=nome_indicante, tipo__icontains='PINTOR').first()
            if pintor_obj:
                config_pin = ConfiguracaoPontos.objects.filter(tipo_usuario='PINTOR').first()
                if config_pin:
                    pontos_indicacao = int(float(dados_venda['valor_total']) * config_pin.pontos_por_real)
                    pintor_obj.pontos += pontos_indicacao
                    pintor_obj.save()

        return venda.id

def autorizar_cancelamento(venda_id, login_auth, senha_auth, motivo):
    autorizador = Usuarios.objects.filter(login=login_auth, senha=senha_auth).first()

    if autorizador:
        try:
            venda = Vendas.objects.get(id=venda_id)
            venda.status = 'CANCELADA'
            venda.save()
            return True, f"Venda #{venda_id} cancelada por {autorizador.login}. Motivo: {motivo}"
        except Exception as e:
            return False, f"Erro ao cancelar o documento: {str(e)}"

    return False, "Cancelamento Negado: Login ou Senha do autorizador estão incorretos."
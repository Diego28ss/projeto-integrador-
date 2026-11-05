from decimal import Decimal

from django.test import TestCase

from inventario.models.clientes.cliente_models import Clientes
from inventario.models.vendas.venda_models import ConfiguracaoPontos
from inventario.services.clientes.pontos_services import calcular_resgate_pontos


class CalcularResgatePontosTests(TestCase):
    def test_retorna_mensagem_quando_cliente_nao_informado(self):
        resultado = calcular_resgate_pontos(None)

        self.assertEqual(resultado["mensagem"], "Cliente não informado.")
        self.assertEqual(resultado["valor_desconto"], 0.0)

    def test_retorna_mensagem_quando_cliente_nao_encontrado(self):
        resultado = calcular_resgate_pontos(999)

        self.assertEqual(resultado["mensagem"], "Cliente não encontrado.")
        self.assertEqual(resultado["pontos"], 0)

    def test_retorna_mensagem_quando_cliente_nao_tem_pontos(self):
        cliente = Clientes.objects.create(nome="Cliente sem pontos")

        resultado = calcular_resgate_pontos(cliente.id)

        self.assertEqual(resultado["mensagem"], "Sem pontos acumulados.")
        self.assertEqual(resultado["pontos_a_resgatar"], 0)

    def test_calcula_desconto_com_divisor_configurado(self):
        cliente = Clientes.objects.create(
            nome="Cliente fidelidade",
            pontos=Decimal("250.00"),
        )
        ConfiguracaoPontos.objects.create(
            tipo_usuario="CLIENTE",
            divisor_resgate=Decimal("50.00"),
        )

        resultado = calcular_resgate_pontos(cliente.id)

        self.assertEqual(resultado["pontos"], 250.0)
        self.assertEqual(resultado["pontos_a_resgatar"], 250.0)
        self.assertEqual(resultado["valor_desconto"], 5.0)

    def test_usa_divisor_padrao_quando_nao_ha_configuracao(self):
        cliente = Clientes.objects.create(
            nome="Cliente regra padrão",
            pontos=Decimal("200.00"),
        )

        resultado = calcular_resgate_pontos(cliente.id)

        self.assertEqual(resultado["valor_desconto"], 2.0)

from decimal import Decimal

from django.test import TestCase

from inventario.models.usuarios.usuario_models import Usuarios
from inventario.models.vendas.venda_models import Vendas
from inventario.services.vendas.dashboard_services import (
    calcular_totais_colaboradores,
    obter_metricas_dashboard,
)


class DashboardServicesTests(TestCase):
    def setUp(self):
        self.vendedor = Usuarios.objects.create(
            login="vendedor",
            senha="senha",
            comissao=Decimal("10.00"),
        )
        Vendas.objects.create(
            vendedor=self.vendedor.login,
            valor_total=Decimal("100.00"),
            status="VENDA",
        )
        Vendas.objects.create(
            vendedor=self.vendedor.login,
            valor_total=Decimal("50.00"),
            status="VENDA",
        )
        Vendas.objects.create(
            vendedor=self.vendedor.login,
            valor_total=Decimal("80.00"),
            status="ORCAMENTO",
        )
        Vendas.objects.create(
            vendedor=self.vendedor.login,
            valor_total=Decimal("40.00"),
            status="CANCELADA",
        )

    def test_metricas_consideram_vendas_confirmadas_e_orcamentos(self):
        resultado = obter_metricas_dashboard(None, None)

        self.assertEqual(resultado["faturamento"], 150.0)
        self.assertEqual(resultado["qtd_vendas"], 2)
        self.assertEqual(resultado["qtd_orcamentos"], 1)
        self.assertEqual(resultado["ticket_medio"], 75.0)

    def test_filtro_de_vendedor_limita_vendas_consideradas(self):
        resultado = obter_metricas_dashboard("outro-vendedor", None)

        self.assertEqual(resultado["faturamento"], 0.0)
        self.assertEqual(resultado["qtd_vendas"], 0)
        self.assertEqual(resultado["ticket_medio"], 0.0)

    def test_comissao_considera_apenas_vendas_finalizadas(self):
        colaboradores = {
            colaborador.login: colaborador
            for colaborador in calcular_totais_colaboradores()
        }

        vendedor = colaboradores[self.vendedor.login]
        self.assertEqual(vendedor.total_vendido, 150.0)
        self.assertEqual(vendedor.comissao_a_pagar, 15.0)

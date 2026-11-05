from decimal import Decimal

from django.test import TestCase

from inventario.models.clientes.cliente_models import Clientes, HistoricoPontos
from inventario.models.produtos.produto_models import Produtos
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.models.vendas.venda_models import ConfiguracaoPontos, Vendas
from inventario.services.vendas.pdv_services import (
    autorizar_cancelamento,
    processar_nova_venda,
)


class ProcessarNovaVendaTests(TestCase):
    def setUp(self):
        self.cliente = Clientes.objects.create(nome="Cliente teste")
        self.produto = Produtos.objects.create(
            nome="Tinta teste",
            preco_venda=Decimal("50.00"),
            estoque_atual=10,
        )
        self.vendedor = Usuarios.objects.create(
            login="vendedor",
            senha="senha",
            comissao=Decimal("5.00"),
        )
        ConfiguracaoPontos.objects.create(
            tipo_usuario="CLIENTE",
            pontos_por_real=Decimal("1.00"),
        )

    def dados_venda(self, **overrides):
        dados = {
            "cliente_id": self.cliente.id,
            "indicante_id": None,
            "vendedor": self.vendedor.login,
            "valor_total": "100.00",
            "valor_desconto": "0.00",
            "cupom_texto": "",
        }
        dados.update(overrides)
        return dados

    def test_venda_finalizada_atualiza_estoque_pontos_e_comissao(self):
        venda_id = processar_nova_venda(
            self.dados_venda(),
            [{"id": self.produto.id, "qtd": 2}],
            "VENDA",
        )

        self.produto.refresh_from_db()
        self.cliente.refresh_from_db()
        venda = Vendas.objects.get(id=venda_id)

        self.assertEqual(self.produto.estoque_atual, 8)
        self.assertEqual(self.cliente.pontos, Decimal("100.00"))
        self.assertEqual(venda.valor_comissao, Decimal("5.00"))
        self.assertTrue(
            HistoricoPontos.objects.filter(
                cliente=self.cliente,
                venda=venda,
                tipo_operacao="GANHO_CLIENTE",
                pontos=Decimal("100.00"),
            ).exists()
        )

    def test_orcamento_nao_atualiza_estoque_pontos_ou_comissao(self):
        venda_id = processar_nova_venda(
            self.dados_venda(),
            [{"id": self.produto.id, "qtd": 2}],
            "ORCAMENTO",
        )

        self.produto.refresh_from_db()
        self.cliente.refresh_from_db()
        venda = Vendas.objects.get(id=venda_id)

        self.assertEqual(self.produto.estoque_atual, 10)
        self.assertEqual(self.cliente.pontos, Decimal("0.00"))
        self.assertEqual(venda.valor_comissao, Decimal("0.00"))
        self.assertFalse(HistoricoPontos.objects.filter(venda=venda).exists())

    def test_resgate_de_pontos_debita_saldo_e_registra_historico(self):
        self.cliente.pontos = Decimal("200.00")
        self.cliente.save()

        venda_id = processar_nova_venda(
            self.dados_venda(valor_total="20.00"),
            [],
            "VENDA",
            pontos_resgatados=100,
            valor_desconto_pontos=1,
        )

        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.pontos, Decimal("100.00"))
        self.assertTrue(
            HistoricoPontos.objects.filter(
                cliente=self.cliente,
                venda_id=venda_id,
                tipo_operacao="RESGATE",
                pontos=Decimal("-100.00"),
            ).exists()
        )


class AutorizarCancelamentoTests(TestCase):
    def setUp(self):
        self.cliente = Clientes.objects.create(nome="Cliente teste")
        self.autorizador = Usuarios.objects.create(
            login="gerente",
            senha="senha-segura",
        )
        ConfiguracaoPontos.objects.create(
            tipo_usuario="CLIENTE",
            pontos_por_real=Decimal("1.00"),
        )
        self.venda_id = processar_nova_venda(
            {
                "cliente_id": self.cliente.id,
                "indicante_id": None,
                "vendedor": None,
                "valor_total": "100.00",
                "valor_desconto": "0.00",
                "cupom_texto": "",
            },
            [],
            "VENDA",
        )

    def test_cancelamento_autorizado_estorna_pontos_e_comissao(self):
        autorizado, _ = autorizar_cancelamento(
            self.venda_id,
            self.autorizador.login,
            self.autorizador.senha,
            "Teste automatizado",
        )

        self.cliente.refresh_from_db()
        venda = Vendas.objects.get(id=self.venda_id)

        self.assertTrue(autorizado)
        self.assertEqual(self.cliente.pontos, Decimal("0.00"))
        self.assertEqual(venda.status, "CANCELADA")
        self.assertEqual(venda.valor_comissao, Decimal("0.00"))
        self.assertTrue(
            HistoricoPontos.objects.filter(
                venda=venda,
                tipo_operacao="ESTORNO_GANHO",
                pontos=Decimal("-100.00"),
            ).exists()
        )

    def test_cancelamento_com_credenciais_invalidas_e_negado(self):
        autorizado, mensagem = autorizar_cancelamento(
            self.venda_id,
            self.autorizador.login,
            "senha-incorreta",
            "Teste automatizado",
        )

        self.cliente.refresh_from_db()
        venda = Vendas.objects.get(id=self.venda_id)

        self.assertFalse(autorizado)
        self.assertIn("Cancelamento Negado", mensagem)
        self.assertEqual(self.cliente.pontos, Decimal("100.00"))
        self.assertEqual(venda.status, "VENDA")

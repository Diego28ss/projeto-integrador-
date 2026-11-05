from django.test import TestCase, Client

class PainelDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_acesso_painel_com_sessao(self):
        session = self.client.session
        session['usuario_logado'] = 'teste'
        session['perfil_usuario'] = 'Colaborador'
        session.save()

        response = self.client.get('/painel/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventario/index.html')

from decimal import Decimal
from django.test import TestCase
from inventario.models.produtos.produto_models import Produtos
from inventario.models.clientes.cliente_models import Clientes
from inventario.models.vendas.venda_models import ConfiguracaoPontos
from inventario.services.vendas.pdv_services import calcular_resgate_pontos

class TestesEngenheiroQA(TestCase):

    def setUp(self):
        """Cenário base para os testes unitários."""
        # Cria uma lata de tinta de teste com estoque inicial = 5
        self.produto = Produtos.objects.create(
            nome="Lata Tinta Acrílica Fosca 18L",
            estoque_atual=5
        )

        # Regra de fidelidade: 100 pontos = R$ 1,00 de desconto
        self.config_pontos = ConfiguracaoPontos.objects.create(
            tipo_usuario='CLIENTE',
            pontos_por_real=Decimal('1.00'),
            divisor_resgate=Decimal('100.00')
        )

    # -------------------------------------------------------------
    # 1. TESTE DE ESTOQUE (Tentativa de 'quebrar' com venda excessiva)
    # -------------------------------------------------------------
    def test_bloqueio_venda_acima_do_estoque(self):
        """Valida se o método tem_estoque_suficiente recusa vender mais latas do que existem."""
        latas_solicitadas = 6  # Temos apenas 5 latas no estoque

        tem_estoque = self.produto.tem_estoque_suficiente(latas_solicitadas)
        
        # O sistema NÃO pode autorizar essa baixa
        self.assertFalse(
            tem_estoque, 
            "FALHA CRÍTICA: O sistema permitiu venda com quantidade superior ao estoque disponível!"
        )

    def test_autorizacao_venda_limite_estoque(self):
        """Garante que a venda no limite exato do estoque (5 latas) seja permitida."""
        tem_estoque = self.produto.tem_estoque_suficiente(5)
        self.assertTrue(tem_estoque, "O sistema deveria permitir a venda do estoque total disponível.")

    # -------------------------------------------------------------
    # 2. TESTE DE PAGAMENTO E TROCO INCONSISTENTE
    # -------------------------------------------------------------
    def test_validacao_troco_invalido(self):
        """Garante que pagamento menor que o total da compra gere saldo devedor e não troco válido."""
        valor_total = Decimal("150.00")
        valor_entregue = Decimal("100.00")  # Faltam R$ 50,00

        troco = valor_entregue - valor_total

        # O troco não pode ser positivo nem zero
        self.assertLess(
            troco, Decimal("0.00"), 
            "FALHA NO CAIXA: Pagamento insuficiente não pode gerar troco positivo."
        )

    # -------------------------------------------------------------
    # 3. TESTE DO MOTOR DE FIDELIZAÇÃO (MÓDULO DE PONTOS)
    # -------------------------------------------------------------
    def test_resgate_pontos_cliente_sem_saldo(self):
        """Tenta resgatar desconto para cliente com zero pontos acumulados."""
        cliente_zerado = Clientes.objects.create(
            nome="Consumidor Balcão",
            pontos=Decimal('0.00')
        )

        resultado = calcular_resgate_pontos(cliente_zerado.id)

        self.assertEqual(
            resultado['valor_desconto'], 0.0, 
            "Cliente sem pontos não pode receber desconto financeiro."
        )
        self.assertEqual(resultado['mensagem'], 'Sem pontos acumulados.')

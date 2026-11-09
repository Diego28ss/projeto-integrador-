from django.test import TestCase
from decimal import Decimal
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.models.vendas.caixa_models import CaixaDiario, SangriaCaixa
from inventario.services.vendas.caixa_services import (
    autenticar_dupla_credencial, 
    abrir_caixa, 
    registrar_sangria, 
    fechar_caixa
)
from inventario.services.vendas.pdv_services import processar_nova_venda

class CaixaDiarioTests(TestCase):
    
    def setUp(self):
        """
        Prepara o ambiente antes de cada teste rodar.
        Cria um Administrador e um Colaborador virtuais.
        """
        self.admin = Usuarios.objects.create(
            login='gerente1', 
            senha='123', 
            perfil='Administrador'
        )
        self.colab = Usuarios.objects.create(
            login='operador1', 
            senha='321', 
            perfil='Colaborador',
            comissao=Decimal('1.00')
        )

    def test_autenticar_dupla_credencial(self):
        """Testa se o sistema bloqueia senhas erradas e perfis inválidos."""
        # Teste 1: Sucesso (Credenciais corretas)
        sucesso, msg, adm, col = autenticar_dupla_credencial('gerente1', '123', 'operador1', '321')
        self.assertTrue(sucesso)
        self.assertEqual(adm, self.admin)
        
        # Teste 2: Falha (O gerente digitou a senha errada)
        sucesso, msg, adm, col = autenticar_dupla_credencial('gerente1', 'senha_errada', 'operador1', '321')
        self.assertFalse(sucesso)
        
        # Teste 3: Falha (Um colaborador tentou autorizar a abertura do caixa se passando por admin)
        sucesso, msg, adm, col = autenticar_dupla_credencial('operador1', '321', 'operador1', '321')
        self.assertFalse(sucesso)
        self.assertIn("não possui perfil de Administrador", msg)

    def test_abrir_caixa_seguro(self):
        """Testa se o caixa abre corretamente e impede abertura duplicada."""
        # Abrindo o caixa pela primeira vez com R$ 100 de troco
        sucesso, msg = abrir_caixa(self.admin, self.colab, 100.00)
        self.assertTrue(sucesso)
        
        # Verifica se o caixa foi gravado no banco de dados
        caixa = CaixaDiario.objects.get(operador=self.colab, status='ABERTO')
        self.assertEqual(caixa.fundo_inicial, Decimal('100.00'))
        
        # Tentando abrir o caixa de novo para o mesmo operador (deve falhar)
        sucesso_duplicado, msg_duplicado = abrir_caixa(self.admin, self.colab, 50.00)
        self.assertFalse(sucesso_duplicado)
        self.assertIn("já possui um caixa ABERTO", msg_duplicado)

    def test_integracao_venda_e_caixa(self):
        """Testa se uma venda em dinheiro cai automaticamente no caixa aberto."""
        # 1. Abre o caixa com R$ 50,00
        abrir_caixa(self.admin, self.colab, 50.00)
        
        # 2. Prepara os dados simulados que viriam do Front-end (Membro B)
        dados_venda = {
            'valor_total': 150.00,
            'valor_desconto': 0.00,
            'vendedor': 'operador1',
            'forma_pagamento': 'DINHEIRO',
            'cupom_texto': 'Teste Unitário'
        }
        
        # 3. Processa a venda
        processar_nova_venda(dados_venda, carrinho=[], status_venda='VENDA')
        
        # 4. Verifica se o dinheiro foi para a gaveta
        caixa = CaixaDiario.objects.get(operador=self.colab, status='ABERTO')
        self.assertEqual(caixa.total_dinheiro, Decimal('150.00'))
        
        # 5. O dinheiro esperado físico na gaveta agora deve ser R$ 200 (150 da venda + 50 de troco)
        self.assertEqual(caixa.calcular_dinheiro_esperado(), Decimal('200.00'))

    def test_fluxo_completo_com_sangria_e_fechamento(self):
        """
        Simula um dia inteiro de trabalho:
        Abre o caixa -> Faz venda -> Faz sangria -> Fecha o caixa e confere a quebra.
        """
        # 1. Abre com R$ 100 de troco
        abrir_caixa(self.admin, self.colab, 100.00)
        caixa = CaixaDiario.objects.get(operador=self.colab)
        
        # 2. Simula venda direta no banco para acelerar o teste (entrou R$ 500 em dinheiro)
        caixa.total_dinheiro += Decimal('500.00')
        caixa.save()
        
        # 3. Faz uma sangria (Retira R$ 200 para o cofre)
        sucesso_sangria, msg = registrar_sangria(caixa, self.admin, 200.00, "Excesso de notas")
        self.assertTrue(sucesso_sangria)
        self.assertEqual(caixa.total_sangrias, Decimal('200.00'))
        
        # 4. Calcula o que deve ter na gaveta: 100 (troco) + 500 (vendas) - 200 (sangria) = 400
        self.assertEqual(caixa.calcular_dinheiro_esperado(), Decimal('400.00'))
        
        # 5. Fecha o caixa informando que contou exatamente R$ 400 em notas na gaveta
        sucesso_fechamento, diferenca, esperado = fechar_caixa(caixa, 400.00)
        
        self.assertTrue(sucesso_fechamento)
        self.assertEqual(esperado, Decimal('400.00'))
        self.assertEqual(diferenca, Decimal('0.00')) # Zero quebra de caixa, bateu exato!
        
        # Verifica se o caixa foi realmente fechado
        caixa.refresh_from_db()
        self.assertEqual(caixa.status, 'FECHADO')
        self.assertIsNotNone(caixa.data_fechamento)
        
from django.db import models
from django.utils import timezone

class Vendas(models.Model):
    # Definição dos status possíveis para identificar em qual etapa a venda se encontra
    STATUS_CHOICES = [
        ('VENDA', 'Venda Finalizada'),
        ('ORCAMENTO', 'Orçamento'),
        ('CANCELADA', 'Cancelada'),
    ]

    # NOVO: Lista de formas de pagamento para o PDV conseguir contabilizar e bater o caixa diário
    FORMA_PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('DEBITO', 'Cartão de Débito'),
        ('CREDITO', 'Cartão de Crédito'),
    ]

    # Regista a data e hora exata em que a venda ocorreu no balcão
    data_venda = models.DateTimeField(default=timezone.now)
    
    # Armazena os valores financeiros primários da compra
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Suporta valores fracionados (centavos) aplicados no programa de fidelidade
    pontos_resgatados = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_desconto_pontos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Identifica textualmente o colaborador que realizou o atendimento
    vendedor = models.CharField(max_length=100, blank=True, null=True)
    
    # Guarda estaticamente a comissão, garantindo a imutabilidade do valor no histórico
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # NOVO CAMPO: Grava como o cliente pagou para permitir o fechamento e contabilidade da gaveta
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='DINHEIRO')
    
    # Relacionamentos com o modelo de Clientes, separando o comprador final do pintor que indicou a venda
    cliente = models.ForeignKey('inventario.Clientes', on_delete=models.SET_NULL, null=True, blank=True, related_name='compras_feitas')
    indicante = models.ForeignKey('inventario.Clientes', on_delete=models.SET_NULL, null=True, blank=True, related_name='indicacoes_realizadas')
    
    # Guarda o texto processado para ser impresso diretamente na impressora térmica
    cupom_texto = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='VENDA')

    # Função simples que retorna o nome da venda para facilitar a visualização no banco de dados (Admin)
    def __str__(self):
        return f"{self.status} {self.id} - Cliente ID: {self.cliente_id}"
    


class ConfiguracaoPontos(models.Model):
    TIPO_CHOICES = [
        ('CLIENTE', 'Cliente Regular'),
        ('PINTOR', 'Pintor / Indicante'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, unique=True)
    
    # ATUALIZADO: Define quantos pontos o usuário ganha a cada R$ 1,00 gasto (Decimal)
    pontos_por_real = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    # ATUALIZADO: Trava a matemática do sistema em decimal (100.00 pontos = R$ 1,00).
    divisor_resgate = models.DecimalField(max_digits=10, decimal_places=2, default=100.00, help_text="Quantos pontos equivalem a R$ 1,00")

    def __str__(self):
        return f"Regra {self.tipo_usuario}: Ganha {self.pontos_por_real}pts a cada R$ 1,00"
    
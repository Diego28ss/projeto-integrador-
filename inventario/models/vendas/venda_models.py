from django.db import models
from django.utils import timezone

class Vendas(models.Model):
    STATUS_CHOICES = [
        ('VENDA', 'Venda Finalizada'),
        ('ORCAMENTO', 'Orçamento'),
        ('CANCELADA', 'Cancelada'),
    ]

    data_venda = models.DateTimeField(default=timezone.now)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # ATUALIZADO: Suporta valores fracionados (centavos) para pontos
    pontos_resgatados = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_desconto_pontos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    vendedor = models.CharField(max_length=100, blank=True, null=True)
    
    # NOVO CAMPO: Guarda o valor exato da comissão gerada nesta venda
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # ATUALIZAÇÃO: Vínculo direto (ID) com o cadastro do cliente.
    cliente = models.ForeignKey('inventario.Clientes', on_delete=models.SET_NULL, null=True, blank=True, related_name='compras_feitas')
    indicante = models.ForeignKey('inventario.Clientes', on_delete=models.SET_NULL, null=True, blank=True, related_name='indicacoes_realizadas')
    
    cupom_texto = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='VENDA')

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
    
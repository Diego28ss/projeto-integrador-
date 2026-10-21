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
    vendedor = models.CharField(max_length=100, blank=True, null=True)
    cliente = models.CharField(max_length=255, blank=True, null=True)
    indicante = models.CharField(max_length=255, blank=True, null=True)
    cupom_texto = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='VENDA')

    def __str__(self):
        return f"{self.status} {self.id} - {self.cliente}"

class ConfiguracaoPontos(models.Model):
    TIPO_CHOICES = [
        ('CLIENTE', 'Cliente Regular'),
        ('PINTOR', 'Pintor / Indicante'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, unique=True)
    pontos_por_real = models.IntegerField(default=1)
    pontos_necessarios_resgate = models.IntegerField(default=30)
    valor_resgate_reais = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)

    def __str__(self):
        return f"Regra {self.tipo_usuario}: {self.pontos_necessarios_resgate}pts = R$ {self.valor_resgate_reais}"
    
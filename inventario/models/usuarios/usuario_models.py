from django.db import models
from decimal import Decimal

class Usuarios(models.Model):
    login = models.CharField(max_length=100, unique=True)
    senha = models.CharField(max_length=100)
    perfil = models.CharField(max_length=50, default='Colaborador')
    
    # Taxa de comissão em porcentagem (Ex: 1.00 para 1%)
    comissao = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return self.login
        
    # FAT MODEL: Retorna a comissão calculada baseada no valor líquido da venda
    def calcular_comissao(self, valor_total_venda):
        # Converte para Decimal para garantir exatidão nos centavos
        valor_base = Decimal(str(valor_total_venda))
        resultado = (valor_base * self.comissao) / Decimal('100.00')
        return round(resultado, 2)
    
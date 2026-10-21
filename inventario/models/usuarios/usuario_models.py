from django.db import models

class Usuarios(models.Model):
    login = models.CharField(max_length=100, unique=True)
    senha = models.CharField(max_length=100)
    perfil = models.CharField(max_length=50, default='Colaborador')
    comissao = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return self.login
        
    # FAT MODEL: Retorna a comissão calculada baseada em um valor
    def calcular_comissao(self, valor_total_venda):
        return (float(valor_total_venda) * float(self.comissao)) / 100
    
from django.db import models

class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Familia(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Produtos(models.Model):
    nome = models.CharField(max_length=255)
    cod_barras = models.CharField(max_length=100, blank=True, null=True)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    margem_lucro = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estoque_atual = models.IntegerField(default=0)
    unidade = models.CharField(max_length=10, default='UN')
    status = models.CharField(max_length=20, default='ATIVO')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    familia = models.ForeignKey(Familia, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome

    # FAT MODEL: O próprio produto sabe calcular se tem estoque
    def tem_estoque_suficiente(self, quantidade_solicitada):
        return self.estoque_atual >= int(quantidade_solicitada)
    
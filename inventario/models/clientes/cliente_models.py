from django.db import models

class Clientes(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=50, blank=True, null=True)
    cpf = models.CharField(max_length=20, blank=True, null=True)
    cep = models.CharField(max_length=20, blank=True, null=True)
    rua = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=50, blank=True, null=True)
    complemento = models.CharField(max_length=150, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    tipo = models.CharField(max_length=50, default="CLIENTE")
    pontos = models.IntegerField(default=0)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return self.nome

    def resgatar_pontos(self, quantidade):
        if self.pontos >= quantidade:
            self.pontos -= quantidade
            self.save()
            return True
        return False
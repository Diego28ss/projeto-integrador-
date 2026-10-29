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
    
    # ATUALIZADO: Agora suporta valores fracionados (centavos)
    pontos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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

# NOVA CLASSE: Atuará como o "extrato bancário", gravando toda movimentação de pontos.
class HistoricoPontos(models.Model):
    # Relaciona o histórico com o dono dos pontos.
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE, related_name='historico_pontos')
    
    # Relaciona com a venda que gerou ou gastou os pontos.
    venda = models.ForeignKey('inventario.Vendas', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Identifica a origem (Ex: 'GANHO_CLIENTE', 'GANHO_INDICANTE', 'RESGATE').
    tipo_operacao = models.CharField(max_length=50) 
    
    # ATUALIZADO: Salva a quantidade movimentada em decimais
    pontos = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Detalhe humano para exibir no modal de extrato (Ex: "Indicação da compra de João").
    descricao = models.CharField(max_length=255)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historico_pontos'

    def __str__(self):
        return f"{self.cliente.nome} - {self.pontos} pts ({self.tipo_operacao})"
    
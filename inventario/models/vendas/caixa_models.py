from django.db import models
from django.utils import timezone
from decimal import Decimal

class CaixaDiario(models.Model):
    STATUS_CHOICES = [
        ('ABERTO', 'Caixa Aberto'),
        ('FECHADO', 'Caixa Fechado'),
    ]

    # Controlo de Tempo e Estado
    data_abertura = models.DateTimeField(default=timezone.now)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')

    # Dupla Credencial (Vínculo com o ficheiro usuario_models.py)
    operador = models.ForeignKey(
        'inventario.Usuarios', 
        on_delete=models.PROTECT, 
        related_name='caixas_operados',
        help_text="Colaborador responsável pelo balcão"
    )
    administrador_autorizador = models.ForeignKey(
        'inventario.Usuarios', 
        on_delete=models.PROTECT, 
        related_name='caixas_autorizados',
        help_text="Gerente que conferiu e autorizou a abertura"
    )

    # Lastro e Movimentos Financeiros (Alta precisão decimal)
    fundo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Agregadores calculados automaticamente a cada venda
    total_dinheiro = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_pix = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    total_sangrias = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Caixa {self.id} - Operador: {self.operador.login} - {self.status}"

    # FAT MODEL: Calcula o lastro físico real em tempo real
    def calcular_dinheiro_esperado(self):
        """Retorna quanto dinheiro físico deve estar na gaveta neste momento."""
        return (self.fundo_inicial + self.total_dinheiro) - self.total_sangrias


class SangriaCaixa(models.Model):
    caixa_diario = models.ForeignKey(CaixaDiario, on_delete=models.CASCADE, related_name='sangrias')
    data_hora = models.DateTimeField(default=timezone.now)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=255)
    
    # Registo de quem autorizou a remoção de notas da gaveta
    autorizador = models.ForeignKey(
        'inventario.Usuarios', 
        on_delete=models.PROTECT, 
        related_name='sangrias_realizadas'
    )

    def __str__(self):
        return f"Sangria de R$ {self.valor} no {self.caixa_diario} por {self.autorizador.login}"
    
from django.db import models

class Marca(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

class Familia(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

# ==============================================================================
# NOVAS TABELAS FISCAIS (CFOP e CSOSN)
# ==============================================================================
class TributacaoCFOP(models.Model):
    codigo = models.CharField(max_length=4, unique=True)
    descricao = models.CharField(max_length=255)
    ativo = models.BooleanField(default=False) # Inicia inativo até o usuário ligar na configuração

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

class TributacaoCSOSN(models.Model):
    codigo = models.CharField(max_length=4, unique=True)
    descricao = models.CharField(max_length=255)
    ativo = models.BooleanField(default=False) # Inicia inativo até o usuário ligar

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# ==============================================================================
# TABELA DE PRODUTOS ATUALIZADA
# ==============================================================================
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

    # ------------------ NOVOS CAMPOS FISCAIS E DE VÍNCULO ------------------
    cod_interno = models.CharField(max_length=20, unique=True, blank=True, null=True)
    cod_fornecedor = models.CharField(max_length=100, blank=True, null=True)
    ncm = models.CharField(max_length=10, blank=True, null=True)
    cest = models.CharField(max_length=10, blank=True, null=True)
    cfop_padrao = models.ForeignKey(TributacaoCFOP, on_delete=models.SET_NULL, null=True, blank=True)
    csosn_padrao = models.ForeignKey(TributacaoCSOSN, on_delete=models.SET_NULL, null=True, blank=True)
    # -----------------------------------------------------------------------

    def __str__(self):
        return self.nome

    def tem_estoque_suficiente(self, quantidade_solicitada):
        return self.estoque_atual >= int(quantidade_solicitada)

    # FAT MODEL: Geração Automática do Código Interno
    def save(self, *args, **kwargs):
        # Descobre se é um produto novo verificando se ele já tem um "ID" no banco
        produto_novo = self.pk is None
        
        # Salva o produto para o banco de dados gerar o número do ID
        super(Produtos, self).save(*args, **kwargs)

        # Se for novo e não tiver código interno, cria um baseado no ID (Ex: PRD00001)
        if produto_novo and not self.cod_interno:
            self.cod_interno = f"PRD{self.id:05d}"
            # Salva apenas a atualização do campo código interno para não gerar loop
            super(Produtos, self).save(update_fields=['cod_interno'])
            
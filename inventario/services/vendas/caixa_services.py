from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from inventario.models.usuarios.usuario_models import Usuarios
from inventario.models.vendas.caixa_models import CaixaDiario, SangriaCaixa

# Função responsável por verificar se as duas pessoas (Admin e Colaborador) têm as senhas corretas
def autenticar_dupla_credencial(login_admin, senha_admin, login_colaborador, senha_colaborador):
    """
    Verifica no banco de dados se o gerente e o operador inseriram as credenciais corretas.
    Retorna uma tupla (sucesso, mensagem, admin_obj, colab_obj).
    """
    try:
        admin = Usuarios.objects.get(login__iexact=str(login_admin).strip(), senha=str(senha_admin).strip())
        if admin.perfil.strip().lower() != 'administrador':
            return False, "O usuário autorizador não possui perfil de Administrador.", None, None
            
        colab = Usuarios.objects.get(login__iexact=str(login_colaborador).strip(), senha=str(senha_colaborador).strip())
        return True, "Credenciais validadas com sucesso.", admin, colab
        
    except Usuarios.DoesNotExist:
        return False, "Credenciais inválidas. Verifique os logins e senhas digitados.", None, None


# Função responsável por registrar a abertura do caixa de forma segura
@transaction.atomic
def abrir_caixa(admin, colab, fundo_inicial):
    """
    Abre um novo turno de caixa garantindo que o colaborador não tenha outro caixa aberto.
    """
    caixa_existente = CaixaDiario.objects.filter(operador=colab, status='ABERTO').exists()
    
    if caixa_existente:
        return False, f"O operador {colab.login} já possui um caixa ABERTO."

    novo_caixa = CaixaDiario.objects.create(
        operador=colab,
        administrador_autorizador=admin,
        fundo_inicial=Decimal(str(fundo_inicial))
    )
    
    return True, f"Caixa {novo_caixa.id} aberto com sucesso para {colab.login}."


# Função responsável por retirar dinheiro da gaveta por segurança (Sangria)
@transaction.atomic
def registrar_sangria(caixa, admin_autorizador, valor_retirado, motivo):
    """
    Registra a retirada de dinheiro físico da gaveta (sangria) e atualiza o total retirado no caixa.
    """
    valor_decimal = Decimal(str(valor_retirado))
    
    SangriaCaixa.objects.create(
        caixa_diario=caixa,
        valor=valor_decimal,
        motivo=motivo,
        autorizador=admin_autorizador
    )
    
    caixa.total_sangrias += valor_decimal
    caixa.save()
    
    return True, f"Sangria de R$ {valor_decimal} registrada com sucesso."


# Função responsável por auditar o dinheiro contado e fechar o turno
@transaction.atomic
def fechar_caixa(caixa, valor_fisico_informado):
    """
    Encerra o turno do caixa, calculando a diferença entre o que o sistema espera e o dinheiro contado pelo operador.
    """
    valor_informado_decimal = Decimal(str(valor_fisico_informado))
    dinheiro_esperado = caixa.calcular_dinheiro_esperado()
    diferenca = valor_informado_decimal - dinheiro_esperado
    
    caixa.status = 'FECHADO'
    caixa.data_fechamento = timezone.now()
    caixa.save()
    
    return True, diferenca, dinheiro_esperado

from django.shortcuts import get_object_or_404
from inventario.models.clientes.cliente_models import Clientes

def salvar_dados_cliente(post_data):
    cliente_id = post_data.get('cliente_id')

    if cliente_id and cliente_id.strip():
        cliente = get_object_or_404(Clientes, id=cliente_id)
    else:
        cliente = Clientes()

    cliente.nome = post_data.get('nome', '')
    cliente.telefone = post_data.get('telefone', '')
    cliente.cpf = post_data.get('cpf', '')

    cliente.cep = post_data.get('cep', '')
    cliente.rua = post_data.get('rua', '')
    cliente.numero = post_data.get('numero', '')
    cliente.complemento = post_data.get('complemento', '')
    cliente.bairro = post_data.get('bairro', '')
    cliente.cidade = post_data.get('cidade', '')
    cliente.estado = post_data.get('estado', '')

    tipos = []
    if post_data.get('check_cliente'):
        tipos.append("CLIENTE")
    if post_data.get('check_pintor'):
        tipos.append("PINTOR")
    cliente.tipo = ", ".join(tipos) if tipos else "CLIENTE"

    cliente.save()
    return cliente
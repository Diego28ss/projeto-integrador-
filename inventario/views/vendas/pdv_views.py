from decimal import Decimal
from django.contrib import messages
from inventario.models.vendas.caixa_models import CaixaDiario, SangriaCaixa
from inventario.services.vendas import caixa_services

import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q
from inventario.models.produtos.produto_models import Produtos
from inventario.models.clientes.cliente_models import Clientes
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.services.vendas import pdv_services
from inventario.services.clientes import pontos_services

def tela_pdv(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    caixa = CaixaDiario.objects.filter(status='ABERTO').last()
    if not caixa:
        return redirect('tela_painel_pdv')

    caixa.total_digital = (caixa.total_pix or Decimal('0.00')) + (caixa.total_debito or Decimal('0.00')) + (caixa.total_credito or Decimal('0.00'))

    produtos = Produtos.objects.exclude(status='INATIVO')
    vendedores = Usuarios.objects.all()
    clientes = Clientes.objects.all()

    context = {
        'produtos': produtos,
        'vendedores': vendedores,
        'vendedores_list': vendedores,
        'clientes': clientes,
        'pintores': clientes.filter(tipo__icontains='PINTOR'),
        'caixa': caixa,
    }
    return render(request, 'inventario/pdv.html', context)

def api_consultar_pontos(request):
    cliente_id = request.GET.get('cliente_id')
    
    if cliente_id:
        try:
            cliente_id = int(cliente_id)
        except ValueError:
            cliente_id = None
            
    resultado = pontos_services.calcular_resgate_pontos(cliente_id)
    return JsonResponse(resultado)

def api_buscar_produtos(request):
    query = request.GET.get('q', '').strip()
    produtos = Produtos.objects.exclude(status='INATIVO')

    if query:
        palavras = query.split()
        for palavra in palavras:
            produtos = produtos.filter(
                Q(nome__icontains=palavra) |
                Q(cod_barras__icontains=palavra)
            )

    produtos = produtos[:50]
    resultados = [{'id': p.id, 'nome': p.nome, 'preco_venda': float(p.preco_venda), 'estoque_atual': p.estoque_atual, 'cod_barras': p.cod_barras or ''} for p in produtos]
    return JsonResponse({'produtos': resultados})

def api_salvar_venda(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            carrinho = dados.get('carrinho', [])
            status_venda = dados.get('status', 'VENDA')
            
            # NOVO: Pega o operador da sessão de forma blindada, ignorando o JavaScript!
            operador_oficial = request.session.get('operador_caixa')
            if not operador_oficial:
                # Fallback de segurança buscando o último caixa aberto direto do banco de dados
                caixa = CaixaDiario.objects.filter(status='ABERTO').last()
                operador_oficial = caixa.operador.login if caixa else dados.get('vendedor', '')

            dados_venda = {
                'valor_total': dados.get('valor_final', 0),
                'valor_desconto': dados.get('desconto', 0),
                'vendedor': operador_oficial, # <--- SUBSTITUÍDO: Força o nome correto na venda
                'cliente_id': dados.get('cliente_id'),
                'indicante_id': dados.get('indicante_id'),
                'cupom_texto': json.dumps(carrinho),
                # NOVO: Preparando a recepção da forma de pagamento para a Fase 4 do caixa
                'forma_pagamento': dados.get('forma_pagamento', 'DINHEIRO') 
            }

            venda_id = pdv_services.processar_nova_venda(
                dados_venda=dados_venda,
                carrinho=carrinho,
                status_venda=status_venda,
                pontos_resgatados=float(dados.get('pontos_resgatados', 0.0)),
                valor_desconto_pontos=float(dados.get('valor_desconto_pontos', 0.0))
            )
            return JsonResponse({'status': 'sucesso', 'venda_id': venda_id})
            
        except ValueError as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
        except Exception as e:
            import traceback
            print(traceback.format_exc()) 
            return JsonResponse({'status': 'erro', 'mensagem': f'Erro interno: {str(e)}'})
            
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido.'})


def _converter_moeda(valor_str):
    if not valor_str:
        return Decimal('0.00')
    limpo = str(valor_str).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return Decimal(limpo)
    except:
        return Decimal('0.00')

def tela_painel_pdv(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    caixa = CaixaDiario.objects.filter(status='ABERTO').last()
    if caixa:
        caixa.total_digital = (caixa.total_pix or Decimal('0.00')) + (caixa.total_debito or Decimal('0.00')) + (caixa.total_credito or Decimal('0.00'))

    context = {
        'caixa_aberto': bool(caixa),
        'caixa': caixa,
    }
    return render(request, 'inventario/painel_pdv.html', context)

def tela_abertura_caixa(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    caixa = CaixaDiario.objects.filter(status='ABERTO').last()
    if caixa:
        return redirect('tela_pdv')

    return render(request, 'inventario/abertura_caixa.html')

def abrir_caixa_view(request):
    if request.method != 'POST':
        return redirect('tela_abertura_caixa')

    admin_user = request.POST.get('admin_user', '').strip()
    admin_pass = request.POST.get('admin_pass', '').strip()
    colab_user = request.POST.get('colaborador_user', '').strip()
    colab_pass = request.POST.get('colaborador_pass', '').strip()
    fundo_inicial_str = request.POST.get('fundo_inicial', '0')

    valido, msg, admin_obj, colab_obj = caixa_services.autenticar_dupla_credencial(
        admin_user, admin_pass, colab_user, colab_pass
    )

    if not valido:
        messages.error(request, msg)
        return redirect('tela_abertura_caixa')

    fundo_decimal = _converter_moeda(fundo_inicial_str)
    sucesso, msg_caixa = caixa_services.abrir_caixa(admin_obj, colab_obj, fundo_decimal)

    if not sucesso:
        messages.error(request, msg_caixa)
        return redirect('tela_abertura_caixa')

    # NOVO: Guarda na sessão do navegador quem é o operador oficial da gaveta
    request.session['operador_caixa'] = colab_obj.login

    messages.success(request, msg_caixa)
    return redirect('tela_pdv')


def realizar_sangria(request):
    if request.method != 'POST':
        return redirect('tela_pdv')

    valor_str = request.POST.get('valor_sangria', '0')
    motivo = request.POST.get('motivo_sangria', '').strip()
    admin_user = request.POST.get('admin_user', '').strip()
    admin_pass = request.POST.get('admin_pass', '').strip()
    op_user = request.POST.get('op_user', '').strip()
    op_pass = request.POST.get('op_pass', '').strip()

    valido, msg, admin_obj, colab_obj = caixa_services.autenticar_dupla_credencial(
        admin_user, admin_pass, op_user, op_pass
    )

    if not valido:
        messages.error(request, f'Falha na autorização: {msg}')
        return redirect('tela_pdv')

    caixa = CaixaDiario.objects.filter(status='ABERTO').last()
    if not caixa:
        messages.error(request, 'Nenhum caixa aberto para realizar sangria.')
        return redirect('tela_painel_pdv')

    valor_decimal = _converter_moeda(valor_str)
    sucesso, msg_sangria = caixa_services.registrar_sangria(caixa, admin_obj, valor_decimal, motivo)

    if sucesso:
        messages.success(request, msg_sangria)
    else:
        messages.error(request, msg_sangria)

    return redirect('tela_pdv')

def fechar_caixa_view(request):
    if request.method != 'POST':
        return redirect('tela_pdv')

    valor_contagem_str = request.POST.get('valor_contagem_fisica', '0')
    admin_user = request.POST.get('admin_user_fechamento', '').strip()
    admin_pass = request.POST.get('admin_pass_fechamento', '').strip()

    try:
        admin_obj = Usuarios.objects.get(login=admin_user, senha=admin_pass)
        if admin_obj.perfil != 'Administrador':
            messages.error(request, 'O usuário autorizador não possui perfil de Administrador.')
            return redirect('tela_pdv')
    except Usuarios.DoesNotExist:
        messages.error(request, 'Credenciais de Administrador inválidas para fechamento.')
        return redirect('tela_pdv')

    caixa = CaixaDiario.objects.filter(status='ABERTO').last()
    if not caixa:
        messages.error(request, 'Nenhum caixa aberto para fechamento.')
        return redirect('tela_painel_pdv')

    valor_contagem_decimal = _converter_moeda(valor_contagem_str)
    sucesso, diferenca, esperado = caixa_services.fechar_caixa(caixa, valor_contagem_decimal)

    if sucesso:
        # NOVO: Limpa a sessão quando a gaveta é fechada
        request.session.pop('operador_caixa', None) 
        
        status_dif = 'Sem divergências' if diferenca == 0 else f'Diferença em dinheiro: R$ {diferenca:.2f}'
        messages.success(request, f'Caixa fechado com sucesso! Total esperado em dinheiro: R$ {esperado:.2f}. {status_dif}')
    else:
        messages.error(request, 'Erro ao fechar o caixa.')

    return redirect('tela_painel_pdv')

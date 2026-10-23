import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction

# Importação do seu modelo customizado de usuários
from inventario.models import Usuarios

# Importações consolidadas do módulo de produtos e auditoria
from inventario.models.produtos.produto_models import (
    Produtos, 
    Marca, 
    Familia, 
    TributacaoCFOP, 
    TributacaoCSOSN,
    AuditoriaEstoque
)

from inventario.services.estoque import xml_services

def tela_estoque_produtos(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    query = request.GET.get('q', '')
    produtos = Produtos.objects.all()

    if query:
        produtos = produtos.filter(
            Q(nome__icontains=query) |
            Q(cod_barras__icontains=query) |
            Q(cod_interno__icontains=query) |
            Q(marca__nome__icontains=query) |
            Q(familia__nome__icontains=query)
        )

    marcas = Marca.objects.all().order_by('nome')
    familias = Familia.objects.all().order_by('nome')
    
    # Busca apenas os impostos ativados pelo usuário
    cfops_ativos = TributacaoCFOP.objects.filter(ativo=True).order_by('codigo')
    csosns_ativos = TributacaoCSOSN.objects.filter(ativo=True).order_by('codigo')

    context = {
        'produtos': produtos,
        'query': query,
        'marcas': marcas,
        'familias': familias,
        'cfops': cfops_ativos,
        'csosns': csosns_ativos,
    }
    return render(request, 'inventario/estoque_produtos.html', context)

def salvar_produto(request):
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        nome = request.POST.get('nome')
        cod_barras = request.POST.get('cod_barras', '')
        preco_custo = request.POST.get('preco_custo', '0').replace(',', '.')
        preco_venda = request.POST.get('preco_venda', '0').replace(',', '.')
        estoque_atual = request.POST.get('estoque_atual', 0)
        unidade = request.POST.get('unidade', 'UN')
        status = request.POST.get('status', 'ATIVO')
        marca_id = request.POST.get('marca')
        familia_id = request.POST.get('familia')
        
        # Novos campos fiscais capturados do form HTML
        ncm = request.POST.get('ncm', '')
        cest = request.POST.get('cest', '')
        cfop_id = request.POST.get('cfop')
        csosn_id = request.POST.get('csosn')

        marca_obj = Marca.objects.filter(id=marca_id).first() if marca_id else None
        familia_obj = Familia.objects.filter(id=familia_id).first() if familia_id else None
        cfop_obj = TributacaoCFOP.objects.filter(id=cfop_id).first() if cfop_id else None
        csosn_obj = TributacaoCSOSN.objects.filter(id=csosn_id).first() if csosn_id else None

        if produto_id and produto_id.strip():
            produto = get_object_or_404(Produtos, id=produto_id)
            produto.nome = nome
            produto.cod_barras = cod_barras
            produto.preco_custo = preco_custo
            produto.preco_venda = preco_venda
            produto.estoque_atual = estoque_atual
            produto.unidade = unidade
            produto.status = status
            produto.marca = marca_obj
            produto.familia = familia_obj
            produto.ncm = ncm
            produto.cest = cest
            produto.cfop_padrao = cfop_obj
            produto.csosn_padrao = csosn_obj
            produto.save()
            messages.success(request, f"Produto '{nome}' atualizado com sucesso!")
        else:
            Produtos.objects.create(
                nome=nome, cod_barras=cod_barras, preco_custo=preco_custo,
                preco_venda=preco_venda, estoque_atual=estoque_atual,
                unidade=unidade, marca=marca_obj, familia=familia_obj, status=status,
                ncm=ncm, cest=cest, cfop_padrao=cfop_obj, csosn_padrao=csosn_obj
            )
            messages.success(request, f"Produto '{nome}' cadastrado com sucesso!")
    return redirect('tela_estoque_produtos')

def excluir_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    nome = produto.nome
    produto.delete()
    messages.success(request, f"Produto '{nome}' excluído!")
    return redirect('tela_estoque_produtos')

def tela_entrada_carga(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    return render(request, 'inventario/entrada_carga.html')

def api_produto_por_codigo(request):
    codigo = request.GET.get('codigo', '').strip()
    produto = Produtos.objects.filter(cod_barras=codigo).first()
    if produto:
        return JsonResponse({'status': 'ok', 'id': produto.id, 'nome': produto.nome})
    return JsonResponse({'status': 'erro', 'mensagem': 'Produto não cadastrado!'})

def api_efetivar_entrada(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            itens = dados.get('itens', [])
            from django.db import transaction
            with transaction.atomic():
                for item in itens:
                    produto_id = item.get('id')
                    qtd_a_entrar = int(item.get('qtd', 0))
                    if qtd_a_entrar > 0:
                        produto = get_object_or_404(Produtos, id=produto_id)
                        produto.estoque_atual += qtd_a_entrar
                        produto.save()
            return JsonResponse({'status': 'sucesso'})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido.'})

def api_upload_xml(request):
    if request.method == 'POST' and request.FILES.get('arquivo_xml'):
        try:
            arquivo = request.FILES['arquivo_xml']
            
            # Delega a leitura para a camada de Serviços
            dados_extraidos = xml_services.processar_upload_xml(arquivo)
            
            return JsonResponse({'status': 'sucesso', 'dados': dados_extraidos})
            
        except ValueError as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
        except Exception as e:
            import traceback
            print(traceback.format_exc()) # Ajuda a localizar erros se o processar_upload_xml falhar
            return JsonResponse({'status': 'erro', 'mensagem': 'Erro interno ao processar o ficheiro.'})
            
    return JsonResponse({'status': 'erro', 'mensagem': 'Nenhum arquivo recebido.'})

def tela_acerto_estoque(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    return render(request, 'inventario/acerto_estoque.html')

# ==========================================
# APIs PARA O ACERTO DE ESTOQUE E AUDITORIA
# ==========================================
def api_buscar_produtos_acerto(request):
    """
    Função que procura produtos pelo nome, código interno ou código de barras
    e devolve os dados para a tela de Acerto de Estoque.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'produtos': []})
    
    produtos = Produtos.objects.filter(
        Q(nome__icontains=query) | 
        Q(cod_interno__icontains=query) | 
        Q(cod_barras__icontains=query)
    ).filter(status='ATIVO')[:15]
    
    dados = [{
        'id': p.id, 
        'cod_interno': p.cod_interno or '---',
        'cod_barras': p.cod_barras or '', # Necessário para o bipador funcionar
        'nome': p.nome, 
        'estoque': p.estoque_atual
    } for p in produtos]
    
    return JsonResponse({'produtos': dados})

# Adicione esta importação no topo do arquivo (ajuste o caminho se o modelo estiver noutro local)
from inventario.models import Usuarios 
import json
from django.db import transaction
from django.http import JsonResponse
from inventario.models.produtos.produto_models import Produtos, AuditoriaEstoque

def api_efetivar_acerto_seguro(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            produto_id = dados.get('produto_id')
            novo_estoque = int(dados.get('novo_estoque', 0))
            motivo = dados.get('motivo')
            usuario_login = dados.get('usuario')
            senha_digitada = dados.get('senha')

            # 1. Validação de Segurança na sua tabela customizada (inventario_usuarios)
            usuario_valido = Usuarios.objects.filter(login=usuario_login, senha=senha_digitada).first()
            
            if not usuario_valido:
                return JsonResponse({'status': 'erro', 'mensagem': 'Credenciais inválidas. Assinatura recusada.'})
            
            # 2. Transação Segura
            with transaction.atomic():
                produto = Produtos.objects.get(id=produto_id)
                estoque_antigo = produto.estoque_atual
                diferenca_qtd = novo_estoque - estoque_antigo
                
                if diferenca_qtd == 0:
                    return JsonResponse({'status': 'erro', 'mensagem': 'O novo estoque é igual ao atual.'})

                diferenca_financeira = float(produto.preco_custo) * diferenca_qtd

                produto.estoque_atual = novo_estoque
                produto.save()

                AuditoriaEstoque.objects.create(
                    produto=produto,
                    estoque_antigo=estoque_antigo,
                    estoque_novo=novo_estoque,
                    diferenca_quantidade=diferenca_qtd,
                    diferenca_financeira=diferenca_financeira,
                    motivo=motivo,
                    usuario=usuario_valido.login
                )
                
            return JsonResponse({'status': 'sucesso'})
            
        except Produtos.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Produto não encontrado.'})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
            
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido.'})

def tela_auditoria_estoque(request):
    """
    Carrega o histórico completo de acertos de estoque, ordenado
    do mais recente para o mais antigo, para visualização da gerência.
    """
    if 'usuario_logado' not in request.session:
        return redirect('login')
    
    auditorias = AuditoriaEstoque.objects.select_related('produto').order_by('-data_alteracao')
    
    return render(request, 'inventario/auditoria_estoque.html', {'auditorias': auditorias})

def api_cancelar_entrada_seguro(request):
    """
    Valida a assinatura de segurança e retira (estorna) as quantidades 
    do estoque referentes a uma Nota Fiscal cancelada, gerando auditoria.
    """
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            motivo = dados.get('motivo')
            usuario_login = dados.get('usuario')
            senha_digitada = dados.get('senha')
            itens = dados.get('itens', [])

            # Validação de Segurança na sua tabela customizada
            usuario_valido = Usuarios.objects.filter(login=usuario_login, senha=senha_digitada).first()
            if not usuario_valido:
                return JsonResponse({'status': 'erro', 'mensagem': 'Credenciais inválidas. Cancelamento recusado.'})
            
            with transaction.atomic():
                for item in itens:
                    produto_id = item.get('id')
                    qtd_estornar = int(item.get('qtd', 0))
                    
                    if qtd_estornar > 0:
                        produto = get_object_or_404(Produtos, id=produto_id)
                        estoque_antigo = produto.estoque_atual
                        novo_estoque = estoque_antigo - qtd_estornar
                        
                        # Calculo financeiro negativo para o estorno
                        diferenca_financeira = float(produto.preco_custo) * (-qtd_estornar)
                        
                        produto.estoque_atual = novo_estoque
                        produto.save()
                        
                        # Grava na Auditoria o estorno do estoque
                        AuditoriaEstoque.objects.create(
                            produto=produto,
                            estoque_antigo=estoque_antigo,
                            estoque_novo=novo_estoque,
                            diferenca_quantidade=-qtd_estornar,
                            diferenca_financeira=diferenca_financeira,
                            motivo=f"Estorno de NF - {motivo}",
                            usuario=usuario_valido.login
                        )
                        
            return JsonResponse({'status': 'sucesso'})
            
        except Exception as e:
            return JsonResponse({'status': 'erro', 'mensagem': str(e)})
            
    return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido.'})

def tela_conferencia_scanner(request, chave):
    """
    Renderiza a interface isolada para contagem física de mercadorias 
    recebidas no XML utilizando leitor de código de barras.
    """
    if 'usuario_logado' not in request.session:
        return redirect('login')
        
    return render(request, 'inventario/conferencia_scanner.html', {'chave': chave})

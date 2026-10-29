from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from inventario.models.produtos.produto_models import Familia, Marca, TributacaoCFOP, TributacaoCSOSN

# Importações direcionadas para a nova estrutura de pastas (Fat Models)
from inventario.models.produtos.produto_models import Familia, Marca
from inventario.models.usuarios.usuario_models import Usuarios
from inventario.models.vendas.venda_models import ConfiguracaoPontos, Vendas

# ==========================================
# ⚙️ GESTÃO DE MARCAS E FAMÍLIAS
# ==========================================

def tela_marcas(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    
    familias = Familia.objects.all().order_by('nome')
    marcas = Marca.objects.all().order_by('nome')
    
    return render(request, 'inventario/gerencia_auxiliares.html', {
        'familias': familias, 
        'marcas': marcas, 
        'marcas_list': marcas, 
        'fabricantes': marcas, 
        'aba_ativa': 'marcas'
    })

def salvar_marca(request):
    if request.method == 'POST':
        marca_id = request.POST.get('marca_id')
        nome = request.POST.get('nome')
        
        if marca_id:
            marca = get_object_or_404(Marca, id=marca_id)
            marca.nome = nome
            marca.save()
            messages.success(request, f"Marca '{nome}' atualizada!")
        else:
            Marca.objects.create(nome=nome)
            messages.success(request, f"Marca '{nome}' cadastrada!")
            
    return redirect('tela_marcas')

def excluir_marca(request, id):
    marca = get_object_or_404(Marca, id=id)
    nome = marca.nome
    marca.delete()
    messages.success(request, f"Marca '{nome}' excluída!")
    return redirect('tela_marcas')

def tela_familias(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
        
    familias = Familia.objects.all().order_by('nome')
    marcas = Marca.objects.all().order_by('nome')
    
    return render(request, 'inventario/gerencia_auxiliares.html', {
        'familias': familias, 
        'familias_list': familias, 
        'grupos': familias, 
        'marcas': marcas, 
        'aba_ativa': 'familias'
    })

def salvar_familia(request):
    if request.method == 'POST':
        familia_id = request.POST.get('familia_id')
        nome = request.POST.get('nome')
        
        if familia_id:
            familia = get_object_or_404(Familia, id=familia_id)
            familia.nome = nome
            familia.save()
            messages.success(request, f"Família '{nome}' atualizada com sucesso!")
        else:
            Familia.objects.create(nome=nome)
            messages.success(request, f"Família '{nome}' cadastrada!")
            
    return redirect('tela_familias')

def excluir_familia(request, id):
    familia = get_object_or_404(Familia, id=id)
    nome = familia.nome
    familia.delete()
    messages.success(request, f"Família '{nome}' excluída!")
    return redirect('tela_familias')


# ==========================================
# 👥 GESTÃO DE EQUIPA E COMISSÕES
# ==========================================

def tela_colaboradores(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    lista_equipe = Usuarios.objects.all()

    for colaborador in lista_equipe:
        # A view usa a agregação do banco de dados (mais rápido que o loop antigo)
        total_vendido = Vendas.objects.filter(
            vendedor=colaborador.login, 
            status='VENDA'
        ).aggregate(total=Sum('valor_total'))['total'] or 0.0

        # Delegação para o FAT MODEL: A classe Usuário calcula a sua própria comissão
        comissao_a_pagar = colaborador.calcular_comissao(total_vendido)

        colaborador.total_vendido = float(total_vendido)
        colaborador.comissao_a_pagar = float(comissao_a_pagar)

    return render(request, 'inventario/colaboradores.html', {'equipe': lista_equipe})

def salvar_colaborador(request):
    if request.method == 'POST':
        colaborador_id = request.POST.get('colaborador_id')
        login = request.POST.get('login', '').strip()
        senha_nova = request.POST.get('senha', '').strip()
        perfil = request.POST.get('perfil', 'Colaborador')
        comissao = request.POST.get('comissao', '0.00').replace(',', '.')

        try:
            if colaborador_id and colaborador_id.strip() and colaborador_id != 'None':
                colaborador = get_object_or_404(Usuarios, id=colaborador_id)

                if Usuarios.objects.filter(login=login).exclude(id=colaborador.id).exists():
                    messages.error(request, f"Erro: O login '{login}' já está em uso por outra pessoa!")
                    return redirect('tela_colaboradores')

                colaborador.login = login
                if senha_nova:
                    colaborador.senha = senha_nova
                colaborador.perfil = perfil
                colaborador.comissao = comissao
                colaborador.save()
                messages.success(request, f"Colaborador '{login}' atualizado com sucesso!")
            else:
                colaborador_existente = Usuarios.objects.filter(login=login).first()
                if colaborador_existente:
                    if senha_nova:
                        colaborador_existente.senha = senha_nova
                    colaborador_existente.perfil = perfil
                    colaborador_existente.comissao = comissao
                    colaborador_existente.save()
                    messages.success(request, f"Colaborador '{login}' atualizado com sucesso!")
                else:
                    Usuarios.objects.create(login=login, senha=senha_nova, perfil=perfil, comissao=comissao)
                    messages.success(request, f"Colaborador '{login}' cadastrado com sucesso!")

        except Exception as e:
            messages.error(request, f"Erro inesperado ao salvar alterações: {str(e)}")

    return redirect('tela_colaboradores')

def excluir_colaborador(request, id):
    colaborador = get_object_or_404(Usuarios, id=id)
    login = colaborador.login
    colaborador.delete()
    messages.success(request, f"Colaborador '{login}' removido com sucesso!")
    return redirect('tela_colaboradores')


# ==========================================
# ⚙️ REGRAS DE FIDELIDADE (PONTUAÇÃO)
# ==========================================

def tela_manutencao_pontos(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
        
    return render(request, 'inventario/manutencao_pontos.html', {
        'conf_cliente': ConfiguracaoPontos.objects.filter(tipo_usuario='CLIENTE').first(),
        'conf_pintor': ConfiguracaoPontos.objects.filter(tipo_usuario='PINTOR').first()
    })

def salvar_configuracao_pontos(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo_usuario')
        pontos_raw = request.POST.get('pontos_por_real', '1')
        
        try:
            pontos = int(pontos_raw) if pontos_raw.strip() != "" else 1
        except ValueError:
            pontos = 1

        config, created = ConfiguracaoPontos.objects.get_or_create(tipo_usuario=tipo)
        # ATUALIZAÇÃO: Agora altera a nova coluna pontos_por_real
        config.pontos_por_real = pontos
        
        # Garante que o divisor universal esteja travado em 100
        config.divisor_resgate = 100
        config.save()

        messages.success(request, f"Regras de pontuação para {tipo.lower()} salvas com sucesso!")

    return redirect('tela_manutencao_pontos')


# ==========================================
# ⚖️ CONFIGURAÇÕES FISCAIS (CFOP / CSOSN)
# ==========================================
def tela_config_fiscal(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')

    context = {
        'cfops': TributacaoCFOP.objects.all().order_by('codigo'),
        'csosns': TributacaoCSOSN.objects.all().order_by('codigo')
    }
    return render(request, 'inventario/config_fiscal.html', context)

def salvar_cfop(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        if codigo and descricao:
            TributacaoCFOP.objects.create(codigo=codigo, descricao=descricao, ativo=True)
            messages.success(request, f"CFOP {codigo} cadastrado com sucesso!")
    return redirect('tela_config_fiscal')

def alternar_cfop(request, id):
    cfop = get_object_or_404(TributacaoCFOP, id=id)
    cfop.ativo = not cfop.ativo
    cfop.save()
    return redirect('tela_config_fiscal')

def excluir_cfop(request, id):
    cfop = get_object_or_404(TributacaoCFOP, id=id)
    cfop.delete()
    messages.success(request, "CFOP excluído com sucesso!")
    return redirect('tela_config_fiscal')

def salvar_csosn(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        if codigo and descricao:
            TributacaoCSOSN.objects.create(codigo=codigo, descricao=descricao, ativo=True)
            messages.success(request, f"CSOSN {codigo} cadastrado!")
    return redirect('tela_config_fiscal')

def alternar_csosn(request, id):
    csosn = get_object_or_404(TributacaoCSOSN, id=id)
    csosn.ativo = not csosn.ativo
    csosn.save()
    return redirect('tela_config_fiscal')

def excluir_csosn(request, id):
    csosn = get_object_or_404(TributacaoCSOSN, id=id)
    csosn.delete()
    messages.success(request, "CSOSN excluído com sucesso!")
    return redirect('tela_config_fiscal')

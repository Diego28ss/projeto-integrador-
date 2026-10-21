from django.shortcuts import render, redirect
from django.contrib import messages
from inventario.models.usuarios.usuario_models import Usuarios

def tela_login(request):
    if 'usuario_logado' in request.session:
        return redirect('painel_principal')

    if request.method == 'POST':
        login_input = request.POST.get('login', '').strip()
        senha_input = request.POST.get('senha', '').strip()

        try:
            colaborador = Usuarios.objects.filter(login=login_input, senha=senha_input).first()

            if colaborador:
                request.session['usuario_logado'] = colaborador.login
                request.session['perfil_usuario'] = colaborador.perfil
                messages.success(request, f"Bem-vindo de volta, {colaborador.login}!")
                return redirect('painel_principal')
            else:
                messages.error(request, "Usuário ou senha incorretos.")
        except Exception as e:
            print(f"Erro crítico no login: {e}")
            messages.error(request, "Ocorreu um erro interno ao tentar realizar o login. Tente novamente.")

    return render(request, 'inventario/login.html')

def logout(request):
    request.session.flush()
    return redirect('login')

def painel_principal(request):
    if 'usuario_logado' not in request.session:
        return redirect('login')
    return render(request, 'inventario/index.html')

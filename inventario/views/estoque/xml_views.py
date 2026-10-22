from django.shortcuts import render, redirect

def tela_conferencia_xml(request, chave):
    """
    Renderiza a tela de conferência detalhada da NF-e.
    A chave é passada pela URL e enviada ao template para o JavaScript buscar os itens na memória.
    """
    if 'usuario_logado' not in request.session:
        return redirect('login')
        
    return render(request, 'inventario/conferencia_xml.html', {'chave': chave})

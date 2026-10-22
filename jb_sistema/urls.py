from django.contrib import admin
from django.urls import path

# Importações das novas Thin Views separadas por módulo
from inventario.views import autenticacao_views
from inventario.views.vendas import pdv_views, relatorios_views
from inventario.views.estoque import estoque_views
from inventario.views.clientes import cliente_views
from inventario.views.configuracoes import config_views
from inventario.views.estoque import estoque_views, xml_views

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),

    # 🔐 Autenticação
    path('', autenticacao_views.tela_login, name='login'),
    path('logout/', autenticacao_views.logout, name='logout'),

    # 📊 Painel Principal
    path('painel/', autenticacao_views.painel_principal, name='painel_principal'),

    # 🛒 Frente de Caixa (PDV) e APIs de Venda
    path('pdv/', pdv_views.tela_pdv, name='tela_pdv'),
    path('api/consultar-pontos/', pdv_views.api_consultar_pontos, name='api_consultar_pontos'),
    path('api/salvar-venda/', pdv_views.api_salvar_venda, name='api_salvar_venda'),
    path('api/buscar-produtos/', pdv_views.api_buscar_produtos, name='api_buscar_produtos'),

    # 📦 Controle de Estoque
    path('estoque/', estoque_views.tela_estoque_produtos, name='tela_estoque_produtos'),
    path('estoque/salvar/', estoque_views.salvar_produto, name='salvar_produto'),
    path('estoque/excluir/<int:id>/', estoque_views.excluir_produto, name='excluir_produto'),
    path('entrada-carga/', estoque_views.tela_entrada_carga, name='tela_entrada_carga'),
    path('api/produto-por-codigo/', estoque_views.api_produto_por_codigo, name='api_produto_por_codigo'),
    path('api/efetivar-entrada/', estoque_views.api_efetivar_entrada, name='api_efetivar_entrada'),
    path('api/upload-xml/', estoque_views.api_upload_xml, name='api_upload_xml'),
    path('entrada-carga/conferencia/<str:chave>/', xml_views.tela_conferencia_xml, name='tela_conferencia_xml'),
    path('gerencia/fiscal/', config_views.tela_config_fiscal, name='tela_config_fiscal'),
    path('gerencia/fiscal/cfop/salvar/', config_views.salvar_cfop, name='salvar_cfop'),
    path('gerencia/fiscal/cfop/alternar/<int:id>/', config_views.alternar_cfop, name='alternar_cfop'),
    path('gerencia/fiscal/cfop/excluir/<int:id>/', config_views.excluir_cfop, name='excluir_cfop'),
    path('gerencia/fiscal/csosn/salvar/', config_views.salvar_csosn, name='salvar_csosn'),
    path('gerencia/fiscal/csosn/alternar/<int:id>/', config_views.alternar_csosn, name='alternar_csosn'),
    path('gerencia/fiscal/csosn/excluir/<int:id>/', config_views.excluir_csosn, name='excluir_csosn'),
    
    

    # 👥 Clientes
    path('clientes/', cliente_views.tela_consultar_clientes, name='tela_consultar_clientes'),
    path('clientes/editar/', cliente_views.salvar_edicao_cliente, name='salvar_edicao_cliente'),
    path('clientes/excluir/<int:id>/', cliente_views.excluir_cliente, name='excluir_cliente'),
    path('api/historico-cliente/', cliente_views.api_historico_cliente, name='api_historico_cliente'),

    # ⚙️ Gerência de Auxiliares
    path('gerencia/auxiliares/', config_views.tela_marcas, name='tela_gerencia_auxiliares'),
    path('gerencia/marcas/', config_views.tela_marcas, name='tela_marcas'),
    path('gerencia/familias/', config_views.tela_familias, name='tela_familias'),
    path('gerencia/auxiliares/marca/salvar/', config_views.salvar_marca, name='salvar_marca'),
    path('gerencia/auxiliares/marca/excluir/<int:id>/', config_views.excluir_marca, name='excluir_marca'),
    path('gerencia/auxiliares/familia/salvar/', config_views.salvar_familia, name='salvar_familia'),
    path('gerencia/auxiliares/familia/excluir/<int:id>/', config_views.excluir_familia, name='excluir_familia'),

    # 📄 Relatórios e Impressão
    path('gerencia/relatorios/', relatorios_views.tela_relatorios, name='tela_relatorios'),
    path('venda/cupom/<int:id>/', relatorios_views.imprimir_cupom, name='imprimir_cupom'),
    path('gerencia/vendas/cancelar/', relatorios_views.cancelar_venda, name='cancelar_venda'),
    path('venda/cupom-a4/<int:id>/', relatorios_views.imprimir_cupom_a4, name='imprimir_cupom_a4'),

    # 🔄 ROTAS DE COMPATIBILIDADE (Fallbacks e Soluções de Cache)
    path('cupom/<int:id>/', relatorios_views.imprimir_cupom),
    path('cupom_a4/<int:id>/', relatorios_views.imprimir_cupom_a4),

    # Pedidos com underline para compatibilidade de rotas antigas
    path('api/produto_por_codigo/', estoque_views.api_produto_por_codigo),
    path('api/efetivar_entrada/', estoque_views.api_efetivar_entrada),

    # 👥 Gestão de Equipe e Pontos
    path('gerencia/colaboradores/', config_views.tela_colaboradores, name='tela_colaboradores'),
    path('gerencia/colaboradores/salvar/', config_views.salvar_colaborador, name='salvar_colaborador'),
    path('gerencia/colaboradores/excluir/<int:id>/', config_views.excluir_colaborador, name='excluir_colaborador'),
    path('gerencia/pontos/', config_views.tela_manutencao_pontos, name='tela_manutencao_pontos'),
    path('gerencia/pontos/salvar/', config_views.salvar_configuracao_pontos, name='salvar_configuracao_pontos'),
]
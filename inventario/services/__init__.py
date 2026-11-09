from .clientes.pontos_services import calcular_resgate_pontos
from .clientes.cliente_services import salvar_dados_cliente
from .vendas.pdv_services import processar_nova_venda, autorizar_cancelamento
from .vendas.dashboard_services import obter_metricas_dashboard, calcular_totais_colaboradores
from .estoque.xml_services import processar_upload_xml

# NOVO: Importando as funções de serviço do Caixa
from .vendas.caixa_services import (
    autenticar_dupla_credencial, 
    abrir_caixa, 
    registrar_sangria, 
    fechar_caixa
)

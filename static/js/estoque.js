let meuModal;

document.addEventListener("DOMContentLoaded", function () {
    meuModal = new bootstrap.Modal(document.getElementById('modalProduto'));
});

function calcularVenda() {
    let custo = parseFloat(document.getElementById('formPrecoCusto').value.replace(',', '.')) || 0;
    let margem = parseFloat(document.getElementById('formMargemLucro').value.replace(',', '.')) || 0;
    let venda = custo + (custo * (margem / 100));
    document.getElementById('formPrecoVenda').value = venda.toFixed(2).replace('.', ',');
}

function abrirModalNovo() {
    document.getElementById('modalTitulo').innerText = "📦 Novo Produto";
    document.getElementById('formId').value = "";
    document.getElementById('formCodInterno').value = ""; // Fica vazio para o sistema gerar
    document.getElementById('formNome').value = "";
    document.getElementById('formCodBarras').value = "";
    
    // Campos Fiscais
    document.getElementById('formCodFornecedor').value = "";
    document.getElementById('formNCM').value = "";
    document.getElementById('formCEST').value = "";
    document.getElementById('formCFOP').value = "";
    document.getElementById('formCSOSN').value = "";

    document.getElementById('formPrecoCusto').value = "0,00";
    document.getElementById('formMargemLucro').value = "0,00";
    document.getElementById('formPrecoVenda').value = "0,00";
    document.getElementById('formMarca').value = "";
    document.getElementById('formFamilia').value = "";
    document.getElementById('formStatus').value = "ATIVO";
    document.getElementById('formEstoque').value = "0";
    document.getElementById('formUnidade').value = "UN";
    
    meuModal.show();
}

function prepararEdicao(botao) {
    document.getElementById('modalTitulo').innerText = "✏️ Editar Produto";
    document.getElementById('formId').value = botao.getAttribute('data-id');
    document.getElementById('formCodInterno').value = botao.getAttribute('data-codinterno');
    document.getElementById('formNome').value = botao.getAttribute('data-nome');
    document.getElementById('formCodBarras').value = botao.getAttribute('data-cod');
    
    // Campos Fiscais
    document.getElementById('formCodFornecedor').value = botao.getAttribute('data-codfornecedor');
    document.getElementById('formNCM').value = botao.getAttribute('data-ncm');
    document.getElementById('formCEST').value = botao.getAttribute('data-cest');
    document.getElementById('formCFOP').value = botao.getAttribute('data-cfop');
    document.getElementById('formCSOSN').value = botao.getAttribute('data-csosn');

    let custo = botao.getAttribute('data-custo').replace('.', ',');
    let margem = botao.getAttribute('data-margem').replace('.', ',');
    let venda = botao.getAttribute('data-venda').replace('.', ',');

    document.getElementById('formPrecoCusto').value = custo;
    document.getElementById('formMargemLucro').value = margem;
    document.getElementById('formPrecoVenda').value = venda;

    document.getElementById('formMarca').value = botao.getAttribute('data-marca');
    document.getElementById('formFamilia').value = botao.getAttribute('data-familia');

    let status = botao.getAttribute('data-status');
    document.getElementById('formStatus').value = status ? status : "ATIVO";

    document.getElementById('formEstoque').value = botao.getAttribute('data-estoque');
    document.getElementById('formUnidade').value = botao.getAttribute('data-unidade');

    meuModal.show();
}

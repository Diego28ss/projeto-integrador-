let produtoAtivo = null;
let contagemBipador = 0;
let modalAssinatura;

document.addEventListener("DOMContentLoaded", function() {
    modalAssinatura = new bootstrap.Modal(document.getElementById('modalAssinaturaAcerto'));

    // Eventos de Busca
    document.getElementById('btnBuscarManual').addEventListener('click', buscarProdutoAcerto);
    document.getElementById('inputBuscaManual').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            buscarProdutoAcerto();
        }
    });

    // Eventos do Bipador (Scanner)
    document.getElementById('inputBipadorAcerto').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            processarBipe(this.value.trim());
        }
    });

    // Ações de Contagem e Limpeza
    document.getElementById('btnGravarContagem').addEventListener('click', transferirContagemParaManual);
    document.getElementById('btnLimparAcerto').addEventListener('click', limparBipador);

    // Finalização
    document.getElementById('btnAtualizarEstoque').addEventListener('click', prepararAssinatura);
    document.getElementById('btnConfirmarAssinatura').addEventListener('click', efetivarAcertoSeguro);
});

// ==========================================
// 1. BUSCA E SELEÇÃO DE PRODUTO
// ==========================================
function buscarProdutoAcerto() {
    let q = document.getElementById('inputBuscaManual').value.trim();
    if (q.length < 2) return;
    
    // Usaremos uma nova API que criaremos na Fase 4 para trazer também o código de barras
    fetch(`/api/estoque/buscar-acerto/?q=${q}`)
    .then(res => res.json())
    .then(data => {
        let html = '';
        data.produtos.forEach(p => {
            html += `
            <button class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" 
                onclick="selecionarProduto(${p.id}, '${p.nome.replace(/'/g, "\\'")}', '${p.cod_interno}', '${p.cod_barras}', ${p.estoque})">
                <div>
                    <strong class="text-dark">${p.nome}</strong><br>
                    <small class="text-muted">Cód: ${p.cod_interno} | EAN: ${p.cod_barras || 'Sem código'}</small>
                </div>
                <span class="badge bg-dark fs-6">${p.estoque} UN</span>
            </button>`;
        });
        let lista = document.getElementById('listaBuscaManual');
        lista.innerHTML = html || '<p class="text-muted p-3 mb-0">Nenhum produto encontrado.</p>';
        lista.style.display = 'block';
    });
}

function selecionarProduto(id, nome, codInterno, codBarras, estoque) {
    produtoAtivo = {
        id: id,
        nome: nome,
        codInterno: codInterno,
        codBarras: codBarras || 'SEM_CODIGO',
        estoque: estoque
    };

    // Atualiza Módulo 2 (Manual)
    document.getElementById('manualNomeProduto').innerText = nome;
    document.getElementById('manualCodProduto').innerText = `Cód Interno: ${codInterno} | EAN: ${codBarras || '---'}`;
    document.getElementById('manualEstoqueAtual').value = estoque;
    document.getElementById('manualNovoEstoque').value = estoque;
    document.getElementById('manualNovoEstoque').disabled = false;
    document.getElementById('btnAtualizarEstoque').disabled = false;

    // Atualiza Módulo 1 (Bipador)
    document.getElementById('lblNomeProdutoBipado').innerText = nome;
    document.getElementById('lblCodProdutoBipado').innerText = `EAN Esperado: ${codBarras || 'Produto sem código de barras'}`;
    document.getElementById('lblEstoqueAtual').innerText = estoque;
    
    let inputBipador = document.getElementById('inputBipadorAcerto');
    if (codBarras) {
        inputBipador.disabled = false;
        inputBipador.placeholder = "Pode bipar...";
        document.getElementById('labelBipador').innerText = "Scanner Liberado - Aguardando bipagem";
        document.getElementById('labelBipador').className = "form-label fw-bold text-success";
        inputBipador.focus();
    } else {
        inputBipador.disabled = true;
        inputBipador.placeholder = "Bloqueado (Sem EAN)";
        document.getElementById('labelBipador').innerText = "Produto não possui Código de Barras cadastrado.";
        document.getElementById('labelBipador').className = "form-label fw-bold text-danger";
    }

    document.getElementById('btnGravarContagem').disabled = false;
    document.getElementById('listaBuscaManual').style.display = 'none';
    document.getElementById('inputBuscaManual').value = '';
    
    // Reseta a contagem atual
    limparBipador();
}

// Oculta a lista de busca ao clicar fora
document.addEventListener('click', function(e) {
    if (!e.target.closest('#listaBuscaManual') && !e.target.closest('#inputBuscaManual')) {
        document.getElementById('listaBuscaManual').style.display = 'none';
    }
});

// ==========================================
// 2. LÓGICA DO SCANNER (BIPADOR)
// ==========================================
function processarBipe(codigoLido) {
    let inputBipador = document.getElementById('inputBipadorAcerto');
    
    if (!produtoAtivo) return;

    if (codigoLido === produtoAtivo.codBarras) {
        contagemBipador++;
        document.getElementById('lblNovaContagem').innerText = contagemBipador;
        inputBipador.value = ''; // Limpa para o próximo bipe instantaneamente
    } else {
        alert(`⚠️ ATENÇÃO: O código lido (${codigoLido}) não pertence ao produto selecionado (${produtoAtivo.nome}).`);
        inputBipador.value = '';
    }
}

function limparBipador() {
    contagemBipador = 0;
    document.getElementById('lblNovaContagem').innerText = "0";
    let inputBipador = document.getElementById('inputBipadorAcerto');
    inputBipador.value = '';
    if (!inputBipador.disabled) inputBipador.focus();
}

function transferirContagemParaManual() {
    if (contagemBipador === 0) {
        alert("A contagem está zerada.");
        return;
    }
    document.getElementById('manualNovoEstoque').value = contagemBipador;
    document.getElementById('manualNovoEstoque').classList.add('is-valid');
    setTimeout(() => document.getElementById('manualNovoEstoque').classList.remove('is-valid'), 2000);
}

// ==========================================
// 3. ASSINATURA DE SEGURANÇA E GRAVAÇÃO
// ==========================================
function prepararAssinatura() {
    if (!produtoAtivo) return;
    
    let novoEstoque = document.getElementById('manualNovoEstoque').value;
    
    if (novoEstoque === "" || parseInt(novoEstoque) < 0) {
        alert("Digite um estoque válido.");
        return;
    }

    if (parseInt(novoEstoque) === parseInt(produtoAtivo.estoque)) {
        alert("O novo estoque é igual ao estoque atual. Nenhuma alteração necessária.");
        return;
    }

    // Preenche o Modal com os dados
    document.getElementById('lblConfirmacaoProduto').innerText = produtoAtivo.nome;
    document.getElementById('lblConfirmacaoAntigo').innerText = produtoAtivo.estoque;
    document.getElementById('lblConfirmacaoNovo').innerText = novoEstoque;
    
    // Limpa campos de segurança
    document.getElementById('motivoAcerto').value = "";
    document.getElementById('usuarioAcerto').value = "";
    document.getElementById('senhaAcerto').value = "";
    
    modalAssinatura.show();
}

function efetivarAcertoSeguro() {
    let motivo = document.getElementById('motivoAcerto').value;
    let usuario = document.getElementById('usuarioAcerto').value.trim();
    let senha = document.getElementById('senhaAcerto').value;
    let novoEstoque = parseInt(document.getElementById('manualNovoEstoque').value);

    if (!motivo || !usuario || !senha) {
        alert("Preencha todos os campos de segurança obrigatórios.");
        return;
    }

    let payload = {
        produto_id: produtoAtivo.id,
        novo_estoque: novoEstoque,
        motivo: motivo,
        usuario: usuario,
        senha: senha
    };

    // Chamada para a API da Fase 4
    fetch('/api/estoque/efetivar-acerto-seguro/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfTokenConfig },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'sucesso') {
            alert(`✅ Acerto concluído!\nNovo estoque de ${produtoAtivo.nome}: ${novoEstoque} UN`);
            modalAssinatura.hide();
            // Reseta a tela para o próximo produto
            window.location.reload();
        } else {
            alert("❌ Erro de Segurança: " + data.mensagem);
        }
    })
    .catch(err => {
        alert("Erro de comunicação com o servidor.");
    });
}

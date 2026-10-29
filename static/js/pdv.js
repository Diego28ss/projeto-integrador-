let carrinho = [];
let tagsBusca = [];
let pointsToRedeem = 0;
let valorDescontoPontosAplicado = 0.0;
let descontoGlobalAplicado = false;

document.addEventListener("DOMContentLoaded", function() {
    const inputBusca = document.getElementById('inputBusca');
    if (inputBusca) inputBusca.focus();
});

function adicionarItemAoCarrinho(produto) {
    let item = carrinho.find(i => i.id === produto.id);
    if (item) {
        item.qtd++;
    } else {
        carrinho.push({
            id: produto.id,
            nome: produto.nome,
            preco: parseFloat(produto.preco_venda),
            preco_desconto: parseFloat(produto.preco_venda),
            qtd: 1
        });
    }
    descontoGlobalAplicado = false;
    atualizarTela();
}

function tratarInputBusca(event, input) {
    let texto = input.value.trim();

    if (event.key === "Enter") {
        event.preventDefault();
        if (!texto && tagsBusca.length === 0) return;

        let query = texto;
        if (tagsBusca.length > 0) {
            query = tagsBusca.join(" ") + (texto ? " " + texto : "");
        }

        fetch(`/api/buscar-produtos/?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                const produtos = data.produtos || [];

                let produtoExato = produtos.find(p => p.cod_barras && p.cod_barras.trim() === texto);
                if (produtoExato) {
                    adicionarItemAoCarrinho(produtoExato);
                    input.value = "";
                    tagsBusca = [];
                    renderizarTags();
                    document.getElementById('resultadosBusca').style.display = 'none';
                    return;
                }

                if (produtos.length === 1) {
                    adicionarItemAoCarrinho(produtos[0]);
                    input.value = "";
                    tagsBusca = [];
                    renderizarTags();
                    document.getElementById('resultadosBusca').style.display = 'none';
                    return;
                }

                if (texto !== "") {
                    tagsBusca.push(texto.toUpperCase());
                    input.value = "";
                    renderizarTags();
                    buscarProduto("");
                }
            })
            .catch(err => console.error("Erro na busca de produtos:", err));
    } else {
        setTimeout(() => {
            buscarProduto(input.value.trim());
        }, 100);
    }
}

function renderizarTags() {
    let html = '';
    tagsBusca.forEach((tag, index) => {
        html += `<span class="badge text-white me-2 mb-2 p-2 fs-6 shadow-sm d-flex align-items-center" style="background-color: #888B8D;">
                    ${tag}
                    <i class="bi bi-x-circle ms-2" style="cursor: pointer;" onclick="removerTag(${index})"></i>
                 </span>`;
    });
    document.getElementById('areaTags').innerHTML = html;
}

function removerTag(index) {
    tagsBusca.splice(index, 1);
    renderizarTags();
    buscarProduto(document.getElementById('inputBusca').value.trim());
}

function buscarProduto(textoDigitado) {
    let termosParaBuscar = [...tagsBusca];
    if (textoDigitado.length > 0) termosParaBuscar.push(textoDigitado);
    let queryFinal = termosParaBuscar.join(" ");

    if (queryFinal.length < 2) {
        document.getElementById('resultadosBusca').style.display = 'none';
        return;
    }

    fetch(`/api/buscar-produtos/?q=${encodeURIComponent(queryFinal)}`)
        .then(res => res.json())
        .then(data => {
            let html = '';
            if(data.produtos.length === 0) {
                html = '<div class="list-group-item text-muted text-center py-3">Nenhum produto encontrado.</div>';
            } else {
                data.produtos.forEach((p) => {
                    let nomeSeguro = p.nome.replace(/"/g, '&quot;').replace(/'/g, "\\'");
                    html += `<button type="button"
                                class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                                data-id="${p.id}" data-nome="${nomeSeguro}" data-preco="${p.preco_venda}"
                                onclick="adicionarDiretoDoBotao(this)">
                                <span class="text-start"><strong>${p.nome}</strong><br><small class="text-muted">Estoque: ${p.estoque_atual} | Cód: ${p.cod_barras || 'S/N'}</small></span>
                                <strong style="color: #00C853;" class="fs-5">R$ ${p.preco_venda.toFixed(2).replace('.', ',')}</strong>
                             </button>`;
                });
            }
            document.getElementById('resultadosBusca').innerHTML = html;
            document.getElementById('resultadosBusca').style.display = 'block';
        });
}

function adicionarDiretoDoBotao(botao) {
    let id = parseInt(botao.getAttribute('data-id'));
    let nome = botao.getAttribute('data-nome');
    let preco = parseFloat(botao.getAttribute('data-preco'));

    adicionarItemAoCarrinho({ id: id, nome: nome, preco_venda: preco });

    document.getElementById('resultadosBusca').style.display = 'none';
    document.getElementById('inputBusca').value = '';
    tagsBusca = [];
    renderizarTags();
    document.getElementById('inputBusca').focus();
}

function atualizarTela() {
    let html = '';
    let totalComDescontosItens = 0;

    carrinho.forEach((item, index) => {
        if (item.preco_desconto === undefined) item.preco_desconto = item.preco;
        let totalLinha = item.preco_desconto * item.qtd;
        totalComDescontosItens += totalLinha;

        html += `<tr>
            <td class="text-start fw-bold text-secondary">${item.nome}</td>
            <td><input type="number" class="form-control form-control-sm text-center fw-bold" value="${item.qtd}" min="1" onchange="mudarQtd(${index}, this.value)"></td>
            <td class="text-muted align-middle">R$ ${item.preco.toFixed(2).replace('.', ',')}</td>
            <td><input type="number" class="form-control form-control-sm text-center fw-bold" style="color: #00C853;" value="${item.preco_desconto.toFixed(2)}" step="0.01" min="0" onchange="mudarPrecoDesconto(${index}, this.value)"></td>
            <td class="text-dark fw-bold align-middle">R$ ${totalLinha.toFixed(2).replace('.', ',')}</td>
            <td><button type="button" class="btn btn-sm btn-link text-danger fs-5 p-0" onclick="removerItem(${index})"><i class="bi bi-trash-fill"></i></button></td>
        </tr>`;
    });

    document.getElementById('tabelaCarrinho').innerHTML = html;

    if (!descontoGlobalAplicado) {
        document.getElementById('inputValorFinal').value = totalComDescontosItens.toFixed(2);
        document.getElementById('inputDescontoPerc').value = '';
    }
    atualizarResumoCaixa();
}

function mudarQtd(index, valor) {
    carrinho[index].qtd = parseInt(valor) || 1;
    descontoGlobalAplicado = false;
    atualizarTela();
}

function mudarPrecoDesconto(index, valor) {
    carrinho[index].preco_desconto = parseFloat(valor) || carrinho[index].preco;
    descontoGlobalAplicado = false;
    atualizarTela();
}

function removerItem(index) {
    carrinho.splice(index, 1);
    descontoGlobalAplicado = false;
    atualizarTela();
}

function aplicarDescontoGlobalPorPorcentagem() {
    let perc = parseFloat(document.getElementById('inputDescontoPerc').value) || 0;
    let totalItens = carrinho.reduce((s, i) => s + (i.preco_desconto * i.qtd), 0);
    let novoValorFinal = totalItens - (totalItens * (perc / 100));

    document.getElementById('inputValorFinal').value = novoValorFinal.toFixed(2);
    descontoGlobalAplicado = true;
    atualizarResumoCaixa();
}

function aplicarDescontoGlobalPorValor() {
    let valorFinalInput = parseFloat(document.getElementById('inputValorFinal').value) || 0;
    let totalItens = carrinho.reduce((s, i) => s + (i.preco_desconto * i.qtd), 0);

    if (totalItens > 0) {
        let perc = ((totalItens - valorFinalInput) / totalItens) * 100;
        document.getElementById('inputDescontoPerc').value = perc.toFixed(2);
    } else {
        document.getElementById('inputDescontoPerc').value = '';
    }
    descontoGlobalAplicado = true;
    atualizarResumoCaixa();
}

function calcularTroco() {
    let total = parseFloat(document.getElementById('inputValorFinal').value) || 0;
    let recebido = parseFloat(document.getElementById('inputValorRecebido').value) || 0;
    let troco = recebido - total;

    if (recebido > 0 && troco >= 0) {
        document.getElementById('inputTroco').value = `R$ ${troco.toFixed(2).replace('.', ',')}`;
    } else {
        document.getElementById('inputTroco').value = 'R$ 0,00';
    }
}

function atualizarResumoCaixa() {
    let subtotalOriginal = carrinho.reduce((s, i) => s + (i.preco * i.qtd), 0);
    let valorFinal = parseFloat(document.getElementById('inputValorFinal').value) || 0;
    
    // A economia total é tudo que baixou do subtotal
    let economiaTotal = subtotalOriginal - valorFinal;
    
    // O desconto comum é a economia total MENOS o que veio de pontos
    let descontoComum = economiaTotal - valorDescontoPontosAplicado;
    if (descontoComum < 0.01) descontoComum = 0; // Previne errinhos de dízima no JS

    document.getElementById('txtSubtotal').innerText = `R$ ${subtotalOriginal.toFixed(2).replace('.', ',')}`;
    
    // Atualiza o Desconto Comum
    document.getElementById('txtDesconto').innerText = `- R$ ${descontoComum > 0 ? descontoComum.toFixed(2).replace('.', ',') : '0,00'}`;
    
    // Atualiza o Desconto de Pontos
    let linhaDescontoPontos = document.getElementById('linhaDescontoPontos');
    if (valorDescontoPontosAplicado > 0) {
        linhaDescontoPontos.style.display = 'flex';
        document.getElementById('txtDescontoPontos').innerText = `- R$ ${valorDescontoPontosAplicado.toFixed(2).replace('.', ',')}`;
    } else {
        linhaDescontoPontos.style.display = 'none';
    }

    document.getElementById('txtTotalCompra').innerText = `R$ ${valorFinal.toFixed(2).replace('.', ',')}`;

    calcularTroco();
}


function limparCarrinho() {
    if(confirm("Deseja realmente limpar toda a operação?")) {
        carrinho = [];
        tagsBusca = [];
        pointsToRedeem = 0;
        valorDescontoPontosAplicado = 0.0;
        descontoGlobalAplicado = false;
        renderizarTags();
        document.getElementById('inputBusca').value = '';
        document.getElementById('resultadosBusca').style.display = 'none';
        document.getElementById('selectCliente').value = '';
        document.getElementById('selectIndicante').value = '';
        document.getElementById('areaResgatePontos').style.display = 'none';
        document.getElementById('inputValorRecebido').value = '';
        document.getElementById('inputTroco').value = 'R$ 0,00';
        
        let btnVenda = document.getElementById('btnVenda');
        if(btnVenda) {
            btnVenda.disabled = false;
            btnVenda.style.opacity = '1';
            btnVenda.style.cursor = 'pointer';
        }
        
        atualizarTela();
    }
}


function verificarPontos() {
    let clienteId = document.getElementById('selectCliente').value;
    let areaResgate = document.getElementById('areaResgatePontos');
    let btnVenda = document.getElementById('btnVenda');
    
    pointsToRedeem = 0;
    valorDescontoPontosAplicado = 0.0;
    areaResgate.style.display = 'none';
    
    // Libera o botão por padrão
    if(btnVenda) {
        btnVenda.disabled = false;
        btnVenda.style.opacity = '1';
        btnVenda.style.cursor = 'pointer';
    }

    if (clienteId) {
        fetch(`/api/consultar-pontos/?cliente_id=${encodeURIComponent(clienteId)}`)
            .then(res => res.json())
            .then(data => {
                if (data.pontos_a_resgatar > 0) {
                    // TRAVA VISUAL E FUNCIONAL DO BOTÃO DE VENDA
                    if(btnVenda) {
                        btnVenda.disabled = true; 
                        btnVenda.style.opacity = '0.4'; // Deixa o botão apagadinho
                        btnVenda.style.cursor = 'not-allowed'; // Muda o mouse para proibido
                    }
                    
                    areaResgate.innerHTML = `
                        <div class="alert p-3 mb-0 shadow-sm text-center text-dark" style="background-color: #FFB81C; border: none; border-radius: 8px;">
                            <strong class="d-block mb-1 fs-5">🎁 Saldo: ${data.pontos} pontos</strong>
                            <span class="d-block mb-3">Vale <b>R$ ${data.valor_desconto.toFixed(2).replace('.', ',')}</b> de desconto!</span>
                            
                            <div class="d-flex gap-2">
                                <button type="button" class="btn text-white fw-bold w-50 shadow-sm" style="background-color: #101820;" onclick="aplicarDescontoPontos(${data.pontos_a_resgatar}, ${data.valor_desconto})">
                                    💰 RESGATAR
                                </button>
                                <button type="button" class="btn btn-outline-dark fw-bold w-50 shadow-sm" onclick="ignorarResgatePontos()">
                                    NÃO RESGATAR
                                </button>
                            </div>
                        </div>
                    `;
                    areaResgate.style.display = 'block';
                }
            })
            .catch(err => console.error("Erro ao buscar pontos:", err));
    }
}


function aplicarDescontoPontos(pontos, valorDesconto) {
    let totalComDescontosItens = carrinho.reduce((s, i) => s + (i.preco_desconto * i.qtd), 0);
    if (totalComDescontosItens <= 0) return alert("Adicione produtos no carrinho antes de aplicar o desconto!");

    if (valorDesconto > totalComDescontosItens) valorDesconto = totalComDescontosItens;

    pointsToRedeem = pontos;
    valorDescontoPontosAplicado = valorDesconto;

    let inputFinal = document.getElementById('inputValorFinal');
    inputFinal.value = (totalComDescontosItens - valorDesconto).toFixed(2);

    aplicarDescontoGlobalPorValor();

    // Esconde o painel amarelo
    document.getElementById('areaResgatePontos').style.display = 'none';
    
    // DESTRAVA O BOTÃO DE VENDA
    let btnVenda = document.getElementById('btnVenda');
    if(btnVenda) {
        btnVenda.disabled = false;
        btnVenda.style.opacity = '1';
        btnVenda.style.cursor = 'pointer';
    }
}


function finalizarOperacao(statusSelecionado) {
    if (carrinho.length === 0) return alert("O carrinho está vazio!");
    
    // BLOQUEIO DURO: Se o botão estiver desativado, impede a venda à força
    let btnVenda = document.getElementById('btnVenda');
    if (statusSelecionado === 'VENDA' && btnVenda && btnVenda.disabled === true) {
        return alert("⚠️ Atenção: Você precisa escolher se vai RESGATAR ou NÃO RESGATAR os pontos do cliente antes de finalizar a venda.");
    }

    let subtotalComDescontosItens = carrinho.reduce((s, i) => s + (i.preco_desconto * i.qtd), 0);
    let valorFinal = parseFloat(document.getElementById('inputValorFinal').value) || 0;
    
    let descontoGlobalAdicional = subtotalComDescontosItens - valorFinal;

    let pacote = {
        cliente_id: document.getElementById('selectCliente').value || null,
        indicante_id: document.getElementById('selectIndicante').value || null,
        vendedor: document.getElementById('selectVendedor').value,
        status: statusSelecionado,
        valor_final: valorFinal,
        desconto: descontoGlobalAdicional > 0 ? descontoGlobalAdicional : 0,
        pontos_resgatados: pointsToRedeem,
        valor_desconto_pontos: valorDescontoPontosAplicado,
        carrinho: carrinho
    };

    fetch('/api/salvar-venda/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfTokenConfig},
        body: JSON.stringify(pacote)
    }).then(res => res.json()).then(data => {
        if (data.status === 'sucesso') {
            if(statusSelecionado === 'ORCAMENTO') {
                alert('📝 Orçamento gerado com sucesso!');
            } else {
                alert('✅ Venda finalizada com sucesso! O estoque foi deduzido e a pontuação atualizada.');
            }

            window.open(`/venda/cupom/${data.venda_id}/`, '_blank', 'width=1024,height=850,scrollbars=yes,resizable=yes');
            location.reload();
        } else {
            alert("Erro ao salvar a operação: " + data.mensagem);
        }
    });
}

function ignorarResgatePontos() {
    pointsToRedeem = 0;
    valorDescontoPontosAplicado = 0.0;
    
    // Esconde o painel amarelo
    document.getElementById('areaResgatePontos').style.display = 'none';
    
    // DESTRAVA O BOTÃO DE VENDA
    let btnVenda = document.getElementById('btnVenda');
    if(btnVenda) {
        btnVenda.disabled = false;
        btnVenda.style.opacity = '1';
        btnVenda.style.cursor = 'pointer';
    }
}

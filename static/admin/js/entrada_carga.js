let itensEntrada = [];

// 1. CAPTURA O CÓDIGO
function processarBip(event, codigoBruto) {
    if (event.key === "Enter") {
        let codigoLimpo = codigoBruto.trim();
        if (codigoLimpo === "") return;

        let urlSegura = `/api/produto-por-codigo/?codigo=${codigoLimpo}&_nocache=${Date.now()}`;

        fetch(urlSegura)
            .then(res => {
                if (!res.ok) throw new Error("Erro na rota");
                return res.json();
            })
            .then(data => {
                if (data.status === 'ok') {
                    let item = itensEntrada.find(i => i.id === data.id);
                    if (item) {
                        item.qtd++;
                    } else {
                        itensEntrada.push({ id: data.id, nome: data.nome, codigo: codigoLimpo, qtd: 1 });
                    }
                    document.getElementById('bipador').value = '';
                    renderLista();
                } else {
                    alert(`❌ O servidor não encontrou o produto!\nCódigo: "${codigoLimpo}"`);
                    document.getElementById('bipador').value = '';
                }
            })
            .catch(error => alert("Erro ao buscar o produto."));
    }
}

// 2. ATUALIZA A TELA INICIAL COM OS NOVOS BOTÕES
function renderLista() {
    let html = '';
    itensEntrada.forEach(i => {
        html += `
        <tr>
            <td class="align-middle">${i.codigo}</td>
            <td class="text-start align-middle">${i.nome}</td>
            <td class="fw-bold text-success text-center align-middle" style="font-size: 1.2rem;">${i.qtd}</td>
            <td class="text-center align-middle">
                <button class="btn btn-sm btn-warning fw-bold shadow-sm me-1" onclick="editarQuantidade(${i.id}, '${i.nome}')" title="Editar Quantidade">✏️</button>
                <button class="btn btn-sm btn-danger fw-bold shadow-sm" onclick="removerItem(${i.id}, '${i.nome}')" title="Excluir Produto">🗑️</button>
            </td>
        </tr>`;
    });
    document.getElementById('listaEntrada').innerHTML = html;
}

// NOVA FUNÇÃO: EDITAR QUANTIDADE
function editarQuantidade(idProduto, nomeProduto) {
    let item = itensEntrada.find(i => i.id === idProduto);
    if (item) {
        let novaQtd = prompt(`Digite a nova quantidade para:\n📦 ${nomeProduto}`, item.qtd);

        if (novaQtd !== null && novaQtd.trim() !== "") {
            let qtdConvertida = parseInt(novaQtd);
            if (qtdConvertida > 0) {
                item.qtd = qtdConvertida;
                renderLista();
            } else {
                alert("A quantidade deve ser maior que zero!");
            }
        }
    }
}

// NOVA FUNÇÃO: REMOVER ITEM
function removerItem(idProduto, nomeProduto) {
    if (confirm(`Tem certeza que deseja remover "${nomeProduto}" da lista de entrada?`)) {
        itensEntrada = itensEntrada.filter(i => i.id !== idProduto);
        renderLista();
    }
}

// 3. ABRE O RELATÓRIO DE CONFERÊNCIA
function prepararConferencia() {
    if (itensEntrada.length === 0) return alert("Bipe algum produto antes de conferir!");

    let html = '';
    let totalFisico = 0;

    itensEntrada.forEach(i => {
        html += `<tr><td>${i.codigo}</td><td class="text-start">${i.nome}</td><td class="fw-bold text-center">${i.qtd}</td></tr>`;
        totalFisico += i.qtd;
    });
    document.getElementById('listaConferencia').innerHTML = html;
    document.getElementById('totalItensBadge').innerText = totalFisico;

    let agora = new Date();
    document.getElementById('dataHoraAtual').innerText = agora.toLocaleString('pt-BR');

    var myModal = new bootstrap.Modal(document.getElementById('modalConferencia'));
    myModal.show();
}

// 4. SALVA NO BANCO DE DADOS
function confirmarEfetivacao() {
    let btn = document.getElementById('btnConfirmar');
    btn.disabled = true;
    btn.innerText = "⏳ Salvando...";

    let urlSeguraEfetivar = `/api/efetivar-entrada/?_nocache=${Date.now()}`;

    fetch(urlSeguraEfetivar, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfTokenConfig },
        body: JSON.stringify({ itens: itensEntrada })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'sucesso') {
                alert("✅ Estoque atualizado com sucesso!");

                itensEntrada = [];
                renderLista();

                var modalEl = document.getElementById('modalConferencia');
                var modalObj = bootstrap.Modal.getInstance(modalEl);
                modalObj.hide();

                btn.disabled = false;
                btn.innerText = "✅ Confirmar Entrada no Estoque";
            } else {
                alert("Erro ao salvar: " + data.mensagem);
                btn.disabled = false;
                btn.innerText = "✅ Confirmar Entrada no Estoque";
            }
        })
        .catch(error => {
            alert("Erro ao tentar salvar no banco de dados.");
            btn.disabled = false;
            btn.innerText = "✅ Confirmar Entrada no Estoque";
        });
}

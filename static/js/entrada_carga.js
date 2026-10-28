let itensEntrada = [];

// ==========================================
// 📥 INICIALIZAÇÃO DA TELA
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById('listaNotas')) {
        carregarNotasDaMemoria();
    }
});

// ==========================================
// 🚀 ENVIO E PROCESSAMENTO DE XML
// ==========================================
function enviarXML(input) {
    if (input.files.length === 0) return;

    let arquivo = input.files[0];
    let formData = new FormData();
    formData.append('arquivo_xml', arquivo);

    let btnLabel = input.previousElementSibling;
    let textoOriginal = btnLabel.innerHTML;
    btnLabel.innerHTML = '<i class="bi bi-hourglass-split"></i> PROCESSANDO...';

    fetch('/api/upload-xml/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfTokenConfig },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        btnLabel.innerHTML = textoOriginal;
        
        if (data.status === 'sucesso') {
            let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
            
            if (notasSalvas.find(n => n.chave === data.dados.chave)) {
                alert("❌ Bloqueio de Segurança: Esta Nota Fiscal já foi importada e está na lista!");
                input.value = ""; 
                return;
            }

            let notaProcessada = data.dados;
            notaProcessada.status = 'Pendente';
            
            notasSalvas.push(notaProcessada);
            localStorage.setItem('xmls_jb_tintas', JSON.stringify(notasSalvas));
            
            alert("✅ XML importado! A inteligência de vínculos automáticos foi aplicada.");
            carregarNotasDaMemoria(); 
        } else {
            alert("❌ Erro no servidor: " + data.mensagem);
        }
    })
    .catch(erro => {
        btnLabel.innerHTML = textoOriginal;
        alert("❌ Erro de comunicação. Verifique se a rota da API existe.");
        console.error(erro);
    });

    input.value = ""; 
}

// ==========================================
// 📊 RENDERIZAÇÃO DA TABELA DE NOTAS
// ==========================================
function carregarNotasDaMemoria() {
    let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
    let tbody = document.getElementById('listaNotas');
    if (!tbody) return;
    
    let html = '';
    
    if (notasSalvas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-4 text-muted">Nenhuma nota importada. Utilize o botão IMPORTAR XML acima.</td></tr>';
        return;
    }

    notasSalvas.reverse().forEach(nota => {
        let parser = new DOMParser();
        let xmlDoc = parser.parseFromString(nota.xml_puro, "text/xml");
        
        let numNota = "---", serie = "---", dEmi = "---", fornecedor = "---", valor = "0.00";
        
        try {
            let ide = xmlDoc.getElementsByTagName("ide")[0];
            if (ide) {
                numNota = ide.getElementsByTagName("nNF")[0]?.textContent || "---";
                serie = ide.getElementsByTagName("serie")[0]?.textContent || "---";
                let d = ide.getElementsByTagName("dhEmi")[0]?.textContent;
                if (d) dEmi = d.substring(0, 10).split('-').reverse().join('/');
            }
            let emit = xmlDoc.getElementsByTagName("emit")[0];
            if (emit) fornecedor = emit.getElementsByTagName("xNome")[0]?.textContent || "---";
            let total = xmlDoc.getElementsByTagName("total")[0];
            if (total) valor = parseFloat(total.getElementsByTagName("vNF")[0]?.textContent).toFixed(2).replace('.', ',');
        } catch (e) { console.error("Erro ao ler dados do XML.", e); }

        let statusBadge = '';
        let acoes = '';

        if (nota.status === 'CONCLUIDO') {
            statusBadge = '<span class="badge bg-success">Finalizada</span>';
            acoes = `
                <a href="/entrada-carga/conferencia/${nota.chave}" class="btn btn-sm btn-secondary fw-bold shadow-sm" title="Visualizar Nota">
                    <i class="bi bi-eye"></i> Ver
                </a>
                <button class="btn btn-sm btn-danger fw-bold shadow-sm" title="Estornar Entrada" onclick="prepararCancelamento('${nota.chave}')">
                    <i class="bi bi-trash"></i> Cancelar
                </button>
            `;
        } else {
            statusBadge = '<span class="badge bg-danger">Pendente</span>';
            acoes = `
                <a href="/entrada-carga/conferencia/${nota.chave}" class="btn btn-sm text-white fw-bold shadow-sm" style="background-color: #C60C30;" title="Iniciar Conferência">
                    <i class="bi bi-list-check"></i> Conferir
                </a>
                <button class="btn btn-sm btn-outline-danger fw-bold shadow-sm" title="Excluir XML" onclick="excluirXMLMemoria('${nota.chave}')">
                    <i class="bi bi-trash"></i>
                </button>
            `;
        }

        html += `
            <tr class="linha-nota">
                <td>${statusBadge}</td>
                <td class="fw-bold text-secondary">${numNota}</td>
                <td>${serie}</td>
                <td>${dEmi}</td>
                <td class="text-start fornecedor-busca">${fornecedor}</td>
                <td class="text-end fw-bold" style="color: #101820;">R$ ${valor}</td>
                <td class="text-center d-flex justify-content-center gap-1">${acoes}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function excluirXMLMemoria(chave) {
    if (confirm("Tem certeza que deseja excluir esta nota pendente do sistema?")) {
        let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
        notasSalvas = notasSalvas.filter(n => n.chave !== chave);
        localStorage.setItem('xmls_jb_tintas', JSON.stringify(notasSalvas));
        
        localStorage.removeItem('rascunho_xml_' + chave);
        carregarNotasDaMemoria();
    }
}

function iniciarConferencia(chave) {
    window.location.href = `/entrada-carga/conferencia/${chave}/`;
}

function filtrarNotas() {
    let input = document.getElementById("inputFiltroNota").value.toUpperCase();
    let linhas = document.querySelectorAll(".linha-nota");
    linhas.forEach(linha => {
        let textoLinha = linha.innerText.toUpperCase();
        linha.style.display = textoLinha.includes(input) ? "" : "none";
    });
}

// ==========================================
// 📦 BIPADOR E CAIXA AVULSA (LEGADO)
// ==========================================
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

function removerItem(idProduto, nomeProduto) {
    if (confirm(`Tem certeza que deseja remover "${nomeProduto}" da lista de entrada?`)) {
        itensEntrada = itensEntrada.filter(i => i.id !== idProduto);
        renderLista();
    }
}

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
    document.getElementById('dataHoraAtual').innerText = new Date().toLocaleString('pt-BR');

    var myModal = new bootstrap.Modal(document.getElementById('modalConferencia'));
    myModal.show();
}

function confirmarEfetivacao() {
    let btn = document.getElementById('btnConfirmar');
    btn.disabled = true;
    btn.innerText = "⏳ Salvando...";

    fetch(`/api/efetivar-entrada/?_nocache=${Date.now()}`, {
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
            bootstrap.Modal.getInstance(document.getElementById('modalConferencia')).hide();
        } else {
            alert("Erro ao salvar: " + data.mensagem);
        }
        btn.disabled = false;
        btn.innerText = "✅ Confirmar Entrada no Estoque";
    })
    .catch(error => {
        alert("Erro ao tentar salvar no banco de dados.");
        btn.disabled = false;
        btn.innerText = "✅ Confirmar Entrada no Estoque";
    });
}

// ==========================================
// ⚠️ ESTORNO SEGURO DE ENTRADA CONCLUÍDA
// ==========================================
let modalCancelamento = null;
function prepararCancelamento(chave) {
    document.getElementById('chaveNotaCancelamento').value = chave;
    document.getElementById('motivoCancelamento').value = '';
    document.getElementById('usuarioCancelamento').value = '';
    document.getElementById('senhaCancelamento').value = '';
    
    if (!modalCancelamento) modalCancelamento = new bootstrap.Modal(document.getElementById('modalAssinaturaCancelamento'));
    modalCancelamento.show();
}

function efetivarCancelamentoSeguro() {
    let chave = document.getElementById('chaveNotaCancelamento').value;
    let motivo = document.getElementById('motivoCancelamento').value.trim();
    let usuario = document.getElementById('usuarioCancelamento').value.trim();
    let senha = document.getElementById('senhaCancelamento').value;

    if (!motivo || !usuario || !senha) {
        alert("Preencha todos os campos obrigatórios (Motivo, Usuário e Senha).");
        return;
    }

    let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
    let notaIndex = notasSalvas.findIndex(n => n.chave === chave);
    
    if (notaIndex === -1 || !notasSalvas[notaIndex].itens_processados) {
        alert("Erro: Não foi possível recuperar a lista de produtos processados nesta nota.");
        return;
    }

    let itensEstorno = notasSalvas[notaIndex].itens_processados;
    let payload = {
        motivo: motivo,
        usuario: usuario,
        senha: senha,
        itens: itensEstorno
    };

    fetch('/api/estoque/cancelar-entrada/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfTokenConfig },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'sucesso') {
            notasSalvas.splice(notaIndex, 1);
            localStorage.setItem('xmls_jb_tintas', JSON.stringify(notasSalvas));
            alert("✅ Nota cancelada e estoque estornado com sucesso!");
            modalCancelamento.hide();
            carregarNotasDaMemoria();
        } else {
            alert("❌ Erro de Segurança: " + data.mensagem);
        }
    })
    .catch(err => alert("Erro na comunicação com o servidor."));
}

let itensEntrada = [];

// ==========================================
// 📥 LEITURA E ARMAZENAMENTO DE XML (LOCALSTORAGE)
// ==========================================

// 1. Carrega as notas salvas no LocalStorage assim que a página abre
document.addEventListener("DOMContentLoaded", function() {
    // Se a tabela de notas existir na tela (na tela inicial), carrega os dados
    if (document.getElementById('listaNotas')) {
        carregarTabelaXMLs();
    }
});

// 2. Função acionada ao escolher o arquivo XML no botão "IMPORTAR XML"
function enviarXML(input) {
    if (input.files.length === 0) return;

    let arquivo = input.files[0];
    let leitor = new FileReader(); // Ferramenta nativa do navegador para ler arquivos

    // Quando terminar de ler o arquivo do computador do usuário...
    leitor.onload = function(evento) {
        let conteudoXML = evento.target.result;
        
        // Converte o texto do arquivo em um "Documento XML" navegável
        let parser = new DOMParser();
        let xmlDoc = parser.parseFromString(conteudoXML, "text/xml");

        try {
            // Navegando nas tags do XML da Nota Fiscal (NF-e)
            let infNFe = xmlDoc.getElementsByTagName("infNFe")[0];
            if (!infNFe) throw "O arquivo selecionado não é uma NF-e válida.";

            let chave = infNFe.getAttribute("Id").replace("NFe", "");
            
            let ide = xmlDoc.getElementsByTagName("ide")[0];
            let numero = ide.getElementsByTagName("nNF")[0].textContent;
            let serie = ide.getElementsByTagName("serie")[0].textContent;
            
            // Formatando a data de AAAA-MM-DD para DD/MM/AAAA
            let dataEmissaoCrua = ide.getElementsByTagName("dhEmi")[0].textContent.substring(0, 10);
            let dataEmissao = dataEmissaoCrua.split('-').reverse().join('/');

            let emit = xmlDoc.getElementsByTagName("emit")[0];
            let fornecedor = emit.getElementsByTagName("xNome")[0].textContent;

            let total = xmlDoc.getElementsByTagName("total")[0];
            let vNF = total.getElementsByTagName("vNF")[0].textContent;
            let valorTotal = parseFloat(vNF);

            // 3. Montar o pacote de dados da nota
            let nota = {
                chave: chave,
                numero: numero,
                serie: serie,
                data_emissao: dataEmissao,
                fornecedor: fornecedor,
                valor_total: valorTotal,
                xml_puro: conteudoXML, // Guardamos o XML inteiro na memória para usar na tela de conferência!
                status: 'Pendente'
            };

            // 4. Salvar no LocalStorage do navegador
            let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];

            // Bloqueio de duplicidade na memória
            if (notasSalvas.find(n => n.chave === chave)) {
                alert("❌ Esta Nota Fiscal já está na sua lista de conferência!");
            } else {
                notasSalvas.push(nota);
                localStorage.setItem('xmls_jb_tintas', JSON.stringify(notasSalvas));
                alert("✅ XML carregado com sucesso!");
                carregarTabelaXMLs(); // Atualiza a tabela na tela imediatamente
            }

        } catch (erro) {
            alert("❌ Erro ao ler o XML: " + erro);
            console.error(erro);
        }

        input.value = ""; // Limpa o input para permitir importar a mesma nota novamente se necessário (após excluir)
    };

    // Manda o leitor processar o arquivo como texto puro
    leitor.readAsText(arquivo);
}

// 5. Função que desenha as notas na tabela HTML da tela inicial
function carregarTabelaXMLs() {
    let tabela = document.getElementById('listaNotas');
    if (!tabela) return;

    let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
    let html = '';

    if (notasSalvas.length === 0) {
        tabela.innerHTML = `<tr><td colspan="7" class="py-4 text-muted">Nenhum XML aguardando conferência. Clique em IMPORTAR XML para iniciar.</td></tr>`;
        return;
    }

    notasSalvas.forEach((nota) => {
        let badgeCor = nota.status === 'Pendente' ? 'bg-danger' : (nota.status === 'Em Conferência' ? 'bg-warning text-dark' : 'bg-success');
        
        html += `
        <tr>
            <td><span class="badge ${badgeCor}">${nota.status}</span></td>
            <td class="fw-bold text-secondary">${nota.numero}</td>
            <td>${nota.serie}</td>
            <td>${nota.data_emissao}</td>
            <td class="text-start">${nota.fornecedor}</td>
            <td class="text-end fw-bold" style="color: #101820;">R$ ${nota.valor_total.toFixed(2).replace('.', ',')}</td>
            <td class="text-center">
                <button class="btn btn-sm text-white fw-bold shadow-sm" style="background-color: #C60C30;" onclick="iniciarConferencia('${nota.chave}')">
                    <i class="bi bi-list-check"></i> Conferir
                </button>
                <button class="btn btn-sm btn-outline-danger fw-bold shadow-sm ms-1" onclick="excluirXMLMemoria('${nota.chave}')" title="Remover da lista">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>`;
    });

    tabela.innerHTML = html;
}

// 6. Função para o usuário poder excluir da lista caso importe errado
function excluirXMLMemoria(chave) {
    if (confirm("Deseja remover este XML da lista de conferência?")) {
        let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
        notasSalvas = notasSalvas.filter(n => n.chave !== chave);
        localStorage.setItem('xmls_jb_tintas', JSON.stringify(notasSalvas));
        carregarTabelaXMLs();
    }
}

// 7. Ação de clicar no botão "Conferir"
function iniciarConferencia(chave) {
    // Redireciona o navegador para a tela de conferência usando a rota configurada no urls.py
    window.location.href = `/entrada-carga/conferencia/${chave}/`;
}


// ==========================================
// 📦 BIPADOR (CÓDIGO LEGADO DA ENTRADA AVULSA)
// ==========================================

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

document.addEventListener("DOMContentLoaded", function() {
    carregarNotasDaMemoria();
});

function carregarNotasDaMemoria() {
    let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
    let tbody = document.getElementById('listaNotas');
    let html = '';
    
    if (notasSalvas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-4 text-muted">Nenhuma nota importada. Utilize o botão IMPORTAR XML acima.</td></tr>';
        return;
    }

    // Inverte o array para as mais recentes aparecerem no topo
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
        } catch (e) { console.error("Erro ao ler dados do XML para a listagem.", e); }

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

function filtrarNotas() {
    let input = document.getElementById("inputFiltroNota").value.toUpperCase();
    let linhas = document.querySelectorAll(".linha-nota");
    linhas.forEach(linha => {
        let textoLinha = linha.innerText.toUpperCase();
        linha.style.display = textoLinha.includes(input) ? "" : "none";
    });
}

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
            // Remove a nota da lista ou altera o status para cancelada
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

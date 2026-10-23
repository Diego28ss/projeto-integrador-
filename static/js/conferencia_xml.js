let linhaAtivaIndex = null;
let dadosFiscaisAtivos = {};

document.addEventListener("DOMContentLoaded", function() {
    carregarDadosNota();

    // Eventos do Modal de Busca (Lupa)
    document.querySelector('#modalVincular .input-group button').addEventListener('click', buscarProdutoVinculo);
    document.getElementById('inputBuscaVinculo').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') buscarProdutoVinculo();
    });
});

function getTagText(parentNode, tagName, defaultVal = "---") {
    if (!parentNode) return defaultVal;
    let node = parentNode.getElementsByTagName(tagName)[0];
    return node ? node.textContent : defaultVal;
}

function getTagFloat(parentNode, tagName, defaultVal = 0.0) {
    let text = getTagText(parentNode, tagName, "");
    return text ? parseFloat(text) : defaultVal;
}

function formatBRL(valor) {
    return parseFloat(valor).toFixed(2).replace('.', ',');
}

function carregarDadosNota() {
    let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
    let nota = notasSalvas.find(n => n.chave === nfeChaveParam);

    if (!nota) {
        alert("Nota Fiscal não encontrada na memória do navegador!");
        window.location.href = '/entrada-carga/';
        return;
    }

    let parser = new DOMParser();
    let xmlDoc = parser.parseFromString(nota.xml_puro, "text/xml");

    // Cabeçalho
    let ide = xmlDoc.getElementsByTagName("ide")[0];
    if (ide) {
        document.getElementById('lblNumeroSerie').innerText = `${getTagText(ide, "nNF")} / ${getTagText(ide, "serie")}`;
        let rawDate = getTagText(ide, "dhEmi");
        if (rawDate !== "---") {
            document.getElementById('lblDataEmissao').innerText = rawDate.substring(0, 10).split('-').reverse().join('/');
        }
        document.getElementById('nfe_modelo').innerText = `${getTagText(ide, "mod")} - NF-e`;
        document.getElementById('nfe_natureza').innerText = getTagText(ide, "natOp");
    }

    // Fornecedor
    let emit = xmlDoc.getElementsByTagName("emit")[0];
    if (emit) {
        document.getElementById('lblFornecedor').innerText = getTagText(emit, "xNome");
        document.getElementById('lblCnpjFornecedor').innerText = getTagText(emit, "CNPJ");
        document.getElementById('lblIeFornecedor').innerText = getTagText(emit, "IE");
        let enderEmit = emit.getElementsByTagName("enderEmit")[0];
        if (enderEmit) {
            document.getElementById('lblEndFornecedor').innerText = `${getTagText(enderEmit, "xLgr")}, ${getTagText(enderEmit, "nro")} - ${getTagText(enderEmit, "xBairro")} - ${getTagText(enderEmit, "xMun")} / ${getTagText(enderEmit, "UF")} - ${getTagText(enderEmit, "CEP")}`;
            document.getElementById('lblTelFornecedor').innerText = getTagText(enderEmit, "fone");
        }
        let crt = getTagText(emit, "CRT");
        document.getElementById('nfe_regime').innerText = crt === "1" ? "1 - Simples Nacional" : (crt === "3" ? "3 - Regime Normal" : crt);
    }

    // Destinatário
    let dest = xmlDoc.getElementsByTagName("dest")[0];
    if (dest) {
        document.getElementById('lblDestinatario').innerText = getTagText(dest, "xNome");
        document.getElementById('lblCnpjDestinatario').innerText = getTagText(dest, "CNPJ", getTagText(dest, "CPF"));
        document.getElementById('lblIeDestinatario').innerText = getTagText(dest, "IE");
        let enderDest = dest.getElementsByTagName("enderDest")[0];
        if (enderDest) {
            document.getElementById('lblEndDestinatario').innerText = `${getTagText(enderDest, "xLgr")}, ${getTagText(enderDest, "nro")} - ${getTagText(enderDest, "xBairro")} - ${getTagText(enderDest, "xMun")} / ${getTagText(enderDest, "UF")} - ${getTagText(enderDest, "CEP")}`;
        }
        document.getElementById('lblEmailDestinatario').innerText = getTagText(dest, "email");
    }

    // Totais
    let total = xmlDoc.getElementsByTagName("total")[0];
    if (total) {
        let icmsTot = total.getElementsByTagName("ICMSTot")[0];
        if (icmsTot) {
            document.getElementById('lblTotProd').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vProd"))}`;
            document.getElementById('tot_bc_icms').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vBC"))}`;
            document.getElementById('tot_icms').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vICMS"))}`;
            document.getElementById('tot_bc_icms_st').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vBCST"))}`;
            document.getElementById('tot_icms_st').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vST"))}`;
            document.getElementById('tot_ipi').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vIPI"))}`;
            document.getElementById('lblTotFrete').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vFrete"))}`;
            document.getElementById('tot_seguro').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vSeg"))}`;
            document.getElementById('lblTotDesc').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vDesc"))}`;
            document.getElementById('tot_pis').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vPIS"))}`;
            document.getElementById('tot_cofins').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vCOFINS"))}`;
            document.getElementById('lblTotNF').innerText = `R$ ${formatBRL(getTagFloat(icmsTot, "vNF"))}`;
        }
    }

    // Transportes
    let transp = xmlDoc.getElementsByTagName("transp")[0];
    if (transp) {
        let modFrete = getTagText(transp, "modFrete");
        let descFrete = {"0": "0 - Remetente (CIF)", "1": "1 - Destinatário (FOB)", "2": "2 - Terceiros", "9": "9 - Sem Frete"};
        document.getElementById('transp_modFrete').innerText = descFrete[modFrete] || modFrete;
        let transporta = transp.getElementsByTagName("transporta")[0];
        if (transporta) {
            document.getElementById('transp_nome').innerText = getTagText(transporta, "xNome");
            document.getElementById('transp_cnpj').innerText = getTagText(transporta, "CNPJ", getTagText(transporta, "CPF"));
            document.getElementById('transp_ie').innerText = getTagText(transporta, "IE");
            document.getElementById('transp_end').innerText = `${getTagText(transporta, "xEnder")} - ${getTagText(transporta, "xMun")} / ${getTagText(transporta, "UF")}`;
        }
        let veicTransp = transp.getElementsByTagName("veicTransp")[0];
        if (veicTransp) {
            document.getElementById('transp_placa').innerText = getTagText(veicTransp, "placa");
            document.getElementById('transp_uf').innerText = getTagText(veicTransp, "UF");
            document.getElementById('transp_rntc').innerText = getTagText(veicTransp, "RNTC");
        }
        let vol = transp.getElementsByTagName("vol")[0];
        if (vol) {
            document.getElementById('vol_qVol').innerText = getTagText(vol, "qVol", "0");
            document.getElementById('vol_esp').innerText = getTagText(vol, "esp");
            document.getElementById('vol_marca').innerText = getTagText(vol, "marca");
            document.getElementById('vol_pesoL').innerText = getTagFloat(vol, "pesoL").toFixed(3);
            document.getElementById('vol_pesoB').innerText = getTagFloat(vol, "pesoB").toFixed(3);
        }
    }

    // Tabela de Produtos com Leitura de Rascunho
    let rascunho = JSON.parse(localStorage.getItem('rascunho_xml_' + nfeChaveParam)) || {};
    let itensHtml = '';
    let detNodes = xmlDoc.getElementsByTagName("det");
    
    for (let i = 0; i < detNodes.length; i++) {
        let det = detNodes[i];
        let nItem = det.getAttribute("nItem");
        let prod = det.getElementsByTagName("prod")[0];
        let imposto = det.getElementsByTagName("imposto")[0];

        let cProd = getTagText(prod, "cProd");
        let xProd = getTagText(prod, "xProd").replace(/'/g, "\\'").replace(/"/g, '&quot;');
        let cEAN = getTagText(prod, "cEAN", "");
        if (cEAN === "SEM GTIN") cEAN = "";
        let ncm = getTagText(prod, "NCM", "");
        let cest = getTagText(prod, "CEST", "");
        let cfopXml = getTagText(prod, "CFOP");
        let qCom = getTagText(prod, "qCom");
        let uCom = getTagText(prod, "uCom");
        let vUnCom = getTagFloat(prod, "vUnCom");
        let vProd = getTagFloat(prod, "vProd");

        let cstCsosn = "---", bcIcms = 0.0, vIcms = 0.0, pIcms = 0.0;
        let icmsNode = imposto ? imposto.getElementsByTagName("ICMS")[0] : null;
        if (icmsNode && icmsNode.children.length > 0) {
            let icmsTag = icmsNode.children[0];
            cstCsosn = getTagText(icmsTag, "CST", getTagText(icmsTag, "CSOSN", "---"));
            bcIcms = getTagFloat(icmsTag, "vBC");
            vIcms = getTagFloat(icmsTag, "vICMS");
            pIcms = getTagFloat(icmsTag, "pICMS");
        }

        let vIpi = 0.0;
        let ipiNode = imposto ? imposto.getElementsByTagName("IPI")[0] : null;
        if (ipiNode) {
            let ipiTrib = ipiNode.getElementsByTagName("IPITrib")[0];
            if (ipiTrib) vIpi = getTagFloat(ipiTrib, "vIPI");
        }

        // DADOS SALVOS NO RASCUNHO
        let rascunhoLinha = rascunho[i] || null;
        let vinculado = rascunhoLinha ? rascunhoLinha.vinculado : 'nao';
        let produtoId = rascunhoLinha ? rascunhoLinha.produtoId : '';
        let statusStr = rascunhoLinha ? rascunhoLinha.status : 'pendente';
        let codInterno = rascunhoLinha ? rascunhoLinha.codInterno : '---';
        let nomeInterno = rascunhoLinha ? rascunhoLinha.nomeInterno : 'Aguardando vínculo...';
        let fator = rascunhoLinha ? rascunhoLinha.fator : '1';
        let cfopEnt = rascunhoLinha ? rascunhoLinha.cfopEnt : '1102';

        let btnAcoesStatus = statusStr === 'concluido' ? 'disabled' : '';
        let htmlCod = vinculado === 'sim' ? `<span class="badge bg-dark">${codInterno}</span>` : `<span class="text-muted">---</span>`;
        let htmlNome = vinculado === 'sim' ? `<strong class="text-success">${nomeInterno}</strong>` : `<span class="text-muted">Aguardando vínculo...</span>`;
        
        let htmlBtnStatus = statusStr === 'concluido' 
            ? `<button type="button" id="btn_status_${i}" class="btn btn-sm text-white fw-bold w-100" style="background-color: #00C853;" onclick="abrirModalDesvincular(${i})">Concluído</button>`
            : `<button type="button" id="btn_status_${i}" class="btn btn-sm text-white fw-bold w-100" style="background-color: #C60C30;" onclick="toggleStatus(${i})">Pendente</button>`;

        itensHtml += `
        <tr id="linha_xml_${i}" data-vinculado="${vinculado}" data-produto-id="${produtoId}" data-status="${statusStr}">
            <td class="text-center fw-bold">${nItem}</td>
            <td class="text-secondary">${cProd}</td>
            <td class="text-center">
                <button type="button" id="btn_lupa_${i}" class="btn btn-sm btn-dark px-2 py-0" title="Vincular Existente" onclick="abrirModalVinculo(${i}, '${cProd}', '${ncm}', '${cest}')" ${btnAcoesStatus}><i class="bi bi-search"></i></button>
                <button type="button" id="btn_novo_${i}" class="btn btn-sm text-white px-2 py-0" style="background-color: #C60C30;" title="Cadastrar Novo" onclick="abrirModalNovoXML(${i}, '${cProd}', '${xProd}', '${cEAN}', ${vUnCom}, '${ncm}', '${cest}')" ${btnAcoesStatus}><i class="bi bi-plus-lg"></i></button>
            </td>
            <td class="text-center" id="col_cod_${i}">${htmlCod}</td>
            <td id="col_nome_${i}">${htmlNome}</td>
            <td class="text-center"><input type="number" id="input_fator_${i}" class="form-control form-control-sm text-center" value="${fator}" style="width: 60px;" ${btnAcoesStatus}></td>
            <td class="text-center fw-bold text-primary">0</td>
            <td class="text-center p-1">${htmlBtnStatus}</td>
            <td><small>${xProd}</small></td>
            <td class="text-center">${cfopXml}</td>
            <td class="text-center"><input type="text" id="input_cfop_ent_${i}" class="form-control form-control-sm text-center" value="${cfopEnt}" style="width: 70px;" ${btnAcoesStatus}></td>
            <td class="text-center fw-bold">${qCom}</td>
            <td class="text-center">${uCom}</td>
            <td class="text-end">R$ ${formatBRL(vUnCom)}</td>
            <td class="text-end fw-bold">R$ ${formatBRL(vProd)}</td>
            <td class="text-center">${cstCsosn}</td>
            <td class="text-end">R$ ${formatBRL(bcIcms)}</td>
            <td class="text-end">R$ ${formatBRL(vIcms)}</td>
            <td class="text-end">R$ ${formatBRL(vIpi)}</td>
            <td class="text-center">${pIcms}%</td>
        </tr>`;
    }
    document.getElementById('listaProdutosXML').innerHTML = itensHtml;
}

// ==========================================
// FUNÇÕES DE VÍNCULO E CADASTRO
// ==========================================
function atualizarLinhaTabela(index, codInterno, nome, produtoId) {
    let tr = document.getElementById(`linha_xml_${index}`);
    tr.setAttribute('data-produto-id', produtoId);
    tr.setAttribute('data-vinculado', 'sim');
    
    document.getElementById(`col_cod_${index}`).innerHTML = `<span class="badge bg-dark">${codInterno}</span>`;
    document.getElementById(`col_nome_${index}`).innerHTML = `<strong class="text-success">${nome}</strong>`;
    tr.style.backgroundColor = ''; 
}

function abrirModalVinculo(index, codFornecedor, ncm, cest) {
    linhaAtivaIndex = index;
    dadosFiscaisAtivos = { cod_fornecedor: codFornecedor, ncm: ncm, cest: cest };
    document.getElementById('inputBuscaVinculo').value = '';
    document.getElementById('resultadoBuscaVinculo').innerHTML = '';
    new bootstrap.Modal(document.getElementById('modalVincular')).show();
}

function buscarProdutoVinculo() {
    let q = document.getElementById('inputBuscaVinculo').value;
    if (q.length < 2) return;
    
    fetch(`/api/xml/buscar-produtos/?q=${q}`)
    .then(res => res.json())
    .then(data => {
        let html = '';
        data.produtos.forEach(p => {
            html += `
            <button class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" onclick="efetivarVinculo(${p.id}, '${p.cod_interno}', '${p.nome.replace(/'/g, "\\'")}')">
                <div>
                    <strong>${p.nome}</strong><br>
                    <small class="text-muted">Cód: ${p.cod_interno} | Estoque: ${p.estoque}</small>
                </div>
                <span class="badge bg-success">Vincular</span>
            </button>`;
        });
        document.getElementById('resultadoBuscaVinculo').innerHTML = html || '<p class="text-muted p-2">Nenhum produto encontrado.</p>';
    });
}

function efetivarVinculo(produtoId, codInterno, nomeProduto) {
    let payload = { produto_id: produtoId, ...dadosFiscaisAtivos };
    
    fetch('/api/xml/vincular-produto/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfTokenConfig },
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(data => {
        if (data.status === 'sucesso') {
            atualizarLinhaTabela(linhaAtivaIndex, data.cod_interno, data.nome, produtoId);
            bootstrap.Modal.getInstance(document.getElementById('modalVincular')).hide();
        } else {
            alert("Erro: " + data.mensagem);
        }
    });
}

function abrirModalNovoXML(index, codFornecedor, nome, ean, custo, ncm, cest) {
    const params = new URLSearchParams({
        action: 'novo_via_xml',
        nome: nome,
        ean: ean,
        custo: custo,
        ncm: ncm,
        cest: cest,
        cod_forn: codFornecedor
    });
    
    const url = `/estoque/?${params.toString()}`;
    window.open(url, '_blank');
    
    alert("Uma nova guia foi aberta com o cadastro completo do produto!\n\n1. Preencha a marca, impostos e salve.\n2. Volte para esta tela de XML.\n3. Clique na 'Lupa' deste item e vincule o produto que acabou de criar.");
}

// ==========================================
// FUNÇÕES DE STATUS, LOTE E RASCUNHO
// ==========================================
function salvarRascunho() {
    let rascunho = {};
    let linhas = document.querySelectorAll('[id^="linha_xml_"]');
    
    linhas.forEach((tr) => {
        let index = tr.id.split('_')[2];
        rascunho[index] = {
            vinculado: tr.getAttribute('data-vinculado'),
            produtoId: tr.getAttribute('data-produto-id'),
            status: tr.getAttribute('data-status'),
            codInterno: document.getElementById(`col_cod_${index}`).innerText.trim(),
            nomeInterno: document.getElementById(`col_nome_${index}`).innerText.trim(),
            fator: document.getElementById(`input_fator_${index}`).value,
            cfopEnt: document.getElementById(`input_cfop_ent_${index}`).value
        };
    });
    
    localStorage.setItem('rascunho_xml_' + nfeChaveParam, JSON.stringify(rascunho));
    alert("💾 Progresso salvo com sucesso! Você pode fechar o sistema e continuar depois.");
}

function toggleStatus(index) {
    let tr = document.getElementById(`linha_xml_${index}`);
    let vinculado = tr.getAttribute('data-vinculado');
    let fator = parseFloat(document.getElementById(`input_fator_${index}`).value) || 0;
    
    if (vinculado !== 'sim') {
        alert("⚠️ Operação negada: O produto do XML precisa estar VINCULADO a um produto do sistema.");
        return;
    }
    if (fator <= 0) {
        alert("⚠️ Operação negada: O Fator de conversão não pode ser 0 ou vazio.");
        return;
    }
    
    // Altera para Concluído e bloqueia edição
    tr.setAttribute('data-status', 'concluido');
    document.getElementById(`btn_lupa_${index}`).disabled = true;
    document.getElementById(`btn_novo_${index}`).disabled = true;
    document.getElementById(`input_fator_${index}`).disabled = true;
    document.getElementById(`input_cfop_ent_${index}`).disabled = true;
    
    let btnStatus = document.getElementById(`btn_status_${index}`);
    btnStatus.style.backgroundColor = '#00C853';
    btnStatus.innerText = 'Concluído';
    btnStatus.setAttribute('onclick', `abrirModalDesvincular(${index})`);
}

function abrirModalDesvincular(index) {
    linhaAtivaIndex = index;
    new bootstrap.Modal(document.getElementById('modalDesvincular')).show();
}

function confirmarDesvinculo() {
    let index = linhaAtivaIndex;
    let tr = document.getElementById(`linha_xml_${index}`);
    
    // Retorna para Pendente e limpa o vínculo
    tr.setAttribute('data-status', 'pendente');
    tr.setAttribute('data-vinculado', 'nao');
    tr.setAttribute('data-produto-id', '');
    
    document.getElementById(`col_cod_${index}`).innerHTML = `<span class="text-muted">---</span>`;
    document.getElementById(`col_nome_${index}`).innerHTML = `<span class="text-muted">Aguardando vínculo...</span>`;
    
    document.getElementById(`btn_lupa_${index}`).disabled = false;
    document.getElementById(`btn_novo_${index}`).disabled = false;
    document.getElementById(`input_fator_${index}`).disabled = false;
    document.getElementById(`input_cfop_ent_${index}`).disabled = false;
    
    let btnStatus = document.getElementById(`btn_status_${index}`);
    btnStatus.style.backgroundColor = '#C60C30';
    btnStatus.innerText = 'Pendente';
    btnStatus.setAttribute('onclick', `toggleStatus(${index})`);
    
    bootstrap.Modal.getInstance(document.getElementById('modalDesvincular')).hide();
}

function abrirModalCfopLote() {
    new bootstrap.Modal(document.getElementById('modalCfopLote')).show();
}

function aplicarCfopLote() {
    let novoCfop = document.getElementById('inputCfopLote').value.trim();
    if (!novoCfop) return;
    
    let linhas = document.querySelectorAll('[id^="linha_xml_"]');
    linhas.forEach((tr) => {
        let index = tr.id.split('_')[2];
        if (tr.getAttribute('data-status') !== 'concluido') {
            document.getElementById(`input_cfop_ent_${index}`).value = novoCfop;
        }
    });
    bootstrap.Modal.getInstance(document.getElementById('modalCfopLote')).hide();
}

function liberarDivergenciasLote() {
    let linhas = document.querySelectorAll('[id^="linha_xml_"]');
    let falhas = 0;
    
    linhas.forEach((tr) => {
        let index = tr.id.split('_')[2];
        if (tr.getAttribute('data-status') !== 'concluido') {
            let vinculado = tr.getAttribute('data-vinculado');
            let fator = parseFloat(document.getElementById(`input_fator_${index}`).value) || 0;
            
            if (vinculado === 'sim' && fator > 0) {
                toggleStatus(index);
            } else {
                falhas++;
            }
        }
    });
    
    if (falhas > 0) {
        alert(`⚠️ Atenção: ${falhas} produto(s) continuam pendentes. Verifique vínculos e fator de conversão.`);
    } else {
        alert("✅ Todos os produtos foram verificados e definidos como Concluídos!");
    }
}

function finalizarEntrada() {
    let itensParaEntrada = [];
    let linhas = document.querySelectorAll('[id^="linha_xml_"]');
    let todasConcluidas = true;

    linhas.forEach((tr) => {
        if (tr.getAttribute('data-status') !== 'concluido') {
            todasConcluidas = false;
            tr.style.backgroundColor = '#ffe6e6';
        } else {
            let index = tr.id.split('_')[2];
            let id = tr.getAttribute('data-produto-id');
            let fator = parseFloat(document.getElementById(`input_fator_${index}`).value) || 1;
            let qtdXml = parseFloat(tr.cells[11].innerText);
            let qtdFinal = qtdXml * fator; 
            itensParaEntrada.push({ id: id, qtd: qtdFinal });
        }
    });

    if (!todasConcluidas) {
        alert("⚠️ Operação bloqueada! Existem linhas com status 'Pendente'.");
        return;
    }

    if (confirm(`Atenção: Você está prestes a somar fisicamente o estoque de ${itensParaEntrada.length} produtos.\nConfirma a operação?`)) {
        fetch('/api/efetivar-entrada/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfTokenConfig },
            body: JSON.stringify({ itens: itensParaEntrada })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'sucesso') {
                // ATUALIZA O STATUS DA NOTA NO NAVEGADOR E GUARDA OS ITENS PARA POSSÍVEL ESTORNO
                let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
                let notaIndex = notasSalvas.findIndex(n => n.chave === nfeChaveParam);
                if (notaIndex !== -1) {
                    notasSalvas[notaIndex].status = 'CONCLUIDO';
                    notasSalvas[notaIndex].itens_processados = itensParaEntrada;
                    localStorage.setItem('xmls_jb_tintas', JSON.stringify(notasSalvas));
                }
                
                localStorage.removeItem('rascunho_xml_' + nfeChaveParam);
                alert("✅ Sucesso! O estoque da loja foi abastecido com as quantidades faturadas.");
                
                // REDIRECIONAMENTO CORRIGIDO PARA A TELA DE ENTRADA
                window.location.href = '/entrada-carga/';
            } else {
                alert("Erro ao finalizar a entrada: " + data.mensagem);
            }
        });
    }
}


document.addEventListener("DOMContentLoaded", function() {
    carregarDadosNota();
});

// Funções utilitárias seguras para leitura do XML
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

    // ==========================================
    // 1. CABEÇALHO DA NF-e
    // ==========================================
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

    // ==========================================
    // 2. FORNECEDOR E DESTINATÁRIO
    // ==========================================
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
        let crtLabel = crt === "1" ? "1 - Simples Nacional" : (crt === "3" ? "3 - Regime Normal" : crt);
        document.getElementById('nfe_regime').innerText = crtLabel;
    }

    let dest = xmlDoc.getElementsByTagName("dest")[0];
    if (dest) {
        document.getElementById('lblDestinatario').innerText = getTagText(dest, "xNome");
        let cnpjCpf = getTagText(dest, "CNPJ", getTagText(dest, "CPF"));
        document.getElementById('lblCnpjDestinatario').innerText = cnpjCpf;
        document.getElementById('lblIeDestinatario').innerText = getTagText(dest, "IE");
        
        let enderDest = dest.getElementsByTagName("enderDest")[0];
        if (enderDest) {
            document.getElementById('lblEndDestinatario').innerText = `${getTagText(enderDest, "xLgr")}, ${getTagText(enderDest, "nro")} - ${getTagText(enderDest, "xBairro")} - ${getTagText(enderDest, "xMun")} / ${getTagText(enderDest, "UF")} - ${getTagText(enderDest, "CEP")}`;
        }
        document.getElementById('lblEmailDestinatario').innerText = getTagText(dest, "email");
    }

    // ==========================================
    // 3. TOTAIS E IMPOSTOS
    // ==========================================
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

    // ==========================================
    // 4. TRANSPORTE E VOLUMES
    // ==========================================
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

    // ==========================================
    // 5. LISTAGEM DE PRODUTOS DA NOTA
    // ==========================================
    let itensHtml = '';
    let detNodes = xmlDoc.getElementsByTagName("det");
    
    for (let i = 0; i < detNodes.length; i++) {
        let det = detNodes[i];
        let nItem = det.getAttribute("nItem");
        let prod = det.getElementsByTagName("prod")[0];
        let imposto = det.getElementsByTagName("imposto")[0];

        let cProd = getTagText(prod, "cProd");
        let xProd = getTagText(prod, "xProd");
        let cfop = getTagText(prod, "CFOP");
        let qCom = getTagText(prod, "qCom");
        let uCom = getTagText(prod, "uCom");
        let vUnCom = getTagFloat(prod, "vUnCom");
        let vProd = getTagFloat(prod, "vProd");

        // Captura de CST ou CSOSN, Base de Cálculo, Valor ICMS e Percentual ICMS
        let cstCsosn = "---", bcIcms = 0.0, vIcms = 0.0, pIcms = 0.0;
        let icmsNode = imposto ? imposto.getElementsByTagName("ICMS")[0] : null;
        if (icmsNode && icmsNode.children.length > 0) {
            let icmsTag = icmsNode.children[0]; // Pega a primeira tag filha (ex: ICMS00, ICMSSN102)
            cstCsosn = getTagText(icmsTag, "CST", getTagText(icmsTag, "CSOSN", "---"));
            bcIcms = getTagFloat(icmsTag, "vBC");
            vIcms = getTagFloat(icmsTag, "vICMS");
            pIcms = getTagFloat(icmsTag, "pICMS");
        }

        // Captura do IPI
        let vIpi = 0.0;
        let ipiNode = imposto ? imposto.getElementsByTagName("IPI")[0] : null;
        if (ipiNode) {
            let ipiTrib = ipiNode.getElementsByTagName("IPITrib")[0];
            if (ipiTrib) vIpi = getTagFloat(ipiTrib, "vIPI");
        }

        itensHtml += `
        <tr>
            <td class="text-center fw-bold">${nItem}</td>
            <td class="text-secondary">${cProd}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-dark px-2 py-0" title="Vincular Produto Existente"><i class="bi bi-search"></i></button>
                <button class="btn btn-sm text-white px-2 py-0" style="background-color: #C60C30;" title="Cadastrar Novo Produto"><i class="bi bi-plus-lg"></i></button>
            </td>
            <td class="text-muted">---</td>
            <td class="text-muted">Aguardando vínculo...</td>
            <td class="text-center"><input type="number" class="form-control form-control-sm text-center" value="1" style="width: 60px;"></td>
            <td class="text-center fw-bold text-primary">0</td>
            <td class="text-center"><span class="badge bg-danger">Pendente</span></td>
            <td>${xProd}</td>
            <td class="text-center">${cfop}</td>
            <td class="text-center"><input type="text" class="form-control form-control-sm text-center" value="1102" style="width: 70px;"></td>
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

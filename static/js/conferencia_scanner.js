let itensScanner = [];

document.addEventListener("DOMContentLoaded", function() {
    carregarItensXML();

    // Evento da Barra de Bipagem (Scanner)
    let inputScanner = document.getElementById('inputScannerXml');
    inputScanner.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            processarBipe(this.value.trim());
        }
    });

    // Botão Salvar e Voltar
    document.querySelector('button.btn-success, button[style*="background-color: #00C853;"]').addEventListener('click', salvarEVoltar);
});

// ==========================================
// 1. CARREGAR DADOS DO XML
// ==========================================
function carregarItensXML() {
    let progressoSalvo = JSON.parse(localStorage.getItem('scanner_nfe_' + nfeChaveParam));
    
    if (progressoSalvo) {
        itensScanner = progressoSalvo;
    } else {
        let notasSalvas = JSON.parse(localStorage.getItem('xmls_jb_tintas')) || [];
        let notaAtual = notasSalvas.find(n => n.chave === nfeChaveParam);
        
        if (!notaAtual) {
            alert("Erro: XML não encontrado na memória do navegador.");
            return;
        }

        let parser = new DOMParser();
        let xmlDoc = parser.parseFromString(notaAtual.xml_puro, "text/xml");
        let detNodes = xmlDoc.getElementsByTagName("det");
        
        for (let i = 0; i < detNodes.length; i++) {
            let prod = detNodes[i].getElementsByTagName("prod")[0];
            let cEAN = prod.getElementsByTagName("cEAN")[0]?.textContent || "SEM_EAN";
            
            // Pula produtos sem código de barras válido no XML (ex: "SEM GTIN")
            if (cEAN.toUpperCase() === "SEM GTIN" || cEAN === "") cEAN = "SEM_EAN";

            itensScanner.push({
                indice: i,
                descricao: prod.getElementsByTagName("xProd")[0]?.textContent || "Produto sem nome",
                ean: cEAN,
                qtd_nota: parseFloat(prod.getElementsByTagName("qCom")[0]?.textContent || 0),
                qtd_bipada: 0
            });
        }
    }
    renderizarTabela();
}

// ==========================================
// 2. LÓGICA DO SCANNER (BIPADOR)
// ==========================================
function processarBipe(codigoLido) {
    let inputScanner = document.getElementById('inputScannerXml');
    inputScanner.value = ''; // Limpa instantaneamente para o próximo bipe

    if (!codigoLido || codigoLido === "SEM_EAN") return;

    // Procura se o código bipado existe no XML atual
    let itemEncontrado = itensScanner.find(item => item.ean === codigoLido);

    if (itemEncontrado) {
        itemEncontrado.qtd_bipada++;
        salvarProgresso();
        renderizarTabela();
    } else {
        // Bloqueia e avisa se o produto não for desta nota
        alert(`⚠️ ERRO: O código de barras ${codigoLido} NÃO PERTENCE a esta Nota Fiscal.`);
    }
    inputScanner.focus();
}

// ==========================================
// 3. AÇÕES MANUAIS (+ E -)
// ==========================================
function alterarQtd(indice, operacao) {
    let item = itensScanner[indice];
    if (operacao === '+') {
        item.qtd_bipada++;
    } else if (operacao === '-') {
        if (item.qtd_bipada > 0) item.qtd_bipada--;
    }
    salvarProgresso();
    renderizarTabela();
    document.getElementById('inputScannerXml').focus();
}

// ==========================================
// 4. RENDERIZAÇÃO DA TABELA E CÁLCULO
// ==========================================
function renderizarTabela() {
    let tbody = document.getElementById('tabelaScannerItens');
    let html = '';

    itensScanner.forEach((item, index) => {
        // Cálculo de Falta/Sobra (Qtd Nota - Qtd Bipada)
        let diferenca = item.qtd_nota - item.qtd_bipada;
        let badgeStatus = '';

        if (diferenca > 0) {
            badgeStatus = `<span class="badge bg-danger fs-6 text-white">Falta: ${diferenca}</span>`;
        } else if (diferenca < 0) {
            badgeStatus = `<span class="badge bg-warning text-dark fs-6">Sobra: ${Math.abs(diferenca)}</span>`;
        } else {
            badgeStatus = `<span class="badge bg-success fs-6 text-white"><i class="bi bi-check-circle"></i> OK</span>`;
        }

        html += `
            <tr style="${diferenca === 0 ? 'background-color: #f0fff4;' : ''}">
                <td class="text-start fw-bold text-secondary">${item.descricao}</td>
                <td><span class="badge bg-secondary fs-6">${item.ean}</span></td>
                <td class="fw-bold fs-5">${item.qtd_nota}</td>
                <td class="fw-bold fs-5 ${diferenca === 0 ? 'text-success' : 'text-primary'}">${item.qtd_bipada}</td>
                <td>${badgeStatus}</td>
                <td>
                    <div class="btn-group shadow-sm" role="group">
                        <button type="button" class="btn btn-outline-danger fw-bold px-3" onclick="alterarQtd(${index}, '-')"><i class="bi bi-dash-lg"></i></button>
                        <button type="button" class="btn btn-outline-success fw-bold px-3" onclick="alterarQtd(${index}, '+')"><i class="bi bi-plus-lg"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// ==========================================
// 5. SALVAR E INTEGRAR
// ==========================================
function salvarProgresso() {
    localStorage.setItem('scanner_nfe_' + nfeChaveParam, JSON.stringify(itensScanner));
}

function salvarEVoltar() {
    // Retorna para a tela de conferência principal
    window.location.href = `/entrada-carga/conferencia/${nfeChaveParam}/`;
}

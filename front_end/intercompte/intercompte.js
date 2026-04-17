let interChart = null;
let currentPOV = 'debiteur'; // 'debiteur' ou 'destinataire'
let accountsCache = [];      // Stocke les infos des comptes (nom, devise, etc.)

document.addEventListener('DOMContentLoaded', () => {
    initIntercompte();

    // Gestion du Toggle POV
    const toggleBtn = document.getElementById('btnTogglePOV');
    toggleBtn.onclick = function() {
        currentPOV = (currentPOV === 'debiteur') ? 'destinataire' : 'debiteur';
        this.textContent = currentPOV.charAt(0).toUpperCase() + currentPOV.slice(1);
        this.classList.toggle('active');
        refreshInterChart();
    };

    // Bouton d'exécution
    document.getElementById('btnExecuteTransfer').onclick = submitTransfer;

    // Surveillance des changements de comptes pour l'affichage des devises
    document.getElementById('selectDebiteur').onchange = checkCurrencies;
    document.getElementById('selectDestinataire').onchange = checkCurrencies;
});

/**
 * Initialise les menus déroulants avec les comptes disponibles
 */
async function initIntercompte() {
    const res = await fetch('/api/dashboard/accounts');
    accountsCache = await res.json();
    
    const s1 = document.getElementById('selectDebiteur');
    const s2 = document.getElementById('selectDestinataire');
    
    accountsCache.forEach((acc, index) => {
        const opt = `<option value="${index}">${acc.name} (${acc.devise})</option>`;
        s1.innerHTML += opt;
        s2.innerHTML += opt;
    });

    document.getElementById('transferDate').valueAsDate = new Date();
}

/**
 * Vérifie si les deux comptes ont la même devise
 * Affiche ou cache le deuxième champ de montant en conséquence
 */
function checkCurrencies() {
    const idxSrc = document.getElementById('selectDebiteur').value;
    const idxDst = document.getElementById('selectDestinataire').value;

    if (idxSrc === "" || idxDst === "") return;

    const devSrc = accountsCache[idxSrc].devise;
    const devDst = accountsCache[idxDst].devise;

    const wrapperIn = document.getElementById('wrapperAmountIn'); // Ton div contenant le 2eme input
    const labelOut = document.getElementById('labelAmountOut');
    const labelIn = document.getElementById('labelAmountIn');

    if (devSrc !== devDst) {
        // Cas multi-devises
        if(wrapperIn) wrapperIn.style.display = "flex";
        labelOut.textContent = `Montant Sortie (${devSrc})`;
        if(labelIn) labelIn.textContent = `Montant Réception (${devDst})`;
    } else {
        // Même devise
        if(wrapperIn) wrapperIn.style.display = "none";
        labelOut.textContent = `Montant (${devSrc})`;
    }
    
    refreshInterChart();
}

/**
 * Envoie le virement à l'API
 */
async function submitTransfer() {
    const idxSrc = document.getElementById('selectDebiteur').value;
    const idxDst = document.getElementById('selectDestinataire').value;
    const amountOut = parseFloat(document.getElementById('transferAmountOut').value);
    let amountIn = document.getElementById('transferAmountIn') ? parseFloat(document.getElementById('transferAmountIn').value) : amountOut;

    // Si même devise, on s'assure que In = Out
    if (accountsCache[idxSrc].devise === accountsCache[idxDst].devise) {
        amountIn = amountOut;
    }

    if (isNaN(amountOut) || (document.getElementById('wrapperAmountIn')?.style.display !== 'none' && isNaN(amountIn))) {
        alert("Veuillez saisir des montants valides.");
        return;
    }

    const payload = {
            from_idx: idxSrc,
            to_idx: idxDst,
            label: document.getElementById('transferLabel').value,
            amount_out: amountOut,
            amount_in: amountIn,
            // C'est cette ligne qui compte :
            date: document.getElementById('transferDate').value 
        };

    const res = await fetch('/api/intercompte/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Virement inter-compte enregistré avec succès.");
        refreshInterChart();
    } else {
        const err = await res.json();
        alert("Erreur : " + err.message);
    }
}

/**
 * Met à jour le graphique cumulatif
 */async function refreshInterChart() {
    const s1 = document.getElementById('selectDebiteur').value;
    const s2 = document.getElementById('selectDestinataire').value;
    if (s1 === "" || s2 === "") return;

    const res = await fetch(`/api/intercompte/chart-data?src=${s1}&dst=${s2}`);
    const data = await res.json();

    const ctx = document.getElementById('interAccountChart').getContext('2d');
    if (interChart) interChart.destroy();

    // POV logic
    const chartValues = (currentPOV === 'debiteur') ? data.cumul : data.cumul.map(v => -v);

    interChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates, // Ce sont nos strings YYYY-MM-DD
            datasets: [{
                label: `Balance (Vue ${currentPOV})`,
                data: chartValues,
                borderColor: currentPOV === 'debiteur' ? '#ef4444' : '#10b981',
                backgroundColor: currentPOV === 'debiteur' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                fill: true,
                stepped: true, // L'effet escalier
                pointRadius: 4,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    // Si le graphique ne s'affiche pas, assure-toi que 
                    // type: 'category' est utilisé si tu n'as pas de plugin Moment/Luxon
                    type: 'category', 
                    grid: { display: false },
                    ticks: { 
                        color: '#7a8299',
                        maxRotation: 45
                    }
                },
                y: {
                    grid: { color: '#1f2433' },
                    ticks: { color: '#7a8299' }
                }
            }
        }
    });
}
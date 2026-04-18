const API_PRED = '/api/prediction';
let predictionChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initAccountList();
});

async function initAccountList() {
    // Utilisation de la route dashboard qui fonctionne d'après tes logs précédents
    const res = await fetch('/api/dashboard/accounts'); 
    if (!res.ok) return;
    
    const accounts = await res.json();
    const selector = document.getElementById('accountSelector');
    
    accounts.forEach((acc, i) => {
        const opt = document.createElement('option');
        opt.value = i; 
        opt.textContent = acc.name || acc.account_name;
        selector.appendChild(opt);
    });
}

function updateProbLabel(val) {
    document.getElementById('probVal').textContent = val;
}

async function loadPredictions() {
    const idx = document.getElementById('accountSelector').value;
    const prob = document.getElementById('probRange').value;
    if (!idx) return;

    try {
        const res = await fetch(`${API_PRED}/${idx}/full?probabilite=${prob}`);
        const result = await res.json();
        
        if (result.status === "success") {
            const data = result.data;
            document.getElementById('soldeInfo').textContent = `Solde actuel : ${data.solde_actuel.toFixed(2)}€`;
            
            renderTables(data.predictions);
            // CORRECTION : On passe les données de stress et le solde
            renderChart(data.stress_test, data.solde_actuel);
        }
    } catch (e) {
        console.error("Erreur chargement:", e);
    }
}

function renderTables(predictions) {
    const tbodyRev = document.getElementById('revenuTableBody');
    const tbodyDep = document.getElementById('depenseTableBody');
    tbodyRev.innerHTML = '';
    tbodyDep.innerHTML = '';

    predictions.forEach(p => {
        const row = `<tr>
            <td>${p.Categorie}</td>
            <td>${p.Date_Prevue}</td>
            <td class="num">${p.Montant_Moyen.toFixed(2)}€</td>
            <td><span class="fiabilite-tag">${p.Fiabilite}</span></td>
        </tr>`;
        if (p.Type === 'Revenu') tbodyRev.innerHTML += row;
        else tbodyDep.innerHTML += row;
    });
}

function renderChart(stressData, soldeDepart) {
    const canvas = document.getElementById('predictionChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (predictionChart) predictionChart.destroy();

    // Extraction des labels et valeurs
    const labels = ["Aujourd'hui", ...stressData.map(d => d.Date_Prevue)];
    const values = [soldeDepart, ...stressData.map(d => d.Solde_Cumule)];

    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Scénario de Stress (Pire Cas)',
                data: values,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                fill: true,
                stepped: true, // IMPORTANT : pour voir les paliers de dépenses
                tension: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { 
                    grid: { color: '#1f2433' }, 
                    ticks: { color: '#7a8299', callback: v => v + '€' } 
                },
                x: { grid: { display: false }, ticks: { color: '#7a8299' } }
            },
            plugins: {
                legend: { labels: { color: '#e8eaf0', font: { family: 'IBM Plex Mono' } } }
            }
        }
    });
}
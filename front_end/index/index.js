const API_URL = '/api/dashboard';
let selectedIndex = null;
let isCreating = false;
let globalChart = null;

document.addEventListener('DOMContentLoaded', () => {
    refreshDashboard();

    // Liaison des boutons de la toolbar
    document.getElementById('btnCreate').onclick = () => uiCreateRow();
    document.getElementById('btnDelete').onclick = () => deleteAccount();
});

/**
 * Rafraîchit l'intégralité du dashboard (Stats, Tableau, Graphique)
 */
async function refreshDashboard() {
    
    try {
        const period = document.getElementById('periodSelector').value; // Récupère la valeur

        const [statsRes, accountsRes, evolutionRes] = await Promise.all([
            fetch(`${API_URL}/stats`),
            fetch(`${API_URL}/accounts`),
            fetch(`${API_URL}/evolution?period=${period}`)

        ]);

        const stats = await statsRes.json();
        const accounts = await accountsRes.json();
        const evolutionData = await evolutionRes.json();

        updateHeaderStats(stats);
        renderTable(accounts);
        renderGlobalChart(evolutionData);
    } catch (error) {
        console.error("Erreur lors de la mise à jour du dashboard:", error);
    }
}

/**
 * Met à jour les compteurs en haut de page
 */
function updateHeaderStats(stats) {
    document.getElementById('kpiRevenu').textContent = fmt(stats.Revenu) + ' €';
    document.getElementById('kpiDepense').textContent = fmt(stats.Depense) + ' €';
    const soldeEl = document.getElementById('kpiSolde');
    soldeEl.textContent = fmt(stats.Ecart) + ' €';
    soldeEl.className = 'kpi-value ' + (stats.Ecart >= 0 ? 'positive' : 'negative');
}

/**
 * Génère le tableau des comptes avec support du double-clic
 */
function renderTable(accounts) {
    const tbody = document.getElementById('accountTableBody');
    tbody.innerHTML = '';
    isCreating = false;

    if (accounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-msg">Aucun compte trouvé</td></tr>';
        return;
    }

    accounts.forEach((acc, index) => {
        const row = document.createElement('tr');
        row.dataset.index = index;
        if (selectedIndex === index) row.classList.add('selected');

        row.innerHTML = `
            <td class="editable col-name" ondblclick="makeEditable(this, ${index}, 'name')">${acc.name}</td>
            <td class="editable col-devise" ondblclick="makeEditable(this, ${index}, 'devise')">${acc.devise}</td>
            <td class="num positive">${fmt(acc.Revenu)}</td>
            <td class="num negative">${fmt(acc.Depense)}</td>
            <td class="num bold">${fmt(acc.Ecart)}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span class="badge-state ${acc.status ? 'active' : 'inactive'}">
                        <span class="badge-dot"></span>
                        ${acc.status ? 'Actif' : 'Inactif'}
                    </span>
                    <button onclick="event.stopPropagation(); toggleStatus(${index})" class="btn-status-toggle" title="Changer l'état">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                    </button>
                </div>
            </td>
        `;
        row.onclick = () => setSelected(index);
        tbody.appendChild(row);
    });
}

/**
 * Transforme une cellule en champ texte pour modification
 */
function makeEditable(td, index, field) {
    if (td.querySelector('input')) return; 

    const originalValue = td.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = originalValue;
    input.className = 'inline-input';
    
    td.textContent = '';
    td.appendChild(input);
    input.focus();

    const save = async () => {
        const newValue = input.value.trim();
        if (newValue !== originalValue && newValue !== "") {
            const row = td.parentElement;
            // Récupère les valeurs pour envoyer l'objet complet à l'API
            const name = field === 'name' ? newValue : row.querySelector('.col-name').textContent;
            const devise = field === 'devise' ? newValue : row.querySelector('.col-devise').textContent;

            const res = await fetch(`${API_URL}/account/${index}/modify`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, devise })
            });
            
            if (res.ok) refreshDashboard();
        } else {
            td.textContent = originalValue;
        }
    };

    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') save();
        if (e.key === 'Escape') td.textContent = originalValue;
    });
    input.addEventListener('blur', save);
}

/**
 * Gère le graphique d'évolution globale
 */

function renderGlobalChart(apiResponse) {
    const ctx = document.getElementById('globalEvolutionChart').getContext('2d');
    if (globalChart) globalChart.destroy();

    // Note : apiResponse contient maintenant { labels: [...], datasets: [...] }
    const labels = apiResponse.labels;
    const datasets = apiResponse.datasets.map((ds, index) => {
        const colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
        const color = colors[index % colors.length];
        
        return {
            label: ds.account,
            data: ds.values,
            borderColor: color,
            backgroundColor: color,
            showLine: false, // Tes points
            pointRadius: 4,
            borderWidth: 1
        };
    });

    globalChart = new Chart(ctx, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#7a8299', maxRotation: 45 }
                },
                y: {
                    grid: { color: '#1f2433' },
                    ticks: { color: '#7a8299' }
                }
            }
        }
    });
}

/**
 * Fonctions de création et suppression
 */
function uiCreateRow() {
    if (isCreating) return;
    isCreating = true;
    const tbody = document.getElementById('accountTableBody');
    const tr = document.createElement('tr');
    tr.className = 'creation-row';
    tr.innerHTML = `
        <td><input type="text" id="newName" placeholder="Nom..." autofocus></td>
        <td><input type="text" id="newDevise" value="EUR" style="width: 60px;"></td>
        <td colspan="3" class="creating-hint">Entrée pour valider →</td>
        <td><button onclick="submitNewAccount()" class="btn-submit-row">OK</button></td>
    `;
    tbody.prepend(tr);
    document.getElementById('newName').addEventListener('keydown', e => {
        if (e.key === 'Enter') submitNewAccount();
        if (e.key === 'Escape') refreshDashboard();
    });
}

async function submitNewAccount() {
    const name = document.getElementById('newName').value.trim();
    const devise = document.getElementById('newDevise').value.trim();
    if (!name) return alert("Nom obligatoire");

    const res = await fetch(`${API_URL}/account/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, devise })
    });
    if (res.ok) refreshDashboard();
}

async function toggleStatus(index) {
    const res = await fetch(`${API_URL}/account/${index}/toggle-status`, { method: 'POST' });
    if (res.ok) refreshDashboard();
}

async function deleteAccount() {
    if (selectedIndex === null) return alert("Sélectionnez un compte");
    if (!confirm("Supprimer ce compte ?")) return;

    const res = await fetch(`${API_URL}/account/${selectedIndex}/delete`, { method: 'DELETE' });
    if (res.ok) {
        selectedIndex = null;
        refreshDashboard();
    }
}

function setSelected(index) {
    selectedIndex = index;
    document.querySelectorAll('#accountTableBody tr').forEach(tr => {
        tr.classList.toggle('selected', parseInt(tr.dataset.index) === index);
    });
}

function fmt(n) {
    return Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2 });
}
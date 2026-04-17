let chartRev = null;
let chartDep = null;

document.addEventListener('DOMContentLoaded', () => {
    // Initialisation des dates : Du 1er du mois à aujourd'hui
    // Initialisation des dates : Du 1er février 2025 à aujourd'hui
    const now = new Date();
    const firstDay = "2025-02-01"; // Date fixe au format YYYY-MM-DD
    const today = now.toISOString().split('T')[0];
    
    document.getElementById('statsDateStart').value = firstDay;
    document.getElementById('statsDateEnd').value = today;

    initAccountSelect();
});

async function initAccountSelect() {
    const res = await fetch('/api/dashboard/accounts');
    const accounts = await res.json();
    const select = document.getElementById('selectAccountStats');
    
    accounts.forEach((acc, index) => {
        const opt = document.createElement('option');
        opt.value = index;
        opt.textContent = acc.name;
        select.appendChild(opt);
    });
    
    if (accounts.length > 0) loadStats();
}

async function loadStats() {
    const accIdx = document.getElementById('selectAccountStats').value;
    const start = document.getElementById('statsDateStart').value;
    const end = document.getElementById('statsDateEnd').value;
    
    const url = `/api/stats/repartition?account=${accIdx}&start=${start}&end=${end}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        
        // Mise à jour des labels totaux
        document.getElementById('totalRevLabel').textContent = `${data.total_revenu.toLocaleString()} €`;
        document.getElementById('totalDepLabel').textContent = `${data.total_depense.toLocaleString()} €`;
        
        updateCharts(data);
        updateTable(data);
    } catch (e) {
        console.error("Erreur de chargement:", e);
    }
}

function updateCharts(data) {
    const chartConfig = (id, labels, values, total, colorScheme) => {
        const ctx = document.getElementById(id).getContext('2d');
        const colors = colorScheme === 'green' ? 
            ['#10b981', '#059669', '#34d399', '#6ee7b7'] : 
            ['#ef4444', '#dc2626', '#f87171', '#fca5a5'];

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: '#1f2433',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#7a8299' } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const val = ctx.raw;
                                const pc = ((val / total) * 100).toFixed(1);
                                return ` ${val.toLocaleString()} € (${pc}%)`;
                            }
                        }
                    }
                }
            }
        });
    };

    if (chartRev) chartRev.destroy();
    chartRev = chartConfig('chartRevenus', Object.keys(data.revenus), Object.values(data.revenus), data.total_revenu, 'green');

    if (chartDep) chartDep.destroy();
    chartDep = chartConfig('chartDepenses', Object.keys(data.depenses), Object.values(data.depenses), data.total_depense, 'red');
}

function updateTable(data) {
    const tbody = document.getElementById('statsTableBody');
    tbody.innerHTML = '';

    const addRows = (obj, total, colorClass) => {
        Object.entries(obj).sort((a,b) => b[1] - a[1]).forEach(([cat, val]) => {
            const pc = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
            tbody.innerHTML += `
                <tr>
                    <td>${cat}</td>
                    <td class="${colorClass}">${colorClass === 'text-success' ? 'Revenu' : 'Dépense'}</td>
                    <td>${val.toLocaleString()} €</td>
                    <td>
                        <div class="percent-bar"><div class="percent-fill" style="width:${pc}%; background:${colorClass === 'text-success' ? '#10b981':'#ef4444'}"></div></div>
                        <span style="font-size:11px; color:#7a8299">${pc}%</span>
                    </td>
                </tr>
            `;
        });
    };

    addRows(data.revenus, data.total_revenu, 'text-success');
    addRows(data.depenses, data.total_depense, 'text-danger');
}
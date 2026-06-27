/* ── State ──────────────────────────────────────────── */
let srcId     = null;
let destId    = null;
let srcDevise = null;
let destDevise = null;
let chart     = null;

/* ── Init ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    srcId  = parseInt(params.get('src'))  || null;
    destId = parseInt(params.get('dest')) || null;

    document.getElementById('ic-date').value = new Date().toISOString().slice(0, 10);

    document.getElementById('ic-back').addEventListener('click', () => {
        window.location.href = srcId ? `/compte?id=${srcId}` : '/';
    });

    document.getElementById('ic-submit').addEventListener('click', submitVirement);

    // Quand dest change dans le select → recharger graphique + historique
    document.getElementById('ic-dest-select').addEventListener('change', onDestChange);

    // Attendre que menu_compte.js ait chargé les comptes
    const wait = setInterval(() => {
        if (window.accounts && window.accounts.length > 0) {
            clearInterval(wait);
            initPage();
        }
    }, 50);
});

/* ── Init page ──────────────────────────────────────── */
function initPage() {
    const src = window.accounts.find(c => c.id === srcId);
    if (!src) return;

    srcDevise = src.devise;
    document.getElementById('ic-src-name').textContent  = src.name;
    document.getElementById('ic-form-src').textContent  = src.name;
    document.getElementById('ic-devise-src').textContent = src.devise;

    // Remplir le select avec tous les comptes sauf source
    const sel = document.getElementById('ic-dest-select');
    sel.innerHTML = '<option value="">Choisir un compte…</option>';
    window.accounts.forEach(c => {
        if (c.id !== srcId) {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.dataset.devise = c.devise;
            opt.dataset.name   = c.name;
            opt.textContent    = `${c.name} (${c.devise})`;
            if (c.id === destId) opt.selected = true;
            sel.appendChild(opt);
        }
    });

    // Si destId pré-sélectionné depuis URL
    if (destId) {
        const dest = window.accounts.find(c => c.id === destId);
        if (dest) {
            destDevise = dest.devise;
            document.getElementById('ic-dest-name').textContent = dest.name;
            updateDeviseRow();
            loadChartAndHistory();
        }
    }

    // Highlight sidebar
    if (srcId) {
        const item = document.querySelector(`.account-item[data-id="${srcId}"]`);
        if (item) {
            document.querySelectorAll('.account-item.active').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            window.activeId = srcId;
            if (typeof updateDeleteButton === 'function') updateDeleteButton();
        }
    }
}

/* ── Dest change ────────────────────────────────────── */
function onDestChange() {
    const sel = document.getElementById('ic-dest-select');
    const opt = sel.options[sel.selectedIndex];
    if (!opt || !opt.value) {
        destId = null;
        document.getElementById('ic-dest-name').textContent = '—';
        document.getElementById('ic-history-list').innerHTML = '';
        if (chart) { chart.destroy(); chart = null; }
        return;
    }
    destId     = parseInt(opt.value);
    destDevise = opt.dataset.devise;
    const destName = opt.dataset.name;
    document.getElementById('ic-dest-name').textContent = destName;
    document.getElementById('ic-devise-dest').textContent = destDevise;
    updateDeviseRow();
    loadChartAndHistory();
}

function updateDeviseRow() {
    document.getElementById('ic-devise-dest').textContent = destDevise || '—';
    const show = destDevise && srcDevise && destDevise !== srcDevise;
    document.getElementById('ic-row-dest-amount').style.display = show ? 'flex' : 'none';
}

/* ── Graphique + historique ─────────────────────────── */
function loadChartAndHistory() {
    if (!destId) return;

    document.getElementById('ic-history-list').innerHTML =
        '<div class="ic-history-loading">Chargement…</div>';

    // 1. Données cumulées pour le graphique
    fetch(`/api/comptes/${srcId}/intercompte?dest_id=${destId}`)
        .then(r => r.json())
        .then(rows => {
            renderChart(rows);
        })
        .catch(() => showEmptyChart());

    // 2. Transactions brutes pour l'historique
    const destName = document.getElementById('ic-dest-name').textContent;
    fetch(`/api/comptes/${srcId}/transactions?classe=${encodeURIComponent(destName)}`)
        .then(r => r.json())
        .then(txs => renderHistory(txs))
        .catch(() => {
            document.getElementById('ic-history-list').innerHTML =
                '<div class="ic-history-empty">Erreur de chargement</div>';
        });
}

/* ── Chart ──────────────────────────────────────────── */
function renderChart(rows) {
    const canvas   = document.getElementById('ic-chart');
    const emptyEl  = document.getElementById('ic-chart-empty');

    if (chart) { chart.destroy(); chart = null; }

    if (!rows.length || rows.error) {
        showEmptyChart('Aucun virement entre ces comptes');
        return;
    }

    canvas.style.display  = 'block';
    emptyEl.style.display = 'none';

    const labels   = rows.map(r => r.date);
    const depenses = rows.map(r => parseFloat(r.depense_cumule) || 0);
    const revenus  = rows.map(r => parseFloat(r.revenu_cumule)  || 0);
    const solde    = rows.map(r => parseFloat(r.solde_cumule)   || 0);

    chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Envoyé cumulé',
                    data: depenses,
                    borderColor: '#F87171',
                    backgroundColor: 'rgba(248,113,113,0.08)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: false,
                },
                {
                    label: 'Reçu cumulé',
                    data: revenus,
                    borderColor: '#34D399',
                    backgroundColor: 'rgba(52,211,153,0.08)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: false,
                },
                {
                    label: 'Solde net',
                    data: solde,
                    borderColor: '#2DD4BF',
                    backgroundColor: 'rgba(45,212,191,0.08)',
                    borderWidth: 2.5,
                    pointRadius: 0,
                    tension: 0.3,
                    fill: true,
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        font: { family: 'Inter', size: 11 },
                        color: '#64748B',
                        boxWidth: 12,
                        padding: 12,
                    }
                },
                tooltip: {
                    backgroundColor: '#1E293B',
                    titleFont: { family: 'Inter', size: 11 },
                    bodyFont:  { family: 'Inter', size: 11 },
                    padding: 10,
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#94A3B8',
                        maxTicksLimit: 8,
                    },
                    grid: { color: 'rgba(0,0,0,0.04)' }
                },
                y: {
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#94A3B8',
                    },
                    grid: { color: 'rgba(0,0,0,0.04)' }
                }
            }
        }
    });
}

function showEmptyChart(msg) {
    const canvas  = document.getElementById('ic-chart');
    const emptyEl = document.getElementById('ic-chart-empty');
    if (chart) { chart.destroy(); chart = null; }
    canvas.style.display  = 'none';
    emptyEl.style.display = 'flex';
    if (msg) emptyEl.textContent = msg;
}

/* ── Historique ─────────────────────────────────────── */
function renderHistory(txs) {
    const container = document.getElementById('ic-history-list');

    if (!txs || !txs.length) {
        container.innerHTML = '<div class="ic-history-empty">Aucun virement entre ces comptes</div>';
        return;
    }

    txs.sort((a, b) => b.date.localeCompare(a.date));

    container.innerHTML = txs.map(tx => {
        const isRevenu = tx.est_revenu === 1 || tx.est_revenu === true;
        const cls      = isRevenu ? 'received' : 'sent';
        const sign     = isRevenu ? '+' : '−';
        const dir      = isRevenu ? `← Reçu` : `→ Envoyé`;
        const devise   = srcDevise || '';
        return `
            <div class="ic-history-item">
                <div class="ic-history-left">
                    <span class="ic-history-date">${tx.date}</span>
                    <span class="ic-history-label">${escHtml(tx.intitule || 'Virement')}</span>
                </div>
                <div class="ic-history-right">
                    <span class="ic-history-amount ${cls}">${sign}${parseFloat(tx.valeur).toFixed(2)} ${devise}</span>
                    <span class="ic-history-direction">${dir}</span>
                </div>
            </div>
        `;
    }).join('');
}

/* ── Submit ─────────────────────────────────────────── */
function submitVirement() {
    if (!destId) { showToast('⚠ Choisissez un compte destinataire.'); return; }

    const date        = document.getElementById('ic-date').value;
    const valSrc      = parseFloat(document.getElementById('ic-valeur-src').value);
    const commentaire = document.getElementById('ic-commentaire').value.trim() || 'Virement';
    const sameDevise  = srcDevise === destDevise;
    const valDest     = sameDevise ? valSrc : parseFloat(document.getElementById('ic-valeur-dest').value);

    if (!date)                        { showToast('⚠ Entrez une date.'); return; }
    if (isNaN(valSrc) || valSrc <= 0) { showToast('⚠ Montant invalide.'); return; }
    if (!sameDevise && (isNaN(valDest) || valDest <= 0)) { showToast('⚠ Montant reçu invalide.'); return; }

    const btn = document.getElementById('ic-submit');
    btn.disabled = true;
    btn.textContent = 'Envoi…';

    fetch('/api/virement', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            source_id:     srcId,
            dest_id:       destId,
            date,
            commentaire,
            valeur_source: valSrc,
            valeur_dest:   valDest
        })
    })
    .then(r => r.json())
    .then(res => {
        btn.disabled = false;
        btn.textContent = 'Valider le virement';
        if (res.success) {
            document.getElementById('ic-valeur-src').value   = '';
            document.getElementById('ic-valeur-dest').value  = '';
            document.getElementById('ic-commentaire').value  = '';
            showToast('Virement effectué ✓');
            loadChartAndHistory();
            if (typeof loadAccounts === 'function') loadAccounts();
        } else {
            showToast('⚠ ' + (res.error || 'Erreur inconnue'));
        }
    })
    .catch(() => {
        btn.disabled = false;
        btn.textContent = 'Valider le virement';
        showToast('⚠ Erreur réseau.');
    });
}

/* ── Helpers ────────────────────────────────────────── */
function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
/* showToast vient de menu_compte.js */
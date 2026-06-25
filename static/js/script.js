/* ── State ──────────────────────────────────────────── */
let accounts = [];
let editingId = null;
let activeId = null;

/* ── Init ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    loadAccounts();

    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-cancel').addEventListener('click', closeModal);
    document.getElementById('modal-save').addEventListener('click', saveEdit);
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
        if (e.target === document.getElementById('modal-overlay')) closeModal();
    });
});

/* ── Load accounts ──────────────────────────────────── */
function loadAccounts() {
    fetch('/api/comptes')
        .then(r => r.json())
        .then(data => {
            accounts = data;
            renderSidebar();
        })
        .catch(err => console.error('Erreur chargement comptes:', err));
}

/* ── Render sidebar ─────────────────────────────────── */
function renderSidebar() {
    const list = document.getElementById('account-list');

    // Globaux — comptes actifs uniquement
    const totalRev = accounts.reduce((s, c) => s + c.revenus, 0);
    const totalDep = accounts.reduce((s, c) => s + c.depenses, 0);
    const totalEcart = totalRev - totalDep;

    document.getElementById('global-revenus').textContent  = formatAmount(totalRev, '');
    document.getElementById('global-depenses').textContent = formatAmount(totalDep, '');

    const ecartEl = document.getElementById('global-ecart');
    ecartEl.textContent = (totalEcart >= 0 ? '+' : '') + formatAmount(totalEcart, '');
    ecartEl.style.color = totalEcart >= 0 ? 'var(--revenue)' : 'var(--expense)';

    list.innerHTML = '';

    accounts.forEach(compte => {
        const item = buildAccountItem(compte);
        list.appendChild(item);
    });
}

function buildAccountItem(compte) {
    const item = document.createElement('div');
    item.className = 'account-item' +
        (compte.actif ? '' : ' inactive-account') +
        (compte.id === activeId ? ' active' : '');
    item.dataset.id = compte.id;

    const soldeClass = compte.solde < 0 ? 'negative' : '';
    const debutFmt = compte.debut ? compte.debut.slice(0, 7) : '—';
    const finFmt   = compte.fin   ? compte.fin.slice(0, 7)   : '—';

    item.innerHTML = `
        <div class="account-summary">
            <div class="account-name-wrap">
                <div class="account-name">${escHtml(compte.name)}</div>
                <span class="account-devise-badge">${escHtml(compte.devise)}</span>
            </div>
            <span class="account-solde ${soldeClass}">${formatAmount(compte.solde, compte.devise)}</span>
            <span class="account-chevron">▶</span>
        </div>
        <div class="account-details">
            <div class="account-details-inner">
                <div class="account-stats">
                    <div class="stat-box rev">
                        <span class="stat-label">Revenus</span>
                        <span class="stat-value">${formatAmount(compte.revenus, compte.devise)}</span>
                    </div>
                    <div class="stat-box dep">
                        <span class="stat-label">Dépenses</span>
                        <span class="stat-value">${formatAmount(compte.depenses, compte.devise)}</span>
                    </div>
                </div>
                <div class="account-dates">${debutFmt} → ${finFmt}</div>
                <div class="account-actions">
                    <button class="btn-action btn-edit" data-id="${compte.id}">
                        ✏ Modifier
                    </button>
                    <label class="toggle-wrap" title="${compte.actif ? 'Désactiver' : 'Activer'} le compte">
                        <span class="toggle-label">${compte.actif ? 'Actif' : 'Inactif'}</span>
                        <span class="toggle-switch">
                            <input type="checkbox" ${compte.actif ? 'checked' : ''} data-toggle-id="${compte.id}">
                            <span class="toggle-track"></span>
                            <span class="toggle-thumb"></span>
                        </span>
                    </label>
                </div>
            </div>
        </div>
    `;

    // Click on summary → toggle open + set active
    item.querySelector('.account-summary').addEventListener('click', (e) => {
        // Don't trigger if click was on a button/input inside
        if (e.target.closest('.btn-action') || e.target.closest('.toggle-wrap')) return;
        toggleOpen(item, compte);
    });

    // Edit button
    item.querySelector('.btn-edit').addEventListener('click', (e) => {
        e.stopPropagation();
        openModal(compte);
    });

    // Toggle switch
    item.querySelector(`[data-toggle-id="${compte.id}"]`).addEventListener('change', (e) => {
        e.stopPropagation();
        toggleActif(compte, item);
    });

    return item;
}

function toggleOpen(item, compte) {
    const isOpen = item.classList.contains('open');

    // Close all others
    document.querySelectorAll('.account-item.open').forEach(el => el.classList.remove('open'));

    if (!isOpen) {
        item.classList.add('open');
        // Set as active (for main panel in future)
        document.querySelectorAll('.account-item.active').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        activeId = compte.id;
        showMainPanel(compte);
    } else {
        item.classList.remove('active');
        activeId = null;
        showPlaceholder();
    }
}

/* ── Main panel ─────────────────────────────────────── */
function showMainPanel(compte) {
    const panel = document.getElementById('main-panel');
    panel.innerHTML = `
        <div style="max-width: 680px;">
            <div style="display:flex; align-items:baseline; gap:12px; margin-bottom: 32px;">
                <h2 style="font-size:1.5rem; font-weight:700; color:#1E293B;">${escHtml(compte.name)}</h2>
                <span style="font-size:0.75rem; font-weight:600; color:var(--accent); background:rgba(45,212,191,0.1); padding:2px 8px; border-radius:5px;">${escHtml(compte.devise)}</span>
                ${!compte.actif ? '<span style="font-size:0.75rem;color:#64748B;background:#F1F5F9;padding:2px 8px;border-radius:5px;">Inactif</span>' : ''}
            </div>
            <p style="color:#94A3B8; font-size:0.9rem;">Le tableau des transactions sera affiché ici dans un prochain onglet.</p>
        </div>
    `;
}

function showPlaceholder() {
    const panel = document.getElementById('main-panel');
    panel.innerHTML = `
        <div class="main-placeholder" id="main-placeholder">
            <div class="placeholder-icon">⬡</div>
            <h2>Sélectionnez un compte</h2>
            <p>Cliquez sur un compte dans la barre latérale pour afficher son tableau de bord.</p>
        </div>
    `;
}

/* ── Edit modal ─────────────────────────────────────── */
function openModal(compte) {
    editingId = compte.id;
    document.getElementById('edit-name').value = compte.name;
    document.getElementById('edit-devise').value = compte.devise;
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('edit-name').focus();
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('open');
    editingId = null;
}

function saveEdit() {
    const name   = document.getElementById('edit-name').value.trim();
    const devise = document.getElementById('edit-devise').value.trim().toUpperCase();

    if (!name || !devise) {
        showToast('Nom et devise requis.');
        return;
    }

    fetch(`/api/comptes/${editingId}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, devise })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) {
            closeModal();
            loadAccounts(); // Reload to reflect changes
            showToast('Compte mis à jour ✓');
        }
    })
    .catch(() => showToast('Erreur lors de la sauvegarde.'));
}

/* ── Toggle actif ───────────────────────────────────── */
function toggleActif(compte, item) {
    fetch(`/api/comptes/${compte.id}/toggle`, { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                compte.actif = res.actif;
                // Update classes
                if (res.actif) {
                    item.classList.remove('inactive-account');
                } else {
                    item.classList.add('inactive-account');
                }
                // Update label
                const label = item.querySelector('.toggle-label');
                if (label) label.textContent = res.actif ? 'Actif' : 'Inactif';
                showToast(res.actif ? 'Compte activé ✓' : 'Compte désactivé');
            }
        })
        .catch(() => showToast('Erreur lors du changement d\'état.'));
}

/* ── Toast ──────────────────────────────────────────── */
let toastTimer;
function showToast(msg) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
}

/* ── Helpers ────────────────────────────────────────── */
function formatAmount(val, devise) {
    const formatted = Math.abs(val).toLocaleString('fr-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return (val < 0 ? '−' : '') + formatted + (devise ? ' ' + devise : '');
}

function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
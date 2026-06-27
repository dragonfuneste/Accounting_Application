/* ── State ──────────────────────────────────────────── */
window.accounts  = [];
let accounts = window.accounts;
let editingId = null;
let deletingId = null;
window.activeId  = null;
let activeId = window.activeId;

/* ── Init ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    loadAccounts();

    // Sidebar buttons
    document.getElementById('btn-add-compte').addEventListener('click', openAddModal);
    document.getElementById('btn-delete-compte').addEventListener('click', openDeleteModal);

    // Add modal
    document.getElementById('add-close').addEventListener('click', closeAddModal);
    document.getElementById('add-cancel').addEventListener('click', closeAddModal);
    document.getElementById('add-save').addEventListener('click', saveNewCompte);
    document.getElementById('add-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'add-overlay') closeAddModal();
    });
    document.getElementById('add-name').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') saveNewCompte();
    });

    // Edit modal
    document.getElementById('edit-close').addEventListener('click', closeEditModal);
    document.getElementById('edit-cancel').addEventListener('click', closeEditModal);
    document.getElementById('edit-save').addEventListener('click', saveEdit);
    document.getElementById('edit-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'edit-overlay') closeEditModal();
    });

    // Delete modal
    document.getElementById('delete-close').addEventListener('click', closeDeleteModal);
    document.getElementById('delete-cancel').addEventListener('click', closeDeleteModal);
    document.getElementById('delete-confirm').addEventListener('click', confirmDelete);
    document.getElementById('delete-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'delete-overlay') closeDeleteModal();
    });
});

/* ── Load ───────────────────────────────────────────── */
function loadAccounts() {
    fetch('/api/comptes')
        .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(data => { accounts = data; window.accounts = data; renderSidebar(); })
        .catch(err => {
            console.error('Erreur:', err);
            document.getElementById('account-list').innerHTML =
                '<div class="account-list-loading" style="color:var(--expense)">Erreur de chargement</div>';
        });
}

/* ── Render sidebar ─────────────────────────────────── */
function renderSidebar() {
    const totalRev   = accounts.reduce((s, c) => s + c.revenus, 0);
    const totalDep   = accounts.reduce((s, c) => s + c.depenses, 0);
    const totalEcart = totalRev - totalDep;

    document.getElementById('global-revenus').textContent  = formatAmount(totalRev, '');
    document.getElementById('global-depenses').textContent = formatAmount(totalDep, '');
    const ecartEl = document.getElementById('global-ecart');
    ecartEl.textContent = (totalEcart >= 0 ? '+' : '') + formatAmount(totalEcart, '');
    ecartEl.style.color = totalEcart >= 0 ? 'var(--revenue)' : 'var(--expense)';

    const list = document.getElementById('account-list');
    list.innerHTML = '';
    accounts.forEach(c => list.appendChild(buildAccountItem(c)));

    updateDeleteButton();
}

/* ── Build account item ─────────────────────────────── */
function buildAccountItem(compte) {
    const item = document.createElement('div');
    item.className = 'account-item'
        + (compte.actif ? '' : ' inactive-account')
        + (compte.id === activeId ? ' active open' : '');
    item.dataset.id = compte.id;

    const debutFmt = compte.debut ? compte.debut.slice(0, 7) : '—';
    const finFmt   = compte.fin   ? compte.fin.slice(0, 7)   : '—';

    item.innerHTML = `
        <div class="account-summary">
            <div class="account-name-wrap">
                <div class="account-name">${escHtml(compte.name)}</div>
                <span class="account-devise-badge">${escHtml(compte.devise)}</span>
            </div>
            <span class="account-solde ${compte.solde < 0 ? 'negative' : ''}">${formatAmount(compte.solde, compte.devise)}</span>
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
                    <button class="btn-action btn-edit" data-id="${compte.id}">✏ Modifier</button>
                    <label class="toggle-wrap">
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

    item.querySelector('.account-summary').addEventListener('click', (e) => {
        if (e.target.closest('.btn-action') || e.target.closest('.toggle-wrap')) return;
        toggleOpen(item, compte);
    });
    item.querySelector('.btn-edit').addEventListener('click', (e) => {
        e.stopPropagation();
        openEditModal(compte);
    });
    item.querySelector(`[data-toggle-id="${compte.id}"]`).addEventListener('change', () => {
        toggleActif(compte, item);
    });

    return item;
}

/* ── Toggle open ────────────────────────────────────── */
function toggleOpen(item, compte) {
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.account-item.open').forEach(el => el.classList.remove('open'));
    document.querySelectorAll('.account-item.active').forEach(el => el.classList.remove('active'));

    if (!isOpen) {
        item.classList.add('open', 'active');
        activeId = compte.id; window.activeId = activeId;
        showMainPanel(compte);
    } else {
        activeId = null; window.activeId = null;
        showPlaceholder();
    }
    updateDeleteButton();
}

/* ── Main panel ─────────────────────────────────────── */
function showMainPanel(compte) {
    window.location.href = '/compte?id=' + compte.id;
}

function showPlaceholder() {
    document.getElementById('main-panel').innerHTML = `
        <div class="main-placeholder">
            <div class="placeholder-icon">⬡</div>
            <h2>Sélectionnez un compte</h2>
            <p>Cliquez sur un compte dans la barre latérale pour afficher son tableau de bord.</p>
        </div>
    `;
}

/* ── Add modal ──────────────────────────────────────── */
function openAddModal() {
    document.getElementById('add-name').value = '';
    document.getElementById('add-devise').value = 'EUR';
    document.getElementById('add-overlay').classList.add('open');
    setTimeout(() => document.getElementById('add-name').focus(), 50);
}

function closeAddModal() {
    document.getElementById('add-overlay').classList.remove('open');
}

function saveNewCompte() {
    const name   = document.getElementById('add-name').value.trim();
    const devise = document.getElementById('add-devise').value.trim().toUpperCase();
    if (!name || !devise) { showToast('Nom et devise requis.'); return; }

    fetch('/api/comptes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, devise })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) { closeAddModal(); loadAccounts(); showToast(`Compte « ${res.name} » créé ✓`); }
        else showToast('Erreur : ' + res.error);
    })
    .catch(() => showToast('Erreur réseau.'));
}

/* ── Edit modal ─────────────────────────────────────── */
function openEditModal(compte) {
    editingId = compte.id;
    document.getElementById('edit-name').value = compte.name;
    document.getElementById('edit-devise').value = compte.devise;
    document.getElementById('edit-overlay').classList.add('open');
    document.getElementById('edit-name').focus();
}

function closeEditModal() {
    document.getElementById('edit-overlay').classList.remove('open');
    editingId = null;
}

function saveEdit() {
    const name   = document.getElementById('edit-name').value.trim();
    const devise = document.getElementById('edit-devise').value.trim().toUpperCase();
    if (!name || !devise) { showToast('Nom et devise requis.'); return; }

    fetch(`/api/comptes/${editingId}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, devise })
    })
    .then(r => r.json())
    .then(res => {
        if (res.success) { closeEditModal(); loadAccounts(); showToast('Compte mis à jour ✓'); }
        else showToast('Erreur : ' + res.error);
    })
    .catch(() => showToast('Erreur sauvegarde.'));
}

/* ── Toggle actif ───────────────────────────────────── */
function toggleActif(compte, item) {
    fetch(`/api/comptes/${compte.id}/toggle`, { method: 'POST' })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                compte.actif = res.actif;
                item.classList.toggle('inactive-account', !res.actif);
                item.querySelector('.toggle-label').textContent = res.actif ? 'Actif' : 'Inactif';
                loadAccounts();
                showToast(res.actif ? 'Compte activé ✓' : 'Compte désactivé');
            }
        })
        .catch(() => showToast("Erreur toggle."));
}

/* ── Delete modal ───────────────────────────────────── */
function updateDeleteButton() {
    document.getElementById('btn-delete-compte').disabled = (activeId === null);
}

function openDeleteModal() {
    if (activeId === null) return;
    const compte = accounts.find(c => c.id === activeId);
    if (!compte) return;
    deletingId = activeId;

    const nb = compte.nb_transactions ?? 0;
    const el = document.getElementById('delete-warning-text');
    if (nb > 0) {
        el.innerHTML = `Vous allez supprimer <strong>${escHtml(compte.name)}</strong> ainsi que
            <span class="delete-warning-count">${nb} transaction${nb > 1 ? 's' : ''}</span> associée${nb > 1 ? 's' : ''}.
            <br><br>Cette action est <strong>irréversible</strong>.`;
    } else {
        el.innerHTML = `Vous allez supprimer <strong>${escHtml(compte.name)}</strong>.<br><br>
            Cette action est <strong>irréversible</strong>.`;
    }
    document.getElementById('delete-overlay').classList.add('open');
}

function closeDeleteModal() {
    document.getElementById('delete-overlay').classList.remove('open');
    deletingId = null;
}

function confirmDelete() {
    if (!deletingId) return;
    fetch(`/api/comptes/${deletingId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                closeDeleteModal();
                activeId = null; window.activeId = null;
                showPlaceholder();
                loadAccounts();
                showToast('Compte supprimé');
            } else showToast('Erreur : ' + res.error);
        })
        .catch(() => showToast('Erreur suppression.'));
}

/* ── Toast ──────────────────────────────────────────── */
let toastTimer;
function showToast(msg) {
    let toast = document.querySelector('.toast');
    if (!toast) { toast = document.createElement('div'); toast.className = 'toast'; document.body.appendChild(toast); }
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
}

/* ── Helpers ────────────────────────────────────────── */
function formatAmount(val, devise) {
    const fmt = Math.abs(val).toLocaleString('fr-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return (val < 0 ? '−' : '') + fmt + (devise ? ' ' + devise : '');
}

function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
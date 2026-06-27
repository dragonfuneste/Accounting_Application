/* ── Tabs ───────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
        if (btn.dataset.tab === 'virement' && currentCompte) initVirement(currentCompte);
    });
});

/* ── Override showMainPanel depuis menu_compte.js ──── */
let currentCompte = null;

function showMainPanel(compte) {
    currentCompte = compte;
    document.getElementById('compte-title').textContent  = compte.name;
    document.getElementById('compte-devise').textContent = compte.devise;

    const statusEl = document.getElementById('compte-status');
    statusEl.style.display = compte.actif ? 'none' : 'inline-block';

    // Init onglet actif si c'est virement
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab?.dataset.tab === 'virement') initVirement(compte);
}

function showPlaceholder() {
    document.getElementById('compte-title').textContent  = '—';
    document.getElementById('compte-devise').textContent = '—';
    document.getElementById('compte-status').style.display = 'none';
}

/* ── Charger le compte depuis l'URL (?id=X) ─────────── */
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const id = parseInt(params.get('id'));
    if (id) {
        // Attendre que menu_compte.js ait chargé les comptes
        const wait = setInterval(() => {
            if (window.accounts && window.accounts.length > 0) {
                clearInterval(wait);
                const compte = window.accounts.find(c => c.id === id);
                if (compte) {
                    // Ouvrir et activer le bon compte dans la sidebar
                    const item = document.querySelector(`.account-item[data-id="${id}"]`);
                    if (item) {
                        document.querySelectorAll('.account-item.open').forEach(el => el.classList.remove('open'));
                        document.querySelectorAll('.account-item.active').forEach(el => el.classList.remove('active'));
                        item.classList.add('open', 'active');
                        window.activeId = id;
                        updateDeleteButton();
                    }
                    showMainPanel(compte);
                }
            }
        }, 50);
    }
});

/* ── Virement ────────────────────────────────────────── */
function initVirement(compteActif) {
    // Remplir le nom source
    document.getElementById('virement-source-name').textContent = compteActif.name;
    document.getElementById('virement-devise-src').textContent  = compteActif.devise;

    // Date du jour par défaut
    const today = new Date().toISOString().slice(0, 10);
    document.getElementById('virement-date').value = today;

    // Remplir le select destinataire (tous sauf source)
    const sel = document.getElementById('virement-dest');
    sel.innerHTML = '<option value="">Choisir un compte…</option>';
    (window.accounts || []).forEach(c => {
        if (c.id !== compteActif.id) {
            const opt = document.createElement('option');
            opt.value    = c.id;
            opt.dataset.devise = c.devise;
            opt.textContent = c.name + ' (' + c.devise + ')';
            sel.appendChild(opt);
        }
    });

    // Afficher/masquer champ montant reçu selon devise
    sel.addEventListener('change', () => {
        const opt = sel.options[sel.selectedIndex];
        const destDevise = opt?.dataset?.devise || '';
        const sameCurrency = destDevise === compteActif.devise || !destDevise;

        document.getElementById('virement-devise-dest').textContent = destDevise || '—';
        document.getElementById('vform-row-dest-amount').style.display = sameCurrency ? 'none' : 'flex';
    });

    // Soumettre
    const btn = document.getElementById('virement-submit');
    // Retirer ancien listener si existe
    btn.replaceWith(btn.cloneNode(true));
    document.getElementById('virement-submit').addEventListener('click', () => submitVirement(compteActif));
}

function submitVirement(compteActif) {
    const destId = parseInt(document.getElementById('virement-dest').value);
    if (!destId) { showVirementError('Choisissez un compte destinataire.'); return; }

    // Naviguer vers la page intercompte dédiée avec src et dest
    window.location.href = `/intercompte?src=${compteActif.id}&dest=${destId}`;
}

function showVirementError(msg) {
    // Réutilise le toast
    if (typeof showToast === 'function') showToast('⚠ ' + msg);
}
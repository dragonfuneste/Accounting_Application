const API = '/api/projects';
let selectedObjId = null;
let projectsData  = [];

// État du modal de liaison
let linkModal = {
    oid         : null,
    sid         : null,
    accounts    : [],
    account     : null,
    search      : '',
    typeFilter  : '',
    transactions: [],
};

document.addEventListener('DOMContentLoaded', () => {
    refresh();
    document.getElementById('btnNewProject').onclick   = () => openModal('modalProject');
    document.getElementById('btnDeleteProject').onclick = () => deleteProject();
    document.getElementById('btnNewStep').onclick      = () => openModal('modalStep');

    // Filtres du modal de liaison
    document.getElementById('linkSearch').addEventListener('input', e => {
        linkModal.search = e.target.value;
        fetchTransactions();
    });
    document.getElementById('linkTypeFilter').addEventListener('change', e => {
        linkModal.typeFilter = e.target.value;
        fetchTransactions();
    });
    document.getElementById('linkAccount').addEventListener('change', e => {
        linkModal.account = e.target.value;
        fetchTransactions();
    });
});

// ══════════════════════════════════════════════════════════════════════════════
//  REFRESH
// ══════════════════════════════════════════════════════════════════════════════

async function refresh() {
    try {
        const res  = await fetch(API);
        const data = await res.json();
        projectsData = data.objectifs;
        updateKPIs(data.summary);
        renderSticky(data.objectifs);
        if (selectedObjId) {
            const obj = data.objectifs.find(o => o.id === selectedObjId);
            if (obj) renderDetail(obj);
            else     hideDetail();
        }
    } catch (err) {
        console.error('Erreur refresh projects:', err);
    }
}

// ══════════════════════════════════════════════════════════════════════════════
//  KPIs
// ══════════════════════════════════════════════════════════════════════════════

function updateKPIs(summary) {
    document.getElementById('kpiEpargne').textContent  = fmt(summary['épargné_total'])  + ' €';
    document.getElementById('kpiDepense').textContent  = fmt(summary['dépensé_total'])  + ' €';
    document.getElementById('kpiObjectif').textContent = fmt(summary['objectif_total']) + ' €';
    document.getElementById('kpiRestant').textContent  = fmt(summary['restant_total'])  + ' €';
    document.getElementById('kpiNbProjects').textContent = summary['nb_objectifs'] + ' projets';
}

// ══════════════════════════════════════════════════════════════════════════════
//  STICKY NOTES
// ══════════════════════════════════════════════════════════════════════════════

function renderSticky(objectifs) {
    const row = document.getElementById('stickyRow');
    row.innerHTML = '';

    if (objectifs.length === 0) {
        row.innerHTML = '<span style="font-family:var(--mono);font-size:11px;color:var(--text-muted);padding:20px;">Aucun projet — créez-en un</span>';
        return;
    }

    objectifs.forEach(obj => {
        const pct       = obj.bar_global.percent;
        const fillClass = pct >= 100 ? 'complete' : pct >= 75 ? 'warning' : '';

        const card = document.createElement('div');
        card.className = 'sticky-card' + (obj.id === selectedObjId ? ' selected' : '');
        card.dataset.id = obj.id;

        card.innerHTML = `
            <div class="sticky-top">
                <span class="sticky-logo">${obj.logo || '🎯'}</span>
                <span class="sticky-rank">#${obj.priority_rank + 1}</span>
            </div>
            <div class="sticky-name">${esc(obj.name)}</div>
            <div class="sticky-deadline ${obj.deadline_depasse ? 'overdue' : ''}">
                ${obj.deadline ? '⏱ ' + obj.deadline : '—'}
            </div>
            <div class="sticky-progress-wrap">
                <div class="sticky-progress-label">
                    <span>${pct}%</span>
                    <span>${fmt(obj.montant_epargne)} / ${fmt(obj.montant_objectif)} €</span>
                </div>
                <div class="sticky-track">
                    <div class="sticky-fill ${fillClass}" style="width:${Math.min(pct,100)}%"></div>
                </div>
            </div>
        `;

        card.onclick = () => selectProject(obj.id);
        row.appendChild(card);
    });
}

function selectProject(oid) {
    selectedObjId = oid;
    document.querySelectorAll('.sticky-card').forEach(c =>
        c.classList.toggle('selected', c.dataset.id === oid)
    );
    document.getElementById('btnDeleteProject').disabled = false;
    const obj = projectsData.find(o => o.id === oid);
    if (obj) renderDetail(obj);
}

// ══════════════════════════════════════════════════════════════════════════════
//  DETAIL PANEL
// ══════════════════════════════════════════════════════════════════════════════

function renderDetail(obj) {
    document.getElementById('detailPanel').style.display = '';
    document.getElementById('detailLogo').textContent = obj.logo || '🎯';
    document.getElementById('detailName').textContent = obj.name;
    document.getElementById('detailBut').textContent  = obj.but || '';

    const deadlineEl = document.getElementById('detailDeadline');
    deadlineEl.textContent = obj.deadline ? '⏱ ' + obj.deadline : '';
    deadlineEl.className   = 'detail-deadline' + (obj.deadline_depasse ? ' overdue' : '');

    const pct = obj.bar_global.percent;
    document.getElementById('detailProgress').textContent     = pct + '%';
    document.getElementById('detailAmounts').textContent      = fmt(obj.montant_epargne) + ' € / ' + fmt(obj.montant_objectif) + ' €';
    document.getElementById('detailProgressFill').style.width = Math.min(pct, 100) + '%';

    renderSteps(obj.steps);
}

function hideDetail() {
    document.getElementById('detailPanel').style.display = 'none';
    selectedObjId = null;
    document.getElementById('btnDeleteProject').disabled = true;
}

function renderSteps(steps) {
    const grid = document.getElementById('stepsGrid');
    grid.innerHTML = '';

    if (steps.length === 0) {
        grid.innerHTML = '<div class="steps-empty">Aucune étape — ajoutez-en une</div>';
        return;
    }

    steps.forEach(step => {
        const col = document.createElement('div');
        col.className = 'step-col';

        const badgeClass = {
            'En cours' : 'en-cours',
            'Terminé'  : 'termine',
            'En pause' : 'en-pause',
        }[step.status] || 'en-cours';

        const bg = step.bar_global.percent;
        const br = step.bar_revenu.percent;
        const bd = step.bar_depense.percent;

        col.innerHTML = `
            <div class="step-col-header">
                <div class="step-col-name">${esc(step.name)}</div>
                <span class="step-badge ${badgeClass}">${step.status}</span>
            </div>

            <div class="step-bars">
                <div class="step-bar-row">
                    <div class="step-bar-label">
                        <span>Accompli</span>
                        <span>${bg}% — ${fmt(step.bar_global.value)} €</span>
                    </div>
                    <div class="step-track">
                        <div class="step-fill global" style="width:${Math.min(bg,100)}%"></div>
                    </div>
                </div>
                <div class="step-bar-row">
                    <div class="step-bar-label">
                        <span>Revenus</span>
                        <span>${br}% — ${fmt(step.bar_revenu.value)} €</span>
                    </div>
                    <div class="step-track">
                        <div class="step-fill revenu" style="width:${Math.min(br,100)}%"></div>
                    </div>
                </div>
                <div class="step-bar-row">
                    <div class="step-bar-label">
                        <span>Dépenses</span>
                        <span>${bd}% — ${fmt(step.bar_depense.value)} €</span>
                    </div>
                    <div class="step-track">
                        <div class="step-fill depense" style="width:${Math.min(bd,100)}%"></div>
                    </div>
                </div>
            </div>

            <div class="step-but">${esc(step.but || '')}</div>

            <div class="step-meta">
                <div class="step-meta-row">
                    <span>Début</span>
                    <span>${step.date_debut || '—'}</span>
                </div>
                <div class="step-meta-row">
                    <span>Fin</span>
                    <span class="${step.deadline_depasse ? 'overdue' : ''}">${step.date_fin || '—'}</span>
                </div>
                <div class="step-meta-row">
                    <span>Objectif</span>
                    <span>${fmt(step.bar_global.target)} €</span>
                </div>
                <div class="step-meta-row">
                    <span>Restant</span>
                    <span>${fmt(step.bar_global.target - step.bar_global.value)} €</span>
                </div>
            </div>

            <div class="step-actions">
                <button class="btn btn-primary btn-sm" onclick="openLinkModal('${step.id}')">
                    ＋ Lier transaction
                </button>
                <button class="step-delete" onclick="deleteStep('${step.id}')">✕ Supprimer</button>
            </div>
        `;

        grid.appendChild(col);
    });
}

// ══════════════════════════════════════════════════════════════════════════════
//  MODAL LIAISON TRANSACTIONS
// ══════════════════════════════════════════════════════════════════════════════

async function openLinkModal(sid) {
    if (!selectedObjId) return;

    linkModal.oid    = selectedObjId;
    linkModal.sid    = sid;
    linkModal.search = '';
    linkModal.typeFilter = '';
    document.getElementById('linkSearch').value     = '';
    document.getElementById('linkTypeFilter').value = '';
    document.getElementById('linkTxList').innerHTML = '<div class="link-loading">Chargement…</div>';

    // Charger la liste des comptes
    const res      = await fetch(`${API}/accounts`);
    const accounts = await res.json();
    linkModal.accounts = accounts;

    const select = document.getElementById('linkAccount');
    select.innerHTML = accounts.map(a =>
        `<option value="${esc(a.name)}">${esc(a.name)} (${esc(a.devise)})</option>`
    ).join('');
    linkModal.account = accounts[0]?.name || null;

    openModal('modalLink');
    fetchTransactions();
}

async function fetchTransactions() {
    if (!linkModal.account) return;

    const params = new URLSearchParams({
        oid   : linkModal.oid,
        sid   : linkModal.sid,
        search: linkModal.search,
        type  : linkModal.typeFilter,
    });

    const res  = await fetch(`${API}/accounts/${encodeURIComponent(linkModal.account)}/transactions?${params}`);
    const txs  = await res.json();
    linkModal.transactions = txs;
    renderTxList(txs);
}

function renderTxList(txs) {
    const list = document.getElementById('linkTxList');

    if (txs.length === 0) {
        list.innerHTML = '<div class="link-empty">Aucune transaction trouvée</div>';
        return;
    }

    list.innerHTML = txs.map(tx => {
        const linked   = tx.is_linked;
        const typeClass = tx.depense ? 'tx-depense' : 'tx-revenu';
        const typeLabel = tx.depense ? '▼ Dépense' : '▲ Revenu';
        const sign      = tx.depense ? '−' : '+';

        return `
            <div class="tx-row ${linked ? 'tx-linked' : ''}">
                <div class="tx-info">
                    <div class="tx-main">
                        <span class="tx-intitule">${esc(tx.intitule)}</span>
                        <span class="tx-badge ${typeClass}">${typeLabel}</span>
                    </div>
                    <div class="tx-sub">
                        <span class="tx-date">${esc(tx.date)}</span>
                        <span class="tx-cat">${esc(tx.categorie)} · ${esc(tx.classe)}</span>
                    </div>
                </div>
                <div class="tx-right">
                    <span class="tx-montant ${typeClass}">${sign} ${fmt(tx.montant)} €</span>
                    ${linked
                        ? `<button class="btn btn-danger btn-xs" onclick="unlinkTx('${tx.tid}', ${tx.depense})">Délier</button>`
                        : `<button class="btn btn-primary btn-xs" onclick="linkTx('${tx.tid}', ${tx.depense})">Lier</button>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

async function linkTx(tid, depense) {
    const res = await fetch(`${API}/objective/${linkModal.oid}/step/${linkModal.sid}/link`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({
            account_name: linkModal.account,
            tid,
            depense,
        }),
    });

    if (res.ok) {
        fetchTransactions(); // recharge le modal
        refresh();           // recharge les KPIs et les barres
    }
}

async function unlinkTx(tid, depense) {
    const res = await fetch(`${API}/objective/${linkModal.oid}/step/${linkModal.sid}/link`, {
        method : 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({
            account_name: linkModal.account,
            tid,
            depense,
        }),
    });

    if (res.ok) {
        fetchTransactions();
        refresh();
    }
}

// ══════════════════════════════════════════════════════════════════════════════
//  CRUD OBJECTIF
// ══════════════════════════════════════════════════════════════════════════════

async function submitNewProject() {
    const name       = document.getElementById('newObjName').value.trim();
    const but        = document.getElementById('newObjBut').value.trim();
    const importance = parseInt(document.getElementById('newObjImportance').value) || 1;
    const deadline   = document.getElementById('newObjDeadline').value || null;
    const logo       = document.getElementById('newObjLogo').value.trim() || '🎯';

    if (!name) return alert('Nom obligatoire');

    const res = await fetch(`${API}/objective/add`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ name, but, importance, deadline, logo }),
    });
    if (res.ok) { closeModal('modalProject'); refresh(); }
}

async function deleteProject() {
    if (!selectedObjId) return;
    if (!confirm('Supprimer ce projet et toutes ses étapes ?')) return;

    const res = await fetch(`${API}/objective/${selectedObjId}/delete`, { method: 'DELETE' });
    if (res.ok) { hideDetail(); refresh(); }
}

// ══════════════════════════════════════════════════════════════════════════════
//  CRUD STEP
// ══════════════════════════════════════════════════════════════════════════════

async function submitNewStep() {
    if (!selectedObjId) return;

    const name     = document.getElementById('newStepName').value.trim();
    const but      = document.getElementById('newStepBut').value.trim();
    const target   = parseFloat(document.getElementById('newStepTarget').value) || 0;
    const deadline = document.getElementById('newStepDeadline').value || null;

    if (!name)       return alert('Nom obligatoire');
    if (target <= 0) return alert('Objectif financier obligatoire');

    const res = await fetch(`${API}/objective/${selectedObjId}/step/add`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ name, but, target, deadline }),
    });
    if (res.ok) { closeModal('modalStep'); refresh(); }
}

async function deleteStep(sid) {
    if (!selectedObjId) return;
    if (!confirm('Supprimer cette étape ?')) return;

    const res = await fetch(`${API}/objective/${selectedObjId}/step/${sid}/delete`, { method: 'DELETE' });
    if (res.ok) refresh();
}

// ══════════════════════════════════════════════════════════════════════════════
//  MODALS
// ══════════════════════════════════════════════════════════════════════════════

function openModal(id)  { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.style.display = 'none';
    }
});

// ══════════════════════════════════════════════════════════════════════════════
//  UTILS
// ══════════════════════════════════════════════════════════════════════════════

function fmt(n) {
    return Number(n || 0).toLocaleString('fr-FR', { minimumFractionDigits: 2 });
}

function esc(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
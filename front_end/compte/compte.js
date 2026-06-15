/**
 * GESTION DÉTAILLÉE D'UN COMPTE - compte.js
 */

const _pathParts = window.location.pathname.split('/').filter(p => p !== "");
const _lastPart = _pathParts.pop();
let currentAccountIndex = /^\d+$/.test(_lastPart) ? parseInt(_lastPart) : 0;

let selectedLineIndex = null;
let columns = [];
let cachedRows = [];
let isCreating = false;
let sortStates = {};
let filterTimeout;

const COMBO_COLS = ["Categorie", "Classe", "Type"];
const REQUIRED_COLS = ["Date", "Valeur"];
const DATE_COL = "Date";

document.addEventListener('DOMContentLoaded', async () => {
    await initAccountSelector();
    await loadAccountData();
});

/* ─── 1. CHARGEMENT ET SYNC ─── */

async function initAccountSelector() {
    const selector = document.getElementById('accountSelector');
    if (!selector) return;
    try {
        const res = await fetch('/api/account/list');
        const accounts = await res.json();
        selector.innerHTML = accounts.map(acc => `
            <option value="${acc.index}" ${acc.index == currentAccountIndex ? 'selected' : ''}>
                ${acc.name.toUpperCase()}
            </option>
        `).join('');
        selector.onchange = (e) => { window.location.href = `/compte/${e.target.value}`; };
    } catch (err) { console.error("Erreur liste comptes:", err); }
}

async function loadAccountData() {
    try {
        const savedFilters = {};
        document.querySelectorAll('.filter-input').forEach(input => {
            if (input.value.trim() !== "") {
                savedFilters[input.dataset.col] = input.value;
            }
        });

        const res = await fetch(`/api/account/${currentAccountIndex}/data`);
        const data = await res.json();
        cachedRows = data.rows || [];

        // FIX : exclure real_index dès l'extraction
        if (cachedRows.length > 0) {
            columns = Object.keys(cachedRows[0]).filter(k => k !== 'real_index');
        } else {
            columns = ['Categorie', 'Classe', 'Date', 'Intitule', 'Type', 'Valeur'];
        }

        renderTableHead(columns);
        renderTableBody(cachedRows);

        Object.keys(savedFilters).forEach(col => {
            const input = document.querySelector(`.filter-input[data-col="${col}"]`);
            if (input) input.value = savedFilters[col];
        });

        if (Object.keys(savedFilters).length > 0) {
            const lastCol = Object.keys(savedFilters).pop();
            triggerServerFilter(lastCol, savedFilters[lastCol]);
        }

    } catch (err) { console.error("Erreur de chargement:", err); }
}

/* ─── 2. RENDU DU TABLEAU ─── */

function renderTableHead(cols) {
    const thead = document.getElementById('tableHead');
    if (!thead) return;

    // cols est déjà sans real_index grâce au fix dans loadAccountData
    let html = `<tr>`;
    cols.forEach(col => {
        const state = sortStates[col] || null;
        let icon = (state === 'asc') ? " ↑" : (state === 'desc' ? " ↓" : " ↕");
        html += `<th onclick="handleSort('${col}')" style="cursor:pointer; user-select:none;">
                    ${col}<span class="sort-icon">${icon}</span>
                 </th>`;
    });
    html += `<th>Actions</th></tr>`;

    html += `<tr class="filter-row">`;
    cols.forEach(col => {
        html += `<td><input type="text" class="filter-input" data-col="${col}" onkeyup="handleFilter(event)"></td>`;
    });
    html += `<td></td></tr>`;

    thead.innerHTML = html;
}

function renderTableBody(rows) {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    rows.forEach((row) => {
        const tr = document.createElement('tr');
        tr.dataset.realIndex = row.real_index;

        tr.innerHTML = columns.map(col => {
            const val = row[col] ?? "";
            const isNum = typeof val === 'number';
            const cls = isNum ? (val < 0 ? 'num negative' : 'num positive') : '';
            // Forcer l'affichage ISO (YYYY-MM-DD) pour les dates
            let display = isNum ? val.toFixed(2) : val;
            if (col === DATE_COL && display) {
                // Convertir DD/MM/YYYY → YYYY-MM-DD si besoin
                const m = String(display).match(/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/);
                if (m) display = `${m[3]}-${m[2]}-${m[1]}`;
            }
            return `<td class="${cls}">${display}</td>`;
        }).join('') + '<td></td>';

        tr.onclick = () => {
            document.querySelectorAll('#tableBody tr').forEach(r => r.classList.remove('selected'));
            tr.classList.add('selected');
            selectedLineIndex = row.real_index;
        };

        tr.ondblclick = () => uiEditRow(tr, row.real_index, row);
        tbody.appendChild(tr);
    });
}

/* ─── 3. FILTRAGE ET TRI ─── */

function handleFilter(event) {
    clearTimeout(filterTimeout);
    const input = event.target;
    const column = input.dataset.col;
    const keyword = input.value;
    filterTimeout = setTimeout(() => triggerServerFilter(column, keyword), 300);
}

async function triggerServerFilter(column, keyword) {
    try {
        const res = await fetch(`/api/account/${currentAccountIndex}/filter`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column, keyword })
        });
        const data = await res.json();
        renderTableBody(data.rows);
    } catch (err) { console.error("Erreur filtrage:", err); }
}

async function handleSort(column) {
    const currentState = sortStates[column] || 'desc';
    let nextState = (currentState === 'asc') ? 'desc' : 'asc';
    let apiValue = (nextState === 'asc');
    sortStates = { [column]: nextState };

    try {
        await fetch(`/api/account/${currentAccountIndex}/sort`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column, croissant: apiValue })
        });
        await loadAccountData();
    } catch (err) { console.error("Erreur tri:", err); }
}

/* ─── 4. COMPOSANTS D'ÉDITION ─── */

function toInputDate(val) {
    if (!val) return "";
    const s = String(val).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    const m = s.match(/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/);
    if (m) return `${m[3]}-${m[2]}-${m[1]}`;
    return "";
}

function fromInputDate(val) {
    const s = String(val).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    const m = s.match(/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/);
    if (m) return `${m[3]}-${m[2]}-${m[1]}`;
    return val;
}

function createDateInput(value = "") {
    const input = document.createElement('input');
    input.type = "date";
    input.className = "inline-input date-input";
    input.dataset.col = DATE_COL;
    input.value = toInputDate(value);
    return input;
}

function createCombobox(colName, value = "") {
    const wrapper = document.createElement('div');
    wrapper.className = "combo-wrapper";

    const input = document.createElement('input');
    input.type = "text";
    input.className = "inline-input";
    input.value = value;
    input.dataset.col = colName;
    input.autocomplete = "off";

    const dropdown = document.createElement('ul');
    dropdown.className = "combo-dropdown";

    const showSuggestions = (filter) => {
        const uniqueVals = [...new Set(cachedRows.map(r => r[colName]))]
            .filter(v => v !== null && v !== undefined && v !== "");
        const options = uniqueVals.filter(v =>
            v.toString().toLowerCase().includes(filter.toLowerCase())
        );
        dropdown.innerHTML = '';
        if (options.length === 0) { dropdown.style.display = 'none'; return; }
        options.forEach(opt => {
            const li = document.createElement('li');
            li.textContent = opt;
            li.onmousedown = (e) => {
                e.preventDefault();
                input.value = opt;
                dropdown.style.display = 'none';
            };
            dropdown.appendChild(li);
        });
        dropdown.style.display = 'block';
    };

    input.oninput = () => showSuggestions(input.value);
    input.onfocus = () => showSuggestions(input.value);
    input.onblur = () => setTimeout(() => dropdown.style.display = 'none', 200);

    wrapper.appendChild(input);
    wrapper.appendChild(dropdown);
    return wrapper;
}

function createCell(col, value = "") {
    const td = document.createElement('td');
    if (col === DATE_COL) {
        td.appendChild(createDateInput(value));
    } else if (COMBO_COLS.includes(col)) {
        td.appendChild(createCombobox(col, value));
    } else {
        const inp = document.createElement('input');
        inp.type = "text";
        inp.className = "inline-input";
        inp.dataset.col = col;
        inp.value = value;
        td.appendChild(inp);
    }
    return td;
}

function collectRowValues(tr) {
    const values = {};
    tr.querySelectorAll('input[data-col]').forEach(input => {
        const col = input.dataset.col;
        values[col] = (col === DATE_COL) ? fromInputDate(input.value) : input.value;
    });
    return values;
}

/* ─── 5. ACTIONS ─── */

async function uiEditRow(tr, realIdx, rowData) {
    if (isCreating) return;

    // Désactiver le double-clic pendant l'édition
    tr.ondblclick = null;

    const cells = tr.querySelectorAll('td');
    // columns est déjà sans real_index, cells a columns.length + 1 (Actions)
    columns.forEach((col, i) => {
        const val = rowData[col] ?? "";
        cells[i].innerHTML = '';
        if (col === DATE_COL) {
            cells[i].appendChild(createDateInput(val));
        } else if (COMBO_COLS.includes(col)) {
            cells[i].appendChild(createCombobox(col, val));
        } else {
            const inp = document.createElement('input');
            inp.type = "text";
            inp.className = "inline-input";
            inp.dataset.col = col;
            inp.value = val;
            cells[i].appendChild(inp);
        }
    });

    const saveEdit = async () => {
        const updated = collectRowValues(tr);
        // Vérifier que la date n'est pas vide
        if (updated[DATE_COL] === '') {
            alert('La date est obligatoire.');
            return;
        }
        try {
            const res = await fetch(`/api/account/${currentAccountIndex}/line/${realIdx}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updated)
            });
            if (res.ok) await loadAccountData();
            else console.error("Erreur PUT:", res.status);
        } catch (err) { console.error("Erreur modification:", err); }
    };

    // Bouton Valider dans la cellule Actions (fiable sur tous navigateurs)
    const actionCell = cells[columns.length]; // dernière cellule = Actions
    actionCell.innerHTML = '';
    const btnSave = document.createElement('button');
    btnSave.textContent = '✓';
    btnSave.className = 'btn btn-primary';
    btnSave.style.cssText = 'padding:2px 8px; font-size:12px;';
    btnSave.onclick = saveEdit;
    const btnCancel = document.createElement('button');
    btnCancel.textContent = '✕';
    btnCancel.className = 'btn btn-danger';
    btnCancel.style.cssText = 'padding:2px 8px; font-size:12px; margin-left:4px;';
    btnCancel.onclick = () => loadAccountData();
    actionCell.appendChild(btnSave);
    actionCell.appendChild(btnCancel);

    tr.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') { e.preventDefault(); await saveEdit(); }
            if (e.key === 'Escape') await loadAccountData();
        });
        // keyup en complément pour l'input date (Enter peut être bloqué par le picker)
        if (inp.type === 'date') {
            inp.addEventListener('keyup', async (e) => {
                if (e.key === 'Enter') await saveEdit();
            });
        }
    });
}

async function deleteSelected() {
    if (selectedLineIndex === null) return alert("Sélectionnez une ligne");
    if (!confirm("Supprimer ?")) return;
    const res = await fetch(`/api/account/${currentAccountIndex}/line/${selectedLineIndex}`, { method: 'DELETE' });
    if (res.ok) { selectedLineIndex = null; await loadAccountData(); }
}

function saveChanges() {
    loadAccountData();
    alert("Synchronisation terminée.");
}

async function uiAddRow() {
    if (isCreating) return;
    isCreating = true;

    const tbody = document.getElementById('tableBody');
    const tr = document.createElement('tr');
    tr.className = "editing-row newly-added-row";

    columns.forEach(col => tr.appendChild(createCell(col, "")));

    const actionTd = document.createElement('td');
    tr.appendChild(actionTd);

    const handleKey = async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const newValues = collectRowValues(tr);

            const missing = columns.filter(col =>
                !newValues[col] || newValues[col].toString().trim() === ""
            );

            if (missing.length > 0) {
                alert(`Erreur : Tous les champs sont obligatoires (${missing.join(', ')})`);
                const firstEmpty = tr.querySelector(`input[data-col="${missing[0]}"]`);
                if (firstEmpty) firstEmpty.focus();
                return;
            }

            try {
                const res = await fetch(`/api/account/${currentAccountIndex}/line`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newValues)
                });
                if (res.ok) {
                    isCreating = false;
                    await loadAccountData();
                }
            } catch (err) { console.error("Erreur ajout:", err); }
        }
        if (e.key === 'Escape') {
            isCreating = false;
            tr.remove();
        }
    };

    // FIX : keydown sur chaque input, pas sur le tr
    tbody.prepend(tr);
    tr.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('keydown', handleKey);
    });

    const firstInput = tr.querySelector('input');
    if (firstInput) firstInput.focus();
}
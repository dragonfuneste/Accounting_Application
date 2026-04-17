/**
 * GESTION DÉTAILLÉE D'UN COMPTE - compte.js (Version Complète et Corrigée)
 */

let currentAccountIndex = window.location.pathname.split('/').filter(p => p !== "").pop() || 0;
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
        // --- ÉTAPE 1 : Sauvegarder l'état actuel des filtres ---
        const savedFilters = {};
        document.querySelectorAll('.filter-input').forEach(input => {
            if (input.value.trim() !== "") {
                savedFilters[input.dataset.col] = input.value;
            }
        });

        const res = await fetch(`/api/account/${currentAccountIndex}/data`);
        const data = await res.json();
        cachedRows = data.rows || [];

        if (cachedRows.length > 0) {
            columns = Object.keys(cachedRows[0]);
        } else {
            columns = ['Categorie', 'Classe', 'Date', 'Intitule', 'Type', 'Valeur'];
        }

        // --- ÉTAPE 2 : Redessiner ---
        renderTableHead(columns);
        renderTableBody(cachedRows);

        // --- ÉTAPE 3 : Restaurer les filtres ---
        Object.keys(savedFilters).forEach(col => {
            const input = document.querySelector(`.filter-input[data-col="${col}"]`);
            if (input) {
                input.value = savedFilters[col];
            }
        });
        
        // Si un filtre était actif, on demande au serveur de filtrer la vue
        if (Object.keys(savedFilters).length > 0) {
            // On prend le dernier filtre pour rafraîchir la vue filtrée
            const lastCol = Object.keys(savedFilters).pop();
            triggerServerFilter(lastCol, savedFilters[lastCol]);
        }

    } catch (err) { console.error("Erreur de chargement:", err); }
}

/* ─── 2. RENDU DU TABLEAU ─── */

function renderTableHead(cols) {
    const thead = document.getElementById('tableHead');
    if (!thead) return;

    const filteredCols = cols.filter(c => c !== 'real_index');
    
    // Ligne 1 : Titres
    let html = `<tr>`;
    filteredCols.forEach(col => {
        const state = sortStates[col] || null;
        let icon = (state === 'asc') ? " ↑" : (state === 'desc' ? " ↓" : " ↕");
        html += `<th onclick="handleSort('${col}')" style="cursor:pointer; user-select:none;">
                    ${col}<span class="sort-icon">${icon}</span>
                 </th>`;
    });
    html += `<th>Actions</th></tr>`;
    
    // Ligne 2 : Filtres
    html += `<tr class="filter-row">`;
    filteredCols.forEach(col => {
        html += `<td><input type="text" class="filter-input" data-col="${col}" onkeyup="handleFilter(event)"></td>`;
    });
    html += `<td></td></tr>`;
    
    thead.innerHTML = html;
}

function renderTableBody(rows) {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    isCreating = false;
    tbody.innerHTML = '';

    if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${columns.length + 1}" class="empty-msg">Aucune transaction trouvée.</td></tr>`;
        return;
    }

    rows.forEach((row) => {
        const tr = document.createElement('tr');
        tr.dataset.realIndex = row.real_index; 

        tr.innerHTML = columns
            .filter(col => col !== 'real_index')
            .map(col => {
                const val = row[col] ?? "";
                const isNum = typeof val === 'number';
                const cls = isNum ? (val < 0 ? 'num negative' : 'num positive') : '';
                return `<td class="${cls}">${isNum ? val.toFixed(2) : val}</td>`;
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

/* ─── 3. FILTRAGE ET TRI (SERVER-SIDE) ─── */

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
    const currentState = sortStates[column] || null;
    let nextState = (currentState === null) ? 'asc' : (currentState === 'asc' ? 'desc' : null);
    let apiValue = (nextState === 'asc') ? true : (nextState === 'desc' ? false : null);

    sortStates = { [column]: nextState };

    try {
        await fetch(`/api/account/${currentAccountIndex}/sort`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column: apiValue === null ? null : column, croissant: apiValue })
        });
        await loadAccountData(); 
    } catch (err) { console.error("Erreur tri:", err); }
}

/* ─── 4. ÉDITION ET COMPOSANTS (REMIS À NEUF) ─── */

function toInputDate(val) {
    if (!val) return "";
    const s = String(val).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    const m = s.match(/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/);
    if (m) return `${m[3]}-${m[2]}-${m[1]}`;
    return "";
}

function fromInputDate(val) {
    if (!val) return "";
    const m = val.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) return `${m[3]}/${m[2]}/${m[1]}`;
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
    wrapper.style.cssText = "position:relative; width:100%;";
    const input = document.createElement('input');
    input.type = "text"; input.className = "inline-input";
    input.value = value; input.dataset.col = colName; input.autocomplete = "off";

    const dropdown = document.createElement('ul');
    dropdown.className = "combo-dropdown"; // Défini dans ton CSS

    const showSuggestions = (filter) => {
        const uniqueVals = [...new Set(cachedRows.map(r => r[colName]))].filter(v => v);
        const options = uniqueVals.filter(v => v.toString().toLowerCase().includes(filter.toLowerCase()));
        dropdown.innerHTML = '';
        if (options.length === 0) { dropdown.style.display = 'none'; return; }
        options.forEach(opt => {
            const li = document.createElement('li');
            li.textContent = opt;
            li.onmousedown = () => { input.value = opt; dropdown.style.display = 'none'; };
            dropdown.appendChild(li);
        });
        dropdown.style.display = 'block';
    };

    input.oninput = () => showSuggestions(input.value);
    input.onfocus = () => showSuggestions(input.value);
    input.onblur = () => setTimeout(() => dropdown.style.display = 'none', 150);

    wrapper.appendChild(input); wrapper.appendChild(dropdown);
    return wrapper;
}

function createCell(col, value = "") {
    const td = document.createElement('td');
    if (col === DATE_COL) td.appendChild(createDateInput(value));
    else if (COMBO_COLS.includes(col)) td.appendChild(createCombobox(col, value));
    else {
        const inp = document.createElement('input');
        inp.type = "text"; inp.className = "inline-input";
        inp.dataset.col = col; inp.value = value;
        td.appendChild(inp);
    }
    return td;
}

function collectRowValues(tr) {
    const values = {};
    tr.querySelectorAll('input').forEach(input => {
        const col = input.dataset.col;
        if (col) values[col] = (col === DATE_COL) ? fromInputDate(input.value) : input.value;
    });
    return values;
}

/* ─── 5. ACTIONS ─── */

async function uiEditRow(tr, realIdx, rowData) {
    if (isCreating) return;
    const cells = tr.querySelectorAll('td');
    const filteredCols = columns.filter(c => c !== 'real_index');

    filteredCols.forEach((col, i) => {
        const val = rowData[col] ?? "";
        cells[i].innerHTML = '';
        cells[i].appendChild(col === DATE_COL ? createDateInput(val) : 
                            (COMBO_COLS.includes(col) ? createCombobox(col, val) : 
                            createCell(col, val).firstChild));
    });

    tr.onkeydown = async (e) => {
        if (e.key === 'Enter') {
            const updated = collectRowValues(tr);
            const res = await fetch(`/api/account/${currentAccountIndex}/line/${realIdx}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updated)
            });
            if (res.ok) await loadAccountData();
        }
        if (e.key === 'Escape') await loadAccountData();
    };
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
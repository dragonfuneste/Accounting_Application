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
        tbody.innerHTML = '';

        rows.forEach((row) => {
            const tr = document.createElement('tr');
            tr.dataset.realIndex = row.real_index; 

            tr.innerHTML = columns
                .filter(col => col !== 'real_index')
                .map(col => {
                    const val = row[col] ?? "";
                    // On affiche la valeur brute envoyée par l'API (qui sera ISO grâce à Python)
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
    const currentState = sortStates[column] || 'desc'; // Par défaut on vient de desc pour passer à asc
    
    // Bascule binaire : si c'était asc, ça devient desc, sinon ça devient asc
    let nextState = (currentState === 'asc') ? 'desc' : 'asc';
    let apiValue = (nextState === 'asc'); // Devient true ou false (plus de null)

    // On met à jour l'icône
    sortStates = { [column]: nextState };

    try {
        await fetch(`/api/account/${currentAccountIndex}/sort`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                column: column, 
                croissant: apiValue 
            })
        });
        await loadAccountData(); 
    } catch (err) { console.error("Erreur tri:", err); }
}

/* ─── 4. ÉDITION ET COMPOSANTS (REMIS À NEUF) ─── */

function toInputDate(val) {
    if (!val) return "";
    const s = String(val).trim();
    // Si c'est déjà de l'ISO (YYYY-MM-DD), on renvoie tel quel
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    // Si c'est du FR (DD/MM/YYYY), on le convertit en ISO pour l'input date
    const m = s.match(/^(\d{2})[\/\-](\d{2})[\/\-](\d{4})$/);
    if (m) return `${m[3]}-${m[2]}-${m[1]}`;
    return "";
}

function fromInputDate(val) {
    // ICI : On ne veut plus de conversion vers le FR. 
    // On veut que la fonction renvoie de l'ISO quoi qu'il arrive.
    const s = String(val).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s; // C'est déjà bon
    
    // Si on reçoit du FR, on le transforme en ISO pour l'affichage
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
    wrapper.className = "combo-wrapper"; // Pour le CSS
    
    const input = document.createElement('input');
    input.type = "text"; 
    input.className = "inline-input";
    input.value = value; 
    input.dataset.col = colName; 
    input.autocomplete = "off";

    const dropdown = document.createElement('ul');
    dropdown.className = "combo-dropdown";

    const showSuggestions = (filter) => {
        // 1. Extraire les valeurs uniques de la colonne demandée
        const uniqueVals = [...new Set(cachedRows.map(r => r[colName]))]
            .filter(v => v !== null && v !== undefined && v !== "");

        // 2. Filtrer selon la saisie
        const options = uniqueVals.filter(v => 
            v.toString().toLowerCase().includes(filter.toLowerCase())
        );

        dropdown.innerHTML = '';
        
        if (options.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        // 3. Créer les éléments de liste
        options.forEach(opt => {
            const li = document.createElement('li');
            li.textContent = opt;
            // Utiliser mousedown plutôt que click (évite le conflit avec le blur de l'input)
            li.onmousedown = (e) => {
                e.preventDefault(); // Empêche l'input de perdre le focus avant la sélection
                input.value = opt;
                dropdown.style.display = 'none';
            };
            dropdown.appendChild(li);
        });

        dropdown.style.display = 'block';
    };

    input.oninput = () => showSuggestions(input.value);
    input.onfocus = () => showSuggestions(input.value);
    input.onblur = () => {
        // Petit délai pour laisser le temps au mousedown de s'exécuter
        setTimeout(() => dropdown.style.display = 'none', 200);
    };

    wrapper.appendChild(input);
    wrapper.appendChild(dropdown);
    return wrapper;
}

function createCell(col, value = "") {
    const td = document.createElement('td');
    
    if (col === DATE_COL) {
        td.appendChild(createDateInput(value));
    } 
    else if (COMBO_COLS.includes(col)) {
        // Cette fonction crée déjà le wrapper + input + dropdown
        td.appendChild(createCombobox(col, value));
    } 
    else {
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

async function uiAddRow() {
    if (isCreating) return;
    isCreating = true;

    const tbody = document.getElementById('tableBody');
    const tr = document.createElement('tr');
    tr.className = "editing-row newly-added-row";

    // On récupère les colonnes (exclu real_index)
    const filteredCols = columns.filter(c => c !== 'real_index');
    
    // On génère les cellules (cela inclut les Combobox via createCell)
    filteredCols.forEach(col => {
        tr.appendChild(createCell(col, ""));
    });

    // Ajout de la cellule pour la colonne "Actions"
    const actionTd = document.createElement('td');
    tr.appendChild(actionTd);

    // --- GESTION DES TOUCHES ---
    tr.onkeydown = async (e) => {
        if (e.key === 'Enter') {
            const newValues = collectRowValues(tr);
            
            // --- VALIDATION STRICTE ---
            // On vérifie que CHAQUE colonne a une valeur non vide
            const missing = filteredCols.filter(col => {
                return !newValues[col] || newValues[col].toString().trim() === "";
            });
            
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
            } catch (err) {
                console.error("Erreur ajout:", err);
            }
        }
        if (e.key === 'Escape') {
            isCreating = false;
            tr.remove();
        }
    };

    // On insère d'abord dans le DOM
    tbody.prepend(tr);
    
    // Puis on donne le focus (ce qui activera proprement les écouteurs de la combobox)
    const firstInput = tr.querySelector('input');
    if (firstInput) firstInput.focus();
}
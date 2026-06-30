import React, { useState, useEffect, useCallback, useRef } from 'react';
import './TableauOnglet.css';

const API = 'http://127.0.0.1:5000/api';
const COLS = ['date', 'intitule', 'categorie', 'classe', 'est_revenu', 'valeur'];
const COL_LABELS = { date: 'Date', intitule: 'Intitulé', categorie: 'Catégorie', classe: 'Classe', est_revenu: 'Type', valeur: 'Valeur' };
const DROPDOWN_COLS = new Set(['categorie', 'classe', 'est_revenu']);

const EMPTY_ROW = { date: '', intitule: '', categorie: '', classe: '', est_revenu: 1, valeur: '' };

function fmt(v) {
  return Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function ComboCell({ col, value, onChange, options }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  if (col === 'est_revenu') {
    return (
      <select
        className="cell-select"
        value={value}
        onChange={e => onChange(parseInt(e.target.value))}
        autoFocus
      >
        <option value={1}>Revenu</option>
        <option value={0}>Dépense</option>
      </select>
    );
  }

  const filtered = options.filter(o => o.toLowerCase().includes(String(value).toLowerCase()));

  return (
    <div className="combo-wrap" ref={ref}>
      <input
        className="cell-input"
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        autoFocus
      />
      {open && filtered.length > 0 && (
        <div className="combo-dropdown">
          {filtered.map(o => (
            <div key={o} className="combo-option" onMouseDown={() => { onChange(o); setOpen(false); }}>
              {o}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EditableRow({ row, options, onSave, onCancel, isNew }) {
  const [form, setForm] = useState({ ...row });
  const rowRef = useRef(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleKey = e => {
    if (e.key === 'Enter') onSave(form);
    if (e.key === 'Escape') onCancel();
  };

  return (
    <tr className="row-editing" ref={rowRef} onKeyDown={handleKey}>
      {COLS.map(col => (
        <td key={col}>
          {DROPDOWN_COLS.has(col) ? (
            <ComboCell
              col={col}
              value={form[col]}
              onChange={v => set(col, v)}
              options={col === 'est_revenu' ? [] : (options[col === 'categorie' ? 'categories' : 'classes'] || [])}
            />
          ) : col === 'valeur' ? (
            <input
              className="cell-input"
              type="number" step="0.01" min="0"
              value={form[col]}
              onChange={e => set(col, e.target.value)}
            />
          ) : (
            <input
              className="cell-input"
              type={col === 'date' ? 'date' : 'text'}
              value={col === 'date' && form[col] ? form[col].slice(0, 10) : form[col]}
              onChange={e => set(col, e.target.value)}
              autoFocus={col === 'date'}
            />
          )}
        </td>
      ))}
      <td className="action-cell">
        <button className="btn-save" onClick={() => onSave(form)} title="Valider (Entrée)">✓</button>
        <button className="btn-cancel" onClick={onCancel} title="Annuler (Échap)">✕</button>
      </td>
    </tr>
  );
}

export default function TableauOnglet({ compte }) {
  const [rows, setRows] = useState([]);
  const [options, setOptions] = useState({ categories: [], classes: [] });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState(null); // 'asc' | 'desc' | null
  const [editingId, setEditingId] = useState(null);
  const [addingRow, setAddingRow] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/comptes/${compte.id}/transactions`).then(r => r.json()),
      fetch(`${API}/comptes/${compte.id}/transactions/options`).then(r => r.json()),
    ]).then(([txs, opts]) => {
      setRows(Array.isArray(txs) ? txs : []);
      setOptions(opts);
      setLoading(false);
    }).catch(() => { setError('Erreur de chargement'); setLoading(false); });
  }, [compte.id]);

  useEffect(() => { load(); }, [load]);

  // ── Sort ──────────────────────────────────────────────────────────
  const handleSort = col => {
    if (sortCol !== col) { setSortCol(col); setSortDir('asc'); return; }
    if (sortDir === 'asc') { setSortDir('desc'); return; }
    if (sortDir === 'desc') { setSortCol(null); setSortDir(null); }
  };

  const sortIcon = col => {
    if (sortCol !== col) return <span className="sort-icon neutral">⇅</span>;
    return sortDir === 'asc'
      ? <span className="sort-icon active">↑</span>
      : <span className="sort-icon active">↓</span>;
  };

  // ── Filter + sort ─────────────────────────────────────────────────
  let displayed = rows.filter(r =>
    !search || COLS.some(c => String(r[c] ?? '').toLowerCase().includes(search.toLowerCase()))
  );

  if (sortCol && sortDir) {
    displayed = [...displayed].sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      const cmp = String(av ?? '').localeCompare(String(bv ?? ''), 'fr', { numeric: true });
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }

  // ── Add ───────────────────────────────────────────────────────────
  const handleAdd = async form => {
    setError('');
    try {
      const res = await fetch(`${API}/comptes/${compte.id}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: form.date, intitule: form.intitule, categorie: form.categorie,
          classe: form.classe, est_revenu: form.est_revenu, valeur: Number(form.valeur)
        })
      });
      if (!res.ok) { const b = await res.json(); setError(b.error || 'Erreur'); return; }
      setAddingRow(false);
      load();
    } catch { setError('Impossible de joindre le serveur'); }
  };

  // ── Edit ──────────────────────────────────────────────────────────
  const handleEdit = async form => {
    setError('');
    try {
      const res = await fetch(`${API}/comptes/${compte.id}/transactions/${form.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: form.date, intitule: form.intitule, categorie: form.categorie,
          classe: form.classe, est_revenu: form.est_revenu, valeur: Number(form.valeur)
        })
      });
      if (!res.ok) { const b = await res.json(); setError(b.error || 'Erreur'); return; }
      setEditingId(null);
      load();
    } catch { setError('Impossible de joindre le serveur'); }
  };

  // ── Delete ────────────────────────────────────────────────────────
  const handleDelete = async () => {
    if (!selectedId) return;
    try {
      await fetch(`${API}/comptes/${compte.id}/transactions/${selectedId}`, { method: 'DELETE' });
      setSelectedId(null);
      load();
    } catch { setError('Erreur suppression'); }
  };

  // ── Keyboard on table ─────────────────────────────────────────────
  const handleTableKey = e => {
    if (e.key === 'Delete' && selectedId && !editingId) handleDelete();
  };

  return (
    <div className="tableau-wrap" onKeyDown={handleTableKey} tabIndex={-1}>

      {/* Toolbar */}
      <div className="tableau-toolbar">
        <input
          className="search-input"
          placeholder="🔍 Rechercher dans toutes les colonnes…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="toolbar-actions">
          <button className="btn-add-tx" onClick={() => { setAddingRow(true); setEditingId(null); }}>
            + Ajouter
          </button>
          <button
            className="btn-del-tx"
            onClick={handleDelete}
            disabled={!selectedId || !!editingId}
          >
            🗑 Supprimer
          </button>
        </div>
      </div>

      {error && <p className="tx-error">{error}</p>}

      {/* Table */}
      <div className="tableau-scroll">
        {loading ? (
          <div className="tx-loading">Chargement…</div>
        ) : (
          <table className="tx-table">
            <thead>
              <tr>
                {COLS.map(col => (
                  <th key={col} onClick={() => handleSort(col)} className="sortable-th">
                    {COL_LABELS[col]} {sortIcon(col)}
                  </th>
                ))}
                <th className="action-th" />
              </tr>
            </thead>
            <tbody>
              {/* Ligne d'ajout */}
              {addingRow && (
                <EditableRow
                  row={{ ...EMPTY_ROW, date: new Date().toISOString().slice(0, 10) }}
                  options={options}
                  onSave={handleAdd}
                  onCancel={() => setAddingRow(false)}
                  isNew
                />
              )}
              {displayed.length === 0 && !addingRow && (
                <tr><td colSpan={7} className="tx-empty">Aucune transaction</td></tr>
              )}
              {displayed.map(row => (
                editingId === row.id ? (
                  <EditableRow
                    key={row.id}
                    row={row}
                    options={options}
                    onSave={handleEdit}
                    onCancel={() => setEditingId(null)}
                  />
                ) : (
                  <tr
                    key={row.id}
                    className={`tx-row ${selectedId === row.id ? 'selected' : ''} ${row.est_revenu ? 'is-rev' : 'is-dep'}`}
                    onClick={() => setSelectedId(row.id)}
                    onDoubleClick={() => { setEditingId(row.id); setAddingRow(false); }}
                  >
                    <td>{row.date}</td>
                    <td>{row.intitule}</td>
                    <td><span className="tag">{row.categorie}</span></td>
                    <td>{row.classe}</td>
                    <td>
                      <span className={`type-badge ${row.est_revenu ? 'rev' : 'dep'}`}>
                        {row.est_revenu ? 'Revenu' : 'Dépense'}
                      </span>
                    </td>
                    <td className={`val-cell ${row.est_revenu ? 'rev' : 'dep'}`}>
                      {row.est_revenu ? '+' : '−'}{fmt(row.valeur)} {compte.devise}
                    </td>
                    <td className="action-cell" />
                  </tr>
                )
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="tableau-footer">
        {displayed.length} transaction{displayed.length > 1 ? 's' : ''}
        {search ? ` (filtré sur "${search}")` : ''}
      </div>
    </div>
  );
}
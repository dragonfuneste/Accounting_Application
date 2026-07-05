import React, { useState, useEffect, useCallback } from 'react';
import './ProjetOnglet.css';

const API = 'http://127.0.0.1:5000/api';

function fmt(n) {
  return Number(n || 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function daysLeft(dateStr) {
  if (!dateStr) return null;
  const d = Math.ceil((new Date(dateStr) - new Date()) / 86400000);
  return d;
}

function EtatBadge({ etat }) {
  const map = {
    'Terminé':       'badge-termine',
    'En cours':      'badge-encours',
    'non commencé':  'badge-noncommence',
    'Annulé':        'badge-annule',
  };
  return <span className={`etat-badge ${map[etat] || ''}`}>{etat}</span>;
}

function ProgressBar({ pct, color }) {
  const c = color || (pct >= 100 ? '#34D399' : pct >= 50 ? '#60A5FA' : '#F97316');
  return (
    <div className="prog-track">
      <div className="prog-fill" style={{ width: `${Math.min(100, pct)}%`, background: c }} />
    </div>
  );
}

/* ── Modal générique ──────────────────────────────── */
function Modal({ title, onClose, children, danger }) {
  return (
    <div className="proj-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className={`proj-modal ${danger ? 'danger' : ''}`}>
        <div className="proj-modal-header">
          <h3>{title}</h3>
          <button className="proj-modal-close" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

/* ── Formulaire projet ────────────────────────────── */
function ProjetForm({ initial, onSave, onClose }) {
  const [form, setForm] = useState({
    nom_projet: '', Emoji_logo_projet: '📁', objectif: '',
    priorite: 1, date_fin: '', ...initial
  });
  const s = (k, v) => setForm(f => ({ ...f, [k]: v }));

  return (
    <>
      <div className="proj-modal-body">
        <div className="form-row2">
          <label><span>Emoji</span>
            <input value={form.Emoji_logo_projet} onChange={e => s('Emoji_logo_projet', e.target.value)}
                   style={{ width: 60, textAlign: 'center', fontSize: '1.2rem' }} /></label>
          <label style={{ flex: 1 }}><span>Nom du projet</span>
            <input value={form.nom_projet} onChange={e => s('nom_projet', e.target.value)}
                   placeholder="ex: Voyage au Japon" autoFocus /></label>
        </div>
        <label><span>Objectif</span>
          <textarea value={form.objectif} onChange={e => s('objectif', e.target.value)}
                    rows={2} placeholder="Description de l'objectif…" /></label>
        <div className="form-row2">
          <label><span>Priorité (1 = haute)</span>
            <input type="number" min={1} max={10} value={form.priorite}
                   onChange={e => s('priorite', Number(e.target.value))} /></label>
          <label><span>Date cible</span>
            <input type="date" value={form.date_fin || ''}
                   onChange={e => s('date_fin', e.target.value)} /></label>
        </div>
      </div>
      <div className="proj-modal-footer">
        <button className="btn-secondary" onClick={onClose}>Annuler</button>
        <button className="btn-primary" onClick={() => onSave(form)}>Enregistrer</button>
      </div>
    </>
  );
}

/* ── Formulaire étape ─────────────────────────────── */
function EtapeForm({ initial, onSave, onClose }) {
  const ETATS = ['non commencé', 'En cours', 'Terminé', 'Annulé'];
  const [form, setForm] = useState({
    nom_etape: '', objectif: '', cible: '', date_fin: '',
    etat: 'non commencé', priorite: 1, ...initial
  });
  const s = (k, v) => setForm(f => ({ ...f, [k]: v }));

  return (
    <>
      <div className="proj-modal-body">
        <label><span>Nom de l'étape</span>
          <input value={form.nom_etape} onChange={e => s('nom_etape', e.target.value)} autoFocus /></label>
        <label><span>Objectif</span>
          <textarea value={form.objectif} onChange={e => s('objectif', e.target.value)} rows={2} /></label>
        <div className="form-row2">
          <label><span>Cible (€)</span>
            <input type="number" min={0} step={0.01} value={form.cible}
                   onChange={e => s('cible', e.target.value)} /></label>
          <label><span>Date limite</span>
            <input type="date" value={form.date_fin || ''}
                   onChange={e => s('date_fin', e.target.value)} /></label>
        </div>
        <div className="form-row2">
          <label><span>État</span>
            <select value={form.etat} onChange={e => s('etat', e.target.value)}>
              {ETATS.map(et => <option key={et}>{et}</option>)}
            </select></label>
          <label><span>Priorité</span>
            <input type="number" min={1} max={10} value={form.priorite}
                   onChange={e => s('priorite', Number(e.target.value))} /></label>
        </div>
      </div>
      <div className="proj-modal-footer">
        <button className="btn-secondary" onClick={onClose}>Annuler</button>
        <button className="btn-primary" onClick={() => onSave(form)}>Enregistrer</button>
      </div>
    </>
  );
}

/* ── Modal liaison transaction ────────────────────── */
function TxLinkModal({ etape, projetId, onClose, onLinked }) {
  const [query, setQuery]     = useState('');
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [pct, setPct]           = useState(100);
  const [dispo, setDispo]       = useState(null);
  const [error, setError]       = useState('');

  // Suggestions depuis les keywords de l'étape
  useEffect(() => {
    if (etape.keywords?.length) {
      const kws = etape.keywords.map(k => `kw=${encodeURIComponent(k)}`).join('&');
      fetch(`${API}/projets/search_transactions?${kws}`)
        .then(r => r.json()).then(setResults).catch(() => {});
    }
  }, [etape.keywords]);

  const search = () => {
    if (!query.trim()) return;
    fetch(`${API}/projets/search_transactions?kw=${encodeURIComponent(query)}`)
      .then(r => r.json()).then(setResults).catch(() => {});
  };

  const selectTx = tx => {
    setSelected(tx);
    fetch(`${API}/projets/tx/${tx.id}/disponibilite`)
      .then(r => r.json()).then(d => {
        setDispo(d);
        setPct(Math.min(100, d.restant));
      });
  };

  const link = async () => {
    if (!selected) return;
    const res = await fetch(`${API}/projets/${projetId}/etapes/${etape.id}/transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tx_id: selected.id, pourcentage: pct }),
    }).then(r => r.json());
    if (res.error) { setError(res.error); return; }
    onLinked();
    onClose();
  };

  return (
    <Modal title={`Lier une transaction — ${etape.nom_etape}`} onClose={onClose}>
      <div className="proj-modal-body">
        {/* Barre de recherche */}
        <div className="tx-search-bar">
          <input value={query} onChange={e => setQuery(e.target.value)}
                 onKeyDown={e => e.key === 'Enter' && search()}
                 placeholder="Rechercher par intitulé, classe, catégorie…" />
          <button className="btn-primary" onClick={search}>Rechercher</button>
        </div>

        {/* Keywords suggérés */}
        {etape.keywords?.length > 0 && (
          <div className="tx-keywords">
            <span className="tx-kw-label">Suggestions :</span>
            {etape.keywords.map(kw => (
              <button key={kw} className="tx-kw-chip"
                      onClick={() => { setQuery(kw); search(); }}>{kw}</button>
            ))}
          </div>
        )}

        {/* Résultats */}
        <div className="tx-results">
          {results.map(tx => (
            <div key={tx.id}
                 className={`tx-result-row ${selected?.id === tx.id ? 'selected' : ''}`}
                 onClick={() => selectTx(tx)}>
              <span className="tx-r-date">{tx.date}</span>
              <span className="tx-r-intitule">{tx.intitule}</span>
              <span className="tx-r-cat">{tx.categorie}</span>
              <span className={`tx-r-val ${tx.est_revenu ? 'rev' : 'dep'}`}>
                {tx.est_revenu ? '+' : '−'}{fmt(tx.valeur)}
              </span>
            </div>
          ))}
          {results.length === 0 && <p className="tx-empty">Aucun résultat</p>}
        </div>

        {/* Pourcentage */}
        {selected && dispo && (
          <div className="tx-pct-section">
            <div className="tx-dispo-info">
              <span>Utilisé : <strong>{dispo.utilise}%</strong></span>
              <span className={dispo.restant <= 0 ? 'dispo-zero' : ''}>
                Disponible : <strong>{dispo.restant}%</strong>
              </span>
            </div>
            {dispo.restant > 0 ? (
              <label className="tx-pct-label">
                <span>% à lier à cette étape</span>
                <div className="tx-pct-row">
                  <input type="range" min={1} max={dispo.restant} value={pct}
                         onChange={e => setPct(Number(e.target.value))} />
                  <span className="tx-pct-val">{pct}%</span>
                </div>
              </label>
            ) : (
              <p className="dispo-zero-msg">⚠ Cette transaction est déjà liée à 100%</p>
            )}
          </div>
        )}
        {error && <p className="proj-error">{error}</p>}
      </div>
      <div className="proj-modal-footer">
        <button className="btn-secondary" onClick={onClose}>Annuler</button>
        <button className="btn-primary" onClick={link}
                disabled={!selected || !dispo || dispo.restant <= 0}>
          Lier ({pct}%)
        </button>
      </div>
    </Modal>
  );
}

/* ── Bloc étape ───────────────────────────────────── */
function EtapeBloc({ etape, projetId, onUpdated, onDelete }) {
  const [showTxModal,   setShowTxModal]   = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDelConfirm, setShowDelConfirm] = useState(false);

  const pct    = etape.progression ?? 0;
  const retard = etape.est_en_retard;
  const fini   = etape.etat === 'Terminé';
  const annule = etape.etat === 'Annulé';
  const days   = daysLeft(etape.date_fin);

  const handleDoubleClick = () => {
    if (!fini && !annule) setShowTxModal(true);
  };

  const saveEdit = async form => {
    await fetch(`${API}/projets/${projetId}/etapes/${etape.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    setShowEditModal(false);
    onUpdated();
  };

  const unlinkTx = async txId => {
    await fetch(`${API}/projets/${projetId}/etapes/${etape.id}/transactions/${txId}`, {
      method: 'DELETE'
    });
    onUpdated();
  };

  return (
    <div
      className={`etape-bloc ${retard ? 'retard' : ''} ${fini ? 'termine' : ''} ${annule ? 'annule' : ''}`}
      onDoubleClick={handleDoubleClick}
      title={!fini && !annule ? 'Double-clic pour lier des transactions' : ''}
    >
      <div className="etape-header">
        <div className="etape-title-row">
          <span className="etape-num">#{etape.priorite}</span>
          <strong className="etape-nom">{etape.nom_etape}</strong>
          <EtatBadge etat={etape.etat} />
          {retard && <span className="alerte-rouge">⚠ En retard</span>}
        </div>
        <div className="etape-actions">
          <button className="btn-sm" onClick={e => { e.stopPropagation(); setShowEditModal(true); }}>✏</button>
          <button className="btn-sm danger" onClick={e => { e.stopPropagation(); setShowDelConfirm(true); }}>🗑</button>
        </div>
      </div>

      {etape.objectif && <p className="etape-objectif">{etape.objectif}</p>}

      <div className="etape-stats">
        <span>{fmt(etape.montant_realise)} / {fmt(etape.cible)}</span>
        <span className="etape-pct">{pct}%</span>
        {days !== null && (
          <span className={`etape-days ${days < 0 ? 'late' : days < 30 ? 'soon' : ''}`}>
            {days < 0 ? `${Math.abs(days)}j de retard` : `${days}j restants`}
          </span>
        )}
      </div>
      <ProgressBar pct={pct} />

      {/* Transactions liées */}
      {etape.transactions?.length > 0 && (
        <div className="etape-txs">
          {etape.transactions.map(t => (
            <div key={t.id_transaction} className="etape-tx-chip">
              <span>Tx #{t.id_transaction} — {t.pourcentage_lie}%</span>
              <button className="chip-del" onClick={() => unlinkTx(t.id_transaction)}>✕</button>
            </div>
          ))}
        </div>
      )}

      {!fini && !annule && (
        <button className="btn-link-tx" onClick={e => { e.stopPropagation(); setShowTxModal(true); }}>
          + Lier une transaction
        </button>
      )}

      {showEditModal && (
        <Modal title="Modifier l'étape" onClose={() => setShowEditModal(false)}>
          <EtapeForm initial={{ nom_etape: etape.nom_etape, objectif: etape.objectif,
            cible: etape.cible, date_fin: etape.date_fin,
            etat: etape.etat, priorite: etape.priorite }}
            onSave={saveEdit} onClose={() => setShowEditModal(false)} />
        </Modal>
      )}

      {showDelConfirm && (
        <Modal title="Supprimer l'étape" onClose={() => setShowDelConfirm(false)} danger>
          <div className="proj-modal-body">
            <p>Supprimer <strong>{etape.nom_etape}</strong> ? Cette action est irréversible.</p>
          </div>
          <div className="proj-modal-footer">
            <button className="btn-secondary" onClick={() => setShowDelConfirm(false)}>Annuler</button>
            <button className="btn-danger" onClick={() => { onDelete(etape.id); setShowDelConfirm(false); }}>
              Supprimer
            </button>
          </div>
        </Modal>
      )}

      {showTxModal && (
        <TxLinkModal etape={etape} projetId={projetId}
          onClose={() => setShowTxModal(false)} onLinked={onUpdated} />
      )}
    </div>
  );
}

/* ── Vue détail projet ────────────────────────────── */
function ProjetDetail({ projet, onBack, onUpdated }) {
  const [showAddEtape, setShowAddEtape] = useState(false);

  const addEtape = async form => {
    await fetch(`${API}/projets/${projet.id}/etapes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    setShowAddEtape(false);
    onUpdated();
  };

  const deleteEtape = async eid => {
    await fetch(`${API}/projets/${projet.id}/etapes/${eid}`, { method: 'DELETE' });
    onUpdated();
  };

  const etapesSorted = [...(projet.etapes || [])].sort((a, b) => a.priorite - b.priorite);
  const termine = projet.etat_calcule === 'Terminé';
  const retard  = projet.est_en_retard && !termine;
  const days    = daysLeft(projet.date_fin);

  return (
    <div className="projet-detail">
      <div className="detail-topbar">
        <button className="btn-back" onClick={onBack}>← Projets</button>
        <div className="detail-title">
          <span className="detail-emoji">{projet.Emoji_logo_projet}</span>
          <h2>{projet.nom_projet}</h2>
          <EtatBadge etat={projet.etat_calcule} />
          {retard && <span className="alerte-rouge">⚠ Projet en retard</span>}
          {termine && <span className="tampon-succes">✓ RÉUSSI</span>}
        </div>
      </div>

      <p className="detail-objectif">{projet.objectif}</p>

      <div className="detail-stats-bar">
        <div className="ds-item">
          <span>Budget total</span>
          <strong>{fmt(projet.cible_totale)} €</strong>
        </div>
        <div className="ds-item">
          <span>Réalisé</span>
          <strong>{fmt(projet.montant_realise)} €</strong>
        </div>
        <div className="ds-item">
          <span>Progression</span>
          <strong>{projet.progression}%</strong>
        </div>
        {days !== null && (
          <div className={`ds-item ${days < 0 ? 'late' : days < 30 ? 'soon' : ''}`}>
            <span>Échéance</span>
            <strong>{days < 0 ? `${Math.abs(days)}j dépassé` : `${days}j restants`}</strong>
          </div>
        )}
      </div>
      <ProgressBar pct={projet.progression} />

      <div className="etapes-header">
        <h3>Étapes ({etapesSorted.length})</h3>
        <button className="btn-primary" onClick={() => setShowAddEtape(true)}>+ Ajouter une étape</button>
      </div>

      <div className="etapes-grid">
        {etapesSorted.map(etape => (
          <EtapeBloc
            key={etape.id}
            etape={etape}
            projetId={projet.id}
            onUpdated={onUpdated}
            onDelete={deleteEtape}
          />
        ))}
        {etapesSorted.length === 0 && (
          <p className="no-etapes">Aucune étape — cliquez sur "+ Ajouter une étape"</p>
        )}
      </div>

      {showAddEtape && (
        <Modal title="Nouvelle étape" onClose={() => setShowAddEtape(false)}>
          <EtapeForm onSave={addEtape} onClose={() => setShowAddEtape(false)} />
        </Modal>
      )}
    </div>
  );
}

/* ── Carte projet (liste) ─────────────────────────── */
function ProjetCard({ projet, onClick, onEdit, onDelete }) {
  const pct     = projet.progression ?? 0;
  const termine = projet.etat_calcule === 'Terminé';
  const retard  = projet.est_en_retard && !termine;
  const days    = daysLeft(projet.date_fin);

  return (
    <div className={`projet-card ${termine ? 'card-termine' : ''} ${retard ? 'card-retard' : ''}`}
         onClick={onClick}>
      {termine && <div className="tampon-succes-card">✓ RÉUSSI</div>}
      {retard  && !termine && <div className="alerte-card">⚠ En retard</div>}

      <div className="card-header">
        <span className="card-emoji">{projet.Emoji_logo_projet}</span>
        <div className="card-title">
          <strong>{projet.nom_projet}</strong>
          <EtatBadge etat={projet.etat_calcule} />
        </div>
        <div className="card-menu">
          <button className="btn-sm" onClick={e => { e.stopPropagation(); onEdit(); }}>✏</button>
          <button className="btn-sm danger" onClick={e => { e.stopPropagation(); onDelete(); }}>🗑</button>
        </div>
      </div>

      <p className="card-objectif">{projet.objectif}</p>

      <div className="card-stats">
        <span>{fmt(projet.montant_realise)} / {fmt(projet.cible_totale)} €</span>
        <span>{pct}%</span>
      </div>
      <ProgressBar pct={pct} />

      <div className="card-footer">
        <span className="card-priority">Priorité #{projet.priorite}</span>
        {days !== null && (
          <span className={`card-days ${days < 0 ? 'late' : days < 30 ? 'soon' : ''}`}>
            {days < 0 ? `${Math.abs(days)}j dépassé` : `${days}j`}
          </span>
        )}
      </div>
    </div>
  );
}

/* ── Composant principal ──────────────────────────── */
export default function ProjetOnglet() {
  const [projets, setProjets]           = useState([]);
  const [loading, setLoading]           = useState(true);
  const [selected, setSelected]         = useState(null); // projet actif en détail
  const [showAdd, setShowAdd]           = useState(false);
  const [editTarget, setEditTarget]     = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const load = useCallback(() => {
    fetch(`${API}/projets`)
      .then(r => r.json())
      .then(d => { setProjets(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  // Resync le projet sélectionné après rechargement
  useEffect(() => {
    if (selected) {
      const updated = projets.find(p => p.id === selected.id);
      if (updated) setSelected(updated);
    }
  }, [projets]);

  const addProjet = async form => {
    await fetch(`${API}/projets`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    setShowAdd(false);
    load();
  };

  const saveEdit = async form => {
    await fetch(`${API}/projets/${editTarget.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    setEditTarget(null);
    load();
  };

  const confirmDelete = async () => {
    await fetch(`${API}/projets/${deleteTarget.id}`, { method: 'DELETE' });
    setDeleteTarget(null);
    if (selected?.id === deleteTarget.id) setSelected(null);
    load();
  };

  // Totaux globaux
  const totalCible    = projets.reduce((s, p) => s + (p.cible_totale || 0), 0);
  const totalRealise  = projets.reduce((s, p) => s + (p.montant_realise || 0), 0);
  const enRetard      = projets.filter(p => p.est_en_retard && p.etat_calcule !== 'Terminé').length;
  const termines      = projets.filter(p => p.etat_calcule === 'Terminé').length;

  if (loading) return <div className="proj-loading">Chargement…</div>;

  // Vue détail
  if (selected) {
    return (
      <ProjetDetail
        projet={selected}
        onBack={() => setSelected(null)}
        onUpdated={() => load()}
      />
    );
  }

  return (
    <div className="projets-wrap">

      {/* Stats globales */}
      <div className="projets-stats-bar">
        <div className="ps-item">
          <span>Projets actifs</span>
          <strong>{projets.filter(p => p.etat_calcule !== 'Terminé').length}</strong>
        </div>
        <div className="ps-item">
          <span>Terminés</span>
          <strong className="rev">{termines}</strong>
        </div>
        <div className={`ps-item ${enRetard > 0 ? 'late' : ''}`}>
          <span>En retard</span>
          <strong className={enRetard > 0 ? 'dep' : ''}>{enRetard}</strong>
        </div>
        <div className="ps-item">
          <span>Budget total</span>
          <strong>{fmt(totalCible)} €</strong>
        </div>
        <div className="ps-item">
          <span>Réalisé</span>
          <strong>{fmt(totalRealise)} €</strong>
        </div>
        <button className="btn-primary ps-add" onClick={() => setShowAdd(true)}>
          + Nouveau projet
        </button>
      </div>

      {/* Grille de projets */}
      {projets.length === 0 ? (
        <div className="no-projets">
          <span className="no-proj-icon">🗂</span>
          <p>Aucun projet — créez votre premier projet !</p>
        </div>
      ) : (
        <div className="projets-grid">
          {projets.map(p => (
            <ProjetCard
              key={p.id}
              projet={p}
              onClick={() => setSelected(p)}
              onEdit={() => setEditTarget(p)}
              onDelete={() => setDeleteTarget(p)}
            />
          ))}
        </div>
      )}

      {/* Modales */}
      {showAdd && (
        <Modal title="Nouveau projet" onClose={() => setShowAdd(false)}>
          <ProjetForm onSave={addProjet} onClose={() => setShowAdd(false)} />
        </Modal>
      )}

      {editTarget && (
        <Modal title={`Modifier — ${editTarget.nom_projet}`} onClose={() => setEditTarget(null)}>
          <ProjetForm initial={editTarget} onSave={saveEdit} onClose={() => setEditTarget(null)} />
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="Supprimer le projet" onClose={() => setDeleteTarget(null)} danger>
          <div className="proj-modal-body">
            <p>Supprimer <strong>{deleteTarget.nom_projet}</strong> et toutes ses étapes ?
               Cette action est irréversible.</p>
          </div>
          <div className="proj-modal-footer">
            <button className="btn-secondary" onClick={() => setDeleteTarget(null)}>Annuler</button>
            <button className="btn-danger" onClick={confirmDelete}>Supprimer</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
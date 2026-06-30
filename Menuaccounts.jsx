import React, { useState, useEffect, useCallback } from 'react';
import './Menuaccounts.css';
import CompteDetail from './CompteDetail';
import CompteOnglets from './CompteOnglets';

const API = 'http://127.0.0.1:5000/api';

function fmt(n, devise = '€') {
  return `${Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${devise}`;
}

function Toast({ msg }) {
  return msg ? <div className="toast show">{msg}</div> : null;
}

function ModalAddCompte({ onClose, onAdd }) {
  const [name, setName] = useState('');
  const [devise, setDevise] = useState('EUR');
  const [error, setError] = useState('');

  const submit = async () => {
    if (!name.trim()) return;
    setError('');
    try {
      const res = await fetch(`${API}/comptes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), devise }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error || `Erreur serveur (${res.status})`);
        return;
      }
      onAdd();
      onClose();
    } catch {
      setError('Impossible de joindre le serveur');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Nouveau compte</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <label>
            <span>Nom du compte</span>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="ex: Compte courant" autoFocus />
          </label>
          <label>
            <span>Devise</span>
            <input value={devise} onChange={e => setDevise(e.target.value)} placeholder="EUR" maxLength={5} />
          </label>
          {error && <p style={{ color: '#DC2626', fontSize: '0.8rem' }}>{error}</p>}
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Annuler</button>
          <button className="btn-primary" onClick={submit}>Créer</button>
        </div>
      </div>
    </div>
  );
}

function ModalEditCompte({ compte, onClose, onSaved }) {
  const [name, setName] = useState(compte.name);
  const [devise, setDevise] = useState(compte.devise);

  const submit = async () => {
    if (!name.trim()) return;
    await fetch(`${API}/comptes/${compte.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim(), devise: devise.trim() }),
    });
    onSaved();
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Modifier « {compte.name} »</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <label>
            <span>Nom du compte</span>
            <input value={name} onChange={e => setName(e.target.value)} autoFocus />
          </label>
          <label>
            <span>Devise</span>
            <input value={devise} onChange={e => setDevise(e.target.value)} maxLength={5} />
          </label>
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Annuler</button>
          <button className="btn-primary" onClick={submit}>Enregistrer</button>
        </div>
      </div>
    </div>
  );
}

function ModalConfirmDelete({ compte, onClose, onDelete }) {
  const confirm = async () => {
    await fetch(`${API}/comptes/${compte.id}`, { method: 'DELETE' });
    onDelete();
    onClose();
  };
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal danger" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Supprimer « {compte.name} » ?</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p className="modal-warn">Cette action est irréversible. Toutes les transactions associées seront supprimées.</p>
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Annuler</button>
          <button className="btn-danger" onClick={confirm}>Supprimer</button>
        </div>
      </div>
    </div>
  );
}

function AccountItem({ compte, isOpen, onToggle, onDeleteClick, onDetailClick, onEditClick, onToggleStatus }) {
  const isActive = compte.status;

  return (
    <div className={`account-item ${isActive ? 'active' : 'inactive'} ${isOpen ? 'open' : ''}`}>
      <div className="account-summary" onClick={onToggle}>
        <div className="account-status-dot" title={isActive ? 'Actif' : 'Inactif'} data-active={isActive} />
        <div className="account-name-wrap">
          <div className="account-name">{compte.name}</div>
        </div>
        <span className="account-devise-badge">{compte.devise}</span>
        <span className={`account-solde ${compte.solde < 0 ? 'negative' : ''}`}>
          {fmt(compte.solde, compte.devise)}
        </span>
        <span className="account-chevron">▶</span>
      </div>

      {isOpen && (
        <div className="account-details">
          <div className="account-stats">
            <div className="stat-box">
              <span className="stat-label">Revenus</span>
              <span className="stat-value rev">{fmt(compte.revenus, compte.devise)}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Dépenses</span>
              <span className="stat-value dep">{fmt(compte.depenses, compte.devise)}</span>
            </div>
            <div className="stat-box full">
              <span className="stat-label">Solde net</span>
              <span className={`stat-value ${compte.solde < 0 ? 'dep' : 'rev'}`}>{fmt(compte.solde, compte.devise)}</span>
            </div>
          </div>

          <div className="account-status-row">
            <label className="status-switch" onClick={e => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={isActive}
                onChange={() => onToggleStatus(compte)}
              />
              <span className="status-switch-track">
                <span className="status-switch-thumb" />
              </span>
              <span className={`status-switch-label ${isActive ? 'on' : 'off'}`}>
                {isActive ? 'Actif' : 'Inactif'}
              </span>
            </label>
            {compte.debut && (
              <span className="account-dates">
                {compte.debut} → {compte.fin}
              </span>
            )}
          </div>

          <div className="account-actions">
            <button className="btn-action" onClick={(e) => { e.stopPropagation(); onDetailClick(compte); }}>
              📊 Détails
            </button>
            <button className="btn-action" onClick={(e) => { e.stopPropagation(); onEditClick(compte); }}>
              ✏️ Modifier
            </button>
            <button className="btn-action danger" onClick={(e) => { e.stopPropagation(); onDeleteClick(compte); }}>
              🗑
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Menuaccounts() {
  const [comptes, setComptes] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [editTarget, setEditTarget] = useState(null);
  const [detailTarget, setDetailTarget] = useState(null);
  const [toast, setToast] = useState('');

  const load = useCallback(() => {
    fetch(`${API}/comptes`)
      .then(r => r.json())
      .then(setComptes)
      .catch(() => setToast('Impossible de joindre le serveur'));
  }, []);

  useEffect(() => { load(); }, [load]);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 2800);
  };

  const handleAdd = () => { load(); showToast('Compte créé ✓'); };
  const handleDelete = () => { load(); showToast('Compte supprimé'); };
  const handleEditSaved = () => { load(); showToast('Compte mis à jour ✓'); };

  const handleToggleStatus = async (compte) => {
    try {
      const res = await fetch(`${API}/comptes/${compte.id}/toggle`, { method: 'PATCH' });
      if (!res.ok) {
        showToast('Erreur lors du changement de statut');
        return;
      }
      const data = await res.json();
      load();
      showToast(data.actif ? `${compte.name} activé ✓` : `${compte.name} désactivé`);
    } catch {
      showToast('Impossible de joindre le serveur');
    }
  };

  const actifs = comptes.filter(c => c.status);
  const selectedCompte = comptes.find(c => c.id === openId) || null;
  const totalRevenu  = actifs.reduce((s, c) => s + c.revenus, 0);
  const totalDepense = actifs.reduce((s, c) => s + c.depenses, 0);
  const totalSolde   = actifs.reduce((s, c) => s + c.solde, 0);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">◈</div>
          <h1>Mes Comptes</h1>
          <div className="sidebar-header-actions">
            <button className="btn-icon" title="Ajouter un compte" onClick={() => setShowAdd(true)}>＋</button>
          </div>
        </div>

        <div className="sidebar-global">
          <div className="sidebar-global-row">
            <span className="sidebar-global-label">Revenus totaux</span>
            <span className="sidebar-global-amount rev">{fmt(totalRevenu)}</span>
          </div>
          <div className="sidebar-global-divider" />
          <div className="sidebar-global-row">
            <span className="sidebar-global-label">Dépenses totales</span>
            <span className="sidebar-global-amount dep">{fmt(totalDepense)}</span>
          </div>
          <div className="sidebar-global-divider" />
          <div className="sidebar-global-row">
            <span className="sidebar-global-label">Solde global</span>
            <span className={`sidebar-global-amount ${totalSolde < 0 ? 'dep' : 'rev'}`}>{fmt(totalSolde)}</span>
          </div>
        </div>

        <div className="account-list">
          {comptes.length === 0 && (
            <div className="empty-list">Aucun compte trouvé</div>
          )}
          {comptes.map(compte => (
            <AccountItem
              key={compte.id}
              compte={compte}
              isOpen={openId === compte.id}
              onToggle={() => {
                const willOpen = openId !== compte.id;
                setOpenId(willOpen ? compte.id : null);
              }}
              onDeleteClick={setDeleteTarget}
              onToggleStatus={handleToggleStatus}
              onDetailClick={setDetailTarget}
              onEditClick={setEditTarget}
            />
          ))}
        </div>
      </aside>

      <main className="main-panel">
        <CompteOnglets compte={selectedCompte} onAccountsChanged={load} />
      </main>

      {showAdd && <ModalAddCompte onClose={() => setShowAdd(false)} onAdd={handleAdd} />}
      {editTarget && <ModalEditCompte compte={editTarget} onClose={() => setEditTarget(null)} onSaved={handleEditSaved} />}
      {deleteTarget && <ModalConfirmDelete compte={deleteTarget} onClose={() => setDeleteTarget(null)} onDelete={handleDelete} />}
      {detailTarget && <CompteDetail compteId={detailTarget.id} onClose={() => setDetailTarget(null)} />}

      <Toast msg={toast} />
    </div>
  );
}
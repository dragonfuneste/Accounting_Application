import React, { useState, useEffect, useCallback } from 'react';
import './Menuaccounts.css';

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

  const submit = async () => {
    if (!name.trim()) return;
    await fetch(`${API}/comptes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim(), devise }),
    });
    onAdd();
    onClose();
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
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Annuler</button>
          <button className="btn-primary" onClick={submit}>Créer</button>
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

function AccountItem({ compte, isOpen, onToggle, onDeleteClick }) {
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
            <span className={`status-badge ${isActive ? 'on' : 'off'}`}>
              {isActive ? '● Actif' : '○ Inactif'}
            </span>
            {compte.debut && (
              <span className="account-dates">
                {compte.debut} → {compte.fin}
              </span>
            )}
          </div>

          <div className="account-actions">
            <button className="btn-action">📊 Détails</button>
            <button className="btn-action">✏️ Modifier</button>
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

  // Stats globales (tous comptes actifs en EUR uniquement pour la somme)
  const actifs = comptes.filter(c => c.status && c.devise === 'EUR');
  const totalRevenu  = actifs.reduce((s, c) => s + c.revenus, 0);
  const totalDepense = actifs.reduce((s, c) => s + c.depenses, 0);
  const totalSolde   = actifs.reduce((s, c) => s + c.solde, 0);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        {/* Header */}
        <div className="sidebar-header">
          <div className="sidebar-logo">◈</div>
          <h1>Mes Comptes</h1>
          <div className="sidebar-header-actions">
            <button className="btn-icon" title="Ajouter un compte" onClick={() => setShowAdd(true)}>＋</button>
          </div>
        </div>

        {/* Global stats */}
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

        {/* Account list */}
        <div className="account-list">
          {comptes.length === 0 && (
            <div className="empty-list">Aucun compte trouvé</div>
          )}
          {comptes.map(compte => (
            <AccountItem
              key={compte.id}
              compte={compte}
              isOpen={openId === compte.id}
              onToggle={() => setOpenId(openId === compte.id ? null : compte.id)}
              onDeleteClick={setDeleteTarget}
            />
          ))}
        </div>
      </aside>

      {/* Main panel */}
      <main className="main-panel">
        <div className="placeholder">
          <div className="placeholder-icon">🗂️</div>
          <h2>Aucun compte sélectionné</h2>
          <p>Sélectionnez un compte dans la liste pour voir les détails et les statistiques.</p>
        </div>
      </main>

      {/* Modals */}
      {showAdd && <ModalAddCompte onClose={() => setShowAdd(false)} onAdd={handleAdd} />}
      {deleteTarget && <ModalConfirmDelete compte={deleteTarget} onClose={() => setDeleteTarget(null)} onDelete={handleDelete} />}

      <Toast msg={toast} />
    </div>
  );
}
import React, { useState, useEffect, useCallback } from 'react';
import './VirementIntercompteOnglet.css';

const API = 'http://127.0.0.1:5000/api';

function fmt(n, devise = '') {
  return `${Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}${devise ? ' ' + devise : ''}`;
}

function CumulChart({ rows }) {
  if (!rows || rows.length === 0) {
    return <div className="chart-empty">Aucun virement entre ces comptes pour le moment</div>;
  }

  const width = 720, height = 260, padL = 56, padR = 20, padT = 16, padB = 30;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;

  const allValues = rows.flatMap(r => [r.depense_cumule, r.revenu_cumule]);
  const maxVal = Math.max(...allValues, 1);
  const minVal = Math.min(...allValues, 0);
  const range = maxVal - minVal || 1;

  const xFor = i => padL + (i / (rows.length - 1 || 1)) * innerW;
  const yFor = v => padT + innerH - ((v - minVal) / range) * innerH;

  const depPoints = rows.map((r, i) => `${xFor(i)},${yFor(r.depense_cumule)}`).join(' ');
  const revPoints = rows.map((r, i) => `${xFor(i)},${yFor(r.revenu_cumule)}`).join(' ');

  const yTicks = 4;
  const yTickVals = Array.from({ length: yTicks + 1 }, (_, i) => minVal + (range / yTicks) * i);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="cumul-chart">
      {/* grid */}
      {yTickVals.map((v, i) => (
        <g key={i}>
          <line x1={padL} y1={yFor(v)} x2={width - padR} y2={yFor(v)} stroke="#EEF2F6" strokeWidth="1" />
          <text x={padL - 8} y={yFor(v) + 4} textAnchor="end" fontSize="10" fill="#94A3B8">{Math.round(v)}</text>
        </g>
      ))}
      {/* x labels (first, mid, last) */}
      {[0, Math.floor(rows.length / 2), rows.length - 1].map(i => (
        <text key={i} x={xFor(i)} y={height - 8} textAnchor="middle" fontSize="9.5" fill="#94A3B8">
          {rows[i].date}
        </text>
      ))}
      <polyline points={depPoints} fill="none" stroke="#F87171" strokeWidth="2.2" />
      <polyline points={revPoints} fill="none" stroke="#34D399" strokeWidth="2.2" />
    </svg>
  );
}

export default function VirementIntercompteOnglet({ compte, onAccountsChanged }) {
  const [comptes, setComptes] = useState([]);
  const [destId, setDestId] = useState(null);

  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 16));
  const [valeurSrc, setValeurSrc] = useState('');
  const [valeurDest, setValeurDest] = useState('');
  const [commentaire, setCommentaire] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Charger tous les comptes (pour la colonne de sélection)
  const loadComptes = useCallback(() => {
    fetch(`${API}/comptes`).then(r => r.json()).then(setComptes).catch(() => {});
  }, []);

  useEffect(() => { loadComptes(); }, [loadComptes]);

  const destCompte = comptes.find(c => c.id === destId);
  const sameDevise = destCompte ? destCompte.devise === compte.devise : true;

  const loadHistory = useCallback(() => {
    if (!destId) { setHistory([]); return; }
    setLoadingHistory(true);
    fetch(`${API}/comptes/${compte.id}/intercompte/${destId}`)
      .then(r => r.json())
      .then(data => setHistory(Array.isArray(data) ? data : []))
      .catch(() => setHistory([]))
      .finally(() => setLoadingHistory(false));
  }, [compte.id, destId]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const resetForm = () => {
    setValeurSrc(''); setValeurDest(''); setCommentaire('');
    setDate(new Date().toISOString().slice(0, 16));
  };

  const submit = async () => {
    setError('');
    if (!destId) { setError('Sélectionnez un compte destinataire.'); return; }
    if (!valeurSrc || Number(valeurSrc) <= 0) { setError('Entrez une valeur valide.'); return; }
    if (!sameDevise && (!valeurDest || Number(valeurDest) <= 0)) {
      setError('Entrez la valeur reçue dans la devise du compte destinataire.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API}/comptes/${compte.id}/virement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dest_id: destId,
          date: date.replace('T', ' '),
          commentaire,
          valeur_src: Number(valeurSrc),
          valeur_dest: sameDevise ? Number(valeurSrc) : Number(valeurDest),
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error || `Erreur serveur (${res.status})`);
        return;
      }
      resetForm();
      loadHistory();
      loadComptes();
      if (onAccountsChanged) onAccountsChanged();
    } catch {
      setError('Impossible de joindre le serveur');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="vi-layout">

      {/* Colonne gauche : sélection du compte destinataire */}
      <aside className="vi-dest-list">
        <h4>Compte destinataire</h4>
        {comptes.filter(c => c.id !== compte.id && c.status).length === 0 && (
          <p className="vi-empty">Aucun autre compte disponible</p>
        )}
        {comptes.filter(c => c.id !== compte.id && c.status).map(c => (
          <button
            key={c.id}
            className={`vi-dest-block ${destId === c.id ? 'selected' : ''}`}
            onClick={() => setDestId(c.id)}
          >
            <span className="vi-dest-name">{c.name}</span>
            <span className="vi-dest-devise">{c.devise}</span>
            <span className={`vi-dest-solde ${c.solde < 0 ? 'neg' : ''}`}>{fmt(c.solde)}</span>
          </button>
        ))}
      </aside>

      {/* Colonne droite : formulaire + graphique + tableau */}
      <div className="vi-main">

        {/* Formulaire */}
        <div className="vi-form-card">
          <h4>Nouveau virement {destCompte ? `vers ${destCompte.name}` : ''}</h4>

          <div className="vi-form-grid">
            <label>
              <span>Date</span>
              <input type="datetime-local" value={date} onChange={e => setDate(e.target.value)} />
            </label>
            <label>
              <span>Valeur envoyée ({compte.devise})</span>
              <input type="number" min="0" step="0.01" value={valeurSrc} onChange={e => setValeurSrc(e.target.value)} placeholder="0.00" />
            </label>
            {!sameDevise && destCompte && (
              <label>
                <span>Valeur reçue ({destCompte.devise})</span>
                <input type="number" min="0" step="0.01" value={valeurDest} onChange={e => setValeurDest(e.target.value)} placeholder="0.00" />
              </label>
            )}
            <label className="vi-comment-label">
              <span>Commentaire</span>
              <input type="text" value={commentaire} onChange={e => setCommentaire(e.target.value)} placeholder="ex: remboursement, épargne…" />
            </label>
          </div>

          {error && <p className="vi-error">{error}</p>}

          <button className="vi-submit-btn" onClick={submit} disabled={submitting || !destId}>
            {submitting ? 'Envoi…' : 'Valider le virement'}
          </button>
        </div>

        {/* Graphique cumulé */}
        <div className="vi-chart-card">
          <h4>Évolution cumulée {destCompte ? `— ${compte.name} ↔ ${destCompte.name}` : ''}</h4>
          <div className="vi-legend">
            <span className="legend-item"><span className="dot dep" /> Dépenses cumulées</span>
            <span className="legend-item"><span className="dot rev" /> Revenus cumulés</span>
          </div>
          {loadingHistory ? (
            <div className="chart-empty">Chargement…</div>
          ) : (
            <CumulChart rows={history} />
          )}
        </div>

        {/* Tableau */}
        <div className="vi-table-card">
          <h4>Détail des virements</h4>
          {history.length === 0 ? (
            <p className="vi-empty">Aucune donnée</p>
          ) : (
            <table className="vi-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Dépense cumulée</th>
                  <th>Revenu cumulé</th>
                  <th>Solde cumulé</th>
                </tr>
              </thead>
              <tbody>
                {history.slice().reverse().map((row, i) => (
                  <tr key={i}>
                    <td>{row.date}</td>
                    <td className="td-dep">{fmt(row.depense_cumule)}</td>
                    <td className="td-rev">{fmt(row.revenu_cumule)}</td>
                    <td className={row.solde_cumule < 0 ? 'td-dep' : 'td-rev'}>{fmt(row.solde_cumule)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      </div>
    </div>
  );
}
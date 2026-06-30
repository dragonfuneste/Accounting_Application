import React, { useState, useEffect } from 'react';
import './CompteDetail.css';

const API = 'http://127.0.0.1:5000/api';

function fmt(n, devise = '€') {
  return `${Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${devise}`;
}

function PctBadge({ value }) {
  if (value === null || value === undefined) {
    return <span className="pct-badge neutral">—</span>;
  }
  const up = value >= 0;
  return (
    <span className={`pct-badge ${up ? 'up' : 'down'}`}>
      {up ? '▲' : '▼'} {Math.abs(value)}%
    </span>
  );
}

function MiniChart({ cumul, devise }) {
  if (!cumul || cumul.length === 0) {
    return <div className="chart-empty">Pas assez de données pour le graphique</div>;
  }

  const width = 600, height = 180, padding = 30;
  const soldes = cumul.map(c => c.solde_cumule);
  const min = Math.min(...soldes, 0);
  const max = Math.max(...soldes, 0);
  const range = max - min || 1;

  const points = cumul.map((c, i) => {
    const x = padding + (i / (cumul.length - 1 || 1)) * (width - padding * 2);
    const y = height - padding - ((c.solde_cumule - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  const zeroY = height - padding - ((0 - min) / range) * (height - padding * 2);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mini-chart">
      <line x1={padding} y1={zeroY} x2={width - padding} y2={zeroY} stroke="#E2E8F0" strokeDasharray="3,3" />
      <polyline points={points} fill="none" stroke="#2DD4BF" strokeWidth="2.5" />
      <polygon
        points={`${padding},${zeroY} ${points} ${width - padding},${zeroY}`}
        fill="rgba(45,212,191,0.08)"
      />
    </svg>
  );
}

export default function CompteDetail({ compteId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/comptes/${compteId}/detail`)
      .then(r => r.json())
      .then(data => { setDetail(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [compteId]);

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="detail-modal" onClick={e => e.stopPropagation()}>
          <div className="detail-loading">Chargement…</div>
        </div>
      </div>
    );
  }

  if (!detail || detail.error) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="detail-modal" onClick={e => e.stopPropagation()}>
          <div className="detail-loading">Erreur de chargement</div>
        </div>
      </div>
    );
  }

  const { name, devise, periode, nb_transactions, transaction_recurrente, comparaison_mois, cumul } = detail;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="detail-modal" onClick={e => e.stopPropagation()}>

        <div className="detail-header">
          <h2>{name}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="detail-body">

          {/* Période */}
          <div className="detail-section">
            <h4>Période</h4>
            {periode.debut ? (
              <p className="detail-period">
                {periode.debut} → {periode.fin}
                <span className="period-days">({periode.nb_jours} jours)</span>
              </p>
            ) : (
              <p className="detail-empty">Aucune transaction enregistrée</p>
            )}
          </div>

          {/* Stats clés */}
          <div className="detail-grid">
            <div className="kpi-box">
              <span className="kpi-label">Transactions totales</span>
              <span className="kpi-value">{nb_transactions}</span>
            </div>
            {transaction_recurrente && (
              <div className="kpi-box">
                <span className="kpi-label">Le plus récurrent</span>
                <span className="kpi-value small">
                  {transaction_recurrente.categorie} / {transaction_recurrente.classe}
                </span>
                <span className="kpi-sub">{transaction_recurrente.occurrences} fois</span>
              </div>
            )}
          </div>

          {/* Comparaison mensuelle */}
          {comparaison_mois && (
            <div className="detail-section">
              <h4>Ce mois-ci vs mois dernier ({comparaison_mois.mois_actuel})</h4>
              <div className="compare-grid">
                <div className="compare-row">
                  <span className="compare-label">Revenus</span>
                  <span className="compare-values">
                    {fmt(comparaison_mois.revenus_actuel, devise)}
                    <span className="compare-prev">vs {fmt(comparaison_mois.revenus_precedent, devise)}</span>
                  </span>
                  <PctBadge value={comparaison_mois.revenus_pct} />
                </div>
                <div className="compare-row">
                  <span className="compare-label">Dépenses</span>
                  <span className="compare-values">
                    {fmt(comparaison_mois.depenses_actuel, devise)}
                    <span className="compare-prev">vs {fmt(comparaison_mois.depenses_precedent, devise)}</span>
                  </span>
                  <PctBadge value={comparaison_mois.depenses_pct} />
                </div>
                <div className="compare-row">
                  <span className="compare-label">Solde net</span>
                  <span className="compare-values"></span>
                  <PctBadge value={comparaison_mois.solde_pct} />
                </div>
              </div>
            </div>
          )}

          {/* Graphique cumulé */}
          <div className="detail-section">
            <h4>Évolution du solde cumulé</h4>
            <MiniChart cumul={cumul} devise={devise} />
          </div>

        </div>
      </div>
    </div>
  );
}
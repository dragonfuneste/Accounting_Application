import React, { useState, useEffect, useCallback } from 'react';
import '../../css/PredictionOnglet.css';

const API = 'http://127.0.0.1:5000/api';

function fmt(n) {
  return Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/* ── Jauge N mois ─────────────────────────────────────────── */
function MonthGauge({ value, max, onChange }) {
  return (
    <div className="gauge-wrap">
      <div className="gauge-header">
        <span className="gauge-label">Mois analysés</span>
        <span className="gauge-value">{value}</span>
      </div>
      <input
        type="range"
        min={1}
        max={max}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="gauge-slider"
      />
      <div className="gauge-bounds">
        <span>1</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

/* ── Barre de probabilité ─────────────────────────────────── */
function ProbaBadge({ pct }) {
  const color = pct >= 75 ? '#059669' : pct >= 50 ? '#F59E0B' : '#94A3B8';
  return (
    <div className="proba-bar-wrap">
      <div className="proba-bar-track">
        <div className="proba-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="proba-pct" style={{ color }}>{pct}%</span>
    </div>
  );
}

/* ── Graphique cumulé prédictif avec hover ────────────────── */
function CumulPredChart({ cumul, soldeActuel, devise }) {
  const [hovered, setHovered] = useState(null);

  if (!cumul || cumul.length === 0) return <div className="pred-empty">Aucune donnée</div>;

  const W = 700, H = 260, PL = 65, PR = 20, PT = 20, PB = 56;
  const iW = W - PL - PR, iH = H - PT - PB;

  // Point de départ = solde actuel
  const allVals = [soldeActuel, ...cumul.map(c => c.cumul)];
  const minV = Math.min(...allVals), maxV = Math.max(...allVals);
  const range = maxV - minV || 1;

  const points = [{ date: 'Actuel', cumul: soldeActuel, intitule: 'Solde actuel', est_revenu: null, valeur: 0, probabilite: 100 }, ...cumul];

  const xFor = i => PL + (i / (points.length - 1)) * iW;
  const yFor = v => PT + iH - ((v - minV) / range) * iH;

  const polyPts = points.map((p, i) => `${xFor(i)},${yFor(p.cumul)}`).join(' ');

  const ticks = 4;
  const yTicks = Array.from({ length: ticks + 1 }, (_, i) => minV + (range / ticks) * i);

  return (
    <div className="cumul-pred-wrap">
      {/* Tooltip */}
      {hovered !== null && (
        <div className="pred-tooltip" style={{
          left: `${Math.min(xFor(hovered) + 12, W - 160)}px`,
          top:  `${Math.max(yFor(points[hovered].cumul) - 80, 0)}px`,
        }}>
          <div className="tooltip-date">{points[hovered].date}</div>
          <div className="tooltip-intitule">{points[hovered].intitule}</div>
          {points[hovered].est_revenu !== null && (
            <div className={`tooltip-val ${points[hovered].est_revenu ? 'rev' : 'dep'}`}>
              {points[hovered].est_revenu ? '+' : '−'}{fmt(points[hovered].valeur)} {devise}
            </div>
          )}
          <div className="tooltip-cumul">Solde → {fmt(points[hovered].cumul)} {devise}</div>
          {points[hovered].est_revenu !== null && (
            <>
              <div className="tooltip-sub">Rev. cumulé : +{fmt(points[hovered].rev_cumul)}</div>
              <div className="tooltip-sub">Dép. cumulée : −{fmt(points[hovered].dep_cumul)}</div>
              <div className={`tooltip-sub ${points[hovered].ecart >= 0 ? 'rev' : 'dep'}`}>
                Écart : {points[hovered].ecart >= 0 ? '+' : ''}{fmt(points[hovered].ecart)}
              </div>
              <div className="tooltip-proba">Probabilité : {points[hovered].probabilite}%</div>
            </>
          )}
        </div>
      )}

      <svg viewBox={`0 0 ${W} ${H}`} className="pred-svg"
           onMouseLeave={() => setHovered(null)}>
        {/* Grille Y */}
        {yTicks.map((v, i) => (
          <g key={i}>
            <line x1={PL} y1={yFor(v)} x2={W - PR} y2={yFor(v)} stroke="#EEF2F6" strokeWidth="1" />
            <text x={PL - 6} y={yFor(v) + 4} textAnchor="end" fontSize="10" fill="#94A3B8">{Math.round(v)}</text>
          </g>
        ))}
        {/* Zéro */}
        {minV < 0 && maxV > 0 && (
          <line x1={PL} y1={yFor(0)} x2={W - PR} y2={yFor(0)} stroke="#CBD5E1" strokeDasharray="4,3" strokeWidth="1" />
        )}
        {/* Ligne */}
        <polyline points={polyPts} fill="none" stroke="#A78BFA" strokeWidth="2.2" strokeDasharray="6,3" />
        <polygon
          points={`${PL},${yFor(minV)} ${polyPts} ${xFor(points.length-1)},${yFor(minV)}`}
          fill="rgba(167,139,250,0.07)"
        />
        {/* Points interactifs */}
        {points.map((p, i) => (
          <g key={i}>
            <circle
              cx={xFor(i)} cy={yFor(p.cumul)} r="6"
              fill="transparent"
              onMouseEnter={() => setHovered(i)}
            />
            <circle
              cx={xFor(i)} cy={yFor(p.cumul)}
              r={hovered === i ? 5 : 3}
              fill={p.est_revenu === null ? '#64748B' : p.est_revenu ? '#34D399' : '#F87171'}
              stroke="white" strokeWidth="1.5"
              style={{ pointerEvents: 'none' }}
            />
            {/* Label date en bas (espacé) */}
            {(i === 0 || i === points.length - 1 || points.length <= 10 || i % Math.ceil(points.length / 8) === 0) && (
              <text
                x={xFor(i)} y={H - 8}
                textAnchor="middle" fontSize="8.5" fill="#94A3B8"
                transform={`rotate(-30, ${xFor(i)}, ${H - 8})`}
              >
                {p.date.slice(5)}
              </text>
            )}
          </g>
        ))}
        {/* Séparateur "aujourd'hui" */}
        <line x1={PL} y1={PT} x2={PL} y2={PT + iH} stroke="#E2E8F0" strokeWidth="1" strokeDasharray="3,3" />
        <text x={PL + 4} y={PT + 10} fontSize="9" fill="#94A3B8">Actuel</text>
      </svg>

      {/* Résumé prédictif en bas */}
      <div className="pred-summary-bar">
        <div className="pred-summary-item rev">
          <span>Revenus prévus</span>
          <strong>+{fmt(cumul[cumul.length - 1]?.rev_cumul || 0)} {devise}</strong>
        </div>
        <div className="pred-summary-item dep">
          <span>Dépenses prévues</span>
          <strong>−{fmt(cumul[cumul.length - 1]?.dep_cumul || 0)} {devise}</strong>
        </div>
        <div className={`pred-summary-item ${(cumul[cumul.length-1]?.ecart || 0) >= 0 ? 'rev' : 'dep'}`}>
          <span>Écart prévu</span>
          <strong>{(cumul[cumul.length-1]?.ecart || 0) >= 0 ? '+' : ''}{fmt(cumul[cumul.length - 1]?.ecart || 0)} {devise}</strong>
        </div>
      </div>
    </div>
  );
}

/* ── Composant principal ──────────────────────────────────── */
export default function PredictionOnglet({ compte }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [nMonths, setNMonths] = useState(3);
  const [maxMonths, setMax]   = useState(12);
  const [minConf, setMinConf] = useState(50);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetch(`${API}/comptes/${compte.id}/prediction?n_months=${nMonths}`)
      .then(r => r.json())
      .then(d => {
        if (d.error) { setError(d.error); setLoading(false); return; }
        setData(d);
        if (d.max_months) setMax(d.max_months);
        setLoading(false);
      })
      .catch(err => { setError('Erreur réseau : ' + err.message); setLoading(false); });
  }, [compte.id, nMonths]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="pred-wrap">

      {/* Jauge */}
      <div className="pred-gauge-section">
        <MonthGauge value={nMonths} max={Math.max(maxMonths, 3)} onChange={setNMonths} />
        <p className="pred-desc">
          Analyse les <strong>{nMonths} derniers mois</strong> pour identifier les transactions récurrentes
          et estimer leur probabilité d'apparaître le mois prochain.
        </p>
      </div>

      {/* Seuil de confiance */}
      <div className="pred-conf-section">
        <div className="gauge-header">
          <span className="gauge-label">Seuil de confiance (cumulé)</span>
          <span className="gauge-value conf">{minConf}%</span>
        </div>
        <input
          type="range" min={0} max={100} step={5}
          value={minConf}
          onChange={e => setMinConf(Number(e.target.value))}
          className="gauge-slider"
        />
        <div className="gauge-bounds"><span>0%</span><span>100%</span></div>
        <p className="pred-desc" style={{marginTop:4}}>
          Seules les transactions avec ≥ <strong>{minConf}%</strong> de probabilité sont incluses dans le graphique cumulé.
        </p>
      </div>

      {loading ? (
        <div className="pred-empty">Chargement…</div>
      ) : error ? (
        <div className="pred-error">
          <p>⚠ Erreur serveur :</p>
          <code>{error}</code>
        </div>
      ) : !data || !data.predictions?.length ? (
        <div className="pred-empty">Aucune prédiction disponible</div>
      ) : (
        <>
          {/* Tableau des prédictions */}
          <div className="pred-section">
            <h4>Transactions probables — mois prochain</h4>
            <div className="pred-table-wrap">
              <table className="pred-table">
                <thead>
                  <tr>
                    <th>Intitulé</th>
                    <th>Catégorie / Classe</th>
                    <th>Type</th>
                    <th>Valeur estimée</th>
                    <th>Date estimée</th>
                    <th>Probabilité</th>
                  </tr>
                </thead>
                <tbody>
                  {data.predictions.map((p, i) => (
                    <tr key={i} className={p.probabilite >= 75 ? 'high-proba' : p.probabilite >= 50 ? 'med-proba' : ''}>
                      <td className="pred-intitule">{p.intitule}</td>
                      <td className="pred-cat">{p.categorie} / {p.classe}</td>
                      <td>
                        <span className={`type-badge-pred ${p.est_revenu ? 'rev' : 'dep'}`}>
                          {p.est_revenu ? 'Revenu' : 'Dépense'}
                        </span>
                      </td>
                      <td className={`pred-val ${p.est_revenu ? 'rev' : 'dep'}`}>
                        {p.est_revenu ? '+' : '−'}{fmt(p.valeur)} {compte.devise}
                      </td>
                      <td className="pred-date">{p.date}</td>
                      <td><ProbaBadge pct={p.probabilite} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Graphique cumulé prédictif */}
          <div className="pred-section">
            <h4>Impact cumulé prévisible</h4>
            <p className="pred-chart-hint">Survolez les points pour voir le détail de chaque transaction</p>
            <CumulPredChart
              cumul={data.cumul_pred.filter(p => p.probabilite >= minConf)}
              soldeActuel={data.solde_actuel}
              devise={compte.devise}
            />
          </div>
        </>
      )}
    </div>
  );
}
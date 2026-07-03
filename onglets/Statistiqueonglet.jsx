import React, { useState, useEffect, useCallback, useRef } from 'react';
import './StatistiqueOnglet.css';

const API = 'http://127.0.0.1:5000/api';

function fmt(n) {
  return Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/* ── Frise chronologique ─────────────────────────────────────── */
function TimelineSlider({ months, debut, fin, onChange }) {
  const iStart = months.indexOf(debut);
  const iEnd   = months.indexOf(fin);
  const dragging = useRef(null);
  const barRef   = useRef(null);

  const getPct = e => {
    const rect = barRef.current.getBoundingClientRect();
    return Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  };

  const onMouseDown = (handle, e) => {
    e.preventDefault();
    dragging.current = handle;
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onMouseMove = useCallback(e => {
    if (!dragging.current) return;
    const pct = getPct(e);
    const idx  = Math.round(pct * (months.length - 1));
    const m    = months[idx];
    if (dragging.current === 'start') {
      if (idx <= months.indexOf(fin)) onChange(m, fin);
    } else {
      if (idx >= months.indexOf(debut)) onChange(debut, m);
    }
  }, [months, debut, fin, onChange]);

  const onMouseUp = useCallback(() => {
    dragging.current = null;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  }, [onMouseMove]);

  if (!months.length) return null;
  const pStart = iStart / (months.length - 1);
  const pEnd   = iEnd   / (months.length - 1);

  return (
    <div className="timeline-wrap">
      <div className="timeline-labels">
        <span>{months[0]}</span>
        <span className="tl-selection">{debut} → {fin}</span>
        <span>{months[months.length - 1]}</span>
      </div>
      <div className="timeline-bar" ref={barRef}>
        <div className="tl-track" />
        <div className="tl-range" style={{ left: `${pStart*100}%`, width: `${(pEnd-pStart)*100}%` }} />
        {months.map((m, i) => (
          <div
            key={m}
            className={`tl-tick ${m === debut || m === fin ? 'edge' : (i > iStart && i < iEnd ? 'in' : '')}`}
            style={{ left: `${(i/(months.length-1))*100}%` }}
            onClick={() => {
              if (i < months.indexOf(debut) || Math.abs(i - iStart) < Math.abs(i - iEnd))
                onChange(m, fin);
              else
                onChange(debut, m);
            }}
          />
        ))}
        <div className="tl-handle" style={{ left: `${pStart*100}%` }}
             onMouseDown={e => onMouseDown('start', e)} title={debut} />
        <div className="tl-handle" style={{ left: `${pEnd*100}%` }}
             onMouseDown={e => onMouseDown('end', e)} title={fin} />
      </div>
    </div>
  );
}

/* ── Totaux KPI ──────────────────────────────────────────────── */
function KpiBar({ totaux, moyennes, devise }) {
  const items = [
    { label: 'Revenus',  val: totaux.revenus,  avg: moyennes.revenus,  cls: 'rev' },
    { label: 'Dépenses', val: totaux.depenses, avg: moyennes.depenses, cls: 'dep' },
    { label: 'Solde',    val: totaux.solde,    avg: moyennes.solde,    cls: totaux.solde >= 0 ? 'rev' : 'dep' },
  ];
  return (
    <div className="kpi-bar">
      {items.map(it => (
        <div key={it.label} className="kpi-card">
          <span className="kpi-label">{it.label}</span>
          <span className={`kpi-val ${it.cls}`}>{fmt(it.val)} {devise}</span>
          <span className="kpi-avg">Moy/mois : {fmt(it.avg)} {devise}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Top 3 par mois ──────────────────────────────────────────── */
function Top3Table({ top3, months }) {
  const [openMonth, setOpenMonth] = useState(months[months.length-1]);
  const entries = top3[openMonth] || [];
  return (
    <div className="top3-wrap">
      <div className="top3-header">
        <h4>Top 3 dépenses récurrentes</h4>
        <select value={openMonth} onChange={e => setOpenMonth(e.target.value)} className="month-select">
          {months.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      {entries.length === 0
        ? <p className="stat-empty">Aucune dépense ce mois</p>
        : <table className="stat-table">
            <thead><tr><th>Intitulé</th><th>Total</th><th>Fois</th></tr></thead>
            <tbody>
              {entries.map((e,i) => (
                <tr key={i}>
                  <td>{e.intitule}</td>
                  <td className="td-dep">{fmt(e.total)}</td>
                  <td>{e.occurrences}</td>
                </tr>
              ))}
            </tbody>
          </table>
      }
    </div>
  );
}

/* ── Graphique cumulé SVG ────────────────────────────────────── */
function CumulChart({ series, stats }) {
  if (!series || series.length < 2) return <div className="stat-empty">Pas assez de données</div>;

  const W=700, H=220, PL=60, PR=20, PT=20, PB=28;
  const iW = W-PL-PR, iH = H-PT-PB;

  const vals = series.map(s => s.cumul);
  const trends = series.map(s => s.trend);
  const allV = [...vals, ...trends];
  const minV = Math.min(...allV), maxV = Math.max(...allV);
  const range = maxV - minV || 1;

  const xFor = i => PL + (i / (series.length-1)) * iW;
  const yFor = v => PT + iH - ((v - minV) / range) * iH;

  const cumulPts = series.map((s,i) => `${xFor(i)},${yFor(s.cumul)}`).join(' ');
  const trendPts = series.map((s,i) => `${xFor(i)},${yFor(s.trend)}`).join(' ');

  const minIdx = vals.indexOf(Math.min(...vals));
  const maxIdx = vals.indexOf(Math.max(...vals));

  const ticks = 4;
  const yTicks = Array.from({length: ticks+1}, (_,i) => minV + (range/ticks)*i);
  const xStep = Math.max(1, Math.floor(series.length / 6));
  const xTicks = series.filter((_, i) => i % xStep === 0 || i === series.length-1);

  return (
    <div className="cumul-chart-wrap">
      <div className="cumul-badges">
        <span className="badge min">Min : {fmt(stats.min)}</span>
        <span className="badge cur">Actuel : {fmt(stats.actuel)}</span>
        <span className="badge max">Max : {fmt(stats.max)}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="cumul-svg">
        {yTicks.map((v,i) => (
          <g key={i}>
            <line x1={PL} y1={yFor(v)} x2={W-PR} y2={yFor(v)} stroke="#EEF2F6" strokeWidth="1"/>
            <text x={PL-6} y={yFor(v)+4} textAnchor="end" fontSize="10" fill="#94A3B8">{Math.round(v)}</text>
          </g>
        ))}
        {xTicks.map((s,i) => (
          <text key={i} x={xFor(series.indexOf(s))} y={H-6} textAnchor="middle" fontSize="9" fill="#94A3B8">{s.date.slice(0,7)}</text>
        ))}
        <line x1={PL} y1={yFor(0)} x2={W-PR} y2={yFor(0)} stroke="#CBD5E1" strokeDasharray="4,3" strokeWidth="1"/>
        <polyline points={cumulPts} fill="none" stroke="#2DD4BF" strokeWidth="2.2"/>
        <polygon points={`${PL},${yFor(0)} ${cumulPts} ${W-PR},${yFor(0)}`} fill="rgba(45,212,191,0.07)"/>
        <polyline points={trendPts} fill="none" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="5,3"/>
        {/* Min / Max markers */}
        <circle cx={xFor(minIdx)} cy={yFor(vals[minIdx])} r="4" fill="#F87171"/>
        <circle cx={xFor(maxIdx)} cy={yFor(vals[maxIdx])} r="4" fill="#34D399"/>
        <circle cx={xFor(series.length-1)} cy={yFor(vals[series.length-1])} r="4" fill="#2DD4BF"/>
      </svg>
      <div className="cumul-legend">
        <span><span className="dot teal"/>Solde cumulé</span>
        <span><span className="dot amber"/>Tendance</span>
        <span><span className="dot red"/>Min</span>
        <span><span className="dot green"/>Max</span>
      </div>
    </div>
  );
}

/* ── Sankey simplifié ────────────────────────────────────────── */
function Sankey({ depenses, revenus }) {
  const maxVal = Math.max(
    ...depenses.map(d => d.valeur),
    ...revenus.map(r => r.valeur), 1
  );
  const barH = (v) => Math.max(6, (v / maxVal) * 160);
  const COLORS = ['#2DD4BF','#34D399','#60A5FA','#A78BFA','#F472B6','#F97316','#FACC15','#94A3B8'];

  return (
    <div className="sankey-wrap">
      <div className="sankey-col">
        <h5 className="sankey-title rev">Revenus par catégorie</h5>
        {revenus.map((r,i) => (
          <div key={r.categorie} className="sankey-bar-row">
            <span className="sankey-cat">{r.categorie}</span>
            <div className="sankey-bar-bg">
              <div className="sankey-bar" style={{width:`${(r.valeur/maxVal)*100}%`, background: COLORS[i%COLORS.length]}} />
            </div>
            <span className="sankey-val">{fmt(r.valeur)}</span>
          </div>
        ))}
      </div>
      <div className="sankey-col">
        <h5 className="sankey-title dep">Dépenses par catégorie</h5>
        {depenses.map((d,i) => (
          <div key={d.categorie} className="sankey-bar-row">
            <span className="sankey-cat">{d.categorie}</span>
            <div className="sankey-bar-bg">
              <div className="sankey-bar" style={{width:`${(d.valeur/maxVal)*100}%`, background: COLORS[i%COLORS.length]}} />
            </div>
            <span className="sankey-val">{fmt(d.valeur)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Camembert SVG ───────────────────────────────────────────── */
function PieChart({ data, title, onSliceClick, selectedKey, keyField = 'categorie', valField = 'valeur' }) {
  const total = data.reduce((s,d) => s + d[valField], 0);
  if (total === 0) return <div className="stat-empty">Aucune donnée</div>;

  const COLORS = ['#2DD4BF','#34D399','#60A5FA','#A78BFA','#F472B6','#F97316','#FACC15','#94A3B8','#F87171','#6EE7B7'];
  const R = 80, CX = 100, CY = 100;

  let angle = -Math.PI/2;
  const slices = data.map((d,i) => {
    const pct = d[valField] / total;
    const a1 = angle, a2 = angle + pct * 2 * Math.PI;
    angle = a2;
    const x1 = CX + R * Math.cos(a1), y1 = CY + R * Math.sin(a1);
    const x2 = CX + R * Math.cos(a2), y2 = CY + R * Math.sin(a2);
    const large = pct > 0.5 ? 1 : 0;
    const midA = (a1+a2)/2;
    const lx = CX + (R+18) * Math.cos(midA);
    const ly = CY + (R+18) * Math.sin(midA);
    return { key: d[keyField], pct, x1,y1,x2,y2, large, color: COLORS[i%COLORS.length], lx, ly, val: d[valField] };
  });

  return (
    <div className="pie-wrap">
      <h5 className="pie-title">{title}</h5>
      <svg viewBox="0 0 200 200" className="pie-svg">
        {slices.map(s => (
          <g key={s.key} onClick={() => onSliceClick && onSliceClick(s.key)}
             style={{cursor: onSliceClick ? 'pointer' : 'default'}}>
            <path
              d={`M${CX},${CY} L${s.x1},${s.y1} A${R},${R},0,${s.large},1,${s.x2},${s.y2} Z`}
              fill={s.color}
              opacity={selectedKey && selectedKey !== s.key ? 0.35 : 1}
              stroke="white" strokeWidth="1.5"
            />
            {s.pct > 0.05 && (
              <text x={s.lx} y={s.ly} textAnchor="middle" fontSize="8" fill="#475569" fontWeight="600">
                {Math.round(s.pct*100)}%
              </text>
            )}
          </g>
        ))}
      </svg>
      <div className="pie-legend">
        {slices.map(s => (
          <div key={s.key} className={`pie-legend-item ${selectedKey === s.key ? 'selected' : ''}`}
               onClick={() => onSliceClick && onSliceClick(s.key)}>
            <span className="pie-dot" style={{background: s.color}}/>
            <span className="pie-cat">{s.key}</span>
            <span className="pie-pct">{Math.round(s.pct*100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Top 5 dépenses ──────────────────────────────────────────── */
function Top5Table({ data, devise }) {
  return (
    <div className="top5-wrap">
      <h4>Top 5 dépenses (total période)</h4>
      <table className="stat-table">
        <thead><tr><th>#</th><th>Intitulé</th><th>Total</th></tr></thead>
        <tbody>
          {data.map((r,i) => (
            <tr key={i}>
              <td className="rank">#{i+1}</td>
              <td>{r.intitule}</td>
              <td className="td-dep">{fmt(r.total)} {devise}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Composant principal ─────────────────────────────────────── */
export default function StatistiqueOnglet({ compte }) {
  const [data, setData]                 = useState(null);
  const [loading, setLoading]           = useState(true);
  const [excludeVirement, setExclude]   = useState(false);
  const [debut, setDebut]               = useState(null);
  const [fin, setFin]                   = useState(null);
  const [selectedCat, setSelectedCat]   = useState(null);

  const load = useCallback(() => {
    if (!debut || !fin) return;
    setLoading(true);
    const params = new URLSearchParams({ debut, fin, exclude_virement: excludeVirement });
    fetch(`${API}/comptes/${compte.id}/stats?${params}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [compte.id, debut, fin, excludeVirement]);

  // Premier chargement : récupérer les mois disponibles
  useEffect(() => {
    fetch(`${API}/comptes/${compte.id}/stats?debut=0000-01&fin=9999-12`)
      .then(r => r.json())
      .then(d => {
        if (d.all_months && d.all_months.length) {
          const months = d.all_months;
          setDebut(months[0]);
          setFin(months[months.length-1]);
          setData(d);
        }
        setLoading(false);
      });
  }, [compte.id]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="stat-loading">Chargement…</div>;
  if (!data || data.empty) return <div className="stat-empty">Aucune donnée pour ce compte</div>;

  const months = data.all_months || [];

  return (
    <div className="stat-wrap">

      {/* Frise chronologique */}
      <div className="stat-section">
        <TimelineSlider
          months={months}
          debut={debut}
          fin={fin}
          onChange={(d,f) => { setDebut(d); setFin(f); }}
        />
        <label className="exclude-toggle">
          <input type="checkbox" checked={excludeVirement}
                 onChange={e => setExclude(e.target.checked)} />
          Ignorer les virements intercomptes
        </label>
      </div>

      {/* KPI totaux */}
      <KpiBar totaux={data.totaux} moyennes={data.moyennes} devise={compte.devise} />

      {/* Top 3 par mois */}
      <div className="stat-section">
        <Top3Table top3={data.top3_par_mois} months={data.evolution_mensuelle.map(m => m.month)} />
      </div>

      {/* Graphique cumulé */}
      <div className="stat-section">
        <h4>Évolution du solde cumulé</h4>
        <CumulChart series={data.cumul_series} stats={data.cumul_stats} />
      </div>

      {/* Sankey */}
      <div className="stat-section">
        <h4>Flux par catégorie</h4>
        <Sankey depenses={data.sankey.depenses} revenus={data.sankey.revenus} />
      </div>

      {/* Camemberts */}
      <div className="stat-section">
        <div className="pies-row">
          <PieChart
            data={data.sankey.revenus}
            title="Répartition revenus"
            onSliceClick={k => setSelectedCat(k === selectedCat ? null : k)}
            selectedKey={selectedCat}
          />
          <PieChart
            data={data.sankey.depenses}
            title="Répartition dépenses"
            onSliceClick={k => setSelectedCat(k === selectedCat ? null : k)}
            selectedKey={selectedCat}
          />
          {selectedCat && data.classes_by_cat[selectedCat] && (
            <PieChart
              data={data.classes_by_cat[selectedCat]}
              title={`Classes — ${selectedCat}`}
              keyField="classe"
              selectedKey={null}
            />
          )}
        </div>
        {selectedCat && (
          <p className="cat-hint">
            Catégorie sélectionnée : <strong>{selectedCat}</strong>
            <button className="btn-clear-cat" onClick={() => setSelectedCat(null)}>✕ Effacer</button>
          </p>
        )}
      </div>

      {/* Top 5 dépenses */}
      <div className="stat-section">
        <Top5Table data={data.top5_depenses} devise={compte.devise} />
      </div>

    </div>
  );
}
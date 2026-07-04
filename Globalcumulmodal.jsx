import React, { useState, useEffect, useRef, useCallback } from 'react';
import './GlobalCumulModal.css';

const API = 'http://127.0.0.1:5000/api';
const COLORS = ['#2DD4BF','#60A5FA','#F472B6','#34D399','#F97316','#A78BFA','#FACC15','#F87171'];

function fmt(n) {
  return Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/* ── Slider fenêtre — par mois ────────────────────── */
function WindowSlider({ allMonths, windowStart, windowEnd, onChange }) {
  const barRef  = useRef(null);
  const dragging = useRef(null);
  const n = allMonths.length;

  const iStart = allMonths.indexOf(windowStart);
  const iEnd   = allMonths.indexOf(windowEnd);
  const pStart = n > 1 ? iStart / (n - 1) : 0;
  const pEnd   = n > 1 ? iEnd   / (n - 1) : 1;

  const idxAt = e => {
    const rect = barRef.current.getBoundingClientRect();
    const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    return Math.round(pct * (n - 1));
  };

  const onMove = useCallback(e => {
    if (!dragging.current) return;
    const idx = idxAt(e);
    const m   = allMonths[idx];
    if (dragging.current === 'start' && idx <= allMonths.indexOf(windowEnd))
      onChange(m, windowEnd);
    else if (dragging.current === 'end' && idx >= allMonths.indexOf(windowStart))
      onChange(windowStart, m);
  }, [allMonths, windowStart, windowEnd, onChange]);

  const onUp = useCallback(() => {
    dragging.current = null;
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
  }, [onMove]);

  const startDrag = (handle, e) => {
    e.preventDefault();
    dragging.current = handle;
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  if (n === 0) return null;

  return (
    <div className="gc-slider-wrap">
      <div className="gc-slider-labels">
        <span>{allMonths[0]}</span>
        <span className="gc-window-label">{windowStart} → {windowEnd}</span>
        <span>{allMonths[n - 1]}</span>
      </div>
      <div className="gc-slider-bar" ref={barRef}>
        <div className="gc-track" />
        <div className="gc-range" style={{ left:`${pStart*100}%`, width:`${(pEnd-pStart)*100}%` }} />
        <div className="gc-handle" style={{ left:`${pStart*100}%` }}
             onMouseDown={e => startDrag('start', e)} />
        <div className="gc-handle" style={{ left:`${pEnd*100}%` }}
             onMouseDown={e => startDrag('end', e)} />
      </div>
    </div>
  );
}

/* ── Graphique SVG ────────────────────────────────── */
function MultiCumulChart({ comptes, showTotal, windowStart, windowEnd }) {
  const [hovered, setHovered] = useState(null);
  const svgRef = useRef(null);

  const W=760, H=280, PL=72, PR=20, PT=16, PB=32;
  const iW = W-PL-PR, iH = H-PT-PB;

  // Regrouper par mois — prendre la dernière valeur de chaque mois
  const monthlyFor = series => {
    const map = {};
    series.forEach(p => {
      if (p.date >= windowStart+'-01' && p.date <= windowEnd+'-31')
        map[p.date.slice(0,7)] = p.cumul;
    });
    return Object.entries(map).sort(([a],[b]) => a.localeCompare(b))
                              .map(([month, cumul]) => ({ month, cumul }));
  };

  const seriesData = comptes.map((c, i) => ({
    ...c,
    monthly: monthlyFor(c.series),
    color: COLORS[i % COLORS.length],
  })).filter(c => c.monthly.length > 0);

  // Courbe cumulée globale (somme de tous les comptes par mois)
  let totalSeries = null;
  if (showTotal && seriesData.length > 1) {
    const allMonths = [...new Set(seriesData.flatMap(c => c.monthly.map(p => p.month)))].sort();
    // Pour chaque mois, somme des dernières valeurs connues de chaque compte
    const totals = allMonths.map(month => {
      const sum = seriesData.reduce((s, c) => {
        const pts = c.monthly.filter(p => p.month <= month);
        return s + (pts.length ? pts[pts.length-1].cumul : 0);
      }, 0);
      return { month, cumul: round2(sum) };
    });
    totalSeries = totals;
  }

  const allMonths = [...new Set([
    ...seriesData.flatMap(c => c.monthly.map(p => p.month)),
    ...(totalSeries ? totalSeries.map(p => p.month) : [])
  ])].sort();

  if (allMonths.length === 0) return <div className="gc-empty">Aucune donnée dans cette période</div>;

  const allVals = [
    ...seriesData.flatMap(c => c.monthly.map(p => p.cumul)),
    ...(totalSeries ? totalSeries.map(p => p.cumul) : [])
  ];
  const minV = Math.min(...allVals), maxV = Math.max(...allVals);
  const range = maxV - minV || 1;

  const xFor = m => PL + (allMonths.indexOf(m) / (allMonths.length - 1 || 1)) * iW;
  const yFor = v => PT + iH - ((v - minV) / range) * iH;

  const yTicks = 5;
  const yTickVals = Array.from({length: yTicks+1}, (_,i) => minV + (range/yTicks)*i);
  const xStep = Math.max(1, Math.floor(allMonths.length / 8));

  const handleMove = e => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mx   = (e.clientX - rect.left) * (W / rect.width);
    const xi   = Math.round(((mx - PL) / iW) * (allMonths.length - 1));
    if (xi < 0 || xi >= allMonths.length) { setHovered(null); return; }
    const month = allMonths[xi];
    const items = seriesData.map(c => {
      const pts = c.monthly.filter(p => p.month <= month);
      return { name: c.name, color: c.color, cumul: pts.length ? pts[pts.length-1].cumul : null };
    });
    if (totalSeries) {
      const pts = totalSeries.filter(p => p.month <= month);
      if (pts.length) items.push({ name: 'Total', color: '#1E293B', cumul: pts[pts.length-1].cumul });
    }
    setHovered({ x: mx, month, items });
  };

  return (
    <div className="gc-chart-wrap">
      {hovered && (
        <div className="gc-tooltip" style={{
          left: Math.min(hovered.x + 14, W - 200) + 'px',
          top: '10px',
        }}>
          <div className="gc-tooltip-date">{hovered.month}</div>
          {hovered.items.filter(i => i.cumul !== null).map(item => (
            <div key={item.name} className="gc-tooltip-row">
              <span className="gc-tooltip-dot" style={{ background: item.color }} />
              <span>{item.name}</span>
              <strong>{fmt(item.cumul)}</strong>
            </div>
          ))}
        </div>
      )}

      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="gc-svg"
           preserveAspectRatio="xMidYMid meet"
           onMouseMove={handleMove} onMouseLeave={() => setHovered(null)}>

        {/* Grille Y */}
        {yTickVals.map((v,i) => (
          <g key={i}>
            <line x1={PL} y1={yFor(v)} x2={W-PR} y2={yFor(v)} stroke="#EEF2F6" strokeWidth="1"/>
            <text x={PL-6} y={yFor(v)+4} textAnchor="end" fontSize="10" fill="#94A3B8">
              {Math.round(v)}
            </text>
          </g>
        ))}

        {/* Zéro */}
        {minV < 0 && maxV > 0 && (
          <line x1={PL} y1={yFor(0)} x2={W-PR} y2={yFor(0)}
                stroke="#CBD5E1" strokeDasharray="4,3" strokeWidth="1"/>
        )}

        {/* Labels X — par mois, espacement auto */}
        {allMonths.filter((_,i) => i % xStep === 0 || i === allMonths.length-1).map(m => (
          <text key={m} x={xFor(m)} y={H-4}
                textAnchor="middle" fontSize="10" fill="#94A3B8">
            {m}
          </text>
        ))}

        {/* Courbes comptes */}
        {seriesData.map(c => {
          const pts = c.monthly.map(p => `${xFor(p.month)},${yFor(p.cumul)}`).join(' ');
          return (
            <g key={c.id}>
              <polyline points={pts} fill="none" stroke={c.color} strokeWidth="2" strokeLinejoin="round"/>
              <circle cx={xFor(c.monthly[c.monthly.length-1].month)}
                      cy={yFor(c.monthly[c.monthly.length-1].cumul)}
                      r="3.5" fill={c.color} stroke="white" strokeWidth="1.5"/>
            </g>
          );
        })}

        {/* Courbe totale */}
        {totalSeries && (() => {
          const pts = totalSeries.map(p => `${xFor(p.month)},${yFor(p.cumul)}`).join(' ');
          return (
            <g>
              <polyline points={pts} fill="none" stroke="#1E293B"
                        strokeWidth="2.5" strokeDasharray="6,3" strokeLinejoin="round"/>
              <circle cx={xFor(totalSeries[totalSeries.length-1].month)}
                      cy={yFor(totalSeries[totalSeries.length-1].cumul)}
                      r="4" fill="#1E293B" stroke="white" strokeWidth="1.5"/>
            </g>
          );
        })()}

        {/* Ligne hover */}
        {hovered && hovered.x >= PL && hovered.x <= W-PR && (
          <line x1={hovered.x} y1={PT} x2={hovered.x} y2={PT+iH}
                stroke="#CBD5E1" strokeWidth="1" strokeDasharray="3,3"/>
        )}
      </svg>
    </div>
  );
}

function round2(n) { return Math.round(n * 100) / 100; }

/* ── Modal ────────────────────────────────────────── */
export default function GlobalCumulModal({ onClose }) {
  const [comptes, setComptes]      = useState([]);
  const [loading, setLoading]      = useState(true);
  const [windowStart, setWinStart] = useState(null);
  const [windowEnd,   setWinEnd]   = useState(null);
  const [showTotal,   setTotal]    = useState(true);

  useEffect(() => {
    fetch(`${API}/global/cumul`)
      .then(r => r.json())
      .then(data => {
        setComptes(data);
        if (data.length) {
          const months = [...new Set(data.flatMap(c => c.series.map(p => p.date.slice(0,7))))].sort();
          setWinStart(months[0]);
          setWinEnd(months[months.length-1]);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const allMonths = [...new Set(comptes.flatMap(c => c.series.map(p => p.date.slice(0,7))))].sort();

  return (
    <div className="gc-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="gc-modal">

        <div className="gc-modal-header">
          <h2>Évolution globale des comptes</h2>
          <div className="gc-header-actions">
            <label className="gc-total-toggle">
              <input type="checkbox" checked={showTotal} onChange={e => setTotal(e.target.checked)}/>
              Afficher le total cumulé
            </label>
            <button className="gc-close" onClick={onClose}>✕</button>
          </div>
        </div>

        {loading ? <div className="gc-empty">Chargement…</div> : (
          <div className="gc-modal-body">

            {/* Légende */}
            <div className="gc-legend">
              {comptes.map((c, i) => (
                <div key={c.id} className="gc-legend-item">
                  <span className="gc-legend-dot" style={{ background: COLORS[i % COLORS.length] }}/>
                  <span className="gc-legend-name">{c.name}</span>
                  <span className="gc-legend-val"
                        style={{ color: c.cumul_final >= 0 ? '#059669' : '#DC2626' }}>
                    {c.cumul_final >= 0 ? '+' : ''}{fmt(c.cumul_final)}
                  </span>
                </div>
              ))}
              {showTotal && comptes.length > 1 && (
                <div className="gc-legend-item total">
                  <span className="gc-legend-dot" style={{ background: '#1E293B' }}/>
                  <span className="gc-legend-name">Total</span>
                  <span className="gc-legend-val"
                        style={{ color: comptes.reduce((s,c)=>s+c.cumul_final,0) >= 0 ? '#059669':'#DC2626' }}>
                    {fmt(comptes.reduce((s,c)=>s+c.cumul_final,0))}
                  </span>
                </div>
              )}
            </div>

            {/* Graphique */}
            {windowStart && windowEnd && (
              <MultiCumulChart
                comptes={comptes}
                showTotal={showTotal}
                windowStart={windowStart}
                windowEnd={windowEnd}
              />
            )}

            {/* Slider par mois */}
            {allMonths.length > 1 && windowStart && windowEnd && (
              <WindowSlider
                allMonths={allMonths}
                windowStart={windowStart}
                windowEnd={windowEnd}
                onChange={(s, e) => { setWinStart(s); setWinEnd(e); }}
              />
            )}

          </div>
        )}
      </div>
    </div>
  );
}
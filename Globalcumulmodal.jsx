import React, { useState, useEffect, useRef, useCallback } from 'react';
import './GlobalCumulModal.css';

const API = 'http://127.0.0.1:5000/api';

const COLORS = ['#2DD4BF', '#60A5FA', '#F472B6', '#34D399', '#F97316', '#A78BFA', '#FACC15', '#F87171'];

function fmt(n) {
  return Number(n).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/* ── Slider fenêtre temporelle ────────────────────── */
function WindowSlider({ allDates, windowStart, windowEnd, onChange }) {
  const barRef = useRef(null);
  const dragging = useRef(null);
  const n = allDates.length;

  const iStart = allDates.indexOf(windowStart);
  const iEnd   = allDates.indexOf(windowEnd);
  const pStart = n > 1 ? iStart / (n - 1) : 0;
  const pEnd   = n > 1 ? iEnd   / (n - 1) : 1;

  const getPct = e => {
    const rect = barRef.current.getBoundingClientRect();
    return Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  };

  const onMouseMove = useCallback(e => {
    if (!dragging.current || !barRef.current) return;
    const pct = getPct(e);
    const idx = Math.round(pct * (n - 1));
    const d = allDates[idx];
    if (dragging.current === 'start' && idx <= allDates.indexOf(windowEnd))
      onChange(d, windowEnd);
    else if (dragging.current === 'end' && idx >= allDates.indexOf(windowStart))
      onChange(windowStart, d);
  }, [allDates, windowStart, windowEnd, onChange, n]);

  const onMouseUp = useCallback(() => {
    dragging.current = null;
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  }, [onMouseMove]);

  const startDrag = (handle, e) => {
    e.preventDefault();
    dragging.current = handle;
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  if (n === 0) return null;

  return (
    <div className="gc-slider-wrap">
      <div className="gc-slider-labels">
        <span>{allDates[0]}</span>
        <span className="gc-window-label">{windowStart} → {windowEnd}</span>
        <span>{allDates[n - 1]}</span>
      </div>
      <div className="gc-slider-bar" ref={barRef}>
        <div className="gc-track" />
        <div className="gc-range" style={{ left: `${pStart * 100}%`, width: `${(pEnd - pStart) * 100}%` }} />
        <div className="gc-handle" style={{ left: `${pStart * 100}%` }}
             onMouseDown={e => startDrag('start', e)} />
        <div className="gc-handle" style={{ left: `${pEnd * 100}%` }}
             onMouseDown={e => startDrag('end', e)} />
      </div>
    </div>
  );
}

/* ── Graphique SVG multi-comptes ──────────────────── */
function MultiCumulChart({ comptes, windowStart, windowEnd }) {
  const [hovered, setHovered] = useState(null); // { x, y, items }

  // Filtrer chaque série sur la fenêtre pour l'affichage
  // mais les valeurs cumulées restent celles calculées globalement
  const filtered = comptes.map(c => ({
    ...c,
    visible: c.series.filter(p => p.date >= windowStart && p.date <= windowEnd)
  })).filter(c => c.visible.length > 0);

  if (!filtered.length) return <div className="gc-empty">Aucune donnée dans cette période</div>;

  const W = 760, H = 320, PL = 70, PR = 20, PT = 20, PB = 36;
  const iW = W - PL - PR, iH = H - PT - PB;

  const allVals = filtered.flatMap(c => c.visible.map(p => p.cumul));
  const minV = Math.min(...allVals), maxV = Math.max(...allVals);
  const range = maxV - minV || 1;

  // Dates uniques triées dans la fenêtre
  const allDates = [...new Set(filtered.flatMap(c => c.visible.map(p => p.date)))].sort();
  const xFor = d => PL + (allDates.indexOf(d) / (allDates.length - 1 || 1)) * iW;
  const yFor = v => PT + iH - ((v - minV) / range) * iH;

  const yTicks = 5;
  const yTickVals = Array.from({ length: yTicks + 1 }, (_, i) => minV + (range / yTicks) * i);
  const xStep = Math.max(1, Math.floor(allDates.length / 7));

  const handleMouseMove = (e, svgEl) => {
    const rect = svgEl.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (W / rect.width);
    // Trouver la date la plus proche
    const xi = Math.round(((mx - PL) / iW) * (allDates.length - 1));
    if (xi < 0 || xi >= allDates.length) { setHovered(null); return; }
    const date = allDates[xi];
    const items = filtered.map(c => {
      // Valeur cumulée la plus proche de cette date
      const closest = c.visible.reduce((best, p) => {
        return Math.abs(p.date.localeCompare(date)) < Math.abs(best.date.localeCompare(date)) ? p : best;
      }, c.visible[0]);
      return { name: c.name, cumul: closest?.cumul, color: COLORS[filtered.indexOf(c) % COLORS.length] };
    });
    setHovered({ x: mx, y: e.clientY - rect.top * (H / rect.height), date, items });
  };

  return (
    <div className="gc-chart-wrap" style={{ position: 'relative' }}>
      {hovered && (
        <div className="gc-tooltip" style={{
          left: Math.min(hovered.x + 14, W - 200) + 'px',
          top: Math.max(hovered.y - 60, 0) + 'px',
        }}>
          <div className="gc-tooltip-date">{hovered.date}</div>
          {hovered.items.filter(i => i.cumul !== undefined).map(item => (
            <div key={item.name} className="gc-tooltip-row">
              <span className="gc-tooltip-dot" style={{ background: item.color }} />
              <span>{item.name}</span>
              <strong>{fmt(item.cumul)}</strong>
            </div>
          ))}
        </div>
      )}
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="gc-svg"
        preserveAspectRatio="none"
        onMouseMove={e => handleMouseMove(e, e.currentTarget)}
        onMouseLeave={() => setHovered(null)}
      >
        {/* Grille Y */}
        {yTickVals.map((v, i) => (
          <g key={i}>
            <line x1={PL} y1={yFor(v)} x2={W - PR} y2={yFor(v)} stroke="#EEF2F6" strokeWidth="1" />
            <text x={PL - 6} y={yFor(v) + 4} textAnchor="end" fontSize="10" fill="#94A3B8">{Math.round(v)}</text>
          </g>
        ))}
        {/* Zéro */}
        {minV < 0 && maxV > 0 && (
          <line x1={PL} y1={yFor(0)} x2={W - PR} y2={yFor(0)}
                stroke="#CBD5E1" strokeDasharray="4,3" strokeWidth="1" />
        )}
        {/* Labels X */}
        {allDates.filter((_, i) => i % xStep === 0 || i === allDates.length - 1).map(d => (
          <text key={d} x={xFor(d)} y={H - 8}
                textAnchor="middle" fontSize="9" fill="#94A3B8"
                transform={`rotate(-25,${xFor(d)},${H - 8})`}>
            {d.slice(0, 7)}
          </text>
        ))}
        {/* Courbes */}
        {filtered.map((c, ci) => {
          const pts = c.visible.map(p => `${xFor(p.date)},${yFor(p.cumul)}`).join(' ');
          return (
            <g key={c.id}>
              <polyline points={pts} fill="none"
                        stroke={COLORS[ci % COLORS.length]}
                        strokeWidth="2.2" strokeLinejoin="round" />
              {/* Point final */}
              <circle
                cx={xFor(c.visible[c.visible.length - 1].date)}
                cy={yFor(c.visible[c.visible.length - 1].cumul)}
                r="4" fill={COLORS[ci % COLORS.length]} stroke="white" strokeWidth="1.5"
              />
            </g>
          );
        })}
        {/* Ligne de hover */}
        {hovered && hovered.x >= PL && hovered.x <= W - PR && (
          <line x1={hovered.x} y1={PT} x2={hovered.x} y2={PT + iH}
                stroke="#CBD5E1" strokeWidth="1" strokeDasharray="3,3" />
        )}
      </svg>
    </div>
  );
}

/* ── Modal principal ──────────────────────────────── */
export default function GlobalCumulModal({ onClose }) {
  const [comptes, setComptes]       = useState([]);
  const [loading, setLoading]       = useState(true);
  const [windowStart, setWinStart]  = useState(null);
  const [windowEnd,   setWinEnd]    = useState(null);

  useEffect(() => {
    fetch(`${API}/global/cumul`)
      .then(r => r.json())
      .then(data => {
        setComptes(data);
        if (data.length) {
          const allDates = data.flatMap(c => c.series.map(p => p.date)).sort();
          setWinStart(allDates[0]);
          setWinEnd(allDates[allDates.length - 1]);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Toutes les dates uniques triées
  const allDates = [...new Set(comptes.flatMap(c => c.series.map(p => p.date)))].sort();

  return (
    <div className="gc-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="gc-modal">

        <div className="gc-modal-header">
          <h2>Évolution globale des comptes</h2>
          <button className="gc-close" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="gc-empty">Chargement…</div>
        ) : (
          <div className="gc-modal-body">

            {/* Légende comptes */}
            <div className="gc-legend">
              {comptes.map((c, i) => (
                <div key={c.id} className="gc-legend-item">
                  <span className="gc-legend-dot" style={{ background: COLORS[i % COLORS.length] }} />
                  <span className="gc-legend-name">{c.name}</span>
                  <span className="gc-legend-val" style={{ color: c.cumul_final >= 0 ? '#059669' : '#DC2626' }}>
                    {c.cumul_final >= 0 ? '+' : ''}{fmt(c.cumul_final)}
                  </span>
                </div>
              ))}
            </div>

            {/* Graphique */}
            {windowStart && windowEnd && (
              <MultiCumulChart
                comptes={comptes}
                windowStart={windowStart}
                windowEnd={windowEnd}
              />
            )}

            {/* Slider fenêtre */}
            {allDates.length > 1 && windowStart && windowEnd && (
              <WindowSlider
                allDates={allDates}
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
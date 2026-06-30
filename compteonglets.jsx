import React, { useState } from 'react';
import TableauOnglet from './onglets/TableauOnglet';
import VirementIntercompteOnglet from './onglets/VirementIntercompteOnglet';
import StatistiqueOnglet from './onglets/StatistiqueOnglet';
import PredictionOnglet from './onglets/PredictionOnglet';
import './CompteOnglets.css';

const TABS = [
  { key: 'tableau',    label: 'Tableau',   icon: '📋' },
  { key: 'virement',   label: 'Virement',  icon: '🔁', requiresActive: true },
  { key: 'statistique',label: 'Stats',     icon: '📊' },
  { key: 'prediction', label: 'Prédiction',icon: '🔮', requiresActive: true },
];

export default function CompteOnglets({ compte, onAccountsChanged }) {
  const [active, setActive] = useState('tableau');

  if (!compte) {
    return (
      <div className="onglets-placeholder">
        <div className="placeholder-icon">🗂️</div>
        <h2>Aucun compte sélectionné</h2>
        <p>Sélectionnez un compte dans la liste pour voir ses détails.</p>
      </div>
    );
  }

  const visibleTabs = TABS.filter(tab => !tab.requiresActive || compte.status);

  // Si l'onglet actif n'est plus visible (ex: compte désactivé pendant qu'on était sur Virement)
  if (!visibleTabs.find(t => t.key === active)) {
    setActive('tableau');
  }

  return (
    <div className="compte-onglets">

      <div className="compte-onglets-header">
        <div className="compte-onglets-title">
          <span className="compte-onglets-name">{compte.name}</span>
          <span className="compte-onglets-devise">{compte.devise}</span>
        </div>

        <nav className="onglets-nav">
          {visibleTabs.map(tab => (
            <button
              key={tab.key}
              className={`onglet-btn ${active === tab.key ? 'active' : ''}`}
              onClick={() => setActive(tab.key)}
            >
              <span className="onglet-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="onglets-content">
        {active === 'tableau'     && <TableauOnglet compte={compte} />}
        {active === 'virement'    && compte.status && <VirementIntercompteOnglet compte={compte} onAccountsChanged={onAccountsChanged} />}
        {active === 'statistique' && <StatistiqueOnglet compte={compte} />}
        {active === 'prediction'  && compte.status && <PredictionOnglet compte={compte} />}
      </div>

    </div>
  );
}
import React from 'react';

export default function StatistiqueOnglet({ compte }) {
  return (
    <div>
      <h3 style={{ fontSize: '0.9rem', color: '#64748B', marginBottom: 12 }}>
        Statistiques — {compte.name}
      </h3>
      <p style={{ color: '#94A3B8', fontSize: '0.85rem' }}>
        Les statistiques détaillées seront affichées ici.
      </p>
    </div>
  );
}
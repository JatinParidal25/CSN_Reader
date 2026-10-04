import React from 'react';
import { Database, GitFork, BarChart3, Columns, Activity } from 'lucide-react';
import type { ParsedCSN } from '../types/metadata';

interface Props {
  metadata: ParsedCSN;
  onRefresh?: () => void;
}

export const Dashboard: React.FC<Props> = ({ metadata }) => {
  const cards = [
    {
      label: 'Objects / Entities',
      value: metadata.object_count,
      icon: Database,
      color: 'var(--accent-purple)',
      bg: 'rgba(168, 85, 247, 0.1)',
      border: 'rgba(168, 85, 247, 0.25)',
    },
    {
      label: 'Relationships & Edges',
      value: metadata.relationship_count,
      icon: GitFork,
      color: 'var(--accent-cyan)',
      bg: 'rgba(56, 189, 248, 0.1)',
      border: 'rgba(56, 189, 248, 0.25)',
    },
    {
      label: 'Calculated Measures',
      value: metadata.measure_count,
      icon: BarChart3,
      color: 'var(--accent-emerald)',
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.25)',
    },
    {
      label: 'Total Extracted Fields',
      value: metadata.field_count,
      icon: Columns,
      color: 'var(--accent-blue)',
      bg: 'rgba(59, 130, 246, 0.1)',
      border: 'rgba(59, 130, 246, 0.25)',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={24} color="var(--accent-cyan)" />
            Datasphere Metadata Dashboard
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Active Model: <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{metadata.filename}</span>
            {metadata.version ? ` • CSN v${metadata.version}` : ''}
          </p>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '14px',
        }}
      >
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="glass-panel"
              style={{
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                borderColor: card.border,
                transition: 'transform 0.2s ease',
              }}
            >
              <div
                style={{
                  width: '46px',
                  height: '46px',
                  borderRadius: '10px',
                  background: card.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: card.color,
                }}
              >
                <Icon size={24} />
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                  {card.label}
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {card.value}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

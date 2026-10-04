import React, { useState } from 'react';
import { Search, Layers, ChevronRight, BarChart2 } from 'lucide-react';
import type { ObjectMetadata } from '../types/metadata';

interface Props {
  objects: ObjectMetadata[];
  selectedObject: ObjectMetadata | null;
  onSelectObject: (obj: ObjectMetadata) => void;
}

export const ObjectList: React.FC<Props> = ({ objects, selectedObject, onSelectObject }) => {
  const [search, setSearch] = useState('');
  const [filterPattern, setFilterPattern] = useState<string>('ALL');

  const getPatternBadgeClass = (pattern?: string | null) => {
    if (!pattern) return 'badge-entity';
    const p = pattern.toUpperCase();
    if (p.includes('CUBE')) return 'badge-cube';
    if (p.includes('FACT')) return 'badge-fact';
    if (p.includes('DIMENSION')) return 'badge-dim';
    return 'badge-entity';
  };

  const patterns = ['ALL', ...Array.from(new Set(objects.map((o) => o.modeling_pattern || 'ENTITY')))];

  const filtered = objects.filter((obj) => {
    const matchesSearch =
      obj.name.toLowerCase().includes(search.toLowerCase()) ||
      (obj.label && obj.label.toLowerCase().includes(search.toLowerCase()));

    const matchesPattern =
      filterPattern === 'ALL' || (obj.modeling_pattern || 'ENTITY') === filterPattern;

    return matchesSearch && matchesPattern;
  });

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header & Search */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Datasphere Objects</h3>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {filtered.length} / {objects.length}
          </span>
        </div>

        {/* Search input */}
        <div style={{ position: 'relative', marginBottom: '10px' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
          <input
            type="text"
            placeholder="Filter objects or labels..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 34px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              fontSize: '0.825rem',
              outline: 'none',
            }}
          />
        </div>

        {/* Pattern Filter Tags */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
          {patterns.map((pat) => (
            <button
              key={pat}
              onClick={() => setFilterPattern(pat)}
              style={{
                background: filterPattern === pat ? 'var(--accent-blue)' : 'var(--bg-surface)',
                color: filterPattern === pat ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.7rem',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                fontWeight: 500,
              }}
            >
              {pat}
            </button>
          ))}
        </div>
      </div>

      {/* List items */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No objects match the search criteria.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {filtered.map((obj) => {
              const isSelected = selectedObject?.name === obj.name;
              return (
                <div
                  key={obj.name}
                  onClick={() => onSelectObject(obj)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '8px',
                    background: isSelected ? 'var(--bg-card-active)' : 'transparent',
                    border: isSelected ? '1px solid var(--border-accent)' : '1px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) (e.currentTarget.style.background = 'var(--bg-card-hover)');
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) (e.currentTarget.style.background = 'transparent');
                  }}
                >
                  <div style={{ overflow: 'hidden', marginRight: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontWeight: 600,
                          fontSize: '0.875rem',
                          color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)',
                          fontFamily: 'var(--font-mono)',
                          whiteSpace: 'nowrap',
                          textOverflow: 'ellipsis',
                          overflow: 'hidden',
                        }}
                      >
                        {obj.name}
                      </span>
                    </div>

                    {obj.label && obj.label !== obj.name && (
                      <div
                        style={{
                          fontSize: '0.75rem',
                          color: 'var(--text-secondary)',
                          whiteSpace: 'nowrap',
                          textOverflow: 'ellipsis',
                          overflow: 'hidden',
                          marginTop: '2px',
                        }}
                      >
                        {obj.label}
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '6px' }}>
                      <span className={`badge ${getPatternBadgeClass(obj.modeling_pattern)}`}>
                        {obj.modeling_pattern || obj.kind}
                      </span>

                      {obj.measures.length > 0 && (
                        <span className="badge badge-measure" title={`${obj.measures.length} measures`}>
                          <BarChart2 size={10} /> {obj.measures.length}
                        </span>
                      )}

                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {obj.fields.length} cols
                      </span>
                    </div>
                  </div>

                  <ChevronRight size={16} color={isSelected ? 'var(--accent-cyan)' : 'var(--text-muted)'} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  Database,
  Columns,
  Link as LinkIcon,
  GitBranch,
  Key,
  BarChart3,
  ExternalLink,
  Layers,
  FolderTree,
} from 'lucide-react';
import type { ObjectMetadata } from '../types/metadata';

interface Props {
  object: ObjectMetadata;
  onNavigateToObject?: (objName: string) => void;
  onViewLineage?: () => void;
}

export const ObjectDetails: React.FC<Props> = ({ object, onNavigateToObject, onViewLineage }) => {
  const [activeTab, setActiveTab] = useState<'fields' | 'associations' | 'hierarchies' | 'sources'>('fields');
  const [fieldSearch, setFieldSearch] = useState('');

  const filteredFields = object.fields.filter(
    (f) =>
      f.name.toLowerCase().includes(fieldSearch.toLowerCase()) ||
      (f.label && f.label.toLowerCase().includes(fieldSearch.toLowerCase()))
  );

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={24} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {object.name}
            </h2>
            <span className="badge badge-cube">
              {object.modeling_pattern || object.kind}
            </span>
          </div>

          {object.label && (
            <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {object.label}
            </div>
          )}

          {object.supported_capabilities && object.supported_capabilities.length > 0 && (
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Capabilities:</span>
              {object.supported_capabilities.map((cap) => (
                <span key={cap} className="badge badge-entity" style={{ fontSize: '0.7rem' }}>
                  {cap}
                </span>
              ))}
            </div>
          )}
        </div>

        {onViewLineage && (
          <button className="btn-primary" onClick={onViewLineage}>
            <GitBranch size={16} /> View Lineage Graph
          </button>
        )}
      </div>

      {/* Upstream Direct Sources Banner */}
      {object.source_objects.length > 0 && (
        <div
          style={{
            padding: '12px 16px',
            background: 'rgba(56, 189, 248, 0.05)',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flexWrap: 'wrap',
          }}
        >
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={16} /> Direct Upstream Sources:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {object.source_objects.map((src) => (
              <button
                key={src}
                onClick={() => onNavigateToObject && onNavigateToObject(src)}
                className="btn-secondary"
                style={{ padding: '3px 8px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
              >
                {src} <ExternalLink size={12} style={{ marginLeft: '4px' }} />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', display: 'flex', gap: '8px' }}>
        <button
          onClick={() => setActiveTab('fields')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'fields' ? '2px solid var(--accent-cyan)' : '2px solid transparent',
            color: activeTab === 'fields' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            padding: '10px 16px',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Columns size={16} /> Fields ({object.fields.length})
        </button>

        <button
          onClick={() => setActiveTab('associations')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'associations' ? '2px solid var(--accent-cyan)' : '2px solid transparent',
            color: activeTab === 'associations' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            padding: '10px 16px',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <LinkIcon size={16} /> Associations ({object.associations.length})
        </button>

        {object.hierarchies && object.hierarchies.length > 0 && (
          <button
            onClick={() => setActiveTab('hierarchies')}
            style={{
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'hierarchies' ? '2px solid var(--accent-cyan)' : '2px solid transparent',
              color: activeTab === 'hierarchies' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              padding: '10px 16px',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <FolderTree size={16} /> Hierarchies ({object.hierarchies.length})
          </button>
        )}
      </div>

      {/* Tab 1: Fields Table */}
      {activeTab === 'fields' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Search fields by name or label..."
              value={fieldSearch}
              onChange={(e) => setFieldSearch(e.target.value)}
              style={{
                width: '320px',
                padding: '6px 12px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '0.825rem',
                outline: 'none',
              }}
            />
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Showing {filteredFields.length} of {object.fields.length} fields
            </div>
          </div>

          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Field Name</th>
                  <th>Label</th>
                  <th>Data Type</th>
                  <th>Key</th>
                  <th>Measure</th>
                  <th>Aggregation</th>
                  <th>Association / Ref</th>
                </tr>
              </thead>
              <tbody>
                {filteredFields.map((field) => (
                  <tr key={field.name}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                      {field.name}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{field.label || '-'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {field.type || field.native_type || '-'}
                    </td>
                    <td>
                      {field.key ? (
                        <span className="badge badge-key">
                          <Key size={10} /> Key
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>No</span>
                      )}
                    </td>
                    <td>
                      {field.is_measure ? (
                        <span className="badge badge-measure">
                          <BarChart3 size={10} /> Measure
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Dimension</span>
                      )}
                    </td>
                    <td>
                      {field.aggregation ? (
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 600,
                            color: 'var(--accent-emerald)',
                            background: 'rgba(16, 185, 129, 0.1)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                          }}
                        >
                          {field.aggregation}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {field.foreign_key_association ? (
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-purple)' }}>
                          FK: {field.foreign_key_association}
                        </span>
                      ) : field.navigation_attribute_ref ? (
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>
                          Nav: {field.navigation_attribute_ref.join(' ➔ ')}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Associations Table */}
      {activeTab === 'associations' && (
        <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          {object.associations.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No associations defined for this object.
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Association Name</th>
                  <th>Target Entity</th>
                  <th>Relationship Type</th>
                  <th>Cardinality</th>
                  <th>Label</th>
                </tr>
              </thead>
              <tbody>
                {object.associations.map((assoc) => (
                  <tr key={assoc.name}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-purple)' }}>
                      {assoc.name}
                    </td>
                    <td>
                      <button
                        onClick={() => onNavigateToObject && onNavigateToObject(assoc.target)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--accent-cyan)',
                          fontFamily: 'var(--font-mono)',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          textDecoration: 'underline',
                        }}
                      >
                        {assoc.target} <ExternalLink size={12} />
                      </button>
                    </td>
                    <td>
                      <span className="badge badge-dim">{assoc.relationship_type}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{assoc.cardinality || '1..*'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{assoc.label || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab 3: Hierarchies */}
      {activeTab === 'hierarchies' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {object.hierarchies.map((h) => (
            <div
              key={h.name}
              style={{
                padding: '16px',
                borderRadius: '8px',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '8px' }}>
                {h.label || h.name}
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                {h.levels.map((lvl, idx) => (
                  <React.Fragment key={lvl}>
                    <div
                      style={{
                        padding: '6px 14px',
                        background: 'var(--bg-card)',
                        borderRadius: '6px',
                        border: '1px solid var(--border-strong)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                      }}
                    >
                      Level {idx + 1}: <span style={{ color: 'var(--accent-cyan)' }}>{lvl}</span>
                    </div>
                    {idx < h.levels.length - 1 && <span style={{ color: 'var(--text-muted)', fontSize: '1.2rem' }}>➔</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

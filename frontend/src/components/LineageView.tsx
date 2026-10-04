import React, { useState, useEffect } from 'react';
import {
  GitBranch,
  ArrowRight,
  AlertTriangle,
  Layers,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import { api } from '../services/api';
import type { ImpactResponse, LineageResponse } from '../types/metadata';
import { LoadingIndicator } from './LoadingIndicator';

interface Props {
  sessionId: string;
  objectName: string;
  onSelectObject: (name: string) => void;
}

export const LineageView: React.FC<Props> = ({ sessionId, objectName, onSelectObject }) => {
  const [viewMode, setViewMode] = useState<'lineage' | 'impact'>('lineage');
  const [loading, setLoading] = useState(false);
  const [lineage, setLineage] = useState<LineageResponse | null>(null);
  const [impact, setImpact] = useState<ImpactResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [linRes, impRes] = await Promise.all([
          api.getLineage(sessionId, objectName),
          api.getImpact(sessionId, objectName),
        ]);
        if (isMounted) {
          setLineage(linRes);
          setImpact(impRes);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Failed to load lineage graph.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();
    return () => {
      isMounted = false;
    };
  }, [sessionId, objectName]);

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <span className="badge badge-severity-critical">🔴 Critical Impact</span>;
      case 'HIGH':
        return <span className="badge badge-severity-high">🟠 High Impact</span>;
      case 'MEDIUM':
        return <span className="badge badge-severity-medium">🟡 Medium Impact</span>;
      default:
        return <span className="badge badge-severity-low">🟢 Low Impact</span>;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header and Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitBranch size={22} color="var(--accent-cyan)" />
            Lineage & Impact Analysis
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Inspecting entity: <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{objectName}</span>
          </p>
        </div>

        <div style={{ display: 'flex', background: 'var(--bg-input)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => setViewMode('lineage')}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              border: 'none',
              background: viewMode === 'lineage' ? 'var(--accent-blue)' : 'transparent',
              color: viewMode === 'lineage' ? '#fff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.825rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Layers size={14} /> Lineage Flow
          </button>
          <button
            onClick={() => setViewMode('impact')}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              border: 'none',
              background: viewMode === 'impact' ? 'var(--accent-amber)' : 'transparent',
              color: viewMode === 'impact' ? '#000' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.825rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <AlertTriangle size={14} /> Impact Analysis
          </button>
        </div>
      </div>

      {loading && <LoadingIndicator message="Computing graph traversal & dependencies..." />}

      {error && (
        <div style={{ padding: '16px', borderRadius: '8px', background: 'rgba(244, 63, 94, 0.1)', color: '#fda4af' }}>
          {error}
        </div>
      )}

      {/* LINEAGE FLOW VIEW */}
      {!loading && viewMode === 'lineage' && lineage && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr auto 1fr',
              gap: '12px',
              alignItems: 'center',
              padding: '20px 0',
              overflowX: 'auto',
            }}
          >
            {/* Column 1: Upstream Dependencies */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                ⬆️ Upstream Sources ({lineage.upstream.length})
              </div>
              {lineage.upstream.length === 0 ? (
                <div style={{ padding: '14px', borderRadius: '8px', background: 'var(--bg-surface)', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  Root entity (No upstream dependencies)
                </div>
              ) : (
                lineage.upstream.map((u) => (
                  <div
                    key={u}
                    onClick={() => onSelectObject(u)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '8px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-strong)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
                  >
                    <div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600 }}>{u}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Source Dependency</div>
                    </div>
                    <ExternalLink size={14} color="var(--text-muted)" />
                  </div>
                ))
              )}
            </div>

            {/* Arrow 1 */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <ArrowRight size={24} color="var(--accent-cyan)" />
            </div>

            {/* Column 2: Current Selected Focus Object */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                🎯 Focus Object
              </div>
              <div
                style={{
                  padding: '18px 20px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(59, 130, 246, 0.2))',
                  border: '2px solid var(--accent-cyan)',
                  boxShadow: '0 0 24px rgba(56, 189, 248, 0.2)',
                }}
              >
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                  {objectName}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: '4px' }}>
                  Currently Selected in CSN Model
                </div>
                <div style={{ display: 'flex', gap: '6px', marginTop: '10px' }}>
                  <span className="badge badge-cube">Target Object</span>
                </div>
              </div>
            </div>

            {/* Arrow 2 */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <ArrowRight size={24} color="var(--accent-purple)" />
            </div>

            {/* Column 3: Downstream Consumers */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                ⬇️ Downstream Consumers ({lineage.downstream.length})
              </div>
              {lineage.downstream.length === 0 ? (
                <div style={{ padding: '14px', borderRadius: '8px', background: 'var(--bg-surface)', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  Top-level consumer (No downstream dependents)
                </div>
              ) : (
                lineage.downstream.map((d) => (
                  <div
                    key={d}
                    onClick={() => onSelectObject(d)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '8px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-strong)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-purple)')}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
                  >
                    <div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600 }}>{d}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Dependent Consumer</div>
                    </div>
                    <ExternalLink size={14} color="var(--text-muted)" />
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Subgraph Edge Summary Table */}
          {lineage.edges.length > 0 && (
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
              <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Extracted Subgraph Relationships ({lineage.edges.length} edges)
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {lineage.edges.map((e, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '6px 12px',
                      background: 'var(--bg-surface)',
                      borderRadius: '6px',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.775rem',
                      fontFamily: 'var(--font-mono)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <span>{e.source}</span>
                    <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>➔ [{e.relationship_type}]</span>
                    <span>{e.target}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* IMPACT ANALYSIS VIEW */}
      {!loading && viewMode === 'impact' && impact && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Summary Box */}
          <div
            style={{
              padding: '20px',
              borderRadius: '12px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-strong)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldAlert size={24} color="var(--accent-amber)" />
                <h4 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Change Impact Assessment</h4>
              </div>
              {getSeverityBadge(impact.severity)}
            </div>

            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
              {impact.details.map((det, i) => (
                <p key={i} style={{ marginBottom: '4px' }}>
                  • {det}
                </p>
              ))}
            </div>
          </div>

          {/* Grid of affected dependents */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {/* Direct Dependents */}
            <div
              style={{
                padding: '16px',
                borderRadius: '8px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-amber)', marginBottom: '10px' }}>
                Direct Dependents ({impact.direct_dependents.length})
              </div>
              {impact.direct_dependents.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>None. Object can be modified safely.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {impact.direct_dependents.map((dep) => (
                    <div
                      key={dep}
                      onClick={() => onSelectObject(dep)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-strong)',
                        cursor: 'pointer',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.825rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span>{dep}</span>
                      <ExternalLink size={12} color="var(--accent-amber)" />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* All Transitive Downstream Affected */}
            <div
              style={{
                padding: '16px',
                borderRadius: '8px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-rose)', marginBottom: '10px' }}>
                Total Downstream Impacted ({impact.downstream_dependents.length})
              </div>
              {impact.downstream_dependents.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No downstream models impacted.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {impact.downstream_dependents.map((dep) => (
                    <div
                      key={dep}
                      onClick={() => onSelectObject(dep)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-strong)',
                        cursor: 'pointer',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.825rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span>{dep}</span>
                      <ExternalLink size={12} color="var(--accent-rose)" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import {
  Database,
  GitBranch,
  MessageSquare,
  Upload,
  LayoutDashboard,
  Sparkles,
  Info,
} from 'lucide-react';
import { FileUpload } from './components/FileUpload';
import { Dashboard } from './components/Dashboard';
import { ObjectList } from './components/ObjectList';
import { ObjectDetails } from './components/ObjectDetails';
import { LineageView } from './components/LineageView';
import { ChatPanel } from './components/ChatPanel';
import { api } from './services/api';
import type { ObjectMetadata, ParsedCSN, UploadResponse } from './types/metadata';

export const App: React.FC = () => {
  const [activeSession, setActiveSession] = useState<UploadResponse | null>(null);
  const [metadata, setMetadata] = useState<ParsedCSN | null>(null);
  const [selectedObject, setSelectedObject] = useState<ObjectMetadata | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'lineage' | 'chat'>('overview');
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);

  const handleUploadSuccess = async (uploadRes: UploadResponse) => {
    setActiveSession(uploadRes);
    setShowUploadModal(false);
    try {
      const fullMeta = await api.getMetadata(uploadRes.session_id);
      setMetadata(fullMeta);
      if (fullMeta.objects.length > 0) {
        // Find analytic cube if present, or first object
        const defaultObj =
          fullMeta.objects.find((o) => o.modeling_pattern === 'ANALYTICAL_CUBE') ||
          fullMeta.objects[0];
        setSelectedObject(defaultObj);
      }
    } catch (err) {
      console.error('Failed to fetch parsed metadata:', err);
    }
  };

  const handleNavigateToObject = (objectName: string) => {
    if (!metadata) return;
    const target = metadata.objects.find((o) => o.name === objectName);
    if (target) {
      setSelectedObject(target);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          height: '64px',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(9, 13, 22, 0.85)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #0284c7, #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              boxShadow: '0 0 16px rgba(56, 189, 248, 0.3)',
            }}
          >
            <Database size={20} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
              SAP Datasphere Metadata & Lineage Agent
            </h1>
            <p style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
              Deterministic CSN Parser • In-Memory Graph • LangGraph Copilot
            </p>
          </div>
        </div>

        {/* View Switcher Tabs (when CSN loaded) */}
        {activeSession && (
          <div
            style={{
              display: 'flex',
              background: 'var(--bg-input)',
              padding: '4px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <button
              onClick={() => setActiveTab('overview')}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                background: activeTab === 'overview' ? 'var(--accent-blue)' : 'transparent',
                color: activeTab === 'overview' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.825rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <LayoutDashboard size={15} /> Overview & Metadata
            </button>

            <button
              onClick={() => setActiveTab('lineage')}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                background: activeTab === 'lineage' ? 'var(--accent-blue)' : 'transparent',
                color: activeTab === 'lineage' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.825rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <GitBranch size={15} /> Lineage & Impact
            </button>

            <button
              onClick={() => setActiveTab('chat')}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                background: activeTab === 'chat' ? 'var(--accent-blue)' : 'transparent',
                color: activeTab === 'chat' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600,
                fontSize: '0.825rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <MessageSquare size={15} /> AI Copilot
            </button>
          </div>
        )}

        {/* Right action button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {activeSession ? (
            <button className="btn-secondary" onClick={() => setShowUploadModal(true)} style={{ fontSize: '0.825rem' }}>
              <Upload size={14} /> Upload Different CSN
            </button>
          ) : (
            <span className="badge badge-dim">MVP v1.0.0</span>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main style={{ flex: 1, padding: '24px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
        {!activeSession || showUploadModal ? (
          /* Initial Landing / Upload View */
          <div style={{ maxWidth: '800px', margin: '40px auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ textAlign: 'center', marginBottom: '12px' }}>
              <span className="badge badge-cube" style={{ marginBottom: '12px' }}>
                <Sparkles size={12} /> Production Quality MVP
              </span>
              <h2 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', marginTop: '8px' }}>
                Datasphere Metadata & Lineage Engine
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginTop: '8px', lineHeight: 1.6 }}>
                Deterministically extract entities, dimensions, analytical cubes, measures, associations,
                and dependencies from SAP Datasphere CSN/JSON files — and query them through a LangGraph agent.
              </p>
            </div>

            <FileUpload onUploadSuccess={handleUploadSuccess} activeUpload={activeSession} />

            {/* Architecture Explainer Card */}
            <div
              className="glass-panel"
              style={{
                padding: '20px',
                background: 'rgba(15, 23, 42, 0.6)',
                borderLeft: '4px solid var(--accent-cyan)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Info size={18} color="var(--accent-cyan)" />
                <h4 style={{ fontWeight: 600, fontSize: '0.95rem' }}>Architectural Principle</h4>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                The raw CSN is <strong>never</strong> passed directly into the LLM context. Python deterministically
                parses the CSN, constructs an in-memory directed metadata graph, and computes lineage and impact
                analysis. The LangGraph agent uses deterministic tools to query this graph, ensuring zero hallucination.
              </p>
            </div>
          </div>
        ) : (
          /* Active Session Workspace */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Dashboard Overview */}
            {metadata && <Dashboard metadata={metadata} />}

            {/* Content Area Based on Tab */}
            {activeTab === 'overview' && metadata && (
              <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '20px', alignItems: 'start' }}>
                {/* Left Object List */}
                <div style={{ height: 'calc(100vh - 280px)', minHeight: '550px' }}>
                  <ObjectList
                    objects={metadata.objects}
                    selectedObject={selectedObject}
                    onSelectObject={(obj) => setSelectedObject(obj)}
                  />
                </div>

                {/* Right Object Details */}
                <div>
                  {selectedObject ? (
                    <ObjectDetails
                      object={selectedObject}
                      onNavigateToObject={handleNavigateToObject}
                      onViewLineage={() => setActiveTab('lineage')}
                    />
                  ) : (
                    <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      Select an object from the left sidebar to view its fields, measures, and associations.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Lineage Tab */}
            {activeTab === 'lineage' && metadata && selectedObject && (
              <LineageView
                sessionId={activeSession.session_id}
                objectName={selectedObject.name}
                onSelectObject={handleNavigateToObject}
              />
            )}

            {/* Chat Tab */}
            {activeTab === 'chat' && (
              <div style={{ maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
                <ChatPanel
                  sessionId={activeSession.session_id}
                  selectedObjectName={selectedObject?.name}
                />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default App;

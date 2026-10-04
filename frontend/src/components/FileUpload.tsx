import React, { useState, useRef } from 'react';
import { UploadCloud, FileJson, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import type { UploadResponse } from '../types/metadata';
import { LoadingIndicator } from './LoadingIndicator';

interface Props {
  onUploadSuccess: (data: UploadResponse) => void;
  activeUpload?: UploadResponse | null;
}

export const FileUpload: React.FC<Props> = ({ onUploadSuccess, activeUpload }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileProcess = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.json')) {
      setError('Please upload a valid JSON/CSN file (.json).');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.uploadCSN(file);
      onUploadSuccess(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to parse CSN file.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  const handleQuickLoad = async (type: 'sample' | 'full') => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.loadSample(type);
      onUploadSuccess(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load sample CSN.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: isDragging ? '2px dashed var(--accent-cyan)' : '2px dashed var(--border-strong)',
          borderRadius: '12px',
          padding: '32px 20px',
          textAlign: 'center',
          background: isDragging ? 'rgba(56, 189, 248, 0.05)' : 'rgba(17, 24, 39, 0.5)',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileProcess(e.target.files[0]);
            }
          }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(56, 189, 248, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)',
            }}
          >
            <UploadCloud size={28} />
          </div>

          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Upload SAP Datasphere CSN
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Drag and drop your CSN .json file here, or click to browse
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span className="badge badge-entity">
              <FileJson size={12} /> .JSON / CSN 2.0
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Up to 50 MB
            </span>
          </div>
        </div>
      </div>

      {/* Quick Load Buttons for Instant MVP Testing */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Quick load test data:
        </span>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            onClick={(e) => {
              e.stopPropagation();
              handleQuickLoad('sample');
            }}
            disabled={loading}
          >
            <Sparkles size={14} color="var(--accent-cyan)" />
            Load Sample CSN
          </button>

          <button
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            onClick={(e) => {
              e.stopPropagation();
              handleQuickLoad('full');
            }}
            disabled={loading}
          >
            <Sparkles size={14} color="var(--accent-purple)" />
            Load Full 1.2MB CSN
          </button>
        </div>
      </div>

      {loading && <LoadingIndicator message="Parsing CSN deterministically & generating metadata graph..." />}

      {error && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fda4af',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.875rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Success Summary */}
      {activeUpload && !loading && (
        <div
          className="glass-panel"
          style={{
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            borderLeft: '4px solid var(--accent-emerald)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} color="var(--accent-emerald)" />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{activeUpload.filename}</span>
            </div>
            <span className="badge badge-measure">Active Session</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '8px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-subtle)',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Objects</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {activeUpload.object_count}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Relationships</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {activeUpload.relationship_count}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fields</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
                {activeUpload.field_count}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Measures</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                {activeUpload.measure_count}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

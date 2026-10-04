import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingIndicator: React.FC<Props> = ({ message = 'Processing...', size = 'md' }) => {
  const sizeMap = {
    sm: 16,
    md: 24,
    lg: 36,
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '16px' }}>
      <Loader2
        size={sizeMap[size]}
        style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-cyan)' }}
      />
      {message && <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{message}</span>}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

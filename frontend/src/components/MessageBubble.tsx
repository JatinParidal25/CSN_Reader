import React from 'react';
import { Bot, User, Wrench } from 'lucide-react';
import type { ChatMessage } from '../types/metadata';

interface Props {
  message: ChatMessage;
}

export const MessageBubble: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';

  // Helper to format basic markdown tables, code, and bold text cleanly
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    let inTable = false;
    let tableRows: string[][] = [];

    const elements: React.ReactNode[] = [];

    lines.forEach((line, idx) => {
      // Check for table divider
      if (line.trim().startsWith('|') && line.includes('---')) {
        inTable = true;
        return;
      }

      // Check for table row
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        const cells = line
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim());
        tableRows.push(cells);
        return;
      }

      // Flush table if we were in table and hit non-table line
      if (inTable && tableRows.length > 0) {
        const header = tableRows[0];
        const body = tableRows.slice(1);
        elements.push(
          <div key={`table-${idx}`} style={{ overflowX: 'auto', margin: '10px 0' }}>
            <table className="data-table">
              <thead>
                <tr>
                  {header.map((h, i) => (
                    <th key={i}>{h.replace(/\*\*/g, '')}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {row.map((cell, cIdx) => (
                      <td key={cIdx}>{cell.replace(/\*\*/g, '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        inTable = false;
        tableRows = [];
      }

      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={idx} style={{ color: 'var(--accent-cyan)', margin: '10px 0 6px 0', fontSize: '1rem', fontWeight: 600 }}>
            {line.replace('### ', '')}
          </h3>
        );
        return;
      }
      if (line.startsWith('#### ')) {
        elements.push(
          <h4 key={idx} style={{ color: 'var(--text-primary)', margin: '8px 0 4px 0', fontSize: '0.9rem', fontWeight: 600 }}>
            {line.replace('#### ', '')}
          </h4>
        );
        return;
      }

      // Bullet points
      if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
        elements.push(
          <div key={idx} style={{ display: 'flex', gap: '8px', marginLeft: '8px', marginBottom: '4px' }}>
            <span style={{ color: 'var(--accent-cyan)' }}>•</span>
            <span>{line.replace(/^[-•]\s*/, '')}</span>
          </div>
        );
        return;
      }

      if (line.trim()) {
        elements.push(
          <p key={idx} style={{ marginBottom: '6px' }}>
            {line}
          </p>
        );
      }
    });

    // Flush any trailing table
    if (tableRows.length > 0) {
      const header = tableRows[0];
      const body = tableRows.slice(1);
      elements.push(
        <div key="table-end" style={{ overflowX: 'auto', margin: '10px 0' }}>
          <table className="data-table">
            <thead>
              <tr>
                {header.map((h, i) => (
                  <th key={i}>{h.replace(/\*\*/g, '')}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx}>{cell.replace(/\*\*/g, '')}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return elements;
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-start',
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}
    >
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: isUser ? 'var(--accent-blue)' : 'rgba(56, 189, 248, 0.15)',
          color: isUser ? '#fff' : 'var(--accent-cyan)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div
        style={{
          maxWidth: '85%',
          background: isUser ? 'var(--accent-blue)' : 'var(--bg-card)',
          color: isUser ? '#ffffff' : 'var(--text-primary)',
          borderRadius: '12px',
          padding: '12px 16px',
          border: isUser ? 'none' : '1px solid var(--border-subtle)',
          boxShadow: isUser ? '0 4px 12px rgba(37, 99, 235, 0.25)' : 'none',
        }}
      >
        {/* Tools Used Badge */}
        {!isUser && message.tools_used && message.tools_used.length > 0 && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '2px 8px',
              borderRadius: '4px',
              background: 'rgba(56, 189, 248, 0.1)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              fontSize: '0.725rem',
              color: 'var(--accent-cyan)',
              fontFamily: 'var(--font-mono)',
              marginBottom: '8px',
            }}
          >
            <Wrench size={12} />
            <span>Tools used: {message.tools_used.join(', ')}</span>
          </div>
        )}

        <div className="markdown-body" style={{ color: isUser ? '#ffffff' : 'var(--text-primary)' }}>
          {isUser ? message.content : renderFormattedContent(message.content)}
        </div>

        <div
          style={{
            fontSize: '0.7rem',
            color: isUser ? 'rgba(255, 255, 255, 0.7)' : 'var(--text-muted)',
            marginTop: '6px',
            textAlign: isUser ? 'right' : 'left',
          }}
        >
          {message.timestamp}
        </div>
      </div>
    </div>
  );
};

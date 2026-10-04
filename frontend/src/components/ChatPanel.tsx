import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, Sparkles, MessageSquare } from 'lucide-react';
import { api } from '../services/api';
import type { ChatMessage } from '../types/metadata';
import { LoadingIndicator } from './LoadingIndicator';
import { MessageBubble } from './MessageBubble';

interface Props {
  sessionId: string | null;
  selectedObjectName?: string | null;
}

export const ChatPanel: React.FC<Props> = ({ sessionId, selectedObjectName }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const samplePrompts = [
    'Show me all objects',
    selectedObjectName
      ? `Explain ${selectedObjectName}`
      : 'Explain Current_Month_OI_Analytic_Model',
    selectedObjectName
      ? `What is the lineage of ${selectedObjectName}?`
      : 'What is the lineage of Current_Month_OI_Analytic_Model?',
    'What is NETWR?',
    'What depends on Time_table_heirarchy?',
    'What could be affected if Time_table_heirarchy changes?',
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || !sessionId || loading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.chat(sessionId, query);
      const botMsg: ChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response.answer,
        tools_used: response.tools_used,
        sources: response.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const botErrorMsg: ChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: `⚠️ Error processing query: ${err.response?.data?.detail || err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botErrorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: '520px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)',
            }}
          >
            <Bot size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Datasphere AI Copilot</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Deterministic Tool Retrieval + LLM Synthesis
            </p>
          </div>
        </div>

        {sessionId ? (
          <span className="badge badge-measure">Ready</span>
        ) : (
          <span className="badge badge-entity">Upload CSN to Activate</span>
        )}
      </div>

      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              margin: 'auto',
              maxWidth: '480px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
              color: 'var(--text-secondary)',
            }}
          >
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'rgba(56, 189, 248, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-cyan)',
              }}
            >
              <MessageSquare size={24} />
            </div>
            <h4 style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: 600 }}>
              Ask anything about your Datasphere CSN
            </h4>
            <p style={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
              The AI agent queries the deterministic metadata graph for objects, fields, measures,
              associations, and lineage — without hallucinations.
            </p>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}

        {loading && <LoadingIndicator message="LangGraph agent querying deterministic tools & synthesizing..." />}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Chips */}
      {sessionId && (
        <div
          style={{
            padding: '8px 16px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'rgba(15, 23, 42, 0.4)',
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
            whiteSpace: 'nowrap',
          }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Sparkles size={12} color="var(--accent-cyan)" /> Suggestions:
          </span>
          {samplePrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleSend(prompt)}
              disabled={loading}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-strong)',
                color: 'var(--text-secondary)',
                borderRadius: '16px',
                padding: '4px 12px',
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-strong)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input box */}
      <div
        style={{
          padding: '16px',
          borderTop: '1px solid var(--border-subtle)',
          background: 'var(--bg-input)',
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '10px' }}
        >
          <input
            type="text"
            placeholder={
              sessionId
                ? 'Ask about your Datasphere metadata, lineage, measures, or impact...'
                : 'Please upload a CSN file above to start chatting...'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!sessionId || loading}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: '8px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-strong)',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={!sessionId || !input.trim() || loading}
            style={{
              opacity: !sessionId || !input.trim() || loading ? 0.5 : 1,
              cursor: !sessionId || !input.trim() || loading ? 'not-allowed' : 'pointer',
            }}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};

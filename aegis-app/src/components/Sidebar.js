import React from 'react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: '⬡ Overview' },
    { id: 'map', label: '◈ Forensic Map' },
    { id: 'registry', label: '▦ Asset Registry' },
    { id: 'console', label: '⟨/⟩ Schema Console' },
    { id: 'analysis', label: '⚡ Attack Vectors' },
    { id: 'shadowtrace', label: '⚔ ShadowTrace AI' }
  ];

  return (
    <div style={{ width: '220px', borderRight: '1px solid var(--border)', background: 'var(--bg2)', padding: '24px 0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          style={{
            background: activeTab === tab.id ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
            border: 'none',
            borderRight: activeTab === tab.id ? '3px solid var(--clean)' : '3px solid transparent',
            color: activeTab === tab.id ? 'var(--clean)' : 'var(--text-dim)',
            padding: '12px 24px',
            textAlign: 'left',
            fontFamily: 'Share Tech Mono',
            fontSize: '14px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            fontWeight: activeTab === tab.id ? 'bold' : 'normal',
            letterSpacing: '1px'
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

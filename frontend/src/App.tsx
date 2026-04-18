import React, { useState, useEffect, useRef } from 'react';
import { Authenticator, useAuthenticator } from '@aws-amplify/ui-react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { ReactFlow, MiniMap, Controls, Background, useNodesState, useEdgesState } from '@xyflow/react';
import { Send, RefreshCw, Activity, Terminal } from 'lucide-react';

const initialNodes = [
  { id: '1', position: { x: 50, y: 50 }, data: { label: 'User Intent' }, style: { background: '#1d1d20', color: '#fff', border: '1px solid #3b82f6', borderRadius: '8px' } },
  { id: '2', position: { x: 50, y: 150 }, data: { label: 'Planner Agent' }, style: { background: '#1d1d20', color: '#fff', border: '1px solid #27272a', borderRadius: '8px' } },
  { id: '3', position: { x: 50, y: 250 }, data: { label: 'Validator Agent' }, style: { background: '#1d1d20', color: '#fff', border: '1px solid #27272a', borderRadius: '8px' } },
  { id: '4', position: { x: 50, y: 350 }, data: { label: 'Executor Agent' }, style: { background: '#1d1d20', color: '#fff', border: '1px solid #27272a', borderRadius: '8px' } }
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: false },
  { id: 'e2-3', source: '2', target: '3', animated: false },
  { id: 'e3-4', source: '3', target: '4', animated: false },
];

function Dashboard() {
  const { user, signOut } = useAuthenticator((context) => [context.user]);
  const [prompt, setPrompt] = useState('');
  const [logs, setLogs] = useState<string[]>(['System: Connecting to DataPilot network...', 'System: Authorization verified.']);
  const [runs, setRuns] = useState<any[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const fireContextRun = async () => {
    if (!prompt.trim()) return;
    
    // Animate the flow diagram targeting the Executor
    setEdges(eds => eds.map(e => ({ ...e, animated: true, style: { stroke: '#3b82f6' } })));
    setNodes(nds => nds.map(n => n.id === '2' ? { ...n, style: { ...n.style, border: '1px solid #3b82f6' } } : n));
    
    setLogs(prev => [...prev, `User[${user.username}]: ${prompt}`]);
    setLogs(prev => [...prev, `System: Generating execution pipeline dynamically via LLM...`]);
    setPrompt('');
    
    // Optional: Get token explicitly
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.accessToken?.toString();
      // Normally we would POST to http://localhost:8000/pipeline here using the JWT
      // but without the backend running natively we simulate the visual response
      setTimeout(() => {
        setLogs(prev => [...prev, `Validator: Schema ok. Prechecks passed.`]);
        setNodes(nds => nds.map(n => n.id === '3' ? { ...n, style: { ...n.style, border: '1px solid #3b82f6' } } : n));
      }, 1000);
      
      setTimeout(() => {
        setLogs(prev => [...prev, `Executor: Commencing Extraction sequence...`]);
        setNodes(nds => nds.map(n => n.id === '4' ? { ...n, style: { ...n.style, border: '1px solid #3b82f6', boxShadow: '0 0 15px rgba(59, 130, 246, 0.4)' } } : n));
        setRuns([{ id: 'pl-9f8x7', status: 'done', rows: 430, time: '2.4s' }, ...runs]);
        setEdges(eds => eds.map(e => ({ ...e, animated: false, style: { stroke: '#27272a' } })));
      }, 2500);
    } catch (e) {
      console.error(e);
      setLogs(prev => [...prev, `Error: Failed to fetch JWT Authorization. Are you verified?`]);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Left Sidebar */}
      <div className="sidebar">
        <div className="panel chat-panel">
          <div className="chat-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>DataPilot</span>
            <button onClick={signOut} style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)' }}>
              Sign out {user.username}
            </button>
          </div>
          
          <div className="log-panel">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#60a5fa' }}>
               <Terminal size={16} /> Live Data Stream
            </div>
            {logs.map((L, i) => (
              <div key={i} className="log-entry">
                <span style={{ color: '#3b82f6' }}>{new Date().toISOString().split('T')[1].slice(0, 8)}</span> &gt; {L}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>

          <div className="input-area">
            <input 
              type="text" 
              placeholder="E.g., Extract input.csv to users table..." 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fireContextRun()}
            />
            <button onClick={fireContextRun}><Send size={18} /></button>
          </div>
        </div>
      </div>

      {/* Main Area */}
      <div className="main-area">
        <div className="panel flow-panel">
          <ReactFlow 
            nodes={nodes} 
            edges={edges} 
            onNodesChange={onNodesChange} 
            onEdgesChange={onEdgesChange} 
            fitView
            colorMode="dark"
          >
            <Controls />
            <MiniMap />
            <Background gap={12} size={1} />
          </ReactFlow>
        </div>
        
        <div className="panel history-panel">
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={20} /> Pipeline Execution History
          </h3>
          {runs.map((r, i) => (
            <div key={i} className="run-card">
              <div>
                <strong>Pipeline {r.id}</strong>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                  Processed {r.rows} rows in {r.time}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className={`status-badge status-${r.status}`}>{r.status}</span>
                {r.status === 'failed' && (
                  <button className="retry-btn"><RefreshCw size={14} /></button>
                )}
              </div>
            </div>
          ))}
          {runs.length === 0 && <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No pipelines ran in this session.</div>}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Authenticator hideSignUp>
      <Dashboard />
    </Authenticator>
  );
}

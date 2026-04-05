import React, { useState, useEffect, useCallback, useRef } from 'react';
import './OracleView.css';

const API = process.env.REACT_APP_BACKEND_URL;

const OracleView = ({ token }) => {
  const [dashboard, setDashboard] = useState(null);
  const [health, setHealth] = useState(null);
  const [agents, setAgents] = useState(null);
  const [queue, setQueue] = useState([]);
  const [brain, setBrain] = useState([]);
  const [brainQuery, setBrainQuery] = useState('');
  const [tasks, setTasks] = useState([]);
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [agentInvoke, setAgentInvoke] = useState({ agent: '', message: '', result: null, loading: false });
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 5, task_type: 'general' });
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const loadDashboard = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/api/admin/oracle/dashboard`, { headers });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setDashboard(data);
      setQueue(data.queue || []);
      setError(null);
    } catch (e) { setError(e.message); }
  }, [token]); // eslint-disable-line

  const loadHealth = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/api/admin/oracle/health`, { headers });
      if (resp.ok) setHealth(await resp.json());
    } catch (e) { /* silent */ }
  }, [token]); // eslint-disable-line

  const loadAgents = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/api/admin/oracle/agents`, { headers });
      if (resp.ok) setAgents(await resp.json());
    } catch (e) { /* silent */ }
  }, [token]); // eslint-disable-line

  const loadTasks = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/api/admin/oracle/tasks?limit=50`, { headers });
      if (resp.ok) {
        const d = await resp.json();
        setTasks(d.tasks || []);
      }
    } catch (e) { /* silent */ }
  }, [token]); // eslint-disable-line

  const searchBrain = useCallback(async (q) => {
    try {
      const url = q ? `${API}/api/admin/oracle/brain?q=${encodeURIComponent(q)}&limit=20` : `${API}/api/admin/oracle/brain?limit=20`;
      const resp = await fetch(url, { headers });
      if (resp.ok) {
        const d = await resp.json();
        setBrain(d.notes || []);
      }
    } catch (e) { /* silent */ }
  }, [token]); // eslint-disable-line

  const invokeAgent = async () => {
    if (!agentInvoke.agent || !agentInvoke.message) return;
    setAgentInvoke(prev => ({ ...prev, loading: true, result: null }));
    try {
      const resp = await fetch(`${API}/api/admin/oracle/invoke-agent`, {
        method: 'POST', headers,
        body: JSON.stringify({ agent_name: agentInvoke.agent, message: agentInvoke.message, use_brain: true })
      });
      const data = await resp.json();
      setAgentInvoke(prev => ({ ...prev, loading: false, result: data }));
    } catch (e) {
      setAgentInvoke(prev => ({ ...prev, loading: false, result: { error: e.message } }));
    }
  };

  const createTask = async () => {
    if (!newTask.title) return;
    setLoading(true);
    try {
      const resp = await fetch(`${API}/api/admin/oracle/tasks`, {
        method: 'POST', headers,
        body: JSON.stringify(newTask)
      });
      if (resp.ok) {
        setNewTask({ title: '', description: '', priority: 5, task_type: 'general' });
        loadDashboard();
      }
    } catch (e) { /* silent */ }
    setLoading(false);
  };

  useEffect(() => {
    loadDashboard();
    loadHealth();
    intervalRef.current = setInterval(loadDashboard, 30000);
    return () => clearInterval(intervalRef.current);
  }, [loadDashboard, loadHealth]);

  useEffect(() => {
    if (tab === 'agents') loadAgents();
    if (tab === 'tasks') loadTasks();
    if (tab === 'brain') searchBrain('');
  }, [tab, loadAgents, loadTasks, searchBrain]);

  const counts = dashboard?.counts || {};
  const oStatus = dashboard?.oracle_status || {};

  return (
    <div className="ora-container" data-testid="oracle-view">
      {/* Header */}
      <div className="ora-header" data-testid="oracle-header">
        <div className="ora-header-left">
          <span className="ora-icon material-symbols-outlined">hub</span>
          <div>
            <h2 className="ora-title">Oracle Command Center</h2>
            <p className="ora-subtitle">Supabase + DeepSeek + Brain — Live-Daten</p>
          </div>
        </div>
        <div className="ora-health-pills">
          <span className={`ora-pill ${health?.supabase?.connected ? 'ora-pill--ok' : 'ora-pill--err'}`} data-testid="oracle-supabase-status">
            <span className="ora-pill-dot" /> Supabase
          </span>
          <span className={`ora-pill ${health?.deepseek?.connected ? 'ora-pill--ok' : 'ora-pill--err'}`} data-testid="oracle-deepseek-status">
            <span className="ora-pill-dot" /> DeepSeek
          </span>
        </div>
      </div>

      {error && <div className="ora-error">Verbindungsfehler: {error}</div>}

      {/* Tabs */}
      <div className="ora-tabs" data-testid="oracle-tabs">
        {[
          { id: 'overview', label: 'Übersicht', icon: 'dashboard' },
          { id: 'queue', label: 'Task-Queue', icon: 'queue' },
          { id: 'agents', label: 'Agenten', icon: 'smart_toy' },
          { id: 'brain', label: 'Brain', icon: 'neurology' },
          { id: 'tasks', label: 'Oracle-Tasks', icon: 'task_alt' },
          { id: 'invoke', label: 'Agent aufrufen', icon: 'play_arrow' },
        ].map(t => (
          <button key={t.id} className={`ora-tab ${tab === t.id ? 'ora-tab--active' : ''}`} onClick={() => setTab(t.id)} data-testid={`oracle-tab-${t.id}`}>
            <span className="material-symbols-outlined">{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* ═══ OVERVIEW ═══ */}
      {tab === 'overview' && (
        <div className="ora-grid" data-testid="oracle-overview">
          <StatCard icon="description" label="Brain-Notes" value={counts.brain_notes} color="#8b5cf6" />
          <StatCard icon="school" label="Knowledge" value={counts.knowledge_entries} color="#06b6d4" />
          <StatCard icon="memory" label="Memory" value={counts.memory_entries} color="#f59e0b" />
          <StatCard icon="smart_toy" label="AI-Agenten" value={counts.ai_agents} color="#10b981" />
          <StatCard icon="task_alt" label="Oracle-Tasks" value={counts.oracle_tasks_total} color="#ef4444" />
          <StatCard icon="verified" label="Audit-Logs" value={counts.audit_logs} color="#6366f1" />

          <div className="ora-card ora-card--wide" data-testid="oracle-status-card">
            <h3 className="ora-card-title"><span className="material-symbols-outlined">monitoring</span> Oracle-Status</h3>
            <div className="ora-status-grid">
              <StatusItem label="Pending" value={oStatus.pending} color="#f59e0b" />
              <StatusItem label="Running" value={oStatus.running} color="#06b6d4" />
              <StatusItem label="Completed (24h)" value={oStatus.completed_24h} color="#10b981" />
              <StatusItem label="Failed" value={oStatus.failed} color="#ef4444" />
              <StatusItem label="Knowledge" value={oStatus.knowledge_entries} color="#8b5cf6" />
              <StatusItem label="Unverarbeitet" value={oStatus.unprocessed_knowledge_tasks} color="#94a3b8" />
            </div>
          </div>

          <div className="ora-card ora-card--wide" data-testid="oracle-queue-preview">
            <h3 className="ora-card-title"><span className="material-symbols-outlined">queue</span> Aktive Queue ({queue.length})</h3>
            <div className="ora-queue-list">
              {queue.slice(0, 8).map(q => (
                <div key={q.id} className="ora-queue-item">
                  <span className={`ora-queue-badge ora-queue-badge--${q.status}`}>{q.status}</span>
                  <span className="ora-queue-type">{q.type}</span>
                  <span className="ora-queue-agent">{q.owner_agent || '-'}</span>
                  <span className="ora-queue-pri">P{q.priority}</span>
                </div>
              ))}
              {queue.length === 0 && <p className="ora-empty">Keine aktiven Queue-Einträge</p>}
            </div>
          </div>
        </div>
      )}

      {/* ═══ QUEUE ═══ */}
      {tab === 'queue' && (
        <div className="ora-section" data-testid="oracle-queue-section">
          <div className="ora-section-header">
            <h3>Task-Queue ({dashboard?.queue_pending} pending, {dashboard?.queue_running} running)</h3>
            <button className="ora-btn-sm" onClick={loadDashboard} data-testid="oracle-queue-refresh">
              <span className="material-symbols-outlined">refresh</span>
            </button>
          </div>
          <div className="ora-table-wrap">
            <table className="ora-table" data-testid="oracle-queue-table">
              <thead>
                <tr><th>Typ</th><th>Status</th><th>Agent</th><th>Erstellt</th><th>Tags</th><th>P</th></tr>
              </thead>
              <tbody>
                {queue.map(q => (
                  <tr key={q.id}>
                    <td className="ora-cell-mono">{q.type}</td>
                    <td><span className={`ora-queue-badge ora-queue-badge--${q.status}`}>{q.status}</span></td>
                    <td>{q.owner_agent || '-'}</td>
                    <td className="ora-cell-date">{fmtDate(q.created_at)}</td>
                    <td>{(q.tags || []).join(', ')}</td>
                    <td className="ora-cell-pri">{q.priority}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══ AGENTS ═══ */}
      {tab === 'agents' && agents && (
        <div className="ora-section" data-testid="oracle-agents-section">
          <h3>Oracle-Agenten ({agents.oracle_agents?.length || 0})</h3>
          <div className="ora-agent-grid">
            {(agents.oracle_agents || []).map(a => (
              <div key={a.id} className="ora-agent-card" data-testid={`oracle-agent-${a.id}`}>
                <div className="ora-agent-top">
                  <span className={`ora-agent-dot ora-agent-dot--${a.status}`} />
                  <strong>{a.id || a.type}</strong>
                  <span className="ora-agent-type">{a.type}</span>
                </div>
                <div className="ora-agent-caps">{(a.capabilities || []).join(', ')}</div>
              </div>
            ))}
          </div>

          <h3 style={{marginTop: 24}}>AI-Agenten aus Supabase ({agents.ai_agents?.length || 0})</h3>
          <div className="ora-agent-grid">
            {(agents.ai_agents || []).map(a => (
              <div key={a.id} className="ora-agent-card" data-testid={`ai-agent-${a.name}`}>
                <div className="ora-agent-top">
                  <span className="ora-agent-avatar" style={{ background: a.avatar_color || '#333' }}>
                    {a.avatar_initials || a.name?.[0]}
                  </span>
                  <div>
                    <strong>{a.name}</strong>
                    <span className="ora-agent-role">{a.role}</span>
                  </div>
                  <span className={`ora-agent-dot ora-agent-dot--${a.status === 'online' ? 'active' : 'idle'}`} />
                </div>
                <p className="ora-agent-desc">{a.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ BRAIN ═══ */}
      {tab === 'brain' && (
        <div className="ora-section" data-testid="oracle-brain-section">
          <div className="ora-section-header">
            <h3>Brain-Notes ({counts.brain_notes})</h3>
            <div className="ora-search-bar">
              <input
                type="text"
                className="ora-search-input"
                placeholder="Brain durchsuchen..."
                value={brainQuery}
                onChange={e => setBrainQuery(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') searchBrain(brainQuery); }}
                data-testid="oracle-brain-search"
              />
              <button className="ora-btn-sm" onClick={() => searchBrain(brainQuery)} data-testid="oracle-brain-search-btn">
                <span className="material-symbols-outlined">search</span>
              </button>
            </div>
          </div>
          <div className="ora-brain-list">
            {brain.map(n => (
              <div key={n.id} className="ora-brain-card" data-testid={`brain-note-${n.id}`}>
                <div className="ora-brain-top">
                  <strong>{n.title}</strong>
                  <span className="ora-brain-type">{n.note_type}</span>
                </div>
                <p className="ora-brain-content">{n.content_preview}</p>
                <div className="ora-brain-tags">
                  {(n.tags || []).map(t => <span key={t} className="ora-tag">{t}</span>)}
                  <span className="ora-brain-date">{fmtDate(n.created_at)}</span>
                </div>
              </div>
            ))}
            {brain.length === 0 && <p className="ora-empty">Keine Brain-Notes gefunden</p>}
          </div>
        </div>
      )}

      {/* ═══ ORACLE TASKS ═══ */}
      {tab === 'tasks' && (
        <div className="ora-section" data-testid="oracle-tasks-section">
          <div className="ora-section-header">
            <h3>Oracle-Tasks ({tasks.length})</h3>
            <button className="ora-btn-sm" onClick={loadTasks}><span className="material-symbols-outlined">refresh</span></button>
          </div>

          <div className="ora-create-task" data-testid="oracle-create-task">
            <input className="ora-input" placeholder="Task-Titel..." value={newTask.title} onChange={e => setNewTask({ ...newTask, title: e.target.value })} data-testid="oracle-task-title" />
            <input className="ora-input" placeholder="Beschreibung..." value={newTask.description} onChange={e => setNewTask({ ...newTask, description: e.target.value })} data-testid="oracle-task-desc" />
            <select className="ora-select" value={newTask.task_type} onChange={e => setNewTask({ ...newTask, task_type: e.target.value })} data-testid="oracle-task-type">
              {['general','agent_task','user_request','project_task','system_task','improvement','monitoring','security','infrastructure','verification','optimization','deployment','configuration','data','crm','email','llm','kpi'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select className="ora-select" value={newTask.priority} onChange={e => setNewTask({ ...newTask, priority: parseInt(e.target.value) })} data-testid="oracle-task-priority">
              {[1,2,3,4,5,6,7,8,9,10].map(p => <option key={p} value={p}>P{p}</option>)}
            </select>
            <button className="ora-btn" onClick={createTask} disabled={loading || !newTask.title} data-testid="oracle-task-create-btn">Task erstellen</button>
          </div>

          <div className="ora-table-wrap">
            <table className="ora-table" data-testid="oracle-tasks-table">
              <thead>
                <tr><th>Titel</th><th>Typ</th><th>Status</th><th>Agent</th><th>P</th><th>Erstellt</th></tr>
              </thead>
              <tbody>
                {tasks.map(t => (
                  <tr key={t.id}>
                    <td>{t.title || t.description?.slice(0, 60) || '-'}</td>
                    <td className="ora-cell-mono">{t.type}</td>
                    <td><span className={`ora-queue-badge ora-queue-badge--${t.status}`}>{t.status}</span></td>
                    <td>{t.owner_agent || '-'}</td>
                    <td className="ora-cell-pri">{t.priority}</td>
                    <td className="ora-cell-date">{fmtDate(t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══ INVOKE AGENT ═══ */}
      {tab === 'invoke' && (
        <div className="ora-section" data-testid="oracle-invoke-section">
          <h3>DeepSeek-Agent aufrufen</h3>
          <div className="ora-invoke-form">
            <input className="ora-input" placeholder="Agent-Name (z.B. Strategist, Architect)..." value={agentInvoke.agent} onChange={e => setAgentInvoke({ ...agentInvoke, agent: e.target.value })} data-testid="oracle-invoke-agent" />
            <textarea className="ora-textarea" placeholder="Nachricht an den Agenten..." value={agentInvoke.message} onChange={e => setAgentInvoke({ ...agentInvoke, message: e.target.value })} rows={4} data-testid="oracle-invoke-message" />
            <button className="ora-btn" onClick={invokeAgent} disabled={agentInvoke.loading || !agentInvoke.agent || !agentInvoke.message} data-testid="oracle-invoke-btn">
              {agentInvoke.loading ? 'Agent arbeitet...' : 'Agent aufrufen'}
            </button>
          </div>
          {agentInvoke.result && (
            <div className={`ora-invoke-result ${agentInvoke.result.error ? 'ora-invoke-result--err' : ''}`} data-testid="oracle-invoke-result">
              {agentInvoke.result.error ? (
                <p>Fehler: {agentInvoke.result.error}</p>
              ) : (
                <>
                  <div className="ora-invoke-meta">
                    <span>Agent: <strong>{agentInvoke.result.agent}</strong></span>
                    <span>Rolle: {agentInvoke.result.role}</span>
                    <span>Modell: {agentInvoke.result.model}</span>
                  </div>
                  <div className="ora-invoke-text">{agentInvoke.result.response}</div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/* ── Sub-components ── */
const StatCard = ({ icon, label, value, color }) => (
  <div className="ora-stat" style={{ '--stat-color': color }}>
    <span className="material-symbols-outlined ora-stat-icon">{icon}</span>
    <div className="ora-stat-value">{value != null ? value.toLocaleString('de-DE') : '-'}</div>
    <div className="ora-stat-label">{label}</div>
  </div>
);

const StatusItem = ({ label, value, color }) => (
  <div className="ora-status-item">
    <span className="ora-status-val" style={{ color }}>{value ?? '-'}</span>
    <span className="ora-status-lbl">{label}</span>
  </div>
);

const fmtDate = (d) => {
  if (!d) return '-';
  try { return new Date(d).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' }); }
  catch { return d; }
};

export default OracleView;

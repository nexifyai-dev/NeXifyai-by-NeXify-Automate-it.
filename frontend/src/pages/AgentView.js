import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API = process.env.REACT_APP_BACKEND_URL || '';
const I = ({ n }) => <span className="material-symbols-outlined">{n}</span>;
const genAgentSid = () => `agent_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;

const AgentView = ({ headers, apiFetch }) => {
  /* ── State ── */
  const [activeTab, setActiveTab] = useState('chat');
  const [agentStatus, setAgentStatus] = useState(null);

  // Chat
  const [sessionId, setSessionId] = useState(() => genAgentSid());
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatBusy, setChatBusy] = useState(false);
  const chatEndRef = useRef(null);

  // Brain
  const [brainQuery, setBrainQuery] = useState('');
  const [brainResults, setBrainResults] = useState([]);
  const [brainBusy, setBrainBusy] = useState(false);
  const [brainStoreText, setBrainStoreText] = useState('');
  const [brainStoreLayer, setBrainStoreLayer] = useState('KNOWLEDGE');
  const [brainStoreBusy, setBrainStoreBusy] = useState(false);
  const [brainStoreMsg, setBrainStoreMsg] = useState('');
  const [brainMemories, setBrainMemories] = useState([]);
  const [brainListBusy, setBrainListBusy] = useState(false);
  const [brainTab, setBrainTab] = useState('search');

  // Code
  const [codeInput, setCodeInput] = useState('# Python Code hier eingeben\nprint("Hallo NeXify AI!")');
  const [codeLang, setCodeLang] = useState('python');
  const [codeResult, setCodeResult] = useState(null);
  const [codeBusy, setCodeBusy] = useState(false);

  // API
  const [apiUrl, setApiUrl] = useState('');
  const [apiMethod, setApiMethod] = useState('GET');
  const [apiHeaders, setApiHeaders] = useState('');
  const [apiBody, setApiBody] = useState('');
  const [apiResult, setApiResult] = useState(null);
  const [apiBusy, setApiBusy] = useState(false);

  // Sessions
  const [sessions, setSessions] = useState([]);
  const [sessionsOpen, setSessionsOpen] = useState(false);

  /* ── Load status ── */
  useEffect(() => {
    apiFetch('/api/admin/agent/status').then(d => d && setAgentStatus(d));
  }, [apiFetch]);

  /* ── Auto-scroll chat ── */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /* ── Chat ── */
  const sendMessage = useCallback(async () => {
    if (!chatInput.trim() || chatBusy) return;
    const msg = chatInput.trim();
    setChatInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg, ts: new Date().toISOString() }]);
    setChatBusy(true);

    try {
      const r = await fetch(`${API}/api/admin/agent/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ session_id: sessionId, message: msg, auto_brain: true }),
      });
      const d = await r.json();
      if (!r.ok) {
        const errorMsg = d.detail || d.error || `HTTP ${r.status}`;
        setMessages(prev => [...prev, { role: 'assistant', content: `Fehler: ${errorMsg}`, ts: new Date().toISOString() }]);
      } else if (d.message) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: d.message,
          ts: new Date().toISOString(),
          provider: d.provider,
          model: d.model,
          brain_context_loaded: d.brain_context_loaded,
        }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Fehler: ${e.message}`, ts: new Date().toISOString() }]);
    } finally {
      setChatBusy(false);
    }
  }, [chatInput, chatBusy, sessionId, headers]);

  const newSession = () => {
    setSessionId(genAgentSid());
    setMessages([]);
  };

  const loadSessions = async () => {
    const d = await apiFetch('/api/admin/agent/sessions');
    if (d) setSessions(d.sessions || []);
    setSessionsOpen(true);
  };

  const loadSession = async (sid) => {
    const d = await apiFetch(`/api/admin/agent/sessions/${sid}`);
    if (d) {
      setSessionId(sid);
      setMessages(d.messages || []);
      setSessionsOpen(false);
    }
  };

  /* ── Brain ── */
  const searchBrain = async () => {
    if (!brainQuery.trim()) return;
    setBrainBusy(true);
    try {
      const r = await fetch(`${API}/api/admin/agent/brain/search`, {
        method: 'POST', headers,
        body: JSON.stringify({ query: brainQuery, top_k: 10 }),
      });
      const d = await r.json();
      setBrainResults(d.results || d || []);
    } catch (e) {
      setBrainResults([{ error: e.message }]);
    } finally {
      setBrainBusy(false);
    }
  };

  const storeBrain = async () => {
    if (!brainStoreText.trim()) return;
    setBrainStoreBusy(true);
    setBrainStoreMsg('');
    try {
      const r = await fetch(`${API}/api/admin/agent/brain/store`, {
        method: 'POST', headers,
        body: JSON.stringify({ content: brainStoreText, memory_layer: brainStoreLayer }),
      });
      const d = await r.json();
      setBrainStoreMsg(d.error ? `Fehler: ${d.error}` : 'Erfolgreich gespeichert');
      setBrainStoreText('');
    } catch (e) {
      setBrainStoreMsg(`Fehler: ${e.message}`);
    } finally {
      setBrainStoreBusy(false);
    }
  };

  const listBrainMemories = async () => {
    setBrainListBusy(true);
    try {
      const d = await apiFetch('/api/admin/agent/brain/memories');
      setBrainMemories(d?.results || d || []);
    } catch (e) {
      setBrainMemories([]);
    } finally {
      setBrainListBusy(false);
    }
  };

  const deleteBrainMemory = async (memId) => {
    if (!window.confirm('Memory wirklich löschen?')) return;
    await apiFetch(`/api/admin/agent/brain/${memId}`, { method: 'DELETE' });
    setBrainMemories(prev => prev.filter(m => m.id !== memId));
  };

  /* ── Code Execution ── */
  const runCode = async () => {
    if (!codeInput.trim()) return;
    setCodeBusy(true);
    setCodeResult(null);
    try {
      const r = await fetch(`${API}/api/admin/agent/execute`, {
        method: 'POST', headers,
        body: JSON.stringify({ code: codeInput, language: codeLang, timeout: 30 }),
      });
      const d = await r.json();
      setCodeResult(d);
    } catch (e) {
      setCodeResult({ stderr: e.message, returncode: -1 });
    } finally {
      setCodeBusy(false);
    }
  };

  /* ── API Call ── */
  const executeApiCall = async () => {
    if (!apiUrl.trim()) return;
    setApiBusy(true);
    setApiResult(null);
    try {
      let parsedHeaders = {};
      if (apiHeaders.trim()) {
        try { parsedHeaders = JSON.parse(apiHeaders); } catch (e) { /* ignore */ }
      }
      let parsedBody = null;
      if (apiBody.trim()) {
        try { parsedBody = JSON.parse(apiBody); } catch (e) { parsedBody = apiBody; }
      }
      const r = await fetch(`${API}/api/admin/agent/api-call`, {
        method: 'POST', headers,
        body: JSON.stringify({ url: apiUrl, method: apiMethod, headers: parsedHeaders, body: parsedBody }),
      });
      const d = await r.json();
      setApiResult(d);
    } catch (e) {
      setApiResult({ error: e.message, status: 0 });
    } finally {
      setApiBusy(false);
    }
  };

  /* ── Tab Nav ── */
  const tabs = [
    { id: 'chat', icon: 'smart_toy', label: 'Agent Chat' },
    { id: 'brain', icon: 'psychology', label: 'Brain' },
    { id: 'code', icon: 'code', label: 'Code' },
    { id: 'api', icon: 'api', label: 'API' },
  ];

  return (
    <div className="agent-view" data-testid="agent-view">
      {/* Status Bar */}
      <div className="agent-status-bar">
        <div className="agent-status-left">
          <span className="agent-status-dot" style={{ background: agentStatus?.brain_connected ? '#10b981' : '#ef4444' }}></span>
          <span className="agent-status-text">
            Brain: {agentStatus?.brain_connected ? 'Verbunden' : 'Nicht verbunden'}
          </span>
          {agentStatus?.llm_providers?.filter(p => p.available).map(p => (
            <span key={p.name} className="agent-provider-badge">{p.name}</span>
          ))}
        </div>
        <div className="agent-status-right">
          <span className="agent-status-text">{agentStatus?.active_sessions || 0} aktive Sessions</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="agent-tabs">
        {tabs.map(t => (
          <button
            key={t.id}
            className={`agent-tab ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
            data-testid={`agent-tab-${t.id}`}
          >
            <I n={t.icon} /><span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* ══════════ CHAT TAB ══════════ */}
      {activeTab === 'chat' && (
        <div className="agent-chat-container" data-testid="agent-chat">
          <div className="agent-chat-toolbar">
            <button className="adm-btn-sm" onClick={newSession}><I n="add" /> Neue Session</button>
            <button className="adm-btn-sm" onClick={loadSessions}><I n="history" /> Sessions</button>
            <span className="agent-session-id">Session: {sessionId.slice(0, 20)}...</span>
          </div>

          {/* Sessions Drawer */}
          {sessionsOpen && (
            <div className="agent-sessions-drawer">
              <div className="agent-sessions-header">
                <h4>Gespeicherte Sessions</h4>
                <button className="adm-btn-icon" onClick={() => setSessionsOpen(false)}><I n="close" /></button>
              </div>
              {sessions.length === 0 && <p className="adm-muted">Keine Sessions gefunden</p>}
              {sessions.map((s, i) => (
                <div key={i} className="agent-session-item" onClick={() => loadSession(s.session_id)}>
                  <span className="agent-session-item-id">{s.session_id}</span>
                  <span className="adm-muted">{s.messages?.[0]?.content?.slice(0, 60) || '...'}</span>
                </div>
              ))}
            </div>
          )}

          {/* Messages */}
          <div className="agent-chat-messages">
            {messages.length === 0 && (
              <div className="agent-chat-welcome">
                <div className="agent-welcome-icon"><I n="smart_toy" /></div>
                <h3>NeXify AI (Master)</h3>
                <p>Dein operativer KI-Assistent mit Brain, Code-Ausführung und API-Zugriff.</p>
                <div className="agent-welcome-hints">
                  <button onClick={() => setChatInput('Was sind unsere aktuellen Tarife?')}>Tarife abfragen</button>
                  <button onClick={() => setChatInput('Erstelle eine Zusammenfassung unserer Services')}>Services zusammenfassen</button>
                  <button onClick={() => setChatInput('Analysiere den aktuellen Systemstatus')}>Systemstatus prüfen</button>
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`agent-msg ${m.role}`}>
                <div className="agent-msg-header">
                  <I n={m.role === 'user' ? 'person' : 'smart_toy'} />
                  <span className="agent-msg-role">{m.role === 'user' ? 'Du' : 'NeXify AI'}</span>
                  {m.provider && <span className="agent-msg-provider">{m.provider}/{m.model}</span>}
                  {m.brain_context_loaded && <span className="agent-msg-brain"><I n="psychology" /> Brain</span>}
                </div>
                <div className="agent-msg-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                </div>
              </div>
            ))}
            {chatBusy && (
              <div className="agent-msg assistant">
                <div className="agent-msg-header"><I n="smart_toy" /><span className="agent-msg-role">NeXify AI</span></div>
                <div className="agent-msg-content"><div className="agent-typing"><span></span><span></span><span></span></div></div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="agent-chat-input-bar">
            <textarea
              className="agent-chat-input"
              placeholder="Nachricht an NeXify AI (Master)..."
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
              rows={1}
              data-testid="agent-chat-input"
            />
            <button className="agent-send-btn" onClick={sendMessage} disabled={chatBusy || !chatInput.trim()} data-testid="agent-send-btn">
              <I n="send" />
            </button>
          </div>
        </div>
      )}

      {/* ══════════ BRAIN TAB ══════════ */}
      {activeTab === 'brain' && (
        <div className="agent-brain-container" data-testid="agent-brain">
          <div className="agent-brain-tabs">
            <button className={`agent-brain-tab ${brainTab === 'search' ? 'active' : ''}`} onClick={() => setBrainTab('search')}>
              <I n="search" /> Suchen
            </button>
            <button className={`agent-brain-tab ${brainTab === 'store' ? 'active' : ''}`} onClick={() => setBrainTab('store')}>
              <I n="add_circle" /> Speichern
            </button>
            <button className={`agent-brain-tab ${brainTab === 'list' ? 'active' : ''}`} onClick={() => { setBrainTab('list'); listBrainMemories(); }}>
              <I n="list" /> Alle Memories
            </button>
          </div>

          {brainTab === 'search' && (
            <div className="agent-brain-panel">
              <div className="agent-brain-search-bar">
                <input
                  className="agent-brain-input"
                  placeholder="Brain durchsuchen..."
                  value={brainQuery}
                  onChange={e => setBrainQuery(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') searchBrain(); }}
                />
                <button className="adm-btn-primary" onClick={searchBrain} disabled={brainBusy} style={{ width: 'auto', padding: '8px 16px' }}>
                  {brainBusy ? 'Suche...' : 'Suchen'}
                </button>
              </div>
              <div className="agent-brain-results">
                {brainResults.length === 0 && <p className="adm-muted" style={{ padding: 20 }}>Keine Ergebnisse. Gib eine Suchanfrage ein.</p>}
                {Array.isArray(brainResults) && brainResults.map((r, i) => (
                  <div key={i} className="agent-brain-result">
                    <div className="agent-brain-result-text">
                      {r.memory || r.content || r.text || JSON.stringify(r)}
                    </div>
                    {r.score && <span className="agent-brain-score">Score: {(r.score * 100).toFixed(1)}%</span>}
                    {r.metadata && (
                      <div className="agent-brain-meta">
                        {r.metadata.memory_layer && <span className="agent-provider-badge">{r.metadata.memory_layer}</span>}
                        {r.metadata.scope && <span className="agent-provider-badge">{r.metadata.scope}</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {brainTab === 'store' && (
            <div className="agent-brain-panel">
              <div className="agent-brain-store-form">
                <div className="adm-field">
                  <label>Memory Layer</label>
                  <select value={brainStoreLayer} onChange={e => setBrainStoreLayer(e.target.value)} className="adm-select">
                    <option value="KNOWLEDGE">KNOWLEDGE</option>
                    <option value="STATE">STATE</option>
                    <option value="TODO">TODO</option>
                  </select>
                </div>
                <div className="adm-field">
                  <label>Inhalt</label>
                  <textarea
                    className="agent-brain-textarea"
                    placeholder="Wissen, Entscheidung, Status oder Aufgabe eingeben..."
                    value={brainStoreText}
                    onChange={e => setBrainStoreText(e.target.value)}
                    rows={6}
                  />
                </div>
                <button className="adm-btn-primary" onClick={storeBrain} disabled={brainStoreBusy} style={{ width: 'auto' }}>
                  {brainStoreBusy ? 'Speichere...' : 'Im Brain speichern'}
                </button>
                {brainStoreMsg && <div className={`agent-brain-store-msg ${brainStoreMsg.startsWith('Fehler') ? 'error' : 'success'}`}>{brainStoreMsg}</div>}
              </div>
            </div>
          )}

          {brainTab === 'list' && (
            <div className="agent-brain-panel">
              <div className="agent-brain-list-header">
                <span>{brainMemories.length} Memories</span>
                <button className="adm-btn-sm" onClick={listBrainMemories} disabled={brainListBusy}>
                  <I n="refresh" /> {brainListBusy ? 'Lade...' : 'Aktualisieren'}
                </button>
              </div>
              <div className="agent-brain-results">
                {brainMemories.length === 0 && <p className="adm-muted" style={{ padding: 20 }}>Keine Memories gefunden.</p>}
                {Array.isArray(brainMemories) && brainMemories.map((m, i) => (
                  <div key={i} className="agent-brain-result">
                    <div className="agent-brain-result-text">{m.memory || m.content || m.text || JSON.stringify(m)}</div>
                    {m.metadata && (
                      <div className="agent-brain-meta">
                        {m.metadata.memory_layer && <span className="agent-provider-badge">{m.metadata.memory_layer}</span>}
                        {m.id && (
                          <button className="adm-btn-danger-sm" onClick={() => deleteBrainMemory(m.id)} title="Löschen">
                            <I n="delete" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ══════════ CODE TAB ══════════ */}
      {activeTab === 'code' && (
        <div className="agent-code-container" data-testid="agent-code">
          <div className="agent-code-toolbar">
            <select className="adm-select" value={codeLang} onChange={e => setCodeLang(e.target.value)}>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
            </select>
            <button className="adm-btn-primary" onClick={runCode} disabled={codeBusy} style={{ width: 'auto', padding: '6px 16px' }}>
              <I n="play_arrow" /> {codeBusy ? 'Ausführen...' : 'Ausführen'}
            </button>
          </div>
          <div className="agent-code-editor-wrap">
            <textarea
              className="agent-code-editor"
              value={codeInput}
              onChange={e => setCodeInput(e.target.value)}
              spellCheck={false}
              data-testid="agent-code-editor"
            />
          </div>
          {codeResult && (
            <div className="agent-code-output" data-testid="agent-code-output">
              <div className="agent-code-output-header">
                <span style={{ color: codeResult.returncode === 0 ? '#10b981' : '#ef4444' }}>
                  <I n={codeResult.returncode === 0 ? 'check_circle' : 'error'} />
                  {codeResult.returncode === 0 ? ' Erfolgreich' : ` Fehler (Code ${codeResult.returncode})`}
                </span>
                <span className="adm-muted">{codeResult.duration_ms}ms · {codeResult.language}</span>
              </div>
              {codeResult.stdout && (
                <div className="agent-code-stdout">
                  <label>STDOUT</label>
                  <pre>{codeResult.stdout}</pre>
                </div>
              )}
              {codeResult.stderr && (
                <div className="agent-code-stderr">
                  <label>STDERR</label>
                  <pre>{codeResult.stderr}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ══════════ API TAB ══════════ */}
      {activeTab === 'api' && (
        <div className="agent-api-container" data-testid="agent-api">
          <div className="agent-api-form">
            <div className="agent-api-url-bar">
              <select className="adm-select" value={apiMethod} onChange={e => setApiMethod(e.target.value)} style={{ width: 100 }}>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
                <option value="DELETE">DELETE</option>
              </select>
              <input
                className="agent-api-url-input"
                placeholder="https://api.example.com/endpoint"
                value={apiUrl}
                onChange={e => setApiUrl(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') executeApiCall(); }}
              />
              <button className="adm-btn-primary" onClick={executeApiCall} disabled={apiBusy} style={{ width: 'auto', padding: '8px 16px' }}>
                <I n="send" /> {apiBusy ? '...' : 'Senden'}
              </button>
            </div>
            <div className="agent-api-extras">
              <div className="adm-field">
                <label>Headers (JSON)</label>
                <textarea
                  className="agent-api-textarea"
                  placeholder='{"Authorization": "Bearer token"}'
                  value={apiHeaders}
                  onChange={e => setApiHeaders(e.target.value)}
                  rows={3}
                />
              </div>
              {['POST', 'PUT', 'PATCH'].includes(apiMethod) && (
                <div className="adm-field">
                  <label>Body (JSON)</label>
                  <textarea
                    className="agent-api-textarea"
                    placeholder='{"key": "value"}'
                    value={apiBody}
                    onChange={e => setApiBody(e.target.value)}
                    rows={4}
                  />
                </div>
              )}
            </div>
          </div>

          {apiResult && (
            <div className="agent-api-result" data-testid="agent-api-result">
              <div className="agent-api-result-header">
                <span style={{ color: apiResult.status >= 200 && apiResult.status < 300 ? '#10b981' : '#ef4444' }}>
                  Status: {apiResult.status}
                </span>
                <span className="adm-muted">{apiResult.duration_ms}ms</span>
              </div>
              <div className="agent-api-result-body">
                <label>Response</label>
                <pre>{typeof apiResult.body === 'object' ? JSON.stringify(apiResult.body, null, 2) : apiResult.body}</pre>
              </div>
              {apiResult.error && <div className="agent-api-error">{apiResult.error}</div>}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentView;

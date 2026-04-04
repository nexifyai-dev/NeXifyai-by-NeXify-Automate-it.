import React, { useState, useEffect, useRef, useCallback } from 'react';
import './CustomerPortal.css';

const API = process.env.REACT_APP_BACKEND_URL || '';
const I = ({ n }) => <span className="material-symbols-outlined">{n}</span>;
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '-';
const fmtTime = (d) => d ? new Date(d).toLocaleString('de-DE', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '-';
const fmtEur = (v) => v != null ? new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(v) : '-';

const QUOTE_STATUS = {
  draft: { l: 'Entwurf', c: '#6b7b8d', i: 'edit' },
  sent: { l: 'Versendet', c: '#3b82f6', i: 'send' },
  opened: { l: 'Geöffnet', c: '#f59e0b', i: 'visibility' },
  accepted: { l: 'Angenommen', c: '#10b981', i: 'check_circle' },
  declined: { l: 'Abgelehnt', c: '#ef4444', i: 'cancel' },
  revision_requested: { l: 'Änderung angefragt', c: '#8b5cf6', i: 'edit_note' },
};

const CustomerPortal = () => {
  useEffect(() => { document.body.classList.add('hide-wa'); return () => document.body.classList.remove('hide-wa'); }, []);
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get('token');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('overview');
  const [actionBusy, setActionBusy] = useState('');
  const [revisionNotes, setRevisionNotes] = useState('');
  const [showRevision, setShowRevision] = useState(null);
  const [authToken, setAuthToken] = useState('');
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [contractDetail, setContractDetail] = useState(null);
  const [contractLoading, setContractLoading] = useState(false);
  const [legalAccepted, setLegalAccepted] = useState({});
  const [signatureType, setSignatureType] = useState('canvas');
  const [signatureName, setSignatureName] = useState('');
  const [signatureData, setSignatureData] = useState('');
  const [contractBusy, setContractBusy] = useState('');
  const [changeRequest, setChangeRequest] = useState('');
  const [declineReason, setDeclineReason] = useState('');
  const [showDecline, setShowDecline] = useState(false);
  const [showChangeReq, setShowChangeReq] = useState(false);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [projectDetail, setProjectDetail] = useState(null);
  const [projectChatMsg, setProjectChatMsg] = useState('');
  const [financeData, setFinanceData] = useState(null);
  const [financeLoading, setFinanceLoading] = useState(false);
  const canvasRef = useRef(null);
  const isDrawingRef = useRef(false);

  const apiFetch = (url, opts = {}) => {
    const headers = { ...opts.headers };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
    return fetch(url, { ...opts, headers });
  };

  const loadDashboard = async (jwt) => {
    try {
      const r = await fetch(`${API}/api/customer/dashboard`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (!r.ok) throw new Error('Zugang abgelaufen');
      const d = await r.json();
      setData(d);
      setAuthToken(jwt);
    } catch (e) {
      throw e;
    }
  };

  const loadLegacyToken = async (token) => {
    try {
      const r = await fetch(`${API}/api/portal/customer/${token}`);
      if (!r.ok) throw new Error('Zugangslink ungültig oder abgelaufen');
      const d = await r.json();
      setData(d);
    } catch (e) {
      throw e;
    }
  };

  const reload = () => {
    if (authToken) {
      loadDashboard(authToken).catch(e => setError(e.message));
      loadContracts();
      loadProjects();
    } else if (urlToken) {
      loadLegacyToken(urlToken).catch(e => setError(e.message));
    }
  };

  const loadContracts = useCallback(async () => {
    if (!authToken) return;
    try {
      const r = await fetch(`${API}/api/customer/contracts`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (r.ok) { const d = await r.json(); setContracts(d.contracts || []); }
    } catch {}
  }, [authToken]);

  const loadContractDetail = async (contractId) => {
    setContractLoading(true);
    try {
      const r = await fetch(`${API}/api/customer/contracts/${contractId}`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (r.ok) {
        const d = await r.json();
        setContractDetail(d);
        setSelectedContract(contractId);
        const initial = {};
        (d.legal_module_definitions || []).forEach(lm => { initial[lm.key] = d.legal_modules?.[lm.key]?.accepted || false; });
        setLegalAccepted(initial);
        setSignatureData('');
        setSignatureName('');
        setShowDecline(false);
        setShowChangeReq(false);
      }
    } catch (e) { console.error(e); } finally { setContractLoading(false); }
  };

  const loadProjects = useCallback(async () => {
    if (!authToken) return;
    try {
      const r = await fetch(`${API}/api/customer/projects`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (r.ok) { const d = await r.json(); setProjects(d.projects || []); }
    } catch {}
  }, [authToken]);

  const loadFinance = useCallback(async () => {
    if (!authToken) return;
    setFinanceLoading(true);
    try {
      const r = await fetch(`${API}/api/customer/finance`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (r.ok) { const d = await r.json(); setFinanceData(d); }
    } catch {} finally { setFinanceLoading(false); }
  }, [authToken]);

  const loadProjectDetail = async (projectId) => {
    try {
      const r = await fetch(`${API}/api/customer/projects/${projectId}`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (r.ok) { const d = await r.json(); setProjectDetail(d); setSelectedProject(projectId); }
    } catch {}
  };

  const sendProjectChatMsg = async () => {
    if (!projectChatMsg.trim() || !selectedProject) return;
    try {
      await fetch(`${API}/api/customer/projects/${selectedProject}/chat`, {
        method: 'POST', headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: projectChatMsg }),
      });
      setProjectChatMsg('');
      loadProjectDetail(selectedProject);
    } catch {}
  };

  /* Signature Canvas */
  const initCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const startDraw = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    isDrawingRef.current = true;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    ctx.beginPath();
    ctx.moveTo(x, y);
  }, []);

  const draw = useCallback((e) => {
    if (!isDrawingRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    e.preventDefault();
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    ctx.lineTo(x, y);
    ctx.stroke();
  }, []);

  const endDraw = useCallback(() => {
    isDrawingRef.current = false;
    const canvas = canvasRef.current;
    if (canvas) setSignatureData(canvas.toDataURL('image/png'));
  }, []);

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setSignatureData('');
  }, []);

  useEffect(() => { if (tab === 'contracts' && selectedContract && signatureType === 'canvas') { setTimeout(initCanvas, 200); } }, [tab, selectedContract, signatureType, initCanvas]);

  const allRequiredLegalAccepted = () => {
    if (!contractDetail?.legal_module_definitions) return false;
    return contractDetail.legal_module_definitions.filter(l => l.required).every(l => legalAccepted[l.key]);
  };

  const hasValidSignature = () => {
    if (signatureType === 'name') return signatureName.trim().length >= 2;
    return !!signatureData;
  };

  const acceptContract = async () => {
    if (!allRequiredLegalAccepted() || !hasValidSignature()) return;
    setContractBusy('accepting');
    try {
      const payload = {
        signature_type: signatureType,
        signature_data: signatureType === 'name' ? signatureName : signatureData,
        legal_modules_accepted: legalAccepted,
        customer_name: contractDetail?.customer?.name || '',
      };
      const r = await fetch(`${API}/api/customer/contracts/${selectedContract}/accept`, {
        method: 'POST', headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (r.ok) {
        loadContractDetail(selectedContract);
        loadContracts();
      }
    } catch (e) { console.error(e); } finally { setContractBusy(''); }
  };

  const declineContract = async () => {
    setContractBusy('declining');
    try {
      await fetch(`${API}/api/customer/contracts/${selectedContract}/decline`, {
        method: 'POST', headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: declineReason }),
      });
      loadContractDetail(selectedContract);
      loadContracts();
      setShowDecline(false);
    } catch (e) { console.error(e); } finally { setContractBusy(''); }
  };

  const requestChange = async () => {
    if (!changeRequest.trim()) return;
    setContractBusy('change');
    try {
      await fetch(`${API}/api/customer/contracts/${selectedContract}/request-change`, {
        method: 'POST', headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ requested_changes: changeRequest }),
      });
      loadContractDetail(selectedContract);
      loadContracts();
      setShowChangeReq(false);
      setChangeRequest('');
    } catch (e) { console.error(e); } finally { setContractBusy(''); }
  };

  useEffect(() => {
    const init = async () => {
      // 1. Check JWT from localStorage (nach /login Auth)
      const stored = localStorage.getItem('nx_auth');
      if (stored) {
        try {
          const auth = JSON.parse(stored);
          if (auth.role === 'customer' && auth.token) {
            await loadDashboard(auth.token);
            setLoading(false);
            // Load contracts and projects after dashboard
            return;
          }
        } catch {}
      }
      
      // 2. Check URL path for direct magic link token: /portal/{token}
      const pathParts = window.location.pathname.split('/portal/');
      const pathToken = pathParts.length > 1 ? pathParts[1] : null;
      if (pathToken) {
        try {
          // Verify token → get JWT
          const vr = await fetch(`${API}/api/auth/verify-token`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: pathToken }),
          });
          if (vr.ok) {
            const vd = await vr.json();
            localStorage.setItem('nx_auth', JSON.stringify({
              token: vd.access_token, role: 'customer', email: vd.email, name: vd.customer_name
            }));
            await loadDashboard(vd.access_token);
            setLoading(false);
            return;
          }
        } catch {}
      }
      
      // 3. Legacy query param token
      if (urlToken) {
        try {
          await loadLegacyToken(urlToken);
          setLoading(false);
          return;
        } catch (e) {
          setError(e.message);
          setLoading(false);
          return;
        }
      }
      
      // 4. No auth → redirect to login
      setError('Bitte melden Sie sich an, um auf Ihr Portal zuzugreifen.');
      setLoading(false);
    };
    init();
  }, []);

  useEffect(() => {
    if (authToken) { loadContracts(); loadProjects(); loadFinance(); }
  }, [authToken, loadContracts, loadProjects, loadFinance]);

  const logout = () => {
    localStorage.removeItem('nx_auth');
    window.location.href = '/login';
  };

  const quoteAction = async (quoteId, action, body = {}) => {
    setActionBusy(`${quoteId}_${action}`);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
      const qp = urlToken ? `?token=${urlToken}` : '';
      const r = await fetch(`${API}/api/portal/quote/${quoteId}/${action}${qp}`, {
        method: 'POST', headers, body: JSON.stringify(body)
      });
      if (r.ok) reload();
    } catch (e) { console.error(e); } finally { setActionBusy(''); }
  };

  if (loading) return (
    <div className="cp-loading"><div className="cp-spinner"></div><p>Laden...</p></div>
  );

  if (error) return (
    <div className="cp-error">
      <div className="cp-error-box">
        <I n="lock" /><h2>Zugang nicht möglich</h2>
        <p>{error}</p>
        <a href="/login" className="cp-btn cp-btn-primary" data-testid="portal-login-link">Zum Login</a>
        <a href="/" className="cp-btn" style={{marginTop:8}}>Zur Startseite</a>
      </div>
    </div>
  );

  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 640;
  const tabs = [
    { id: 'overview', icon: 'dashboard', label: 'Übersicht', shortLabel: 'Übersicht' },
    { id: 'contracts', icon: 'gavel', label: `Verträge (${contracts.length})`, shortLabel: `Verträge` },
    { id: 'projects', icon: 'folder_special', label: `Projekte (${projects.length})`, shortLabel: 'Projekte' },
    { id: 'quotes', icon: 'description', label: `Angebote (${data?.quotes?.length || 0})`, shortLabel: 'Angebote' },
    { id: 'invoices', icon: 'account_balance', label: `Finanzen (${financeData?.summary?.total_invoices || data?.invoices?.length || 0})`, shortLabel: 'Finanzen' },
    { id: 'bookings', icon: 'event', label: `Termine (${data?.bookings?.length || 0})`, shortLabel: 'Termine' },
    { id: 'communication', icon: 'forum', label: `Kommunikation (${data?.communications?.length || 0})`, shortLabel: 'Chat' },
    { id: 'timeline', icon: 'timeline', label: 'Aktivität', shortLabel: 'Aktivität' },
  ];

  return (
    <div className="cp-layout" data-testid="customer-portal">
      <header className="cp-header">
        <div className="cp-header-inner">
          <div className="cp-logo"><img src="/icon-mark.svg" alt="" width="28" height="28" /><span>NeXify<em>AI</em></span></div>
          <div className="cp-user">
            <I n="person" /> {data?.customer_name || data?.email}
            <button className="cp-logout-btn" onClick={logout} title="Abmelden" data-testid="portal-logout"><I n="logout" /></button>
          </div>
        </div>
      </header>
      <div className="cp-tabs" data-testid="cp-tabs">
        {tabs.map(t => (
          <button key={t.id} className={`cp-tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)} data-testid={`cp-tab-${t.id}`}>
            <I n={t.icon} /><span className="cp-tab-label">{t.label}</span><span className="cp-tab-short">{t.shortLabel}</span>
          </button>
        ))}
      </div>
      <main className="cp-main">
        {tab === 'overview' && (
          <div className="cp-overview" data-testid="cp-overview">
            <h2>Willkommen{data?.customer_name ? `, ${data.customer_name.split(' ')[0]}` : ''}</h2>
            <div className="cp-stat-grid">
              <div className="cp-stat"><I n="description" /><div className="cp-stat-val">{data?.quotes?.length || 0}</div><div className="cp-stat-label">Angebote</div></div>
              <div className="cp-stat"><I n="receipt" /><div className="cp-stat-val">{data?.invoices?.length || 0}</div><div className="cp-stat-label">Rechnungen</div></div>
              <div className="cp-stat"><I n="event" /><div className="cp-stat-val">{data?.bookings?.length || 0}</div><div className="cp-stat-label">Termine</div></div>
              <div className="cp-stat"><I n="forum" /><div className="cp-stat-val">{data?.communications?.length || 0}</div><div className="cp-stat-label">Gespräche</div></div>
            </div>
            {data?.quotes?.length > 0 && (
              <div className="cp-section">
                <h3>Aktuelle Angebote</h3>
                {data.quotes.slice(0, 3).map(q => {
                  const s = QUOTE_STATUS[q.status] || { l: q.status, c: '#6b7b8d' };
                  return (
                    <div key={q.quote_id} className="cp-card" data-testid={`cp-quote-${q.quote_id}`}>
                      <div className="cp-card-header">
                        <span className="cp-card-title">{q.quote_number}</span>
                        <span className="cp-badge" style={{ background: s.c + '22', color: s.c }}><I n={s.i || 'circle'} /> {s.l}</span>
                      </div>
                      <div className="cp-card-body">
                        <span>{q.calculation?.tier_name || q.tier}</span>
                        <span className="cp-card-price">{fmtEur(q.calculation?.total_contract_eur)}</span>
                      </div>
                      <div className="cp-card-footer">
                        <span>{fmtDate(q.created_at)}</span>
                        {(q.status === 'sent' || q.status === 'opened') && (
                          <a href={`/angebot?token=${token}&qid=${q.quote_id}`} className="cp-btn cp-btn-primary cp-btn-sm" data-testid={`cp-open-quote-${q.quote_id}`}>Angebot öffnen</a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ══════════ CONTRACTS TAB ══════════ */}
        {tab === 'contracts' && (
          <div className="cp-contracts" data-testid="cp-contracts">
            {selectedContract && contractDetail ? (() => {
              const cd = contractDetail;
              const CTR_S = { draft:{l:'Entwurf',c:'#6b7b8d'}, review:{l:'Review',c:'#f59e0b'}, sent:{l:'Zur Prüfung',c:'#3b82f6'}, viewed:{l:'Eingesehen',c:'#06b6d4'}, accepted:{l:'Angenommen',c:'#10b981'}, declined:{l:'Abgelehnt',c:'#ef4444'}, change_requested:{l:'Änderung angefragt',c:'#f97316'}, amended:{l:'Überarbeitet',c:'#8b5cf6'}, cancelled:{l:'Storniert',c:'#64748b'}, expired:{l:'Abgelaufen',c:'#4a5568'} };
              const st = CTR_S[cd.status] || CTR_S.draft;
              const canSign = ['sent', 'viewed'].includes(cd.status);
              const isAccepted = cd.status === 'accepted';
              const isDeclined = cd.status === 'declined';
              const isChangeReq = cd.status === 'change_requested';
              return (
                <div data-testid="cp-contract-detail">
                  <button className="cp-btn cp-btn-secondary cp-btn-sm" onClick={() => { setSelectedContract(null); setContractDetail(null); }} data-testid="cp-contract-back"><I n="arrow_back" /> Alle Verträge</button>
                  <div style={{display:'flex',alignItems:'center',gap:12,margin:'20px 0 16px',flexWrap:'wrap'}}>
                    <h2 style={{margin:0}}>Vertrag {cd.contract_number}</h2>
                    <span className="cp-badge" style={{background:st.c+'22',color:st.c,fontSize:'.75rem'}}>{st.l}</span>
                  </div>

                  {/* Status messages */}
                  {isAccepted && <div className="cp-status-box cp-status-success" data-testid="cp-contract-accepted-msg"><I n="verified" /> <span>Vertrag erfolgreich angenommen. Vielen Dank für Ihr Vertrauen.</span></div>}
                  {isDeclined && <div className="cp-status-box cp-status-danger" data-testid="cp-contract-declined-msg"><I n="cancel" /> <span>Vertrag wurde abgelehnt. Bei Fragen kontaktieren Sie uns gerne.</span></div>}
                  {isChangeReq && <div className="cp-status-box cp-status-warning" data-testid="cp-contract-change-msg"><I n="edit_note" /> <span>Ihre Änderungsanfrage wurde übermittelt. Wir melden uns in Kürze.</span></div>}

                  {/* Contract info */}
                  <div className="cp-card" style={{marginBottom:16}}>
                    <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(180px,1fr))',gap:12}}>
                      <div><div className="cp-meta-label">Vertragstyp</div><div className="cp-meta-val">{{standard:'Standardvertrag',individual:'Individualvertrag',amendment:'Nachtragsvertrag'}[cd.contract_type]||cd.contract_type}</div></div>
                      <div><div className="cp-meta-label">Tarif</div><div className="cp-meta-val">{cd.calculation?.tier_name || cd.tier_key || '-'}</div></div>
                      <div><div className="cp-meta-label">Version</div><div className="cp-meta-val">v{cd.version || 1}</div></div>
                      <div><div className="cp-meta-label">Erstellt</div><div className="cp-meta-val">{fmtDate(cd.created_at)}</div></div>
                    </div>
                  </div>

                  {/* Calculation */}
                  {cd.calculation && cd.calculation.total_contract_eur && (
                    <div className="cp-card" style={{marginBottom:16}}>
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Kommerzielle Konditionen</h3>
                      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(180px,1fr))',gap:12}}>
                        <div><div className="cp-meta-label">Gesamtvertragswert</div><div className="cp-meta-val" style={{fontSize:'1.125rem',fontWeight:700,color:'#fff'}}>{fmtEur(cd.calculation.total_contract_eur)}</div></div>
                        <div><div className="cp-meta-label">Aktivierungsanzahlung (30%)</div><div className="cp-meta-val" style={{color:'#ff9b7a',fontWeight:600}}>{fmtEur(cd.calculation.upfront_eur)}</div></div>
                        <div><div className="cp-meta-label">Monatsrate</div><div className="cp-meta-val">{fmtEur(cd.calculation.recurring_eur)}/Monat</div></div>
                        <div><div className="cp-meta-label">Laufzeit</div><div className="cp-meta-val">{cd.calculation.contract_months || 0} Monate</div></div>
                      </div>
                    </div>
                  )}

                  {/* Appendices */}
                  {(cd.appendices_detail || []).length > 0 && (
                    <div className="cp-card" style={{marginBottom:16}}>
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Vertragsanlagen</h3>
                      {cd.appendices_detail.map(a => (
                        <div key={a.appendix_id} style={{padding:'10px 0',borderBottom:'1px solid rgba(255,255,255,0.03)'}} data-testid={`cp-appendix-${a.appendix_id}`}>
                          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                            <span style={{fontWeight:600,color:'#fff',fontSize:'.8125rem'}}>{a.title}</span>
                            {a.pricing?.amount > 0 && <span style={{color:'#ff9b7a',fontWeight:600}}>{fmtEur(a.pricing.amount)}</span>}
                          </div>
                          {a.content?.description && <p style={{margin:'4px 0 0',fontSize:'.75rem',color:'#6b7b8d'}}>{a.content.description}</p>}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Signature Preview (P3: nach Annahme) */}
                  {isAccepted && cd.signature_preview && (
                    <div className="cp-card cp-sig-preview-card" style={{marginBottom:16}} data-testid="cp-signature-preview">
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Ihre Unterschrift</h3>
                      <div className="cp-sig-preview-inner">
                        {cd.signature_preview.is_image ? (
                          <img src={cd.signature_preview.data} alt="Signatur" className="cp-sig-preview-img" data-testid="cp-sig-preview-img" />
                        ) : (
                          <div className="cp-sig-preview-name" data-testid="cp-sig-preview-name">{cd.signature_preview.data}</div>
                        )}
                        <div className="cp-sig-preview-meta">
                          <span><I n="person" /> {cd.signature_preview.customer_name}</span>
                          <span><I n="schedule" /> {fmtTime(cd.signature_preview.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Contract PDF Download */}
                  {cd.has_pdf && (
                    <div className="cp-card" style={{marginBottom:16}} data-testid="cp-contract-pdf">
                      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                        <div>
                          <h3 style={{margin:0,fontSize:'.9375rem'}}>Vertragsdokument</h3>
                          <p style={{margin:'4px 0 0',fontSize:'.75rem',color:'#6b7b8d'}}>PDF-Version Ihres Vertrags</p>
                        </div>
                        <a href={`${API}${cd.pdf_url}`} target="_blank" rel="noreferrer" className="cp-btn cp-btn-secondary" data-testid="cp-contract-pdf-download"><I n="picture_as_pdf" /> PDF herunterladen</a>
                      </div>
                    </div>
                  )}

                  {/* Versions History (P3) */}
                  {cd.versions && cd.versions.length > 0 && (
                    <div className="cp-card" style={{marginBottom:16}} data-testid="cp-contract-versions">
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Versionshistorie</h3>
                      <div className="cp-version-list">
                        {cd.versions.map((v, idx) => (
                          <div key={idx} className="cp-version-item" data-testid={`cp-version-${v.version}`}>
                            <div className="cp-version-badge">v{v.version}</div>
                            <div className="cp-version-info">
                              <span className="cp-version-status">{{draft:'Entwurf',sent:'Versendet',viewed:'Eingesehen',accepted:'Angenommen',declined:'Abgelehnt',change_requested:'Änderung angefragt',amended:'Überarbeitet'}[v.status]||v.status}</span>
                              <span className="cp-version-date">{fmtTime(v.timestamp)}</span>
                            </div>
                          </div>
                        ))}
                        <div className="cp-version-item cp-version-current">
                          <div className="cp-version-badge" style={{background:'rgba(255,155,122,0.15)',color:'#ff9b7a'}}>v{cd.version || 1}</div>
                          <div className="cp-version-info">
                            <span className="cp-version-status" style={{color:'#ff9b7a'}}>Aktuelle Version</span>
                            <span className="cp-version-date">{fmtTime(cd.updated_at)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Evidence Trail (P3: Nachvollziehbares Evidenzpaket) */}
                  {cd.evidence_trail && cd.evidence_trail.length > 0 && (
                    <div className="cp-card" style={{marginBottom:16}} data-testid="cp-evidence-trail">
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Nachweisprotokoll</h3>
                      <p style={{fontSize:'.6875rem',color:'#6b7b8d',marginBottom:12}}>Alle rechtlich relevanten Aktionen zu diesem Vertrag.</p>
                      {cd.evidence_trail.map(ev => {
                        const actionLabels = {accepted:'Angenommen',declined:'Abgelehnt',change_requested:'Änderung angefragt',viewed:'Eingesehen'};
                        return (
                          <div key={ev.evidence_id} className="cp-evidence-item" data-testid={`cp-evidence-${ev.evidence_id}`}>
                            <div className="cp-evidence-header">
                              <span className="cp-badge cp-badge-sm" style={{background: ev.action === 'accepted' ? '#10b98122' : ev.action === 'declined' ? '#ef444422' : '#3b82f622', color: ev.action === 'accepted' ? '#10b981' : ev.action === 'declined' ? '#ef4444' : '#3b82f6'}}>
                                {actionLabels[ev.action] || ev.action}
                              </span>
                              <span className="cp-evidence-time">{fmtTime(ev.timestamp)}</span>
                            </div>
                            <div className="cp-evidence-details">
                              <div><span className="cp-finance-label">Version</span><span>v{ev.contract_version}</span></div>
                              <div><span className="cp-finance-label">Hash</span><span className="cp-finance-mono" style={{fontSize:'.625rem'}}>{ev.document_hash?.substring(0, 16)}...</span></div>
                              <div><span className="cp-finance-label">IP</span><span className="cp-finance-mono" style={{fontSize:'.75rem'}}>{ev.ip_address}</span></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Change Request Detail */}
                  {isChangeReq && cd.change_request_detail && (
                    <div className="cp-card" style={{marginBottom:16}} data-testid="cp-change-request-detail">
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Ihre Änderungsanfrage</h3>
                      <div style={{background:'rgba(249,115,22,0.06)',border:'1px solid rgba(249,115,22,0.15)',borderRadius:8,padding:14}}>
                        <p style={{margin:0,color:'#c8d1dc',fontSize:'.8125rem',whiteSpace:'pre-wrap'}}>{cd.change_request_detail.text}</p>
                        <span style={{fontSize:'.6875rem',color:'#6b7b8d',marginTop:8,display:'block'}}>Gesendet: {fmtTime(cd.change_request_detail.timestamp)}</span>
                      </div>
                    </div>
                  )}

                  {/* Legal Modules */}
                  {canSign && (
                    <div className="cp-card" style={{marginBottom:16}} data-testid="cp-legal-modules">
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Rechtliche Bestimmungen</h3>
                      <p style={{fontSize:'.75rem',color:'#6b7b8d',marginBottom:16}}>Bitte bestätigen Sie die folgenden rechtlichen Bestimmungen, um den Vertrag anzunehmen.</p>
                      {(cd.legal_module_definitions || []).map(lm => (
                        <label key={lm.key} className="cp-legal-check" data-testid={`cp-legal-${lm.key}`}>
                          <input type="checkbox" checked={legalAccepted[lm.key] || false} onChange={e => setLegalAccepted({ ...legalAccepted, [lm.key]: e.target.checked })} />
                          <span className="cp-legal-check-box"><I n={legalAccepted[lm.key] ? 'check_box' : 'check_box_outline_blank'} /></span>
                          <div>
                            <span className="cp-legal-label">{lm.label}{lm.required && <span style={{color:'#ef4444'}}> *</span>}</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Signature */}
                  {canSign && (
                    <div className="cp-card" style={{marginBottom:16}} data-testid="cp-signature-section">
                      <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Digitale Unterschrift</h3>
                      <div className="cp-sig-toggle">
                        <button className={`cp-sig-btn ${signatureType === 'canvas' ? 'active' : ''}`} onClick={() => setSignatureType('canvas')} data-testid="cp-sig-canvas-btn"><I n="draw" /> Zeichnen</button>
                        <button className={`cp-sig-btn ${signatureType === 'name' ? 'active' : ''}`} onClick={() => setSignatureType('name')} data-testid="cp-sig-name-btn"><I n="edit" /> Name eingeben</button>
                      </div>
                      {signatureType === 'canvas' ? (
                        <div className="cp-canvas-wrap">
                          <canvas ref={canvasRef} className="cp-sig-canvas" data-testid="cp-sig-canvas"
                            onMouseDown={startDraw} onMouseMove={draw} onMouseUp={endDraw} onMouseLeave={endDraw}
                            onTouchStart={startDraw} onTouchMove={draw} onTouchEnd={endDraw}
                          />
                          <button className="cp-btn cp-btn-secondary cp-btn-sm" onClick={clearCanvas} style={{marginTop:8}} data-testid="cp-sig-clear"><I n="delete" /> Löschen</button>
                          {signatureData && <p style={{fontSize:'.6875rem',color:'#10b981',marginTop:4}}>Unterschrift erfasst</p>}
                        </div>
                      ) : (
                        <div>
                          <input type="text" className="cp-sig-name-input" value={signatureName} onChange={e => setSignatureName(e.target.value)} placeholder="Vor- und Nachname" data-testid="cp-sig-name-input" />
                          {signatureName.trim().length >= 2 && <p style={{fontSize:'.6875rem',color:'#10b981',marginTop:4}}>Name erfasst</p>}
                        </div>
                      )}
                      <div className="cp-meta-label" style={{marginTop:12}}>Dokumentenhash</div>
                      <div style={{fontSize:'.6875rem',fontFamily:'monospace',color:'#6b7b8d',wordBreak:'break-all'}}>{cd.document_hash}</div>
                    </div>
                  )}

                  {/* Actions */}
                  {canSign && (
                    <div className="cp-contract-actions" data-testid="cp-contract-actions">
                      <button className="cp-btn cp-btn-accept" onClick={acceptContract} disabled={!allRequiredLegalAccepted() || !hasValidSignature() || !!contractBusy} data-testid="cp-accept-contract">
                        {contractBusy === 'accepting' ? 'Wird verarbeitet...' : <><I n="verified" /> Vertrag annehmen</>}
                      </button>
                      <button className="cp-btn cp-btn-secondary" onClick={() => setShowChangeReq(!showChangeReq)} disabled={!!contractBusy} data-testid="cp-change-contract"><I n="edit_note" /> Änderung anfragen</button>
                      <button className="cp-btn cp-btn-danger" onClick={() => setShowDecline(!showDecline)} disabled={!!contractBusy} data-testid="cp-decline-contract"><I n="cancel" /> Ablehnen</button>
                    </div>
                  )}

                  {showChangeReq && canSign && (
                    <div className="cp-revision-form" style={{marginTop:12}} data-testid="cp-change-form">
                      <textarea value={changeRequest} onChange={e => setChangeRequest(e.target.value)} rows={3} placeholder="Welche Änderungen wünschen Sie am Vertrag?" />
                      <div style={{display:'flex',gap:8,marginTop:8}}>
                        <button className="cp-btn cp-btn-primary cp-btn-sm" onClick={requestChange} disabled={!changeRequest.trim() || !!contractBusy}>Anfrage senden</button>
                        <button className="cp-btn cp-btn-secondary cp-btn-sm" onClick={() => setShowChangeReq(false)}>Abbrechen</button>
                      </div>
                    </div>
                  )}

                  {showDecline && canSign && (
                    <div className="cp-revision-form" style={{marginTop:12}} data-testid="cp-decline-form">
                      <textarea value={declineReason} onChange={e => setDeclineReason(e.target.value)} rows={3} placeholder="Grund der Ablehnung (optional)" />
                      <div style={{display:'flex',gap:8,marginTop:8}}>
                        <button className="cp-btn cp-btn-danger cp-btn-sm" onClick={declineContract} disabled={!!contractBusy}>Vertrag ablehnen</button>
                        <button className="cp-btn cp-btn-secondary cp-btn-sm" onClick={() => setShowDecline(false)}>Abbrechen</button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })() : (
              <>
                <h2>Ihre Verträge</h2>
                {contracts.length === 0 ? (
                  <div className="cp-empty"><I n="gavel" /><p>Noch keine Verträge vorhanden.</p></div>
                ) : contracts.map(c => {
                  const CTR_S = { draft:{l:'Entwurf',c:'#6b7b8d'}, sent:{l:'Zur Prüfung',c:'#3b82f6'}, viewed:{l:'Eingesehen',c:'#06b6d4'}, accepted:{l:'Angenommen',c:'#10b981'}, declined:{l:'Abgelehnt',c:'#ef4444'}, change_requested:{l:'Änderung angefragt',c:'#f97316'} };
                  const st = CTR_S[c.status] || { l: c.status, c: '#6b7b8d' };
                  return (
                    <div key={c.contract_id} className="cp-card" style={{cursor:'pointer'}} onClick={() => loadContractDetail(c.contract_id)} data-testid={`cp-contract-${c.contract_id}`}>
                      <div className="cp-card-header">
                        <span className="cp-card-title">{c.contract_number}</span>
                        <span className="cp-badge" style={{background:st.c+'22',color:st.c}}>{st.l}</span>
                      </div>
                      <div className="cp-card-body">
                        <span>{{standard:'Standardvertrag',individual:'Individualvertrag',amendment:'Nachtrag'}[c.contract_type]||c.contract_type}</span>
                        <span className="cp-card-price">{fmtEur(c.calculation?.total_contract_eur)}</span>
                      </div>
                      <div className="cp-card-footer">
                        <span>{fmtDate(c.created_at)}</span>
                        {['sent','viewed'].includes(c.status) && <span className="cp-btn cp-btn-primary cp-btn-sm" data-testid={`cp-open-contract-${c.contract_id}`}>Vertrag prüfen</span>}
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </div>
        )}

        {/* ══════════ PROJECTS TAB ══════════ */}
        {tab === 'projects' && (
          <div className="cp-projects" data-testid="cp-projects">
            {selectedProject && projectDetail ? (() => {
              const pd = projectDetail;
              const PRJ_S = { draft:{l:'Entwurf',c:'#6b7b8d'}, discovery:{l:'Discovery',c:'#3b82f6'}, planning:{l:'Planung',c:'#f59e0b'}, approved:{l:'Freigegeben',c:'#10b981'}, build:{l:'Build',c:'#8b5cf6'}, review:{l:'Review',c:'#ec4899'}, handover:{l:'Handover',c:'#06b6d4'}, live:{l:'Live',c:'#22c55e'}, paused:{l:'Pausiert',c:'#f97316'}, closed:{l:'Abgeschlossen',c:'#64748b'} };
              const st = PRJ_S[pd.status] || PRJ_S.draft;
              return (
                <div data-testid="cp-project-detail">
                  <button className="cp-btn cp-btn-secondary cp-btn-sm" onClick={() => { setSelectedProject(null); setProjectDetail(null); }} data-testid="cp-project-back"><I n="arrow_back" /> Alle Projekte</button>
                  <div style={{display:'flex',alignItems:'center',gap:12,margin:'20px 0 16px',flexWrap:'wrap'}}>
                    <h2 style={{margin:0}}>{pd.title}</h2>
                    <span className="cp-badge" style={{background:st.c+'22',color:st.c}}>{st.l}</span>
                    <span className="cp-badge" style={{background:'rgba(255,155,122,0.12)',color:'#ff9b7a'}}>{pd.completeness || 0}% abgeschlossen</span>
                  </div>
                  {/* Progress */}
                  <div style={{background:'rgba(255,255,255,0.04)',borderRadius:6,height:8,marginBottom:20,overflow:'hidden'}}>
                    <div style={{background:'linear-gradient(90deg,#ff9b7a,#ffb599)',height:'100%',width:`${pd.completeness||0}%`,borderRadius:6,transition:'width .5s'}}></div>
                  </div>
                  {/* Sections */}
                  {(pd.sections || []).length > 0 && (
                    <div style={{marginBottom:24}}>
                      <h3 style={{fontSize:'.9375rem',marginBottom:12}}>Projektdokumentation</h3>
                      {pd.sections.map(s => (
                        <div key={s.section_id} className="cp-card" style={{marginBottom:8,borderLeft:`3px solid ${s.status==='freigegeben'?'#10b981':s.status==='review'?'#3b82f6':'#f59e0b'}`}} data-testid={`cp-section-${s.section_key}`}>
                          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}>
                            <span style={{fontWeight:600,color:'#fff',fontSize:'.8125rem'}}>{s.label}</span>
                            <span className="cp-badge" style={{background:s.status==='freigegeben'?'#10b98122':'#f59e0b22',color:s.status==='freigegeben'?'#10b981':'#f59e0b',fontSize:'.625rem'}}>{s.status} v{s.version}</span>
                          </div>
                          <p style={{fontSize:'.8125rem',color:'#c8d1dc',whiteSpace:'pre-wrap',lineHeight:1.6}}>{s.content}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Build-Handover */}
                  {pd.latest_version && (
                    <div className="cp-card" style={{marginBottom:20}}>
                      <h3 style={{margin:'0 0 8px',fontSize:'.9375rem'}}>Build-Handover (v{pd.latest_version.version})</h3>
                      <pre style={{background:'rgba(12,17,23,0.8)',padding:16,borderRadius:6,fontSize:'.75rem',color:'#c8d1dc',overflow:'auto',maxHeight:300,whiteSpace:'pre-wrap',wordBreak:'break-word'}}>{pd.latest_version.markdown}</pre>
                    </div>
                  )}
                  {/* Chat */}
                  <h3 style={{fontSize:'.9375rem',marginBottom:12}}>Projektchat</h3>
                  <div className="cp-card">
                    <div style={{maxHeight:300,overflowY:'auto',marginBottom:12}}>
                      {(pd.chat || []).map(m => (
                        <div key={m.message_id} style={{marginBottom:8,padding:'8px 12px',background:m.sender_type==='customer'?'rgba(255,155,122,0.06)':'rgba(59,130,246,0.06)',borderRadius:6,borderLeft:`3px solid ${m.sender_type==='customer'?'#ff9b7a':'#3b82f6'}`}}>
                          <div style={{display:'flex',justifyContent:'space-between',fontSize:'.6875rem',color:'#6b7b8d',marginBottom:2}}>
                            <span>{m.sender_type === 'customer' ? 'Sie' : 'NeXifyAI'}</span>
                            <span>{fmtTime(m.timestamp)}</span>
                          </div>
                          <div style={{fontSize:'.8125rem',color:'#c8d1dc',whiteSpace:'pre-wrap'}}>{m.content}</div>
                        </div>
                      ))}
                      {(!pd.chat || pd.chat.length === 0) && <div style={{textAlign:'center',padding:20,color:'#4a5568',fontSize:'.8125rem'}}>Noch keine Nachrichten</div>}
                    </div>
                    <div style={{display:'flex',gap:8}}>
                      <input style={{flex:1,background:'rgba(14,20,28,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',padding:'10px 14px',fontSize:'.8125rem',borderRadius:4}} value={projectChatMsg} onChange={e => setProjectChatMsg(e.target.value)} placeholder="Nachricht schreiben..." onKeyDown={e => { if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendProjectChatMsg();}}} data-testid="cp-project-chat-input" />
                      <button className="cp-btn cp-btn-primary" style={{flexShrink:0}} onClick={sendProjectChatMsg} disabled={!projectChatMsg.trim()} data-testid="cp-project-chat-send"><I n="send" /></button>
                    </div>
                  </div>
                </div>
              );
            })() : (
              <>
                <h2>Ihre Projekte</h2>
                {projects.length === 0 ? (
                  <div className="cp-empty"><I n="folder_special" /><p>Noch keine Projekte vorhanden.</p></div>
                ) : projects.map(p => {
                  const PRJ_S = { draft:{l:'Entwurf',c:'#6b7b8d'}, discovery:{l:'Discovery',c:'#3b82f6'}, planning:{l:'Planung',c:'#f59e0b'}, build:{l:'Build',c:'#8b5cf6'}, live:{l:'Live',c:'#22c55e'} };
                  const st = PRJ_S[p.status] || { l: p.status, c: '#6b7b8d' };
                  return (
                    <div key={p.project_id} className="cp-card" style={{cursor:'pointer'}} onClick={() => loadProjectDetail(p.project_id)} data-testid={`cp-project-${p.project_id}`}>
                      <div className="cp-card-header">
                        <span className="cp-card-title">{p.title}</span>
                        <span className="cp-badge" style={{background:st.c+'22',color:st.c}}>{st.l}</span>
                      </div>
                      <div className="cp-card-body">
                        <span>{p.tier || '-'}</span>
                        <span style={{color:'#ff9b7a',fontWeight:600}}>{p.completeness || 0}%</span>
                      </div>
                      <div className="cp-card-footer">
                        <span>{fmtDate(p.created_at)}</span>
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </div>
        )}

        {tab === 'quotes' && (
          <div className="cp-quotes" data-testid="cp-quotes">
            <h2>Ihre Angebote</h2>
            {(!data?.quotes || data.quotes.length === 0) ? (
              <div className="cp-empty"><I n="description" /><p>Noch keine Angebote vorhanden.</p></div>
            ) : data.quotes.map(q => {
              const s = QUOTE_STATUS[q.status] || { l: q.status, c: '#6b7b8d' };
              return (
                <div key={q.quote_id} className="cp-card" data-testid={`cp-quote-card-${q.quote_id}`}>
                  <div className="cp-card-header">
                    <span className="cp-card-title">{q.quote_number}</span>
                    <span className="cp-badge" style={{ background: s.c + '22', color: s.c }}><I n={s.i || 'circle'} /> {s.l}</span>
                  </div>
                  <div className="cp-card-body">
                    <span>{q.calculation?.tier_name || q.tier}</span>
                    <span className="cp-card-price">{fmtEur(q.calculation?.total_contract_eur)}</span>
                  </div>
                  <div className="cp-card-actions">
                    {(q.status === 'sent' || q.status === 'opened') && (<>
                      <button className="cp-btn cp-btn-accept" onClick={() => quoteAction(q.quote_id, 'accept')} disabled={!!actionBusy} data-testid={`cp-accept-${q.quote_id}`}><I n="check_circle" /> Annehmen</button>
                      <button className="cp-btn cp-btn-danger" onClick={() => quoteAction(q.quote_id, 'decline')} disabled={!!actionBusy} data-testid={`cp-decline-${q.quote_id}`}><I n="cancel" /> Ablehnen</button>
                      <button className="cp-btn cp-btn-secondary" onClick={() => { setShowRevision(q.quote_id); setRevisionNotes(''); }} data-testid={`cp-revision-${q.quote_id}`}><I n="edit_note" /> Änderung anfragen</button>
                    </>)}
                    <a href={`/angebot?token=${token}&qid=${q.quote_id}`} className="cp-btn cp-btn-primary" data-testid={`cp-view-quote-${q.quote_id}`}><I n="visibility" /> Ansehen</a>
                    <a href={`${API}/api/documents/quote/${q.quote_id}/pdf`} target="_blank" rel="noreferrer" className="cp-btn cp-btn-secondary" data-testid={`cp-dl-quote-${q.quote_id}`}><I n="picture_as_pdf" /> PDF</a>
                  </div>
                  {showRevision === q.quote_id && (
                    <div className="cp-revision-form" data-testid="cp-revision-form">
                      <textarea value={revisionNotes} onChange={e => setRevisionNotes(e.target.value)} placeholder="Welche Änderungen wünschen Sie?" rows={3} />
                      <div style={{display:'flex',gap:8,marginTop:8}}>
                        <button className="cp-btn cp-btn-primary cp-btn-sm" onClick={() => { quoteAction(q.quote_id, 'revision', { notes: revisionNotes }); setShowRevision(null); }} disabled={!revisionNotes.trim()}>Absenden</button>
                        <button className="cp-btn cp-btn-secondary cp-btn-sm" onClick={() => setShowRevision(null)}>Abbrechen</button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {tab === 'invoices' && (
          <div className="cp-finance" data-testid="cp-finance">
            <h2>Ihre Finanzen</h2>
            {financeLoading ? (
              <div className="cp-empty"><div className="cp-spinner"></div><p>Finanzdaten laden...</p></div>
            ) : financeData ? (
              <>
                {/* Finance Summary */}
                <div className="cp-stat-grid cp-finance-summary" data-testid="cp-finance-summary">
                  <div className="cp-stat">
                    <I n="receipt_long" />
                    <div className="cp-stat-val">{financeData.summary.total_invoices}</div>
                    <div className="cp-stat-label">Rechnungen</div>
                  </div>
                  <div className="cp-stat">
                    <I n="pending_actions" />
                    <div className="cp-stat-val" style={{color: financeData.summary.open_invoices > 0 ? '#f59e0b' : '#10b981'}}>{financeData.summary.open_invoices}</div>
                    <div className="cp-stat-label">Offen</div>
                  </div>
                  <div className="cp-stat">
                    <I n="payments" />
                    <div className="cp-stat-val" style={{color:'#10b981'}}>{fmtEur(financeData.summary.total_paid_eur)}</div>
                    <div className="cp-stat-label">Bezahlt</div>
                  </div>
                  <div className="cp-stat">
                    <I n="account_balance_wallet" />
                    <div className="cp-stat-val" style={{color: financeData.summary.total_outstanding_eur > 0 ? '#f59e0b' : '#10b981'}}>{fmtEur(financeData.summary.total_outstanding_eur)}</div>
                    <div className="cp-stat-label">Ausstehend</div>
                  </div>
                </div>

                {/* Overdue Warning */}
                {financeData.summary.overdue_invoices > 0 && (
                  <div className="cp-finance-alert cp-finance-alert-warning" data-testid="cp-finance-overdue-alert">
                    <I n="warning" />
                    <div>
                      <strong>{financeData.summary.overdue_invoices} Rechnung{financeData.summary.overdue_invoices > 1 ? 'en' : ''} überfällig</strong>
                      <p>Bitte begleichen Sie offene Rechnungen zeitnah, um Mahngebühren zu vermeiden.</p>
                    </div>
                  </div>
                )}

                {/* Invoice List */}
                <div className="cp-finance-section">
                  <h3>Rechnungen</h3>
                  {financeData.invoices.length === 0 ? (
                    <div className="cp-empty"><I n="receipt" /><p>Noch keine Rechnungen vorhanden.</p></div>
                  ) : financeData.invoices.map(inv => {
                    const severityColor = { success: '#10b981', warning: '#f59e0b', error: '#ef4444', neutral: '#6b7b8d' }[inv.payment_status_severity] || '#6b7b8d';
                    return (
                      <div key={inv.invoice_id} className={`cp-card cp-finance-card ${inv.is_overdue ? 'cp-card-overdue' : ''}`} data-testid={`cp-fin-inv-${inv.invoice_id}`}>
                        <div className="cp-card-header">
                          <div className="cp-finance-card-title">
                            <span className="cp-card-title">{inv.invoice_number}</span>
                            {inv.type === 'deposit' && <span className="cp-badge cp-badge-sm" style={{background:'#3b82f622',color:'#3b82f6'}}>Anzahlung</span>}
                          </div>
                          <span className="cp-badge" style={{ background: severityColor + '22', color: severityColor }} data-testid={`cp-fin-status-${inv.invoice_id}`}>
                            <I n={inv.payment_status === 'paid' ? 'check_circle' : inv.is_overdue ? 'error' : 'schedule'} />
                            {inv.payment_status_label}
                          </span>
                        </div>
                        <div className="cp-finance-card-body">
                          <div className="cp-finance-detail-grid">
                            <div className="cp-finance-detail">
                              <span className="cp-finance-label">Netto</span>
                              <span className="cp-finance-value">{fmtEur(inv.amount_net)}</span>
                            </div>
                            <div className="cp-finance-detail">
                              <span className="cp-finance-label">USt. ({inv.vat_rate}%)</span>
                              <span className="cp-finance-value">{fmtEur(inv.amount_vat)}</span>
                            </div>
                            <div className="cp-finance-detail cp-finance-detail-total">
                              <span className="cp-finance-label">Brutto</span>
                              <span className="cp-finance-value cp-finance-total">{fmtEur(inv.amount_gross)}</span>
                            </div>
                            <div className="cp-finance-detail">
                              <span className="cp-finance-label">Rechnungsdatum</span>
                              <span className="cp-finance-value">{inv.date}</span>
                            </div>
                            <div className="cp-finance-detail">
                              <span className="cp-finance-label">Fällig bis</span>
                              <span className="cp-finance-value" style={{color: inv.is_overdue ? '#ef4444' : 'inherit'}}>{inv.due_date}</span>
                            </div>
                            {inv.reminder_count > 0 && (
                              <div className="cp-finance-detail">
                                <span className="cp-finance-label">Mahnstufe</span>
                                <span className="cp-finance-value" style={{color:'#ef4444'}}>{inv.reminder_level}</span>
                              </div>
                            )}
                          </div>
                          {inv.items && inv.items.length > 0 && (
                            <div className="cp-finance-items">
                              {inv.items.map((item, idx) => (
                                <div key={idx} className="cp-finance-item">
                                  <span>{item.description}</span>
                                  <span>{fmtEur(item.amount_net)}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="cp-card-actions cp-finance-actions">
                          {inv.has_pdf && (
                            <a href={`${API}${inv.pdf_url}`} target="_blank" rel="noreferrer" className="cp-btn cp-btn-secondary" data-testid={`cp-fin-pdf-${inv.invoice_id}`}>
                              <I n="picture_as_pdf" /> PDF herunterladen
                            </a>
                          )}
                          {inv.checkout_url && inv.payment_status !== 'paid' && (
                            <a href={inv.checkout_url} target="_blank" rel="noreferrer" className="cp-btn cp-btn-primary" data-testid={`cp-fin-pay-${inv.invoice_id}`}>
                              <I n="payment" /> Jetzt online bezahlen
                            </a>
                          )}
                        </div>
                        {/* Bank transfer info for pending invoices */}
                        {inv.payment_status !== 'paid' && inv.payment_status !== 'cancelled' && (
                          <div className="cp-finance-bank" data-testid={`cp-fin-bank-${inv.invoice_id}`}>
                            <div className="cp-finance-bank-header"><I n="account_balance" /> <span>Alternativ per Banküberweisung</span></div>
                            <div className="cp-finance-bank-grid">
                              <div><span className="cp-finance-label">Empfänger</span><span>{financeData.bank_transfer_info.account_holder}</span></div>
                              <div><span className="cp-finance-label">IBAN</span><span className="cp-finance-mono">{financeData.bank_transfer_info.iban}</span></div>
                              <div><span className="cp-finance-label">BIC</span><span className="cp-finance-mono">{financeData.bank_transfer_info.bic}</span></div>
                              <div><span className="cp-finance-label">Verwendungszweck</span><span className="cp-finance-mono cp-finance-ref">{inv.payment_reference}</span></div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Linked Contracts Summary */}
                {financeData.contracts && financeData.contracts.length > 0 && (
                  <div className="cp-finance-section">
                    <h3>Verträge</h3>
                    {financeData.contracts.map(c => (
                      <div key={c.contract_id} className="cp-card cp-finance-contract-card" data-testid={`cp-fin-ctr-${c.contract_id}`}>
                        <div className="cp-card-header">
                          <span className="cp-card-title">{c.contract_number || c.contract_id}</span>
                          <span className="cp-badge" style={{ background: c.status === 'accepted' ? '#10b98122' : '#3b82f622', color: c.status === 'accepted' ? '#10b981' : '#3b82f6' }}>
                            {c.status === 'accepted' ? 'Aktiv' : c.status}
                          </span>
                        </div>
                        <div className="cp-finance-detail-grid">
                          <div className="cp-finance-detail"><span className="cp-finance-label">Vertragswert</span><span className="cp-finance-value">{fmtEur(c.total_value)}</span></div>
                          {c.monthly_value > 0 && <div className="cp-finance-detail"><span className="cp-finance-label">Monatlich</span><span className="cp-finance-value">{fmtEur(c.monthly_value)}</span></div>}
                          <div className="cp-finance-detail"><span className="cp-finance-label">Erstellt</span><span className="cp-finance-value">{fmtDate(c.created_at)}</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div className="cp-empty"><I n="account_balance" /><p>Finanzdaten konnten nicht geladen werden.</p><button className="cp-btn cp-btn-secondary" onClick={loadFinance}>Erneut laden</button></div>
            )}
          </div>
        )}

        {tab === 'bookings' && (
          <div className="cp-bookings" data-testid="cp-bookings">
            <h2>Ihre Termine</h2>
            {(!data?.bookings || data.bookings.length === 0) ? (
              <div className="cp-empty"><I n="event" /><p>Noch keine Termine vorhanden.</p></div>
            ) : data.bookings.map(bk => (
              <div key={bk.booking_id} className="cp-card" data-testid={`cp-bk-${bk.booking_id}`}>
                <div className="cp-card-header">
                  <span className="cp-card-title">{bk.date} um {bk.time}</span>
                  <span className="cp-badge" style={{ background: '#3b82f622', color: '#3b82f6' }}><I n="event" /> {bk.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === 'communication' && (
          <div className="cp-communication" data-testid="cp-communication">
            <h2>Ihre Kommunikation</h2>
            {(!data?.communications || data.communications.length === 0) ? (
              <div className="cp-empty"><I n="forum" /><p>Noch keine Nachrichten vorhanden.</p></div>
            ) : data.communications.map((c, i) => {
              const isConvo = c.type === 'conversation';
              const channels = isConvo ? (c.channels || []).join(', ') : 'Chat';
              return (
                <div key={i} className="cp-card cp-comm-card" data-testid={`cp-comm-${i}`}>
                  <div className="cp-card-header">
                    <span className="cp-card-title">{channels}{isConvo && c.message_count ? ` (${c.message_count} Nachrichten)` : ''}</span>
                    <span className="cp-card-date">{fmtDate(c.date)}</span>
                  </div>
                  <div className="cp-comm-messages">
                    {(c.messages || []).slice(0, 3).map((m, j) => (
                      <div key={j} className={`cp-comm-msg ${m.role === 'user' || m.direction === 'inbound' ? 'user' : 'ai'}`}>
                        <span className="cp-comm-role">{m.role === 'user' || m.direction === 'inbound' ? 'Sie' : 'NeXifyAI'}{m.channel ? ` (${m.channel})` : ''}</span>
                        <span className="cp-comm-text">{m.content}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab === 'timeline' && (
          <div className="cp-timeline" data-testid="cp-timeline">
            <h2>Aktivitätsverlauf</h2>
            {(!data?.timeline || data.timeline.length === 0) ? (
              <div className="cp-empty"><I n="timeline" /><p>Noch keine Aktivitäten vorhanden.</p></div>
            ) : (
              <div className="cp-timeline-list">
                {data.timeline.map((evt, i) => (
                  <div key={i} className="cp-timeline-item" data-testid={`cp-tl-${i}`}>
                    <div className="cp-timeline-dot"></div>
                    <div className="cp-timeline-content">
                      <span className="cp-timeline-action">{evt.action?.replace(/_/g, ' ')}</span>
                      {evt.channel && <span className="cp-badge cp-badge-sm">{evt.channel}</span>}
                      <span className="cp-timeline-date">{fmtDate(evt.timestamp)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
      <footer className="cp-footer">
        <p>NeXifyAI by NeXify Automate — KvK 90483944 — USt-ID NL865786276B01</p>
        <div className="cp-footer-links">
          <a href="/de/impressum">Impressum</a>
          <a href="/de/datenschutz">Datenschutz</a>
          <a href="/de/agb">AGB</a>
        </div>
      </footer>
    </div>
  );
};

export default CustomerPortal;

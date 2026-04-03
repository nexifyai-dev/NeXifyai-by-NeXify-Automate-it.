import React, { useState, useEffect, useCallback, useMemo } from 'react';
import './Admin.css';

const API = process.env.REACT_APP_BACKEND_URL || '';
const I = ({ n }) => <span className="material-symbols-outlined">{n}</span>;

const fmtDate = (d) => d ? new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '-';
const fmtDateLong = (d) => d ? new Date(d).toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' }) : '-';
const fmtTime = (d) => d ? new Date(d).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-';
const fmtEur = (v) => v != null ? new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(v) : '-';

const STATUS_MAP = {
  neu: { label: 'Neu', color: '#3b82f6' }, kontaktiert: { label: 'Kontaktiert', color: '#f59e0b' },
  qualifiziert: { label: 'Qualifiziert', color: '#10b981' }, termin_gebucht: { label: 'Termin', color: '#8b5cf6' },
  abgeschlossen: { label: 'Abgeschlossen', color: '#6b7280' }, abgelehnt: { label: 'Abgelehnt', color: '#ef4444' }
};

const BOOKING_STATUS = {
  confirmed: { label: 'Bestätigt', color: '#10b981', icon: 'check_circle' },
  pending: { label: 'Ausstehend', color: '#f59e0b', icon: 'schedule' },
  completed: { label: 'Abgeschlossen', color: '#6b7280', icon: 'task_alt' },
  cancelled: { label: 'Storniert', color: '#ef4444', icon: 'cancel' },
  no_show: { label: 'Nicht erschienen', color: '#dc2626', icon: 'person_off' },
  rescheduled: { label: 'Verschoben', color: '#3b82f6', icon: 'event_repeat' }
};

const Admin = () => {
  useEffect(() => { document.body.classList.add('hide-wa'); return () => document.body.classList.remove('hide-wa'); }, []);
  const [token, setToken] = useState(() => {
    // Check both storage keys for backward compatibility
    const directToken = localStorage.getItem('nx_admin_token');
    if (directToken) return directToken;
    try {
      const auth = JSON.parse(localStorage.getItem('nx_auth') || '{}');
      if (auth.role === 'admin' && auth.token) {
        localStorage.setItem('nx_admin_token', auth.token); // Sync for future
        return auth.token;
      }
    } catch {}
    return '';
  });
  const [view, setView] = useState('dashboard');
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginErr, setLoginErr] = useState('');
  const [loginBusy, setLoginBusy] = useState(false);
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [leadsTotal, setLeadsTotal] = useState(0);
  const [leadsSearch, setLeadsSearch] = useState('');
  const [leadsFilter, setLeadsFilter] = useState('all');
  const [selectedLead, setSelectedLead] = useState(null);
  const [calMonth, setCalMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [calData, setCalData] = useState({ bookings: [], blocked_slots: [] });
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [custSearch, setCustSearch] = useState('');
  const [custDetail, setCustDetail] = useState(null);
  const [blockForm, setBlockForm] = useState({ date: '', time: '', reason: '', all_day: false });
  const [showBlockForm, setShowBlockForm] = useState(false);
  const [bookingNote, setBookingNote] = useState('');
  const [quotes, setQuotes] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [commStats, setCommStats] = useState(null);
  const [chatSessions, setChatSessions] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [waStatus, setWaStatus] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConvo, setSelectedConvo] = useState(null);
  const [quoteForm, setQuoteForm] = useState({ tier: 'starter', customer_name: '', customer_email: '', customer_company: '', customer_country: 'DE', customer_industry: '', use_case: '', notes: '', discount_percent: 0, discount_reason: '', special_items: [] });
  const [showQuoteForm, setShowQuoteForm] = useState(false);
  const [commBusy, setCommBusy] = useState('');
  const [waMessages, setWaMessages] = useState([]);
  const [waSendTo, setWaSendTo] = useState('');
  const [waSendMsg, setWaSendMsg] = useState('');
  const [waSending, setWaSending] = useState(false);
  const [convoReply, setConvoReply] = useState('');
  const [convoReplying, setConvoReplying] = useState(false);
  const [agentsList, setAgentsList] = useState(null);
  const [agentTask, setAgentTask] = useState('');
  const [agentTarget, setAgentTarget] = useState('');
  const [agentResult, setAgentResult] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [auditData, setAuditData] = useState(null);
  const [auditTimeline, setAuditTimeline] = useState([]);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [leadForm, setLeadForm] = useState({ vorname:'', nachname:'', email:'', unternehmen:'', telefon:'', nachricht:'', source:'admin' });
  const [showCustomerForm, setShowCustomerForm] = useState(false);
  const [customerForm, setCustomerForm] = useState({ vorname:'', nachname:'', email:'', unternehmen:'', telefon:'', branche:'' });
  const [editLead, setEditLead] = useState(null);
  const [editCustomer, setEditCustomer] = useState(null);
  const [editQuote, setEditQuote] = useState(null);
  const [editInvoice, setEditInvoice] = useState(null);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [bookingForm, setBookingForm] = useState({ vorname:'', nachname:'', email:'', telefon:'', unternehmen:'', thema:'', date:'', time:'' });

  const headers = useMemo(() => ({ 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }), [token]);

  const apiFetch = useCallback(async (url, opts = {}) => {
    const r = await fetch(`${API}${url}`, { ...opts, headers: { ...headers, ...opts.headers } });
    if (r.status === 401) { setToken(''); localStorage.removeItem('nx_admin_token'); return null; }
    return r.json();
  }, [headers]);

  const login = async (e) => {
    e.preventDefault(); setLoginErr(''); setLoginBusy(true);
    try {
      const r = await fetch(`${API}/api/admin/login`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${encodeURIComponent(loginForm.email)}&password=${encodeURIComponent(loginForm.password)}` });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Anmeldung fehlgeschlagen');
      setToken(d.access_token); localStorage.setItem('nx_admin_token', d.access_token);
      localStorage.setItem('nx_auth', JSON.stringify({ token: d.access_token, role: 'admin', email: loginEmail }));
    } catch (err) { setLoginErr(err.message); } finally { setLoginBusy(false); }
  };

  /* Load stats */
  useEffect(() => { if (!token) return; apiFetch('/api/admin/stats').then(d => d && setStats(d)); }, [token, apiFetch]);

  /* Load leads */
  useEffect(() => {
    if (!token || view !== 'leads') return;
    const params = new URLSearchParams();
    if (leadsSearch) params.set('search', leadsSearch);
    if (leadsFilter !== 'all') params.set('status', leadsFilter);
    apiFetch(`/api/admin/leads?${params}`).then(d => { if (d) { setLeads(d.leads || []); setLeadsTotal(d.total || 0); } });
  }, [token, view, leadsSearch, leadsFilter, apiFetch]);

  /* Load calendar */
  useEffect(() => {
    if (!token || view !== 'calendar') return;
    apiFetch(`/api/admin/calendar-data?month=${calMonth}`).then(d => d && setCalData(d));
  }, [token, view, calMonth, apiFetch]);

  /* Load customers */
  useEffect(() => {
    if (!token || view !== 'customers') return;
    const params = custSearch ? `?search=${encodeURIComponent(custSearch)}` : '';
    apiFetch(`/api/admin/customers${params}`).then(d => d && setCustomers(d.customers || []));
  }, [token, view, custSearch, apiFetch]);

  /* Load commercial data */
  useEffect(() => {
    if (!token || view !== 'commercial') return;
    apiFetch('/api/admin/quotes').then(d => d && setQuotes(d.quotes || []));
    apiFetch('/api/admin/invoices').then(d => d && setInvoices(d.invoices || []));
    apiFetch('/api/admin/commercial/stats').then(d => d && setCommStats(d));
  }, [token, view, apiFetch]);

  /* Load chat sessions */
  useEffect(() => {
    if (!token || view !== 'chats') return;
    apiFetch('/api/admin/chat-sessions?limit=30').then(d => d && setChatSessions(d.sessions || []));
  }, [token, view, apiFetch]);

  /* Load timeline */
  useEffect(() => {
    if (!token || view !== 'timeline') return;
    apiFetch('/api/admin/timeline?limit=50').then(d => d && setTimeline(d.events || []));
  }, [token, view, apiFetch]);

  /* Load WhatsApp status */
  useEffect(() => {
    if (!token || view !== 'whatsapp') return;
    apiFetch('/api/admin/whatsapp/status').then(d => d && setWaStatus(d));
  }, [token, view, apiFetch]);

  /* Load conversations */
  useEffect(() => {
    if (!token || view !== 'conversations') return;
    apiFetch('/api/admin/conversations?limit=30').then(d => d && setConversations(d.conversations || []));
  }, [token, view, apiFetch]);

  /* ── Update lead status ── */
  const updateLead = async (id, status, notes) => {
    await apiFetch(`/api/admin/leads/${id}`, { method: 'PATCH', body: JSON.stringify({ status, notes }) });
    setLeads(prev => prev.map(l => l.lead_id === id ? { ...l, status } : l));
  };

  /* ── Save full lead edit ── */
  const saveLeadEdit = async () => {
    if (!editLead) return;
    await apiFetch(`/api/admin/leads/${editLead.lead_id}`, { method: 'PATCH', body: JSON.stringify(editLead) });
    setLeads(prev => prev.map(l => l.lead_id === editLead.lead_id ? { ...l, ...editLead } : l));
    setEditLead(null);
  };

  /* ── Save customer edit ── */
  const saveCustomerEdit = async () => {
    if (!editCustomer) return;
    await apiFetch(`/api/admin/customers/${encodeURIComponent(editCustomer.email)}`, { method: 'PATCH', body: JSON.stringify(editCustomer) });
    setEditCustomer(null);
    // Reload
    const params = custSearch ? `?search=${encodeURIComponent(custSearch)}` : '';
    apiFetch(`/api/admin/customers${params}`).then(d => d && setCustomers(d.customers || []));
  };

  /* ── Save quote edit ── */
  const saveQuoteEdit = async () => {
    if (!editQuote) return;
    await apiFetch(`/api/admin/quotes/${editQuote.quote_id}`, { method: 'PATCH', body: JSON.stringify(editQuote) });
    setEditQuote(null);
    apiFetch('/api/admin/quotes').then(d => d && setQuotes(d.quotes || []));
  };

  /* ── Save invoice edit ── */
  const saveInvoiceEdit = async () => {
    if (!editInvoice) return;
    await apiFetch(`/api/admin/invoices/${editInvoice.invoice_id}`, { method: 'PATCH', body: JSON.stringify(editInvoice) });
    setEditInvoice(null);
    apiFetch('/api/admin/invoices').then(d => d && setInvoices(d.invoices || []));
  };

  /* ── Create booking manually ── */
  const createBooking = async () => {
    if (!bookingForm.email.trim() || !bookingForm.date || !bookingForm.time) return;
    const d = await apiFetch('/api/admin/bookings', { method: 'POST', body: JSON.stringify(bookingForm) });
    if (d) {
      setShowBookingForm(false);
      setBookingForm({ vorname:'', nachname:'', email:'', telefon:'', unternehmen:'', thema:'', date:'', time:'' });
      apiFetch(`/api/admin/calendar-data?month=${calMonth}`).then(r => r && setCalData(r));
    }
  };

  /* ── Update booking ── */
  const updateBooking = async (id, updates) => {
    await apiFetch(`/api/admin/bookings/${id}`, { method: 'PATCH', body: JSON.stringify(updates) });
    apiFetch(`/api/admin/calendar-data?month=${calMonth}`).then(d => d && setCalData(d));
    if (selectedBooking?.booking_id === id) {
      setSelectedBooking(prev => ({ ...prev, ...updates }));
    }
  };

  /* ── Delete booking ── */
  const deleteBooking = async (id) => {
    if (!window.confirm('Buchung wirklich löschen?')) return;
    await apiFetch(`/api/admin/bookings/${id}`, { method: 'DELETE' });
    apiFetch(`/api/admin/calendar-data?month=${calMonth}`).then(d => d && setCalData(d));
    setSelectedBooking(null);
  };

  /* ── Block slot ── */
  const createBlockedSlot = async () => {
    if (!blockForm.date) return;
    await apiFetch('/api/admin/blocked-slots', { method: 'POST', body: JSON.stringify(blockForm) });
    apiFetch(`/api/admin/calendar-data?month=${calMonth}`).then(d => d && setCalData(d));
    setBlockForm({ date: '', time: '', reason: '', all_day: false });
    setShowBlockForm(false);
  };

  /* ── Unblock slot ── */
  const deleteBlockedSlot = async (id) => {
    await apiFetch(`/api/admin/blocked-slots/${id}`, { method: 'DELETE' });
    apiFetch(`/api/admin/calendar-data?month=${calMonth}`).then(d => d && setCalData(d));
  };

  /* ── Load customer detail ── */
  const loadCustomerDetail = async (email) => {
    const d = await apiFetch(`/api/admin/customers/${encodeURIComponent(email)}`);
    if (d) setCustDetail({ email, ...d });
  };

  /* ── Load chat detail ── */
  const loadChatDetail = async (sessionId) => {
    const d = await apiFetch(`/api/admin/chat-sessions/${sessionId}`);
    if (d) setSelectedChat(d);
  };

  /* ── WA message loading ── */
  const loadWaMessages = useCallback(async () => {
    const d = await apiFetch('/api/admin/whatsapp/messages?limit=30');
    if (d) setWaMessages(d.messages || []);
  }, [apiFetch]);

  useEffect(() => {
    if (!token || view !== 'whatsapp') return;
    loadWaMessages();
  }, [token, view, loadWaMessages]);

  /* ── Agent list loading ── */
  const loadAgents = useCallback(async () => {
    const d = await apiFetch('/api/admin/agents');
    if (d) setAgentsList(d);
  }, [apiFetch]);

  useEffect(() => {
    if (!token || view !== 'agents') return;
    loadAgents();
  }, [token, view, loadAgents]);

  /* ── Audit loading ── */
  const loadAudit = useCallback(async () => {
    const [health, tl] = await Promise.all([
      apiFetch('/api/admin/audit/health'),
      apiFetch('/api/admin/audit/timeline?hours=48&limit=50'),
    ]);
    if (health) setAuditData(health);
    if (tl) setAuditTimeline(tl.events || []);
  }, [apiFetch]);

  useEffect(() => {
    if (!token || view !== 'audit') return;
    loadAudit();
  }, [token, view, loadAudit]);

  const logout = () => { setToken(''); localStorage.removeItem('nx_admin_token'); localStorage.removeItem('nx_auth'); };

  /* ══════════ LOGIN SCREEN ══════════ */
  if (!token) return (
    <div className="adm-login" data-testid="admin-login">
      <div className="adm-login-left">
        <div className="adm-login-brand">
          <div className="adm-login-logo"><img src="/icon-mark.svg" alt="" width="44" height="44" /><span>NeXify<em>AI</em></span></div>
          <p className="adm-login-tagline">Intelligente Automatisierung für Ihr Unternehmen</p>
        </div>
        <div className="adm-login-features">
          <div className="adm-login-feature"><I n="smart_toy" /><div><strong>9 KI-Agenten</strong><span>Automatisiertes Lead-Management, Outreach und Support</span></div></div>
          <div className="adm-login-feature"><I n="forum" /><div><strong>Zentrale Kommunikation</strong><span>Chat, E-Mail, WhatsApp und Portal in einer Timeline</span></div></div>
          <div className="adm-login-feature"><I n="verified" /><div><strong>Echtzeit-Audit</strong><span>Systemgesundheit und Aktivitäten live überwachen</span></div></div>
        </div>
      </div>
      <div className="adm-login-right">
        <div className="adm-login-box">
          <h1>Willkommen zurück</h1>
          <p className="adm-login-subtitle">Melden Sie sich an, um fortzufahren</p>
          <form onSubmit={login} data-testid="admin-login-form">
            <div className="adm-field"><label>E-Mail-Adresse</label><input type="email" value={loginForm.email} onChange={e => setLoginForm({ ...loginForm, email: e.target.value })} required placeholder="admin@nexifyai.de" data-testid="admin-email" /></div>
            <div className="adm-field"><label>Passwort</label><input type="password" value={loginForm.password} onChange={e => setLoginForm({ ...loginForm, password: e.target.value })} required placeholder="Ihr Passwort" data-testid="admin-password" /></div>
            {loginErr && <div className="adm-err" data-testid="admin-login-error">{loginErr}</div>}
            <button type="submit" className="adm-btn-primary" disabled={loginBusy} data-testid="admin-login-btn">{loginBusy ? 'Anmeldung läuft...' : 'Anmelden'}</button>
          </form>
          <p className="adm-login-footer">Geschützter Bereich — Nur autorisierte Nutzer</p>
        </div>
      </div>
    </div>
  );

  /* ══════════ DASHBOARD VIEW ══════════ */
  const DashboardView = () => (
    <div className="adm-dashboard" data-testid="admin-dashboard">
      <h2>Dashboard</h2>
      <div className="adm-stat-grid">
        <div className="adm-stat-card"><div className="adm-stat-icon"><I n="people" /></div><div className="adm-stat-val">{stats?.leads_total || 0}</div><div className="adm-stat-label">Leads gesamt</div></div>
        <div className="adm-stat-card hl"><div className="adm-stat-icon"><I n="trending_up" /></div><div className="adm-stat-val">{stats?.leads_new || 0}</div><div className="adm-stat-label">Neue Leads</div></div>
        <div className="adm-stat-card"><div className="adm-stat-icon"><I n="calendar_month" /></div><div className="adm-stat-val">{stats?.bookings_total || 0}</div><div className="adm-stat-label">Buchungen</div></div>
        <div className="adm-stat-card"><div className="adm-stat-icon"><I n="forum" /></div><div className="adm-stat-val">{stats?.chat_sessions_total || 0}</div><div className="adm-stat-label">Chat-Sessions</div></div>
      </div>
      {stats?.recent_leads?.length > 0 && (
        <div className="adm-recent">
          <h3>Neueste Leads</h3>
          <div className="adm-table-wrap">
            <table className="adm-table" data-testid="dashboard-recent-table">
              <thead><tr><th>Name</th><th>E-Mail</th><th>Quelle</th><th>Status</th><th>Datum</th></tr></thead>
              <tbody>
                {stats.recent_leads.slice(0, 10).map((l, i) => (
                  <tr key={i}><td>{l.vorname} {l.nachname}</td><td>{l.email}</td><td>{l.source}</td>
                    <td><span className="adm-badge" style={{ background: STATUS_MAP[l.status]?.color + '22', color: STATUS_MAP[l.status]?.color }}>{STATUS_MAP[l.status]?.label || l.status}</span></td>
                    <td>{fmtTime(l.created_at)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  /* ══════════ LEADS VIEW ══════════ */
  const createLead = async () => {
    if (!leadForm.email.trim()) return;
    const d = await apiFetch('/api/admin/leads', { method: 'POST', body: JSON.stringify(leadForm) });
    if (d) { setShowLeadForm(false); setLeadForm({ vorname:'', nachname:'', email:'', unternehmen:'', telefon:'', nachricht:'', source:'admin' }); }
  };
  const LeadsView = () => (
    <div className="adm-leads" data-testid="admin-leads">
      <div className="adm-leads-header">
        <h2>Leads ({leadsTotal})</h2>
        <div className="adm-leads-controls">
          <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => setShowLeadForm(true)} data-testid="add-lead-btn"><I n="person_add" /> Neuer Lead</button>
          <div className="adm-search"><I n="search" /><input placeholder="Suchen..." value={leadsSearch} onChange={e => setLeadsSearch(e.target.value)} data-testid="leads-search" /></div>
          <select className="adm-select" value={leadsFilter} onChange={e => setLeadsFilter(e.target.value)} data-testid="leads-filter">
            <option value="all">Alle</option>
            {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
      </div>
      {showLeadForm && (
        <div className="adm-form-card" data-testid="lead-form">
          <h3>Lead manuell anlegen</h3>
          <div className="adm-form-grid">
            <div className="adm-field"><label>Vorname</label><input value={leadForm.vorname} onChange={e => setLeadForm({...leadForm, vorname: e.target.value})} placeholder="Max" /></div>
            <div className="adm-field"><label>Nachname *</label><input value={leadForm.nachname} onChange={e => setLeadForm({...leadForm, nachname: e.target.value})} placeholder="Mustermann" /></div>
            <div className="adm-field"><label>E-Mail *</label><input type="email" value={leadForm.email} onChange={e => setLeadForm({...leadForm, email: e.target.value})} placeholder="max@firma.de" /></div>
            <div className="adm-field"><label>Unternehmen</label><input value={leadForm.unternehmen} onChange={e => setLeadForm({...leadForm, unternehmen: e.target.value})} placeholder="Firma GmbH" /></div>
            <div className="adm-field"><label>Telefon</label><input value={leadForm.telefon} onChange={e => setLeadForm({...leadForm, telefon: e.target.value})} placeholder="+49 171 234 5678" /></div>
            <div className="adm-field"><label>Quelle</label><select className="adm-select" value={leadForm.source} onChange={e => setLeadForm({...leadForm, source: e.target.value})}><option value="admin">Admin</option><option value="website">Website</option><option value="empfehlung">Empfehlung</option><option value="messe">Messe</option><option value="social">Social Media</option></select></div>
          </div>
          <div className="adm-field" style={{gridColumn:'1/-1'}}><label>Notiz</label><textarea value={leadForm.nachricht} onChange={e => setLeadForm({...leadForm, nachricht: e.target.value})} rows={2} placeholder="Optionale Notiz zum Lead..." style={{width:'100%',resize:'vertical'}} /></div>
          <div className="adm-form-actions">
            <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={createLead} disabled={!leadForm.email.trim()} data-testid="save-lead-btn"><I n="check" /> Speichern</button>
            <button className="adm-btn adm-btn-secondary" onClick={() => setShowLeadForm(false)}>Abbrechen</button>
          </div>
        </div>
      )}
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="leads-table">
          <thead><tr><th>Name</th><th>E-Mail</th><th>Unternehmen</th><th>Quelle</th><th>Status</th><th>Datum</th><th>Aktionen</th></tr></thead>
          <tbody>
            {leads.map((l, i) => (
              <tr key={i} className={selectedLead?.lead_id === l.lead_id ? 'active' : ''} onClick={() => setSelectedLead(l)}>
                <td>{l.vorname} {l.nachname}</td><td>{l.email}</td><td>{l.unternehmen || '-'}</td><td>{l.source}</td>
                <td><span className="adm-badge" style={{ background: STATUS_MAP[l.status]?.color + '22', color: STATUS_MAP[l.status]?.color }}>{STATUS_MAP[l.status]?.label || l.status}</span></td>
                <td>{fmtTime(l.created_at)}</td>
                <td style={{display:'flex',gap:'4px'}} onClick={e => e.stopPropagation()}>
                  <select className="adm-select-sm" value={l.status} onChange={e => updateLead(l.lead_id, e.target.value)}>
                    {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                  <button className="adm-btn-sm" onClick={() => setEditLead({...l, notes: ''})} title="Bearbeiten" data-testid={`edit-lead-${l.lead_id}`}><I n="edit" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {leads.length === 0 && <div className="adm-empty">Keine Leads gefunden</div>}

      {/* Lead Edit Modal */}
      {editLead && (
        <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setEditLead(null)}>
          <div className="adm-modal" data-testid="lead-edit-modal">
            <h3>Lead bearbeiten</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Vorname</label><input value={editLead.vorname||''} onChange={e => setEditLead({...editLead, vorname: e.target.value})} /></div>
              <div className="adm-field"><label>Nachname</label><input value={editLead.nachname||''} onChange={e => setEditLead({...editLead, nachname: e.target.value})} /></div>
              <div className="adm-field"><label>E-Mail</label><input type="email" value={editLead.email||''} onChange={e => setEditLead({...editLead, email: e.target.value})} /></div>
              <div className="adm-field"><label>Unternehmen</label><input value={editLead.unternehmen||''} onChange={e => setEditLead({...editLead, unternehmen: e.target.value})} /></div>
              <div className="adm-field"><label>Telefon</label><input value={editLead.telefon||''} onChange={e => setEditLead({...editLead, telefon: e.target.value})} /></div>
              <div className="adm-field"><label>Quelle</label><select className="adm-select" value={editLead.source||'admin'} onChange={e => setEditLead({...editLead, source: e.target.value})}><option value="admin">Admin</option><option value="website">Website</option><option value="empfehlung">Empfehlung</option><option value="messe">Messe</option><option value="social">Social Media</option><option value="chat">Chat</option></select></div>
              <div className="adm-field"><label>Status</label><select className="adm-select" value={editLead.status||'neu'} onChange={e => setEditLead({...editLead, status: e.target.value})}>{Object.entries(STATUS_MAP).map(([k,v])=><option key={k} value={k}>{v.label}</option>)}</select></div>
            </div>
            <div className="adm-field" style={{marginTop:8}}><label>Notiz hinzufügen</label><textarea value={editLead.notes||''} onChange={e => setEditLead({...editLead, notes: e.target.value})} rows={2} style={{width:'100%',resize:'vertical'}} placeholder="Interne Notiz..." /></div>
            <div className="adm-modal-actions">
              <button className="adm-btn-secondary" onClick={() => setEditLead(null)}>Abbrechen</button>
              <button className="adm-btn-primary" onClick={saveLeadEdit} data-testid="save-lead-edit-btn">Speichern</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  /* ══════════ CALENDAR VIEW ══════════ */
  const CalendarView = () => {
    const [y, m] = calMonth.split('-').map(Number);
    const firstDay = new Date(y, m - 1, 1).getDay();
    const daysInMonth = new Date(y, m, 0).getDate();
    const shift = firstDay === 0 ? 6 : firstDay - 1;
    const today = new Date().toISOString().slice(0, 10);
    const dayNames = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

    const prevMonth = () => { const d = new Date(y, m - 2, 1); setCalMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`); setSelectedDate(null); };
    const nextMonth = () => { const d = new Date(y, m, 1); setCalMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`); setSelectedDate(null); };

    const getDayBookings = (day) => {
      const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      return calData.bookings.filter(b => b.date === dateStr);
    };
    const getDayBlocked = (day) => {
      const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      return calData.blocked_slots.filter(b => b.date === dateStr);
    };

    const selectedDateStr = selectedDate ? `${y}-${String(m).padStart(2, '0')}-${String(selectedDate).padStart(2, '0')}` : null;
    const dayBookings = selectedDate ? getDayBookings(selectedDate) : [];
    const dayBlocked = selectedDate ? getDayBlocked(selectedDate) : [];

    return (
      <div className="adm-calendar" data-testid="admin-calendar">
        <div className="adm-cal-header">
          <h2>Kalender</h2>
          <div className="adm-cal-actions">
            <button className="adm-btn-sm" onClick={() => { setBookingForm({...bookingForm, date: selectedDateStr || ''}); setShowBookingForm(true); }} data-testid="create-booking-btn"><I n="event" /> Termin anlegen</button>
            <button className="adm-btn-sm" onClick={() => { setBlockForm({ ...blockForm, date: selectedDateStr || '' }); setShowBlockForm(true); }} data-testid="block-slot-btn"><I n="block" /> Slot blockieren</button>
          </div>
        </div>

        <div className="adm-cal-nav">
          <button className="adm-btn-icon" onClick={prevMonth}><I n="chevron_left" /></button>
          <h3>{new Date(y, m - 1).toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })}</h3>
          <button className="adm-btn-icon" onClick={nextMonth}><I n="chevron_right" /></button>
        </div>

        <div className="adm-cal-grid">
          {dayNames.map(d => <div key={d} className="adm-cal-day-name">{d}</div>)}
          {Array.from({ length: shift }, (_, i) => <div key={`e-${i}`} className="adm-cal-cell empty"></div>)}
          {Array.from({ length: daysInMonth }, (_, i) => {
            const day = i + 1;
            const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const bookings = getDayBookings(day);
            const blocked = getDayBlocked(day);
            const isToday = dateStr === today;
            const isSelected = selectedDate === day;
            const hasAllDayBlock = blocked.some(b => b.all_day);
            return (
              <div
                key={day}
                className={`adm-cal-cell ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''} ${hasAllDayBlock ? 'blocked' : ''}`}
                onClick={() => setSelectedDate(day)}
                data-testid={`cal-day-${day}`}
              >
                <div className="adm-cal-day-num">{day}</div>
                <div className="adm-cal-indicators">
                  {bookings.length > 0 && <span className="adm-cal-dot booking">{bookings.length}</span>}
                  {blocked.length > 0 && <span className="adm-cal-dot blocked"><I n="block" /></span>}
                </div>
              </div>
            );
          })}
        </div>

        {/* Day Detail Panel */}
        {selectedDate && (
          <div className="adm-day-detail" data-testid="cal-day-detail">
            <h3>{fmtDateLong(selectedDateStr)}</h3>
            <div className="adm-day-sections">
              <div className="adm-day-section">
                <h4><I n="event" /> Termine ({dayBookings.length})</h4>
                {dayBookings.length === 0 && <p className="adm-muted">Keine Termine an diesem Tag</p>}
                {dayBookings.map(b => {
                  const st = BOOKING_STATUS[b.status] || BOOKING_STATUS.pending;
                  return (
                    <div key={b.booking_id} className={`adm-booking-card ${selectedBooking?.booking_id === b.booking_id ? 'active' : ''}`} onClick={() => setSelectedBooking(b)} data-testid={`booking-${b.booking_id}`}>
                      <div className="adm-booking-time">{b.time}</div>
                      <div className="adm-booking-info">
                        <div className="adm-booking-name">{b.vorname} {b.nachname}</div>
                        <div className="adm-booking-email">{b.email}</div>
                        {b.unternehmen && <div className="adm-booking-company">{b.unternehmen}</div>}
                      </div>
                      <span className="adm-badge" style={{ background: st.color + '22', color: st.color }}><I n={st.icon} /> {st.label}</span>
                    </div>
                  );
                })}
              </div>
              <div className="adm-day-section">
                <h4><I n="block" /> Blockierungen ({dayBlocked.length})</h4>
                {dayBlocked.length === 0 && <p className="adm-muted">Keine Blockierungen</p>}
                {dayBlocked.map(b => (
                  <div key={b.slot_id} className="adm-blocked-card">
                    <div><strong>{b.all_day ? 'Ganzer Tag' : b.time}</strong>{b.reason && <span className="adm-muted"> — {b.reason}</span>}</div>
                    <button className="adm-btn-danger-sm" onClick={() => deleteBlockedSlot(b.slot_id)} data-testid={`unblock-${b.slot_id}`}><I n="delete" /></button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Booking Detail Panel */}
        {selectedBooking && (
          <div className="adm-booking-detail" data-testid="booking-detail">
            <div className="adm-detail-header">
              <h3>Buchung: {selectedBooking.booking_id}</h3>
              <button className="adm-btn-icon" onClick={() => setSelectedBooking(null)}><I n="close" /></button>
            </div>
            <div className="adm-detail-grid">
              <div className="adm-detail-field"><label>Name</label><span>{selectedBooking.vorname} {selectedBooking.nachname}</span></div>
              <div className="adm-detail-field"><label>E-Mail</label><span>{selectedBooking.email}</span></div>
              <div className="adm-detail-field"><label>Telefon</label><span>{selectedBooking.telefon || '-'}</span></div>
              <div className="adm-detail-field"><label>Unternehmen</label><span>{selectedBooking.unternehmen || '-'}</span></div>
              <div className="adm-detail-field"><label>Datum</label><span>{fmtDateLong(selectedBooking.date)}</span></div>
              <div className="adm-detail-field"><label>Uhrzeit</label><span>{selectedBooking.time}</span></div>
              <div className="adm-detail-field"><label>Thema</label><span>{selectedBooking.thema || '-'}</span></div>
            </div>
            <div className="adm-detail-actions">
              <label>Status ändern:</label>
              <div className="adm-status-btns">
                {Object.entries(BOOKING_STATUS).map(([k, v]) => (
                  <button
                    key={k}
                    className={`adm-status-btn ${selectedBooking.status === k ? 'active' : ''}`}
                    style={{ '--sc': v.color }}
                    onClick={() => updateBooking(selectedBooking.booking_id, { status: k })}
                    data-testid={`booking-status-${k}`}
                  ><I n={v.icon} /> {v.label}</button>
                ))}
              </div>
            </div>
            <div className="adm-detail-notes">
              <label>Notiz hinzufügen:</label>
              <div className="adm-note-input">
                <input type="text" value={bookingNote} onChange={e => setBookingNote(e.target.value)} placeholder="Interne Notiz..." data-testid="booking-note-input" />
                <button className="adm-btn-sm" onClick={() => { if (bookingNote.trim()) { updateBooking(selectedBooking.booking_id, { notes: bookingNote }); setBookingNote(''); } }} data-testid="booking-note-save"><I n="save" /></button>
              </div>
              {selectedBooking.notes?.length > 0 && (
                <div className="adm-notes-list">
                  {selectedBooking.notes.map((n, i) => (
                    <div key={i} className="adm-note-item"><span className="adm-note-text">{n.text || n}</span><span className="adm-note-meta">{n.by} — {fmtTime(n.at)}</span></div>
                  ))}
                </div>
              )}
            </div>
            <div className="adm-detail-danger">
              <button className="adm-btn-danger" onClick={() => deleteBooking(selectedBooking.booking_id)} data-testid="booking-delete"><I n="delete" /> Buchung löschen</button>
            </div>
          </div>
        )}

        {/* Booking Create Modal */}
        {showBookingForm && (
          <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setShowBookingForm(false)}>
            <div className="adm-modal" data-testid="booking-create-modal">
              <h3>Termin manuell anlegen</h3>
              <div className="adm-form-grid">
                <div className="adm-field"><label>Vorname *</label><input value={bookingForm.vorname} onChange={e => setBookingForm({...bookingForm, vorname: e.target.value})} placeholder="Max" /></div>
                <div className="adm-field"><label>Nachname</label><input value={bookingForm.nachname} onChange={e => setBookingForm({...bookingForm, nachname: e.target.value})} placeholder="Mustermann" /></div>
                <div className="adm-field"><label>E-Mail *</label><input type="email" value={bookingForm.email} onChange={e => setBookingForm({...bookingForm, email: e.target.value})} placeholder="max@firma.de" /></div>
                <div className="adm-field"><label>Telefon</label><input value={bookingForm.telefon} onChange={e => setBookingForm({...bookingForm, telefon: e.target.value})} placeholder="+49 171 234 5678" /></div>
                <div className="adm-field"><label>Unternehmen</label><input value={bookingForm.unternehmen} onChange={e => setBookingForm({...bookingForm, unternehmen: e.target.value})} placeholder="Firma GmbH" /></div>
                <div className="adm-field"><label>Thema</label><input value={bookingForm.thema} onChange={e => setBookingForm({...bookingForm, thema: e.target.value})} placeholder="z.B. Erstgespräch, Demo" /></div>
                <div className="adm-field"><label>Datum *</label><input type="date" value={bookingForm.date} onChange={e => setBookingForm({...bookingForm, date: e.target.value})} data-testid="booking-date" /></div>
                <div className="adm-field"><label>Uhrzeit *</label>
                  <select value={bookingForm.time} onChange={e => setBookingForm({...bookingForm, time: e.target.value})} className="adm-select" data-testid="booking-time">
                    <option value="">Wählen...</option>
                    {['09:00','09:30','10:00','10:30','11:00','11:30','14:00','14:30','15:00','15:30','16:00','16:30','17:00'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
              <div className="adm-modal-actions">
                <button className="adm-btn-secondary" onClick={() => setShowBookingForm(false)}>Abbrechen</button>
                <button className="adm-btn-primary" onClick={createBooking} disabled={!bookingForm.email.trim() || !bookingForm.date || !bookingForm.time} data-testid="save-booking-btn">Termin anlegen</button>
              </div>
            </div>
          </div>
        )}

        {/* Block Slot Modal */}
        {showBlockForm && (
          <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setShowBlockForm(false)}>
            <div className="adm-modal" data-testid="block-slot-modal">
              <h3>Zeitslot blockieren</h3>
              <div className="adm-field"><label>Datum *</label><input type="date" value={blockForm.date} onChange={e => setBlockForm({ ...blockForm, date: e.target.value })} data-testid="block-date" /></div>
              <div className="adm-field"><label className="adm-checkbox-label"><input type="checkbox" checked={blockForm.all_day} onChange={e => setBlockForm({ ...blockForm, all_day: e.target.checked, time: '' })} /> Ganzer Tag</label></div>
              {!blockForm.all_day && (
                <div className="adm-field"><label>Uhrzeit</label>
                  <select value={blockForm.time} onChange={e => setBlockForm({ ...blockForm, time: e.target.value })} className="adm-select" data-testid="block-time">
                    <option value="">Wählen...</option>
                    {['09:00','09:30','10:00','10:30','11:00','11:30','14:00','14:30','15:00','15:30','16:00','16:30'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              )}
              <div className="adm-field"><label>Grund</label><input type="text" value={blockForm.reason} onChange={e => setBlockForm({ ...blockForm, reason: e.target.value })} placeholder="z.B. Team Meeting, Urlaub..." data-testid="block-reason" /></div>
              <div className="adm-modal-actions">
                <button className="adm-btn-secondary" onClick={() => setShowBlockForm(false)}>Abbrechen</button>
                <button className="adm-btn-primary" onClick={createBlockedSlot} disabled={!blockForm.date} data-testid="block-submit">Blockieren</button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  /* ══════════ CUSTOMERS VIEW ══════════ */
  const createCustomer = async () => {
    if (!customerForm.email.trim()) return;
    const d = await apiFetch('/api/admin/customers', { method: 'POST', body: JSON.stringify(customerForm) });
    if (d) { setShowCustomerForm(false); setCustomerForm({ vorname:'', nachname:'', email:'', unternehmen:'', telefon:'', branche:'' }); }
  };
  const generatePortalAccess = async (email) => {
    const d = await apiFetch('/api/admin/customers/portal-access', { method: 'POST', body: JSON.stringify({ email }) });
    if (d?.portal_url) { navigator.clipboard?.writeText(d.portal_url); alert(`Portalzugang erstellt und kopiert:\n${d.portal_url}`); }
  };
  const CustomersView = () => (
    <div className="adm-customers" data-testid="admin-customers">
      <div className="adm-leads-header">
        <h2>Kunden ({customers.length})</h2>
        <div className="adm-leads-controls">
          <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => setShowCustomerForm(true)} data-testid="add-customer-btn"><I n="person_add" /> Neuer Kunde</button>
          <div className="adm-search"><I n="search" /><input placeholder="Suchen..." value={custSearch} onChange={e => setCustSearch(e.target.value)} data-testid="customer-search" /></div>
        </div>
      </div>
      {showCustomerForm && (
        <div className="adm-form-card" data-testid="customer-form">
          <h3>Kunden manuell anlegen</h3>
          <div className="adm-form-grid">
            <div className="adm-field"><label>Vorname</label><input value={customerForm.vorname} onChange={e => setCustomerForm({...customerForm, vorname: e.target.value})} placeholder="Max" /></div>
            <div className="adm-field"><label>Nachname</label><input value={customerForm.nachname} onChange={e => setCustomerForm({...customerForm, nachname: e.target.value})} placeholder="Mustermann" /></div>
            <div className="adm-field"><label>E-Mail *</label><input type="email" value={customerForm.email} onChange={e => setCustomerForm({...customerForm, email: e.target.value})} placeholder="max@firma.de" /></div>
            <div className="adm-field"><label>Unternehmen</label><input value={customerForm.unternehmen} onChange={e => setCustomerForm({...customerForm, unternehmen: e.target.value})} placeholder="Firma GmbH" /></div>
            <div className="adm-field"><label>Telefon</label><input value={customerForm.telefon} onChange={e => setCustomerForm({...customerForm, telefon: e.target.value})} placeholder="+49 171 234 5678" /></div>
            <div className="adm-field"><label>Branche</label><input value={customerForm.branche} onChange={e => setCustomerForm({...customerForm, branche: e.target.value})} placeholder="z.B. Logistik, IT, Gesundheit" /></div>
          </div>
          <div className="adm-form-actions">
            <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={createCustomer} disabled={!customerForm.email.trim()} data-testid="save-customer-btn"><I n="check" /> Speichern</button>
            <button className="adm-btn adm-btn-secondary" onClick={() => setShowCustomerForm(false)}>Abbrechen</button>
          </div>
        </div>
      )}
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="customers-table">
          <thead><tr><th>Name</th><th>E-Mail</th><th>Unternehmen</th><th>Anfragen</th><th>Buchungen</th><th>Erster Kontakt</th><th>Aktionen</th></tr></thead>
          <tbody>
            {customers.map((c, i) => (
              <tr key={i} className={custDetail?.email === c.email ? 'active' : ''} onClick={() => loadCustomerDetail(c.email)} data-testid={`customer-row-${i}`}>
                <td>{c.vorname} {c.nachname}</td><td>{c.email}</td><td>{c.unternehmen || '-'}</td>
                <td><span className="adm-badge">{c.total_leads}</span></td>
                <td><span className="adm-badge">{c.total_bookings}</span></td>
                <td>{fmtDate(c.first_contact)}</td>
                <td onClick={e => e.stopPropagation()} style={{display:'flex',gap:'4px'}}>
                  <button className="adm-btn-sm" onClick={() => setEditCustomer({email:c.email, vorname:c.vorname||'', nachname:c.nachname||'', unternehmen:c.unternehmen||'', telefon:c.telefon||'', branche:c.branche||''})} title="Bearbeiten" data-testid={`edit-customer-${i}`}><I n="edit" /></button>
                  <button className="adm-btn-sm" style={{color:'#ff9b7a'}} onClick={() => generatePortalAccess(c.email)} title="Portalzugang" data-testid={`portal-btn-${i}`}><I n="link" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {customers.length === 0 && <div className="adm-empty">Keine Kunden gefunden</div>}

      {/* Customer Detail */}
      {custDetail && (
        <div className="adm-cust-detail" data-testid="customer-detail">
          <div className="adm-detail-header">
            <h3>{custDetail.email}</h3>
            <div style={{display:'flex',gap:8}}>
              <button className="adm-btn-sm" onClick={() => setEditCustomer({email:custDetail.email, vorname:'', nachname:'', unternehmen:'', telefon:'', branche:''})} title="Bearbeiten" data-testid="edit-customer-detail-btn"><I n="edit" /></button>
              <button className="adm-btn-sm" style={{color:'#ff9b7a'}} onClick={() => generatePortalAccess(custDetail.email)} data-testid="portal-access-btn" title="Portalzugang erstellen"><I n="link" /> Portal</button>
              <button className="adm-btn-icon" onClick={() => setCustDetail(null)}><I n="close" /></button>
            </div>
          </div>
          <div className="adm-cust-tabs">
            <div className="adm-cust-tab-content">
              <h4><I n="mail" /> Anfragen ({custDetail.leads?.length || 0})</h4>
              {custDetail.leads?.map((l, i) => (
                <div key={i} className="adm-cust-item">
                  <span className="adm-badge" style={{ background: STATUS_MAP[l.status]?.color + '22', color: STATUS_MAP[l.status]?.color }}>{STATUS_MAP[l.status]?.label || l.status}</span>
                  <span>{l.source} — {fmtTime(l.created_at)}</span>
                  {l.nachricht && <p className="adm-muted">{l.nachricht}</p>}
                </div>
              ))}
              <h4 style={{ marginTop: 20 }}><I n="calendar_month" /> Buchungen ({custDetail.bookings?.length || 0})</h4>
              {custDetail.bookings?.map((b, i) => {
                const st = BOOKING_STATUS[b.status] || BOOKING_STATUS.pending;
                return (
                  <div key={i} className="adm-cust-item">
                    <span className="adm-badge" style={{ background: st.color + '22', color: st.color }}>{st.label}</span>
                    <span>{fmtDate(b.date)} um {b.time}</span>
                    {b.thema && <p className="adm-muted">{b.thema}</p>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Customer Edit Modal */}
      {editCustomer && (
        <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setEditCustomer(null)}>
          <div className="adm-modal" data-testid="customer-edit-modal">
            <h3>Kunde bearbeiten: {editCustomer.email}</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Vorname</label><input value={editCustomer.vorname} onChange={e => setEditCustomer({...editCustomer, vorname: e.target.value})} /></div>
              <div className="adm-field"><label>Nachname</label><input value={editCustomer.nachname} onChange={e => setEditCustomer({...editCustomer, nachname: e.target.value})} /></div>
              <div className="adm-field"><label>Unternehmen</label><input value={editCustomer.unternehmen} onChange={e => setEditCustomer({...editCustomer, unternehmen: e.target.value})} /></div>
              <div className="adm-field"><label>Telefon</label><input value={editCustomer.telefon} onChange={e => setEditCustomer({...editCustomer, telefon: e.target.value})} /></div>
              <div className="adm-field"><label>Branche</label><input value={editCustomer.branche} onChange={e => setEditCustomer({...editCustomer, branche: e.target.value})} /></div>
            </div>
            <div className="adm-modal-actions">
              <button className="adm-btn-secondary" onClick={() => setEditCustomer(null)}>Abbrechen</button>
              <button className="adm-btn-primary" onClick={saveCustomerEdit} data-testid="save-customer-edit-btn">Speichern</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  /* ══════════ COMMERCIAL VIEW ══════════ */
  const createQuote = async (e) => {
    e.preventDefault(); setCommBusy('create');
    try {
      await apiFetch('/api/admin/quotes', { method: 'POST', body: JSON.stringify(quoteForm) });
      setShowQuoteForm(false); setQuoteForm({ tier: 'starter', customer_name: '', customer_email: '', customer_company: '', customer_country: 'DE', customer_industry: '', use_case: '', notes: '', discount_percent: 0, discount_reason: '', special_items: [] });
      apiFetch('/api/admin/quotes').then(d => d && setQuotes(d.quotes || []));
      apiFetch('/api/admin/commercial/stats').then(d => d && setCommStats(d));
    } catch (e) { alert(e.message); } finally { setCommBusy(''); }
  };

  const sendQuote = async (qid) => {
    setCommBusy(`send_${qid}`);
    try {
      await apiFetch(`/api/admin/quotes/${qid}/send`, { method: 'POST' });
      apiFetch('/api/admin/quotes').then(d => d && setQuotes(d.quotes || []));
    } catch (e) { alert(e.message); } finally { setCommBusy(''); }
  };

  const sendInvoice = async (iid) => {
    setCommBusy(`send_inv_${iid}`);
    try {
      await apiFetch(`/api/admin/invoices/${iid}/send`, { method: 'POST' });
      apiFetch('/api/admin/invoices').then(d => d && setInvoices(d.invoices || []));
    } catch (e) { alert(e.message); } finally { setCommBusy(''); }
  };

  const markPaid = async (iid) => {
    if (!window.confirm('Rechnung als bezahlt markieren?')) return;
    setCommBusy(`pay_${iid}`);
    try {
      await apiFetch(`/api/admin/invoices/${iid}/mark-paid`, { method: 'POST' });
      apiFetch('/api/admin/invoices').then(d => d && setInvoices(d.invoices || []));
      apiFetch('/api/admin/commercial/stats').then(d => d && setCommStats(d));
    } catch (e) { alert(e.message); } finally { setCommBusy(''); }
  };

  const QUOTE_STATUS = { draft: {l:'Entwurf',c:'#3b82f6'}, generated: {l:'Erstellt',c:'#8b5cf6'}, sent: {l:'Versendet',c:'#f59e0b'}, opened: {l:'Geöffnet',c:'#06b6d4'}, accepted: {l:'Angenommen',c:'#10b981'}, declined: {l:'Abgelehnt',c:'#ef4444'}, revision_requested: {l:'Änderung',c:'#f97316'} };
  const INV_STATUS = { created: {l:'Erstellt',c:'#3b82f6'}, sent: {l:'Versendet',c:'#f59e0b'}, payment_completed: {l:'Bezahlt',c:'#10b981'}, payment_pending: {l:'Ausstehend',c:'#f59e0b'}, payment_failed: {l:'Fehlgeschlagen',c:'#ef4444'}, overdue: {l:'Überfällig',c:'#dc2626'} };
  const PAY_STATUS = { pending: {l:'Ausstehend',c:'#f59e0b'}, paid: {l:'Bezahlt',c:'#10b981'}, failed: {l:'Fehlgeschlagen',c:'#ef4444'} };

  const CommercialView = () => (
    <div className="adm-dashboard" data-testid="admin-commercial">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'20px'}}>
        <h2>Angebote & Rechnungen</h2>
        <button className="adm-btn-primary" onClick={() => setShowQuoteForm(true)} data-testid="create-quote-btn"><I n="add" /> Neues Angebot</button>
      </div>

      {commStats && (
        <div className="adm-stat-grid" style={{marginBottom:'24px'}}>
          <div className="adm-stat-card"><div className="adm-stat-icon"><I n="description" /></div><div className="adm-stat-val">{commStats.quotes?.total||0}</div><div className="adm-stat-label">Angebote</div></div>
          <div className="adm-stat-card hl"><div className="adm-stat-icon"><I n="check_circle" /></div><div className="adm-stat-val">{commStats.quotes?.accepted||0}</div><div className="adm-stat-label">Angenommen</div></div>
          <div className="adm-stat-card"><div className="adm-stat-icon"><I n="receipt_long" /></div><div className="adm-stat-val">{commStats.invoices?.total||0}</div><div className="adm-stat-label">Rechnungen</div></div>
          <div className="adm-stat-card hl"><div className="adm-stat-icon"><I n="payments" /></div><div className="adm-stat-val">{fmtEur(commStats.revenue?.total_gross)}</div><div className="adm-stat-label">Umsatz (brutto)</div></div>
        </div>
      )}

      {showQuoteForm && (
        <div className="adm-card" style={{marginBottom:'24px',padding:'20px'}} data-testid="quote-form">
          <h3 style={{margin:'0 0 16px',color:'#fff'}}>Neues Angebot erstellen</h3>
          <form onSubmit={createQuote}>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'12px'}}>
              <div className="adm-field"><label>Tarif</label><select value={quoteForm.tier} onChange={e=>setQuoteForm({...quoteForm,tier:e.target.value})} data-testid="quote-tier"><option value="starter">Starter AI Agenten AG (499 EUR/Mo)</option><option value="growth">Growth AI Agenten AG (1.299 EUR/Mo)</option></select></div>
              <div className="adm-field"><label>Name</label><input value={quoteForm.customer_name} onChange={e=>setQuoteForm({...quoteForm,customer_name:e.target.value})} required data-testid="quote-name" /></div>
              <div className="adm-field"><label>E-Mail</label><input type="email" value={quoteForm.customer_email} onChange={e=>setQuoteForm({...quoteForm,customer_email:e.target.value})} required data-testid="quote-email" /></div>
              <div className="adm-field"><label>Unternehmen</label><input value={quoteForm.customer_company} onChange={e=>setQuoteForm({...quoteForm,customer_company:e.target.value})} data-testid="quote-company" /></div>
              <div className="adm-field"><label>Land</label><select value={quoteForm.customer_country} onChange={e=>setQuoteForm({...quoteForm,customer_country:e.target.value})} data-testid="quote-country"><option value="DE">Deutschland</option><option value="AT">Österreich</option><option value="CH">Schweiz</option><option value="NL">Niederlande</option><option value="BE">Belgien</option><option value="LU">Luxemburg</option><option value="OTHER">Sonstige</option></select></div>
              <div className="adm-field"><label>Branche</label><input value={quoteForm.customer_industry} onChange={e=>setQuoteForm({...quoteForm,customer_industry:e.target.value})} placeholder="z.B. Logistik, Finanz, Gesundheit" data-testid="quote-industry" /></div>
            </div>
            <div className="adm-field" style={{marginTop:'12px'}}><label>Use Case</label><input value={quoteForm.use_case} onChange={e=>setQuoteForm({...quoteForm,use_case:e.target.value})} placeholder="Beschreiben Sie den geplanten Einsatz" data-testid="quote-usecase" /></div>
            <div className="adm-field" style={{marginTop:'12px'}}><label>Interne Notizen</label><textarea value={quoteForm.notes} onChange={e=>setQuoteForm({...quoteForm,notes:e.target.value})} rows={2} placeholder="Interne Bemerkungen (nicht im Angebot sichtbar)" data-testid="quote-notes" style={{width:'100%',resize:'vertical'}} /></div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 2fr',gap:'12px',marginTop:'12px',padding:'14px',background:'rgba(255,155,122,0.04)',borderRadius:8,border:'1px solid rgba(255,155,122,0.08)'}}>
              <div className="adm-field"><label>Rabatt (%)</label><input type="number" min="0" max="25" step="0.5" value={quoteForm.discount_percent} onChange={e=>setQuoteForm({...quoteForm,discount_percent:parseFloat(e.target.value)||0})} data-testid="quote-discount" /></div>
              <div className="adm-field"><label>Rabattgrund (Pflicht bei Rabatt)</label><input value={quoteForm.discount_reason} onChange={e=>setQuoteForm({...quoteForm,discount_reason:e.target.value})} placeholder="z.B. Frühbucher, Partner-Rabatt, Verhandlung" data-testid="quote-discount-reason" /></div>
            </div>
            <div style={{marginTop:'12px'}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                <label style={{fontWeight:600,fontSize:'.8125rem',color:'#fff'}}>Sonderpositionen</label>
                <button type="button" className="adm-btn-sm" onClick={() => setQuoteForm({...quoteForm, special_items:[...quoteForm.special_items, {description:'',amount_eur:0,type:'add'}]})}>+ Hinzufügen</button>
              </div>
              {quoteForm.special_items.map((si, idx) => (
                <div key={idx} style={{display:'grid',gridTemplateColumns:'2fr 1fr auto auto',gap:8,marginBottom:6,alignItems:'end'}}>
                  <div className="adm-field"><label style={{fontSize:'.6875rem'}}>Beschreibung</label><input value={si.description} onChange={e => {const items=[...quoteForm.special_items]; items[idx]={...items[idx],description:e.target.value}; setQuoteForm({...quoteForm,special_items:items});}} placeholder="Zusatzleistung..." /></div>
                  <div className="adm-field"><label style={{fontSize:'.6875rem'}}>Betrag (EUR netto)</label><input type="number" min="0" step="0.01" value={si.amount_eur} onChange={e => {const items=[...quoteForm.special_items]; items[idx]={...items[idx],amount_eur:parseFloat(e.target.value)||0}; setQuoteForm({...quoteForm,special_items:items});}} /></div>
                  <select style={{padding:'7px',background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',borderRadius:4}} value={si.type} onChange={e => {const items=[...quoteForm.special_items]; items[idx]={...items[idx],type:e.target.value}; setQuoteForm({...quoteForm,special_items:items});}}>
                    <option value="add">Zuschlag</option><option value="deduct">Abzug</option>

  /* ══════════ CHATS VIEW ══════════ */
                  </select>
                  <button type="button" className="adm-btn-sm" style={{color:'#ef4444'}} onClick={() => {const items=[...quoteForm.special_items]; items.splice(idx,1); setQuoteForm({...quoteForm,special_items:items});}}>Entfernen</button>
                </div>
              ))}
            </div>
            <div style={{display:'flex',gap:'8px',marginTop:'16px'}}>
              <button type="submit" className="adm-btn-primary" disabled={commBusy==='create'} data-testid="submit-quote-btn">{commBusy==='create' ? 'Erstelle...' : 'Angebot erstellen'}</button>
              <button type="button" className="adm-btn-secondary" onClick={()=>setShowQuoteForm(false)}>Abbrechen</button>
            </div>
          </form>
        </div>
      )}

      <h3 style={{color:'#fff',margin:'0 0 12px'}}>Angebote</h3>
      <div className="adm-table-wrap" style={{marginBottom:'32px'}}>
        <table className="adm-table" data-testid="quotes-table">
          <thead><tr><th>Nr.</th><th>Kunde</th><th>Tarif</th><th>Gesamt</th><th>Status</th><th>Datum</th><th>Aktionen</th></tr></thead>
          <tbody>
            {quotes.length === 0 && <tr><td colSpan={7} style={{textAlign:'center',color:'#666'}}>Keine Angebote</td></tr>}
            {quotes.map(q => {
              const qs = QUOTE_STATUS[q.status] || {l:q.status,c:'#666'};
              return (
                <tr key={q.quote_id}>
                  <td style={{fontFamily:'monospace',fontSize:'12px'}}>{q.quote_number}</td>
                  <td><div>{q.customer?.name}</div><div style={{fontSize:'11px',color:'#666'}}>{q.customer?.company}</div></td>
                  <td>{q.tier === 'growth' ? 'Growth' : 'Starter'}</td>
                  <td>{fmtEur(q.calculation?.total_contract_eur)}</td>
                  <td><span className="adm-badge" style={{background:qs.c+'22',color:qs.c}}>{qs.l}</span></td>
                  <td>{fmtDate(q.created_at)}</td>
                  <td style={{display:'flex',gap:'4px',flexWrap:'wrap'}}>
                    {['draft','generated'].includes(q.status) && <button className="adm-btn-sm" onClick={()=>sendQuote(q.quote_id)} disabled={commBusy===`send_${q.quote_id}`} data-testid={`send-quote-${q.quote_id}`} title="Versenden"><I n="send" /></button>}
                    <button className="adm-btn-sm" onClick={() => setEditQuote({quote_id:q.quote_id, status:q.status, notes:q.notes||'', use_case:q.use_case||'', customer_name:q.customer?.name||'', customer_email:q.customer?.email||'', customer_company:q.customer?.company||'', discount_percent:q.discount?.percent||0, discount_reason:q.discount?.reason||'', special_items:q.special_items||[]})} title="Bearbeiten" data-testid={`edit-quote-${q.quote_id}`}><I n="edit" /></button>
                    <button className="adm-btn-sm" onClick={async () => { await apiFetch(`/api/admin/quotes/${q.quote_id}/copy`, { method: 'POST' }); apiFetch('/api/admin/quotes').then(d => d && setQuotes(d.quotes || [])); }} title="Kopieren"><I n="content_copy" /></button>
                    <a className="adm-btn-sm" href={`${API}/api/documents/quote/${q.quote_id}/pdf`} target="_blank" rel="noreferrer" data-testid={`pdf-quote-${q.quote_id}`} title="PDF"><I n="picture_as_pdf" /></a>
                    {q.status === 'accepted' && <button className="adm-btn-sm" style={{color:'#10b981'}} onClick={async () => { await apiFetch('/api/admin/invoices', { method: 'POST', body: JSON.stringify({ quote_id: q.quote_id }) }); apiFetch('/api/admin/invoices').then(d => d && setInvoices(d.invoices || [])); }} title="Rechnung erstellen"><I n="receipt" /></button>}
                    {q.discount && q.discount.percent > 0 && <span className="adm-badge" style={{background:'#f59e0b22',color:'#f59e0b',fontSize:'.5625rem'}}>-{q.discount.percent}%</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <h3 style={{color:'#fff',margin:'0 0 12px'}}>Rechnungen</h3>
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="invoices-table">
          <thead><tr><th>Nr.</th><th>Kunde</th><th>Typ</th><th>Betrag</th><th>Status</th><th>Zahlung</th><th>Datum</th><th>Aktionen</th></tr></thead>
          <tbody>
            {invoices.length === 0 && <tr><td colSpan={8} style={{textAlign:'center',color:'#666'}}>Keine Rechnungen</td></tr>}
            {invoices.map(inv => {
              const is = INV_STATUS[inv.status] || {l:inv.status,c:'#666'};
              const ps = PAY_STATUS[inv.payment_status] || {l:inv.payment_status||'—',c:'#666'};
              return (
                <tr key={inv.invoice_id}>
                  <td style={{fontFamily:'monospace',fontSize:'12px'}}>{inv.invoice_number}</td>
                  <td><div>{inv.customer?.name}</div><div style={{fontSize:'11px',color:'#666'}}>{inv.customer?.company}</div></td>
                  <td>{inv.type === 'deposit' ? 'Anzahlung' : inv.type === 'monthly' ? 'Monatsrate' : inv.type}</td>
                  <td>{fmtEur(inv.totals?.gross)}</td>
                  <td><span className="adm-badge" style={{background:is.c+'22',color:is.c}}>{is.l}</span></td>
                  <td><span className="adm-badge" style={{background:ps.c+'22',color:ps.c}}>{ps.l}</span></td>
                  <td>{fmtDate(inv.created_at)}</td>
                  <td style={{display:'flex',gap:'4px'}}>
                    {inv.payment_status !== 'paid' && <button className="adm-btn-sm" onClick={()=>markPaid(inv.invoice_id)} disabled={!!commBusy} title="Als bezahlt markieren" data-testid={`pay-${inv.invoice_id}`}><I n="paid" /></button>}
                    <button className="adm-btn-sm" onClick={() => setEditInvoice({invoice_id:inv.invoice_id, status:inv.status, payment_status:inv.payment_status||'pending', notes:inv.notes||''})} title="Bearbeiten" data-testid={`edit-inv-${inv.invoice_id}`}><I n="edit" /></button>
                    <button className="adm-btn-sm" onClick={()=>sendInvoice(inv.invoice_id)} disabled={!!commBusy} title="Per E-Mail senden" data-testid={`send-inv-${inv.invoice_id}`}><I n="send" /></button>
                    <a className="adm-btn-sm" href={`${API}/api/documents/invoice/${inv.invoice_id}/pdf`} target="_blank" rel="noreferrer"><I n="picture_as_pdf" /></a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Quote Edit Modal */}
      {editQuote && (
        <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setEditQuote(null)}>
          <div className="adm-modal" style={{maxWidth:640}} data-testid="quote-edit-modal">
            <h3>Angebot bearbeiten: {editQuote.quote_id?.slice(0,12)}</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Status</label><select className="adm-select" value={editQuote.status} onChange={e => setEditQuote({...editQuote, status: e.target.value})}>{Object.entries(QUOTE_STATUS).map(([k,v])=><option key={k} value={k}>{v.l}</option>)}</select></div>
              <div className="adm-field"><label>Kundenname</label><input value={editQuote.customer_name} onChange={e => setEditQuote({...editQuote, customer_name: e.target.value})} /></div>
              <div className="adm-field"><label>Kunden-E-Mail</label><input value={editQuote.customer_email} onChange={e => setEditQuote({...editQuote, customer_email: e.target.value})} /></div>
              <div className="adm-field"><label>Unternehmen</label><input value={editQuote.customer_company} onChange={e => setEditQuote({...editQuote, customer_company: e.target.value})} /></div>
            </div>
            <div className="adm-field" style={{marginTop:8}}><label>Use Case</label><input value={editQuote.use_case} onChange={e => setEditQuote({...editQuote, use_case: e.target.value})} style={{width:'100%'}} /></div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 2fr',gap:'12px',marginTop:12,padding:'12px',background:'rgba(255,155,122,0.04)',borderRadius:8,border:'1px solid rgba(255,155,122,0.08)'}}>
              <div className="adm-field"><label>Rabatt (%)</label><input type="number" min="0" max="25" step="0.5" value={editQuote.discount_percent} onChange={e => setEditQuote({...editQuote, discount_percent:parseFloat(e.target.value)||0})} /></div>
              <div className="adm-field"><label>Rabattgrund</label><input value={editQuote.discount_reason} onChange={e => setEditQuote({...editQuote, discount_reason: e.target.value})} placeholder="Pflicht bei Rabatt" /></div>
            </div>
            <div style={{marginTop:12}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}>
                <label style={{fontWeight:600,fontSize:'.8125rem',color:'#fff'}}>Sonderpositionen</label>
                <button type="button" className="adm-btn-sm" onClick={() => setEditQuote({...editQuote, special_items:[...(editQuote.special_items||[]), {description:'',amount_eur:0,type:'add'}]})}>+ Hinzufügen</button>
              </div>
              {(editQuote.special_items||[]).map((si, idx) => (
                <div key={idx} style={{display:'grid',gridTemplateColumns:'2fr 1fr auto auto',gap:6,marginBottom:4,alignItems:'end'}}>
                  <div className="adm-field"><input value={si.description} onChange={e => {const items=[...(editQuote.special_items||[])]; items[idx]={...items[idx],description:e.target.value}; setEditQuote({...editQuote,special_items:items});}} placeholder="Beschreibung" /></div>
                  <div className="adm-field"><input type="number" min="0" step="0.01" value={si.amount_eur} onChange={e => {const items=[...(editQuote.special_items||[])]; items[idx]={...items[idx],amount_eur:parseFloat(e.target.value)||0}; setEditQuote({...editQuote,special_items:items});}} /></div>
                  <select style={{padding:'7px',background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',borderRadius:4}} value={si.type} onChange={e => {const items=[...(editQuote.special_items||[])]; items[idx]={...items[idx],type:e.target.value}; setEditQuote({...editQuote,special_items:items});}}><option value="add">Zuschlag</option><option value="deduct">Abzug</option></select>
                  <button type="button" className="adm-btn-sm" style={{color:'#ef4444'}} onClick={() => {const items=[...(editQuote.special_items||[])]; items.splice(idx,1); setEditQuote({...editQuote,special_items:items});}}>Entfernen</button>
                </div>
              ))}
            </div>
            <div className="adm-field" style={{marginTop:8}}><label>Notizen</label><textarea value={editQuote.notes} onChange={e => setEditQuote({...editQuote, notes: e.target.value})} rows={2} style={{width:'100%',resize:'vertical'}} placeholder="Interne Notizen..." /></div>
            <div className="adm-modal-actions">
              <button className="adm-btn-secondary" onClick={() => setEditQuote(null)}>Abbrechen</button>
              <button className="adm-btn-primary" onClick={saveQuoteEdit} data-testid="save-quote-edit-btn">Speichern</button>
            </div>
          </div>
        </div>
      )}

      {/* Invoice Edit Modal */}
      {editInvoice && (
        <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setEditInvoice(null)}>
          <div className="adm-modal" data-testid="invoice-edit-modal">
            <h3>Rechnung bearbeiten: {editInvoice.invoice_id?.slice(0,12)}</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Status</label><select className="adm-select" value={editInvoice.status} onChange={e => setEditInvoice({...editInvoice, status: e.target.value})}>{Object.entries(INV_STATUS).map(([k,v])=><option key={k} value={k}>{v.l}</option>)}</select></div>
              <div className="adm-field"><label>Zahlungsstatus</label><select className="adm-select" value={editInvoice.payment_status} onChange={e => setEditInvoice({...editInvoice, payment_status: e.target.value})}>{Object.entries(PAY_STATUS).map(([k,v])=><option key={k} value={k}>{v.l}</option>)}</select></div>
            </div>
            <div className="adm-field" style={{marginTop:8}}><label>Notizen</label><textarea value={editInvoice.notes} onChange={e => setEditInvoice({...editInvoice, notes: e.target.value})} rows={2} style={{width:'100%',resize:'vertical'}} placeholder="Interne Notizen..." /></div>
            <div className="adm-modal-actions">
              <button className="adm-btn-secondary" onClick={() => setEditInvoice(null)}>Abbrechen</button>
              <button className="adm-btn-primary" onClick={saveInvoiceEdit} data-testid="save-invoice-edit-btn">Speichern</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
  const ChatsView = () => (
    <div className="adm-chats" data-testid="admin-chats">
      {selectedChat ? (
        <div className="adm-chat-detail">
          <button className="adm-back-btn" onClick={() => setSelectedChat(null)}><I n="arrow_back" /> Zurück</button>
          <div className="adm-chat-meta">
            <span>Sitzung: {selectedChat.session_id}</span>
            {selectedChat.customer_email && <span>Kunde: {selectedChat.customer_email}</span>}
            <span>Erstellt: {fmtTime(selectedChat.created_at)}</span>
          </div>
          {selectedChat.qualification && Object.keys(selectedChat.qualification).length > 0 && (
            <div className="adm-chat-qual">
              <h4>Qualifizierung</h4>
              {Object.entries(selectedChat.qualification).map(([k, v]) => (
                <div key={k} className="adm-qual-item"><strong>{k}:</strong> {String(v)}</div>
              ))}
            </div>
          )}
          <div className="adm-chat-messages">
            {(selectedChat.messages || []).map((m, i) => (
              <div key={i} className={`adm-chat-msg ${m.role}`}>
                <div className="adm-chat-msg-role">{m.role === 'user' ? 'Kunde' : 'KI'}</div>
                <div className="adm-chat-msg-text">{m.content}</div>
                {m.ts && <div className="adm-chat-msg-time">{typeof m.ts === 'number' ? new Date(m.ts).toLocaleTimeString('de-DE') : m.ts}</div>}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="adm-section-header">
            <h2>Chat-Sessions</h2>
            <span className="adm-count">{chatSessions.length} Sessions</span>
          </div>
          <div className="adm-table-wrap">
            <table className="adm-table" data-testid="chats-table">
              <thead><tr><th>Sitzung</th><th>Kunde</th><th>Nachrichten</th><th>Letzte Nachricht</th><th>Datum</th><th></th></tr></thead>
              <tbody>
                {chatSessions.map(s => (
                  <tr key={s.session_id} className="adm-row-click" onClick={() => loadChatDetail(s.session_id)}>
                    <td style={{fontFamily:'monospace',fontSize:'11px'}}>{s.session_id.slice(0,16)}</td>
                    <td>{s.customer_email || '—'}</td>
                    <td>{s.message_count}</td>
                    <td style={{maxWidth:'200px',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{s.last_message}</td>
                    <td>{fmtTime(s.created_at)}</td>
                    <td><button className="adm-btn-sm"><I n="visibility" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );

  /* ══════════ TIMELINE VIEW ══════════ */
  const EVENT_ICONS = {
    offer_generated: 'description', offer_sent: 'send', offer_opened: 'visibility',
    offer_accepted: 'check_circle', offer_declined: 'cancel', offer_revision_requested: 'edit',
    invoice_sent: 'receipt', payment_completed: 'paid', booking_created: 'event',
    contact_created: 'person_add', lead_created: 'group_add',
  };
  const TimelineView = () => (
    <div className="adm-timeline" data-testid="admin-timeline">
      <div className="adm-section-header">
        <h2>Aktivitätsverlauf</h2>
        <span className="adm-count">{timeline.length} Ereignisse</span>
      </div>
      <div className="adm-timeline-list">
        {timeline.map((ev, i) => (
          <div key={i} className="adm-timeline-item">
            <div className="adm-timeline-icon"><I n={EVENT_ICONS[ev.event] || 'circle'} /></div>
            <div className="adm-timeline-content">
              <div className="adm-timeline-event">{ev.event?.replace(/_/g, ' ')}</div>
              {ev.ref_id && <div className="adm-timeline-ref">Ref.: {ev.ref_id}</div>}
              <div className="adm-timeline-actor">{ev.actor || '—'}</div>
            </div>
            <div className="adm-timeline-time">{fmtTime(ev.timestamp)}</div>
          </div>
        ))}
        {timeline.length === 0 && <div className="adm-empty">Keine Ereignisse vorhanden</div>}
      </div>
    </div>
  );

  /* ══════════ WHATSAPP CONNECT VIEW ══════════ */
  const WA_STATUS_MAP = {
    unpaired: { l: 'Nicht verbunden', c: '#6b7b8d', i: 'link_off' },
    pairing: { l: 'QR-Code bereit', c: '#f59e0b', i: 'qr_code_2' },
    connected: { l: 'Verbunden', c: '#10b981', i: 'check_circle' },
    reconnecting: { l: 'Verbindung wird hergestellt...', c: '#f59e0b', i: 'sync' },
    disconnected: { l: 'Getrennt', c: '#ef4444', i: 'link_off' },
    failed: { l: 'Fehlgeschlagen', c: '#ef4444', i: 'error' },
  };

  const waAction = async (action) => {
    const d = await apiFetch(`/api/admin/whatsapp/${action}`, { method: 'POST' });
    if (d) apiFetch('/api/admin/whatsapp/status').then(s => s && setWaStatus(s));
    return d;
  };

  const sendWaMessage = async () => {
    if (!waSendMsg.trim()) return;
    setWaSending(true);
    try {
      await apiFetch('/api/admin/whatsapp/send', {
        method: 'POST',
        body: JSON.stringify({ to: waSendTo.trim(), content: waSendMsg.trim() })
      });
      setWaSendMsg('');
      loadWaMessages();
    } catch (e) { console.error(e); } finally { setWaSending(false); }
  };

  const WhatsAppView = () => {
    const st = WA_STATUS_MAP[waStatus?.status] || WA_STATUS_MAP.unpaired;
    const isConnected = waStatus?.status === 'connected';
    return (
      <div className="adm-wa" data-testid="admin-whatsapp">
        <div className="adm-section-header">
          <h2>WhatsApp Connect</h2>
          <span className="adm-badge" style={{ background: st.c + '22', color: st.c }}><I n={st.i} /> {st.l}</span>
        </div>
        <div className="adm-wa-grid">
          {/* Session Status Card */}
          <div className="adm-wa-card">
            <h3>Session-Status</h3>
            <div className="adm-wa-status-row">
              <div className="adm-wa-status-indicator" style={{ background: st.c }}></div>
              <span>{st.l}</span>
            </div>
            {waStatus?.phone_number && <p style={{fontSize:'.8125rem',color:'#c8d1dc',marginBottom:6}}>Telefon: {waStatus.phone_number}</p>}
            {waStatus?.connected_at && <p style={{fontSize:'.75rem',color:'#6b7b8d'}}>Verbunden seit: {fmtTime(waStatus.connected_at)}</p>}
            {waStatus?.last_activity && <p style={{fontSize:'.75rem',color:'#6b7b8d'}}>Letzte Aktivität: {fmtTime(waStatus.last_activity)}</p>}
            {waStatus?.error && <p style={{ color: '#ef4444', fontSize:'.8125rem' }}>Fehler: {waStatus.error}</p>}
            <div className="adm-wa-actions">
              {(!waStatus?.status || waStatus?.status === 'unpaired' || waStatus?.status === 'disconnected' || waStatus?.status === 'failed') && (
                <button className="adm-btn adm-btn-primary" onClick={() => waAction('pair')} data-testid="wa-pair-btn"><I n="qr_code_2" /> QR-Code generieren</button>
              )}
              {(waStatus?.status === 'disconnected' || waStatus?.status === 'failed') && (
                <button className="adm-btn adm-btn-secondary" onClick={() => waAction('reconnect')} data-testid="wa-reconnect-btn"><I n="sync" /> Reconnect</button>
              )}
              {isConnected && (
                <button className="adm-btn adm-btn-danger" onClick={() => waAction('disconnect')} data-testid="wa-disconnect-btn"><I n="link_off" /> Trennen</button>
              )}
              {waStatus?.status === 'pairing' && (
                <button className="adm-btn adm-btn-secondary" onClick={() => waAction('simulate-connect')} data-testid="wa-simulate-btn"><I n="science" /> Verbindung simulieren</button>
              )}
              <button className="adm-btn adm-btn-secondary" onClick={() => waAction('reset')} data-testid="wa-reset-btn"><I n="restart_alt" /> Reset</button>
            </div>
          </div>

          {/* QR Code Card */}
          {waStatus?.status === 'pairing' && waStatus?.qr_code && (
            <div className="adm-wa-card adm-wa-qr-card">
              <h3>QR-Code scannen</h3>
              <div className="adm-wa-qr-box" data-testid="wa-qr-code">
                <I n="qr_code_2" />
                <p className="adm-wa-qr-hint">WhatsApp auf Telefon &rarr; Verknüpfte Geräte &rarr; Gerät hinzufügen &rarr; QR-Code scannen</p>
                <p className="adm-wa-qr-note">Bridge-Modus: In der Produktivumgebung erscheint hier der echte QR-Code.</p>
              </div>
            </div>
          )}

          {/* Send Message Card — only when connected */}
          {isConnected && (
            <div className="adm-wa-card">
              <h3>Nachricht senden</h3>
              <div className="adm-field" style={{marginBottom:8}}>
                <label>An (Telefonnummer)</label>
                <input value={waSendTo} onChange={e => setWaSendTo(e.target.value)} placeholder="+49 171 234 5678" data-testid="wa-send-to" />
              </div>
              <div className="adm-field" style={{marginBottom:8}}>
                <label>Nachricht</label>
                <textarea value={waSendMsg} onChange={e => setWaSendMsg(e.target.value)} rows={3} placeholder="Nachricht eingeben..." style={{width:'100%',resize:'vertical'}} data-testid="wa-send-msg" />
              </div>
              <button className="adm-btn adm-btn-primary" onClick={sendWaMessage} disabled={waSending || !waSendMsg.trim()} data-testid="wa-send-btn">
                <I n="send" /> {waSending ? 'Sende...' : 'Senden'}
              </button>
            </div>
          )}

          {/* Architecture Note */}
          <div className="adm-wa-card">
            <h3>Architektur</h3>
            <div className="adm-wa-arch-info">
              <p><strong>Schicht A — Official Channel:</strong> WhatsApp Business API / Cloud API als Zielarchitektur.</p>
              <p><strong>Schicht B — QR Bridge (aktuell):</strong> Isolierter Connector. Austauschbar ohne Rework der Kernlogik.</p>
              <p><strong>API-First:</strong> Zentrale Messaging-Domain kanalunabhängig. WhatsApp, E-Mail, Chat und Portal teilen dieselbe Conversation-/Message-Struktur.</p>
            </div>
          </div>
        </div>

        {/* Message History */}
        {waMessages.length > 0 && (
          <div style={{marginTop:24}}>
            <div className="adm-section-header">
              <h3 style={{fontSize:'1rem',color:'#fff'}}>WhatsApp-Nachrichten</h3>
              <button className="adm-btn-sm" onClick={loadWaMessages}><I n="refresh" /> Aktualisieren</button>
            </div>
            <div className="adm-table-wrap">
              <table className="adm-table" data-testid="wa-messages-table">
                <thead><tr><th>Richtung</th><th>Kontakt</th><th>Nachricht</th><th>Zeit</th></tr></thead>
                <tbody>
                  {waMessages.map(m => (
                    <tr key={m.message_id}>
                      <td><span className="adm-badge" style={{background: m.direction==='inbound' ? '#10b98122' : '#3b82f622', color: m.direction==='inbound' ? '#10b981' : '#3b82f6'}}>{m.direction==='inbound' ? 'Eingehend' : 'Ausgehend'}</span></td>
                      <td>{m.contact?.phone || m.sender || '—'}</td>
                      <td style={{maxWidth:300,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{m.content}</td>
                      <td>{fmtTime(m.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  /* ══════════ CONVERSATIONS VIEW ══════════ */

  const sendConvoReply = async (conversationId, channel) => {
    if (!convoReply.trim()) return;
    setConvoReplying(true);
    try {
      await apiFetch(`/api/admin/conversations/${conversationId}/reply`, {
        method: 'POST',
        body: JSON.stringify({ content: convoReply.trim(), channel: channel || 'chat' })
      });
      setConvoReply('');
      const d = await apiFetch(`/api/admin/conversations/${conversationId}`);
      if (d) setSelectedConvo(d);
    } catch (e) { console.error(e); } finally { setConvoReplying(false); }
  };

  const ConversationsView = () => (
    <div className="adm-convos" data-testid="admin-conversations">
      {selectedConvo ? (
        <div className="adm-convo-detail">
          <button className="adm-back-btn" onClick={() => { setSelectedConvo(null); setConvoReply(''); }}><I n="arrow_back" /> Zurück</button>
          <div className="adm-chat-meta">
            <span>ID: {selectedConvo.conversation_id?.slice(0,16)}</span>
            {selectedConvo.contact?.email && <span>Kontakt: {selectedConvo.contact.email}</span>}
            <span>Kanäle: {(selectedConvo.channels || []).join(', ')}</span>
            <span className="adm-badge" style={{background: selectedConvo.status === 'open' ? '#10b98122' : '#6b7b8d22', color: selectedConvo.status === 'open' ? '#10b981' : '#6b7b8d'}}>{selectedConvo.status}</span>
          </div>
          <div className="adm-chat-messages">
            {(selectedConvo.messages || []).map((m, i) => (
              <div key={i} className={`adm-chat-msg ${m.direction === 'inbound' ? 'user' : 'assistant'}`}>
                <div className="adm-chat-msg-role">{m.direction === 'inbound' ? (m.sender || 'Kunde') : (m.ai_generated ? 'KI' : 'Admin')} <span style={{opacity:.5,fontSize:'.625rem'}}>({m.channel})</span></div>
                <div className="adm-chat-msg-text">{m.content}</div>
                <div className="adm-chat-msg-time">{fmtTime(m.timestamp)}</div>
              </div>
            ))}
            {(!selectedConvo.messages || selectedConvo.messages.length === 0) && <div className="adm-empty">Keine Nachrichten</div>}
          </div>
          {/* Reply input */}
          <div style={{display:'flex',gap:8,marginTop:12,alignItems:'flex-end'}}>
            <select className="adm-select" style={{width:120,flexShrink:0}} defaultValue={selectedConvo.channel_origin || 'chat'} id="reply-channel" data-testid="convo-reply-channel">
              <option value="chat">Chat</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="email">E-Mail</option>
              <option value="admin">Admin</option>
            </select>
            <input style={{flex:1,background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',padding:'10px 14px',fontSize:'.8125rem'}}
              value={convoReply} onChange={e => setConvoReply(e.target.value)} placeholder="Antwort schreiben..."
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendConvoReply(selectedConvo.conversation_id, document.getElementById('reply-channel')?.value); }}}
              data-testid="convo-reply-input" />
            <button className="adm-btn-primary" style={{width:'auto',padding:'10px 20px',flexShrink:0}} onClick={() => sendConvoReply(selectedConvo.conversation_id, document.getElementById('reply-channel')?.value)} disabled={convoReplying || !convoReply.trim()} data-testid="convo-reply-send">
              <I n="send" />
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="adm-section-header">
            <h2>Konversationen</h2>
            <span className="adm-count">{conversations.length} aktiv</span>
          </div>
          <div className="adm-table-wrap">
            <table className="adm-table" data-testid="conversations-table">
              <thead><tr><th>Kontakt</th><th>Kanäle</th><th>Status</th><th>Nachrichten</th><th>Letzte Aktivität</th><th></th></tr></thead>
              <tbody>
                {conversations.map(c => (
                  <tr key={c.conversation_id} className="adm-row-click" onClick={async () => {
                    const d = await apiFetch(`/api/admin/conversations/${c.conversation_id}`);
                    if (d) setSelectedConvo(d);
                  }}>
                    <td>{c.contact?.email?.replace('@placeholder.nexifyai.de','') || c.contact?.first_name || '—'}</td>
                    <td>{(c.channels || []).map(ch => <span key={ch} className="adm-channel-badge">{ch}</span>)}</td>
                    <td><span className={`adm-status-dot ${c.status}`}></span> {c.status}</td>
                    <td>{c.message_count}</td>
                    <td>{fmtTime(c.last_message_at)}</td>
                    <td><button className="adm-btn-sm"><I n="visibility" /></button></td>
                  </tr>
                ))}
                {conversations.length === 0 && <tr><td colSpan="6" style={{textAlign:'center',padding:'32px',color:'#4a5568'}}>Keine Konversationen</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );

  /* ══════════ AGENTS VIEW ══════════ */

  const executeAgent = async (agentName) => {
    if (!agentTask.trim()) return;
    setAgentLoading(true);
    setAgentResult(null);
    try {
      const endpoint = agentName === 'orchestrator'
        ? '/api/admin/agents/route'
        : `/api/admin/agents/${agentName}/execute`;
      const d = await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify({ task: agentTask, customer_email: agentTarget || undefined })
      });
      if (d) setAgentResult(d);
    } catch (e) { console.error(e); } finally { setAgentLoading(false); }
  };

  const AgentsView = () => (
    <div className="adm-agents" data-testid="admin-agents">
      <div className="adm-section-header">
        <h2>KI-Agenten</h2>
        {agentsList?.orchestrator && <span className="adm-badge" style={{background:'#10b98122',color:'#10b981'}}>Orchestrator aktiv — {agentsList.orchestrator.model}</span>}
      </div>

      {/* Agent Cards */}
      <div className="adm-wa-grid" style={{marginBottom:24}}>
        {agentsList?.agents && Object.entries(agentsList.agents).map(([name, info]) => (
          <div key={name} className="adm-wa-card" style={{cursor:'pointer'}} onClick={() => setAgentTarget(name)}>
            <h3 style={{textTransform:'capitalize'}}>{name}</h3>
            <p style={{fontSize:'.8125rem',color:'#c8d1dc'}}>{info.role}</p>
            <span className="adm-badge" style={{background:'#10b98122',color:'#10b981',marginTop:8,display:'inline-block'}}>{info.status}</span>
          </div>
        ))}
      </div>

      {/* Task Input */}
      <div className="adm-wa-card" style={{marginBottom:24}}>
        <h3>Aufgabe an Agenten senden</h3>
        <div className="adm-field" style={{marginBottom:8}}>
          <label>Kunden-E-Mail (optional)</label>
          <input value={agentTarget} onChange={e => setAgentTarget(e.target.value)} placeholder="kunde@firma.de" data-testid="agent-customer-email" />
        </div>
        <div className="adm-field" style={{marginBottom:12}}>
          <label>Aufgabe</label>
          <textarea value={agentTask} onChange={e => setAgentTask(e.target.value)} rows={4} placeholder="z.B.: Erstelle eine personalisierte Erstansprache..." style={{width:'100%',resize:'vertical'}} data-testid="agent-task-input" />
        </div>
        <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
          <button className="adm-btn adm-btn-primary" onClick={() => executeAgent('orchestrator')} disabled={agentLoading || !agentTask.trim()} data-testid="agent-route-btn">
            <I n="route" /> {agentLoading ? 'Verarbeite...' : 'Orchestrator'}
          </button>
          {agentsList?.agents && Object.keys(agentsList.agents).map(name => (
            <button key={name} className="adm-btn adm-btn-secondary" onClick={() => executeAgent(name)} disabled={agentLoading || !agentTask.trim()} data-testid={`agent-exec-${name}`} style={{textTransform:'capitalize'}}>
              {name}
            </button>
          ))}
        </div>
      </div>

      {/* Result */}
      {agentResult && (
        <div className="adm-wa-card">
          <h3>Ergebnis {agentResult.agent && <span style={{fontWeight:400,fontSize:'.75rem',color:'#6b7b8d'}}>({agentResult.agent})</span>}</h3>
          {agentResult.error ? (
            <p style={{color:'#ef4444'}}>{agentResult.error}</p>
          ) : (
            <pre style={{background:'rgba(19,26,34,0.6)',padding:16,borderRadius:8,fontSize:'.8125rem',color:'#c8d1dc',overflow:'auto',maxHeight:400,whiteSpace:'pre-wrap',wordBreak:'break-word'}} data-testid="agent-result">
              {typeof agentResult.response === 'string' ? agentResult.response : typeof agentResult.routing === 'object' ? JSON.stringify(agentResult.routing, null, 2) : JSON.stringify(agentResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );

  /* ══════════ AUDIT VIEW ══════════ */
  const AuditView = () => (
    <div className="adm-audit" data-testid="admin-audit">
      <div className="adm-section-header">
        <h2>System-Audit</h2>
        <button className="adm-btn-sm" onClick={loadAudit}><I n="refresh" /> Aktualisieren</button>
      </div>

      {/* Health Status */}
      {auditData && (
        <div className="adm-wa-grid" style={{marginBottom:24}}>
          <div className="adm-wa-card">
            <h3>Gesamtstatus</h3>
            <span className="adm-badge" style={{
              background: auditData.overall === 'healthy' ? '#10b98122' : '#ef444422',
              color: auditData.overall === 'healthy' ? '#10b981' : '#ef4444',
              fontSize:'.9375rem', padding:'6px 16px'
            }}>{auditData.overall === 'healthy' ? 'Gesund' : 'Eingeschränkt'}</span>
          </div>
          {auditData.checks && Object.entries(auditData.checks).map(([key, val]) => (
            <div key={key} className="adm-wa-card">
              <h3 style={{textTransform:'capitalize',fontSize:'.875rem'}}>{key.replace(/_/g, ' ')}</h3>
              {typeof val === 'object' ? (
                <div style={{fontSize:'.8125rem',color:'#c8d1dc'}}>
                  {val.status && <span className="adm-badge" style={{background: val.status === 'ok' ? '#10b98122' : '#f59e0b22', color: val.status === 'ok' ? '#10b981' : '#f59e0b'}}>{val.status}</span>}
                  {val.count != null && <span style={{marginLeft:8}}>{val.count} aktiv</span>}
                  {val.names && <p style={{marginTop:4,color:'#6b7b8d'}}>{val.names.join(', ')}</p>}
                  {val.counts && <div style={{marginTop:8}}>{Object.entries(val.counts).map(([c, n]) => <span key={c} style={{display:'inline-block',marginRight:12,fontSize:'.75rem'}}>{c}: <strong style={{color:'#fff'}}>{n}</strong></span>)}</div>}
                  {val.phone && <p style={{marginTop:4}}>Telefon: {val.phone}</p>}
                  {val.detail && <p style={{marginTop:4,color:'#6b7b8d'}}>{val.detail}</p>}
                </div>
              ) : (
                <span style={{fontSize:'.9375rem',fontWeight:700,color:'#fff'}}>{val}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Audit Timeline */}
      {auditTimeline.length > 0 && (
        <div>
          <h3 style={{fontSize:'1rem',color:'#fff',marginBottom:12}}>Letzte 48h Ereignisse ({auditTimeline.length})</h3>
          <div className="adm-table-wrap">
            <table className="adm-table" data-testid="audit-timeline-table">
              <thead><tr><th>Typ</th><th>Aktion</th><th>Kanal</th><th>Akteur</th><th>Zeit</th></tr></thead>
              <tbody>
                {auditTimeline.map((e, i) => (
                  <tr key={i}>
                    <td><span className="adm-channel-badge">{e.entity_type}</span></td>
                    <td>{e.action?.replace(/_/g, ' ')}</td>
                    <td>{e.channel || '—'}</td>
                    <td>{e.actor || '—'}</td>
                    <td>{fmtTime(e.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  /* ══════════ MAIN LAYOUT ══════════ */
  const navItems = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
    { id: 'commercial', icon: 'receipt_long', label: 'Angebote & Rechnungen' },
    { id: 'leads', icon: 'people', label: 'Leads' },
    { id: 'conversations', icon: 'chat', label: 'Kommunikation' },
    { id: 'chats', icon: 'forum', label: 'KI-Chats' },
    { id: 'whatsapp', icon: 'smartphone', label: 'WhatsApp' },
    { id: 'timeline', icon: 'timeline', label: 'Aktivitäten' },
    { id: 'calendar', icon: 'calendar_month', label: 'Kalender' },
    { id: 'customers', icon: 'person_search', label: 'Kunden' },
    { id: 'agents', icon: 'smart_toy', label: 'KI-Agenten' },
    { id: 'audit', icon: 'verified', label: 'Audit' },
  ];

  return (
    <div className="adm-layout" data-testid="admin-panel">
      <aside className="adm-sidebar" data-testid="admin-sidebar">
        <div className="adm-sidebar-logo"><img src="/icon-mark.svg" alt="" width="28" height="28" /><span>NeXify<em>AI</em></span></div>
        <nav className="adm-sidebar-nav">
          {navItems.map(n => (
            <button key={n.id} className={`adm-nav-item ${view === n.id ? 'active' : ''}`} onClick={() => { setView(n.id); setSelectedBooking(null); setCustDetail(null); setSelectedChat(null); setSelectedConvo(null); }} data-testid={`nav-${n.id}`}>
              <I n={n.icon} /><span>{n.label}</span>
            </button>
          ))}
        </nav>
        <button className="adm-logout" onClick={logout} data-testid="admin-logout"><I n="logout" /> Abmelden</button>
      </aside>
      <main className="adm-main">
        <header className="adm-topbar">
          <h1 className="adm-topbar-title">{navItems.find(n => n.id === view)?.label}</h1>
          <div className="adm-topbar-user"><I n="account_circle" /> Administration</div>
        </header>
        <div className="adm-content">
          {view === 'dashboard' && <DashboardView />}
          {view === 'commercial' && <CommercialView />}
          {view === 'leads' && <LeadsView />}
          {view === 'conversations' && <ConversationsView />}
          {view === 'chats' && <ChatsView />}
          {view === 'whatsapp' && <WhatsAppView />}
          {view === 'timeline' && <TimelineView />}
          {view === 'calendar' && <CalendarView />}
          {view === 'customers' && <CustomersView />}
          {view === 'agents' && <AgentsView />}
          {view === 'audit' && <AuditView />}
        </div>
      </main>
    </div>
  );
};

export default Admin;

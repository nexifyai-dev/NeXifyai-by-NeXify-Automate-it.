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
  const [token, setToken] = useState(() => localStorage.getItem('nx_admin_token') || '');
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
  const [quoteForm, setQuoteForm] = useState({ tier: 'starter', customer_name: '', customer_email: '', customer_company: '', customer_country: 'DE', customer_industry: '', use_case: '', notes: '' });
  const [showQuoteForm, setShowQuoteForm] = useState(false);
  const [commBusy, setCommBusy] = useState('');

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
      if (!r.ok) throw new Error(d.detail || 'Login fehlgeschlagen');
      setToken(d.access_token); localStorage.setItem('nx_admin_token', d.access_token);
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

  /* ── Update lead status ── */
  const updateLead = async (id, status, notes) => {
    await apiFetch(`/api/admin/leads/${id}`, { method: 'PATCH', body: JSON.stringify({ status, notes }) });
    setLeads(prev => prev.map(l => l.lead_id === id ? { ...l, status } : l));
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

  const logout = () => { setToken(''); localStorage.removeItem('nx_admin_token'); };

  /* ══════════ LOGIN SCREEN ══════════ */
  if (!token) return (
    <div className="adm-login" data-testid="admin-login">
      <div className="adm-login-box">
        <div className="adm-login-logo"><img src="/icon-mark.svg" alt="" width="36" height="36" /><span>NeXify<em>AI</em></span></div>
        <h1>Admin Panel</h1>
        <form onSubmit={login} data-testid="admin-login-form">
          <div className="adm-field"><label>E-Mail</label><input type="email" value={loginForm.email} onChange={e => setLoginForm({ ...loginForm, email: e.target.value })} required data-testid="admin-email" /></div>
          <div className="adm-field"><label>Passwort</label><input type="password" value={loginForm.password} onChange={e => setLoginForm({ ...loginForm, password: e.target.value })} required data-testid="admin-password" /></div>
          {loginErr && <div className="adm-err" data-testid="admin-login-error">{loginErr}</div>}
          <button type="submit" className="adm-btn-primary" disabled={loginBusy} data-testid="admin-login-btn">{loginBusy ? 'Anmelden...' : 'Anmelden'}</button>
        </form>
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
  const LeadsView = () => (
    <div className="adm-leads" data-testid="admin-leads">
      <div className="adm-leads-header">
        <h2>Leads ({leadsTotal})</h2>
        <div className="adm-leads-controls">
          <div className="adm-search"><I n="search" /><input placeholder="Suchen..." value={leadsSearch} onChange={e => setLeadsSearch(e.target.value)} data-testid="leads-search" /></div>
          <select className="adm-select" value={leadsFilter} onChange={e => setLeadsFilter(e.target.value)} data-testid="leads-filter">
            <option value="all">Alle</option>
            {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
      </div>
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="leads-table">
          <thead><tr><th>Name</th><th>E-Mail</th><th>Unternehmen</th><th>Quelle</th><th>Status</th><th>Datum</th><th>Aktionen</th></tr></thead>
          <tbody>
            {leads.map((l, i) => (
              <tr key={i} className={selectedLead?.lead_id === l.lead_id ? 'active' : ''} onClick={() => setSelectedLead(l)}>
                <td>{l.vorname} {l.nachname}</td><td>{l.email}</td><td>{l.unternehmen || '-'}</td><td>{l.source}</td>
                <td><span className="adm-badge" style={{ background: STATUS_MAP[l.status]?.color + '22', color: STATUS_MAP[l.status]?.color }}>{STATUS_MAP[l.status]?.label || l.status}</span></td>
                <td>{fmtTime(l.created_at)}</td>
                <td>
                  <select className="adm-select-sm" value={l.status} onChange={e => updateLead(l.lead_id, e.target.value)} onClick={e => e.stopPropagation()}>
                    {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {leads.length === 0 && <div className="adm-empty">Keine Leads gefunden</div>}
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
  const CustomersView = () => (
    <div className="adm-customers" data-testid="admin-customers">
      <div className="adm-leads-header">
        <h2>Kunden ({customers.length})</h2>
        <div className="adm-search"><I n="search" /><input placeholder="Suchen..." value={custSearch} onChange={e => setCustSearch(e.target.value)} data-testid="customer-search" /></div>
      </div>
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="customers-table">
          <thead><tr><th>Name</th><th>E-Mail</th><th>Unternehmen</th><th>Anfragen</th><th>Buchungen</th><th>Erster Kontakt</th><th>Letzter Kontakt</th></tr></thead>
          <tbody>
            {customers.map((c, i) => (
              <tr key={i} className={custDetail?.email === c.email ? 'active' : ''} onClick={() => loadCustomerDetail(c.email)} data-testid={`customer-row-${i}`}>
                <td>{c.vorname} {c.nachname}</td><td>{c.email}</td><td>{c.unternehmen || '-'}</td>
                <td><span className="adm-badge">{c.total_leads}</span></td>
                <td><span className="adm-badge">{c.total_bookings}</span></td>
                <td>{fmtDate(c.first_contact)}</td><td>{fmtDate(c.last_contact)}</td>
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
            <button className="adm-btn-icon" onClick={() => setCustDetail(null)}><I n="close" /></button>
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
    </div>
  );

  /* ══════════ COMMERCIAL VIEW ══════════ */
  const createQuote = async (e) => {
    e.preventDefault(); setCommBusy('create');
    try {
      await apiFetch('/api/admin/quotes', { method: 'POST', body: JSON.stringify(quoteForm) });
      setShowQuoteForm(false); setQuoteForm({ tier: 'starter', customer_name: '', customer_email: '', customer_company: '', customer_country: 'DE', customer_industry: '', use_case: '', notes: '' });
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
        <h2>Commercial</h2>
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
                  <td style={{display:'flex',gap:'4px'}}>
                    {['draft','generated'].includes(q.status) && <button className="adm-btn-sm" onClick={()=>sendQuote(q.quote_id)} disabled={commBusy===`send_${q.quote_id}`} data-testid={`send-quote-${q.quote_id}`}><I n="send" /></button>}
                    <a className="adm-btn-sm" href={`${API}/api/documents/quote/${q.quote_id}/pdf`} target="_blank" rel="noreferrer" data-testid={`pdf-quote-${q.quote_id}`}><I n="picture_as_pdf" /></a>
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
                    <button className="adm-btn-sm" onClick={()=>sendInvoice(inv.invoice_id)} disabled={!!commBusy} title="Per E-Mail senden" data-testid={`send-inv-${inv.invoice_id}`}><I n="send" /></button>
                    <a className="adm-btn-sm" href={`${API}/api/documents/invoice/${inv.invoice_id}/pdf`} target="_blank" rel="noreferrer"><I n="picture_as_pdf" /></a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  /* ══════════ CHATS VIEW ══════════ */
  const ChatsView = () => (
    <div className="adm-chats" data-testid="admin-chats">
      {selectedChat ? (
        <div className="adm-chat-detail">
          <button className="adm-back-btn" onClick={() => setSelectedChat(null)}><I n="arrow_back" /> Zurück</button>
          <div className="adm-chat-meta">
            <span>Session: {selectedChat.session_id}</span>
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
              <thead><tr><th>Session</th><th>Kunde</th><th>Nachrichten</th><th>Letzte Nachricht</th><th>Datum</th><th></th></tr></thead>
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
        <h2>Activity Timeline</h2>
        <span className="adm-count">{timeline.length} Events</span>
      </div>
      <div className="adm-timeline-list">
        {timeline.map((ev, i) => (
          <div key={i} className="adm-timeline-item">
            <div className="adm-timeline-icon"><I n={EVENT_ICONS[ev.event] || 'circle'} /></div>
            <div className="adm-timeline-content">
              <div className="adm-timeline-event">{ev.event}</div>
              {ev.ref_id && <div className="adm-timeline-ref">Ref: {ev.ref_id}</div>}
              <div className="adm-timeline-actor">{ev.actor || '—'}</div>
            </div>
            <div className="adm-timeline-time">{fmtTime(ev.timestamp)}</div>
          </div>
        ))}
        {timeline.length === 0 && <div className="adm-empty">Keine Events vorhanden</div>}
      </div>
    </div>
  );

  /* ══════════ MAIN LAYOUT ══════════ */
  const navItems = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
    { id: 'commercial', icon: 'receipt_long', label: 'Commercial' },
    { id: 'leads', icon: 'people', label: 'Leads' },
    { id: 'chats', icon: 'forum', label: 'Chats' },
    { id: 'timeline', icon: 'timeline', label: 'Timeline' },
    { id: 'calendar', icon: 'calendar_month', label: 'Kalender' },
    { id: 'customers', icon: 'person_search', label: 'Kunden' },
  ];

  return (
    <div className="adm-layout" data-testid="admin-panel">
      <aside className="adm-sidebar" data-testid="admin-sidebar">
        <div className="adm-sidebar-logo"><img src="/icon-mark.svg" alt="" width="28" height="28" /><span>NeXify<em>AI</em></span></div>
        <nav className="adm-sidebar-nav">
          {navItems.map(n => (
            <button key={n.id} className={`adm-nav-item ${view === n.id ? 'active' : ''}`} onClick={() => { setView(n.id); setSelectedBooking(null); setCustDetail(null); setSelectedChat(null); }} data-testid={`nav-${n.id}`}>
              <I n={n.icon} /><span>{n.label}</span>
            </button>
          ))}
        </nav>
        <button className="adm-logout" onClick={logout} data-testid="admin-logout"><I n="logout" /> Abmelden</button>
      </aside>
      <main className="adm-main">
        <header className="adm-topbar">
          <h1 className="adm-topbar-title">{navItems.find(n => n.id === view)?.label}</h1>
          <div className="adm-topbar-user"><I n="account_circle" /> Admin</div>
        </header>
        <div className="adm-content">
          {view === 'dashboard' && <DashboardView />}
          {view === 'commercial' && <CommercialView />}
          {view === 'leads' && <LeadsView />}
          {view === 'chats' && <ChatsView />}
          {view === 'timeline' && <TimelineView />}
          {view === 'calendar' && <CalendarView />}
          {view === 'customers' && <CustomersView />}
        </div>
      </main>
    </div>
  );
};

export default Admin;

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import AgentView from './AgentView';
import './Admin.css';
import './AgentView.css';

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
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [projectDetail, setProjectDetail] = useState(null);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectForm, setProjectForm] = useState({ title:'', customer_email:'', tier:'', classification:'' });
  const [projectSectionEdit, setProjectSectionEdit] = useState(null);
  const [projectChatMsg, setProjectChatMsg] = useState('');
  const [projectChatSending, setProjectChatSending] = useState(false);
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [contractDetail, setContractDetail] = useState(null);
  const [showContractForm, setShowContractForm] = useState(false);
  const [contractForm, setContractForm] = useState({ customer_email:'', customer_name:'', customer_company:'', tier_key:'', contract_type:'standard', notes:'' });
  const [showAppendixForm, setShowAppendixForm] = useState(false);
  const [appendixForm, setAppendixForm] = useState({ appendix_type:'ai_agents', title:'', description:'', pricing_amount:0 });
  const [billingStatus, setBillingStatus] = useState(null);
  const [outboundPipeline, setOutboundPipeline] = useState(null);
  const [outboundLeads, setOutboundLeads] = useState([]);
  const [outboundLeadsLoading, setOutboundLeadsLoading] = useState(false);
  const [selectedOutboundLead, setSelectedOutboundLead] = useState(null);
  const [outboundDetail, setOutboundDetail] = useState(null);
  const [showDiscoverForm, setShowDiscoverForm] = useState(false);
  const [discoverForm, setDiscoverForm] = useState({ name:'', website:'', industry:'', email:'', phone:'', contact_name:'', country:'DE', notes:'' });
  const [outboundFilter, setOutboundFilter] = useState('all');
  const [outreachForm, setOutreachForm] = useState({ channel:'email', subject:'', content:'' });
  const [showOutreachForm, setShowOutreachForm] = useState(false);
  const [outboundBusy, setOutboundBusy] = useState('');
  const [complianceSummary, setComplianceSummary] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminUsersLoading, setAdminUsersLoading] = useState(false);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUserForm, setNewUserForm] = useState({ email: '', password: '', role: 'admin' });
  const [webhookEvents, setWebhookEvents] = useState([]);
  /* API Keys State */
  const [apiKeys, setApiKeys] = useState([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(false);
  const [showCreateApiKey, setShowCreateApiKey] = useState(false);
  const [newApiKeyForm, setNewApiKeyForm] = useState({ name: '', scopes: 'all', rate_limit_per_hour: 1000, expires_in_days: '', description: '' });
  const [newApiKeyResult, setNewApiKeyResult] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [webhooksLoading, setWebhooksLoading] = useState(false);
  const [legalAudit, setLegalAudit] = useState([]);
  const [legalRisks, setLegalRisks] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [monitorData, setMonitorData] = useState(null);
  const [monitorLoading, setMonitorLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const headers = useMemo(() => ({ 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }), [token]);

  const apiFetch = useCallback(async (url, opts = {}) => {
    const r = await fetch(`${API}${url}`, { ...opts, headers: { ...headers, ...opts.headers } });
    if (r.status === 401) { setToken(''); localStorage.removeItem('nx_admin_token'); localStorage.removeItem('nx_auth'); return null; }
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
      localStorage.setItem('nx_auth', JSON.stringify({ token: d.access_token, role: 'admin', email: loginForm.email }));
    } catch (err) { setLoginErr(err.message); } finally { setLoginBusy(false); }
  };

  /* Load stats + system health */
  useEffect(() => {
    if (!token) return;
    apiFetch('/api/admin/stats').then(d => d && setStats(d));
    apiFetch('/api/admin/audit/health').then(d => d && setSystemHealth(d));
  }, [token, apiFetch]);

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
    const d = await apiFetch(`/api/admin/customers/${encodeURIComponent(email)}/casefile`);
    if (d) setCustDetail(d);
  };

  const [caseTab, setCaseTab] = useState('uebersicht');
  const [emailForm, setEmailForm] = useState({ subject: '', body: '' });
  const [noteText, setNoteText] = useState('');

  const sendDirectEmail = async () => {
    if (!custDetail || !emailForm.subject.trim()) return;
    const r = await apiFetch('/api/admin/email/send', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to_email: custDetail.email, subject: emailForm.subject, body: emailForm.body }),
    });
    if (r?.status === 'ok') {
      setEmailForm({ subject: '', body: '' });
      loadCustomerDetail(custDetail.email);
    }
  };

  const addCaseNote = async () => {
    if (!custDetail || !noteText.trim()) return;
    await apiFetch(`/api/admin/customers/${encodeURIComponent(custDetail.email)}/note`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: noteText }),
    });
    setNoteText('');
    loadCustomerDetail(custDetail.email);
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

  /* Load projects */
  useEffect(() => {
    if (!token || view !== 'projects') return;
    apiFetch('/api/admin/projects').then(d => d && setProjects(d.projects || []));
  }, [token, view, apiFetch]);

  const loadProjectDetail = async (projectId) => {
    const d = await apiFetch(`/api/admin/projects/${projectId}`);
    if (d) { setProjectDetail(d); setSelectedProject(projectId); }
  };

  const createProject = async () => {
    if (!projectForm.title.trim() || !projectForm.customer_email.trim()) return;
    const d = await apiFetch('/api/admin/projects', { method: 'POST', body: JSON.stringify(projectForm) });
    if (d) {
      setShowProjectForm(false);
      setProjectForm({ title:'', customer_email:'', tier:'', classification:'' });
      apiFetch('/api/admin/projects').then(r => r && setProjects(r.projects || []));
    }
  };

  const updateProjectStatus = async (projectId, status) => {
    await apiFetch(`/api/admin/projects/${projectId}`, { method: 'PATCH', body: JSON.stringify({ status }) });
    if (projectDetail?.project_id === projectId) {
      setProjectDetail(prev => ({ ...prev, status }));
    }
    apiFetch('/api/admin/projects').then(d => d && setProjects(d.projects || []));
  };

  const saveProjectSection = async (projectId, sectionKey, content, sectionStatus) => {
    const d = await apiFetch(`/api/admin/projects/${projectId}/sections`, {
      method: 'POST', body: JSON.stringify({ section_key: sectionKey, content, status: sectionStatus || 'entwurf' })
    });
    if (d) { loadProjectDetail(projectId); setProjectSectionEdit(null); }
  };

  const sendProjectChat = async (projectId) => {
    if (!projectChatMsg.trim()) return;
    setProjectChatSending(true);
    try {
      await apiFetch(`/api/admin/projects/${projectId}/chat`, { method: 'POST', body: JSON.stringify({ content: projectChatMsg }) });
      setProjectChatMsg('');
      loadProjectDetail(projectId);
    } catch (e) { console.error(e); } finally { setProjectChatSending(false); }
  };

  const generateBuildHandover = async (projectId) => {
    const d = await apiFetch(`/api/admin/projects/${projectId}/build-handover`, { method: 'POST', body: JSON.stringify({}) });
    if (d) { loadProjectDetail(projectId); }
  };

  /* Load contracts */
  useEffect(() => {
    if (!token || view !== 'contracts') return;
    apiFetch('/api/admin/contracts').then(d => d && setContracts(d.contracts || []));
  }, [token, view, apiFetch]);

  const loadContractDetail = async (contractId) => {
    const d = await apiFetch(`/api/admin/contracts/${contractId}`);
    if (d) { setContractDetail(d); setSelectedContract(contractId); }
  };

  const createContractFn = async () => {
    if (!contractForm.customer_email.trim()) return;
    const payload = {
      customer: { email: contractForm.customer_email, name: contractForm.customer_name, company: contractForm.customer_company },
      tier_key: contractForm.tier_key,
      contract_type: contractForm.contract_type,
      notes: contractForm.notes,
    };
    const d = await apiFetch('/api/admin/contracts', { method: 'POST', body: JSON.stringify(payload) });
    if (d) {
      setShowContractForm(false);
      setContractForm({ customer_email:'', customer_name:'', customer_company:'', tier_key:'', contract_type:'standard', notes:'' });
      apiFetch('/api/admin/contracts').then(r => r && setContracts(r.contracts || []));
    }
  };

  const updateContractStatus = async (contractId, status) => {
    await apiFetch(`/api/admin/contracts/${contractId}`, { method: 'PATCH', body: JSON.stringify({ status }) });
    loadContractDetail(contractId);
    apiFetch('/api/admin/contracts').then(d => d && setContracts(d.contracts || []));
  };

  const addAppendixFn = async (contractId) => {
    if (!appendixForm.title.trim()) return;
    const d = await apiFetch(`/api/admin/contracts/${contractId}/appendices`, {
      method: 'POST', body: JSON.stringify({
        appendix_type: appendixForm.appendix_type, title: appendixForm.title,
        content: { description: appendixForm.description },
        pricing: { amount: parseFloat(appendixForm.pricing_amount) || 0 },
      })
    });
    if (d) { setShowAppendixForm(false); setAppendixForm({ appendix_type:'ai_agents', title:'', description:'', pricing_amount:0 }); loadContractDetail(contractId); }
  };

  const sendContractFn = async (contractId) => {
    const d = await apiFetch(`/api/admin/contracts/${contractId}/send`, { method: 'POST', body: JSON.stringify({}) });
    if (d) { loadContractDetail(contractId); apiFetch('/api/admin/contracts').then(r => r && setContracts(r.contracts || [])); }
  };

  /* Load billing status */
  useEffect(() => {
    if (!token || view !== 'billing') return;
    apiFetch('/api/admin/billing/status').then(d => d && setBillingStatus(d));
  }, [token, view, apiFetch]);

  /* Load outbound pipeline */
  useEffect(() => {
    if (!token || view !== 'outbound_pipeline') return;
    apiFetch('/api/admin/outbound/pipeline').then(d => d && setOutboundPipeline(d));
    loadOutboundLeads();
  }, [token, view, apiFetch]); // eslint-disable-line

  const loadOutboundLeads = async (statusFilter) => {
    setOutboundLeadsLoading(true);
    const params = new URLSearchParams({ limit: '100' });
    if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
    const d = await apiFetch(`/api/admin/outbound/leads?${params}`);
    if (d) setOutboundLeads(d.leads || []);
    setOutboundLeadsLoading(false);
  };

  const loadOutboundDetail = async (leadId) => {
    const d = await apiFetch(`/api/admin/outbound/${leadId}`);
    if (d) { setOutboundDetail(d); setSelectedOutboundLead(leadId); }
  };

  const discoverLead = async () => {
    if (!discoverForm.name.trim()) return;
    setOutboundBusy('discover');
    const d = await apiFetch('/api/admin/outbound/discover', { method: 'POST', body: JSON.stringify(discoverForm) });
    if (d && !d.error) {
      setShowDiscoverForm(false);
      setDiscoverForm({ name:'', website:'', industry:'', email:'', phone:'', contact_name:'', country:'DE', notes:'' });
      loadOutboundLeads(outboundFilter);
      apiFetch('/api/admin/outbound/pipeline').then(r => r && setOutboundPipeline(r));
    }
    setOutboundBusy('');
  };

  const outboundAction = async (leadId, action, data = {}) => {
    setOutboundBusy(action);
    let url, method = 'POST', body = JSON.stringify(data);
    switch(action) {
      case 'prequalify': url = `/api/admin/outbound/${leadId}/prequalify`; break;
      case 'analyze': url = `/api/admin/outbound/${leadId}/analyze`; break;
      case 'legal-check': url = `/api/admin/outbound/${leadId}/legal-check`; break;
      case 'outreach': url = `/api/admin/outbound/${leadId}/outreach`; break;
      case 'send-outreach': url = `/api/admin/outbound/${leadId}/outreach/${data.outreach_id}/send`; body = '{}'; break;
      case 'followup': url = `/api/admin/outbound/${leadId}/followup`; break;
      case 'respond': url = `/api/admin/outbound/${leadId}/respond`; break;
      case 'handover': url = `/api/admin/outbound/${leadId}/handover`; break;
      default: setOutboundBusy(''); return;
    }
    const d = await apiFetch(url, { method, body });
    if (d) {
      loadOutboundDetail(leadId);
      loadOutboundLeads(outboundFilter);
      apiFetch('/api/admin/outbound/pipeline').then(r => r && setOutboundPipeline(r));
    }
    setOutboundBusy('');
    return d;
  };

  /* Load legal compliance */
  useEffect(() => {
    if (!token || view !== 'legal') return;
    apiFetch('/api/admin/legal/compliance').then(d => d && setComplianceSummary(d));
    apiFetch('/api/admin/legal/audit?limit=20').then(d => d && setLegalAudit(d.audit_log || []));
    apiFetch('/api/admin/legal/risks?resolved=false').then(d => d && setLegalRisks(d.risks || []));
  }, [token, view, apiFetch]);

  useEffect(() => { if (token && view === 'monitoring') loadMonitoring(); }, [token, view]); // eslint-disable-line
  useEffect(() => { if (token && view === 'api_keys') loadApiKeys(); }, [token, view]); // eslint-disable-line

  const logout = () => { setToken(''); localStorage.removeItem('nx_admin_token'); localStorage.removeItem('nx_auth'); };

  /* ══════════ LOGIN SCREEN ══════════ */
  if (!token) {
    localStorage.removeItem('nx_auth');
    localStorage.removeItem('nx_admin_token');
    window.location.href = '/login';
    return (
      <div style={{display:'flex',alignItems:'center',justifyContent:'center',minHeight:'100vh',background:'#080c12',color:'rgba(255,255,255,0.4)',fontSize:'0.875rem'}}>
        Weiterleitung...
      </div>
    );
  }

  /* ══════════ DASHBOARD VIEW ══════════ */
  const DashboardView = () => (
    <div className="adm-dashboard" data-testid="admin-dashboard">
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

      {/* System Health Panel */}
      {systemHealth && (
        <div className="adm-health-panel" data-testid="admin-system-health">
          <h3><I n="monitor_heart" /> System-Health</h3>
          <div className="adm-health-grid">
            <div className={`adm-health-card ${systemHealth.overall === 'healthy' ? 'ok' : 'warn'}`}>
              <span className="adm-health-dot" /><span>System</span>
              <strong>{systemHealth.overall === 'healthy' ? 'Operativ' : 'Warnung'}</strong>
            </div>
            <div className={`adm-health-card ${systemHealth.checks?.database?.status === 'ok' ? 'ok' : 'err'}`}>
              <span className="adm-health-dot" /><span>Datenbank</span>
              <strong>{systemHealth.checks?.database?.status === 'ok' ? 'Verbunden' : 'Fehler'}</strong>
            </div>
            <div className={`adm-health-card ${systemHealth.checks?.workers?.status === 'ok' ? 'ok' : 'warn'}`}>
              <span className="adm-health-dot" /><span>Workers ({systemHealth.checks?.workers?.active || 0})</span>
              <strong>{systemHealth.checks?.workers?.status === 'ok' ? 'Aktiv' : 'Prüfen'}</strong>
            </div>
            <div className={`adm-health-card ${systemHealth.checks?.llm?.status === 'ok' ? 'ok' : 'warn'}`}>
              <span className="adm-health-dot" /><span>KI-Engine</span>
              <strong>{systemHealth.checks?.llm?.status === 'ok' ? (systemHealth.checks?.llm?.provider || 'Aktiv') : 'Inaktiv'}</strong>
            </div>
            <div className={`adm-health-card ${systemHealth.checks?.scheduler?.status === 'ok' ? 'ok' : 'warn'}`}>
              <span className="adm-health-dot" /><span>Scheduler ({systemHealth.checks?.scheduler?.jobs_count || 0} Jobs)</span>
              <strong>{systemHealth.checks?.scheduler?.status === 'ok' ? 'Läuft' : 'Gestoppt'}</strong>
            </div>
            <div className={`adm-health-card ${systemHealth.checks?.memory?.status === 'ok' ? 'ok' : 'warn'}`}>
              <span className="adm-health-dot" /><span>Memory ({systemHealth.checks?.memory?.entries || 0})</span>
              <strong>{systemHealth.checks?.memory?.status === 'ok' ? 'Aktiv' : 'Inaktiv'}</strong>
            </div>
          </div>
          {systemHealth.checks?.recent_errors_24h > 0 && (
            <div className="adm-health-alert" data-testid="health-errors-alert">
              <I n="warning" /> {systemHealth.checks.recent_errors_24h} Fehler in den letzten 24h
            </div>
          )}
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
  const CustomersView = () => {
    const CASE_TABS = [
      { id: 'uebersicht', icon: 'dashboard', label: 'Übersicht' },
      { id: 'anfragen', icon: 'mail', label: 'Anfragen' },
      { id: 'angebote', icon: 'request_quote', label: 'Angebote' },
      { id: 'rechnungen', icon: 'receipt_long', label: 'Rechnungen' },
      { id: 'vertraege', icon: 'description', label: 'Verträge' },
      { id: 'email', icon: 'forward_to_inbox', label: 'E-Mail' },
      { id: 'notizen', icon: 'edit_note', label: 'Notizen' },
      { id: 'timeline', icon: 'timeline', label: 'Aktivität' },
    ];
    const cf = custDetail;
    const con = cf?.contact || {};
    return (
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
              <tr key={i} className={cf?.email === c.email ? 'active' : ''} onClick={() => { loadCustomerDetail(c.email); setCaseTab('uebersicht'); }} data-testid={`customer-row-${i}`}>
                <td>{c.vorname} {c.nachname}</td><td>{c.email}</td><td>{c.unternehmen || '-'}</td>
                <td><span className="adm-badge">{c.total_leads}</span></td>
                <td><span className="adm-badge">{c.total_bookings}</span></td>
                <td>{fmtDate(c.first_contact)}</td>
                <td onClick={e => e.stopPropagation()} style={{display:'flex',gap:'4px'}}>
                  <button className="adm-btn-sm" onClick={() => setEditCustomer({email:c.email, vorname:c.vorname||'', nachname:c.nachname||'', unternehmen:c.unternehmen||'', telefon:c.telefon||'', branche:c.branche||''})} title="Bearbeiten" data-testid={`edit-customer-${i}`}><I n="edit" /></button>
                  <button className="adm-btn-sm" style={{color:'var(--nx-accent)'}} onClick={() => generatePortalAccess(c.email)} title="Portalzugang" data-testid={`portal-btn-${i}`}><I n="link" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {customers.length === 0 && <div className="adm-empty">Keine Kunden gefunden</div>}

      {/* ══════════ KUNDEN-FALLAKTE ══════════ */}
      {cf && (
        <div className="adm-cust-detail" data-testid="customer-casefile" style={{marginTop:20}}>
          {/* Header */}
          <div className="adm-detail-header" style={{flexWrap:'wrap',gap:12}}>
            <div style={{flex:1,minWidth:200}}>
              <h3 style={{margin:0}}>{con.vorname || ''} {con.nachname || ''} {!con.vorname && cf.email}</h3>
              <div style={{display:'flex',gap:16,marginTop:6,flexWrap:'wrap',fontSize:'.8125rem',color:'var(--nx-dim)'}}>
                <span style={{display:'flex',alignItems:'center',gap:4}}><I n="mail" />{cf.email}</span>
                {con.telefon && <span style={{display:'flex',alignItems:'center',gap:4}}><I n="phone" />{con.telefon}</span>}
                {con.unternehmen && <span style={{display:'flex',alignItems:'center',gap:4}}><I n="business" />{con.unternehmen}</span>}
              </div>
            </div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              <button className="adm-btn-sm" onClick={() => setEditCustomer({email:cf.email, vorname:con.vorname||'', nachname:con.nachname||'', unternehmen:con.unternehmen||'', telefon:con.telefon||'', branche:con.branche||''})} data-testid="casefile-edit-btn"><I n="edit" /> Bearbeiten</button>
              <button className="adm-btn-sm" style={{color:'var(--nx-accent)'}} onClick={() => generatePortalAccess(cf.email)} data-testid="casefile-portal-btn"><I n="link" /> Portalzugang</button>
              <button className="adm-btn-icon" onClick={() => setCustDetail(null)} data-testid="casefile-close-btn"><I n="close" /></button>
            </div>
          </div>

          {/* Stat-Leiste */}
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(100px,1fr))',gap:8,margin:'16px 0'}}>
            {[
              { icon: 'mail', label: 'Anfragen', val: cf.stats?.total_leads },
              { icon: 'calendar_month', label: 'Buchungen', val: cf.stats?.total_bookings },
              { icon: 'request_quote', label: 'Angebote', val: cf.stats?.total_quotes },
              { icon: 'receipt_long', label: 'Rechnungen', val: cf.stats?.total_invoices },
              { icon: 'description', label: 'Verträge', val: cf.stats?.total_contracts },
              { icon: 'forward_to_inbox', label: 'E-Mails', val: cf.stats?.total_emails },
            ].map((s, i) => (
              <div key={i} style={{textAlign:'center',padding:'10px 8px',background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-sm)'}}>
                <I n={s.icon} style={{fontSize:'1rem',color:'var(--nx-accent)'}} />
                <div style={{fontSize:'1.25rem',fontWeight:800,color:'#fff'}}>{s.val || 0}</div>
                <div style={{fontSize:'.625rem',color:'var(--nx-dim)',textTransform:'uppercase',letterSpacing:'.04em'}}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Tab-Navigation */}
          <div style={{display:'flex',gap:2,borderBottom:'1px solid var(--nx-border)',marginBottom:16,overflowX:'auto'}}>
            {CASE_TABS.map(t => (
              <button key={t.id} onClick={() => setCaseTab(t.id)} data-testid={`case-tab-${t.id}`}
                style={{display:'flex',alignItems:'center',gap:6,padding:'10px 14px',background:'transparent',border:'none',borderBottom:caseTab===t.id?'2px solid var(--nx-accent)':'2px solid transparent',color:caseTab===t.id?'var(--nx-accent)':'var(--nx-dim)',fontSize:'.8125rem',fontWeight:caseTab===t.id?600:400,cursor:'pointer',whiteSpace:'nowrap',transition:'color 200ms,border-color 200ms'}}>
                <I n={t.icon} style={{fontSize:'1rem'}} />{t.label}
              </button>
            ))}
          </div>

          {/* Tab Content: Übersicht */}
          {caseTab === 'uebersicht' && (
            <div data-testid="case-uebersicht">
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:16}}>
                <div>
                  <h4 style={{fontSize:'.8125rem',color:'var(--nx-accent)',marginBottom:8}}><I n="person" /> Kontaktdaten</h4>
                  <div style={{padding:14,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',fontSize:'.8125rem'}}>
                    {[['Vorname',con.vorname],['Nachname',con.nachname],['E-Mail',cf.email],['Telefon',con.telefon],['Unternehmen',con.unternehmen],['Branche',con.branche],['Position',con.position],['Website',con.website]].map(([l,v],i)=> v ? (
                      <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'6px 0',borderBottom:'1px solid rgba(255,255,255,0.03)'}}>
                        <span style={{color:'var(--nx-dim)'}}>{l}</span><span style={{color:'#fff',fontWeight:500}}>{v}</span>
                      </div>
                    ):null)}
                  </div>
                </div>
                <div>
                  <h4 style={{fontSize:'.8125rem',color:'var(--nx-accent)',marginBottom:8}}><I n="history" /> Letzte Aktivität</h4>
                  <div style={{padding:14,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',fontSize:'.8125rem',maxHeight:240,overflowY:'auto'}}>
                    {(cf.timeline || []).slice(0, 8).map((t, i) => (
                      <div key={i} style={{display:'flex',gap:8,padding:'6px 0',borderBottom:'1px solid rgba(255,255,255,0.03)'}}>
                        <span style={{color:'var(--nx-accent)',fontSize:'.75rem'}}><I n="circle" style={{fontSize:8}} /></span>
                        <span style={{flex:1,color:'#c8d1dc'}}>{t.event}</span>
                        <span style={{color:'var(--nx-dim)',fontSize:'.6875rem',whiteSpace:'nowrap'}}>{fmtTime(t.created_at)}</span>
                      </div>
                    ))}
                    {(!cf.timeline || cf.timeline.length === 0) && <span style={{color:'var(--nx-dim)'}}>Keine Aktivität vorhanden</span>}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Content: Anfragen */}
          {caseTab === 'anfragen' && (
            <div data-testid="case-anfragen">
              {(cf.leads || []).map((l, i) => (
                <div key={i} style={{padding:14,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',marginBottom:8}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                    <span className="adm-badge" style={{background:(STATUS_MAP[l.status]?.color||'#6b7b8d')+'22',color:STATUS_MAP[l.status]?.color||'#6b7b8d'}}>{STATUS_MAP[l.status]?.label || l.status}</span>
                    <span style={{fontSize:'.6875rem',color:'var(--nx-dim)'}}>{fmtTime(l.created_at)}</span>
                  </div>
                  <div style={{fontSize:'.8125rem',color:'#c8d1dc'}}>{l.source && <span style={{fontWeight:600}}>Quelle: {l.source}</span>}</div>
                  {l.nachricht && <p style={{color:'var(--nx-dim)',fontSize:'.8125rem',marginTop:6,fontStyle:'italic'}}>"{l.nachricht}"</p>}
                  {l.notes?.length > 0 && <div style={{marginTop:8,paddingTop:8,borderTop:'1px solid rgba(255,255,255,0.03)'}}>
                    {l.notes.map((n, ni) => <div key={ni} style={{fontSize:'.75rem',color:'var(--nx-dim)',padding:'4px 0',borderLeft:'2px solid rgba(255,107,0,0.15)',paddingLeft:8,marginBottom:4}}>{n.text} <span style={{opacity:.5}}>— {fmtTime(n.date)}</span></div>)}
                  </div>}
                </div>
              ))}
              {(!cf.leads || cf.leads.length === 0) && <div className="adm-empty">Keine Anfragen</div>}
            </div>
          )}

          {/* Tab Content: Angebote */}
          {caseTab === 'angebote' && (
            <div data-testid="case-angebote">
              {(cf.quotes || []).map((q, i) => (
                <div key={i} style={{padding:14,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',marginBottom:8}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                    <span style={{fontWeight:700,color:'#fff'}}>{q.quote_number}</span>
                    <span className="adm-badge" style={{background:q.status==='accepted'?'rgba(52,211,153,0.15)':'rgba(255,107,0,0.15)',color:q.status==='accepted'?'#34d399':'var(--nx-accent)'}}>{q.status}</span>
                  </div>
                  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:8,fontSize:'.8125rem'}}>
                    <div><span style={{color:'var(--nx-dim)',fontSize:'.6875rem',display:'block'}}>Tarif</span><span style={{color:'#fff'}}>{q.calculation?.tier_name || '-'}</span></div>
                    <div><span style={{color:'var(--nx-dim)',fontSize:'.6875rem',display:'block'}}>Gesamtwert</span><span style={{color:'var(--nx-accent)',fontWeight:700}}>{q.calculation?.total_contract_eur?.toLocaleString('de-DE')} EUR</span></div>
                    <div><span style={{color:'var(--nx-dim)',fontSize:'.6875rem',display:'block'}}>Erstellt</span><span style={{color:'#c8d1dc'}}>{fmtDate(q.created_at)}</span></div>
                  </div>
                </div>
              ))}
              {(!cf.quotes || cf.quotes.length === 0) && <div className="adm-empty">Keine Angebote</div>}
            </div>
          )}

          {/* Tab Content: Rechnungen */}
          {caseTab === 'rechnungen' && (
            <div data-testid="case-rechnungen">
              {(cf.invoices || []).map((inv, i) => (
                <div key={i} style={{padding:14,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',marginBottom:8,borderColor:inv.payment_status==='overdue'?'rgba(248,113,113,0.25)':'var(--nx-border)'}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                    <span style={{fontWeight:700,color:'#fff'}}>{inv.invoice_number}</span>
                    <span className="adm-badge" style={{background:inv.payment_status==='paid'?'rgba(52,211,153,0.15)':inv.payment_status==='overdue'?'rgba(248,113,113,0.15)':'rgba(251,191,36,0.15)',color:inv.payment_status==='paid'?'#34d399':inv.payment_status==='overdue'?'#f87171':'#fbbf24'}}>{inv.payment_status==='paid'?'Bezahlt':inv.payment_status==='overdue'?'Überfällig':'Offen'}</span>
                  </div>
                  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:8,fontSize:'.8125rem'}}>
                    <div><span style={{color:'var(--nx-dim)',fontSize:'.6875rem',display:'block'}}>Betrag</span><span style={{color:'var(--nx-accent)',fontWeight:700}}>{inv.total_eur?.toLocaleString('de-DE')} EUR</span></div>
                    <div><span style={{color:'var(--nx-dim)',fontSize:'.6875rem',display:'block'}}>Fällig</span><span style={{color:'#c8d1dc'}}>{fmtDate(inv.due_date)}</span></div>
                    <div><span style={{color:'var(--nx-dim)',fontSize:'.6875rem',display:'block'}}>Erstellt</span><span style={{color:'#c8d1dc'}}>{fmtDate(inv.created_at)}</span></div>
                  </div>
                </div>
              ))}
              {(!cf.invoices || cf.invoices.length === 0) && <div className="adm-empty">Keine Rechnungen</div>}
            </div>
          )}

          {/* Tab Content: Verträge */}
          {caseTab === 'vertraege' && (
            <div data-testid="case-vertraege">
              {(cf.contracts || []).map((c, i) => (
                <div key={i} style={{padding:14,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',marginBottom:8}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                    <span style={{fontWeight:700,color:'#fff'}}>{c.contract_number || `Vertrag ${i+1}`}</span>
                    <span className="adm-badge" style={{background:c.status==='signed'?'rgba(52,211,153,0.15)':'rgba(255,107,0,0.15)',color:c.status==='signed'?'#34d399':'var(--nx-accent)'}}>{c.status}</span>
                  </div>
                  <div style={{fontSize:'.8125rem',color:'#c8d1dc'}}>Erstellt: {fmtDate(c.created_at)}</div>
                </div>
              ))}
              {(!cf.contracts || cf.contracts.length === 0) && <div className="adm-empty">Keine Verträge</div>}
            </div>
          )}

          {/* Tab Content: E-Mail */}
          {caseTab === 'email' && (
            <div data-testid="case-email">
              <div style={{padding:16,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-md)',marginBottom:16}}>
                <h4 style={{fontSize:'.8125rem',color:'var(--nx-accent)',marginBottom:12}}><I n="send" /> Direkt-E-Mail senden</h4>
                <div className="adm-field"><label>Empfänger</label><input value={cf.email} disabled style={{opacity:.6}} /></div>
                <div className="adm-field"><label>Betreff</label><input value={emailForm.subject} onChange={e => setEmailForm({...emailForm, subject: e.target.value})} placeholder="Betreff eingeben..." data-testid="case-email-subject" /></div>
                <div className="adm-field"><label>Nachricht</label><textarea value={emailForm.body} onChange={e => setEmailForm({...emailForm, body: e.target.value})} placeholder="Ihre Nachricht..." rows={5} style={{resize:'vertical',width:'100%',background:'var(--nx-s1)',border:'1px solid var(--nx-border)',color:'#fff',padding:'10px 14px',fontSize:'.875rem',borderRadius:'var(--r-sm)'}} data-testid="case-email-body" /></div>
                <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'10px 24px',marginTop:8}} onClick={sendDirectEmail} disabled={!emailForm.subject.trim()} data-testid="case-email-send-btn"><I n="send" /> E-Mail senden</button>
              </div>
              <h4 style={{fontSize:'.8125rem',color:'var(--nx-dim)',marginBottom:8}}>Gesendete E-Mails ({cf.emails_sent?.length || 0})</h4>
              {(cf.emails_sent || []).map((e, i) => (
                <div key={i} style={{padding:12,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-sm)',marginBottom:6}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                    <span style={{fontWeight:600,color:'#fff',fontSize:'.8125rem'}}>{e.subject}</span>
                    <span style={{color:'var(--nx-dim)',fontSize:'.6875rem'}}>{fmtTime(e.sent_at)}</span>
                  </div>
                  {e.body_preview && <p style={{color:'var(--nx-dim)',fontSize:'.75rem',marginTop:4}}>{e.body_preview}</p>}
                  <span style={{fontSize:'.625rem',color:e.result?.sent?'#34d399':'#f87171'}}>{e.result?.sent?'Gesendet':'Fehlgeschlagen'}</span>
                </div>
              ))}
              {(!cf.emails_sent || cf.emails_sent.length === 0) && <div className="adm-empty" style={{padding:20}}>Noch keine E-Mails gesendet</div>}
            </div>
          )}

          {/* Tab Content: Notizen */}
          {caseTab === 'notizen' && (
            <div data-testid="case-notizen">
              <div style={{display:'flex',gap:8,marginBottom:16}}>
                <input value={noteText} onChange={e => setNoteText(e.target.value)} placeholder="Notiz hinzufügen..." style={{flex:1,background:'var(--nx-s1)',border:'1px solid var(--nx-border)',color:'#fff',padding:'10px 14px',fontSize:'.875rem',borderRadius:'var(--r-sm)'}} data-testid="case-note-input" onKeyDown={e => e.key==='Enter' && addCaseNote()} />
                <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'10px 20px'}} onClick={addCaseNote} disabled={!noteText.trim()} data-testid="case-note-add-btn"><I n="add" /> Hinzufügen</button>
              </div>
              {(con.notes || []).slice().reverse().map((n, i) => (
                <div key={i} style={{padding:12,background:'rgba(255,255,255,0.02)',border:'1px solid var(--nx-border)',borderRadius:'var(--r-sm)',marginBottom:6,borderLeft:'3px solid rgba(255,107,0,0.2)'}}>
                  <div style={{fontSize:'.8125rem',color:'#c8d1dc'}}>{n.text}</div>
                  <div style={{fontSize:'.6875rem',color:'var(--nx-dim)',marginTop:4}}>{n.author} — {fmtTime(n.created_at || n.date)}</div>
                </div>
              ))}
              {(!con.notes || con.notes.length === 0) && <div className="adm-empty" style={{padding:20}}>Keine Notizen vorhanden</div>}
            </div>
          )}

          {/* Tab Content: Timeline */}
          {caseTab === 'timeline' && (
            <div data-testid="case-timeline">
              <div className="adm-timeline-list">
                {(cf.timeline || []).map((t, i) => (
                  <div key={i} className="adm-timeline-item">
                    <div className="adm-timeline-icon"><I n="circle" /></div>
                    <div className="adm-timeline-content">
                      <span className="adm-timeline-event">{t.event}</span>
                      {t.detail && <span className="adm-timeline-ref">{t.detail}</span>}
                      {t.actor && <span className="adm-timeline-actor">{t.actor}</span>}
                    </div>
                    <span className="adm-timeline-time">{fmtTime(t.created_at)}</span>
                  </div>
                ))}
                {(!cf.timeline || cf.timeline.length === 0) && <div className="adm-empty">Keine Aktivität</div>}
              </div>
            </div>
          )}
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
  };

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
            <div style={{display:'grid',gridTemplateColumns:'1fr 2fr',gap:'12px',marginTop:'12px',padding:'14px',background:'rgba(255,107,0,0.04)',borderRadius:8,border:'1px solid rgba(255,107,0,0.08)'}}>
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
            <div style={{display:'grid',gridTemplateColumns:'1fr 2fr',gap:'12px',marginTop:12,padding:'12px',background:'rgba(255,107,0,0.04)',borderRadius:8,border:'1px solid rgba(255,107,0,0.08)'}}>
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

  /* ══════════ PROJECTS VIEW ══════════ */
  const PROJECT_STATUS_MAP = {
    draft: { l: 'Entwurf', c: '#6b7b8d' }, discovery: { l: 'Discovery', c: '#3b82f6' },
    planning: { l: 'Planung', c: '#f59e0b' }, approved: { l: 'Freigegeben', c: '#10b981' },
    build: { l: 'Build', c: '#8b5cf6' }, review: { l: 'Review', c: '#ec4899' },
    handover: { l: 'Handover', c: '#06b6d4' }, live: { l: 'Live', c: '#22c55e' },
    paused: { l: 'Pausiert', c: '#f97316' }, closed: { l: 'Geschlossen', c: '#64748b' },
  };
  const SEC_STATUS_MAP = {
    leer: { l: 'Ausstehend', c: '#4a5568' }, entwurf: { l: 'Entwurf', c: '#f59e0b' },
    review: { l: 'Review', c: '#3b82f6' }, freigegeben: { l: 'Freigegeben', c: '#10b981' },
  };

  const ProjectsView = () => {
    if (projectDetail && selectedProject) {
      const pd = projectDetail;
      const sectionDefs = pd.section_definitions || {};
      const sectionsMap = {};
      (pd.sections || []).forEach(s => { sectionsMap[s.section_key] = s; });
      const allKeys = Object.keys(sectionDefs).filter(k => k !== 'startprompt_emergent');
      const internalKeys = ['startprompt_emergent'];
      const completeness = pd.completeness || 0;

      return (
        <div className="adm-project-detail" data-testid="project-detail">
          <button className="adm-back-btn" onClick={() => { setSelectedProject(null); setProjectDetail(null); setProjectSectionEdit(null); }} data-testid="project-back-btn"><I n="arrow_back" /> Alle Projekte</button>
          <div style={{display:'flex',gap:16,alignItems:'center',marginBottom:16,flexWrap:'wrap'}}>
            <h2 style={{margin:0,fontSize:'1.25rem'}}>{pd.title}</h2>
            <span className="adm-badge" style={{background:(PROJECT_STATUS_MAP[pd.status]?.c||'#6b7b8d')+'22',color:PROJECT_STATUS_MAP[pd.status]?.c||'#6b7b8d'}}>{PROJECT_STATUS_MAP[pd.status]?.l||pd.status}</span>
            <select className="adm-select-sm" value={pd.status} onChange={e => updateProjectStatus(pd.project_id, e.target.value)} data-testid="project-status-select">
              {Object.entries(PROJECT_STATUS_MAP).map(([k,v])=><option key={k} value={k}>{v.l}</option>)}
            </select>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))',gap:8,marginBottom:20}}>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Kunde</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{pd.customer_email}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Tarif</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{pd.tier || '-'}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Version</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>v{pd.build_handover_version || 0}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Vollständigkeit</div><div style={{color:'#FF6B00',fontSize:'1rem',fontWeight:700}}>{completeness}%</div></div>
          </div>

          {/* Progress Bar */}
          <div style={{background:'rgba(255,255,255,0.04)',borderRadius:6,height:8,marginBottom:20,overflow:'hidden'}}>
            <div style={{background:'linear-gradient(90deg,#FF6B00,#FF8533)',height:'100%',width:`${completeness}%`,borderRadius:6,transition:'width .5s'}}></div>
          </div>

          {/* Sections Grid */}
          <h3 style={{fontSize:'.9375rem',color:'#fff',marginBottom:12}}>Planungssektionen</h3>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(280px,1fr))',gap:10,marginBottom:24}}>
            {allKeys.map(key => {
              const sec = sectionsMap[key];
              const st = sec ? (SEC_STATUS_MAP[sec.status] || SEC_STATUS_MAP.entwurf) : SEC_STATUS_MAP.leer;
              return (
                <div key={key} className="adm-wa-card" style={{padding:'14px 16px',cursor:'pointer',borderLeft:`3px solid ${st.c}`}} onClick={() => setProjectSectionEdit({ key, content: sec?.content || '', status: sec?.status || 'entwurf' })} data-testid={`section-${key}`}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                    <span style={{fontSize:'.8125rem',color:'#fff',fontWeight:600}}>{sectionDefs[key] || key}</span>
                    <span className="adm-badge" style={{background:st.c+'22',color:st.c,fontSize:'.625rem'}}>{st.l}{sec ? ` v${sec.version}` : ''}</span>
                  </div>
                  {sec?.content && <p style={{fontSize:'.75rem',color:'#6b7b8d',marginTop:6,overflow:'hidden',textOverflow:'ellipsis',display:'-webkit-box',WebkitLineClamp:2,WebkitBoxOrient:'vertical'}}>{sec.content.slice(0,120)}</p>}
                </div>
              );
            })}
          </div>

          {/* Internal section: Startprompt */}
          {internalKeys.map(key => {
            const sec = sectionsMap[key];
            return (
              <div key={key} style={{marginBottom:16}}>
                <div className="adm-wa-card" style={{padding:'14px 16px',cursor:'pointer',borderLeft:'3px solid #ef4444',opacity:.7}} onClick={() => setProjectSectionEdit({ key, content: sec?.content || '', status: sec?.status || 'entwurf' })} data-testid={`section-${key}`}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                    <span style={{fontSize:'.8125rem',color:'#ef4444',fontWeight:600}}>{sectionDefs[key] || key} (intern)</span>
                    <span className="adm-badge" style={{background:'#ef444422',color:'#ef4444',fontSize:'.625rem'}}>{sec ? `v${sec.version}` : 'leer'}</span>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Section Editor Modal */}
          {projectSectionEdit && (
            <div className="adm-modal-overlay" onClick={e => e.target === e.currentTarget && setProjectSectionEdit(null)}>
              <div className="adm-modal" style={{maxWidth:720}} data-testid="section-editor-modal">
                <h3>{sectionDefs[projectSectionEdit.key] || projectSectionEdit.key}</h3>
                <textarea value={projectSectionEdit.content} onChange={e => setProjectSectionEdit({...projectSectionEdit, content: e.target.value})} rows={12} style={{width:'100%',resize:'vertical',background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',padding:12,fontSize:'.8125rem',fontFamily:'monospace',borderRadius:6}} placeholder="Inhalt der Sektion..." data-testid="section-content-textarea" />
                <div style={{display:'flex',gap:8,marginTop:12,alignItems:'center'}}>
                  <select className="adm-select" value={projectSectionEdit.status} onChange={e => setProjectSectionEdit({...projectSectionEdit, status: e.target.value})} style={{width:140}} data-testid="section-status-select">
                    <option value="entwurf">Entwurf</option>
                    <option value="review">Review</option>
                    <option value="freigegeben">Freigegeben</option>
                  </select>
                  <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={() => saveProjectSection(pd.project_id, projectSectionEdit.key, projectSectionEdit.content, projectSectionEdit.status)} disabled={!projectSectionEdit.content.trim()} data-testid="section-save-btn"><I n="check" /> Speichern</button>
                  <button className="adm-btn adm-btn-secondary" onClick={() => setProjectSectionEdit(null)}>Abbrechen</button>
                </div>
              </div>
            </div>
          )}

          {/* Build Handover */}
          <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap'}}>
            <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'10px 20px'}} onClick={() => generateBuildHandover(pd.project_id)} data-testid="generate-handover-btn"><I n="construction" /> Build-Handover generieren</button>
            {pd.latest_version && <a className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'10px 20px',textDecoration:'none',display:'inline-flex',alignItems:'center',gap:6}} href={`${API}/api/admin/projects/${pd.project_id}/download-handover`} target="_blank" rel="noopener noreferrer" data-testid="download-handover-btn"><I n="download" /> Download v{pd.latest_version.version}</a>}
          </div>
          {pd.latest_version && (
            <div className="adm-wa-card" style={{marginBottom:20}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                <h3 style={{margin:0,fontSize:'.9375rem'}}>Build-Ready-Markdown (v{pd.latest_version.version})</h3>
                <span style={{fontSize:'.6875rem',color:'#6b7b8d'}}>{fmtTime(pd.latest_version.created_at)}</span>
              </div>
              <pre style={{background:'rgba(12,17,23,0.8)',padding:16,borderRadius:6,fontSize:'.75rem',color:'#c8d1dc',overflow:'auto',maxHeight:400,whiteSpace:'pre-wrap',wordBreak:'break-word'}} data-testid="build-handover-content">{pd.latest_version.markdown}</pre>
            </div>
          )}

          {/* Project Chat */}
          <h3 style={{fontSize:'.9375rem',color:'#fff',marginBottom:12}}>Projektchat</h3>
          <div className="adm-wa-card" style={{marginBottom:16}}>
            <div style={{maxHeight:320,overflowY:'auto',marginBottom:12}}>
              {(pd.chat || []).map(m => (
                <div key={m.message_id} style={{marginBottom:10,padding:'8px 12px',background:m.sender_type==='customer'?'rgba(59,130,246,0.08)':'rgba(255,107,0,0.06)',borderRadius:6,borderLeft:`3px solid ${m.sender_type==='customer'?'#3b82f6':'#FF6B00'}`}}>
                  <div style={{display:'flex',justifyContent:'space-between',fontSize:'.6875rem',color:'#6b7b8d',marginBottom:4}}>
                    <span>{m.sender} ({m.sender_type})</span>
                    <span>{fmtTime(m.timestamp)}</span>
                  </div>
                  <div style={{fontSize:'.8125rem',color:'#c8d1dc',whiteSpace:'pre-wrap'}}>{m.content}</div>
                </div>
              ))}
              {(!pd.chat || pd.chat.length === 0) && <div style={{textAlign:'center',padding:20,color:'#4a5568',fontSize:'.8125rem'}}>Noch keine Nachrichten</div>}
            </div>
            <div style={{display:'flex',gap:8}}>
              <input style={{flex:1,background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',padding:'10px 14px',fontSize:'.8125rem',borderRadius:4}} value={projectChatMsg} onChange={e => setProjectChatMsg(e.target.value)} placeholder="Nachricht schreiben..." onKeyDown={e => { if (e.key==='Enter'&&!e.shiftKey) { e.preventDefault(); sendProjectChat(pd.project_id); }}} data-testid="project-chat-input" />
              <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'10px 20px',flexShrink:0}} onClick={() => sendProjectChat(pd.project_id)} disabled={projectChatSending || !projectChatMsg.trim()} data-testid="project-chat-send"><I n="send" /></button>
            </div>
          </div>
        </div>
      );
    }

    // Project List
    return (
      <div className="adm-projects" data-testid="admin-projects">
        <div className="adm-section-header">
          <h2>Projekte ({projects.length})</h2>
          <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => setShowProjectForm(true)} data-testid="create-project-btn"><I n="add_circle" /> Neues Projekt</button>
        </div>

        {showProjectForm && (
          <div className="adm-form-card" data-testid="project-create-form">
            <h3>Projekt anlegen</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Titel *</label><input value={projectForm.title} onChange={e => setProjectForm({...projectForm, title: e.target.value})} placeholder="KI-Agenten für Vertrieb" data-testid="project-title-input" /></div>
              <div className="adm-field"><label>Kunden-E-Mail *</label><input type="email" value={projectForm.customer_email} onChange={e => setProjectForm({...projectForm, customer_email: e.target.value})} placeholder="kunde@firma.de" data-testid="project-email-input" /></div>
              <div className="adm-field"><label>Tarif</label><select className="adm-select" value={projectForm.tier} onChange={e => setProjectForm({...projectForm, tier: e.target.value})} data-testid="project-tier-select"><option value="">—</option><option value="starter">Starter AI Agenten AG</option><option value="growth">Growth AI Agenten AG</option><option value="website_starter">Website Starter</option><option value="website_professional">Website Professional</option><option value="website_enterprise">Website Enterprise</option><option value="seo_starter">SEO Starter</option><option value="seo_growth">SEO Growth</option><option value="bundle">Bundle</option></select></div>
              <div className="adm-field"><label>Klassifikation</label><input value={projectForm.classification} onChange={e => setProjectForm({...projectForm, classification: e.target.value})} placeholder="z.B. Standard, Enterprise..." data-testid="project-class-input" /></div>
            </div>
            <div className="adm-form-actions">
              <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={createProject} disabled={!projectForm.title.trim()||!projectForm.customer_email.trim()} data-testid="project-save-btn"><I n="check" /> Erstellen</button>
              <button className="adm-btn adm-btn-secondary" onClick={() => setShowProjectForm(false)}>Abbrechen</button>
            </div>
          </div>
        )}

        <div className="adm-table-wrap">
          <table className="adm-table" data-testid="projects-table">
            <thead><tr><th>Titel</th><th>Kunde</th><th>Tarif</th><th>Status</th><th>Vollst.</th><th>Version</th><th>Erstellt</th><th></th></tr></thead>
            <tbody>
              {projects.map(p => {
                const st = PROJECT_STATUS_MAP[p.status] || PROJECT_STATUS_MAP.draft;
                return (
                  <tr key={p.project_id} className="adm-row-click" onClick={() => loadProjectDetail(p.project_id)} data-testid={`project-row-${p.project_id}`}>
                    <td style={{fontWeight:600,color:'#fff'}}>{p.title}</td>
                    <td>{p.customer_email}</td>
                    <td>{p.tier || '-'}</td>
                    <td><span className="adm-badge" style={{background:st.c+'22',color:st.c}}>{st.l}</span></td>
                    <td><span style={{color:p.completeness>=80?'#10b981':p.completeness>=40?'#f59e0b':'#6b7b8d',fontWeight:600}}>{p.completeness||0}%</span></td>
                    <td>v{p.build_handover_version||0}</td>
                    <td>{fmtDate(p.created_at)}</td>
                    <td><button className="adm-btn-sm"><I n="visibility" /></button></td>
                  </tr>
                );
              })}
              {projects.length === 0 && <tr><td colSpan="8" style={{textAlign:'center',padding:32,color:'#4a5568'}}>Noch keine Projekte angelegt</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  /* ══════════ CONTRACTS VIEW (P2) ══════════ */
  const CTR_STATUS_MAP = {
    draft: { l:'Entwurf', c:'#6b7b8d' }, review: { l:'Review', c:'#f59e0b' },
    sent: { l:'Versendet', c:'#3b82f6' }, viewed: { l:'Eingesehen', c:'#06b6d4' },
    accepted: { l:'Angenommen', c:'#10b981' }, declined: { l:'Abgelehnt', c:'#ef4444' },
    change_requested: { l:'Änderung', c:'#f97316' }, amended: { l:'Nachgetragen', c:'#8b5cf6' },
    cancelled: { l:'Storniert', c:'#64748b' }, expired: { l:'Abgelaufen', c:'#4a5568' },
  };
  const CTR_TYPE_MAP = { standard:'Standardvertrag', individual:'Individualvertrag', amendment:'Nachtragsvertrag' };
  const APX_TYPE_MAP = { ai_agents:'KI-Agenten', website:'Website', seo:'SEO', app:'App', ai_addon:'KI Add-on', bundle:'Bundle', custom:'Sonderposition' };

  const ContractsView = () => {
    if (contractDetail && selectedContract) {
      const cd = contractDetail;
      const st = CTR_STATUS_MAP[cd.status] || CTR_STATUS_MAP.draft;
      return (
        <div className="adm-contract-detail" data-testid="contract-detail">
          <button className="adm-back-btn" onClick={() => { setSelectedContract(null); setContractDetail(null); setShowAppendixForm(false); }} data-testid="contract-back-btn"><I n="arrow_back" /> Alle Verträge</button>
          <div style={{display:'flex',gap:16,alignItems:'center',marginBottom:16,flexWrap:'wrap'}}>
            <h2 style={{margin:0,fontSize:'1.25rem'}}>Vertrag {cd.contract_number}</h2>
            <span className="adm-badge" style={{background:st.c+'22',color:st.c}}>{st.l}</span>
            <span className="adm-badge" style={{background:'rgba(255,255,255,0.06)',color:'#c8d1dc'}}>{CTR_TYPE_MAP[cd.contract_type] || cd.contract_type}</span>
            <select className="adm-select-sm" value={cd.status} onChange={e => updateContractStatus(cd.contract_id, e.target.value)} data-testid="contract-status-select">
              {Object.entries(CTR_STATUS_MAP).map(([k,v])=><option key={k} value={k}>{v.l}</option>)}
            </select>
          </div>
          {/* Meta cards */}
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))',gap:8,marginBottom:20}}>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Kunde</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{cd.customer?.name||cd.customer?.email}</div><div style={{fontSize:'.6875rem',color:'#6b7b8d'}}>{cd.customer?.company}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Tarif</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{cd.calculation?.tier_name || cd.tier_key || '-'}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Version</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>v{cd.version||1}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Hash</div><div style={{color:'#FF6B00',fontSize:'.6875rem',fontFamily:'monospace',wordBreak:'break-all'}}>{cd.document_hash?.slice(0,16)}...</div></div>
          </div>
          {/* Calculation */}
          {cd.calculation && cd.calculation.total_contract_eur && (
            <div className="adm-wa-card" style={{marginBottom:16}}>
              <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Kommerzielle Konditionen</h3>
              <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(200px,1fr))',gap:10}}>
                <div><span style={{fontSize:'.6875rem',color:'#6b7b8d'}}>Gesamtvertragswert</span><br/><span style={{color:'#fff',fontWeight:600}}>{(cd.calculation.total_contract_eur||0).toLocaleString('de-DE',{style:'currency',currency:'EUR'})}</span></div>
                <div><span style={{fontSize:'.6875rem',color:'#6b7b8d'}}>Aktivierungsanzahlung</span><br/><span style={{color:'#FF6B00',fontWeight:600}}>{(cd.calculation.upfront_eur||0).toLocaleString('de-DE',{style:'currency',currency:'EUR'})}</span></div>
                <div><span style={{fontSize:'.6875rem',color:'#6b7b8d'}}>Monatsrate</span><br/><span style={{color:'#fff',fontWeight:600}}>{(cd.calculation.recurring_eur||0).toLocaleString('de-DE',{style:'currency',currency:'EUR'})}</span></div>
                <div><span style={{fontSize:'.6875rem',color:'#6b7b8d'}}>Laufzeit</span><br/><span style={{color:'#fff',fontWeight:600}}>{cd.calculation.contract_months||0} Monate</span></div>
              </div>
            </div>
          )}
          {/* Appendices */}
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
            <h3 style={{margin:0,fontSize:'.9375rem'}}>Anlagen ({(cd.appendices_detail||[]).length})</h3>
            <button className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'6px 14px',fontSize:'.75rem'}} onClick={() => setShowAppendixForm(!showAppendixForm)} data-testid="add-appendix-btn"><I n="add" /> Anlage</button>
          </div>
          {showAppendixForm && (
            <div className="adm-form-card" style={{marginBottom:16}} data-testid="appendix-form">
              <div className="adm-form-grid">
                <div className="adm-field"><label>Typ</label><select className="adm-select" value={appendixForm.appendix_type} onChange={e => setAppendixForm({...appendixForm, appendix_type: e.target.value})}>{Object.entries(APX_TYPE_MAP).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></div>
                <div className="adm-field"><label>Titel</label><input value={appendixForm.title} onChange={e => setAppendixForm({...appendixForm, title: e.target.value})} placeholder="Anlage: KI-Agenten Vertrieb" data-testid="appendix-title-input" /></div>
                <div className="adm-field"><label>Beschreibung</label><input value={appendixForm.description} onChange={e => setAppendixForm({...appendixForm, description: e.target.value})} placeholder="Leistungsbeschreibung..." /></div>
                <div className="adm-field"><label>Betrag (EUR)</label><input type="number" value={appendixForm.pricing_amount} onChange={e => setAppendixForm({...appendixForm, pricing_amount: e.target.value})} /></div>
              </div>
              <div style={{display:'flex',gap:8,marginTop:12}}>
                <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 16px'}} onClick={() => addAppendixFn(cd.contract_id)} disabled={!appendixForm.title.trim()} data-testid="save-appendix-btn"><I n="check" /> Hinzufügen</button>
                <button className="adm-btn adm-btn-secondary" onClick={() => setShowAppendixForm(false)}>Abbrechen</button>
              </div>
            </div>
          )}
          {(cd.appendices_detail||[]).map(a => (
            <div key={a.appendix_id} className="adm-wa-card" style={{marginBottom:8,borderLeft:`3px solid ${a.appendix_type==='custom'?'#f59e0b':'#3b82f6'}`}} data-testid={`appendix-${a.appendix_id}`}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <div><span style={{fontWeight:600,color:'#fff',fontSize:'.8125rem'}}>{a.title}</span> <span className="adm-badge" style={{background:'rgba(59,130,246,0.12)',color:'#3b82f6',fontSize:'.625rem'}}>{APX_TYPE_MAP[a.appendix_type]||a.appendix_type}</span></div>
                {a.pricing?.amount > 0 && <span style={{color:'#FF6B00',fontWeight:600,fontSize:'.8125rem'}}>{parseFloat(a.pricing.amount).toLocaleString('de-DE',{style:'currency',currency:'EUR'})}</span>}
              </div>
              {a.content?.description && <p style={{margin:'6px 0 0',fontSize:'.75rem',color:'#6b7b8d'}}>{a.content.description}</p>}
            </div>
          ))}
          {/* Legal Modules */}
          <h3 style={{fontSize:'.9375rem',color:'#fff',marginTop:20,marginBottom:12}}>Rechtsmodule</h3>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(240px,1fr))',gap:8,marginBottom:20}}>
            {(cd.legal_module_definitions||[]).map(lm => {
              const accepted = cd.legal_modules?.[lm.key]?.accepted;
              return (
                <div key={lm.key} className="adm-wa-card" style={{padding:'10px 14px',borderLeft:`3px solid ${accepted?'#10b981':lm.required?'#ef4444':'#4a5568'}`}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                    <span style={{fontSize:'.8125rem',color:'#fff'}}>{lm.label}</span>
                    <span className="adm-badge" style={{background:accepted?'#10b98122':'#ef444422',color:accepted?'#10b981':'#ef4444',fontSize:'.625rem'}}>{accepted?'Akzeptiert':'Ausstehend'}{lm.required?' *':''}</span>
                  </div>
                </div>
              );
            })}
          </div>
          {/* Evidence */}
          {(cd.evidence_list||[]).length > 0 && (
            <>
              <h3 style={{fontSize:'.9375rem',color:'#fff',marginBottom:12}}>Evidenzpaket</h3>
              {cd.evidence_list.map(ev => (
                <div key={ev.evidence_id} className="adm-wa-card" style={{marginBottom:8,padding:'12px 16px'}}>
                  <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(200px,1fr))',gap:6,fontSize:'.75rem'}}>
                    <div><span style={{color:'#6b7b8d'}}>Aktion:</span> <span style={{color:ev.action==='accepted'?'#10b981':'#ef4444',fontWeight:600}}>{ev.action}</span></div>
                    <div><span style={{color:'#6b7b8d'}}>Zeitstempel:</span> <span style={{color:'#fff'}}>{fmtTime(ev.timestamp)}</span></div>
                    <div><span style={{color:'#6b7b8d'}}>IP:</span> <span style={{color:'#fff'}}>{ev.ip_address}</span></div>
                    <div><span style={{color:'#6b7b8d'}}>Signaturtyp:</span> <span style={{color:'#fff'}}>{ev.signature_type||'-'}</span></div>
                    <div style={{gridColumn:'1/-1'}}><span style={{color:'#6b7b8d'}}>Dokument-Hash:</span> <span style={{color:'#FF6B00',fontFamily:'monospace',fontSize:'.6875rem'}}>{ev.document_hash}</span></div>
                    <div style={{gridColumn:'1/-1'}}><span style={{color:'#6b7b8d'}}>User Agent:</span> <span style={{color:'#c8d1dc',fontSize:'.6875rem'}}>{ev.user_agent?.slice(0,80)}</span></div>
                  </div>
                </div>
              ))}
            </>
          )}
          {/* Actions */}
          <div style={{display:'flex',gap:8,marginTop:20,flexWrap:'wrap'}}>
            {['draft','review'].includes(cd.status) && <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'10px 20px'}} onClick={() => sendContractFn(cd.contract_id)} data-testid="send-contract-btn"><I n="send" /> An Kunden senden</button>}
            <button className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'10px 20px'}} onClick={async () => {
              const r = await apiFetch(`/api/admin/contracts/${cd.contract_id}/generate-pdf`, { method: 'POST' });
              if (r?.generated) { window.open(`${API}/api/documents/contract/${cd.contract_id}/pdf`, '_blank'); loadContractDetail(cd.contract_id); }
            }} data-testid="contract-generate-pdf-btn"><I n="picture_as_pdf" /> PDF generieren & herunterladen</button>
            {cd.has_pdf && <a href={`${API}/api/documents/contract/${cd.contract_id}/pdf`} target="_blank" rel="noreferrer" className="adm-btn" style={{width:'auto',padding:'10px 20px',textDecoration:'none',display:'flex',alignItems:'center',gap:6}} data-testid="contract-download-pdf-btn"><I n="download" /> PDF herunterladen</a>}
          </div>
        </div>
      );
    }

    // Contract List
    return (
      <div className="adm-contracts" data-testid="admin-contracts">
        <div className="adm-section-header">
          <h2>Verträge ({contracts.length})</h2>
          <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => setShowContractForm(true)} data-testid="create-contract-btn"><I n="add_circle" /> Neuer Vertrag</button>
        </div>
        {showContractForm && (
          <div className="adm-form-card" data-testid="contract-create-form">
            <h3>Vertrag erstellen</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Kunden-E-Mail *</label><input type="email" value={contractForm.customer_email} onChange={e => setContractForm({...contractForm, customer_email: e.target.value})} placeholder="kunde@firma.de" data-testid="contract-email-input" /></div>
              <div className="adm-field"><label>Name</label><input value={contractForm.customer_name} onChange={e => setContractForm({...contractForm, customer_name: e.target.value})} placeholder="Max Mustermann" /></div>
              <div className="adm-field"><label>Firma</label><input value={contractForm.customer_company} onChange={e => setContractForm({...contractForm, customer_company: e.target.value})} placeholder="Firma GmbH" /></div>
              <div className="adm-field"><label>Tarif</label><select className="adm-select" value={contractForm.tier_key} onChange={e => setContractForm({...contractForm, tier_key: e.target.value})} data-testid="contract-tier-select"><option value="">—</option><option value="starter">Starter AI Agenten AG</option><option value="growth">Growth AI Agenten AG</option></select></div>
              <div className="adm-field"><label>Vertragstyp</label><select className="adm-select" value={contractForm.contract_type} onChange={e => setContractForm({...contractForm, contract_type: e.target.value})} data-testid="contract-type-select"><option value="standard">Standardvertrag</option><option value="individual">Individualvertrag</option><option value="amendment">Nachtragsvertrag</option></select></div>
              <div className="adm-field"><label>Notizen</label><input value={contractForm.notes} onChange={e => setContractForm({...contractForm, notes: e.target.value})} placeholder="Interne Notizen..." /></div>
            </div>
            <div className="adm-form-actions">
              <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={createContractFn} disabled={!contractForm.customer_email.trim()} data-testid="contract-save-btn"><I n="check" /> Erstellen</button>
              <button className="adm-btn adm-btn-secondary" onClick={() => setShowContractForm(false)}>Abbrechen</button>
            </div>
          </div>
        )}
        <div className="adm-table-wrap">
          <table className="adm-table" data-testid="contracts-table">
            <thead><tr><th>Nr.</th><th>Kunde</th><th>Tarif</th><th>Typ</th><th>Status</th><th>Version</th><th>Erstellt</th><th></th></tr></thead>
            <tbody>
              {contracts.map(c => {
                const st = CTR_STATUS_MAP[c.status] || CTR_STATUS_MAP.draft;
                return (
                  <tr key={c.contract_id} className="adm-row-click" onClick={() => loadContractDetail(c.contract_id)} data-testid={`contract-row-${c.contract_id}`}>
                    <td style={{fontWeight:600,color:'#fff'}}>{c.contract_number}</td>
                    <td>{c.customer?.name || c.customer?.email}</td>
                    <td>{c.calculation?.tier_name || c.tier_key || '-'}</td>
                    <td>{CTR_TYPE_MAP[c.contract_type]||c.contract_type}</td>
                    <td><span className="adm-badge" style={{background:st.c+'22',color:st.c}}>{st.l}</span></td>
                    <td>v{c.version||1}</td>
                    <td>{fmtDate(c.created_at)}</td>
                    <td><button className="adm-btn-sm"><I n="visibility" /></button></td>
                  </tr>
                );
              })}
              {contracts.length === 0 && <tr><td colSpan="8" style={{textAlign:'center',padding:32,color:'#4a5568'}}>Noch keine Verträge</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  /* ══════════ BILLING DASHBOARD (P7) ══════════ */
  const BillingView = () => {
    const bs = billingStatus;
    if (!bs) return <div style={{textAlign:'center',padding:40,color:'#4a5568'}}>Lade Billing-Status...</div>;
    return (
      <div data-testid="admin-billing">
        <h2>Billing-Dashboard</h2>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:12,marginBottom:24}}>
          <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Angebote</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#fff'}}>{bs.quotes?.total || 0}</div><div style={{fontSize:'.75rem',color:'#10b981'}}>davon akzeptiert: {bs.quotes?.accepted || 0}</div></div>
          <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Rechnungen</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#fff'}}>{bs.invoices?.total || 0}</div><div style={{fontSize:'.75rem',color:'#10b981'}}>bezahlt: {bs.invoices?.paid || 0}</div><div style={{fontSize:'.75rem',color:'#f59e0b'}}>offen: {bs.invoices?.pending || 0}</div><div style={{fontSize:'.75rem',color:'#ef4444'}}>überfällig: {bs.invoices?.overdue || 0}</div></div>
          <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Verträge</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#fff'}}>{bs.contracts?.total || 0}</div><div style={{fontSize:'.75rem',color:'#10b981'}}>aktiv: {bs.contracts?.active || 0}</div></div>
          <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Umsatz</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#FF6B00'}}>{(bs.revenue?.total_gross||0).toLocaleString('de-DE',{style:'currency',currency:'EUR'})}</div><div style={{fontSize:'.75rem',color:'#f59e0b'}}>offen: {(bs.revenue?.total_open||0).toLocaleString('de-DE',{style:'currency',currency:'EUR'})}</div></div>
        </div>
      </div>
    );
  };

  /* ══════════ OUTBOUND LEAD MACHINE (P6) ══════════ */
  const OB_STATUS_MAP = {
    discovered:{l:'Entdeckt',c:'#6b7b8d',icon:'search'}, analyzing:{l:'Analyse',c:'#3b82f6',icon:'analytics'},
    qualified:{l:'Qualifiziert',c:'#10b981',icon:'check_circle'}, unqualified:{l:'Unqualifiziert',c:'#64748b',icon:'cancel'},
    legal_blocked:{l:'Legal blockiert',c:'#ef4444',icon:'block'}, outreach_ready:{l:'Outreach-bereit',c:'#8b5cf6',icon:'send'},
    contacted:{l:'Kontaktiert',c:'#06b6d4',icon:'mark_email_read'}, followup_1:{l:'Follow-up 1',c:'#f59e0b',icon:'replay'},
    followup_2:{l:'Follow-up 2',c:'#f97316',icon:'replay'}, followup_3:{l:'Follow-up 3',c:'#dc2626',icon:'replay'},
    responded:{l:'Antwort',c:'#10b981',icon:'reply'}, meeting_booked:{l:'Termin gebucht',c:'#10b981',icon:'event_available'},
    quote_sent:{l:'Angebot gesendet',c:'#8b5cf6',icon:'receipt_long'}, nurture:{l:'Nurture',c:'#f59e0b',icon:'water_drop'},
    opt_out:{l:'Opt-Out',c:'#ef4444',icon:'person_off'}, suppressed:{l:'Unterdrückt',c:'#64748b',icon:'visibility_off'},
  };

  const OutboundPipelineView = () => {
    const op = outboundPipeline;

    // Lead Detail View
    if (outboundDetail && selectedOutboundLead) {
      const ld = outboundDetail;
      const st = OB_STATUS_MAP[ld.status] || OB_STATUS_MAP.discovered;
      return (
        <div data-testid="outbound-detail">
          <button className="adm-back-btn" onClick={() => { setSelectedOutboundLead(null); setOutboundDetail(null); setShowOutreachForm(false); }} data-testid="outbound-back-btn"><I n="arrow_back" /> Alle Outbound-Leads</button>
          <div style={{display:'flex',gap:16,alignItems:'center',marginBottom:16,flexWrap:'wrap'}}>
            <h2 style={{margin:0,fontSize:'1.25rem'}}>{ld.company_name || 'Unbekannt'}</h2>
            <span className="adm-badge" style={{background:st.c+'22',color:st.c}}><I n={st.icon} /> {st.l}</span>
            <span className="adm-badge" style={{background:'rgba(255,107,0,0.12)',color:'#FF6B00'}}>Score: {ld.score || 0}</span>
          </div>
          {/* Meta */}
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))',gap:8,marginBottom:20}}>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Kontakt</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{ld.contact_name || '-'}</div><div style={{fontSize:'.6875rem',color:'#6b7b8d'}}>{ld.contact_email}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Telefon</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{ld.contact_phone || '-'}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Website</div><div style={{color:'#3b82f6',fontSize:'.8125rem'}}>{ld.website ? <a href={ld.website.startsWith('http')?ld.website:`https://${ld.website}`} target="_blank" rel="noreferrer" style={{color:'#3b82f6'}}>{ld.website}</a> : '-'}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Branche</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{ld.industry || '-'}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Land</div><div style={{color:'#fff',fontSize:'.8125rem',fontWeight:600}}>{ld.country || 'DE'}</div></div>
            <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Legal</div><div style={{color:ld.legal_status==='approved'?'#10b981':ld.legal_status==='blocked'?'#ef4444':'#f59e0b',fontSize:'.8125rem',fontWeight:600}}>{ld.legal_status || 'Ausstehend'}</div></div>
          </div>
          {/* Fit-Products */}
          {(ld.fit_products || []).length > 0 && (
            <div className="adm-wa-card" style={{marginBottom:16}}>
              <h3 style={{margin:'0 0 10px',fontSize:'.9375rem'}}>Produkt-Fit</h3>
              <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
                {ld.fit_products.map((fp, i) => (
                  <div key={i} className="adm-badge" style={{background:'rgba(16,185,129,0.12)',color:'#10b981',padding:'6px 12px',fontSize:'.75rem'}}>{fp.name} — Score: {fp.score}</div>
                ))}
              </div>
            </div>
          )}
          {/* Analysis */}
          {ld.analysis && Object.keys(ld.analysis).length > 0 && (
            <div className="adm-wa-card" style={{marginBottom:16}}>
              <h3 style={{margin:'0 0 10px',fontSize:'.9375rem'}}>Analyse</h3>
              <pre style={{background:'rgba(12,17,23,0.8)',padding:12,borderRadius:6,fontSize:'.75rem',color:'#c8d1dc',overflow:'auto',maxHeight:200,whiteSpace:'pre-wrap'}}>{JSON.stringify(ld.analysis, null, 2)}</pre>
            </div>
          )}
          {ld.notes && (
            <div className="adm-wa-card" style={{marginBottom:16}}>
              <h3 style={{margin:'0 0 8px',fontSize:'.9375rem'}}>Notizen</h3>
              <p style={{margin:0,fontSize:'.8125rem',color:'#c8d1dc',whiteSpace:'pre-wrap'}}>{ld.notes}</p>
            </div>
          )}
          {/* Pipeline Actions */}
          <div className="adm-wa-card" style={{marginBottom:16}}>
            <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Pipeline-Aktionen</h3>
            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              {ld.status === 'discovered' && <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 16px'}} onClick={() => outboundAction(ld.outbound_lead_id, 'prequalify')} disabled={!!outboundBusy} data-testid="ob-prequalify"><I n="fact_check" /> Vorqualifizieren</button>}
              {['discovered','qualified'].includes(ld.status) && <button className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'8px 16px'}} onClick={() => outboundAction(ld.outbound_lead_id, 'analyze')} disabled={!!outboundBusy} data-testid="ob-analyze"><I n="analytics" /> Analysieren & Scoren</button>}
              {['qualified'].includes(ld.status) && ld.legal_status !== 'approved' && <button className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'8px 16px'}} onClick={() => outboundAction(ld.outbound_lead_id, 'legal-check')} disabled={!!outboundBusy} data-testid="ob-legal"><I n="shield" /> Legal-Check</button>}
              {ld.status === 'outreach_ready' && <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 16px'}} onClick={() => setShowOutreachForm(true)} disabled={!!outboundBusy} data-testid="ob-outreach"><I n="send" /> Outreach erstellen</button>}
              {['contacted','followup_1','followup_2'].includes(ld.status) && <button className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'8px 16px'}} onClick={() => outboundAction(ld.outbound_lead_id, 'followup', { days_delay: 3 })} disabled={!!outboundBusy} data-testid="ob-followup"><I n="replay" /> Follow-up (3 Tage)</button>}
              {['contacted','followup_1','followup_2','followup_3'].includes(ld.status) && (
                <>
                  <button className="adm-btn" style={{width:'auto',padding:'8px 16px',background:'rgba(16,185,129,0.12)',color:'#10b981',border:'1px solid rgba(16,185,129,0.2)'}} onClick={() => outboundAction(ld.outbound_lead_id, 'respond', { response_type: 'positive', content: 'Positive Rückmeldung' })} disabled={!!outboundBusy} data-testid="ob-respond-pos"><I n="thumb_up" /> Positive Antwort</button>
                  <button className="adm-btn" style={{width:'auto',padding:'8px 16px',background:'rgba(239,68,68,0.08)',color:'#ef4444',border:'1px solid rgba(239,68,68,0.2)'}} onClick={() => outboundAction(ld.outbound_lead_id, 'respond', { response_type: 'negative' })} disabled={!!outboundBusy} data-testid="ob-respond-neg"><I n="thumb_down" /> Negative Antwort</button>
                </>
              )}
              {['responded','meeting_booked'].includes(ld.status) && (
                <>
                  <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 16px'}} onClick={() => outboundAction(ld.outbound_lead_id, 'handover', { handover_type: 'quote' })} disabled={!!outboundBusy} data-testid="ob-handover-quote"><I n="receipt_long" /> Handover: Angebot</button>
                  <button className="adm-btn adm-btn-secondary" style={{width:'auto',padding:'8px 16px'}} onClick={() => outboundAction(ld.outbound_lead_id, 'handover', { handover_type: 'meeting' })} disabled={!!outboundBusy} data-testid="ob-handover-meeting"><I n="event" /> Handover: Termin</button>
                </>
              )}
            </div>
            {outboundBusy && <div style={{marginTop:8,fontSize:'.75rem',color:'#FF6B00'}}>Aktion wird ausgeführt...</div>}
          </div>
          {/* Outreach Form */}
          {showOutreachForm && (
            <div className="adm-form-card" style={{marginBottom:16}} data-testid="outreach-form">
              <h3>Outreach erstellen</h3>
              <div className="adm-form-grid">
                <div className="adm-field"><label>Kanal</label><select className="adm-select" value={outreachForm.channel} onChange={e => setOutreachForm({...outreachForm, channel: e.target.value})}><option value="email">E-Mail</option><option value="phone">Telefon</option><option value="linkedin">LinkedIn</option></select></div>
                <div className="adm-field"><label>Betreff</label><input value={outreachForm.subject} onChange={e => setOutreachForm({...outreachForm, subject: e.target.value})} placeholder="Betreffzeile..." data-testid="outreach-subject" /></div>
                <div className="adm-field" style={{gridColumn:'1/-1'}}><label>Nachricht</label><textarea value={outreachForm.content} onChange={e => setOutreachForm({...outreachForm, content: e.target.value})} rows={6} placeholder="Personalisierte Erstansprache..." style={{width:'100%',resize:'vertical',background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',padding:12,fontSize:'.8125rem',borderRadius:6}} data-testid="outreach-content" /></div>
              </div>
              <div style={{display:'flex',gap:8,marginTop:12}}>
                <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} disabled={!outreachForm.subject.trim()||!outreachForm.content.trim()} onClick={async () => {
                  const d = await outboundAction(ld.outbound_lead_id, 'outreach', outreachForm);
                  if (d?.outreach_id) { setShowOutreachForm(false); setOutreachForm({ channel:'email', subject:'', content:'' }); }
                }} data-testid="outreach-save"><I n="check" /> Erstellen</button>
                <button className="adm-btn adm-btn-secondary" onClick={() => setShowOutreachForm(false)}>Abbrechen</button>
              </div>
            </div>
          )}
          {/* Outreach History */}
          {(ld.outreach_history || []).length > 0 && (
            <div className="adm-wa-card" style={{marginBottom:16}}>
              <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Outreach-Verlauf ({ld.outreach_history.length})</h3>
              {ld.outreach_history.map((oh, i) => (
                <div key={oh.outreach_id || i} style={{marginBottom:10,padding:'10px 14px',background:'rgba(255,255,255,0.02)',borderRadius:6,borderLeft:`3px solid ${oh.status==='sent'?'#10b981':oh.status==='draft'?'#f59e0b':'#6b7b8d'}`}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:6}}>
                    <div style={{display:'flex',gap:8,alignItems:'center'}}>
                      <span className="adm-badge" style={{background:oh.status==='sent'?'#10b98122':'#f59e0b22',color:oh.status==='sent'?'#10b981':'#f59e0b',fontSize:'.625rem'}}>{oh.status}</span>
                      <span style={{fontSize:'.75rem',color:'#6b7b8d'}}>{oh.channel} | {fmtTime(oh.created_at)}</span>
                    </div>
                    {oh.status === 'draft' && <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'4px 12px',fontSize:'.6875rem'}} onClick={() => outboundAction(ld.outbound_lead_id, 'send-outreach', { outreach_id: oh.outreach_id })} disabled={!!outboundBusy} data-testid={`send-outreach-${oh.outreach_id}`}><I n="send" /> Jetzt senden</button>}
                  </div>
                  {oh.subject && <div style={{fontSize:'.8125rem',color:'#fff',fontWeight:600,marginBottom:4}}>{oh.subject}</div>}
                  {oh.content && <div style={{fontSize:'.75rem',color:'#c8d1dc',whiteSpace:'pre-wrap'}}>{oh.content.slice(0, 200)}{oh.content.length > 200 ? '...' : ''}</div>}
                  {oh.sent_at && <div style={{fontSize:'.6875rem',color:'#6b7b8d',marginTop:4}}>Gesendet: {fmtTime(oh.sent_at)}</div>}
                </div>
              ))}
            </div>
          )}
          {/* Legal Issues */}
          {(ld.legal_issues || []).length > 0 && (
            <div className="adm-wa-card" style={{marginBottom:16,borderLeft:'3px solid #ef4444'}}>
              <h3 style={{margin:'0 0 10px',fontSize:'.9375rem',color:'#ef4444'}}>Legal-Probleme</h3>
              {ld.legal_issues.map((issue, i) => (
                <div key={i} style={{fontSize:'.8125rem',color:'#c8d1dc',padding:'4px 0',borderBottom:'1px solid rgba(255,255,255,0.03)'}}><I n="warning" /> {issue}</div>
              ))}
            </div>
          )}
          {/* Timeline */}
          {(ld.timeline || []).length > 0 && (
            <div className="adm-wa-card">
              <h3 style={{margin:'0 0 12px',fontSize:'.9375rem'}}>Aktivitätsverlauf</h3>
              {ld.timeline.map((t, i) => (
                <div key={t.event_id || i} style={{display:'flex',gap:12,padding:'6px 0',borderBottom:'1px solid rgba(255,255,255,0.03)',fontSize:'.75rem'}}>
                  <span style={{color:'#6b7b8d',whiteSpace:'nowrap'}}>{fmtTime(t.timestamp || t.created_at)}</span>
                  <span style={{color:'#c8d1dc'}}>{t.event}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    // Pipeline Overview + Lead List
    return (
      <div data-testid="admin-outbound">
        <div className="adm-section-header">
          <h2>Outbound Lead Machine</h2>
          <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => setShowDiscoverForm(true)} data-testid="discover-lead-btn"><I n="person_add" /> Lead erfassen</button>
        </div>
        {/* Pipeline Stats */}
        {op && (
          <div style={{marginBottom:24}}>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:8,marginBottom:16}}>
              <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Gesamt</div><div style={{fontSize:'1.25rem',fontWeight:700,color:'#fff'}}>{op.total || 0}</div></div>
              <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Konversionsrate</div><div style={{fontSize:'1.25rem',fontWeight:700,color:'#FF6B00'}}>{(op.conversion_rate || 0).toFixed(1)}%</div></div>
              <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Qualifiziert</div><div style={{fontSize:'1.25rem',fontWeight:700,color:'#10b981'}}>{(op.pipeline||[]).find(s=>s.key==='qualified')?.count||0}</div></div>
              <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Kontaktiert</div><div style={{fontSize:'1.25rem',fontWeight:700,color:'#06b6d4'}}>{(op.pipeline||[]).find(s=>s.key==='contacted')?.count||0}</div></div>
              <div className="adm-stat-card" style={{padding:'12px 16px'}}><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Termine</div><div style={{fontSize:'1.25rem',fontWeight:700,color:'#10b981'}}>{(op.pipeline||[]).find(s=>s.key==='meeting_booked')?.count||0}</div></div>
            </div>
            {/* Mini Pipeline Bar */}
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(100px,1fr))',gap:4}}>
              {(op.pipeline||[]).filter(s=>s.count>0).map(s => {
                const sm = OB_STATUS_MAP[s.key] || {l:s.label,c:'#6b7b8d'};
                return <div key={s.key} style={{background:sm.c+'15',border:`1px solid ${sm.c}33`,borderRadius:6,padding:'6px 10px',textAlign:'center',cursor:'pointer'}} onClick={() => { setOutboundFilter(s.key); loadOutboundLeads(s.key); }}>
                  <div style={{fontSize:'.6875rem',color:sm.c,fontWeight:600}}>{sm.l}</div>
                  <div style={{fontSize:'1rem',fontWeight:700,color:'#fff'}}>{s.count}</div>
                </div>;
              })}
            </div>
          </div>
        )}
        {/* Discover Form */}
        {showDiscoverForm && (
          <div className="adm-form-card" style={{marginBottom:20}} data-testid="discover-form">
            <h3>Neuen Lead erfassen</h3>
            <div className="adm-form-grid">
              <div className="adm-field"><label>Firmenname *</label><input value={discoverForm.name} onChange={e => setDiscoverForm({...discoverForm, name: e.target.value})} placeholder="Firma GmbH" data-testid="discover-name" /></div>
              <div className="adm-field"><label>Website</label><input value={discoverForm.website} onChange={e => setDiscoverForm({...discoverForm, website: e.target.value})} placeholder="https://firma.de" data-testid="discover-website" /></div>
              <div className="adm-field"><label>Branche</label><input value={discoverForm.industry} onChange={e => setDiscoverForm({...discoverForm, industry: e.target.value})} placeholder="z.B. Handwerk, SaaS, Beratung" data-testid="discover-industry" /></div>
              <div className="adm-field"><label>Kontakt E-Mail</label><input type="email" value={discoverForm.email} onChange={e => setDiscoverForm({...discoverForm, email: e.target.value})} placeholder="kontakt@firma.de" data-testid="discover-email" /></div>
              <div className="adm-field"><label>Kontaktperson</label><input value={discoverForm.contact_name} onChange={e => setDiscoverForm({...discoverForm, contact_name: e.target.value})} placeholder="Max Mustermann" /></div>
              <div className="adm-field"><label>Telefon</label><input value={discoverForm.phone} onChange={e => setDiscoverForm({...discoverForm, phone: e.target.value})} placeholder="+49..." /></div>
              <div className="adm-field"><label>Land</label><select className="adm-select" value={discoverForm.country} onChange={e => setDiscoverForm({...discoverForm, country: e.target.value})}><option value="DE">Deutschland</option><option value="AT">Österreich</option><option value="CH">Schweiz</option><option value="NL">Niederlande</option><option value="BE">Belgien</option></select></div>
              <div className="adm-field" style={{gridColumn:'1/-1'}}><label>Notizen / Pain Signals</label><textarea value={discoverForm.notes} onChange={e => setDiscoverForm({...discoverForm, notes: e.target.value})} rows={3} placeholder="z.B. keine website, veraltete Prozesse, sucht KI-Lösung..." style={{width:'100%',resize:'vertical',background:'rgba(19,26,34,0.6)',border:'1px solid rgba(255,255,255,0.06)',color:'#fff',padding:12,fontSize:'.8125rem',borderRadius:6}} data-testid="discover-notes" /></div>
            </div>
            <div className="adm-form-actions">
              <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={discoverLead} disabled={!discoverForm.name.trim()||outboundBusy==='discover'} data-testid="discover-save"><I n="check" /> Erfassen</button>
              <button className="adm-btn adm-btn-secondary" onClick={() => setShowDiscoverForm(false)}>Abbrechen</button>
            </div>
          </div>
        )}
        {/* Filter */}
        <div style={{display:'flex',gap:8,marginBottom:16,alignItems:'center',flexWrap:'wrap'}}>
          <span style={{fontSize:'.8125rem',color:'#6b7b8d'}}>Filter:</span>
          {[{k:'all',l:'Alle'},{k:'discovered',l:'Entdeckt'},{k:'qualified',l:'Qualifiziert'},{k:'outreach_ready',l:'Outreach'},{k:'contacted',l:'Kontaktiert'},{k:'responded',l:'Antwort'},{k:'meeting_booked',l:'Termin'}].map(f => (
            <button key={f.k} className={`adm-btn ${outboundFilter===f.k?'adm-btn-primary':'adm-btn-secondary'}`} style={{width:'auto',padding:'5px 12px',fontSize:'.75rem'}} onClick={() => { setOutboundFilter(f.k); loadOutboundLeads(f.k); }} data-testid={`ob-filter-${f.k}`}>{f.l}</button>
          ))}
        </div>
        {/* Lead Table */}
        <div className="adm-table-wrap">
          <table className="adm-table" data-testid="outbound-leads-table">
            <thead><tr><th>Firma</th><th>Kontakt</th><th>Branche</th><th>Score</th><th>Status</th><th>Legal</th><th>Aktualisiert</th><th></th></tr></thead>
            <tbody>
              {outboundLeadsLoading ? (
                <tr><td colSpan="8" style={{textAlign:'center',padding:32,color:'#6b7b8d'}}>Lade...</td></tr>
              ) : outboundLeads.length === 0 ? (
                <tr><td colSpan="8" style={{textAlign:'center',padding:32,color:'#4a5568'}}>Keine Outbound-Leads{outboundFilter!=='all'?` mit Status "${(OB_STATUS_MAP[outboundFilter]||{}).l||outboundFilter}"`:''}</td></tr>
              ) : outboundLeads.map(lead => {
                const ls = OB_STATUS_MAP[lead.status] || OB_STATUS_MAP.discovered;
                return (
                  <tr key={lead.outbound_lead_id} className="adm-row-click" onClick={() => loadOutboundDetail(lead.outbound_lead_id)} data-testid={`ob-row-${lead.outbound_lead_id}`}>
                    <td style={{fontWeight:600,color:'#fff'}}>{lead.company_name}</td>
                    <td><div>{lead.contact_name || '-'}</div><div style={{fontSize:'.6875rem',color:'#6b7b8d'}}>{lead.contact_email}</div></td>
                    <td>{lead.industry || '-'}</td>
                    <td><span style={{color:lead.score>=60?'#10b981':lead.score>=30?'#f59e0b':'#6b7b8d',fontWeight:600}}>{lead.score || 0}</span></td>
                    <td><span className="adm-badge" style={{background:ls.c+'22',color:ls.c}}>{ls.l}</span></td>
                    <td><span style={{color:lead.legal_status==='approved'?'#10b981':lead.legal_status==='blocked'?'#ef4444':'#6b7b8d',fontSize:'.75rem'}}>{lead.legal_status==='approved'?'OK':lead.legal_status==='blocked'?'Blockiert':'–'}</span></td>
                    <td style={{fontSize:'.75rem',color:'#6b7b8d'}}>{fmtDate(lead.updated_at)}</td>
                    <td><button className="adm-btn-sm"><I n="visibility" /></button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  /* ══════════ LEGAL & COMPLIANCE VIEW (P5) ══════════ */
  const LegalView = () => {
    const cs = complianceSummary;
    return (
      <div data-testid="admin-legal">
        <h2>Legal & Compliance Guardian</h2>
        {cs && (
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))',gap:12,marginBottom:24}}>
            <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Offene Risiken</div><div style={{fontSize:'1.5rem',fontWeight:700,color:cs.risks?.open>0?'#ef4444':'#10b981'}}>{cs.risks?.open || 0}</div></div>
            <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Gelöste Risiken</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#10b981'}}>{cs.risks?.resolved || 0}</div></div>
            <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Audit-Einträge</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#fff'}}>{cs.audits?.total || 0}</div></div>
            <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Opt-Outs</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#f59e0b'}}>{cs.opt_outs || 0}</div></div>
            <div className="adm-stat-card"><div style={{fontSize:'.6875rem',color:'#6b7b8d',textTransform:'uppercase'}}>Suppressions</div><div style={{fontSize:'1.5rem',fontWeight:700,color:'#6b7b8d'}}>{cs.suppressions || 0}</div></div>
          </div>
        )}
        {/* Open Risks */}
        {legalRisks.length > 0 && (
          <div style={{marginBottom:24}}>
            <h3 style={{fontSize:'.9375rem',marginBottom:12}}>Offene Risiken</h3>
            {legalRisks.map(r => (
              <div key={r.risk_id} className="adm-wa-card" style={{marginBottom:8,borderLeft:`3px solid ${r.level==='critical'?'#dc2626':r.level==='high'?'#ef4444':r.level==='medium'?'#f97316':'#f59e0b'}`}}>
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                  <span style={{fontWeight:600,color:'#fff',fontSize:'.8125rem'}}>{r.entity_type} — {r.entity_id?.slice(0,20)}</span>
                  <span className="adm-badge" style={{background:r.level==='critical'?'#dc262622':'#ef444422',color:r.level==='critical'?'#dc2626':'#ef4444',textTransform:'uppercase'}}>{r.level}</span>
                </div>
                <p style={{margin:'6px 0 0',fontSize:'.75rem',color:'#c8d1dc'}}>{r.description}</p>
                {r.mitigation && <p style={{margin:'4px 0 0',fontSize:'.6875rem',color:'#6b7b8d'}}>Mitigierung: {r.mitigation}</p>}
              </div>
            ))}
          </div>
        )}
        {/* Recent Gate Decisions */}
        {cs?.recent_gates?.length > 0 && (
          <div style={{marginBottom:24}}>
            <h3 style={{fontSize:'.9375rem',marginBottom:12}}>Letzte Gate-Blockierungen</h3>
            {cs.recent_gates.map((g, i) => (
              <div key={i} className="adm-wa-card" style={{marginBottom:8,borderLeft:'3px solid #ef4444'}}>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:'.75rem'}}>
                  <span style={{color:'#ef4444',fontWeight:600}}>{g.type}</span>
                  <span style={{color:'#6b7b8d'}}>{fmtTime(g.timestamp)}</span>
                </div>
                <div style={{fontSize:'.75rem',color:'#c8d1dc',marginTop:4}}>{(g.gate_reasons || []).join(', ')}</div>
              </div>
            ))}
          </div>
        )}
        {/* Audit Log */}
        {legalAudit.length > 0 && (
          <div>
            <h3 style={{fontSize:'.9375rem',marginBottom:12}}>Audit-Log (letzte 20)</h3>
            <div className="adm-table-wrap">
              <table className="adm-table">
                <thead><tr><th>Typ</th><th>Risiko</th><th>Gate</th><th>Zeitpunkt</th></tr></thead>
                <tbody>
                  {legalAudit.map((a, i) => (
                    <tr key={i}>
                      <td>{a.type}</td>
                      <td><span className="adm-badge" style={{background:a.risk_level==='none'?'#10b98122':a.risk_level==='critical'?'#dc262622':'#f59e0b22',color:a.risk_level==='none'?'#10b981':a.risk_level==='critical'?'#dc2626':'#f59e0b'}}>{a.risk_level}</span></td>
                      <td>{a.approved ? <span style={{color:'#10b981'}}>Freigegeben</span> : <span style={{color:'#ef4444'}}>Blockiert</span>}</td>
                      <td>{fmtTime(a.timestamp)}</td>
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

  /* ══════════ MONITORING VIEW (P7) ══════════ */
  const loadMonitoring = async () => {
    setMonitorLoading(true);
    const d = await apiFetch('/api/admin/monitoring/status');
    if (d) setMonitorData(d);
    setMonitorLoading(false);
  };

  /* ══════════ ADMIN USERS GOVERNANCE (BLOCK D) ══════════ */
  const loadAdminUsers = useCallback(async () => {
    setAdminUsersLoading(true);
    const d = await apiFetch('/api/admin/users');
    if (d) setAdminUsers(d.users || []);
    setAdminUsersLoading(false);
  }, [apiFetch]);

  const loadWebhookEvents = useCallback(async () => {
    setWebhooksLoading(true);
    const d = await apiFetch('/api/admin/webhooks/events?limit=50');
    if (d) setWebhookEvents(d.events || []);
    setWebhooksLoading(false);
  }, [apiFetch]);

  useEffect(() => {
    if (!token || view !== 'users') return;
    loadAdminUsers();
  }, [token, view, loadAdminUsers]);

  useEffect(() => {
    if (!token || view !== 'webhooks') return;
    loadWebhookEvents();
  }, [token, view, loadWebhookEvents]);

  const createAdminUser = async () => {
    if (!newUserForm.email || !newUserForm.password) return;
    const d = await apiFetch('/api/admin/users', { method: 'POST', body: JSON.stringify(newUserForm) });
    if (d && !d.error) {
      setShowCreateUser(false);
      setNewUserForm({ email: '', password: '', role: 'admin' });
      loadAdminUsers();
    }
  };

  const deleteAdminUser = async (email) => {
    if (!window.confirm(`Admin-Benutzer "${email}" wirklich löschen?`)) return;
    const d = await apiFetch(`/api/admin/users/${email}`, { method: 'DELETE' });
    if (d && !d.error) loadAdminUsers();
  };

  /* ══════ API Keys ══════ */
  const loadApiKeys = useCallback(async () => {
    setApiKeysLoading(true);
    const d = await apiFetch('/api/admin/api-keys');
    if (d?.keys) setApiKeys(d.keys);
    setApiKeysLoading(false);
  }, []);

  const createApiKey = async () => {
    const body = { name: newApiKeyForm.name, scopes: newApiKeyForm.scopes === 'all' ? ['all'] : newApiKeyForm.scopes.split(',').map(s => s.trim()), rate_limit_per_hour: parseInt(newApiKeyForm.rate_limit_per_hour) || 1000, description: newApiKeyForm.description };
    if (newApiKeyForm.expires_in_days) body.expires_in_days = parseInt(newApiKeyForm.expires_in_days);
    const d = await apiFetch('/api/admin/api-keys', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (d?.api_key) { setNewApiKeyResult(d); loadApiKeys(); }
  };

  const toggleApiKey = async (keyId, isActive) => {
    await apiFetch(`/api/admin/api-keys/${keyId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: !isActive }) });
    loadApiKeys();
  };

  const deleteApiKey = async (keyId) => {
    if (!window.confirm('API-Key permanent löschen? Alle externen Integrationen mit diesem Key werden sofort unterbrochen.')) return;
    await apiFetch(`/api/admin/api-keys/${keyId}`, { method: 'DELETE' });
    loadApiKeys();
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const UsersView = () => (
    <div data-testid="admin-users">
      <div className="adm-section-header">
        <h2>Benutzerverwaltung</h2>
        <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => setShowCreateUser(true)} data-testid="create-user-btn"><I n="person_add" /> Neuer Admin</button>
      </div>
      {showCreateUser && (
        <div className="adm-form-card" style={{marginBottom:20}} data-testid="create-user-form">
          <h3>Neuen Admin-Benutzer anlegen</h3>
          <div className="adm-form-grid">
            <div className="adm-field"><label>E-Mail *</label><input type="email" value={newUserForm.email} onChange={e => setNewUserForm({...newUserForm, email: e.target.value})} placeholder="admin@nexify.ai" data-testid="new-user-email" /></div>
            <div className="adm-field"><label>Passwort *</label><input type="password" value={newUserForm.password} onChange={e => setNewUserForm({...newUserForm, password: e.target.value})} placeholder="Min. 8 Zeichen" data-testid="new-user-password" /></div>
            <div className="adm-field"><label>Rolle</label><select className="adm-select" value={newUserForm.role} onChange={e => setNewUserForm({...newUserForm, role: e.target.value})}><option value="admin">Administrator</option><option value="staff">Staff</option><option value="readonly">Nur Lesen</option></select></div>
          </div>
          <div className="adm-form-actions">
            <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={createAdminUser} disabled={!newUserForm.email||!newUserForm.password} data-testid="save-user-btn"><I n="check" /> Anlegen</button>
            <button className="adm-btn adm-btn-secondary" onClick={() => setShowCreateUser(false)}>Abbrechen</button>
          </div>
        </div>
      )}
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="admin-users-table">
          <thead><tr><th>E-Mail</th><th>Rolle</th><th>Erstellt</th><th>Erstellt von</th><th></th></tr></thead>
          <tbody>
            {adminUsersLoading ? (
              <tr><td colSpan="5" style={{textAlign:'center',padding:32,color:'#6b7b8d'}}>Lade...</td></tr>
            ) : adminUsers.length === 0 ? (
              <tr><td colSpan="5" style={{textAlign:'center',padding:32,color:'#4a5568'}}>Keine Admin-Benutzer</td></tr>
            ) : adminUsers.map(u => (
              <tr key={u.email} data-testid={`user-row-${u.email}`}>
                <td style={{fontWeight:600,color:'#fff'}}>{u.email}</td>
                <td><span className="adm-badge" style={{background:u.role==='admin'?'#FF6B0022':'#3b82f622',color:u.role==='admin'?'#FF6B00':'#3b82f6'}}>{u.role || 'admin'}</span></td>
                <td style={{fontSize:'.75rem',color:'#6b7b8d'}}>{fmtDate(u.created_at)}</td>
                <td style={{fontSize:'.75rem',color:'#6b7b8d'}}>{u.created_by || 'system'}</td>
                <td>
                  <button className="adm-btn-sm" style={{color:'#ef4444'}} onClick={() => deleteAdminUser(u.email)} data-testid={`delete-user-${u.email}`}><I n="delete" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const WebhookEventsView = () => (
    <div data-testid="admin-webhooks">
      <div className="adm-section-header">
        <h2>Webhook Event Store</h2>
        <button className="adm-btn adm-btn-secondary" style={{padding:'8px 16px',width:'auto'}} onClick={loadWebhookEvents} data-testid="refresh-webhooks"><I n="refresh" /> Aktualisieren</button>
      </div>
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="webhook-events-table">
          <thead><tr><th>Zeitpunkt</th><th>Typ</th><th>Source</th><th>Status</th><th>Details</th></tr></thead>
          <tbody>
            {webhooksLoading ? (
              <tr><td colSpan="5" style={{textAlign:'center',padding:32,color:'#6b7b8d'}}>Lade...</td></tr>
            ) : webhookEvents.length === 0 ? (
              <tr><td colSpan="5" style={{textAlign:'center',padding:32,color:'#4a5568'}}>Keine Webhook-Events vorhanden</td></tr>
            ) : webhookEvents.map((evt, i) => (
              <tr key={evt.event_id || i}>
                <td style={{fontSize:'.75rem',color:'#6b7b8d',whiteSpace:'nowrap'}}>{fmtTime(evt.timestamp)}</td>
                <td><span className="adm-badge" style={{background:'#3b82f622',color:'#3b82f6'}}>{evt.event_type || '-'}</span></td>
                <td style={{fontSize:'.75rem'}}>{evt.source || '-'}</td>
                <td><span className="adm-badge" style={{background:evt.status==='processed'?'#10b98122':evt.status==='failed'?'#ef444422':'#f59e0b22',color:evt.status==='processed'?'#10b981':evt.status==='failed'?'#ef4444':'#f59e0b'}}>{evt.status || 'pending'}</span></td>
                <td style={{fontSize:'.6875rem',color:'#6b7b8d',maxWidth:200,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{JSON.stringify(evt.payload || {}).slice(0,80)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const MonitoringView = () => {
    if (monitorLoading) return <div className="adm-loading"><I n="sync" /> Lade Systemstatus...</div>;
    if (!monitorData) return <div className="adm-empty"><I n="monitor_heart" /><p>Systemstatus konnte nicht geladen werden.</p><button className="adm-btn adm-btn-primary" onClick={loadMonitoring}>Erneut laden</button></div>;
    const sys = monitorData.systems || {};
    const StatusDot = ({ s }) => <span style={{width:8,height:8,borderRadius:'50%',display:'inline-block',background:s==='ok'||s==='operational'||s==='configured'||s==='healthy'?'#10b981':s==='not_configured'?'#f59e0b':s==='attention'||s==='degraded'?'#f97316':'#ef4444',marginRight:8,flexShrink:0}} />;
    const Card = ({ icon, title, status, children }) => (
      <div className="adm-wa-card" style={{padding:'16px 18px'}} data-testid={`monitor-${title.toLowerCase().replace(/\s/g,'-')}`}>
        <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:10}}>
          <StatusDot s={status} />
          <I n={icon} style={{fontSize:18,color:'#FF6B00'}} />
          <span style={{fontWeight:600,color:'#fff',fontSize:'.875rem'}}>{title}</span>
          <span className="adm-badge" style={{marginLeft:'auto',background:status==='ok'||status==='configured'||status==='healthy'?'#10b98122':'#f59e0b22',color:status==='ok'||status==='configured'||status==='healthy'?'#10b981':'#f59e0b',fontSize:'.625rem'}}>{status}</span>
        </div>
        <div style={{fontSize:'.75rem',color:'#6b7b8d',display:'flex',flexDirection:'column',gap:4}}>{children}</div>
      </div>
    );
    return (
      <div data-testid="admin-monitoring">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20}}>
          <h2>System Monitoring</h2>
          <button className="adm-btn" style={{padding:'6px 14px',width:'auto'}} onClick={loadMonitoring} data-testid="monitor-refresh"><I n="refresh" /> Aktualisieren</button>
        </div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(300px,1fr))',gap:12}}>
          <Card icon="api" title="API" status={sys.api?.status}><span>Version: {sys.api?.version}</span></Card>
          <Card icon="database" title="Datenbank" status={sys.database?.status}><span>Collections: {sys.database?.collections}</span></Card>
          <Card icon="memory" title="Worker / Queue" status={sys.workers?.status}><span>Queue aktiv: {sys.workers?.queue_active ? 'Ja' : 'Nein'}</span></Card>
          <Card icon="email" title="E-Mail (Resend)" status={sys.email?.status}>
            <span>Versendet: {sys.email?.total_sent}</span>
            <span>Fehler: {sys.email?.total_failed}</span>
            <span>API-Key: {sys.email?.api_key_set ? 'Gesetzt' : 'Fehlt'}</span>
          </Card>
          <Card icon="smart_toy" title="LLM / DeepSeek" status={sys.llm?.active_provider === 'deepseek' ? 'ok' : 'fallback'}>
            <span>Provider: {sys.llm?.active_provider}</span>
            <span>Ziel-Architektur: {sys.llm?.is_target_architecture ? 'Ja' : 'Nein (Fallback)'}</span>
            <span>DeepSeek Key: {sys.llm?.providers?.deepseek?.api_key_set ? 'Gesetzt' : 'Fehlt'}</span>
            {sys.llm?.metrics && <span>Calls: {sys.llm.metrics.calls} | Errors: {sys.llm.metrics.errors}</span>}
          </Card>
          <Card icon="payment" title="Revolut" status={sys.payments?.revolut?.status}><span>API-Key: {sys.payments?.revolut?.api_key_set ? 'Gesetzt' : 'Fehlt'}</span></Card>
          <Card icon="webhook" title="Webhooks" status="ok">
            <span>Events gesamt: {sys.webhooks?.total_events}</span>
          </Card>
          <Card icon="shield" title="Memory / Audit" status="ok">
            <span>Timeline: {sys.memory_audit?.timeline_events}</span>
            <span>Legal Audits: {sys.memory_audit?.legal_audits}</span>
            <span>Memory: {sys.memory_audit?.memory_entries}</span>
          </Card>
          <Card icon="report_problem" title="Dead Letter Queue" status={sys.dead_letter_queue?.status}>
            <span>Einträge: {sys.dead_letter_queue?.count}</span>
            {sys.dead_letter_queue?.count > 0 && <span style={{color:'#f97316'}}>Manuelle Intervention empfohlen — Dead-letter-Jobs prüfen</span>}
          </Card>
          <Card icon="cloud_upload" title="Object Storage" status={sys.object_storage?.status}>
            <span>Initialisiert: {sys.object_storage?.initialized ? 'Ja' : 'Nein'}</span>
          </Card>
          <Card icon="folder" title="Dokumente" status="ok">
            <span>Gesamt: {sys.documents?.total}</span>
            <span>Object Storage: {sys.documents?.in_storage}</span>
            <span>MongoDB: {sys.documents?.in_mongodb}</span>
          </Card>
        </div>
        <p style={{marginTop:16,fontSize:'.6875rem',color:'#6b7b8d'}}>Stand: {fmtTime(monitorData.timestamp)}</p>

        {/* Recovery / Self-Healing Status */}
        <div style={{marginTop:24}} data-testid="monitor-recovery">
          <h3 style={{marginBottom:12}}>Recovery & Self-Healing</h3>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(300px,1fr))',gap:12}}>
            {[
              { label: 'LLM Fallback', status: sys.llm?.active_provider === 'deepseek' ? 'DeepSeek primär' : 'Fallback aktiv (Emergent GPT)', ok: sys.llm?.active_provider === 'deepseek', action: sys.llm?.active_provider !== 'deepseek' ? 'DEEPSEEK_API_KEY setzen für Zielarchitektur' : null },
              { label: 'Dead Letter Queue', status: sys.dead_letter_queue?.count === 0 ? 'Leer — kein Handlungsbedarf' : `${sys.dead_letter_queue?.count} Jobs wartend`, ok: sys.dead_letter_queue?.count === 0, action: sys.dead_letter_queue?.count > 0 ? 'Dead-letter-Jobs in Admin prüfen und ggf. neu einreihen' : null },
              { label: 'E-Mail Delivery', status: sys.email?.api_key_set ? `${sys.email?.total_failed} Fehler von ${sys.email?.total_sent + sys.email?.total_failed} gesamt` : 'Nicht konfiguriert', ok: sys.email?.api_key_set && sys.email?.total_failed === 0, action: sys.email?.total_failed > 0 ? 'Fehlgeschlagene E-Mails in Email-Stats prüfen' : null },
              { label: 'Payment Provider', status: sys.payments?.revolut?.api_key_set ? 'Revolut aktiv' : 'Kein Provider', ok: sys.payments?.revolut?.api_key_set },
              { label: 'Object Storage', status: sys.object_storage?.initialized ? 'Initialisiert' : 'Nicht initialisiert — MongoDB-Fallback aktiv', ok: sys.object_storage?.initialized, action: !sys.object_storage?.initialized ? 'Wird bei nächster PDF-Generierung automatisch initialisiert' : null },
            ].map((item, idx) => (
              <div key={idx} className="adm-wa-card" style={{padding:'12px 16px'}}>
                <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
                  <span style={{width:8,height:8,borderRadius:'50%',background:item.ok?'#10b981':'#f59e0b',flexShrink:0}} />
                  <span style={{fontWeight:600,fontSize:'.8125rem',color:'#fff'}}>{item.label}</span>
                </div>
                <p style={{margin:0,fontSize:'.75rem',color:'#c8d1dc'}}>{item.status}</p>
                {item.action && <p style={{margin:'4px 0 0',fontSize:'.6875rem',color:'#f59e0b'}}>→ {item.action}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  /* ══════════ MAIN LAYOUT ══════════ */

  const ApiKeysView = () => (
    <div data-testid="admin-api-keys">
      <div className="adm-section-header">
        <h2>API-Zugang</h2>
        <button className="adm-btn adm-btn-primary" style={{padding:'8px 16px',width:'auto'}} onClick={() => { setShowCreateApiKey(true); setNewApiKeyResult(null); }} data-testid="create-api-key-btn"><I n="vpn_key" /> Neuer API-Key</button>
      </div>
      <div className="adm-form-card" style={{marginBottom:20,borderLeft:'3px solid #FF6B00'}}>
        <div style={{display:'flex',gap:8,alignItems:'flex-start'}}>
          <I n="info" style={{color:'#FF6B00',flexShrink:0}} />
          <div style={{fontSize:'.8125rem',color:'#c8d1dc',lineHeight:1.6}}>
            <strong style={{color:'#fff'}}>Externer API-Zugang</strong><br/>
            Über die API v1 können externe Systeme programmatisch auf NeXifyAI zugreifen.<br/>
            Base URL: <code style={{background:'rgba(255,255,255,0.06)',padding:'2px 6px',borderRadius:3,fontSize:'.75rem',color:'#FF6B00'}}>{API}/api/v1</code><br/>
            Header: <code style={{background:'rgba(255,255,255,0.06)',padding:'2px 6px',borderRadius:3,fontSize:'.75rem',color:'#FF6B00'}}>X-API-Key: nxa_live_...</code><br/>
            <a href={`${API}/api/v1/docs`} target="_blank" rel="noopener noreferrer" style={{color:'#FF6B00',fontWeight:600}}>API-Dokumentation ansehen</a>
          </div>
        </div>
      </div>
      {newApiKeyResult && (
        <div className="adm-form-card" style={{marginBottom:20,borderLeft:'3px solid #10b981',background:'rgba(16,185,129,0.04)'}} data-testid="new-api-key-result">
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:12}}>
            <I n="check_circle" style={{color:'#10b981'}} />
            <strong style={{color:'#10b981',fontSize:'.875rem'}}>API-Key erstellt</strong>
          </div>
          <p style={{color:'#ef4444',fontSize:'.75rem',margin:'0 0 8px',fontWeight:600}}>Dieser Key wird nur einmal angezeigt — jetzt kopieren!</p>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <code style={{flex:1,background:'rgba(0,0,0,0.3)',padding:'10px 14px',borderRadius:4,fontSize:'.8125rem',color:'#fff',wordBreak:'break-all',fontFamily:'monospace'}} data-testid="new-api-key-value">{newApiKeyResult.api_key}</code>
            <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 14px',flexShrink:0}} onClick={() => copyToClipboard(newApiKeyResult.api_key)} data-testid="copy-api-key-btn"><I n={copiedKey ? 'done' : 'content_copy'} /> {copiedKey ? 'Kopiert' : 'Kopieren'}</button>
          </div>
          <div style={{marginTop:12,fontSize:'.75rem',color:'#6b7b8d'}}>
            <span>Name: <strong>{newApiKeyResult.name}</strong></span> &nbsp;|&nbsp;
            <span>Scopes: {newApiKeyResult.scopes?.join(', ')}</span> &nbsp;|&nbsp;
            <span>Rate-Limit: {newApiKeyResult.rate_limit_per_hour}/h</span>
          </div>
          <button className="adm-btn adm-btn-secondary" style={{marginTop:12,width:'auto',padding:'6px 14px'}} onClick={() => setNewApiKeyResult(null)}>Schließen</button>
        </div>
      )}
      {showCreateApiKey && !newApiKeyResult && (
        <div className="adm-form-card" style={{marginBottom:20}} data-testid="create-api-key-form">
          <h3>Neuen API-Key erstellen</h3>
          <div className="adm-form-grid">
            <div className="adm-field"><label>Name *</label><input value={newApiKeyForm.name} onChange={e => setNewApiKeyForm({...newApiKeyForm, name: e.target.value})} placeholder="z.B. Production, Staging, Zapier" data-testid="api-key-name" /></div>
            <div className="adm-field"><label>Berechtigungen (Scopes)</label><select className="adm-select" value={newApiKeyForm.scopes} onChange={e => setNewApiKeyForm({...newApiKeyForm, scopes: e.target.value})} data-testid="api-key-scopes">
              <option value="all">Vollzugriff (all)</option>
              <option value="contacts:read,contacts:write,leads:read,leads:write">Kontakte & Leads</option>
              <option value="quotes:read,contracts:read,invoices:read">Nur Lesen (kommerziell)</option>
              <option value="stats:read">Nur Statistiken</option>
            </select></div>
            <div className="adm-field"><label>Rate-Limit / Stunde</label><input type="number" value={newApiKeyForm.rate_limit_per_hour} onChange={e => setNewApiKeyForm({...newApiKeyForm, rate_limit_per_hour: e.target.value})} data-testid="api-key-rate-limit" /></div>
            <div className="adm-field"><label>Ablauf (Tage, leer = unbegrenzt)</label><input type="number" value={newApiKeyForm.expires_in_days} onChange={e => setNewApiKeyForm({...newApiKeyForm, expires_in_days: e.target.value})} placeholder="Leer für unbegrenzt" data-testid="api-key-expires" /></div>
          </div>
          <div className="adm-field" style={{marginTop:8}}><label>Beschreibung</label><input value={newApiKeyForm.description} onChange={e => setNewApiKeyForm({...newApiKeyForm, description: e.target.value})} placeholder="Wofür wird dieser Key verwendet?" data-testid="api-key-description" /></div>
          <div className="adm-form-actions" style={{marginTop:12}}>
            <button className="adm-btn adm-btn-primary" style={{width:'auto',padding:'8px 20px'}} onClick={createApiKey} disabled={!newApiKeyForm.name.trim()} data-testid="save-api-key-btn"><I n="vpn_key" /> Key erstellen</button>
            <button className="adm-btn adm-btn-secondary" onClick={() => setShowCreateApiKey(false)}>Abbrechen</button>
          </div>
        </div>
      )}
      <div className="adm-table-wrap">
        <table className="adm-table" data-testid="api-keys-table">
          <thead><tr><th>Name</th><th>Key-Prefix</th><th>Scopes</th><th>Rate-Limit</th><th>Anfragen</th><th>Zuletzt genutzt</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {apiKeysLoading ? (
              <tr><td colSpan="8" style={{textAlign:'center',padding:32,color:'#6b7b8d'}}>Lade...</td></tr>
            ) : apiKeys.length === 0 ? (
              <tr><td colSpan="8" style={{textAlign:'center',padding:32,color:'#4a5568'}}>Noch keine API-Keys erstellt</td></tr>
            ) : apiKeys.map(k => (
              <tr key={k.key_id} data-testid={`api-key-row-${k.key_id}`}>
                <td style={{fontWeight:600,color:'#fff'}}>{k.name}{k.description && <div style={{fontSize:'.6875rem',color:'#6b7b8d',fontWeight:400}}>{k.description}</div>}</td>
                <td><code style={{fontSize:'.75rem',color:'#FF6B00',fontFamily:'monospace'}}>{k.key_prefix}</code></td>
                <td style={{fontSize:'.75rem'}}>{k.scopes?.join(', ')}</td>
                <td style={{fontSize:'.75rem'}}>{k.rate_limit_per_hour}/h</td>
                <td style={{fontSize:'.75rem',color:'#FF6B00',fontWeight:600}}>{k.total_requests || 0}</td>
                <td style={{fontSize:'.75rem',color:'#6b7b8d'}}>{k.last_used_at ? fmtTime(k.last_used_at) : 'Nie'}</td>
                <td>
                  <span className="adm-badge" style={{background:k.is_active?'#10b98122':'#ef444422',color:k.is_active?'#10b981':'#ef4444',cursor:'pointer'}} onClick={() => toggleApiKey(k.key_id, k.is_active)} data-testid={`toggle-key-${k.key_id}`}>{k.is_active ? 'Aktiv' : 'Deaktiviert'}</span>
                </td>
                <td><button className="adm-btn-sm" style={{color:'#ef4444'}} onClick={() => deleteApiKey(k.key_id)} data-testid={`delete-key-${k.key_id}`}><I n="delete" /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="adm-form-card" style={{marginTop:20}}>
        <h3 style={{marginBottom:12}}>Schnellstart — cURL Beispiel</h3>
        <code style={{display:'block',background:'rgba(0,0,0,0.3)',padding:'14px 18px',borderRadius:6,fontSize:'.75rem',color:'#c8d1dc',lineHeight:1.8,fontFamily:'monospace',whiteSpace:'pre-wrap',overflowX:'auto'}}>
{`# Statistiken abrufen
curl -H "X-API-Key: nxa_live_..." ${API}/api/v1/stats

# Kontakte auflisten
curl -H "X-API-Key: nxa_live_..." ${API}/api/v1/contacts

# Neuen Lead erstellen
curl -X POST -H "X-API-Key: nxa_live_..." \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@firma.de","vorname":"Max","nachname":"Muster","unternehmen":"Firma GmbH"}' \\
  ${API}/api/v1/leads

# API-Dokumentation
curl ${API}/api/v1/docs`}
        </code>
      </div>
    </div>
  );

  const navItems = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
    { id: 'projects', icon: 'folder_special', label: 'Projekte' },
    { id: 'contracts', icon: 'gavel', label: 'Verträge' },
    { id: 'billing', icon: 'account_balance', label: 'Billing' },
    { id: 'outbound_pipeline', icon: 'rocket_launch', label: 'Outbound' },
    { id: 'legal', icon: 'shield', label: 'Legal' },
    { id: 'commercial', icon: 'receipt_long', label: 'Angebote & Rechnungen' },
    { id: 'leads', icon: 'people', label: 'Leads' },
    { id: 'conversations', icon: 'chat', label: 'Kommunikation' },
    { id: 'chats', icon: 'forum', label: 'KI-Chats' },
    { id: 'whatsapp', icon: 'smartphone', label: 'WhatsApp' },
    { id: 'timeline', icon: 'timeline', label: 'Aktivitäten' },
    { id: 'calendar', icon: 'calendar_month', label: 'Kalender' },
    { id: 'customers', icon: 'person_search', label: 'Kunden' },
    { id: 'agents', icon: 'smart_toy', label: 'KI-Agenten' },
    { id: 'users', icon: 'admin_panel_settings', label: 'Benutzer' },
    { id: 'api_keys', icon: 'vpn_key', label: 'API-Zugang' },
    { id: 'webhooks', icon: 'webhook', label: 'Webhooks' },
    { id: 'audit', icon: 'verified', label: 'Audit' },
    { id: 'monitoring', icon: 'monitor_heart', label: 'Monitoring' },
    { id: 'nexifyai', icon: 'psychology', label: 'NeXifyAI' },
  ];

  return (
    <div className={`adm-layout ${sidebarOpen ? '' : 'adm-collapsed'}`} data-testid="admin-panel">
      <aside className={`adm-sidebar ${sidebarOpen ? '' : 'collapsed'}`} data-testid="admin-sidebar">
        <div className="adm-sidebar-top">
          <div className="adm-sidebar-logo"><img src="/icon-mark.svg" alt="" width="28" height="28" /><span>NeXify<em>AI</em></span></div>
        </div>
        <button className="adm-collapse-btn" onClick={() => setSidebarOpen(!sidebarOpen)} data-testid="sidebar-toggle" title={sidebarOpen ? 'Einklappen' : 'Ausklappen'}>
          <I n={sidebarOpen ? 'chevron_left' : 'chevron_right'} />
        </button>
        <nav className="adm-sidebar-nav">
          {navItems.map(n => (
            <button key={n.id} className={`adm-nav-item ${view === n.id ? 'active' : ''}`} onClick={() => { setView(n.id); setSelectedBooking(null); setCustDetail(null); setSelectedChat(null); setSelectedConvo(null); }} data-testid={`nav-${n.id}`} title={n.label}>
              <I n={n.icon} /><span className="adm-nav-label">{n.label}</span>
            </button>
          ))}
        </nav>
        <button className="adm-logout" onClick={logout} data-testid="admin-logout" title="Abmelden"><I n="logout" /> <span className="adm-nav-label">Abmelden</span></button>
      </aside>
      <main className="adm-main">
        <header className="adm-topbar">
          <h1 className="adm-topbar-title">{navItems.find(n => n.id === view)?.label}</h1>
          <div className="adm-topbar-user"><I n="account_circle" /> Administration</div>
        </header>
        <div className="adm-content">
          {view === 'dashboard' && <DashboardView />}
          {view === 'projects' && <ProjectsView />}
          {view === 'contracts' && <ContractsView />}
          {view === 'billing' && <BillingView />}
          {view === 'outbound_pipeline' && <OutboundPipelineView />}
          {view === 'legal' && <LegalView />}
          {view === 'commercial' && <CommercialView />}
          {view === 'leads' && <LeadsView />}
          {view === 'conversations' && <ConversationsView />}
          {view === 'chats' && <ChatsView />}
          {view === 'whatsapp' && <WhatsAppView />}
          {view === 'timeline' && <TimelineView />}
          {view === 'calendar' && <CalendarView />}
          {view === 'customers' && <CustomersView />}
          {view === 'agents' && <AgentsView />}
          {view === 'users' && <UsersView />}
          {view === 'api_keys' && <ApiKeysView />}
          {view === 'webhooks' && <WebhookEventsView />}
          {view === 'audit' && <AuditView />}
          {view === 'monitoring' && <MonitoringView />}
          {view === 'nexifyai' && <AgentView headers={headers} apiFetch={apiFetch} />}
        </div>
      </main>
    </div>
  );
};

export default Admin;

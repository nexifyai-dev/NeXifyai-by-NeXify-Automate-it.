import React, { useState, useEffect } from 'react';
import './CustomerPortal.css';

const API = process.env.REACT_APP_BACKEND_URL || '';
const I = ({ n }) => <span className="material-symbols-outlined">{n}</span>;
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '-';
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
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('overview');

  useEffect(() => {
    if (!token) { setError('Kein Zugangstoken vorhanden.'); setLoading(false); return; }
    fetch(`${API}/api/portal/customer/${token}`)
      .then(r => { if (!r.ok) throw new Error('Zugangslink ungültig oder abgelaufen'); return r.json(); })
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return (
    <div className="cp-loading"><div className="cp-spinner"></div><p>Laden...</p></div>
  );

  if (error) return (
    <div className="cp-error">
      <div className="cp-error-box">
        <I n="lock" /><h2>Zugang nicht möglich</h2>
        <p>{error}</p>
        <a href="/" className="cp-btn cp-btn-primary">Zur Startseite</a>
      </div>
    </div>
  );

  const tabs = [
    { id: 'overview', icon: 'dashboard', label: 'Übersicht' },
    { id: 'quotes', icon: 'description', label: `Angebote (${data?.quotes?.length || 0})` },
    { id: 'invoices', icon: 'receipt', label: `Rechnungen (${data?.invoices?.length || 0})` },
    { id: 'bookings', icon: 'event', label: `Termine (${data?.bookings?.length || 0})` },
  ];

  return (
    <div className="cp-layout" data-testid="customer-portal">
      <header className="cp-header">
        <div className="cp-header-inner">
          <div className="cp-logo"><img src="/icon-mark.svg" alt="" width="28" height="28" /><span>NeXify<em>AI</em></span></div>
          <div className="cp-user"><I n="person" /> {data?.customer_name || data?.email}</div>
        </div>
      </header>
      <div className="cp-tabs">
        {tabs.map(t => (
          <button key={t.id} className={`cp-tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)} data-testid={`cp-tab-${t.id}`}>
            <I n={t.icon} /><span>{t.label}</span>
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
                    {(q.status === 'sent' || q.status === 'opened') && (
                      <a href={`/angebot?token=${token}&qid=${q.quote_id}`} className="cp-btn cp-btn-primary" data-testid={`cp-view-quote-${q.quote_id}`}><I n="visibility" /> Angebot ansehen</a>
                    )}
                    <a href={`${API}/api/documents/quote/${q.quote_id}/pdf`} target="_blank" rel="noreferrer" className="cp-btn cp-btn-secondary" data-testid={`cp-dl-quote-${q.quote_id}`}><I n="picture_as_pdf" /> PDF herunterladen</a>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab === 'invoices' && (
          <div className="cp-invoices" data-testid="cp-invoices">
            <h2>Ihre Rechnungen</h2>
            {(!data?.invoices || data.invoices.length === 0) ? (
              <div className="cp-empty"><I n="receipt" /><p>Noch keine Rechnungen vorhanden.</p></div>
            ) : data.invoices.map(inv => (
              <div key={inv.invoice_id} className="cp-card" data-testid={`cp-inv-${inv.invoice_id}`}>
                <div className="cp-card-header">
                  <span className="cp-card-title">{inv.invoice_number}</span>
                  <span className="cp-badge" style={{ background: inv.payment_status === 'paid' ? '#10b98122' : '#f59e0b22', color: inv.payment_status === 'paid' ? '#10b981' : '#f59e0b' }}>
                    <I n={inv.payment_status === 'paid' ? 'check_circle' : 'schedule'} /> {inv.payment_status === 'paid' ? 'Bezahlt' : 'Ausstehend'}
                  </span>
                </div>
                <div className="cp-card-body">
                  <span>{fmtDate(inv.created_at)}</span>
                  <span className="cp-card-price">{fmtEur(inv.total_eur)}</span>
                </div>
                <div className="cp-card-actions">
                  <a href={`${API}/api/documents/invoice/${inv.invoice_id}/pdf`} target="_blank" rel="noreferrer" className="cp-btn cp-btn-secondary"><I n="picture_as_pdf" /> PDF herunterladen</a>
                </div>
              </div>
            ))}
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

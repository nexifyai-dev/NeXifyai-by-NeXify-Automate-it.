import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

const fmtEur = (v) => {
  if (v == null) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(v);
};

export default function QuotePortal() {
  const [quote, setQuote] = useState(null);
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [action, setAction] = useState(null);
  const [result, setResult] = useState(null);
  const [declineReason, setDeclineReason] = useState('');
  const [revisionFeedback, setRevisionFeedback] = useState('');
  const [panel, setPanel] = useState(null);

  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  const qid = params.get('qid');

  useEffect(() => {
    if (!token || !qid) { setError('Kein gültiger Zugangslink.'); setLoading(false); return; }
    fetch(`${API}/api/portal/quote/${qid}?token=${encodeURIComponent(token)}`)
      .then(r => { if (!r.ok) throw new Error(r.status === 403 ? 'Zugangslink abgelaufen oder ungültig' : 'Fehler beim Laden'); return r.json(); })
      .then(d => { setQuote(d.quote); setCompany(d.company); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [token, qid]);

  const doAction = async (endpoint, body = null) => {
    setAction(endpoint);
    try {
      const opts = { method: 'POST' };
      if (body) { opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(body); }
      const r = await fetch(`${API}/api/portal/quote/${qid}/${endpoint}?token=${encodeURIComponent(token)}`, opts);
      if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || 'Fehler'); }
      return await r.json();
    } finally { setAction(null); }
  };

  const handleAccept = async () => {
    try {
      const data = await doAction('accept');
      setResult({ type: 'accepted', data });
    } catch (e) { setError(e.message); }
  };

  const handleDecline = async () => {
    try {
      await doAction('decline', { reason: declineReason });
      setResult({ type: 'declined' });
    } catch (e) { setError(e.message); }
  };

  const handleRevision = async () => {
    if (!revisionFeedback.trim()) return;
    try {
      await doAction('revision', { feedback: revisionFeedback });
      setResult({ type: 'revision' });
    } catch (e) { setError(e.message); }
  };

  const S = {
    page: { minHeight: '100vh', background: '#0a0f14', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px', fontFamily: '-apple-system,BlinkMacSystemFont,system-ui,sans-serif' },
    card: { background: '#12171e', borderRadius: '12px', maxWidth: '720px', width: '100%', padding: '40px', boxShadow: '0 4px 32px rgba(0,0,0,0.5)' },
    logo: { marginBottom: '32px', display: 'flex', alignItems: 'center', gap: '4px' },
    brand: { fontSize: '22px', fontWeight: 700, color: '#fff' },
    ai: { fontSize: '22px', fontWeight: 700, color: '#ff9b7a' },
    h1: { fontSize: '24px', fontWeight: 700, color: '#fff', margin: '0 0 4px' },
    sub: { fontSize: '14px', color: '#78829a', margin: '0 0 28px' },
    custBox: { background: '#1a2028', padding: '16px', borderRadius: '8px', marginBottom: '28px' },
    custName: { color: '#fff', fontWeight: 600, margin: '0 0 2px', fontSize: '15px' },
    muted: { color: '#78829a', fontSize: '13px', margin: 0 },
    section: { marginBottom: '28px' },
    secTitle: { color: '#fff', fontSize: '15px', fontWeight: 600, margin: '0 0 12px', paddingBottom: '8px', borderBottom: '1px solid #252a32' },
    row: { display: 'flex', justifyContent: 'space-between', padding: '7px 0', fontSize: '14px', color: '#c5c9d2' },
    rowHl: { display: 'flex', justifyContent: 'space-between', padding: '10px 14px', fontSize: '14px', background: '#1a2028', borderRadius: '6px', borderLeft: '3px solid #ff9b7a', marginBottom: '4px' },
    accent: { color: '#ff9b7a', fontWeight: 600 },
    btn: { width: '100%', padding: '16px', background: '#ff9b7a', color: '#0c1117', fontWeight: 700, fontSize: '16px', border: 'none', borderRadius: '8px', cursor: 'pointer', transition: 'opacity .2s' },
    btnSec: { flex: 1, padding: '12px', background: 'transparent', border: '1px solid', fontWeight: 600, borderRadius: '8px', cursor: 'pointer', fontSize: '14px', transition: 'opacity .2s' },
    ta: { width: '100%', minHeight: '80px', background: '#1a2028', border: '1px solid #333', borderRadius: '6px', color: '#fff', padding: '12px', fontSize: '14px', resize: 'vertical', boxSizing: 'border-box' },
    status: (c) => ({ padding: '24px', background: '#1a2028', borderRadius: '8px', borderLeft: `4px solid ${c}`, marginBottom: '28px' }),
    statusH: { color: '#fff', fontSize: '20px', fontWeight: 700, margin: '0 0 8px' },
    grid3: { display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '16px', marginBottom: '28px' },
    gridItem: { display: 'flex', flexDirection: 'column', gap: '4px' },
    gridLabel: { fontSize: '11px', color: '#78829a', textTransform: 'uppercase', letterSpacing: '0.5px' },
    gridVal: { fontSize: '16px', color: '#fff', fontWeight: 600 },
    payBtn: { display: 'block', width: '100%', textAlign: 'center', padding: '16px', background: '#ff9b7a', color: '#0c1117', fontWeight: 700, fontSize: '16px', borderRadius: '8px', textDecoration: 'none', marginBottom: '16px' },
    bank: { background: '#1a2028', padding: '18px', borderRadius: '8px', marginBottom: '24px', fontSize: '13px', color: '#78829a', lineHeight: 1.7 },
    err: { background: '#3f1111', color: '#f87171', padding: '12px 16px', borderRadius: '6px', fontSize: '14px', marginBottom: '16px' },
    footer: { textAlign: 'center', paddingTop: '24px', borderTop: '1px solid #252a32', color: '#555', fontSize: '11px', lineHeight: 1.7 },
    eu: { marginTop: '12px', fontSize: '10px', color: '#444' },
  };

  if (loading) return <div style={S.page}><div style={S.card}><div style={{color:'#78829a',textAlign:'center',padding:'40px'}}>Angebot wird geladen...</div></div></div>;
  if (error && !quote) return <div style={S.page}><div style={S.card}><div style={S.err}>{error}</div><p style={S.muted}>Bitte verwenden Sie den Link aus Ihrer E-Mail.</p></div></div>;

  if (result) {
    if (result.type === 'accepted') {
      const d = result.data;
      return (
        <div style={S.page}><div style={S.card}>
          <div style={S.logo}><span style={S.brand}>NeXify</span><span style={S.ai}>AI</span></div>
          <div style={S.status('#22c55e')}><h2 style={S.statusH}>Angebot angenommen</h2><p style={S.muted}>Ihre Anzahlungsrechnung wurde erstellt.</p></div>
          <div style={S.grid3}>
            <div style={S.gridItem}><span style={S.gridLabel}>Rechnungsnr.</span><span style={S.gridVal}>{d.invoice_number}</span></div>
            <div style={S.gridItem}><span style={S.gridLabel}>Betrag (brutto)</span><span style={{...S.gridVal,color:'#ff9b7a'}}>{fmtEur(d.amount_gross)}</span></div>
            <div style={S.gridItem}><span style={S.gridLabel}>Faellig am</span><span style={S.gridVal}>{d.due_date}</span></div>
          </div>
          {d.checkout_url && <a href={d.checkout_url} style={S.payBtn} data-testid="pay-online-btn">Jetzt online bezahlen</a>}
          <div style={S.bank}>
            <strong style={{color:'#c5c9d2'}}>Alternativ per Banküberweisung:</strong><br/>
            IBAN: {d.bank_transfer?.iban}<br/>BIC: {d.bank_transfer?.bic}<br/>
            Verwendungszweck: <strong style={{color:'#c5c9d2'}}>{d.bank_transfer?.reference}</strong>
          </div>
          <div style={S.footer}><p>{company?.name} | {company?.phone} | {company?.email}</p><p style={S.eu}>Datenschutzorientiert für den europäischen Rechtsraum entwickelt.</p></div>
        </div></div>
      );
    }
    const msgs = { declined: { c: '#ef4444', t: 'Angebot abgelehnt', s: 'Vielen Dank für Ihre Rückmeldung.' }, revision: { c: '#f59e0b', t: 'Änderungswunsch gesendet', s: 'Wir melden uns in Kürze bei Ihnen.' } };
    const m = msgs[result.type];
    return (
      <div style={S.page}><div style={S.card}>
        <div style={S.logo}><span style={S.brand}>NeXify</span><span style={S.ai}>AI</span></div>
        <div style={S.status(m.c)}><h2 style={S.statusH}>{m.t}</h2><p style={S.muted}>{m.s}</p></div>
        <div style={S.footer}><p>{company?.name} | {company?.phone} | {company?.email}</p></div>
      </div></div>
    );
  }

  const calc = quote?.calculation || {};
  const customer = quote?.customer || {};
  const handled = ['accepted', 'declined'].includes(quote?.status);

  return (
    <div style={S.page}>
      <div style={S.card}>
        <div style={S.logo}><span style={S.brand}>NeXify</span><span style={S.ai}>AI</span></div>
        <h1 style={S.h1} data-testid="quote-title">Angebot {quote?.quote_number}</h1>
        <p style={S.sub}>{calc.tier_name} | Tarif-Nr. {calc.tariff_number}</p>

        <div style={S.custBox}>
          <p style={S.custName}>{customer.company || customer.name}</p>
          <p style={S.muted}>{customer.name}{customer.company ? ` | ${customer.email}` : ''}</p>
        </div>

        {quote?.discovery?.use_case && (
          <div style={S.section}>
            <div style={S.secTitle}>Use Case</div>
            <p style={{color:'#c5c9d2',fontSize:'14px',margin:0,lineHeight:1.6}}>{quote.discovery.use_case}</p>
          </div>
        )}

        <div style={S.section}>
          <div style={S.secTitle}>Kommerzielle Konditionen</div>
          <div style={S.row}><span>Tarifpreis pro Monat</span><span>{fmtEur(calc.reference_monthly_eur)}</span></div>
          <div style={S.row}><span>Vertragslaufzeit</span><span>{calc.contract_months} Monate</span></div>
          <div style={S.rowHl}><strong>Gesamtvertragswert (netto)</strong><strong>{fmtEur(calc.total_contract_eur)}</strong></div>
          <div style={{height:'12px'}} />
          <div style={S.row}><span>Aktivierungsanzahlung (30 %)</span><span>{fmtEur(calc.upfront_eur)}</span></div>
          <div style={{...S.row,fontSize:'13px',color:'#666'}}><span>zzgl. {calc.vat_rate}% USt.</span><span>{fmtEur(calc.upfront_vat)}</span></div>
          <div style={S.rowHl}><strong>Anzahlung (brutto)</strong><span style={S.accent}><strong>{fmtEur(calc.upfront_gross)}</strong></span></div>
          <div style={{height:'8px'}} />
          <div style={S.row}><span>Restbetrag (netto)</span><span>{fmtEur(calc.remaining_eur)}</span></div>
          <div style={S.row}><span>Monatliche Folgerate ({calc.recurring_count}x)</span><span>{fmtEur(calc.recurring_eur)}</span></div>
        </div>

        <div style={S.section}>
          <div style={S.secTitle}>Zahlungsinformationen</div>
          <div style={S.bank}>
            <strong style={{color:'#c5c9d2'}}>IBAN:</strong> NL66 REVO 3601 4304 36<br/>
            <strong style={{color:'#c5c9d2'}}>BIC:</strong> REVONL22<br/>
            <strong style={{color:'#c5c9d2'}}>Kontoinhaber:</strong> NeXify Automate<br/>
            <span style={{fontSize:'12px'}}>Von außerhalb des EWR zusätzlich: BIC CHASDEFX</span>
          </div>
        </div>

        <div style={{textAlign:'center',color:'#78829a',fontSize:'13px',padding:'12px',background:'#1a2028',borderRadius:'6px',marginBottom:'28px'}}>
          Gültig bis: {quote?.valid_until ? new Date(quote.valid_until).toLocaleDateString('de-DE') : ''}
        </div>

        <div style={{marginBottom:'12px'}}>
          <a href={`${API}/api/documents/quote/${qid}/pdf`} target="_blank" rel="noreferrer" style={{color:'#ff9b7a',fontSize:'14px'}} data-testid="pdf-download">PDF-Angebot herunterladen</a>
        </div>

        {error && <div style={S.err}>{error}</div>}

        {handled ? (
          <div style={S.status(quote.status === 'accepted' ? '#22c55e' : '#ef4444')}>
            <p style={{color:'#fff',margin:0}}>Dieses Angebot wurde bereits <strong>{quote.status === 'accepted' ? 'angenommen' : 'abgelehnt'}</strong>.</p>
          </div>
        ) : (
          <div style={{display:'flex',flexDirection:'column',gap:'12px',marginBottom:'28px'}}>
            <button style={{...S.btn, opacity: action ? 0.6 : 1}} onClick={handleAccept} disabled={!!action} data-testid="accept-quote-btn">
              {action === 'accept' ? 'Wird verarbeitet...' : 'Angebot annehmen'}
            </button>
            <div style={{display:'flex',gap:'12px'}}>
              <button style={{...S.btnSec,borderColor:'#ff9b7a',color:'#ff9b7a'}} onClick={() => setPanel(panel === 'revision' ? null : 'revision')} data-testid="revision-btn">Änderung anfragen</button>
              <button style={{...S.btnSec,borderColor:'#555',color:'#999'}} onClick={() => setPanel(panel === 'decline' ? null : 'decline')} data-testid="decline-btn">Angebot ablehnen</button>
            </div>
            {panel === 'revision' && <div>
              <textarea style={S.ta} value={revisionFeedback} onChange={e => setRevisionFeedback(e.target.value)} placeholder="Beschreiben Sie Ihren Änderungswunsch..." data-testid="revision-textarea" />
              <button style={{...S.btn,marginTop:'8px',background:'#ff9b7a',fontSize:'14px',padding:'12px'}} onClick={handleRevision} disabled={!revisionFeedback.trim() || !!action}>Änderungswunsch senden</button>
            </div>}
            {panel === 'decline' && <div>
              <textarea style={S.ta} value={declineReason} onChange={e => setDeclineReason(e.target.value)} placeholder="Grund (optional)..." data-testid="decline-textarea" />
              <button style={{...S.btn,marginTop:'8px',background:'#dc2626',fontSize:'14px',padding:'12px'}} onClick={handleDecline} disabled={!!action}>Ablehnung bestätigen</button>
            </div>}
          </div>
        )}

        <div style={S.footer}>
          <p>{company?.name} | {company?.phone} | {company?.email}</p>
          <p style={S.eu}>Datenschutzorientiert für den europäischen Rechtsraum entwickelt. DSGVO (EU) 2016/679.</p>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLanguage } from '../i18n/LanguageContext';
import T from '../i18n/translations';
import SEOHead from '../components/SEOHead';
import { API, COMPANY, LEGAL_PATHS, I, Logo, track } from '../components/shared';
import './BookingPage.css';

const LOCALE_MAP = { de: 'de-DE', nl: 'nl-NL', en: 'en-GB' };

const TEXTS = {
  de: {
    pageTitle: 'Strategiegespräch buchen',
    pageSubtitle: 'Besprechen Sie mit unseren KI-Strategen Ihr Vorhaben — persönlich, vertraulich und unverbindlich.',
    duration: '30 Min. Videocall',
    free: 'Kostenfrei & unverbindlich',
    expert: 'Persönlicher KI-Stratege',
    trustItems: [
      { icon: 'verified_user', text: 'DSGVO-konformer Beratungsprozess' },
      { icon: 'lock', text: 'Vertrauliche Behandlung Ihrer Informationen' },
      { icon: 'schedule', text: 'Antwort innerhalb von 2 Stunden' },
      { icon: 'workspace_premium', text: 'Keine versteckten Kosten oder Verpflichtungen' },
    ],
    whatHappens: 'Was Sie erwartet',
    expectItems: [
      { num: '1', title: 'Bestandsaufnahme', desc: 'Wir analysieren Ihre aktuelle Situation, Prozesse und Herausforderungen.' },
      { num: '2', title: 'Potenzialanalyse', desc: 'Konkrete KI-Anwendungsfälle und Automatisierungsmöglichkeiten für Ihr Unternehmen.' },
      { num: '3', title: 'Fahrplan', desc: 'Empfehlung mit Zeitplan, Investitionsrahmen und erwarteter Rendite (ROI).' },
    ],
    selectDate: 'Wählen Sie Ihren Wunschtermin',
    selectTime: 'Verfügbare Uhrzeiten',
    noTimes: 'Keine Termine verfügbar',
    yourDetails: 'Ihre Kontaktdaten',
    firstName: 'Vorname',
    lastName: 'Nachname',
    email: 'E-Mail-Adresse',
    phone: 'Telefon (optional)',
    company: 'Unternehmen (optional)',
    topic: 'Worüber möchten Sie sprechen?',
    topicPlaceholder: 'z. B. Vertriebsautomatisierung, Chatbot, Datenanalyse, Workflow-Optimierung ...',
    next: 'Weiter zur Terminbestätigung',
    back: 'Datum ändern',
    submit: 'Termin verbindlich buchen',
    submitting: 'Wird gebucht...',
    successTitle: 'Ihr Termin ist bestätigt!',
    successText: 'Eine Bestätigung mit allen Details wurde an {email} gesendet. Wir freuen uns auf das Gespräch mit Ihnen.',
    successNext: 'Was jetzt passiert:',
    successSteps: [
      'Bestätigung per E-Mail mit Kalender-Einladung',
      'Erinnerung 24h vor dem Termin',
      'Videocall-Link wird rechtzeitig zugestellt',
    ],
    close: 'Fertig',
    backHome: 'Zurück zur Startseite',
    validation: { firstName: 'Vorname erforderlich', lastName: 'Nachname erforderlich', email: 'Gültige E-Mail erforderlich' },
  },
  nl: {
    pageTitle: 'Strategiegesprek boeken',
    pageSubtitle: 'Bespreek uw plannen met onze AI-strategen — persoonlijk, vertrouwelijk en vrijblijvend.',
    duration: '30 min. videocall',
    free: 'Gratis & vrijblijvend',
    expert: 'Persoonlijke AI-strateeg',
    trustItems: [
      { icon: 'verified_user', text: 'AVG-conform adviesproces' },
      { icon: 'lock', text: 'Vertrouwelijke behandeling van uw informatie' },
      { icon: 'schedule', text: 'Reactie binnen 2 uur' },
      { icon: 'workspace_premium', text: 'Geen verborgen kosten of verplichtingen' },
    ],
    whatHappens: 'Wat u kunt verwachten',
    expectItems: [
      { num: '1', title: 'Inventarisatie', desc: 'We analyseren uw huidige situatie, processen en uitdagingen.' },
      { num: '2', title: 'Potentieelanalyse', desc: 'Concrete AI-toepassingen en automatiseringsmogelijkheden voor uw bedrijf.' },
      { num: '3', title: 'Stappenplan', desc: 'Aanbeveling met tijdlijn, investering en verwachte ROI.' },
    ],
    selectDate: 'Kies uw gewenste datum',
    selectTime: 'Beschikbare tijden',
    noTimes: 'Geen tijden beschikbaar',
    yourDetails: 'Uw contactgegevens',
    firstName: 'Voornaam',
    lastName: 'Achternaam',
    email: 'E-mailadres',
    phone: 'Telefoon (optioneel)',
    company: 'Bedrijf (optioneel)',
    topic: 'Waarover wilt u spreken?',
    topicPlaceholder: 'bijv. verkoopautomatisering, chatbot, data-analyse ...',
    next: 'Verder naar bevestiging',
    back: 'Datum wijzigen',
    submit: 'Afspraak bevestigen',
    submitting: 'Bezig...',
    successTitle: 'Uw afspraak is bevestigd!',
    successText: 'Een bevestiging is verzonden naar {email}.',
    successNext: 'Wat nu gebeurt:',
    successSteps: ['Bevestiging per e-mail', 'Herinnering 24u voor de afspraak', 'Videocall-link wordt tijdig verstuurd'],
    close: 'Gereed',
    backHome: 'Terug naar startpagina',
    validation: { firstName: 'Voornaam verplicht', lastName: 'Achternaam verplicht', email: 'Geldig e-mailadres verplicht' },
  },
  en: {
    pageTitle: 'Book Strategy Call',
    pageSubtitle: 'Discuss your project with our AI strategists — personal, confidential, and non-binding.',
    duration: '30 min. video call',
    free: 'Free & non-binding',
    expert: 'Personal AI strategist',
    trustItems: [
      { icon: 'verified_user', text: 'GDPR-compliant consultation process' },
      { icon: 'lock', text: 'Confidential treatment of your information' },
      { icon: 'schedule', text: 'Response within 2 hours' },
      { icon: 'workspace_premium', text: 'No hidden costs or obligations' },
    ],
    whatHappens: 'What to expect',
    expectItems: [
      { num: '1', title: 'Assessment', desc: 'We analyze your current situation, processes and challenges.' },
      { num: '2', title: 'Potential Analysis', desc: 'Concrete AI use cases and automation opportunities for your business.' },
      { num: '3', title: 'Roadmap', desc: 'Recommendation with timeline, investment and expected ROI.' },
    ],
    selectDate: 'Choose your preferred date',
    selectTime: 'Available times',
    noTimes: 'No times available',
    yourDetails: 'Your contact details',
    firstName: 'First name',
    lastName: 'Last name',
    email: 'Email address',
    phone: 'Phone (optional)',
    company: 'Company (optional)',
    topic: 'What would you like to discuss?',
    topicPlaceholder: 'e.g. sales automation, chatbot, data analysis ...',
    next: 'Continue to confirmation',
    back: 'Change date',
    submit: 'Confirm booking',
    submitting: 'Submitting...',
    successTitle: 'Your appointment is confirmed!',
    successText: 'A confirmation has been sent to {email}.',
    successNext: 'What happens next:',
    successSteps: ['Confirmation email with calendar invite', 'Reminder 24h before the call', 'Video call link sent in time'],
    close: 'Done',
    backHome: 'Back to homepage',
    validation: { firstName: 'First name required', lastName: 'Last name required', email: 'Valid email required' },
  },
};

export default function BookingPage() {
  const { lang } = useLanguage();
  const t = TEXTS[lang] || TEXTS.de;
  const locale = LOCALE_MAP[lang] || 'de-DE';
  const lp = LEGAL_PATHS[lang] || LEGAL_PATHS.de;

  const [step, setStep] = useState(1);
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ vorname: '', nachname: '', email: '', telefon: '', unternehmen: '', thema: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState(null);

  const dates = useMemo(() => {
    const d = [];
    const now = new Date();
    for (let i = 1; i <= 21; i++) {
      const x = new Date(now);
      x.setDate(now.getDate() + i);
      if (x.getDay() !== 0 && x.getDay() !== 6) d.push(x.toISOString().split('T')[0]);
    }
    return d;
  }, []);

  useEffect(() => {
    track('booking_page_view', { lang });
  }, [lang]);

  useEffect(() => {
    if (date) {
      fetch(`${API}/api/booking/slots?date=${date}`)
        .then(r => r.json())
        .then(d => setSlots(d.slots || []))
        .catch(() => setSlots(['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']));
    }
  }, [date]);

  const fmtDate = (d) => new Date(d).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  const validate = () => {
    const e = {};
    if (form.vorname.trim().length < 2) e.vorname = t.validation.firstName;
    if (form.nachname.trim().length < 2) e.nachname = t.validation.lastName;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t.validation.email;
    setErrors(e);
    return !Object.keys(e).length;
  };

  const submit = async () => {
    if (!validate()) return;
    setBusy(true);
    track('booking_page_submit', { date, time });
    try {
      const r = await fetch(`${API}/api/booking`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, date, time, source: 'booking_page', language: lang }),
      });
      const d = await r.json();
      if (r.ok) { setOk(d); track('booking_page_confirmed', { id: d.booking_id }); }
      else throw new Error(d.detail || 'Error');
    } catch (e) {
      setErrors({ submit: e.message || 'Booking failed' });
    } finally { setBusy(false); }
  };

  return (
    <div className="bp-root" data-testid="booking-page">
      <SEOHead lang={lang} page="booking" />

      {/* Nav Bar */}
      <nav className="bp-nav" data-testid="bp-nav">
        <div className="bp-nav-inner">
          <a href={`/${lang}`} className="bp-logo" data-testid="bp-logo"><Logo /></a>
          <a href={`/${lang}`} className="bp-back-link" data-testid="bp-back-home"><I n="arrow_back" /> {t.backHome}</a>
        </div>
      </nav>

      <div className="bp-layout">
        {/* Left Column: Info */}
        <div className="bp-info" data-testid="bp-info">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <h1 className="bp-title" data-testid="bp-title">{t.pageTitle}</h1>
            <p className="bp-subtitle">{t.pageSubtitle}</p>

            <div className="bp-badges">
              <span className="bp-badge"><I n="videocam" /> {t.duration}</span>
              <span className="bp-badge bp-badge-green"><I n="verified" /> {t.free}</span>
              <span className="bp-badge"><I n="person" /> {t.expert}</span>
            </div>

            <div className="bp-trust" data-testid="bp-trust">
              {t.trustItems.map((item, i) => (
                <div key={i} className="bp-trust-item">
                  <I n={item.icon} c="bp-trust-icon" />
                  <span>{item.text}</span>
                </div>
              ))}
            </div>

            <div className="bp-expect" data-testid="bp-expect">
              <h3 className="bp-expect-title">{t.whatHappens}</h3>
              {t.expectItems.map((item, i) => (
                <div key={i} className="bp-expect-item">
                  <div className="bp-expect-num">{item.num}</div>
                  <div>
                    <div className="bp-expect-heading">{item.title}</div>
                    <div className="bp-expect-desc">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Right Column: Booking Form */}
        <div className="bp-form-col">
          <motion.div className="bp-card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} data-testid="bp-card">
            <AnimatePresence mode="wait">
              {ok ? (
                <motion.div className="bp-success" key="success" data-testid="bp-success" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <div className="bp-success-icon"><I n="check_circle" /></div>
                  <h2>{t.successTitle}</h2>
                  <div className="bp-success-detail">
                    <div className="bp-success-row"><I n="event" /> <span>{fmtDate(date)}</span></div>
                    <div className="bp-success-row"><I n="schedule" /> <span>{time} Uhr</span></div>
                    <div className="bp-success-row"><I n="mail" /> <span>{form.email}</span></div>
                  </div>
                  <p className="bp-success-text">{t.successText.replace('{email}', form.email)}</p>
                  <div className="bp-success-next">
                    <h4>{t.successNext}</h4>
                    <ul>
                      {t.successSteps.map((s, i) => <li key={i}><I n="check" /> {s}</li>)}
                    </ul>
                  </div>
                  <a href={`/${lang}`} className="bp-btn bp-btn-primary" data-testid="bp-done">{t.close}</a>
                </motion.div>
              ) : step === 1 ? (
                <motion.div key="step1" data-testid="bp-step-1" initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }}>
                  <div className="bp-card-step">1/2</div>
                  <h3 className="bp-card-title">{t.selectDate}</h3>
                  <div className="bp-dates" data-testid="bp-dates">
                    {dates.map(d => (
                      <button key={d} className={`bp-date ${date === d ? 'sel' : ''}`} onClick={() => setDate(d)} data-testid={`bp-date-${d}`}>
                        <span className="bp-date-day">{new Date(d).toLocaleDateString(locale, { weekday: 'short' })}</span>
                        <span className="bp-date-num">{new Date(d).getDate()}</span>
                        <span className="bp-date-month">{new Date(d).toLocaleDateString(locale, { month: 'short' })}</span>
                      </button>
                    ))}
                  </div>
                  {date && (
                    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                      <h3 className="bp-card-title">{t.selectTime}</h3>
                      <div className="bp-times" data-testid="bp-times">
                        {slots.length > 0 ? slots.map(s => (
                          <button key={s} className={`bp-time ${time === s ? 'sel' : ''}`} onClick={() => setTime(s)} data-testid={`bp-time-${s}`}>{s}</button>
                        )) : <p className="bp-no-slots">{t.noTimes}</p>}
                      </div>
                    </motion.div>
                  )}
                  <button className="bp-btn bp-btn-primary" disabled={!date || !time} onClick={() => setStep(2)} data-testid="bp-next">
                    {t.next} <I n="arrow_forward" />
                  </button>
                </motion.div>
              ) : (
                <motion.div key="step2" data-testid="bp-step-2" initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }}>
                  <div className="bp-card-step">2/2</div>
                  <button className="bp-back" onClick={() => setStep(1)} data-testid="bp-back"><I n="arrow_back" /> {t.back}</button>
                  <div className="bp-selected">
                    <I n="event" />
                    <div><strong>{fmtDate(date)}</strong><span>{time} Uhr</span></div>
                  </div>
                  <h3 className="bp-card-title">{t.yourDetails}</h3>
                  <div className="bp-fields">
                    <div className="bp-row">
                      <div className="bp-field">
                        <label>{t.firstName} *</label>
                        <input type="text" className={errors.vorname ? 'err' : ''} value={form.vorname} onChange={e => setForm({...form, vorname: e.target.value})} data-testid="bp-vorname" />
                        {errors.vorname && <span className="bp-err">{errors.vorname}</span>}
                      </div>
                      <div className="bp-field">
                        <label>{t.lastName} *</label>
                        <input type="text" className={errors.nachname ? 'err' : ''} value={form.nachname} onChange={e => setForm({...form, nachname: e.target.value})} data-testid="bp-nachname" />
                        {errors.nachname && <span className="bp-err">{errors.nachname}</span>}
                      </div>
                    </div>
                    <div className="bp-field">
                      <label>{t.email} *</label>
                      <input type="email" className={errors.email ? 'err' : ''} value={form.email} onChange={e => setForm({...form, email: e.target.value})} data-testid="bp-email" />
                      {errors.email && <span className="bp-err">{errors.email}</span>}
                    </div>
                    <div className="bp-row">
                      <div className="bp-field">
                        <label>{t.phone}</label>
                        <input type="tel" value={form.telefon} onChange={e => setForm({...form, telefon: e.target.value})} placeholder="+49 ..." data-testid="bp-telefon" />
                      </div>
                      <div className="bp-field">
                        <label>{t.company}</label>
                        <input type="text" value={form.unternehmen} onChange={e => setForm({...form, unternehmen: e.target.value})} data-testid="bp-company" />
                      </div>
                    </div>
                    <div className="bp-field">
                      <label>{t.topic}</label>
                      <textarea value={form.thema} onChange={e => setForm({...form, thema: e.target.value})} rows={3} placeholder={t.topicPlaceholder} data-testid="bp-thema" />
                    </div>
                    {errors.submit && <div className="bp-submit-err"><I n="error" /> {errors.submit}</div>}
                    <button className="bp-btn bp-btn-primary" onClick={submit} disabled={busy} data-testid="bp-submit">
                      {busy ? <><span className="bp-spinner" />{t.submitting}</> : <>{t.submit} <I n="check_circle" /></>}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>

      {/* Minimal Footer */}
      <footer className="bp-footer" data-testid="bp-footer">
        <div className="bp-footer-inner">
          <span>{COMPANY.legal} &middot; KvK {COMPANY.kvk}</span>
          <div className="bp-footer-links">
            <a href={lp.impressum}>Impressum</a>
            <a href={lp.datenschutz}>Datenschutz</a>
            <a href={lp.agb}>AGB</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

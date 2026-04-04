import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './UnifiedLogin.css';

const API = process.env.REACT_APP_BACKEND_URL;
const I = ({ n, c }) => <span className={`material-symbols-outlined ${c || ''}`}>{n}</span>;

const fadeUp = { hidden: { opacity: 0, y: 18 }, visible: (i = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.5, ease: [0.25, 0.4, 0, 1] } }) };
const fadeIn = { hidden: { opacity: 0 }, visible: (i = 0) => ({ opacity: 1, transition: { delay: i * 0.1, duration: 0.6 } }) };

const UnifiedLogin = () => {
  const [step, setStep] = useState('email');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState('');
  const [regData, setRegData] = useState({ vorname: '', nachname: '', unternehmen: '', telefon: '', nachricht: '', dsgvoAccepted: false });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token && window.location.pathname.includes('/login/verify')) {
      setStep('verifying');
      verifyMagicLink(token);
      return;
    }
    const stored = localStorage.getItem('nx_auth');
    if (stored) {
      try {
        const auth = JSON.parse(stored);
        if (auth.token && auth.role === 'admin') {
          fetch(`${API}/api/admin/stats`, { headers: { 'Authorization': `Bearer ${auth.token}` } })
            .then(r => { if (r.ok) window.location.href = '/admin'; else { localStorage.removeItem('nx_auth'); localStorage.removeItem('nx_admin_token'); } })
            .catch(() => { localStorage.removeItem('nx_auth'); localStorage.removeItem('nx_admin_token'); });
        } else if (auth.token && auth.role === 'customer') {
          window.location.href = '/portal';
        }
      } catch { localStorage.removeItem('nx_auth'); }
    }
  }, []);

  const checkEmail = async () => {
    setError('');
    if (!email.trim()) { setError('Bitte E-Mail eingeben'); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/check-email`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      setRole(data.role);
      if (data.role === 'dual') {
        setStep('role_choice');
      } else if (data.role === 'admin') {
        setStep('password');
      } else if (data.role === 'customer') {
        await requestMagicLink();
      } else {
        setStep('register');
      }
    } catch {
      setError('Verbindungsfehler. Bitte versuchen Sie es erneut.');
    }
    setLoading(false);
  };

  const requestMagicLink = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/request-magic-link`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });
      if (res.ok) {
        setStep('magic_link_sent');
      } else {
        const d = await res.json();
        setError(d.detail || 'Fehler beim Senden des Zugangslinks');
      }
    } catch {
      setError('Verbindungsfehler');
    }
    setLoading(false);
  };

  const loginAdmin = async () => {
    setError('');
    if (!password) { setError('Bitte Passwort eingeben'); return; }
    setLoading(true);
    try {
      const form = new URLSearchParams();
      form.append('username', email.trim());
      form.append('password', password);
      const res = await fetch(`${API}/api/admin/login`, { method: 'POST', body: form });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('nx_auth', JSON.stringify({ token: data.access_token, role: 'admin', email: email.trim() }));
        window.location.href = '/admin';
      } else {
        setError('Ungültige Anmeldedaten');
      }
    } catch {
      setError('Verbindungsfehler');
    }
    setLoading(false);
  };

  const submitRegistration = async () => {
    setError('');
    if (!regData.vorname.trim() || !regData.nachname.trim()) {
      setError('Bitte Vor- und Nachname eingeben');
      return;
    }
    if (!regData.dsgvoAccepted) {
      setError('Bitte stimmen Sie der Datenschutzerklärung zu');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/contact`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          vorname: regData.vorname.trim(),
          nachname: regData.nachname.trim(),
          unternehmen: regData.unternehmen.trim(),
          telefon: regData.telefon.trim(),
          nachricht: regData.nachricht.trim() || 'Angebotsanfrage über Login-Registrierung',
          source: 'registration',
          language: 'de',
        }),
      });
      if (res.ok) {
        setStep('registered');
      } else {
        const d = await res.json();
        setError(d.detail || 'Registrierung fehlgeschlagen');
      }
    } catch {
      setError('Verbindungsfehler');
    }
    setLoading(false);
  };

  const verifyMagicLink = async (token) => {
    setError('');
    try {
      const res = await fetch(`${API}/api/auth/verify-token`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('nx_auth', JSON.stringify({ token: data.access_token, role: 'customer', email: data.email, name: data.customer_name }));
        window.location.href = '/portal';
      } else {
        const d = await res.json();
        setError(d.detail || 'Zugangslink ungültig oder abgelaufen');
        setStep('email');
      }
    } catch {
      setError('Verbindungsfehler');
      setStep('email');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (step === 'email') checkEmail();
      else if (step === 'password') loginAdmin();
      else if (step === 'register') submitRegistration();
    }
  };

  return (
    <div className="ul-page" data-testid="unified-login-page">
      {/* Left Visual Column */}
      <div className="ul-visual" data-testid="login-visual">
        <div className="ul-visual-inner">
          <div className="ul-visual-glow" />
          <div className="ul-visual-glow ul-visual-glow-2" />
          <div className="ul-visual-grid" />
          <motion.div className="ul-visual-content" initial="hidden" animate="visible">
            <motion.div className="ul-visual-logo" variants={fadeUp} custom={0}>
              <img src="/icon-mark.svg" alt="" width="40" height="40" />
              <span>NeXify<span className="ul-visual-ai">AI</span></span>
            </motion.div>
            <motion.p className="ul-visual-tagline" variants={fadeUp} custom={1}>
              Ihre digitale Infrastruktur.<br />Sicher. Intelligent. Skalierbar.
            </motion.p>
            <motion.div className="ul-visual-features" variants={fadeUp} custom={2}>
              <div className="ul-vf"><div className="ul-vf-icon"><I n="encrypted" /></div><span>Verschlüsselte Verbindung</span></div>
              <div className="ul-vf"><div className="ul-vf-icon"><I n="speed" /></div><span>Echtzeitverarbeitung</span></div>
              <div className="ul-vf"><div className="ul-vf-icon"><I n="verified_user" /></div><span>DSGVO-konform</span></div>
            </motion.div>
            <motion.div className="ul-visual-trust" variants={fadeIn} custom={4}>
              <div className="ul-trust-badge">
                <I n="shield" /> 256-bit TLS
              </div>
              <div className="ul-trust-badge">
                <I n="language" /> EU-Hosting
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Right Form Column */}
      <div className="ul-form-col">
        <motion.div className="ul-top-bar" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
          <a href="/" className="ul-home-link" data-testid="login-home-link">
            <I n="arrow_back" /> Startseite
          </a>
        </motion.div>

        <div className="ul-form-center">
          <motion.div className="ul-card" data-testid="unified-login-card" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15, ease: [0.25, 0.4, 0, 1] }}>
            <div className="ul-card-header">
              <h1 className="ul-title">Sicherer Zugang</h1>
              <p className="ul-card-sub">Melden Sie sich an oder erstellen Sie ein Konto</p>
            </div>

            <AnimatePresence mode="wait">
              {step === 'verifying' && (
                <motion.div className="ul-step" key="verifying" data-testid="login-verifying" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <div className="ul-spinner" />
                  <p className="ul-info">Zugangslink wird geprüft...</p>
                </motion.div>
              )}

              {step === 'email' && (
                <motion.div className="ul-step" key="email" data-testid="login-email-step" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }} transition={{ duration: 0.3 }}>
                  <div className="ul-field">
                    <label>E-Mail-Adresse</label>
                    <div className="ul-input-wrap">
                      <I n="mail" c="ul-input-icon" />
                      <input type="email" value={email} onChange={e => setEmail(e.target.value)} onKeyDown={handleKeyDown} placeholder="ihre@email.de" autoFocus data-testid="login-email-input" />
                    </div>
                  </div>
                  <button className="ul-btn" onClick={checkEmail} disabled={loading || !email.trim()} data-testid="login-continue-btn">
                    {loading ? <><div className="ul-btn-spinner" /> Wird geprüft...</> : <>Weiter <I n="arrow_forward" /></>}
                  </button>
                  <p className="ul-hint">Noch kein Konto? Geben Sie Ihre E-Mail ein — wir leiten Sie weiter.</p>
                </motion.div>
              )}

              {step === 'role_choice' && (
                <motion.div className="ul-step" key="role_choice" data-testid="login-role-choice-step" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }} transition={{ duration: 0.3 }}>
                  <div className="ul-role-badge"><I n="verified_user" /> Mehrfach-Zugang erkannt</div>
                  <p className="ul-sub">Für <strong>{email}</strong> existieren mehrere Zugänge. Bitte wählen Sie:</p>
                  <div className="ul-choice-grid">
                    <button className="ul-choice-card" onClick={() => setStep('password')} data-testid="login-choice-admin">
                      <div className="ul-choice-icon"><I n="admin_panel_settings" /></div>
                      <div className="ul-choice-text">
                        <strong>Administration</strong>
                        <span>Mit Passwort anmelden</span>
                      </div>
                      <I n="arrow_forward" c="ul-choice-arrow" />
                    </button>
                    <button className="ul-choice-card" onClick={async () => { await requestMagicLink(); }} data-testid="login-choice-customer">
                      <div className="ul-choice-icon"><I n="dashboard" /></div>
                      <div className="ul-choice-text">
                        <strong>Kundenportal</strong>
                        <span>Zugangslink per E-Mail</span>
                      </div>
                      <I n="arrow_forward" c="ul-choice-arrow" />
                    </button>
                  </div>
                  <button className="ul-link" onClick={() => { setStep('email'); setError(''); }} data-testid="login-role-back">Andere E-Mail verwenden</button>
                </motion.div>
              )}

              {step === 'password' && (
                <motion.div className="ul-step" key="password" data-testid="login-password-step" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }} transition={{ duration: 0.3 }}>
                  <div className="ul-role-badge"><I n="verified_user" /> Verifizierter Zugang</div>
                  <p className="ul-sub">{email}</p>
                  <div className="ul-field">
                    <label>Passwort</label>
                    <div className="ul-input-wrap">
                      <I n="lock" c="ul-input-icon" />
                      <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} onKeyDown={handleKeyDown} placeholder="Passwort eingeben" autoFocus data-testid="login-password-input" />
                      <button type="button" className="ul-pw-toggle" onClick={() => setShowPw(!showPw)} tabIndex={-1} aria-label={showPw ? 'Passwort verbergen' : 'Passwort anzeigen'} data-testid="login-pw-toggle">
                        <I n={showPw ? 'visibility_off' : 'visibility'} />
                      </button>
                    </div>
                  </div>
                  <button className="ul-btn" onClick={loginAdmin} disabled={loading || !password} data-testid="login-admin-btn">
                    {loading ? <><div className="ul-btn-spinner" /> Wird angemeldet...</> : <>Anmelden <I n="login" /></>}
                  </button>
                  <button className="ul-link" onClick={() => { setStep('email'); setPassword(''); setError(''); }} data-testid="login-back-email">Andere E-Mail verwenden</button>
                </motion.div>
              )}

              {step === 'magic_link_sent' && (
                <motion.div className="ul-step" key="magic" data-testid="login-magic-link-sent" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}>
                  <div className="ul-check-icon"><I n="mark_email_read" /></div>
                  <h2>Zugangslink gesendet</h2>
                  <p className="ul-info">Wir haben einen sicheren Zugangslink an <strong>{email}</strong> gesendet.</p>
                  <p className="ul-muted">Der Link ist 24 Stunden gültig. Bitte prüfen Sie auch Ihren Spam-Ordner.</p>
                  <button className="ul-link" onClick={() => { setStep('email'); setError(''); }} data-testid="login-magic-back">Andere E-Mail verwenden</button>
                </motion.div>
              )}

              {step === 'register' && (
                <motion.div className="ul-step" key="register" data-testid="login-register-step" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }} transition={{ duration: 0.3 }}>
                  <div className="ul-role-badge ul-role-new"><I n="person_add" /> Konto erstellen</div>
                  <p className="ul-sub">Kostenlos registrieren und sofort Zugang zu Angeboten, Projektstatus und Rechnungen erhalten.</p>
                  <p className="ul-sub-email">Registrierung für <strong>{email}</strong></p>
                  <div className="ul-field-row">
                    <div className="ul-field">
                      <label>Vorname *</label>
                      <input type="text" value={regData.vorname} onChange={e => setRegData({...regData, vorname: e.target.value})} placeholder="Vorname" autoFocus data-testid="register-firstname" />
                    </div>
                    <div className="ul-field">
                      <label>Nachname *</label>
                      <input type="text" value={regData.nachname} onChange={e => setRegData({...regData, nachname: e.target.value})} placeholder="Nachname" data-testid="register-lastname" />
                    </div>
                  </div>
                  <div className="ul-field">
                    <label>Unternehmen</label>
                    <input type="text" value={regData.unternehmen} onChange={e => setRegData({...regData, unternehmen: e.target.value})} placeholder="Firmenname (optional)" data-testid="register-company" />
                  </div>
                  <div className="ul-field">
                    <label>Telefon</label>
                    <input type="tel" value={regData.telefon} onChange={e => setRegData({...regData, telefon: e.target.value})} placeholder="+49 ..." data-testid="register-phone" />
                  </div>
                  <div className="ul-field">
                    <label>Nachricht / Anfrage</label>
                    <textarea value={regData.nachricht} onChange={e => setRegData({...regData, nachricht: e.target.value})} placeholder="Beschreiben Sie kurz Ihr Anliegen oder Projekt..." rows={3} data-testid="register-message" />
                  </div>
                  <label className="ul-checkbox" data-testid="register-dsgvo">
                    <input type="checkbox" checked={regData.dsgvoAccepted} onChange={e => setRegData({...regData, dsgvoAccepted: e.target.checked})} />
                    <span>Ich habe die <a href="/de/datenschutz" target="_blank" rel="noopener noreferrer">Datenschutzerklärung</a> gelesen und stimme der Verarbeitung meiner Daten zu.</span>
                  </label>
                  <button className="ul-btn" onClick={submitRegistration} disabled={loading || !regData.vorname.trim() || !regData.nachname.trim() || !regData.dsgvoAccepted} data-testid="register-submit-btn">
                    {loading ? <><div className="ul-btn-spinner" /> Wird registriert...</> : <>Konto erstellen <I n="arrow_forward" /></>}
                  </button>
                  <div className="ul-trust-row">
                    <span><I n="lock" /> Verschlüsselt</span>
                    <span><I n="verified_user" /> DSGVO-konform</span>
                    <span><I n="shield" /> Kein Spam</span>
                  </div>
                  <button className="ul-link" onClick={() => { setStep('email'); setError(''); }} data-testid="register-back-email">Andere E-Mail verwenden</button>
                </motion.div>
              )}

              {step === 'registered' && (
                <motion.div className="ul-step" key="done" data-testid="login-registered" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}>
                  <div className="ul-check-icon"><I n="check_circle" /></div>
                  <h2>Willkommen bei NeXifyAI</h2>
                  <p className="ul-info">Ihr Konto wurde erfolgreich angelegt. Wir freuen uns, Sie als neuen Kunden begrüßen zu dürfen.</p>
                  <div className="ul-success-steps">
                    <div className="ul-success-step"><I n="check" /> Kontodaten gespeichert</div>
                    <div className="ul-success-step"><I n="check" /> Bestätigungs-E-Mail wird gesendet</div>
                    <div className="ul-success-step"><I n="schedule" /> Freischaltung innerhalb von 2 Stunden</div>
                  </div>
                  <p className="ul-muted">Sie erhalten eine E-Mail mit Ihrem persönlichen Zugangslink, sobald Ihr Konto freigeschaltet wurde.</p>
                  <div className="ul-success-actions">
                    <a href="/termin" className="ul-btn" data-testid="register-book-meeting">
                      <I n="calendar_month" /> Strategiegespräch buchen
                    </a>
                    <a href="/" className="ul-btn ul-btn-secondary" data-testid="register-back-home">Zurück zur Startseite</a>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <motion.div className="ul-error" data-testid="login-error" initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}>
                <I n="error" c="ul-error-icon" /> {error}
              </motion.div>
            )}
          </motion.div>

          <motion.div className="ul-legal" data-testid="login-legal-links" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
            <a href="/">Startseite</a>
            <span className="ul-dot" />
            <a href="/de/impressum">Impressum</a>
            <span className="ul-dot" />
            <a href="/de/datenschutz">Datenschutz</a>
            <span className="ul-dot" />
            <a href="/de/agb">AGB</a>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedLogin;

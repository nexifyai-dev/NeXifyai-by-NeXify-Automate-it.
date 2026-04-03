import React, { useState, useEffect } from 'react';
import './UnifiedLogin.css';

const API = process.env.REACT_APP_BACKEND_URL;
const I = ({ n, c }) => <span className={`material-symbols-outlined ${c || ''}`}>{n}</span>;

const UnifiedLogin = () => {
  const [step, setStep] = useState('email'); // email | password | magic_link_sent | verifying | register
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState('');
  const [regData, setRegData] = useState({ vorname: '', nachname: '', unternehmen: '', telefon: '', nachricht: '' });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token && window.location.pathname.includes('/login/verify')) {
      setStep('verifying');
      verifyMagicLink(token);
    }
    const stored = localStorage.getItem('nx_auth');
    if (stored) {
      try {
        const auth = JSON.parse(stored);
        if (auth.role === 'admin') window.location.href = '/admin';
        else if (auth.role === 'customer') window.location.href = '/portal';
      } catch {}
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
      if (data.role === 'admin') {
        setStep('password');
      } else if (data.role === 'customer') {
        await requestMagicLink();
      } else {
        // Kein Konto — Registrierung anbieten
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
          <div className="ul-visual-orb" />
          <div className="ul-visual-orb ul-visual-orb-2" />
          <div className="ul-visual-grid" />
          <div className="ul-visual-content">
            <div className="ul-visual-logo">NEXIFY<span className="ul-visual-ai">AI</span></div>
            <p className="ul-visual-tagline">Ihre digitale Infrastruktur.<br />Sicher. Intelligent. Skalierbar.</p>
            <div className="ul-visual-features">
              <div className="ul-vf"><I n="shield" /> Verschlüsselte Verbindung</div>
              <div className="ul-vf"><I n="speed" /> Echtzeitverarbeitung</div>
              <div className="ul-vf"><I n="lock" /> DSGVO-konform</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Form Column */}
      <div className="ul-form-col">
        <div className="ul-top-bar">
          <a href="/" className="ul-home-link" data-testid="login-home-link">
            <I n="arrow_back" /> Startseite
          </a>
        </div>

        <div className="ul-form-center">
          <div className="ul-card" data-testid="unified-login-card">
            <div className="ul-logo">Sicherer Zugang</div>
            <p className="ul-card-sub">Melden Sie sich an oder erstellen Sie ein Konto</p>

            {step === 'verifying' && (
              <div className="ul-step" data-testid="login-verifying">
                <div className="ul-spinner" />
                <p className="ul-info">Zugangslink wird geprüft...</p>
              </div>
            )}

            {step === 'email' && (
              <div className="ul-step" data-testid="login-email-step">
                <div className="ul-field">
                  <label>E-Mail-Adresse</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} onKeyDown={handleKeyDown} placeholder="ihre@email.de" autoFocus data-testid="login-email-input" />
                </div>
                <button className="ul-btn" onClick={checkEmail} disabled={loading || !email.trim()} data-testid="login-continue-btn">
                  {loading ? <><div className="ul-btn-spinner" /> Wird geprüft...</> : 'Weiter'}
                </button>
                <p className="ul-hint">Noch kein Konto? Geben Sie Ihre E-Mail ein — wir leiten Sie weiter.</p>
              </div>
            )}

            {step === 'password' && (
              <div className="ul-step" data-testid="login-password-step">
                <div className="ul-role-badge"><I n="verified_user" /> Verifizierter Zugang</div>
                <p className="ul-sub">{email}</p>
                <div className="ul-field">
                  <label>Passwort</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={handleKeyDown} placeholder="Passwort" autoFocus data-testid="login-password-input" />
                </div>
                <button className="ul-btn" onClick={loginAdmin} disabled={loading || !password} data-testid="login-admin-btn">
                  {loading ? <><div className="ul-btn-spinner" /> Wird angemeldet...</> : 'Anmelden'}
                </button>
                <button className="ul-link" onClick={() => { setStep('email'); setPassword(''); setError(''); }}>Andere E-Mail verwenden</button>
              </div>
            )}

            {step === 'magic_link_sent' && (
              <div className="ul-step" data-testid="login-magic-link-sent">
                <div className="ul-check-icon"><I n="mark_email_read" /></div>
                <h2>Zugangslink gesendet</h2>
                <p className="ul-info">Wir haben einen sicheren Zugangslink an <strong>{email}</strong> gesendet.</p>
                <p className="ul-muted">Der Link ist 24 Stunden gültig. Bitte prüfen Sie auch Ihren Spam-Ordner.</p>
                <button className="ul-link" onClick={() => { setStep('email'); setError(''); }}>Andere E-Mail verwenden</button>
              </div>
            )}

            {step === 'register' && (
              <div className="ul-step" data-testid="login-register-step">
                <div className="ul-role-badge ul-role-new"><I n="person_add" /> Konto erstellen</div>
                <p className="ul-sub">Für <strong>{email}</strong> liegt noch kein Konto vor. Erstellen Sie jetzt eines, um Angebote anzufragen und Ihr Kundenportal zu nutzen.</p>
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
                  <textarea value={regData.nachricht} onChange={e => setRegData({...regData, nachricht: e.target.value})} placeholder="Beschreiben Sie kurz Ihr Anliegen..." rows={3} data-testid="register-message" />
                </div>
                <button className="ul-btn" onClick={submitRegistration} disabled={loading || !regData.vorname.trim() || !regData.nachname.trim()} onKeyDown={handleKeyDown} data-testid="register-submit-btn">
                  {loading ? <><div className="ul-btn-spinner" /> Wird registriert...</> : 'Konto erstellen & Anfrage senden'}
                </button>
                <button className="ul-link" onClick={() => { setStep('email'); setError(''); }}>Andere E-Mail verwenden</button>
              </div>
            )}

            {step === 'registered' && (
              <div className="ul-step" data-testid="login-registered">
                <div className="ul-check-icon"><I n="check_circle" /></div>
                <h2>Konto erstellt</h2>
                <p className="ul-info">Vielen Dank! Ihr Konto wurde erfolgreich angelegt. Wir melden uns in Kürze bei Ihnen.</p>
                <p className="ul-muted">Sie erhalten eine E-Mail mit Ihren Zugangsdaten, sobald Ihr Konto freigeschaltet wurde.</p>
                <a href="/" className="ul-btn" data-testid="register-back-home">Zurück zur Startseite</a>
              </div>
            )}

            {error && <div className="ul-error" data-testid="login-error">{error}</div>}
          </div>

          <div className="ul-legal" data-testid="login-legal-links">
            <a href="/">Startseite</a>
            <span className="ul-dot" />
            <a href="/impressum">Impressum</a>
            <span className="ul-dot" />
            <a href="/datenschutz">Datenschutz</a>
            <span className="ul-dot" />
            <a href="/agb">AGB</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedLogin;

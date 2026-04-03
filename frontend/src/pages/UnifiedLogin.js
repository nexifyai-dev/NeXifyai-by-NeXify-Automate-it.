import React, { useState, useEffect } from 'react';
import './UnifiedLogin.css';

const API = process.env.REACT_APP_BACKEND_URL;
const I = ({ n, c }) => <span className={`material-symbols-outlined ${c || ''}`}>{n}</span>;

const UnifiedLogin = () => {
  const [step, setStep] = useState('email'); // email | admin_password | magic_link_sent | verifying
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState('');

  // Auto-verify magic link token from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token && window.location.pathname.includes('/login/verify')) {
      setStep('verifying');
      verifyMagicLink(token);
    }
    // Check if already logged in
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
        setStep('admin_password');
      } else if (data.role === 'customer') {
        await requestMagicLink();
      } else {
        setError('Kein Konto für diese E-Mail gefunden. Bitte kontaktieren Sie uns.');
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
      const res = await fetch(`${API}/api/admin/login`, {
        method: 'POST', body: form,
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('nx_auth', JSON.stringify({
          token: data.access_token, role: 'admin', email: email.trim()
        }));
        window.location.href = '/admin';
      } else {
        setError('Ungültige Anmeldedaten');
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
        localStorage.setItem('nx_auth', JSON.stringify({
          token: data.access_token, role: 'customer', email: data.email, name: data.customer_name
        }));
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
      else if (step === 'admin_password') loginAdmin();
    }
  };

  return (
    <div className="ul-page" data-testid="unified-login-page">
      <div className="ul-top-bar">
        <a href="/" className="ul-home-link" data-testid="login-home-link">NeXifyAI</a>
      </div>
      <div className="ul-card" data-testid="unified-login-card">
        <div className="ul-logo">Anmelden</div>
        <p className="ul-card-sub">Admin-Bereich oder Kundenportal</p>

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
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                onKeyDown={handleKeyDown} placeholder="ihre@email.de"
                autoFocus data-testid="login-email-input"
              />
            </div>
            <button className="ul-btn" onClick={checkEmail} disabled={loading || !email.trim()} data-testid="login-continue-btn">
              {loading ? 'Wird geprüft...' : 'Weiter'}
            </button>
          </div>
        )}

        {step === 'admin_password' && (
          <div className="ul-step" data-testid="login-password-step">
            <div className="ul-role-badge"><span className="ul-role-icon"><I n="admin_panel_settings" /></span> Interner Zugang</div>
            <p className="ul-sub">{email}</p>
            <div className="ul-field">
              <label>Passwort</label>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)}
                onKeyDown={handleKeyDown} placeholder="Passwort"
                autoFocus data-testid="login-password-input"
              />
            </div>
            <button className="ul-btn" onClick={loginAdmin} disabled={loading || !password} data-testid="login-admin-btn">
              {loading ? 'Wird angemeldet...' : 'Anmelden'}
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
      <div className="ul-footer">nexifyai.de</div>
    </div>
  );
};

export default UnifiedLogin;

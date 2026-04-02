import React, { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext();

const SUPPORTED = ['de', 'nl', 'en'];
const COUNTRY_MAP = { DE: 'de', AT: 'de', CH: 'de', NL: 'nl', BE: 'nl' };

function detectFromPath() {
  const seg = window.location.pathname.split('/')[1];
  return SUPPORTED.includes(seg) ? seg : null;
}

async function detectFromIP() {
  try {
    const r = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(3000) });
    const d = await r.json();
    return COUNTRY_MAP[d.country_code] || 'en';
  } catch {
    try {
      const r = await fetch('https://ip-api.com/json/?fields=countryCode', { signal: AbortSignal.timeout(3000) });
      const d = await r.json();
      return COUNTRY_MAP[d.countryCode] || 'en';
    } catch {
      return 'en';
    }
  }
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    const fromPath = detectFromPath();
    if (fromPath) return fromPath;
    const stored = localStorage.getItem('nx_lang');
    if (stored && SUPPORTED.includes(stored)) return stored;
    return 'de';
  });
  const [detected, setDetected] = useState(false);

  useEffect(() => {
    const fromPath = detectFromPath();
    if (fromPath) { setLangState(fromPath); localStorage.setItem('nx_lang', fromPath); setDetected(true); return; }
    const stored = localStorage.getItem('nx_lang');
    if (stored && SUPPORTED.includes(stored)) { setDetected(true); return; }
    detectFromIP().then(l => { setLangState(l); localStorage.setItem('nx_lang', l); setDetected(true); });
  }, []);

  const setLang = (l) => {
    if (!SUPPORTED.includes(l)) return;
    setLangState(l);
    localStorage.setItem('nx_lang', l);
    const path = window.location.pathname;
    const segs = path.split('/').filter(Boolean);
    if (SUPPORTED.includes(segs[0])) segs[0] = l; else segs.unshift(l);
    const newPath = '/' + segs.join('/');
    window.history.pushState(null, '', newPath);
  };

  return <LanguageContext.Provider value={{ lang, setLang, detected }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  return useContext(LanguageContext);
}

export { SUPPORTED };

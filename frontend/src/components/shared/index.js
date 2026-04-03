import React, { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

export const API = process.env.REACT_APP_BACKEND_URL || '';

export const COMPANY = {
  name: 'NeXifyAI by NeXify', tagline: 'Chat it. Automate it.', legal: 'NeXify Automate',
  ceo: 'Pascal Courbois, Geschäftsführer',
  addr: { de: { s: 'Wallstraße 9', c: '41334 Nettetal-Kaldenkirchen', co: 'Deutschland' }, nl: { s: 'Graaf van Loonstraat 1E', c: '5921 JA Venlo', co: 'Niederlande' } },
  phone: '+31 6 133 188 56', email: 'support@nexify-automate.com', web: 'nexify-automate.com', kvk: '90483944', vat: 'NL865786276B01'
};

export const LEGAL_PATHS = {
  de: { impressum: '/de/impressum', datenschutz: '/de/datenschutz', agb: '/de/agb', ki: '/de/ki-hinweise' },
  nl: { impressum: '/nl/impressum', datenschutz: '/nl/privacybeleid', agb: '/nl/voorwaarden', ki: '/nl/ai-informatie' },
  en: { impressum: '/en/imprint', datenschutz: '/en/privacy', agb: '/en/terms', ki: '/en/ai-transparency' }
};

export const LOCALE_MAP = { de: 'de-DE', nl: 'nl-NL', en: 'en-GB' };

export const genSid = () => `s_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;

export const track = async (ev, props = {}) => {
  try {
    const sid = sessionStorage.getItem('nx_s') || genSid();
    sessionStorage.setItem('nx_s', sid);
    await fetch(`${API}/api/analytics/track`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: ev, properties: { ...props, ts: new Date().toISOString() }, session_id: sid }) });
  } catch (_) {}
};

export const I = ({ n, c = '' }) => <span className={`material-symbols-outlined ${c}`} aria-hidden="true">{n}</span>;

export const fadeUp = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.25, 0.4, 0, 1] } } };
export const fadeIn = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { duration: 0.6 } } };
export const stagger = { visible: { transition: { staggerChildren: 0.1 } } };
export const scaleIn = { hidden: { opacity: 0, scale: 0.9 }, visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: [0.25, 0.4, 0, 1] } } };

export function AnimSection({ children, className = '', id, ...props }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.section ref={ref} id={id} className={className} initial="hidden" animate={isInView ? 'visible' : 'hidden'} variants={stagger} {...props}>
      {children}
    </motion.section>
  );
}

export const BrandName = ({ className }) => <span className={className}>NeXify<span className="brand-ai">AI</span></span>;

export const Logo = ({ size = 'md' }) => {
  const s = size === 'sm' ? 24 : size === 'lg' ? 40 : 32;
  const fs = size === 'sm' ? '.9375rem' : size === 'lg' ? '1.375rem' : '1.125rem';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size === 'sm' ? 8 : 10 }}>
      <img src="/icon-mark.svg" alt="" width={s} height={s} style={{ display: 'block' }} />
      <span style={{ fontFamily: 'var(--f-display)', fontWeight: 800, fontSize: fs, color: '#fff', letterSpacing: '-.02em' }}>
        NeXify<span className="brand-ai">AI</span>
      </span>
    </div>
  );
};

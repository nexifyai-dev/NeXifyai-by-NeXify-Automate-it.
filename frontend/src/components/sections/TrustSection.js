import React from 'react';
import { motion } from 'framer-motion';
import { AnimSection, I, fadeUp } from '../shared';

const TrustSection = ({ t }) => (
  <AnimSection id="trust" className="section bg-dark" data-testid="trust-section">
    <div className="container">
      <motion.header className="section-header centered" variants={fadeUp}>
        <span className="label">{t.lang === 'nl' ? 'VERTROUWEN & VEILIGHEID' : t.lang === 'en' ? 'TRUST & SECURITY' : 'VERTRAUEN & SICHERHEIT'}</span>
        <h2>{t.lang === 'nl' ? 'Datascherming voor de Europese rechtsruimte' : t.lang === 'en' ? 'Data protection for the European legal framework' : 'Datenschutzorientiert für den europäischen Rechtsraum entwickelt'}</h2>
        <p className="section-subtitle">{t.lang === 'nl' ? 'Uw data, uw controle. Privacy by Design, gehost in de EU.' : t.lang === 'en' ? 'Your data, your control. Privacy by Design, hosted in the EU.' : 'Ihre Daten, Ihre Kontrolle. Privacy by Design, gehostet in der EU.'}</p>
      </motion.header>
      <div className="trust-grid" role="list">
        {[
          { icon: 'shield', title: 'DSGVO / AVG', desc: t.lang === 'en' ? 'Full compliance with EU General Data Protection Regulation (2016/679)' : 'Vollständige Umsetzung der Datenschutz-Grundverordnung (EU) 2016/679' },
          { icon: 'policy', title: 'EU AI Act', desc: t.lang === 'en' ? 'Transparency and labeling obligations under (EU) 2024/1689' : 'Transparenz- und Kennzeichnungspflichten gemäß (EU) 2024/1689' },
          { icon: 'cloud_done', title: t.lang === 'en' ? 'EU Hosting' : 'EU-Hosting', desc: t.lang === 'en' ? 'Data processing exclusively in EU data centers (Frankfurt, Amsterdam)' : 'Datenverarbeitung ausschließlich in EU-Rechenzentren (Frankfurt, Amsterdam)' },
          { icon: 'lock', title: t.lang === 'en' ? 'Encryption' : 'Verschlüsselung', desc: t.lang === 'en' ? 'TLS 1.3 in transit, AES-256 at rest, Argon2 password hashing' : 'TLS 1.3 bei Übertragung, AES-256 bei Speicherung, Argon2-Passwort-Hashing' },
          { icon: 'vpn_lock', title: 'Privacy by Design', desc: t.lang === 'en' ? 'Data minimization, purpose limitation, storage periods, RBAC' : 'Datenminimierung, Zweckbindung, Speicherfristen, rollenbasierte Zugriffe' },
          { icon: 'verified_user', title: 'ISO 27001/27701', desc: t.lang === 'en' ? 'Aligned with ISO/IEC 27001 and 27701 standards (not certified)' : 'Orientiert an ISO/IEC 27001 und 27701 (keine Zertifizierung)' },
        ].map((item, i) => (
          <motion.div key={i} className="trust-card" role="listitem" variants={fadeUp}>
            <I n={item.icon} c="trust-icon" />
            <h3>{item.title}</h3>
            <p>{item.desc}</p>
          </motion.div>
        ))}
      </div>
      <div className="trust-ops-grid" data-testid="trust-ops">
        {[
          { icon: 'link', title: t.lang === 'en' ? 'Secure Document Access' : 'Sichere Dokumentenzugriffe', desc: t.lang === 'en' ? 'Time-limited Magic Links instead of passwords. Single-use tokens with automatic expiration.' : 'Zeitbegrenzte Magic Links statt Passwörter. Einmal-Tokens mit automatischer Ablaufzeit.' },
          { icon: 'history', title: 'Audit Trail', desc: t.lang === 'en' ? 'Complete audit logging of all commercial transactions, document access and system changes.' : 'Lückenlose Protokollierung aller kommerziellen Transaktionen, Dokumentenzugriffe und Systemeingriffe.' },
          { icon: 'auto_delete', title: t.lang === 'en' ? 'Data Lifecycle' : 'Daten-Lebenszyklus', desc: t.lang === 'en' ? 'Defined retention and deletion periods per data category. Automated cleanup processes.' : 'Definierte Aufbewahrungs- und Löschfristen pro Datenkategorie. Automatisierte Bereinigungsprozesse.' },
          { icon: 'admin_panel_settings', title: 'RBAC', desc: t.lang === 'en' ? 'Role-based access control with principle of least privilege across all systems.' : 'Rollenbasierte Zugriffskontrolle mit Minimal-Rechte-Prinzip über alle Systeme.' },
        ].map((item, i) => (
          <motion.div key={i} className="trust-ops-card" role="listitem" variants={fadeUp}>
            <I n={item.icon} c="trust-ops-icon" />
            <div>
              <h4>{item.title}</h4>
              <p>{item.desc}</p>
            </div>
          </motion.div>
        ))}
      </div>
      <motion.div className="trust-eu-note" variants={fadeUp}>
        <div className="eu-emblem-row">
          <svg viewBox="0 0 810 540" width="48" height="32" className="eu-flag-svg" aria-label="EU Flag">
            <rect width="810" height="540" fill="#003399"/>
            {[...Array(12)].map((_, i) => {
              const angle = (i * 30 - 90) * Math.PI / 180;
              const cx = 405 + 160 * Math.cos(angle);
              const cy = 270 + 160 * Math.sin(angle);
              return <polygon key={i} points={`${cx},${cy-20} ${cx+6},${cy-6} ${cx+19},${cy-6} ${cx+8},${cy+4} ${cx+12},${cy+19} ${cx},${cy+10} ${cx-12},${cy+19} ${cx-8},${cy+4} ${cx-19},${cy-6} ${cx-6},${cy-6}`} fill="#FFCC00"/>;
            })}
          </svg>
          <span>{t.lang === 'en' ? 'Developed in compliance with European data protection and AI legislation. This does not represent an official EU endorsement, certification or partnership.' : t.lang === 'nl' ? 'Ontwikkeld in overeenstemming met Europese gegevensbeschermings- en AI-wetgeving. Dit vertegenwoordigt geen officiële EU-goedkeuring, certificering of partnerschap.' : 'Datenschutzorientiert für den europäischen Rechtsraum entwickelt. Dies stellt keine offizielle EU-Billigung, Zertifizierung oder Partnerschaft dar.'}</span>
        </div>
      </motion.div>
    </div>
  </AnimSection>
);

export default TrustSection;

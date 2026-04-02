import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Helmet } from 'react-helmet-async';
import { useLanguage } from '../i18n/LanguageContext';
import { getIntegrationBySlug, getFeaturedDetail, INTEGRATION_CATEGORIES } from '../data/integrations';
import '../App.css';

const API = process.env.REACT_APP_BACKEND_URL || '';
const I = ({ n, c = '' }) => <span className={`material-symbols-outlined ${c}`} aria-hidden="true">{n}</span>;

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.25, 0.4, 0, 1] } } };

export default function IntegrationDetail() {
  const { slug } = useParams();
  const { lang } = useLanguage();
  const [faqOpen, setFaqOpen] = useState(0);

  const integration = getIntegrationBySlug(slug);
  const featured = getFeaturedDetail(slug);
  const homePath = `/${lang}`;

  useEffect(() => { window.scrollTo(0, 0); }, [slug]);

  if (!integration) {
    return (
      <div className="legal-page">
        <div className="intd-nav">
          <div className="container">
            <div className="intd-nav-inner">
              <Link to={homePath} className="intd-logo-link" data-testid="intd-logo">
                <img src="/icon-mark.svg" alt="" width="28" height="28" />
                <span className="intd-logo-text">NeXify<span className="intd-logo-accent">AI</span></span>
              </Link>
              <Link to={`${homePath}#integrationen`} className="intd-back" data-testid="intd-back">
                <I n="arrow_back" /> {lang === 'nl' ? 'Terug naar integraties' : lang === 'en' ? 'Back to integrations' : 'Zurück zu Integrationen'}
              </Link>
            </div>
          </div>
        </div>
        <div className="container" style={{ padding: '120px 24px', textAlign: 'center' }}>
          <h1 style={{ fontSize: '1.5rem', marginBottom: 16 }}>{lang === 'en' ? 'Integration not found' : 'Integration nicht gefunden'}</h1>
          <Link to={`${homePath}#integrationen`} className="btn btn-primary">{lang === 'en' ? 'View all integrations' : 'Alle Integrationen ansehen'}</Link>
        </div>
      </div>
    );
  }

  const catName = integration.category.name[lang] || integration.category.name.de;
  const pageTitle = featured ? featured.title[lang] : `${integration.name} — NeXifyAI`;
  const metaDesc = featured ? featured.meta[lang] : (lang === 'de' ? `NeXifyAI integriert KI-Agenten mit ${integration.name} für automatisierte Geschäftsprozesse.` : lang === 'nl' ? `NeXifyAI integreert AI-agenten met ${integration.name} voor geautomatiseerde bedrijfsprocessen.` : `NeXifyAI integrates AI agents with ${integration.name} for automated business processes.`);
  const heroText = featured ? featured.hero[lang] : (lang === 'de' ? `${integration.name} intelligent automatisieren.` : lang === 'nl' ? `${integration.name} intelligent automatiseren.` : `Intelligently automate ${integration.name}.`);
  const usecases = featured ? featured.usecases[lang] : [];
  const faq = featured ? featured.faq[lang] : [];
  const combined = featured ? featured.combinedWith : [];

  const labels = {
    de: { usecases: 'Anwendungsfälle', how: 'So funktioniert die Anbindung', combined: 'Häufig kombiniert mit', faq: 'Häufige Fragen', cta: 'Integration besprechen', ctaSub: 'Kostenlose Erstberatung — wir prüfen Ihre Anbindung.', category: 'Kategorie', protocols: 'Unterstützte Protokolle', backAll: 'Alle Integrationen', steps: [{ t: 'Analyse', d: 'Wir analysieren Ihre bestehende Systemlandschaft und definieren die Integrationsanforderungen.' },{ t: 'Konfiguration', d: 'API-Anbindung, Authentifizierung und Daten-Mapping werden konfiguriert.' },{ t: 'Testing', d: 'Umfassende Tests mit Ihren realen Daten in einer sicheren Staging-Umgebung.' },{ t: 'Go-Live', d: 'Produktiv-Deployment mit Monitoring, Alerting und kontinuierlicher Optimierung.' }], generic: [{ title: 'Prozessautomation', desc: 'KI-Agenten automatisieren wiederkehrende Aufgaben und optimieren Workflows rund um ' + (integration?.name || '') + '.' },{ title: 'Datensynchronisation', desc: 'Bidirektionaler Datenaustausch in Echtzeit zwischen ' + (integration?.name || '') + ' und Ihren weiteren Systemen.' },{ title: 'Intelligente Analysen', desc: 'Automatisierte Auswertungen und Handlungsempfehlungen basierend auf ' + (integration?.name || '') + '-Daten.' }] },
    nl: { usecases: 'Toepassingen', how: 'Zo werkt de koppeling', combined: 'Vaak gecombineerd met', faq: 'Veelgestelde vragen', cta: 'Integratie bespreken', ctaSub: 'Gratis eerste advies — wij controleren uw koppeling.', category: 'Categorie', protocols: 'Ondersteunde protocollen', backAll: 'Alle integraties', steps: [{ t: 'Analyse', d: 'Wij analyseren uw bestaande systeemlandschap en definiëren de integratievereisten.' },{ t: 'Configuratie', d: 'API-koppeling, authenticatie en datamapping worden geconfigureerd.' },{ t: 'Testen', d: 'Uitgebreide tests met uw werkelijke data in een veilige staging-omgeving.' },{ t: 'Go-live', d: 'Productie-deployment met monitoring, alerting en continue optimalisatie.' }], generic: [{ title: 'Procesautomatisering', desc: 'AI-agenten automatiseren terugkerende taken en optimaliseren workflows rondom ' + (integration?.name || '') + '.' },{ title: 'Datasynchronisatie', desc: 'Bidirectionele data-uitwisseling in realtime tussen ' + (integration?.name || '') + ' en uw andere systemen.' },{ title: 'Intelligente analyses', desc: 'Geautomatiseerde evaluaties en actieaanbevelingen op basis van ' + (integration?.name || '') + '-data.' }] },
    en: { usecases: 'Use Cases', how: 'How the integration works', combined: 'Frequently combined with', faq: 'Frequently asked questions', cta: 'Discuss integration', ctaSub: 'Free initial consultation — we evaluate your connection.', category: 'Category', protocols: 'Supported protocols', backAll: 'All integrations', steps: [{ t: 'Analysis', d: 'We analyze your existing system landscape and define integration requirements.' },{ t: 'Configuration', d: 'API connection, authentication, and data mapping are configured.' },{ t: 'Testing', d: 'Comprehensive tests with your real data in a secure staging environment.' },{ t: 'Go-live', d: 'Production deployment with monitoring, alerting, and continuous optimization.' }], generic: [{ title: 'Process automation', desc: 'AI agents automate recurring tasks and optimize workflows around ' + (integration?.name || '') + '.' },{ title: 'Data synchronization', desc: 'Bidirectional real-time data exchange between ' + (integration?.name || '') + ' and your other systems.' },{ title: 'Intelligent analytics', desc: 'Automated evaluations and action recommendations based on ' + (integration?.name || '') + ' data.' }] },
  };
  const l = labels[lang] || labels.de;
  const displayUsecases = usecases.length > 0 ? usecases : l.generic;

  return (
    <div className="legal-page" data-testid="integration-detail-page">
      <Helmet>
        <title>{pageTitle} — NeXifyAI</title>
        <meta name="description" content={metaDesc} />
        <link rel="canonical" href={`${API}/integrationen/${slug}`} />
      </Helmet>

      {/* Navigation */}
      <nav className="intd-nav" data-testid="intd-nav">
        <div className="container">
          <div className="intd-nav-inner">
            <Link to={homePath} className="intd-logo-link" data-testid="intd-logo">
              <img src="/icon-mark.svg" alt="" width="28" height="28" />
              <span className="intd-logo-text">NeXify<span className="intd-logo-accent">AI</span></span>
            </Link>
            <Link to={`${homePath}#integrationen`} className="intd-back" data-testid="intd-back">
              <I n="arrow_back" /> {l.backAll}
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="intd-hero" data-testid="intd-hero">
        <div className="container">
          <motion.div className="intd-hero-inner" initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            <div className="intd-breadcrumb">
              <Link to={`${homePath}#integrationen`}>{l.backAll}</Link>
              <I n="chevron_right" />
              <span>{catName}</span>
              <I n="chevron_right" />
              <span>{integration.name}</span>
            </div>
            <div className="intd-hero-content">
              <div className="intd-hero-icon" style={{ borderColor: featured?.color ? `${featured.color}33` : 'rgba(255,155,122,0.15)' }}>
                <I n={featured?.logo || integration.category.icon} c="intd-hero-icon-inner" />
              </div>
              <div>
                <span className="label" style={{ display: 'block', marginBottom: 8 }}>{catName}</span>
                <h1 className="intd-h1" data-testid="intd-title">{pageTitle}</h1>
                <p className="intd-hero-desc">{heroText}</p>
                <div className="intd-hero-meta">
                  <span className="intd-meta-chip"><I n={integration.category.icon} /> {catName}</span>
                  <span className="intd-meta-chip"><I n="api" /> REST API</span>
                  <span className="intd-meta-chip"><I n="lock" /> OAuth 2.0</span>
                  <span className="intd-meta-chip"><I n="verified_user" /> DSGVO</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="intd-section" data-testid="intd-usecases">
        <div className="container">
          <motion.h2 className="intd-section-title" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <I n="lightbulb" c="intd-section-icon" /> {l.usecases}
          </motion.h2>
          <div className="intd-usecases-grid">
            {displayUsecases.map((uc, i) => (
              <motion.div key={i} className="intd-usecase-card" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} whileHover={{ y: -4 }}>
                <div className="intd-usecase-num">{String(i + 1).padStart(2, '0')}</div>
                <h3>{uc.title}</h3>
                <p>{uc.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="intd-section intd-section-dark" data-testid="intd-process">
        <div className="container">
          <motion.h2 className="intd-section-title" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <I n="route" c="intd-section-icon" /> {l.how}
          </motion.h2>
          <div className="intd-process-grid">
            {l.steps.map((step, i) => (
              <motion.div key={i} className="intd-process-step" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
                <div className="intd-process-num">{String(i + 1).padStart(2, '0')}</div>
                <h3>{step.t}</h3>
                <p>{step.d}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Combined with */}
      {combined.length > 0 && (
        <section className="intd-section" data-testid="intd-combined">
          <div className="container">
            <motion.h2 className="intd-section-title" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
              <I n="link" c="intd-section-icon" /> {l.combined}
            </motion.h2>
            <div className="intd-combined-grid">
              {combined.map(cSlug => {
                const ci = getIntegrationBySlug(cSlug);
                if (!ci) return null;
                const cf = getFeaturedDetail(cSlug);
                return (
                  <Link key={cSlug} to={`/integrationen/${cSlug}`} className="intd-combined-card" data-testid={`intd-combined-${cSlug}`}>
                    <div className="intd-combined-icon" style={{ borderColor: cf?.color ? `${cf.color}33` : 'rgba(255,155,122,0.15)' }}>
                      <I n={cf?.logo || ci.category.icon} />
                    </div>
                    <div className="intd-combined-name">{ci.name}</div>
                    <div className="intd-combined-cat">{ci.category.name[lang] || ci.category.name.de}</div>
                  </Link>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* FAQ */}
      {faq.length > 0 && (
        <section className="intd-section intd-section-dark" data-testid="intd-faq">
          <div className="container">
            <motion.h2 className="intd-section-title" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
              <I n="help" c="intd-section-icon" /> {l.faq}
            </motion.h2>
            <div className="intd-faq-list">
              {faq.map((f, i) => (
                <motion.div key={i} className={`faq-item ${faqOpen === i ? 'open' : ''}`} variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
                  <button type="button" className="faq-q" onClick={() => setFaqOpen(faqOpen === i ? -1 : i)} data-testid={`intd-faq-q-${i}`}>
                    <span>{f.q}</span>
                    <I n={faqOpen === i ? 'expand_less' : 'expand_more'} />
                  </button>
                  <AnimatePresence>
                    {faqOpen === i && (
                      <motion.div className="faq-a" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                        <div className="faq-a-inner">{f.a}</div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="intd-cta-section" data-testid="intd-cta">
        <div className="container">
          <motion.div className="intd-cta-box" variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2>{integration.name} {l.cta.split(' ').slice(0,1).join(' ')} — {l.cta}</h2>
            <p>{l.ctaSub}</p>
            <div className="intd-cta-actions">
              <Link to={`${homePath}#kontakt`} className="btn btn-primary btn-lg btn-glow" data-testid="intd-cta-contact">
                {l.cta} <I n="arrow_forward" />
              </Link>
              <Link to={`${homePath}#preise`} className="btn btn-secondary btn-lg" data-testid="intd-cta-pricing">
                {lang === 'en' ? 'View pricing' : lang === 'nl' ? 'Tarieven bekijken' : 'Tarife ansehen'}
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* More integrations */}
      <section className="intd-section" data-testid="intd-more">
        <div className="container">
          <h2 className="intd-section-title" style={{ marginBottom: 32 }}>
            {lang === 'en' ? 'More integrations' : lang === 'nl' ? 'Meer integraties' : 'Weitere Integrationen'}
          </h2>
          <div className="intd-more-grid">
            {INTEGRATION_CATEGORIES.filter(c => c.key !== integration.category.key).slice(0, 4).map(cat => (
              <div key={cat.key} className="intd-more-cat">
                <h3><I n={cat.icon} c="intd-more-cat-icon" /> {cat.name[lang] || cat.name.de}</h3>
                <div className="intd-more-items">
                  {cat.items.slice(0, 5).map(item => (
                    <Link key={item.slug} to={`/integrationen/${item.slug}`} className="intd-more-link" data-testid={`intd-more-${item.slug}`}>
                      {item.name}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: 40 }}>
            <Link to={`${homePath}#integrationen`} className="btn btn-secondary" data-testid="intd-all-link">
              <I n="grid_view" /> {l.backAll} ({lang === 'en' ? '400+' : '400+'})
            </Link>
          </div>
        </div>
      </section>

      {/* Footer mini */}
      <footer className="intd-footer">
        <div className="container">
          <div className="intd-footer-inner">
            <span>&copy; {new Date().getFullYear()} NeXify Automate</span>
            <div className="intd-footer-links">
              <Link to={`/${lang}/impressum`}>{lang === 'en' ? 'Imprint' : 'Impressum'}</Link>
              <Link to={`/${lang}/${lang === 'nl' ? 'privacybeleid' : lang === 'en' ? 'privacy' : 'datenschutz'}`}>{lang === 'en' ? 'Privacy' : lang === 'nl' ? 'Privacy' : 'Datenschutz'}</Link>
              <Link to={`/${lang}/${lang === 'nl' ? 'voorwaarden' : lang === 'en' ? 'terms' : 'agb'}`}>{lang === 'en' ? 'Terms' : 'AGB'}</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

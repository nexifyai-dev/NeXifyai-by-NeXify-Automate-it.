import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';

// Company Data - Fixed according to project brief
const COMPANY = {
  name: "NeXifyAI by NeXify",
  tagline: "Chat it. Automate it.",
  legalName: "NeXify Automate",
  ceo: "Pascal Courbois, Geschäftsführer",
  addresses: {
    de: {
      street: "Wallstraße 9",
      city: "41334 Nettetal-Kaldenkirchen",
      country: "Deutschland"
    },
    nl: {
      street: "Graaf van Loonstraat 1E",
      city: "5921 JA Venlo",
      country: "Niederlande"
    }
  },
  phone: "+31 6 133 188 56",
  email: "support@nexify-automate.com",
  website: "nexify-automate.com",
  kvk: "90483944",
  vatId: "NL865786276B01"
};

// API URL
const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Material Icon Component
const Icon = ({ name, className = '' }) => (
  <span className={`material-symbols-outlined ${className}`}>{name}</span>
);

// Navigation Component
const Navigation = ({ onOpenChat }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: 'Lösungen', href: '#loesungen' },
    { label: 'Anwendungsfälle', href: '#use-cases' },
    { label: 'Prozess', href: '#prozess' },
    { label: 'Integrationen', href: '#integrationen' },
    { label: 'Preise', href: '#preise' },
    { label: 'FAQ', href: '#faq' },
  ];

  return (
    <nav className="nav" data-testid="navigation">
      <div className="nav-container container">
        <a href="#hero" className="nav-logo" data-testid="nav-logo">
          <span className="nav-logo-mark"></span>
          NeXifyAI
        </a>
        
        {/* Desktop Navigation */}
        <div className="nav-links">
          {navLinks.map(link => (
            <a key={link.href} href={link.href} className="nav-link">
              {link.label}
            </a>
          ))}
        </div>

        <div className="nav-actions">
          <button 
            className="btn btn-primary nav-cta"
            onClick={onOpenChat}
            data-testid="nav-cta-button"
          >
            Gespräch buchen
          </button>
          
          {/* Mobile Menu Button */}
          <button 
            className="nav-mobile-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Menü schließen' : 'Menü öffnen'}
            aria-expanded={mobileMenuOpen}
            data-testid="mobile-menu-toggle"
          >
            <Icon name={mobileMenuOpen ? 'close' : 'menu'} />
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="nav-mobile-menu" data-testid="mobile-menu">
            {navLinks.map(link => (
              <a 
                key={link.href} 
                href={link.href} 
                className="nav-mobile-link"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <button 
              className="btn btn-primary nav-mobile-cta"
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenChat();
              }}
            >
              Gespräch buchen
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

// Hero Section
const HeroSection = ({ onOpenChat, onScrollToContact }) => (
  <section id="hero" className="hero architectural-grid" data-testid="hero-section">
    <div className="container hero-grid">
      <div className="hero-content">
        <span className="hero-label">NeXifyAI by NeXify</span>
        <h1 className="hero-title">
          Aus Chats werden <span className="text-primary">Prozesse.</span><br />
          Aus Prozessen wird Wachstum.
        </h1>
        <p className="hero-description">
          Wir bauen die architektonische Brücke zwischen generativer KI und operativer Exzellenz. 
          Enterprise-Lösungen für den DACH-Mittelstand – präzise, sicher und skalierbar.
        </p>
        <div className="hero-actions">
          <button 
            className="btn btn-primary"
            onClick={onScrollToContact}
            data-testid="hero-cta-primary"
          >
            POTENZIAL ANALYSIEREN
            <Icon name="arrow_forward" />
          </button>
          <a href="#loesungen" className="btn btn-secondary" data-testid="hero-cta-secondary">
            LÖSUNGEN ANSEHEN
          </a>
        </div>
        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-title">Ausrichtung</div>
            <div className="hero-stat-value">Strategische Integration</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-title">Fokus</div>
            <div className="hero-stat-value">Operative Wertschöpfung</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-title">Leistung</div>
            <div className="hero-stat-value">Skalierbare Workflows</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-title">Delivery</div>
            <div className="hero-stat-value">Pünktlich & Präzise</div>
          </div>
        </div>
      </div>
      <div className="hero-visual">
        <ArchitecturePanel />
      </div>
    </div>
  </section>
);

// Architecture Panel Component (Responsive)
const ArchitecturePanel = () => (
  <div className="architecture-panel glass-panel" data-testid="architecture-panel">
    <div className="architecture-inner">
      <div className="architecture-header">
        <div className="architecture-icon">
          <Icon name="account_tree" />
        </div>
        <div className="architecture-title">
          <div className="architecture-code">CORE_ENGINE_V4</div>
          <div className="architecture-name">Inferenz-Architektur</div>
        </div>
      </div>
      
      <div className="architecture-progress">
        <div className="architecture-progress-bar"></div>
      </div>
      
      <div className="architecture-modules">
        <div className="architecture-module">
          <Icon name="psychology" />
          <span>LLM</span>
        </div>
        <div className="architecture-module active">
          <Icon name="memory" />
          <span>Memory</span>
        </div>
        <div className="architecture-module">
          <Icon name="hub" />
          <span>API</span>
        </div>
      </div>
      
      <div className="architecture-flow">
        <div className="architecture-node">Input</div>
        <div className="architecture-connector"></div>
        <div className="architecture-node highlight">Processing</div>
        <div className="architecture-connector"></div>
        <div className="architecture-node">Output</div>
      </div>
    </div>
    <div className="architecture-decor-top"></div>
    <div className="architecture-decor-bottom"></div>
  </div>
);

// Solutions Grid Section
const SolutionsSection = () => {
  const solutions = [
    {
      icon: 'smart_toy',
      title: 'AI-Assistenz',
      description: 'Kontextbewusste Co-Piloten für spezifische Fachabteilungen, integriert in bestehende Toolsets.'
    },
    {
      icon: 'settings_input_component',
      title: 'Automationen',
      description: 'End-to-End Workflow Automatisierung durch agentische KI-Systeme ohne Medienbrüche.'
    },
    {
      icon: 'hub',
      title: 'Integrationen',
      description: 'Nahtlose Anbindung an SAP, Salesforce und Microsoft-Ecosysteme mit höchster Datensicherheit.'
    },
    {
      icon: 'menu_book',
      title: 'Interne Wissenssysteme',
      description: 'Semantic Search & RAG-Architekturen für sofortigen Zugriff auf das gesamte Firmenwissen.'
    },
    {
      icon: 'description',
      title: 'Dokumentenautomation',
      description: 'KI-gestützte Extraktion und Validierung komplexer Vertragsdaten und Dokumente.'
    },
    {
      icon: 'corporate_fare',
      title: 'Enterprise Solutions',
      description: 'Custom-Modelle und On-Premise Deployments für maximale Souveränität Ihrer Daten.'
    }
  ];

  return (
    <section id="loesungen" className="solutions-section" data-testid="solutions-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Infrastruktur für Intelligenz</h2>
          <p className="section-description">
            Keine Spielereien, sondern fundamentale Fähigkeiten für die moderne Enterprise-Architektur.
          </p>
        </div>
        <div className="solutions-grid">
          {solutions.map((solution, idx) => (
            <div key={idx} className="solution-card" data-testid={`solution-card-${idx}`}>
              <Icon name={solution.icon} className="solution-icon" />
              <h3 className="solution-title">{solution.title}</h3>
              <p className="solution-description">{solution.description}</p>
              <div className="solution-indicator"></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Use Cases Section
const UseCasesSection = () => (
  <section id="use-cases" className="use-cases-section" data-testid="use-cases-section">
    <div className="container">
      <div className="section-header">
        <div>
          <h2 className="section-title">Operative Realität</h2>
          <p className="section-description">
            Konkrete Implementierungsszenarien, die heute bereits Produktivität freisetzen.
          </p>
        </div>
      </div>
      <div className="use-cases-grid">
        <div className="use-case-card large">
          <div className="use-case-bg-icon">
            <Icon name="analytics" />
          </div>
          <div className="use-case-content">
            <span className="use-case-label">Effizienz-Boost</span>
            <h3 className="use-case-title">Vertriebsanfragen & Qualifizierung</h3>
            <p className="use-case-description">
              Automatisierte Triage eingehender Leads mit CRM-Abgleich und automatisierter Terminkoordination.
            </p>
          </div>
          <div className="use-case-dashboard">
            <div className="dashboard-card">
              <div className="dashboard-line"></div>
              <div className="dashboard-line short"></div>
              <div className="dashboard-bar"></div>
            </div>
            <div className="dashboard-card">
              <div className="dashboard-avatar"></div>
              <div className="dashboard-metric"></div>
            </div>
          </div>
        </div>
        
        <div className="use-case-card">
          <Icon name="notes" className="use-case-icon" />
          <h3 className="use-case-title">Angebotsstandardisierung</h3>
          <p className="use-case-description">
            Präzise Angebotserstellung aus unstrukturierten Projektnotizen innerhalb von Sekunden.
          </p>
        </div>
        
        <div className="use-case-card">
          <Icon name="database" className="use-case-icon" />
          <h3 className="use-case-title">Wissensbestände</h3>
          <p className="use-case-description">
            Zentralisierung von Silo-Wissen für den Kundensupport und technischen Service.
          </p>
        </div>
        
        <div className="use-case-card wide">
          <div className="use-case-split">
            <div>
              <h3 className="use-case-title">CRM/ERP Orchestrierung</h3>
              <p className="use-case-description">
                Die KI agiert als intelligenter Agent zwischen Ihren Datensilos und führt Aktionen autonom in Drittsystemen aus.
              </p>
            </div>
            <div className="orchestration-visual">
              <div className="orchestration-circle">
                <Icon name="sync_alt" />
                <span className="orchestration-label top">SAP</span>
                <span className="orchestration-label bottom">HubSpot</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);

// Process Section
const ProcessSection = () => {
  const steps = [
    {
      num: '01',
      title: 'Analyse',
      description: 'Status-quo Audit Ihrer Prozesse und Identifikation der größten Hebel für KI-Automation.',
      progress: 1
    },
    {
      num: '02',
      title: 'Architektur',
      description: 'Entwurf der technischen Infrastruktur unter Berücksichtigung von Governance und IT-Security.',
      progress: 2
    },
    {
      num: '03',
      title: 'Umsetzung',
      description: 'Iterative Entwicklung und Integration in Ihre Toolchain mit klarem Fokus auf UI/UX.',
      progress: 3
    },
    {
      num: '04',
      title: 'Optimierung',
      description: 'Kontinuierliches Monitoring, Feedback-Loop und Performance-Tuning der Modelle.',
      progress: 4
    }
  ];

  return (
    <section id="prozess" className="process-section architectural-grid" data-testid="process-section">
      <div className="container">
        <div className="section-header centered">
          <span className="section-label">Workflow</span>
          <h2 className="section-title">Von der Vision zum Deployment</h2>
        </div>
        <div className="process-grid">
          {steps.map((step, idx) => (
            <div key={idx} className="process-step" data-testid={`process-step-${idx}`}>
              <div className="process-num">{step.num}</div>
              <h4 className="process-title">{step.title}</h4>
              <p className="process-description">{step.description}</p>
              <div className="process-progress">
                {[1, 2, 3, 4].map(i => (
                  <div 
                    key={i} 
                    className={`process-bar ${i <= step.progress ? 'active' : ''}`}
                  ></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Integrations Section
const IntegrationsSection = () => {
  const integrations = ['Microsoft 365', 'HubSpot', 'Salesforce', 'SAP S/4HANA'];
  const apis = ['REST API', 'WEBHOOKS', 'PYTHON SDK'];

  return (
    <section id="integrationen" className="integrations-section" data-testid="integrations-section">
      <div className="container integrations-container">
        <div className="integrations-info">
          <h2 className="section-title">Perfekte Symbiose</h2>
          <p className="section-description">
            Unsere Agenten sprechen die Sprache Ihrer bestehenden Software. 
            Keine neuen Silos, sondern intelligente Vernetzung.
          </p>
          <div className="api-badges">
            {apis.map(api => (
              <span key={api} className="api-badge">{api}</span>
            ))}
          </div>
        </div>
        <div className="integrations-grid">
          {integrations.map(name => (
            <div key={name} className="integration-card" data-testid={`integration-${name.replace(/\s/g, '-').toLowerCase()}`}>
              <span className="integration-name">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Governance Section
const GovernanceSection = () => {
  const features = [
    {
      icon: 'gavel',
      title: 'Rechtssicher im DACH-Raum',
      description: 'Vollständige DSGVO-Konformität, Datenspeicherung in zertifizierten deutschen Rechenzentren (Frankfurt/München).'
    },
    {
      icon: 'shield_person',
      title: 'Role-Based Access Control (RBAC)',
      description: 'Präzise Steuerung, welche KI-Modelle Zugriff auf welche Unternehmensdaten haben – auf Benutzerebene.'
    },
    {
      icon: 'policy',
      title: 'Audit-Log Management',
      description: 'Lückenlose Protokollierung aller KI-Entscheidungen und Datenzugriffe für maximale Transparenz.'
    }
  ];

  const certifications = [
    { label: 'Standard', title: 'GDPR/DSGVO', description: '100% Datenschutzkonform.', highlight: false },
    { label: 'Barrierefreiheit', title: 'WCAG 2.2', description: 'Barrierefreie Schnittstellen.', highlight: false },
    { label: 'Zielsetzung', title: 'ISO 27001', description: 'Informationssicherheit angestrebt.', highlight: true },
    { label: 'Roadmap', title: 'SOC 2 Type II', description: 'In Vorbereitung.', highlight: true }
  ];

  return (
    <section className="governance-section" data-testid="governance-section">
      <div className="container governance-container">
        <div className="governance-features">
          <h2 className="section-title">Governance & Compliance</h2>
          <div className="governance-list">
            {features.map((feature, idx) => (
              <div key={idx} className="governance-item">
                <div className="governance-icon">
                  <Icon name={feature.icon} />
                </div>
                <div>
                  <h4 className="governance-item-title">{feature.title}</h4>
                  <p className="governance-item-description">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="certifications-grid">
          {certifications.map((cert, idx) => (
            <div key={idx} className={`certification-card ${cert.highlight ? 'highlight' : ''}`}>
              <span className="certification-label">{cert.label}</span>
              <div className="certification-title">{cert.title}</div>
              <p className="certification-description">{cert.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Pricing Section
const PricingSection = ({ onScrollToContact }) => {
  const plans = [
    {
      name: 'Starter',
      price: '€1.900',
      period: '/Mo',
      features: [
        '2 Custom KI-Agenten',
        'Shared Infrastructure',
        'Email Support (48h)'
      ],
      cta: 'JETZT STARTEN',
      highlight: false
    },
    {
      name: 'Growth',
      price: '€4.500',
      period: '/Mo',
      features: [
        '10 Custom KI-Agenten',
        'Private Cloud Deployment',
        'Priority Support (4h)',
        'CRM/ERP Integration-Kit'
      ],
      cta: 'KOSTENLOS TESTEN',
      highlight: true,
      badge: 'Empfehlung'
    },
    {
      name: 'Enterprise',
      price: 'Individuell',
      period: '',
      features: [
        'Unlimitierte KI-Agenten',
        'On-Premise Option',
        'Dedicated Account Manager',
        'Custom LLM Training'
      ],
      cta: 'ANFRAGE SENDEN',
      highlight: false
    }
  ];

  return (
    <section id="preise" className="pricing-section" data-testid="pricing-section">
      <div className="container">
        <div className="section-header centered">
          <h2 className="section-title">Transparente Architektur-Tarife</h2>
          <p className="section-description">
            Wählen Sie das Fundament, das zu Ihrer Unternehmensgröße passt.
          </p>
        </div>
        <div className="pricing-grid">
          {plans.map((plan, idx) => (
            <div 
              key={idx} 
              className={`pricing-card ${plan.highlight ? 'highlight' : ''}`}
              data-testid={`pricing-card-${plan.name.toLowerCase()}`}
            >
              {plan.badge && <span className="pricing-badge">{plan.badge}</span>}
              <div className="pricing-name">{plan.name}</div>
              <div className="pricing-price">
                {plan.price}
                <span className="pricing-period">{plan.period}</span>
              </div>
              <ul className="pricing-features">
                {plan.features.map((feature, fIdx) => (
                  <li key={fIdx} className="pricing-feature">
                    <Icon name="check_circle" className="pricing-check" />
                    {feature}
                  </li>
                ))}
              </ul>
              <button 
                className={`btn ${plan.highlight ? 'btn-primary' : 'btn-secondary'} pricing-cta`}
                onClick={onScrollToContact}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// FAQ Section
const FAQSection = () => {
  const [openIndex, setOpenIndex] = useState(0);

  const faqs = [
    {
      question: 'Werden unsere Daten zum Training der Modelle genutzt?',
      answer: 'Nein. Alle Kundendaten verbleiben in isolierten Instanzen. Wir nutzen Ihre geschäftskritischen Daten niemals zum Training allgemeiner Sprachmodelle. Ihre Daten bleiben Ihr Eigentum und werden ausschließlich für Ihre spezifischen Anwendungsfälle verwendet.'
    },
    {
      question: 'Wie lange dauert eine Standard-Implementierung?',
      answer: 'Die Implementierungsdauer variiert je nach Komplexität. Ein einfacher KI-Assistent kann innerhalb von 2-4 Wochen produktiv sein. Komplexere Integrationen mit mehreren Systemen (CRM, ERP) benötigen typischerweise 6-12 Wochen. Im Erstgespräch erstellen wir einen realistischen Zeitplan für Ihr Projekt.'
    },
    {
      question: 'Ist die Lösung mit SAP kompatibel?',
      answer: 'Ja. Wir bieten native Konnektoren für SAP S/4HANA und SAP Business One. Die Integration erfolgt über standardisierte APIs und berücksichtigt alle relevanten Sicherheits- und Berechtigungskonzepte. Auch Legacy-SAP-Systeme können über Middleware-Lösungen angebunden werden.'
    },
    {
      question: 'Wie hoch ist die Fehlerquote (Halluzinationen)?',
      answer: 'Durch den Einsatz von RAG-Architekturen (Retrieval-Augmented Generation) und strukturierten Validierungsschritten minimieren wir Halluzinationen erheblich. Bei faktenbasierten Aufgaben liegt die Genauigkeit typischerweise über 95%. Kritische Prozesse können zusätzlich mit Human-in-the-Loop-Mechanismen abgesichert werden.'
    },
    {
      question: 'Welche Datenschutz-Garantien gibt es?',
      answer: 'Alle Daten werden ausschließlich in zertifizierten deutschen Rechenzentren (Frankfurt/München) verarbeitet. Wir sind vollständig DSGVO-konform und können auf Wunsch Auftragsverarbeitungsverträge (AVV) bereitstellen. Für besonders sensible Daten bieten wir On-Premise-Deployments an.'
    }
  ];

  return (
    <section id="faq" className="faq-section" data-testid="faq-section">
      <div className="container faq-container">
        <div className="faq-info">
          <h2 className="section-title">Häufige Fragen</h2>
          <p className="section-description">
            Details zur technischen Umsetzung, Datensicherheit und Integration.
          </p>
        </div>
        <div className="faq-list">
          {faqs.map((faq, idx) => (
            <div 
              key={idx} 
              className={`faq-item ${openIndex === idx ? 'open' : ''}`}
              data-testid={`faq-item-${idx}`}
            >
              <button 
                type="button"
                className="faq-question"
                onClick={() => setOpenIndex(openIndex === idx ? -1 : idx)}
                aria-expanded={openIndex === idx}
              >
                <span>{faq.question}</span>
                <Icon name={openIndex === idx ? 'expand_less' : 'expand_more'} />
              </button>
              {openIndex === idx && (
                <div className="faq-answer">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Contact Form Section
const ContactSection = () => {
  const [formData, setFormData] = useState({
    vorname: '',
    nachname: '',
    email: '',
    nachricht: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);
  const formRef = useRef(null);

  const validate = () => {
    const newErrors = {};
    if (formData.vorname.trim().length < 2) {
      newErrors.vorname = 'Bitte geben Sie Ihren Vornamen ein';
    }
    if (formData.nachname.trim().length < 2) {
      newErrors.nachname = 'Bitte geben Sie Ihren Nachnamen ein';
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Bitte geben Sie eine gültige E-Mail-Adresse ein';
    }
    if (formData.nachricht.trim().length < 10) {
      newErrors.nachricht = 'Bitte beschreiben Sie Ihr Anliegen (mind. 10 Zeichen)';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const response = await fetch(`${API_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setSubmitStatus({ type: 'success', message: result.message });
        setFormData({ vorname: '', nachname: '', email: '', nachricht: '' });
      } else {
        throw new Error(result.detail || 'Übertragung fehlgeschlagen');
      }
    } catch (error) {
      setSubmitStatus({ 
        type: 'error', 
        message: 'Entschuldigung, es gab ein technisches Problem. Bitte versuchen Sie es später erneut oder kontaktieren Sie uns direkt.' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  return (
    <section id="kontakt" className="contact-section" data-testid="contact-section">
      <div className="container contact-container">
        <div className="contact-info">
          <h2 className="section-title large">Bereit für die Architektur des Wachstums?</h2>
          <p className="section-description">
            Lassen Sie uns in einem 30-minütigen Gespräch Ihre operativen Potenziale identifizieren.
          </p>
          <div className="contact-benefits">
            <div className="contact-benefit">
              <Icon name="verified" />
              <span>Kostenloses Erstgespräch</span>
            </div>
            <div className="contact-benefit">
              <Icon name="verified" />
              <span>Prozess-Audit inklusive</span>
            </div>
            <div className="contact-benefit">
              <Icon name="verified" />
              <span>Unverbindliche Beratung</span>
            </div>
          </div>
        </div>
        
        <div className="contact-form-container">
          <form ref={formRef} onSubmit={handleSubmit} className="contact-form" data-testid="contact-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="vorname" className="form-label">Vorname</label>
                <input
                  type="text"
                  id="vorname"
                  name="vorname"
                  value={formData.vorname}
                  onChange={handleChange}
                  className={`form-input ${errors.vorname ? 'error' : ''}`}
                  disabled={isSubmitting}
                  data-testid="input-vorname"
                />
                {errors.vorname && <span className="form-error">{errors.vorname}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="nachname" className="form-label">Nachname</label>
                <input
                  type="text"
                  id="nachname"
                  name="nachname"
                  value={formData.nachname}
                  onChange={handleChange}
                  className={`form-input ${errors.nachname ? 'error' : ''}`}
                  disabled={isSubmitting}
                  data-testid="input-nachname"
                />
                {errors.nachname && <span className="form-error">{errors.nachname}</span>}
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="email" className="form-label">Geschäftliche E-Mail</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`form-input ${errors.email ? 'error' : ''}`}
                disabled={isSubmitting}
                data-testid="input-email"
              />
              {errors.email && <span className="form-error">{errors.email}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="nachricht" className="form-label">Nachricht</label>
              <textarea
                id="nachricht"
                name="nachricht"
                rows="4"
                value={formData.nachricht}
                onChange={handleChange}
                className={`form-textarea ${errors.nachricht ? 'error' : ''}`}
                disabled={isSubmitting}
                data-testid="input-nachricht"
              ></textarea>
              {errors.nachricht && <span className="form-error">{errors.nachricht}</span>}
            </div>
            <button 
              type="submit" 
              className="btn btn-primary contact-submit"
              disabled={isSubmitting}
              data-testid="contact-submit-button"
            >
              {isSubmitting ? (
                <>
                  <span className="spinner"></span>
                  WIRD GESENDET...
                </>
              ) : (
                'STRATEGIEGESPRÄCH ANFORDERN'
              )}
            </button>
            
            {submitStatus && (
              <div className={`form-status ${submitStatus.type}`} data-testid="form-status">
                <Icon name={submitStatus.type === 'success' ? 'check_circle' : 'error'} />
                {submitStatus.message}
              </div>
            )}
          </form>
        </div>
      </div>
    </section>
  );
};

// Advisory Chat Modal
const AdvisoryChatModal = ({ isOpen, onClose }) => {
  const modalRef = useRef(null);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
      modalRef.current?.focus();
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  const starterQuestions = [
    'Wie kann KI unseren Vertrieb unterstützen?',
    'Welche Prozesse eignen sich für Automation?',
    'Wie sicher sind unsere Daten bei Ihnen?',
    'Was unterscheidet Sie von ChatGPT-Wrappern?'
  ];

  return (
    <div 
      className="modal-overlay" 
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="chat-modal-title"
      data-testid="advisory-modal"
    >
      <div 
        className="modal-content advisory-modal"
        ref={modalRef}
        tabIndex={-1}
      >
        <button 
          className="modal-close"
          onClick={onClose}
          aria-label="Schließen"
          data-testid="modal-close-button"
        >
          <Icon name="close" />
        </button>
        
        <div className="advisory-grid">
          <div className="advisory-info">
            <h2 id="chat-modal-title" className="advisory-title">
              Wie können wir Ihnen helfen?
            </h2>
            <p className="advisory-description">
              Unser Advisory-System hilft Ihnen, den richtigen Einstieg in KI-gestützte Automation zu finden. 
              Wählen Sie eine Frage oder beschreiben Sie Ihr Anliegen.
            </p>
            
            <div className="starter-questions">
              {starterQuestions.map((question, idx) => (
                <button 
                  key={idx} 
                  className="starter-question"
                  onClick={() => {
                    // In future: send to chat
                    window.location.href = '#kontakt';
                    onClose();
                  }}
                >
                  {question}
                  <Icon name="arrow_forward" />
                </button>
              ))}
            </div>
            
            <div className="advisory-actions">
              <a href="#kontakt" className="btn btn-primary" onClick={onClose}>
                Projekt einschätzen lassen
              </a>
              <a href="#loesungen" className="btn btn-secondary" onClick={onClose}>
                Lösungen ansehen
              </a>
            </div>
          </div>
          
          <div className="advisory-preview">
            <div className="chat-preview">
              <div className="chat-header">
                <div className="chat-status">
                  <span className="status-dot online"></span>
                  <span>NeXifyAI Advisory</span>
                </div>
              </div>
              <div className="chat-messages">
                <div className="chat-message bot">
                  Willkommen! Ich bin der NeXifyAI Advisor. Wie kann ich Ihnen bei Ihrer KI-Strategie helfen?
                </div>
                <div className="chat-message user">
                  Wir möchten unseren Vertriebsprozess automatisieren.
                </div>
                <div className="chat-message bot">
                  Sehr gut! Vertriebsautomation ist einer unserer Kernbereiche. Darf ich fragen, welches CRM-System Sie aktuell nutzen?
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Footer Component
const Footer = () => (
  <footer className="footer" data-testid="footer">
    <div className="container">
      <div className="footer-grid">
        <div className="footer-company">
          <span className="footer-logo">NeXifyAI</span>
          <p className="footer-tagline">{COMPANY.tagline}</p>
          <p className="footer-legal-name">Ein Produkt von {COMPANY.legalName}</p>
          <div className="footer-contact-info">
            <p><strong>NL:</strong> {COMPANY.addresses.nl.street}, {COMPANY.addresses.nl.city}</p>
            <p><strong>DE:</strong> {COMPANY.addresses.de.street}, {COMPANY.addresses.de.city}</p>
            <p>Tel: <a href={`tel:${COMPANY.phone.replace(/\s/g, '')}`}>{COMPANY.phone}</a></p>
            <p>E-Mail: <a href={`mailto:${COMPANY.email}`}>{COMPANY.email}</a></p>
          </div>
        </div>
        
        <div className="footer-nav">
          <h5 className="footer-nav-title">Navigation</h5>
          <ul className="footer-links">
            <li><a href="#loesungen">Lösungen</a></li>
            <li><a href="#use-cases">Anwendungsfälle</a></li>
            <li><a href="#preise">Preise</a></li>
            <li><a href="#kontakt">Kontakt</a></li>
          </ul>
        </div>
        
        <div className="footer-nav">
          <h5 className="footer-nav-title">Rechtliches</h5>
          <ul className="footer-links">
            <li><a href="#impressum">Impressum</a></li>
            <li><a href="#datenschutz">Datenschutz</a></li>
            <li><a href="#agb">AGB</a></li>
          </ul>
          <div className="footer-legal-ids">
            <p>KvK: {COMPANY.kvk}</p>
            <p>USt-ID: {COMPANY.vatId}</p>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <span className="footer-copyright">
          © {new Date().getFullYear()} {COMPANY.legalName}. Alle Rechte vorbehalten.
        </span>
        <div className="footer-status">
          <span className="status-dot online"></span>
          <span>System Status: Optimal</span>
        </div>
      </div>
    </div>
  </footer>
);

// Chat Trigger Button
const ChatTrigger = ({ onClick }) => (
  <button 
    className="chat-trigger"
    onClick={onClick}
    aria-label="Architektur-Beratung öffnen"
    data-testid="chat-trigger"
  >
    <span className="chat-trigger-text">Architektur-Beratung</span>
    <span className="chat-trigger-icon">
      <Icon name="forum" />
    </span>
  </button>
);

// Main App Component
function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const openChat = useCallback(() => setIsChatOpen(true), []);
  const closeChat = useCallback(() => setIsChatOpen(false), []);
  
  const scrollToContact = useCallback(() => {
    document.getElementById('kontakt')?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  return (
    <div className="app">
      <Navigation onOpenChat={openChat} />
      
      <main>
        <HeroSection onOpenChat={openChat} onScrollToContact={scrollToContact} />
        <SolutionsSection />
        <UseCasesSection />
        <ProcessSection />
        <IntegrationsSection />
        <GovernanceSection />
        <PricingSection onScrollToContact={scrollToContact} />
        <FAQSection />
        <ContactSection />
      </main>
      
      <Footer />
      
      <ChatTrigger onClick={openChat} />
      <AdvisoryChatModal isOpen={isChatOpen} onClose={closeChat} />
    </div>
  );
}

export default App;

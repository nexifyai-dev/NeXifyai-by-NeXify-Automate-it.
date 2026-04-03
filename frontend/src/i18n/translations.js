/* ═══════════════════════════════════════════════
   NeXifyAI — Complete Translations (DE / NL / EN)
   Landing Page + Modals + Footer + Cookie
   ═══════════════════════════════════════════════ */
const t = {
de: {
  nav: { leistungen:'Leistungen', usecases:'Use Cases', appdev:'App-Entwicklung', integrationen:'Integrationen', tarife:'Tarife', faq:'FAQ', cta:'Gespräch buchen', menuOpen:'Menü öffnen', menuClose:'Menü schließen' },
  hero: {
    label:'NEXIFYAI BY NEXIFY',
    h1: ['Intelligente Agenten.', 'Operative', 'Exzellenz.'],
    desc:'NeXifyAI entwickelt KI-Agenten, die Ihre Geschäftsprozesse autonom orchestrieren — von der Kundeninteraktion bis zur Backend-Automatisierung. Keine Spielerei. Operative Realität.',
    cta1:'Strategiegespräch buchen', cta2:'Beratung starten',
    stats: [
      { title:'ENTERPRISE', value:'DACH B2B-Fokus' },
      { title:'AGENTEN', value:'Autonom & adaptiv' },
      { title:'INTEGRATION', value:'400+ Systeme' },
      { title:'COMPLIANCE', value:'DSGVO-konform' }
    ]
  },
  solutions: {
    label:'LEISTUNGEN', title:'Was unsere Agenten leisten',
    subtitle:'Jeder Agent wird spezifisch für Ihren operativen Kontext entwickelt — keine Templates, keine Kompromisse.',
    items: [
      { icon:'neurology', title:'KI-Assistenz & Beratung', desc:'Strategische KI-Beratung und Implementierung autonomer Agenten für Ihre spezifischen Geschäftsprozesse.' },
      { icon:'manufacturing', title:'Automationen & Workflows', desc:'End-to-End-Automatisierung von Geschäftsprozessen — von der Datenerfassung bis zur Entscheidungsfindung.' },
      { icon:'hub', title:'Integrationen & API', desc:'Nahtlose Anbindung an 400+ bestehende Systeme — CRM, ERP, Cloud-Dienste und proprietäre Schnittstellen.' },
      { icon:'school', title:'Wissenssysteme (RAG)', desc:'Intelligente Wissensdatenbanken mit Retrieval-Augmented Generation für präzise, kontextbewusste Antworten.' },
      { icon:'description', title:'Dokumentenautomation', desc:'Automatisierte Verarbeitung, Analyse und Generierung von Geschäftsdokumenten mit KI-Verständnis.' },
      { icon:'shield', title:'Enterprise Solutions', desc:'Skalierbare KI-Infrastruktur mit Enterprise-Grade Security, Compliance und dediziertem Support.' }
    ]
  },
  usecases: {
    label:'OPERATIVE REALITÄT', title:'Agenten in Aktion',
    subtitle:'Keine Theorie. Jeder Use Case basiert auf operativer Realität unserer Enterprise-Kunden.',
    items: [
      { icon:'support_agent', title:'Kundenservice-Agenten', desc:'Autonome First-Level-Resolution mit Eskalationslogik, Sentiment-Analyse und CRM-Integration. 80% Reduktion der Erstantwortzeit.', size:'lg' },
      { icon:'analytics', title:'Revenue Intelligence', desc:'Echtzeit-Analyse von Sales-Pipelines mit prädiktiver Bewertung.', size:'sm' },
      { icon:'inventory_2', title:'Supply-Chain-Optimierung', desc:'Nachfrageprognose und automatische Bestellauslösung.', size:'sm' },
      { icon:'contract', title:'Vertragsanalyse', desc:'Automatische Extraktion von Klauseln, Risikobewertung und Compliance-Prüfung.', size:'wd' },
      { icon:'code', title:'Code-Generierung', desc:'Automatisierte Entwicklung von Microservices und API-Integrationen.', size:'sm' },
    ],
    orchTitle:'Orchestrierung', orchIcon:'account_tree', orchLabels:['SAP / HubSpot','ERP / CRM']
  },
  appdev: {
    label:'APP-ENTWICKLUNG', title:'Ihre Vision. Unsere Entwicklung.',
    subtitle:'Von der Idee zur fertigen Anwendung — wir entwickeln maßgeschneiderte Software mit KI-Integration.',
    items: [
      { icon:'web', title:'Web-Applikationen', desc:'Moderne, skalierbare Webanwendungen mit React, Next.js und Cloud-nativer Architektur.' },
      { icon:'phone_iphone', title:'Mobile Apps', desc:'Native und Cross-Platform Apps für iOS und Android mit nahtloser Backend-Integration.' },
      { icon:'api', title:'API-Entwicklung', desc:'RESTful und GraphQL APIs mit Enterprise-Grade Security und Dokumentation.' },
      { icon:'cloud', title:'Cloud-Infrastruktur', desc:'AWS, Azure und Google Cloud — von der Architektur bis zum laufenden Betrieb.' },
      { icon:'smart_toy', title:'KI-Integration', desc:'Einbindung von LLMs, Computer Vision und ML-Modellen in bestehende Systeme.' },
      { icon:'speed', title:'Performance & Skalierung', desc:'Optimierung für Hochlast-Szenarien mit Caching, CDN und Auto-Scaling.' }
    ],
    highlight: { title:'Warum NeXify für Ihre Entwicklung?', desc:'Wir kombinieren klassische Softwareentwicklung mit modernster KI-Expertise.', metrics: [{ val:'50+', label:'Projekte realisiert' },{ val:'99.9%', label:'Uptime-Garantie' },{ val:'24/7', label:'Support & Monitoring' }] }
  },
  process: {
    label:'PROZESS', title:'Von der Analyse zum autonomen Agenten',
    steps: [
      { num:'01', title:'Discovery & Analyse', desc:'Tiefgreifende Analyse Ihrer Prozesse, Systeme und Optimierungspotenziale.', bars:1 },
      { num:'02', title:'Architektur & Design', desc:'Technische Konzeption der Agenten-Architektur und Integrationslandschaft.', bars:2 },
      { num:'03', title:'Entwicklung & Training', desc:'Iterative Entwicklung, Training und Feintuning der KI-Agenten.', bars:3 },
      { num:'04', title:'Deployment & Skalierung', desc:'Produktiv-Deployment mit Monitoring, kontinuierlicher Optimierung und Support.', bars:4 }
    ]
  },
  integrations: {
    label:'INTEGRATION', title:'400+ Systemintegrationen',
    subtitle:'Unsere Agenten sprechen die Sprache Ihrer bestehenden Systeme. Die aufgeführten Integrationen sind ein Auszug unseres Portfolios — grundsätzlich ist jede erdenkliche Systemanbindung realisierbar.',
    counter:'400+', counterLabel:'Verfügbare Integrationen',
    badges:['REST API','GraphQL','Webhooks','OAuth 2.0','SAML','gRPC'],
    customNote:'Ihre Wunsch-Integration nicht dabei? Kein Problem — wir realisieren jede erdenkliche Anbindung.',
    cats: [
      { name:'CRM & Sales', items:['Salesforce','HubSpot','Pipedrive','Microsoft Dynamics','SAP CRM','Zoho','Freshsales','Monday CRM','Close','Copper'] },
      { name:'ERP & Finanzen', items:['SAP S/4HANA','Oracle NetSuite','Microsoft Dynamics 365','DATEV','Sage','Lexware','Xero','QuickBooks','Exact Online','sevDesk'] },
      { name:'Cloud & Infrastruktur', items:['AWS','Google Cloud','Microsoft Azure','Cloudflare','DigitalOcean','Heroku','Vercel','Docker','Kubernetes','Terraform'] },
      { name:'Kommunikation', items:['Slack','Microsoft Teams','Zoom','Google Workspace','Twilio','SendGrid','Mailchimp','Discord','WhatsApp Business','Intercom'] },
      { name:'Daten & Analytics', items:['Snowflake','BigQuery','Tableau','Power BI','Looker','Mixpanel','Segment','Amplitude','Datadog','Grafana'] },
      { name:'Entwicklung', items:['GitHub','GitLab','Jira','Confluence','Bitbucket','Jenkins','CircleCI','Vercel','Postman','Swagger'] },
      { name:'E-Commerce', items:['Shopify','WooCommerce','Magento','Stripe','PayPal','Klarna','Adyen','Mollie','BigCommerce','PrestaShop'] },
      { name:'Dokumente & Storage', items:['Google Drive','SharePoint','Dropbox','Box','AWS S3','OneDrive','Notion','Airtable','Coda','Confluence'] },
      { name:'Marketing', items:['Google Ads','Meta Ads','LinkedIn Ads','Marketo','Pardot','ActiveCampaign','Brevo','Hootsuite','Buffer','Semrush'] },
      { name:'KI & Machine Learning', items:['OpenAI','Anthropic','Google Gemini','Hugging Face','LangChain','Pinecone','Weaviate','Cohere','Replicate','Mistral'] }
    ]
  },
  governance: {
    label:'GOVERNANCE & COMPLIANCE', title:'Enterprise-Grade Sicherheit',
    items: [
      { icon:'encrypted', title:'Ende-zu-Ende-Verschlüsselung', desc:'AES-256 Verschlüsselung für alle Daten — at rest und in transit.' },
      { icon:'admin_panel_settings', title:'Rollenbasierte Zugriffskontrolle', desc:'Granulare Berechtigungen mit RBAC, SSO und Multi-Faktor-Authentifizierung.' },
      { icon:'monitoring', title:'Audit-Logging & Monitoring', desc:'Lückenlose Protokollierung aller Agenten-Aktivitäten für Compliance-Nachweise.' },
      { icon:'gavel', title:'Regulatorische Compliance', desc:'DSGVO, EU AI Act, ISO 27001 — wir kennen die Anforderungen Ihrer Branche.' }
    ],
    certs: [
      { label:'DATENSCHUTZ', title:'DSGVO', desc:'Vollständig konform', hl:true },
      { label:'KI-REGULIERUNG', title:'EU AI Act', desc:'Art. 52 konform', hl:true },
      { label:'STANDORT', title:'EU-Hosting', desc:'Frankfurt / Amsterdam' },
      { label:'SECURITY', title:'ISO 27001', desc:'Enterprise-Standard' }
    ]
  },
  pricing: {
    label:'INVESTMENT', title:'Transparente Preisgestaltung',
    subtitle:'Zwei leistungsstarke Tarife — 24 Monate Laufzeit, 30 % Aktivierungsanzahlung. Klar, ehrlich, B2B-stark.',
    plans: [
      { name:'Starter AI Agenten AG', price:'499', period:'EUR / Monat (netto)', features:['2 KI-Agenten','Shared Cloud Infrastructure','E-Mail-Support (48h)','Basis-Integrationen (REST API)','Standard-Monitoring','Monatliches Reporting','24 Monate Laufzeit','30 % Aktivierungsanzahlung: 3.592,80 EUR'], cta:'Angebot anfordern' },
      { name:'Growth AI Agenten AG', price:'1.299', period:'EUR / Monat (netto)', badge:'EMPFOHLEN', features:['10 KI-Agenten','Private Cloud Infrastructure','Priority Support (24h)','CRM/ERP-Kit (SAP, HubSpot, Salesforce)','Advanced Monitoring & Analytics','Wöchentliches Reporting','Dedizierter Onboarding-Manager','24 Monate Laufzeit','30 % Aktivierungsanzahlung: 9.352,80 EUR'], cta:'Angebot anfordern', hl:true }
    ]
  },
  faq: {
    label:'FAQ', title:'Häufig gestellte Fragen',
    subtitle:'Transparente Antworten auf die wichtigsten Fragen zu Tarifen, Zahlung und Vertrag.',
    items: [
      { q:'Welche Tarife gibt es?', a:'Wir bieten zwei aktive Kern-Tarife an: Starter AI Agenten AG (499 EUR/Monat) mit 2 KI-Agenten und Growth AI Agenten AG (1.299 EUR/Monat) mit 10 KI-Agenten. Beide mit 24 Monaten Laufzeit.' },
      { q:'Was bedeutet 24 Monate Laufzeit?', a:'Der Vertrag läuft über 24 Monate ab Beauftragung. Dies ermöglicht nachhaltige Implementierung, Optimierung und kontinuierliche Weiterentwicklung Ihrer KI-Agenten.' },
      { q:'Wie funktioniert die 30-%-Aktivierungsanzahlung?', a:'Bei Beauftragung wird eine Aktivierungsanzahlung von 30 % des Gesamtvertragswerts fällig. Diese deckt Projektstart, Priorisierung, Setup, Kapazitätsreservierung und Implementierungsfreigabe ab. Die Anzahlung ist Teil des Gesamtvertragswerts — keine zusätzliche Gebühr.' },
      { q:'Was ist im Starter enthalten?', a:'2 KI-Agenten, Shared Cloud Infrastructure, E-Mail-Support (48h), Basis-Integrationen (REST API), Standard-Monitoring, monatliches Reporting. Gesamtvertragswert: 11.976 EUR (netto).' },
      { q:'Was ist im Growth enthalten?', a:'10 KI-Agenten, Private Cloud, Priority Support (24h), CRM/ERP-Kit (SAP, HubSpot, Salesforce), Advanced Monitoring, wöchentliches Reporting, dedizierter Onboarding-Manager. Gesamtvertragswert: 31.176 EUR (netto).' },
      { q:'Wie wird abgerechnet?', a:'1. Aktivierungsanzahlung (30 %) — sofort fällig nach Angebotsannahme. 2. Monatliche Folgeraten — der Restbetrag in 24 gleichen Raten. Alle Rechnungen per E-Mail und im sicheren Kundencenter.' },
      { q:'Wie erfolgt die Zahlung?', a:'Per sicherem Revolut Checkout (Karte, Banküberweisung, Apple/Google Pay) oder klassische Banküberweisung. IBAN: NL66 REVO 3601 4304 36, BIC: REVONL22.' },
      { q:'Wie funktioniert die Angebotsannahme?', a:'Sie erhalten Ihr Angebot per E-Mail mit sicherem Zugangslink. Dort können Sie das Angebot annehmen, ablehnen oder eine Änderung anfragen. Bei Annahme wird sofort die Anzahlungsrechnung erstellt.' },
      { q:'Wie sicher sind die KI-Agenten?', a:'Unsere Agenten laufen in isolierten Umgebungen mit Ende-zu-Ende-Verschlüsselung. Wir sind DSGVO-konform, erfüllen den EU AI Act und hosten ausschließlich auf EU-Servern in Frankfurt und Amsterdam.' },
      { q:'Wie werden Daten DSGVO-konform verarbeitet?', a:'Alle Daten in EU-Rechenzentren. Zeitlich begrenzte Zugriffslinks statt Passwörter. Vollständige Audit-Logs. Verschlüsselte Speicherung und Übertragung.' }
    ]
  },
  contact: {
    label:'KONTAKT', title:'Lassen Sie uns sprechen',
    subtitle:'Beschreiben Sie Ihre Herausforderung — wir melden uns innerhalb von 24 Stunden.',
    benefits:['Kostenlose Erstberatung (30 Min.)','Individuelles Konzept','Keine versteckten Kosten'],
    ctaBtn:'Oder direkt Termin buchen',
    form: { firstName:'Vorname', lastName:'Nachname', email:'E-Mail', phone:'Telefon', company:'Unternehmen', message:'Ihre Nachricht', submit:'Nachricht senden', sending:'Wird gesendet...', success:'Ihre Nachricht wurde erfolgreich gesendet. Wir melden uns innerhalb von 24 Stunden.', error:'Es gab einen Fehler. Bitte versuchen Sie es erneut oder kontaktieren Sie uns direkt.' },
    validation: { firstName:'Bitte geben Sie Ihren Vornamen ein', lastName:'Bitte geben Sie Ihren Nachnamen ein', email:'Bitte geben Sie eine gültige E-Mail ein', company:'Bitte geben Sie Ihr Unternehmen ein', message:'Bitte beschreiben Sie Ihre Anfrage' }
  },
  footer: {
    tagline:'Chat it. Automate it.',
    nav:'Navigation', legal:'Rechtliches', kontakt:'Kontakt',
    impressum:'Impressum', datenschutz:'Datenschutz', agb:'AGB', ki:'KI-Hinweise', cookie:'Cookie-Einstellungen',
    copy:'© {y} NeXify Automate. Alle Rechte vorbehalten.',
    status:'Alle Systeme operativ'
  },
  chat: {
    sidebarRole:'Advisor', sidebarDesc:'Ihr strategischer KI-Berater — analysiert Ihre Situation und zeigt konkrete Automatisierungspotenziale auf.',
    status:'KI-Berater', statusOn:'Online',
    presets:['Was kann KI in meiner Branche leisten?','Wie integriert ihr euch in unsere Systeme?','Welche Ergebnisse erzielen eure Kunden?','Ich möchte meine Prozesse analysieren lassen','Was unterscheidet euch von anderen Anbietern?'],
    bookBtn:'Kostenloses Strategiegespräch', placeholder:'Stellen Sie Ihre Frage...', topicLabel:'Enterprise KI',
    welcome:'Guten Tag! Ich bin Ihr strategischer Berater bei NeXifyAI und helfe Ihnen, **konkrete Automatisierungspotenziale** in Ihrem Unternehmen zu identifizieren.\n\nWomit kann ich Ihnen weiterhelfen?\n\n- **Prozessanalyse** — Wo steckt Potenzial in Ihren Abläufen?\n- **Systemintegration** — Wie verbinden wir Ihre bestehenden Tools?\n- **Use Cases** — Welche KI-Lösungen passen zu Ihrer Branche?'
  },
  booking: {
    title:'Strategiegespräch buchen',
    steps:['Datum','Uhrzeit','Details'],
    selectDate:'Datum auswählen', selectTime:'Uhrzeit auswählen', noTimes:'Keine Termine verfügbar',
    next:'Weiter', back:'Zurück', submit:'Termin bestätigen',
    firstName:'Vorname', lastName:'Nachname', email:'E-Mail', phone:'Telefon', company:'Unternehmen', message:'Anliegen (optional)',
    successTitle:'Termin bestätigt', successText:'Wir haben Ihnen eine Bestätigung an {email} gesendet.', close:'Schließen',
    validation: { firstName:'Vorname ist erforderlich', lastName:'Nachname ist erforderlich', email:'Gültige E-Mail erforderlich' }
  },
  cookie: {
    text:'Wir verwenden Cookies für Analyse und Funktionalität. Details in unserer',
    link:'Datenschutzerklärung',
    reject:'Nur notwendige', accept:'Alle akzeptieren'
  }
},

nl: {
  nav: { leistungen:'Diensten', usecases:'Use Cases', appdev:'App-Ontwikkeling', integrationen:'Integraties', tarife:'Tarieven', faq:'FAQ', cta:'Gesprek boeken', menuOpen:'Menu openen', menuClose:'Menu sluiten' },
  hero: {
    label:'NEXIFYAI BY NEXIFY',
    h1: ['Intelligente Agenten.', 'Operationele', 'Excellentie.'],
    desc:'NeXifyAI ontwikkelt AI-agenten die uw bedrijfsprocessen autonoom orkestreren — van klantinteractie tot backend-automatisering. Geen speelgoed. Operationele realiteit.',
    cta1:'Strategiegesprek boeken', cta2:'Advies starten',
    stats: [
      { title:'ENTERPRISE', value:'DACH & NL B2B-Focus' },
      { title:'AGENTEN', value:'Autonoom & adaptief' },
      { title:'INTEGRATIE', value:'400+ Systemen' },
      { title:'COMPLIANCE', value:'AVG-conform' }
    ]
  },
  solutions: {
    label:'DIENSTEN', title:'Wat onze agenten doen',
    subtitle:'Elke agent wordt specifiek voor uw operationele context ontwikkeld — geen templates, geen compromissen.',
    items: [
      { icon:'neurology', title:'AI-Consultancy & Advies', desc:'Strategisch AI-advies en implementatie van autonome agenten voor uw specifieke bedrijfsprocessen.' },
      { icon:'manufacturing', title:'Automatiseringen & Workflows', desc:'End-to-end automatisering van bedrijfsprocessen — van gegevensverzameling tot besluitvorming.' },
      { icon:'hub', title:'Integraties & API', desc:'Naadloze koppeling met 400+ bestaande systemen — CRM, ERP, clouddiensten en maatwerk-interfaces.' },
      { icon:'school', title:'Kennissystemen (RAG)', desc:'Intelligente kennisbanken met Retrieval-Augmented Generation voor nauwkeurige, contextbewuste antwoorden.' },
      { icon:'description', title:'Documentautomatisering', desc:'Geautomatiseerde verwerking, analyse en generatie van bedrijfsdocumenten met AI-begrip.' },
      { icon:'shield', title:'Enterprise Solutions', desc:'Schaalbare AI-infrastructuur met enterprise-grade beveiliging, compliance en dedicated support.' }
    ]
  },
  usecases: {
    label:'OPERATIONELE REALITEIT', title:'Agenten in actie',
    subtitle:'Geen theorie. Elke use case is gebaseerd op operationele realiteit van onze enterprise-klanten.',
    items: [
      { icon:'support_agent', title:'Klantenservice-agenten', desc:'Autonome first-level-resolution met escalatielogica, sentimentanalyse en CRM-integratie. 80% reductie van eerste responstijd.', size:'lg' },
      { icon:'analytics', title:'Revenue Intelligence', desc:'Realtime analyse van sales-pipelines met voorspellende beoordeling.', size:'sm' },
      { icon:'inventory_2', title:'Supply-Chain-Optimalisatie', desc:'Vraagvoorspelling en automatische bestellingen.', size:'sm' },
      { icon:'contract', title:'Contractanalyse', desc:'Automatische extractie van clausules, risicobeoordeling en compliance-controle.', size:'wd' },
      { icon:'code', title:'Code-Generatie', desc:'Geautomatiseerde ontwikkeling van microservices en API-integraties.', size:'sm' },
    ],
    orchTitle:'Orkestratie', orchIcon:'account_tree', orchLabels:['SAP / HubSpot','ERP / CRM']
  },
  appdev: {
    label:'APP-ONTWIKKELING', title:'Uw visie. Onze ontwikkeling.',
    subtitle:'Van idee tot afgewerkte applicatie — wij ontwikkelen op maat gemaakte software met AI-integratie.',
    items: [
      { icon:'web', title:'Webapplicaties', desc:'Moderne, schaalbare webapplicaties met React, Next.js en cloud-native architectuur.' },
      { icon:'phone_iphone', title:'Mobiele Apps', desc:'Native en cross-platform apps voor iOS en Android met naadloze backend-integratie.' },
      { icon:'api', title:'API-Ontwikkeling', desc:'RESTful en GraphQL API\'s met enterprise-grade beveiliging en documentatie.' },
      { icon:'cloud', title:'Cloud-Infrastructuur', desc:'AWS, Azure en Google Cloud — van architectuur tot doorlopend beheer.' },
      { icon:'smart_toy', title:'AI-Integratie', desc:'Integratie van LLM\'s, Computer Vision en ML-modellen in bestaande systemen.' },
      { icon:'speed', title:'Performance & Schaalbaarheid', desc:'Optimalisatie voor high-load scenario\'s met caching, CDN en auto-scaling.' }
    ],
    highlight: { title:'Waarom NeXify voor uw ontwikkeling?', desc:'Wij combineren klassieke softwareontwikkeling met de nieuwste AI-expertise.', metrics: [{ val:'50+', label:'Projecten gerealiseerd' },{ val:'99.9%', label:'Uptime-garantie' },{ val:'24/7', label:'Support & Monitoring' }] }
  },
  process: {
    label:'PROCES', title:'Van analyse tot autonome agent',
    steps: [
      { num:'01', title:'Discovery & Analyse', desc:'Diepgaande analyse van uw processen, systemen en optimalisatiemogelijkheden.', bars:1 },
      { num:'02', title:'Architectuur & Design', desc:'Technisch ontwerp van de agent-architectuur en integratielandschap.', bars:2 },
      { num:'03', title:'Ontwikkeling & Training', desc:'Iteratieve ontwikkeling, training en finetuning van de AI-agenten.', bars:3 },
      { num:'04', title:'Deployment & Opschaling', desc:'Productie-deployment met monitoring, continue optimalisatie en support.', bars:4 }
    ]
  },
  integrations: {
    label:'INTEGRATIE', title:'400+ Systeemintegraties',
    subtitle:'Onze agenten spreken de taal van uw bestaande systemen. De getoonde integraties zijn een selectie uit ons portfolio — in principe is elke denkbare systeemkoppeling realiseerbaar.',
    counter:'400+', counterLabel:'Beschikbare integraties',
    badges:['REST API','GraphQL','Webhooks','OAuth 2.0','SAML','gRPC'],
    customNote:'Uw gewenste integratie niet gevonden? Geen probleem — wij realiseren elke denkbare koppeling.',
    cats: [
      { name:'CRM & Sales', items:['Salesforce','HubSpot','Pipedrive','Microsoft Dynamics','SAP CRM','Zoho','Freshsales','Monday CRM','Close','Copper'] },
      { name:'ERP & Financiën', items:['SAP S/4HANA','Oracle NetSuite','Microsoft Dynamics 365','DATEV','Sage','Lexware','Xero','QuickBooks','Exact Online','sevDesk'] },
      { name:'Cloud & Infrastructuur', items:['AWS','Google Cloud','Microsoft Azure','Cloudflare','DigitalOcean','Heroku','Vercel','Docker','Kubernetes','Terraform'] },
      { name:'Communicatie', items:['Slack','Microsoft Teams','Zoom','Google Workspace','Twilio','SendGrid','Mailchimp','Discord','WhatsApp Business','Intercom'] },
      { name:'Data & Analytics', items:['Snowflake','BigQuery','Tableau','Power BI','Looker','Mixpanel','Segment','Amplitude','Datadog','Grafana'] },
      { name:'Ontwikkeling', items:['GitHub','GitLab','Jira','Confluence','Bitbucket','Jenkins','CircleCI','Vercel','Postman','Swagger'] },
      { name:'E-Commerce', items:['Shopify','WooCommerce','Magento','Stripe','PayPal','Klarna','Adyen','Mollie','BigCommerce','PrestaShop'] },
      { name:'Documenten & Storage', items:['Google Drive','SharePoint','Dropbox','Box','AWS S3','OneDrive','Notion','Airtable','Coda','Confluence'] },
      { name:'Marketing', items:['Google Ads','Meta Ads','LinkedIn Ads','Marketo','Pardot','ActiveCampaign','Brevo','Hootsuite','Buffer','Semrush'] },
      { name:'AI & Machine Learning', items:['OpenAI','Anthropic','Google Gemini','Hugging Face','LangChain','Pinecone','Weaviate','Cohere','Replicate','Mistral'] }
    ]
  },
  governance: {
    label:'GOVERNANCE & COMPLIANCE', title:'Enterprise-grade beveiliging',
    items: [
      { icon:'encrypted', title:'End-to-end encryptie', desc:'AES-256 encryptie voor alle gegevens — at rest en in transit.' },
      { icon:'admin_panel_settings', title:'Rolgebaseerde toegangscontrole', desc:'Gedetailleerde autorisaties met RBAC, SSO en multi-factor-authenticatie.' },
      { icon:'monitoring', title:'Audit-logging & Monitoring', desc:'Complete registratie van alle agent-activiteiten voor compliance-bewijsvoering.' },
      { icon:'gavel', title:'Regulatoire compliance', desc:'AVG, EU AI Act, ISO 27001 — wij kennen de eisen van uw branche.' }
    ],
    certs: [
      { label:'PRIVACY', title:'AVG', desc:'Volledig conform', hl:true },
      { label:'AI-REGULERING', title:'EU AI Act', desc:'Art. 52 conform', hl:true },
      { label:'LOCATIE', title:'EU-Hosting', desc:'Frankfurt / Amsterdam' },
      { label:'SECURITY', title:'ISO 27001', desc:'Enterprise-standaard' }
    ]
  },
  pricing: {
    label:'INVESTERING', title:'Transparante prijzen',
    subtitle:'Twee krachtige tarieven — 24 maanden looptijd, 30 % activeringsaanbetaling. Helder, eerlijk, B2B-sterk.',
    plans: [
      { name:'Starter AI Agenten AG', price:'499', period:'EUR / maand (netto)', features:['2 AI-agenten','Shared Cloud Infrastructure','E-mail support (48u)','Basis-integraties (REST API)','Standaard monitoring','Maandelijkse rapportage','24 maanden looptijd','30 % activeringsaanbetaling: 3.592,80 EUR'], cta:'Offerte aanvragen' },
      { name:'Growth AI Agenten AG', price:'1.299', period:'EUR / maand (netto)', badge:'AANBEVOLEN', features:['10 AI-agenten','Private Cloud Infrastructure','Priority support (24u)','CRM/ERP-kit (SAP, HubSpot, Salesforce)','Advanced monitoring & analytics','Wekelijkse rapportage','Dedicated onboarding manager','24 maanden looptijd','30 % activeringsaanbetaling: 9.352,80 EUR'], cta:'Offerte aanvragen', hl:true }
    ]
  },
  faq: {
    label:'FAQ', title:'Veelgestelde vragen',
    subtitle:'Transparante antwoorden op de belangrijkste vragen over tarieven, betaling en contract.',
    items: [
      { q:'Welke tarieven zijn er?', a:'Wij bieden twee actieve kerntarieven: Starter AI Agenten AG (499 EUR/maand) met 2 AI-agenten en Growth AI Agenten AG (1.299 EUR/maand) met 10 AI-agenten. Beide met 24 maanden looptijd.' },
      { q:'Wat betekent 24 maanden looptijd?', a:'Het contract loopt 24 maanden vanaf opdracht. Dit maakt duurzame implementatie, optimalisatie en doorontwikkeling van uw AI-agenten mogelijk.' },
      { q:'Hoe werkt de 30 % activeringsaanbetaling?', a:'Bij opdracht is een aanbetaling van 30 % van de totale contractwaarde verschuldigd. Deze dekt projectstart, prioritering, setup en capaciteitsreservering. De aanbetaling is onderdeel van de contractwaarde — geen extra kosten.' },
      { q:'Hoe wordt er betaald?', a:'Via veilige Revolut Checkout of klassieke bankoverschrijving. IBAN: NL66 REVO 3601 4304 36, BIC: REVONL22.' },
      { q:'Hoe werkt de offerte-aanvaarding?', a:'U ontvangt uw offerte per e-mail met een veilige toegangslink. Daar kunt u de offerte aanvaarden, afwijzen of een wijziging aanvragen.' },
      { q:'Hoe veilig zijn de AI-agenten?', a:'Onze agenten draaien in geisoleerde omgevingen met end-to-end encryptie. AVG-conform, EU AI Act compliant, hosting uitsluitend op EU-servers.' }
    ]
  },
  contact: {
    label:'CONTACT', title:'Laten we praten',
    subtitle:'Beschrijf uw uitdaging — wij reageren binnen 24 uur.',
    benefits:['Gratis eerste advies (30 min.)','Individueel concept','Geen verborgen kosten'],
    ctaBtn:'Of direct een afspraak boeken',
    form: { firstName:'Voornaam', lastName:'Achternaam', email:'E-mail', phone:'Telefoon', company:'Bedrijf', message:'Uw bericht', submit:'Bericht versturen', sending:'Wordt verzonden...', success:'Uw bericht is succesvol verzonden. Wij reageren binnen 24 uur.', error:'Er is een fout opgetreden. Probeer het opnieuw of neem direct contact met ons op.' },
    validation: { firstName:'Vul uw voornaam in', lastName:'Vul uw achternaam in', email:'Vul een geldig e-mailadres in', company:'Vul uw bedrijf in', message:'Beschrijf uw aanvraag' }
  },
  footer: {
    tagline:'Chat it. Automate it.',
    nav:'Navigatie', legal:'Juridisch', kontakt:'Contact',
    impressum:'Impressum', datenschutz:'Privacybeleid', agb:'Voorwaarden', ki:'AI-Informatie', cookie:'Cookie-instellingen',
    copy:'© {y} NeXify Automate. Alle rechten voorbehouden.',
    status:'Alle systemen operationeel'
  },
  chat: {
    sidebarRole:'Adviseur', sidebarDesc:'Uw strategische AI-adviseur — analyseert uw situatie en toont concrete automatiseringsmogelijkheden.',
    status:'AI-Adviseur', statusOn:'Online',
    presets:['Wat kan AI voor mijn branche betekenen?','Hoe integreren jullie met onze systemen?','Welke resultaten behalen jullie klanten?','Ik wil mijn processen laten analyseren','Wat onderscheidt jullie van andere aanbieders?'],
    bookBtn:'Gratis strategiegesprek', placeholder:'Stel uw vraag...', topicLabel:'Enterprise AI',
    welcome:'Welkom! Ik ben uw strategisch adviseur bij NeXifyAI en help u **concrete automatiseringsmogelijkheden** in uw organisatie te identificeren.\n\nWaarmee kan ik u helpen?\n\n- **Procesanalyse** — Waar zit potentieel in uw werkprocessen?\n- **Systeemintegratie** — Hoe verbinden we uw bestaande tools?\n- **Use cases** — Welke AI-oplossingen passen bij uw branche?'
  },
  booking: {
    title:'Strategiegesprek boeken',
    steps:['Datum','Tijd','Details'],
    selectDate:'Datum kiezen', selectTime:'Tijd kiezen', noTimes:'Geen tijden beschikbaar',
    next:'Verder', back:'Terug', submit:'Afspraak bevestigen',
    firstName:'Voornaam', lastName:'Achternaam', email:'E-mail', phone:'Telefoon', company:'Bedrijf', message:'Onderwerp (optioneel)',
    successTitle:'Afspraak bevestigd', successText:'Wij hebben een bevestiging naar {email} gestuurd.', close:'Sluiten',
    validation: { firstName:'Voornaam is vereist', lastName:'Achternaam is vereist', email:'Geldig e-mailadres vereist' }
  },
  cookie: {
    text:'Wij gebruiken cookies voor analyse en functionaliteit. Details in ons',
    link:'Privacybeleid',
    reject:'Alleen noodzakelijk', accept:'Alles accepteren'
  }
},

en: {
  nav: { leistungen:'Services', usecases:'Use Cases', appdev:'App Development', integrationen:'Integrations', tarife:'Pricing', faq:'FAQ', cta:'Book a Call', menuOpen:'Open menu', menuClose:'Close menu' },
  hero: {
    label:'NEXIFYAI BY NEXIFY',
    h1: ['Intelligent Agents.', 'Operational', 'Excellence.'],
    desc:'NeXifyAI builds AI agents that autonomously orchestrate your business processes — from customer interaction to backend automation. Not a gimmick. Operational reality.',
    cta1:'Book Strategy Call', cta2:'Start Advisory Chat',
    stats: [
      { title:'ENTERPRISE', value:'DACH & EU B2B Focus' },
      { title:'AGENTS', value:'Autonomous & adaptive' },
      { title:'INTEGRATION', value:'400+ Systems' },
      { title:'COMPLIANCE', value:'GDPR compliant' }
    ]
  },
  solutions: {
    label:'SERVICES', title:'What our agents deliver',
    subtitle:'Each agent is built specifically for your operational context — no templates, no compromises.',
    items: [
      { icon:'neurology', title:'AI Consulting & Advisory', desc:'Strategic AI consulting and implementation of autonomous agents for your specific business processes.' },
      { icon:'manufacturing', title:'Automations & Workflows', desc:'End-to-end automation of business processes — from data capture to decision-making.' },
      { icon:'hub', title:'Integrations & API', desc:'Seamless connection to 400+ existing systems — CRM, ERP, cloud services, and proprietary interfaces.' },
      { icon:'school', title:'Knowledge Systems (RAG)', desc:'Intelligent knowledge bases with Retrieval-Augmented Generation for precise, context-aware answers.' },
      { icon:'description', title:'Document Automation', desc:'Automated processing, analysis, and generation of business documents with AI comprehension.' },
      { icon:'shield', title:'Enterprise Solutions', desc:'Scalable AI infrastructure with enterprise-grade security, compliance, and dedicated support.' }
    ]
  },
  usecases: {
    label:'OPERATIONAL REALITY', title:'Agents in action',
    subtitle:'No theory. Every use case is based on operational reality from our enterprise clients.',
    items: [
      { icon:'support_agent', title:'Customer Service Agents', desc:'Autonomous first-level resolution with escalation logic, sentiment analysis, and CRM integration. 80% reduction in first response time.', size:'lg' },
      { icon:'analytics', title:'Revenue Intelligence', desc:'Real-time analysis of sales pipelines with predictive scoring.', size:'sm' },
      { icon:'inventory_2', title:'Supply Chain Optimization', desc:'Demand forecasting and automated order triggering.', size:'sm' },
      { icon:'contract', title:'Contract Analysis', desc:'Automatic clause extraction, risk assessment, and compliance checking.', size:'wd' },
      { icon:'code', title:'Code Generation', desc:'Automated development of microservices and API integrations.', size:'sm' },
    ],
    orchTitle:'Orchestration', orchIcon:'account_tree', orchLabels:['SAP / HubSpot','ERP / CRM']
  },
  appdev: {
    label:'APP DEVELOPMENT', title:'Your vision. Our development.',
    subtitle:'From idea to finished application — we build custom software with AI integration.',
    items: [
      { icon:'web', title:'Web Applications', desc:'Modern, scalable web applications with React, Next.js, and cloud-native architecture.' },
      { icon:'phone_iphone', title:'Mobile Apps', desc:'Native and cross-platform apps for iOS and Android with seamless backend integration.' },
      { icon:'api', title:'API Development', desc:'RESTful and GraphQL APIs with enterprise-grade security and documentation.' },
      { icon:'cloud', title:'Cloud Infrastructure', desc:'AWS, Azure, and Google Cloud — from architecture to ongoing operations.' },
      { icon:'smart_toy', title:'AI Integration', desc:'Integration of LLMs, Computer Vision, and ML models into existing systems.' },
      { icon:'speed', title:'Performance & Scaling', desc:'Optimization for high-load scenarios with caching, CDN, and auto-scaling.' }
    ],
    highlight: { title:'Why NeXify for your development?', desc:'We combine classical software engineering with cutting-edge AI expertise.', metrics: [{ val:'50+', label:'Projects delivered' },{ val:'99.9%', label:'Uptime guarantee' },{ val:'24/7', label:'Support & Monitoring' }] }
  },
  process: {
    label:'PROCESS', title:'From analysis to autonomous agent',
    steps: [
      { num:'01', title:'Discovery & Analysis', desc:'In-depth analysis of your processes, systems, and optimization potential.', bars:1 },
      { num:'02', title:'Architecture & Design', desc:'Technical design of the agent architecture and integration landscape.', bars:2 },
      { num:'03', title:'Development & Training', desc:'Iterative development, training, and fine-tuning of AI agents.', bars:3 },
      { num:'04', title:'Deployment & Scaling', desc:'Production deployment with monitoring, continuous optimization, and support.', bars:4 }
    ]
  },
  integrations: {
    label:'INTEGRATION', title:'400+ System Integrations',
    subtitle:'Our agents speak the language of your existing systems. The listed integrations are a selection from our portfolio — virtually any system connection is achievable.',
    counter:'400+', counterLabel:'Available integrations',
    badges:['REST API','GraphQL','Webhooks','OAuth 2.0','SAML','gRPC'],
    customNote:'Don\'t see your integration? No problem — we can build any connection you need.',
    cats: [
      { name:'CRM & Sales', items:['Salesforce','HubSpot','Pipedrive','Microsoft Dynamics','SAP CRM','Zoho','Freshsales','Monday CRM','Close','Copper'] },
      { name:'ERP & Finance', items:['SAP S/4HANA','Oracle NetSuite','Microsoft Dynamics 365','DATEV','Sage','Lexware','Xero','QuickBooks','Exact Online','sevDesk'] },
      { name:'Cloud & Infrastructure', items:['AWS','Google Cloud','Microsoft Azure','Cloudflare','DigitalOcean','Heroku','Vercel','Docker','Kubernetes','Terraform'] },
      { name:'Communication', items:['Slack','Microsoft Teams','Zoom','Google Workspace','Twilio','SendGrid','Mailchimp','Discord','WhatsApp Business','Intercom'] },
      { name:'Data & Analytics', items:['Snowflake','BigQuery','Tableau','Power BI','Looker','Mixpanel','Segment','Amplitude','Datadog','Grafana'] },
      { name:'Development', items:['GitHub','GitLab','Jira','Confluence','Bitbucket','Jenkins','CircleCI','Vercel','Postman','Swagger'] },
      { name:'E-Commerce', items:['Shopify','WooCommerce','Magento','Stripe','PayPal','Klarna','Adyen','Mollie','BigCommerce','PrestaShop'] },
      { name:'Documents & Storage', items:['Google Drive','SharePoint','Dropbox','Box','AWS S3','OneDrive','Notion','Airtable','Coda','Confluence'] },
      { name:'Marketing', items:['Google Ads','Meta Ads','LinkedIn Ads','Marketo','Pardot','ActiveCampaign','Brevo','Hootsuite','Buffer','Semrush'] },
      { name:'AI & Machine Learning', items:['OpenAI','Anthropic','Google Gemini','Hugging Face','LangChain','Pinecone','Weaviate','Cohere','Replicate','Mistral'] }
    ]
  },
  governance: {
    label:'GOVERNANCE & COMPLIANCE', title:'Enterprise-grade security',
    items: [
      { icon:'encrypted', title:'End-to-end encryption', desc:'AES-256 encryption for all data — at rest and in transit.' },
      { icon:'admin_panel_settings', title:'Role-based access control', desc:'Granular permissions with RBAC, SSO, and multi-factor authentication.' },
      { icon:'monitoring', title:'Audit logging & monitoring', desc:'Complete recording of all agent activities for compliance evidence.' },
      { icon:'gavel', title:'Regulatory compliance', desc:'GDPR, EU AI Act, ISO 27001 — we know your industry requirements.' }
    ],
    certs: [
      { label:'PRIVACY', title:'GDPR', desc:'Fully compliant', hl:true },
      { label:'AI REGULATION', title:'EU AI Act', desc:'Art. 52 compliant', hl:true },
      { label:'LOCATION', title:'EU Hosting', desc:'Frankfurt / Amsterdam' },
      { label:'SECURITY', title:'ISO 27001', desc:'Enterprise standard' }
    ]
  },
  pricing: {
    label:'INVESTMENT', title:'Transparent pricing',
    subtitle:'Two powerful plans — 24-month term, 30 % activation deposit. Clear, honest, B2B-ready.',
    plans: [
      { name:'Starter AI Agenten AG', price:'499', period:'EUR / month (net)', features:['2 AI agents','Shared Cloud Infrastructure','Email support (48h)','Basic integrations (REST API)','Standard monitoring','Monthly reporting','24-month contract','30 % activation deposit: EUR 3,592.80'], cta:'Request a Quote' },
      { name:'Growth AI Agenten AG', price:'1,299', period:'EUR / month (net)', badge:'RECOMMENDED', features:['10 AI agents','Private Cloud Infrastructure','Priority support (24h)','CRM/ERP kit (SAP, HubSpot, Salesforce)','Advanced monitoring & analytics','Weekly reporting','Dedicated onboarding manager','24-month contract','30 % activation deposit: EUR 9,352.80'], cta:'Request a Quote', hl:true }
    ]
  },
  faq: {
    label:'FAQ', title:'Frequently asked questions',
    subtitle:'Transparent answers about plans, payments, and contracts.',
    items: [
      { q:'What plans are available?', a:'We offer two core plans: Starter AI Agenten AG (EUR 499/month) with 2 AI agents, and Growth AI Agenten AG (EUR 1,299/month) with 10 AI agents. Both with 24-month terms.' },
      { q:'What does the 24-month term mean?', a:'The contract runs for 24 months from commission. This enables sustainable implementation, optimization, and continuous development of your AI agents.' },
      { q:'How does the 30 % activation deposit work?', a:'Upon commissioning, an activation deposit of 30 % of the total contract value is due. This covers project start, prioritization, setup, and capacity reservation. The deposit is part of the total contract value — no additional fees.' },
      { q:'How do I pay?', a:'Via secure Revolut Checkout or traditional bank transfer. IBAN: NL66 REVO 3601 4304 36, BIC: REVONL22.' },
      { q:'How does quote acceptance work?', a:'You receive your quote via email with a secure access link. There you can accept, decline, or request a revision.' },
      { q:'How secure are the AI agents?', a:'Our agents run in isolated environments with end-to-end encryption. GDPR-compliant, EU AI Act compliant, hosted exclusively on EU servers.' }
    ]
  },
  contact: {
    label:'CONTACT', title:'Let\'s talk',
    subtitle:'Describe your challenge — we\'ll get back to you within 24 hours.',
    benefits:['Free initial consultation (30 min.)','Individual concept','No hidden costs'],
    ctaBtn:'Or book a call directly',
    form: { firstName:'First Name', lastName:'Last Name', email:'Email', phone:'Phone', company:'Company', message:'Your message', submit:'Send message', sending:'Sending...', success:'Your message has been sent successfully. We\'ll get back to you within 24 hours.', error:'An error occurred. Please try again or contact us directly.' },
    validation: { firstName:'Please enter your first name', lastName:'Please enter your last name', email:'Please enter a valid email', company:'Please enter your company', message:'Please describe your inquiry' }
  },
  footer: {
    tagline:'Chat it. Automate it.',
    nav:'Navigation', legal:'Legal', kontakt:'Contact',
    impressum:'Imprint', datenschutz:'Privacy Policy', agb:'Terms', ki:'AI Transparency', cookie:'Cookie Settings',
    copy:'© {y} NeXify Automate. All rights reserved.',
    status:'All systems operational'
  },
  chat: {
    sidebarRole:'Advisor', sidebarDesc:'Your strategic AI consultant — analyzes your situation and identifies concrete automation potential.',
    status:'AI Advisor', statusOn:'Online',
    presets:['What can AI achieve in my industry?','How do you integrate with our systems?','What results do your clients achieve?','I want my processes analyzed','What sets you apart from other providers?'],
    bookBtn:'Free strategy call', placeholder:'Ask your question...', topicLabel:'Enterprise AI',
    welcome:'Hello! I\'m your strategic advisor at NeXifyAI, helping you identify **concrete automation potential** in your organization.\n\nHow can I assist you?\n\n- **Process analysis** — Where is untapped potential in your workflows?\n- **System integration** — How do we connect your existing tools?\n- **Use cases** — Which AI solutions fit your industry?'
  },
  booking: {
    title:'Book Strategy Call',
    steps:['Date','Time','Details'],
    selectDate:'Select date', selectTime:'Select time', noTimes:'No times available',
    next:'Continue', back:'Back', submit:'Confirm appointment',
    firstName:'First Name', lastName:'Last Name', email:'Email', phone:'Phone', company:'Company', message:'Topic (optional)',
    successTitle:'Appointment confirmed', successText:'We\'ve sent a confirmation to {email}.', close:'Close',
    validation: { firstName:'First name is required', lastName:'Last name is required', email:'Valid email required' }
  },
  cookie: {
    text:'We use cookies for analytics and functionality. Details in our',
    link:'Privacy Policy',
    reject:'Necessary only', accept:'Accept all'
  }
}
};

export default t;

/* ═══════════════════════════════════════════════
   NeXifyAI — Integration Data (DE / NL / EN)
   Central data source for Integrations section + SEO pages
   ═══════════════════════════════════════════════ */

export const INTEGRATION_CATEGORIES = [
  {
    key: 'crm-sales',
    icon: 'handshake',
    name: { de: 'CRM & Sales', nl: 'CRM & Sales', en: 'CRM & Sales' },
    desc: { de: 'Nahtlose Anbindung an führende CRM-Systeme für automatisierte Lead-Qualifizierung, Pipeline-Management und Vertriebsoptimierung.', nl: 'Naadloze koppeling met toonaangevende CRM-systemen voor geautomatiseerde lead-kwalificatie, pipeline-management en verkoopoptimalisatie.', en: 'Seamless connection to leading CRM systems for automated lead qualification, pipeline management, and sales optimization.' },
    items: [
      { slug: 'salesforce', name: 'Salesforce', popular: true },
      { slug: 'hubspot', name: 'HubSpot', popular: true },
      { slug: 'pipedrive', name: 'Pipedrive' },
      { slug: 'microsoft-dynamics', name: 'Microsoft Dynamics', popular: true },
      { slug: 'sap-crm', name: 'SAP CRM' },
      { slug: 'zoho', name: 'Zoho CRM' },
      { slug: 'freshsales', name: 'Freshsales' },
      { slug: 'monday-crm', name: 'Monday CRM' },
      { slug: 'close', name: 'Close' },
      { slug: 'copper', name: 'Copper' },
    ]
  },
  {
    key: 'erp-finance',
    icon: 'account_balance',
    name: { de: 'ERP & Finanzen', nl: 'ERP & Financien', en: 'ERP & Finance' },
    desc: { de: 'Direkte Integration in ERP- und Buchhaltungssysteme für automatisierte Rechnungsverarbeitung, Bestandsführung und Finanzreporting.', nl: 'Directe integratie met ERP- en boekhoudsystemen voor geautomatiseerde factuurverwerking, voorraadbeheer en financiele rapportage.', en: 'Direct integration with ERP and accounting systems for automated invoice processing, inventory management, and financial reporting.' },
    items: [
      { slug: 'sap', name: 'SAP S/4HANA', popular: true },
      { slug: 'oracle-netsuite', name: 'Oracle NetSuite' },
      { slug: 'microsoft-dynamics-365', name: 'Microsoft Dynamics 365' },
      { slug: 'datev', name: 'DATEV', popular: true },
      { slug: 'sage', name: 'Sage' },
      { slug: 'lexware', name: 'Lexware' },
      { slug: 'xero', name: 'Xero' },
      { slug: 'quickbooks', name: 'QuickBooks' },
      { slug: 'exact-online', name: 'Exact Online' },
      { slug: 'sevdesk', name: 'sevDesk' },
    ]
  },
  {
    key: 'communication',
    icon: 'forum',
    name: { de: 'Kommunikation', nl: 'Communicatie', en: 'Communication' },
    desc: { de: 'Zentrale Steuerung aller Kommunikationskanaele — von E-Mail über Messaging bis hin zu Video-Conferencing.', nl: 'Centrale aansturing van alle communicatiekanalen — van e-mail tot messaging en videoconferencing.', en: 'Central control of all communication channels — from email to messaging and video conferencing.' },
    items: [
      { slug: 'slack', name: 'Slack', popular: true },
      { slug: 'microsoft-teams', name: 'Microsoft Teams', popular: true },
      { slug: 'zoom', name: 'Zoom' },
      { slug: 'google-workspace', name: 'Google Workspace' },
      { slug: 'twilio', name: 'Twilio' },
      { slug: 'sendgrid', name: 'SendGrid' },
      { slug: 'mailchimp', name: 'Mailchimp' },
      { slug: 'discord', name: 'Discord' },
      { slug: 'whatsapp-business', name: 'WhatsApp Business' },
      { slug: 'intercom', name: 'Intercom' },
    ]
  },
  {
    key: 'cloud',
    icon: 'cloud',
    name: { de: 'Cloud & Infrastruktur', nl: 'Cloud & Infrastructuur', en: 'Cloud & Infrastructure' },
    desc: { de: 'Enterprise-Deployments auf allen grossen Cloud-Plattformen mit Monitoring, Autoscaling und Container-Orchestrierung.', nl: 'Enterprise-deployments op alle grote cloudplatformen met monitoring, autoscaling en container-orchestratie.', en: 'Enterprise deployments on all major cloud platforms with monitoring, autoscaling, and container orchestration.' },
    items: [
      { slug: 'aws', name: 'AWS', popular: true },
      { slug: 'google-cloud', name: 'Google Cloud', popular: true },
      { slug: 'microsoft-azure', name: 'Microsoft Azure' },
      { slug: 'cloudflare', name: 'Cloudflare' },
      { slug: 'digitalocean', name: 'DigitalOcean' },
      { slug: 'heroku', name: 'Heroku' },
      { slug: 'vercel', name: 'Vercel' },
      { slug: 'docker', name: 'Docker' },
      { slug: 'kubernetes', name: 'Kubernetes' },
      { slug: 'terraform', name: 'Terraform' },
    ]
  },
  {
    key: 'analytics',
    icon: 'insights',
    name: { de: 'Daten & Analytics', nl: 'Data & Analytics', en: 'Data & Analytics' },
    desc: { de: 'Echtzeit-Datenverarbeitung, BI-Dashboards und prädiktive Analysen für datengetriebene Entscheidungsfindung.', nl: 'Realtime dataverwerking, BI-dashboards en voorspellende analyses voor datagestuurde besluitvorming.', en: 'Real-time data processing, BI dashboards, and predictive analytics for data-driven decision-making.' },
    items: [
      { slug: 'snowflake', name: 'Snowflake' },
      { slug: 'bigquery', name: 'BigQuery' },
      { slug: 'tableau', name: 'Tableau' },
      { slug: 'power-bi', name: 'Power BI', popular: true },
      { slug: 'looker', name: 'Looker' },
      { slug: 'mixpanel', name: 'Mixpanel' },
      { slug: 'segment', name: 'Segment' },
      { slug: 'amplitude', name: 'Amplitude' },
      { slug: 'datadog', name: 'Datadog' },
      { slug: 'grafana', name: 'Grafana' },
    ]
  },
  {
    key: 'development',
    icon: 'code',
    name: { de: 'Entwicklung', nl: 'Ontwikkeling', en: 'Development' },
    desc: { de: 'CI/CD-Pipelines, Code-Repositories und Projektmanagement-Tools für agile Entwicklungsprozesse.', nl: 'CI/CD-pipelines, code-repositories en projectmanagementtools voor agile ontwikkelprocessen.', en: 'CI/CD pipelines, code repositories, and project management tools for agile development processes.' },
    items: [
      { slug: 'github', name: 'GitHub' },
      { slug: 'gitlab', name: 'GitLab' },
      { slug: 'jira', name: 'Jira' },
      { slug: 'confluence', name: 'Confluence' },
      { slug: 'bitbucket', name: 'Bitbucket' },
      { slug: 'jenkins', name: 'Jenkins' },
      { slug: 'circleci', name: 'CircleCI' },
      { slug: 'postman', name: 'Postman' },
      { slug: 'swagger', name: 'Swagger' },
      { slug: 'sonarqube', name: 'SonarQube' },
    ]
  },
  {
    key: 'ecommerce',
    icon: 'shopping_cart',
    name: { de: 'E-Commerce', nl: 'E-Commerce', en: 'E-Commerce' },
    desc: { de: 'Vollständige Shop-Integration für automatisierte Bestellverarbeitung, Bestandssynchronisation und Payment-Flows.', nl: 'Volledige shop-integratie voor geautomatiseerde orderverwerking, voorraadsynchronisatie en betaalflows.', en: 'Complete shop integration for automated order processing, inventory synchronization, and payment flows.' },
    items: [
      { slug: 'shopify', name: 'Shopify', popular: true },
      { slug: 'woocommerce', name: 'WooCommerce' },
      { slug: 'magento', name: 'Magento' },
      { slug: 'stripe', name: 'Stripe', popular: true },
      { slug: 'paypal', name: 'PayPal' },
      { slug: 'klarna', name: 'Klarna' },
      { slug: 'adyen', name: 'Adyen' },
      { slug: 'mollie', name: 'Mollie' },
      { slug: 'bigcommerce', name: 'BigCommerce' },
      { slug: 'prestashop', name: 'PrestaShop' },
    ]
  },
  {
    key: 'documents',
    icon: 'folder_open',
    name: { de: 'Dokumente & Storage', nl: 'Documenten & Storage', en: 'Documents & Storage' },
    desc: { de: 'Zentrale Dokumentenverwaltung mit automatischer Klassifizierung, Versionierung und intelligenter Suche.', nl: 'Centraal documentbeheer met automatische classificatie, versiebeheer en intelligente zoekfunctie.', en: 'Central document management with automatic classification, versioning, and intelligent search.' },
    items: [
      { slug: 'google-drive', name: 'Google Drive' },
      { slug: 'sharepoint', name: 'SharePoint' },
      { slug: 'dropbox', name: 'Dropbox' },
      { slug: 'box', name: 'Box' },
      { slug: 'aws-s3', name: 'AWS S3' },
      { slug: 'onedrive', name: 'OneDrive' },
      { slug: 'notion', name: 'Notion' },
      { slug: 'airtable', name: 'Airtable' },
      { slug: 'coda', name: 'Coda' },
    ]
  },
  {
    key: 'marketing',
    icon: 'campaign',
    name: { de: 'Marketing', nl: 'Marketing', en: 'Marketing' },
    desc: { de: 'Kampagnen-Automatisierung, Lead-Nurturing und Performance-Tracking über alle Marketingkanaele hinweg.', nl: 'Campagne-automatisering, lead-nurturing en performance-tracking over alle marketingkanalen.', en: 'Campaign automation, lead nurturing, and performance tracking across all marketing channels.' },
    items: [
      { slug: 'google-ads', name: 'Google Ads' },
      { slug: 'meta-ads', name: 'Meta Ads' },
      { slug: 'linkedin-ads', name: 'LinkedIn Ads' },
      { slug: 'marketo', name: 'Marketo' },
      { slug: 'pardot', name: 'Pardot' },
      { slug: 'activecampaign', name: 'ActiveCampaign' },
      { slug: 'brevo', name: 'Brevo' },
      { slug: 'hootsuite', name: 'Hootsuite' },
      { slug: 'buffer', name: 'Buffer' },
      { slug: 'semrush', name: 'Semrush' },
    ]
  },
  {
    key: 'ai-ml',
    icon: 'psychology',
    name: { de: 'KI & Machine Learning', nl: 'AI & Machine Learning', en: 'AI & Machine Learning' },
    desc: { de: 'Anbindung an führende KI-Plattformen für LLM-Integration, Embedding-Generierung und ML-Inferenz.', nl: 'Koppeling met toonaangevende AI-platforms voor LLM-integratie, embedding-generatie en ML-inferentie.', en: 'Connection to leading AI platforms for LLM integration, embedding generation, and ML inference.' },
    items: [
      { slug: 'openai', name: 'OpenAI', popular: true },
      { slug: 'anthropic', name: 'Anthropic' },
      { slug: 'google-gemini', name: 'Google Gemini' },
      { slug: 'hugging-face', name: 'Hugging Face' },
      { slug: 'langchain', name: 'LangChain' },
      { slug: 'pinecone', name: 'Pinecone' },
      { slug: 'weaviate', name: 'Weaviate' },
      { slug: 'cohere', name: 'Cohere' },
      { slug: 'replicate', name: 'Replicate' },
      { slug: 'mistral', name: 'Mistral' },
    ]
  },
  {
    key: 'hr',
    icon: 'groups',
    name: { de: 'HR & Recruiting', nl: 'HR & Recruiting', en: 'HR & Recruiting' },
    desc: { de: 'Automatisierte Bewerberprozesse, Mitarbeiter-Onboarding und HR-Analytics.', nl: 'Geautomatiseerde sollicitatieprocessen, medewerker-onboarding en HR-analytics.', en: 'Automated application processes, employee onboarding, and HR analytics.' },
    items: [
      { slug: 'personio', name: 'Personio' },
      { slug: 'workday', name: 'Workday' },
      { slug: 'bamboohr', name: 'BambooHR' },
      { slug: 'greenhouse', name: 'Greenhouse' },
      { slug: 'lever', name: 'Lever' },
    ]
  },
  {
    key: 'productivity',
    icon: 'task_alt',
    name: { de: 'Produktivitaet', nl: 'Productiviteit', en: 'Productivity' },
    desc: { de: 'Aufgabenmanagement, Workflow-Automatisierung und Teamkollaboration für effizientere Abläufe.', nl: 'Taakbeheer, workflow-automatisering en teamsamenwerking voor efficientere processen.', en: 'Task management, workflow automation, and team collaboration for more efficient processes.' },
    items: [
      { slug: 'asana', name: 'Asana' },
      { slug: 'trello', name: 'Trello' },
      { slug: 'monday', name: 'Monday.com' },
      { slug: 'clickup', name: 'ClickUp' },
      { slug: 'basecamp', name: 'Basecamp' },
    ]
  },
];

/* Featured integrations with detailed content for SEO pages */
export const FEATURED_INTEGRATIONS = {
  salesforce: {
    name: 'Salesforce',
    category: 'crm-sales',
    logo: 'cloud',
    color: '#00A1E0',
    title: { de: 'Salesforce KI-Integration', nl: 'Salesforce AI-Integratie', en: 'Salesforce AI Integration' },
    meta: { de: 'NeXifyAI integriert KI-Agenten direkt in Salesforce — für automatisierte Lead-Qualifizierung, Pipeline-Optimierung und intelligenten Kundenservice.', nl: 'NeXifyAI integreert AI-agenten direct in Salesforce — voor geautomatiseerde lead-kwalificatie, pipeline-optimalisatie en intelligente klantenservice.', en: 'NeXifyAI integrates AI agents directly into Salesforce — for automated lead qualification, pipeline optimization, and intelligent customer service.' },
    hero: { de: 'Ihre Salesforce-Daten. Unsere KI-Agenten. Maximale Vertriebsperformance.', nl: 'Uw Salesforce-data. Onze AI-agenten. Maximale verkoopprestaties.', en: 'Your Salesforce data. Our AI agents. Maximum sales performance.' },
    usecases: {
      de: [
        { title: 'Automatische Lead-Qualifizierung', desc: 'KI-Agenten bewerten eingehende Leads in Echtzeit anhand von Scoring-Modellen und priorisieren für Ihr Sales-Team.' },
        { title: 'Pipeline-Intelligence', desc: 'Prädiktive Analyse Ihrer Sales-Pipeline mit Abschlusswahrscheinlichkeiten und Handlungsempfehlungen.' },
        { title: 'Kundenservice-Automation', desc: 'Autonome Bearbeitung von Service-Cases mit direktem Zugriff auf Salesforce-Kundendaten und Fallhistorie.' },
        { title: 'Reporting-Automation', desc: 'Automatisierte Erstellung von Sales-Reports, Forecasts und KPI-Dashboards aus Salesforce-Daten.' },
      ],
      nl: [
        { title: 'Automatische lead-kwalificatie', desc: 'AI-agenten beoordelen inkomende leads in realtime op basis van scoring-modellen en prioriteren voor uw salesteam.' },
        { title: 'Pipeline-intelligence', desc: 'Voorspellende analyse van uw sales-pipeline met afsluitkansen en actieaanbevelingen.' },
        { title: 'Klantenservice-automatisering', desc: 'Autonome afhandeling van service-cases met directe toegang tot Salesforce-klantdata en casehistorie.' },
        { title: 'Rapportage-automatisering', desc: 'Geautomatiseerd aanmaken van sales-reports, forecasts en KPI-dashboards vanuit Salesforce-data.' },
      ],
      en: [
        { title: 'Automatic lead qualification', desc: 'AI agents evaluate incoming leads in real-time using scoring models and prioritize for your sales team.' },
        { title: 'Pipeline intelligence', desc: 'Predictive analysis of your sales pipeline with close probabilities and action recommendations.' },
        { title: 'Customer service automation', desc: 'Autonomous handling of service cases with direct access to Salesforce customer data and case history.' },
        { title: 'Reporting automation', desc: 'Automated creation of sales reports, forecasts, and KPI dashboards from Salesforce data.' },
      ],
    },
    combinedWith: ['hubspot', 'slack', 'datev', 'openai'],
    faq: {
      de: [
        { q: 'Wie verbinden sich die KI-Agenten mit Salesforce?', a: 'Über die offizielle Salesforce REST/SOAP API mit OAuth 2.0-Authentifizierung. Kein Salesforce-Plugin erforderlich.' },
        { q: 'Welche Salesforce-Editionen werden unterstützt?', a: 'Professional, Enterprise und Unlimited Edition. Für die Developer Edition gelten API-Limitierungen.' },
        { q: 'Wie lange dauert die Salesforce-Integration?', a: 'Standard-Integrationen sind in 2-4 Wochen produktiv. Komplexe Custom-Objekte und Workflows erfordern 4-8 Wochen.' },
      ],
      nl: [
        { q: 'Hoe verbinden de AI-agenten met Salesforce?', a: 'Via de officiele Salesforce REST/SOAP API met OAuth 2.0-authenticatie. Geen Salesforce-plugin vereist.' },
        { q: 'Welke Salesforce-edities worden ondersteund?', a: 'Professional, Enterprise en Unlimited Edition. Voor Developer Edition gelden API-beperkingen.' },
        { q: 'Hoe lang duurt de Salesforce-integratie?', a: 'Standaard-integraties zijn binnen 2-4 weken productief. Complexe custom objects en workflows vereisen 4-8 weken.' },
      ],
      en: [
        { q: 'How do AI agents connect to Salesforce?', a: 'Via the official Salesforce REST/SOAP API with OAuth 2.0 authentication. No Salesforce plugin required.' },
        { q: 'Which Salesforce editions are supported?', a: 'Professional, Enterprise, and Unlimited Edition. Developer Edition has API limitations.' },
        { q: 'How long does the Salesforce integration take?', a: 'Standard integrations go live in 2-4 weeks. Complex custom objects and workflows require 4-8 weeks.' },
      ],
    },
  },
  hubspot: {
    name: 'HubSpot',
    category: 'crm-sales',
    logo: 'hub',
    color: '#FF7A59',
    title: { de: 'HubSpot KI-Integration', nl: 'HubSpot AI-Integratie', en: 'HubSpot AI Integration' },
    meta: { de: 'NeXifyAI integriert KI-Agenten in HubSpot — für automatisiertes Lead-Nurturing, Content-Optimierung und Sales-Automation.', nl: 'NeXifyAI integreert AI-agenten in HubSpot — voor geautomatiseerde lead-nurturing, content-optimalisatie en sales-automatisering.', en: 'NeXifyAI integrates AI agents into HubSpot — for automated lead nurturing, content optimization, and sales automation.' },
    hero: { de: 'HubSpot meets KI-Agenten. Marketing und Vertrieb auf Autopilot.', nl: 'HubSpot meets AI-agenten. Marketing en verkoop op autopilot.', en: 'HubSpot meets AI agents. Marketing and sales on autopilot.' },
    usecases: {
      de: [
        { title: 'Lead-Nurturing-Automation', desc: 'KI-gesteuerte E-Mail-Sequenzen basierend auf Kundenverhalten, Engagement-Scores und Kaufbereitschaft.' },
        { title: 'Content-Strategie-Optimierung', desc: 'Automatische Analyse Ihrer Blog- und Landing-Page-Performance mit konkreten Optimierungsvorschlaegen.' },
        { title: 'Deal-Pipeline-Management', desc: 'KI-Agenten aktualisieren Deal-Stages automatisch und erkennen Stagnation in der Pipeline.' },
        { title: 'Chatbot-Integration', desc: 'Intelligenter Chatbot auf Ihrer Website mit direkter HubSpot-Kontaktanlage und Lead-Routing.' },
      ],
      nl: [
        { title: 'Lead-nurturing-automatisering', desc: 'AI-gestuurde e-mailsequenties op basis van klantgedrag, engagement-scores en koopbereidheid.' },
        { title: 'Content-strategie-optimalisatie', desc: 'Automatische analyse van uw blog- en landingspagina-prestaties met concrete optimalisatievoorstellen.' },
        { title: 'Deal-pipeline-management', desc: 'AI-agenten werken deal-stages automatisch bij en herkennen stagnatie in de pipeline.' },
        { title: 'Chatbot-integratie', desc: 'Intelligente chatbot op uw website met directe HubSpot-contactaanmaak en lead-routing.' },
      ],
      en: [
        { title: 'Lead nurturing automation', desc: 'AI-driven email sequences based on customer behavior, engagement scores, and purchase readiness.' },
        { title: 'Content strategy optimization', desc: 'Automatic analysis of your blog and landing page performance with concrete optimization suggestions.' },
        { title: 'Deal pipeline management', desc: 'AI agents automatically update deal stages and detect pipeline stagnation.' },
        { title: 'Chatbot integration', desc: 'Intelligent chatbot on your website with direct HubSpot contact creation and lead routing.' },
      ],
    },
    combinedWith: ['salesforce', 'google-ads', 'slack', 'mailchimp'],
    faq: {
      de: [
        { q: 'Welche HubSpot-Hubs werden unterstützt?', a: 'Marketing Hub, Sales Hub, Service Hub und CMS Hub — alle mit voller API-Integration.' },
        { q: 'Können bestehende HubSpot-Workflows erweitert werden?', a: 'Ja. Unsere KI-Agenten ergänzen bestehende Workflows mit intelligenter Entscheidungslogik.' },
      ],
      nl: [
        { q: 'Welke HubSpot-hubs worden ondersteund?', a: 'Marketing Hub, Sales Hub, Service Hub en CMS Hub — allemaal met volledige API-integratie.' },
        { q: 'Kunnen bestaande HubSpot-workflows worden uitgebreid?', a: 'Ja. Onze AI-agenten vullen bestaande workflows aan met intelligente beslissingslogica.' },
      ],
      en: [
        { q: 'Which HubSpot hubs are supported?', a: 'Marketing Hub, Sales Hub, Service Hub, and CMS Hub — all with full API integration.' },
        { q: 'Can existing HubSpot workflows be extended?', a: 'Yes. Our AI agents complement existing workflows with intelligent decision logic.' },
      ],
    },
  },
  sap: {
    name: 'SAP S/4HANA',
    category: 'erp-finance',
    logo: 'precision_manufacturing',
    color: '#0FAAFF',
    title: { de: 'SAP S/4HANA KI-Integration', nl: 'SAP S/4HANA AI-Integratie', en: 'SAP S/4HANA AI Integration' },
    meta: { de: 'NeXifyAI verbindet KI-Agenten mit SAP S/4HANA für automatisierte Prozesse in Einkauf, Produktion, Logistik und Finanzen.', nl: 'NeXifyAI verbindt AI-agenten met SAP S/4HANA voor geautomatiseerde processen in inkoop, productie, logistiek en financien.', en: 'NeXifyAI connects AI agents with SAP S/4HANA for automated processes in procurement, production, logistics, and finance.' },
    hero: { de: 'SAP-Prozesse intelligent automatisieren. Ohne Kompromisse.', nl: 'SAP-processen intelligent automatiseren. Zonder compromissen.', en: 'Intelligently automate SAP processes. Without compromise.' },
    usecases: {
      de: [
        { title: 'Einkaufsautomation', desc: 'Automatische Bestellanforderungen basierend auf Bestandsanalysen und Bedarfsprognosen.' },
        { title: 'Rechnungsverarbeitung', desc: 'Intelligente Eingangsrechnungsprüfung mit automatischem Abgleich gegen Bestellungen und Wareneingänge.' },
        { title: 'Produktionsplanung', desc: 'KI-gestützte Kapazitätsplanung und Fertigungsauftragsoptimierung in Echtzeit.' },
        { title: 'Finanz-Reporting', desc: 'Automatisierte Monatsabschluesse, Konsolidierungen und regulatorische Reports.' },
      ],
      nl: [
        { title: 'Inkoopautomatisering', desc: 'Automatische bestelvereisten op basis van voorraadanalyses en behoefteprognoses.' },
        { title: 'Factuurverwerking', desc: 'Intelligente inkomende factuurcontrole met automatische matching tegen bestellingen en goederenontvangst.' },
        { title: 'Productieplanning', desc: 'AI-ondersteunde capaciteitsplanning en productieorderoptimalisatie in realtime.' },
        { title: 'Financiele rapportage', desc: 'Geautomatiseerde maandafsluitingen, consolidaties en regelgevende rapporten.' },
      ],
      en: [
        { title: 'Procurement automation', desc: 'Automatic purchase requisitions based on inventory analysis and demand forecasts.' },
        { title: 'Invoice processing', desc: 'Intelligent incoming invoice verification with automatic matching against orders and goods receipts.' },
        { title: 'Production planning', desc: 'AI-supported capacity planning and production order optimization in real-time.' },
        { title: 'Financial reporting', desc: 'Automated month-end closes, consolidations, and regulatory reports.' },
      ],
    },
    combinedWith: ['datev', 'microsoft-teams', 'power-bi', 'aws'],
    faq: {
      de: [
        { q: 'Wie erfolgt die SAP-Anbindung technisch?', a: 'Über SAP OData Services, RFC/BAPI oder den SAP Integration Suite Connector. On-Premise und Cloud.' },
        { q: 'Ist die Integration mit SAP ECC möglich?', a: 'Ja. Sowohl SAP S/4HANA als auch SAP ECC (ERP 6.0) werden unterstützt.' },
      ],
      nl: [
        { q: 'Hoe werkt de SAP-koppeling technisch?', a: 'Via SAP OData Services, RFC/BAPI of de SAP Integration Suite Connector. On-premise en cloud.' },
        { q: 'Is integratie met SAP ECC mogelijk?', a: 'Ja. Zowel SAP S/4HANA als SAP ECC (ERP 6.0) worden ondersteund.' },
      ],
      en: [
        { q: 'How does the SAP connection work technically?', a: 'Via SAP OData Services, RFC/BAPI, or the SAP Integration Suite Connector. On-premise and cloud.' },
        { q: 'Is integration with SAP ECC possible?', a: 'Yes. Both SAP S/4HANA and SAP ECC (ERP 6.0) are supported.' },
      ],
    },
  },
  datev: {
    name: 'DATEV',
    category: 'erp-finance',
    logo: 'receipt_long',
    color: '#009D3C',
    title: { de: 'DATEV KI-Integration', nl: 'DATEV AI-Integratie', en: 'DATEV AI Integration' },
    meta: { de: 'NeXifyAI automatisiert DATEV-Prozesse mit KI-Agenten — für Buchhaltung, Lohnabrechnung und Steuerberatung im DACH-Raum.', nl: 'NeXifyAI automatiseert DATEV-processen met AI-agenten — voor boekhouding, salarisadministratie en belastingadvies in de DACH-regio.', en: 'NeXifyAI automates DATEV processes with AI agents — for accounting, payroll, and tax advisory in the DACH region.' },
    hero: { de: 'DATEV-Buchhaltung. KI-Agenten. Null manueller Aufwand.', nl: 'DATEV-boekhouding. AI-agenten. Nul handmatige inspanning.', en: 'DATEV accounting. AI agents. Zero manual effort.' },
    usecases: {
      de: [
        { title: 'Belegerfassung', desc: 'Automatische Erkennung, Klassifizierung und Verbuchung von Eingangs- und Ausgangsbelegen.' },
        { title: 'Lohnbuchhaltung', desc: 'KI-gestützte Prüfung und Vorbereitung von Gehaltsabrechnungen mit DATEV LODAS/Lohn und Gehalt.' },
        { title: 'Umsatzsteuer-Voranmeldung', desc: 'Automatisierte Erstellung und Prüfung der monatlichen USt-VA mit Plausibilitätskontrolle.' },
        { title: 'Mandantenkommunikation', desc: 'KI-Agenten bearbeiten Mandantenanfragen und liefern relevante Unterlagen aus DATEV automatisch.' },
      ],
      nl: [
        { title: 'Boekstukverwerking', desc: 'Automatische herkenning, classificatie en boeking van inkomende en uitgaande documenten.' },
        { title: 'Salarisadministratie', desc: 'AI-ondersteunde controle en voorbereiding van salarisberekeningen met DATEV LODAS.' },
        { title: 'Btw-aangifte', desc: 'Geautomatiseerd opstellen en controleren van de maandelijkse btw-aangifte met plausibiliteitscontrole.' },
        { title: 'Klantcommunicatie', desc: 'AI-agenten behandelen klantvragen en leveren relevante documenten vanuit DATEV automatisch.' },
      ],
      en: [
        { title: 'Document processing', desc: 'Automatic recognition, classification, and posting of incoming and outgoing documents.' },
        { title: 'Payroll', desc: 'AI-supported review and preparation of payroll with DATEV LODAS.' },
        { title: 'VAT pre-registration', desc: 'Automated creation and review of monthly VAT returns with plausibility checks.' },
        { title: 'Client communication', desc: 'AI agents handle client inquiries and automatically deliver relevant documents from DATEV.' },
      ],
    },
    combinedWith: ['sap', 'lexware', 'sevdesk', 'slack'],
    faq: {
      de: [
        { q: 'Ist die DATEV-Integration DSGVO-konform?', a: 'Ja. Alle Daten werden verschlüsselt übertragen und ausschließlich in EU-Rechenzentren verarbeitet.' },
        { q: 'Welche DATEV-Produkte werden unterstützt?', a: 'DATEV Unternehmen online, DATEV LODAS, Lohn und Gehalt, Rechnungswesen — über die DATEV-API und Schnittstellen.' },
      ],
      nl: [
        { q: 'Is de DATEV-integratie AVG-conform?', a: 'Ja. Alle data wordt versleuteld verzonden en uitsluitend in EU-datacenters verwerkt.' },
        { q: 'Welke DATEV-producten worden ondersteund?', a: 'DATEV Unternehmen online, DATEV LODAS, Lohn und Gehalt, Rechnungswesen — via de DATEV-API.' },
      ],
      en: [
        { q: 'Is the DATEV integration GDPR-compliant?', a: 'Yes. All data is encrypted in transit and processed exclusively in EU data centers.' },
        { q: 'Which DATEV products are supported?', a: 'DATEV Unternehmen online, DATEV LODAS, Lohn und Gehalt, Rechnungswesen — via the DATEV API.' },
      ],
    },
  },
  slack: {
    name: 'Slack',
    category: 'communication',
    logo: 'tag',
    color: '#4A154B',
    title: { de: 'Slack KI-Integration', nl: 'Slack AI-Integratie', en: 'Slack AI Integration' },
    meta: { de: 'NeXifyAI bringt KI-Agenten direkt in Slack — für automatisierte Benachrichtigungen, Teamkommunikation und Workflow-Steuerung.', nl: 'NeXifyAI brengt AI-agenten direct naar Slack — voor geautomatiseerde meldingen, teamcommunicatie en workflow-aansturing.', en: 'NeXifyAI brings AI agents directly to Slack — for automated notifications, team communication, and workflow control.' },
    hero: { de: 'KI-Agenten in Slack. Automatisierung dort, wo Ihr Team arbeitet.', nl: 'AI-agenten in Slack. Automatisering waar uw team werkt.', en: 'AI agents in Slack. Automation where your team works.' },
    usecases: {
      de: [
        { title: 'Intelligente Benachrichtigungen', desc: 'Kontextbezogene Alerts aus CRM, ERP und Monitoring-Tools direkt in relevante Slack-Channels.' },
        { title: 'Slash-Command-Automationen', desc: 'Eigene /commands für häufige Aufgaben wie Status-Checks, Report-Generierung und Ticket-Erstellung.' },
        { title: 'Meeting-Summaries', desc: 'Automatische Zusammenfassungen von Slack-Diskussionen mit Action Items und Verantwortlichkeiten.' },
      ],
      nl: [
        { title: 'Intelligente meldingen', desc: 'Contextgerelateerde alerts vanuit CRM, ERP en monitoring-tools direct in relevante Slack-channels.' },
        { title: 'Slash-command-automatiseringen', desc: 'Eigen /commands voor veelvoorkomende taken zoals statuschecks, rapportgeneratie en ticketaanmaak.' },
        { title: 'Vergaderings-samenvattingen', desc: 'Automatische samenvattingen van Slack-discussies met actiepunten en verantwoordelijkheden.' },
      ],
      en: [
        { title: 'Intelligent notifications', desc: 'Context-aware alerts from CRM, ERP, and monitoring tools directly in relevant Slack channels.' },
        { title: 'Slash command automations', desc: 'Custom /commands for common tasks like status checks, report generation, and ticket creation.' },
        { title: 'Meeting summaries', desc: 'Automatic summaries of Slack discussions with action items and responsibilities.' },
      ],
    },
    combinedWith: ['salesforce', 'jira', 'github', 'google-workspace'],
    faq: {
      de: [
        { q: 'Brauche ich Slack Enterprise?', a: 'Nein. Die Integration funktioniert mit Slack Free, Pro und Enterprise Grid.' },
      ],
      nl: [
        { q: 'Heb ik Slack Enterprise nodig?', a: 'Nee. De integratie werkt met Slack Free, Pro en Enterprise Grid.' },
      ],
      en: [
        { q: 'Do I need Slack Enterprise?', a: 'No. The integration works with Slack Free, Pro, and Enterprise Grid.' },
      ],
    },
  },
  aws: {
    name: 'AWS',
    category: 'cloud',
    logo: 'dns',
    color: '#FF9900',
    title: { de: 'AWS KI-Integration', nl: 'AWS AI-Integratie', en: 'AWS AI Integration' },
    meta: { de: 'NeXifyAI deployed KI-Agenten auf AWS — skalierbar, sicher und kostenoptimiert mit EC2, Lambda, S3 und SageMaker.', nl: 'NeXifyAI deployt AI-agenten op AWS — schaalbaar, veilig en kostengeoptimaliseerd met EC2, Lambda, S3 en SageMaker.', en: 'NeXifyAI deploys AI agents on AWS — scalable, secure, and cost-optimized with EC2, Lambda, S3, and SageMaker.' },
    hero: { de: 'KI-Agenten auf AWS. Enterprise-Scale. EU-Compliance.', nl: 'AI-agenten op AWS. Enterprise-schaal. EU-compliance.', en: 'AI agents on AWS. Enterprise scale. EU compliance.' },
    usecases: {
      de: [
        { title: 'Serverless-Agenten', desc: 'KI-Agenten als Lambda-Functions für kosteneffiziente, event-getriebene Verarbeitung.' },
        { title: 'Auto-Scaling-Infrastruktur', desc: 'Dynamische Skalierung basierend auf Auslastung mit ECS/EKS und Application Load Balancer.' },
        { title: 'Daten-Pipeline-Automation', desc: 'Automatisierte ETL-Prozesse mit S3, Glue, Athena und Redshift für Ihre BI-Anforderungen.' },
      ],
      nl: [
        { title: 'Serverless-agenten', desc: 'AI-agenten als Lambda-functies voor kosteneffectieve, event-driven verwerking.' },
        { title: 'Auto-scaling-infrastructuur', desc: 'Dynamische schaling op basis van belasting met ECS/EKS en Application Load Balancer.' },
        { title: 'Data-pipeline-automatisering', desc: 'Geautomatiseerde ETL-processen met S3, Glue, Athena en Redshift voor uw BI-vereisten.' },
      ],
      en: [
        { title: 'Serverless agents', desc: 'AI agents as Lambda functions for cost-effective, event-driven processing.' },
        { title: 'Auto-scaling infrastructure', desc: 'Dynamic scaling based on load with ECS/EKS and Application Load Balancer.' },
        { title: 'Data pipeline automation', desc: 'Automated ETL processes with S3, Glue, Athena, and Redshift for your BI requirements.' },
      ],
    },
    combinedWith: ['google-cloud', 'kubernetes', 'terraform', 'datadog'],
    faq: {
      de: [
        { q: 'In welcher AWS-Region werden die Agenten gehostet?', a: 'Standardmäßig in eu-central-1 (Frankfurt) oder eu-west-1 (Irland). Weitere Regionen auf Anfrage.' },
      ],
      nl: [
        { q: 'In welke AWS-regio worden de agenten gehost?', a: 'Standaard in eu-central-1 (Frankfurt) of eu-west-1 (Ierland). Andere regio\'s op aanvraag.' },
      ],
      en: [
        { q: 'In which AWS region are the agents hosted?', a: 'By default in eu-central-1 (Frankfurt) or eu-west-1 (Ireland). Other regions on request.' },
      ],
    },
  },
  shopify: {
    name: 'Shopify',
    category: 'ecommerce',
    logo: 'storefront',
    color: '#96BF48',
    title: { de: 'Shopify KI-Integration', nl: 'Shopify AI-Integratie', en: 'Shopify AI Integration' },
    meta: { de: 'NeXifyAI automatisiert Ihren Shopify-Shop mit KI-Agenten — für Bestellmanagement, Kundenservice und Conversion-Optimierung.', nl: 'NeXifyAI automatiseert uw Shopify-shop met AI-agenten — voor orderbeheer, klantenservice en conversie-optimalisatie.', en: 'NeXifyAI automates your Shopify store with AI agents — for order management, customer service, and conversion optimization.' },
    hero: { de: 'Shopify + KI-Agenten. E-Commerce auf Autopilot.', nl: 'Shopify + AI-agenten. E-commerce op autopilot.', en: 'Shopify + AI agents. E-commerce on autopilot.' },
    usecases: {
      de: [
        { title: 'Bestellautomation', desc: 'Automatisierte Bestellbestaetigung, Versandbenachrichtigung und Retouren-Management.' },
        { title: 'Produkt-Empfehlungen', desc: 'KI-basierte Produktvorschlaege basierend auf Kundenverhalten und Kaufhistorie.' },
        { title: 'Bestandsmanagement', desc: 'Automatische Bestandsüberwachung mit Nachbestellungs-Triggern und Lieferantenbenachrichtigung.' },
      ],
      nl: [
        { title: 'Orderautomatisering', desc: 'Geautomatiseerde orderbevestiging, verzendmelding en retourenbeheer.' },
        { title: 'Productaanbevelingen', desc: 'AI-gebaseerde productvoorstellen op basis van klantgedrag en aankoophistorie.' },
        { title: 'Voorraadbeheer', desc: 'Automatische voorraadmonitoring met nabesteltriggers en leveranciersmelding.' },
      ],
      en: [
        { title: 'Order automation', desc: 'Automated order confirmation, shipping notification, and return management.' },
        { title: 'Product recommendations', desc: 'AI-based product suggestions based on customer behavior and purchase history.' },
        { title: 'Inventory management', desc: 'Automatic inventory monitoring with reorder triggers and supplier notification.' },
      ],
    },
    combinedWith: ['stripe', 'klarna', 'mailchimp', 'google-ads'],
    faq: {
      de: [
        { q: 'Funktioniert die Integration mit Shopify Plus?', a: 'Ja. Shopify Basic, Shopify, Advanced und Shopify Plus — alle Versionen werden unterstützt.' },
      ],
      nl: [
        { q: 'Werkt de integratie met Shopify Plus?', a: 'Ja. Shopify Basic, Shopify, Advanced en Shopify Plus — alle versies worden ondersteund.' },
      ],
      en: [
        { q: 'Does the integration work with Shopify Plus?', a: 'Yes. Shopify Basic, Shopify, Advanced, and Shopify Plus — all versions are supported.' },
      ],
    },
  },
  openai: {
    name: 'OpenAI',
    category: 'ai-ml',
    logo: 'auto_awesome',
    color: '#10A37F',
    title: { de: 'OpenAI KI-Integration', nl: 'OpenAI AI-Integratie', en: 'OpenAI AI Integration' },
    meta: { de: 'NeXifyAI integriert OpenAI-Modelle (GPT, DALL-E, Whisper) in Ihre Geschaeftsprozesse für Text-, Bild- und Sprachverarbeitung.', nl: 'NeXifyAI integreert OpenAI-modellen (GPT, DALL-E, Whisper) in uw bedrijfsprocessen voor tekst-, beeld- en spraakverwerking.', en: 'NeXifyAI integrates OpenAI models (GPT, DALL-E, Whisper) into your business processes for text, image, and speech processing.' },
    hero: { de: 'OpenAI-Power. In Ihrem Unternehmen. Sicher und kontrolliert.', nl: 'OpenAI-kracht. In uw organisatie. Veilig en gecontroleerd.', en: 'OpenAI power. In your business. Secure and controlled.' },
    usecases: {
      de: [
        { title: 'Textgenerierung & Zusammenfassung', desc: 'Automatisierte Erstellung von Reports, E-Mails, Verträgen und Zusammenfassungen mit GPT-Modellen.' },
        { title: 'Dokumentenanalyse', desc: 'KI-gestützte Analyse von Verträgen, Rechnungen und Berichten mit Extraktion relevanter Informationen.' },
        { title: 'Sprachverarbeitung', desc: 'Transkription und Analyse von Calls, Meetings und Voicemails mit OpenAI Whisper.' },
      ],
      nl: [
        { title: 'Tekstgeneratie & samenvatting', desc: 'Geautomatiseerd aanmaken van rapporten, e-mails, contracten en samenvattingen met GPT-modellen.' },
        { title: 'Documentanalyse', desc: 'AI-ondersteunde analyse van contracten, facturen en rapporten met extractie van relevante informatie.' },
        { title: 'Spraakverwerking', desc: 'Transcriptie en analyse van calls, vergaderingen en voicemails met OpenAI Whisper.' },
      ],
      en: [
        { title: 'Text generation & summarization', desc: 'Automated creation of reports, emails, contracts, and summaries with GPT models.' },
        { title: 'Document analysis', desc: 'AI-powered analysis of contracts, invoices, and reports with extraction of relevant information.' },
        { title: 'Speech processing', desc: 'Transcription and analysis of calls, meetings, and voicemails with OpenAI Whisper.' },
      ],
    },
    combinedWith: ['langchain', 'pinecone', 'slack', 'google-drive'],
    faq: {
      de: [
        { q: 'Werden unsere Daten von OpenAI gespeichert?', a: 'Nein. Wir nutzen die Enterprise-API mit Opt-out für Datentraining. Ihre Daten bleiben Ihre Daten.' },
      ],
      nl: [
        { q: 'Worden onze data door OpenAI opgeslagen?', a: 'Nee. Wij gebruiken de Enterprise-API met opt-out voor datatraining. Uw data blijft uw data.' },
      ],
      en: [
        { q: 'Is our data stored by OpenAI?', a: 'No. We use the Enterprise API with opt-out for data training. Your data remains your data.' },
      ],
    },
  },
  stripe: {
    name: 'Stripe',
    category: 'ecommerce',
    logo: 'payments',
    color: '#635BFF',
    title: { de: 'Stripe Payment-Integration', nl: 'Stripe Payment-Integratie', en: 'Stripe Payment Integration' },
    meta: { de: 'NeXifyAI automatisiert Zahlungsprozesse mit Stripe — für Rechnungsstellung, Subscriptions und Revenue-Reporting.', nl: 'NeXifyAI automatiseert betalingsprocessen met Stripe — voor facturering, subscriptions en omzetrapportage.', en: 'NeXifyAI automates payment processes with Stripe — for invoicing, subscriptions, and revenue reporting.' },
    hero: { de: 'Zahlungen. Rechnungen. Subscriptions. Alles automatisiert.', nl: 'Betalingen. Facturen. Subscriptions. Alles geautomatiseerd.', en: 'Payments. Invoices. Subscriptions. All automated.' },
    usecases: {
      de: [
        { title: 'Automatisierte Rechnungsstellung', desc: 'KI-Agenten erstellen, versenden und verfolgen Rechnungen basierend auf Vertragsdaten und Leistungsnachweisen.' },
        { title: 'Subscription-Management', desc: 'Automatisierte Verwaltung wiederkehrender Zahlungen mit Upgrade-, Downgrade- und Kuendigungslogik.' },
        { title: 'Revenue-Analytics', desc: 'Echtzeit-Dashboards für MRR, Churn-Rate, LTV und Zahlungsausfaelle mit prädiktiver Analyse.' },
      ],
      nl: [
        { title: 'Geautomatiseerde facturering', desc: 'AI-agenten maken, verzenden en volgen facturen op basis van contractgegevens en prestatiebewijzen.' },
        { title: 'Subscription-management', desc: 'Geautomatiseerd beheer van terugkerende betalingen met upgrade-, downgrade- en opzeglogica.' },
        { title: 'Revenue-analytics', desc: 'Realtime dashboards voor MRR, churn-rate, LTV en betalingsuitval met voorspellende analyse.' },
      ],
      en: [
        { title: 'Automated invoicing', desc: 'AI agents create, send, and track invoices based on contract data and proof of service.' },
        { title: 'Subscription management', desc: 'Automated management of recurring payments with upgrade, downgrade, and cancellation logic.' },
        { title: 'Revenue analytics', desc: 'Real-time dashboards for MRR, churn rate, LTV, and payment failures with predictive analysis.' },
      ],
    },
    combinedWith: ['shopify', 'salesforce', 'datev', 'quickbooks'],
    faq: {
      de: [
        { q: 'Werden auch SEPA-Lastschriften unterstützt?', a: 'Ja. Stripe unterstützt SEPA, Kreditkarte, Klarna, giropay und weitere europaeische Zahlungsmethoden.' },
      ],
      nl: [
        { q: 'Worden SEPA-incasso\'s ook ondersteund?', a: 'Ja. Stripe ondersteunt SEPA, creditcard, Klarna, iDEAL en andere Europese betaalmethoden.' },
      ],
      en: [
        { q: 'Are SEPA direct debits also supported?', a: 'Yes. Stripe supports SEPA, credit card, Klarna, giropay, and other European payment methods.' },
      ],
    },
  },
};

/* Helper: get all integrations as flat list with category info */
export function getAllIntegrations() {
  const all = [];
  INTEGRATION_CATEGORIES.forEach(cat => {
    cat.items.forEach(item => {
      all.push({ ...item, categoryKey: cat.key, categoryName: cat.name, categoryIcon: cat.icon });
    });
  });
  return all;
}

/* Helper: find integration by slug */
export function getIntegrationBySlug(slug) {
  for (const cat of INTEGRATION_CATEGORIES) {
    const item = cat.items.find(i => i.slug === slug);
    if (item) return { ...item, category: cat };
  }
  return null;
}

/* Helper: get featured integration detail by slug */
export function getFeaturedDetail(slug) {
  return FEATURED_INTEGRATIONS[slug] || null;
}

/* Helper: count total integrations */
export function getTotalIntegrationCount() {
  return INTEGRATION_CATEGORIES.reduce((sum, cat) => sum + cat.items.length, 0);
}

"""
NeXifyAI Commercial Engine v2.0
Single Source of Truth for Tariffs, Pricing, Offers, Invoices, Payments, PDFs, Emails.
"""
import os
import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from io import BytesIO

import httpx
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

logger = logging.getLogger("nexifyai.commercial")

# ═══════════════════════════════════════════════════
# COMPANY MASTER DATA — Single Source of Truth
# ═══════════════════════════════════════════════════
COMPANY_DATA = {
    "name": "NeXify Automate",
    "brand": "NeXifyAI",
    "ceo": "Pascal Courbois",
    "ceo_title": "Geschäftsführer",
    "address_nl": {
        "street": "Graaf van Loonstraat 1E",
        "city": "5921 JA Venlo",
        "country": "Niederlande",
    },
    "address_de": {
        "street": "Wallstrasse 9",
        "city": "41334 Nettetal-Kaldenkirchen",
        "country": "Deutschland",
    },
    "phone": "+31 6 133 188 56",
    "email": "support@nexify-automate.com",
    "web": "nexifyai.de",
    "kvk": "90483944",
    "vat_id": "NL865786276B01",
    "bank": {
        "iban": "NL66 REVO 3601 4304 36",
        "bic": "REVONL22",
        "intermediary_bic": "CHASDEFX",
        "bank_name": "Revolut",
        "account_holder": "NeXify Automate",
    },
}

# ═══════════════════════════════════════════════════
# TARIFF CONFIG — Single Source of Truth
# ═══════════════════════════════════════════════════
TARIFF_CONFIG = {
    "starter": {
        "tariff_number": "NXA-SAA-24-499",
        "slug": "starter-ai-agenten-ag",
        "name": "Starter AI Agenten AG",
        "reference_monthly_eur": 499.00,
        "contract_months": 24,
        "upfront_percent": 30,
        "total_contract_eur": 11976.00,
        "upfront_eur": 3592.80,
        "remaining_eur": 8383.20,
        "recurring_count": 24,
        "recurring_eur": 349.30,
        "billing_mode": "upfront_plus_recurring",
        "target_segment": "B2B-first",
        "status": "active",
        "agents": 2,
        "infrastructure": "Shared Cloud",
        "support": "E-Mail (48h)",
        "features": [
            "2 KI-Agenten",
            "Shared Cloud Infrastructure",
            "E-Mail-Support (48h Response)",
            "Basis-Integrationen (REST API)",
            "Standard-Monitoring",
            "Monatliches Reporting",
        ],
        "payment_products": {
            "activation": {
                "product_code": "starter_activation_30",
                "invoice_type": "deposit",
                "description": "Aktivierungsanzahlung (30 %) — Starter AI Agenten AG",
            },
            "recurring": {
                "product_code": "starter_recurring_24",
                "invoice_type": "monthly",
                "description": "Monatliche Folgerate — Starter AI Agenten AG",
            },
        },
    },
    "growth": {
        "tariff_number": "NXA-GAA-24-1299",
        "slug": "growth-ai-agenten-ag",
        "name": "Growth AI Agenten AG",
        "reference_monthly_eur": 1299.00,
        "contract_months": 24,
        "upfront_percent": 30,
        "total_contract_eur": 31176.00,
        "upfront_eur": 9352.80,
        "remaining_eur": 21823.20,
        "recurring_count": 24,
        "recurring_eur": 909.30,
        "billing_mode": "upfront_plus_recurring",
        "target_segment": "B2B-first",
        "status": "active",
        "agents": 10,
        "infrastructure": "Private Cloud",
        "support": "Priority (24h)",
        "recommended": True,
        "features": [
            "10 KI-Agenten",
            "Private Cloud Infrastructure",
            "Priority Support (24h Response)",
            "CRM/ERP-Integrations-Kit (SAP, HubSpot, Salesforce)",
            "Advanced Monitoring & Analytics",
            "Wöchentliches Reporting",
            "Dedizierter Onboarding-Manager",
        ],
        "payment_products": {
            "activation": {
                "product_code": "growth_activation_30",
                "invoice_type": "deposit",
                "description": "Aktivierungsanzahlung (30 %) — Growth AI Agenten AG",
            },
            "recurring": {
                "product_code": "growth_recurring_24",
                "invoice_type": "monthly",
                "description": "Monatliche Folgerate — Growth AI Agenten AG",
            },
        },
    },
}

# VAT rate (NL BTW)
VAT_RATE = 21

# ═══════════════════════════════════════════════════
# SERVICE CATALOG — Apps, Websites, Bundles
# ═══════════════════════════════════════════════════
SERVICE_CATALOG = {
    "web_starter": {
        "tariff_number": "NXA-WEB-S-2990",
        "slug": "website-starter",
        "name": "Website Starter",
        "category": "website",
        "price_eur": 2990.00,
        "billing_mode": "one_time",
        "features": [
            "Responsive Business Website (bis 5 Seiten)",
            "CI-konformes Design",
            "SEO-Grundoptimierung",
            "Kontaktformular",
            "SSL-Zertifikat",
            "CMS-Integration (WordPress/Headless)",
            "1 Monat Support inklusive",
        ],
        "delivery_weeks": 3,
        "target": "KMU, Startups",
        "status": "active",
    },
    "web_professional": {
        "tariff_number": "NXA-WEB-P-7490",
        "slug": "website-professional",
        "name": "Website Professional",
        "category": "website",
        "price_eur": 7490.00,
        "billing_mode": "one_time",
        "features": [
            "Responsive Business Website (bis 15 Seiten)",
            "Custom Design mit Animationen",
            "SEO-Volloptimierung",
            "Blog/News-System",
            "Kontakt- und Buchungsformulare",
            "Performance-Optimierung (Lighthouse 90+)",
            "Analytics-Integration",
            "3 Monate Support inklusive",
        ],
        "delivery_weeks": 5,
        "target": "Mittelstand",
        "status": "active",
    },
    "web_enterprise": {
        "tariff_number": "NXA-WEB-E-14900",
        "slug": "website-enterprise",
        "name": "Website Enterprise",
        "category": "website",
        "price_eur": 14900.00,
        "billing_mode": "one_time",
        "features": [
            "Enterprise-Website (unbegrenzte Seiten)",
            "Headless CMS (Strapi/Sanity)",
            "Multi-Language-Support",
            "E-Commerce-Integration",
            "Custom API-Anbindungen",
            "Performance-Optimierung (Lighthouse 95+)",
            "Barrierefreiheit (WCAG 2.1 AA)",
            "6 Monate Support inklusive",
            "SLA-gesicherter Betrieb",
        ],
        "delivery_weeks": 8,
        "target": "Enterprise, Konzerne",
        "status": "active",
    },
    "app_mvp": {
        "tariff_number": "NXA-APP-MVP-9900",
        "slug": "app-mvp",
        "name": "App MVP",
        "category": "app",
        "price_eur": 9900.00,
        "billing_mode": "one_time",
        "features": [
            "Cross-Platform App (iOS + Android)",
            "React Native / Flutter",
            "Bis zu 5 Kernfeatures",
            "Backend-API (FastAPI/Node)",
            "User Authentication",
            "Push Notifications",
            "App Store Deployment",
            "2 Monate Support inklusive",
        ],
        "delivery_weeks": 8,
        "target": "Startups, Product Teams",
        "status": "active",
    },
    "app_professional": {
        "tariff_number": "NXA-APP-P-24900",
        "slug": "app-professional",
        "name": "App Professional",
        "category": "app",
        "price_eur": 24900.00,
        "billing_mode": "one_time",
        "features": [
            "Cross-Platform App (iOS + Android + Web)",
            "Unbegrenzte Features",
            "Custom Backend mit Skalierung",
            "Admin-Dashboard",
            "Payment-Integration",
            "CRM/ERP-Anbindung",
            "Analytics & Monitoring",
            "App Store Optimization (ASO)",
            "6 Monate Support inklusive",
        ],
        "delivery_weeks": 14,
        "target": "Mittelstand, Scale-ups",
        "status": "active",
    },
    "ai_addon_chatbot": {
        "tariff_number": "NXA-AI-CB-249",
        "slug": "ai-chatbot-addon",
        "name": "KI-Chatbot Add-on",
        "category": "ai_addon",
        "price_monthly_eur": 249.00,
        "billing_mode": "monthly",
        "features": [
            "KI-gesteuerter Website-Chatbot",
            "Training auf Unternehmensdaten",
            "Lead-Qualifizierung",
            "Terminbuchung",
            "Mehrsprachig (DE/EN/NL)",
            "Analyse-Dashboard",
        ],
        "target": "Alle Unternehmen",
        "status": "active",
    },
    "ai_addon_automation": {
        "tariff_number": "NXA-AI-AUTO-499",
        "slug": "ai-automation-addon",
        "name": "KI-Prozessautomation Add-on",
        "category": "ai_addon",
        "price_monthly_eur": 499.00,
        "billing_mode": "monthly",
        "features": [
            "Workflow-Automation (Zapier/n8n/custom)",
            "E-Mail-Automation",
            "Dokumentenverarbeitung",
            "CRM-Sync",
            "API-Integrationen",
            "Monitoring & Alerting",
        ],
        "target": "KMU, Mittelstand",
        "status": "active",
    },
    "seo_starter": {
        "tariff_number": "NXA-SEO-S-799",
        "slug": "seo-starter",
        "name": "SEO Starter",
        "category": "seo",
        "price_monthly_eur": 799.00,
        "billing_mode": "monthly",
        "min_months": 6,
        "features": [
            "Keyword-Recherche (50 Keywords)",
            "On-Page-Optimierung (5 Seiten/Mo.)",
            "Monatlicher SEO-Report",
            "Core Web Vitals Monitoring",
            "Google Search Console Setup & Management",
            "Technisches SEO-Audit (quartalsweise)",
        ],
        "target": "KMU, Startups",
        "status": "active",
    },
    "seo_growth": {
        "tariff_number": "NXA-SEO-G-1499",
        "slug": "seo-growth",
        "name": "SEO Growth",
        "category": "seo",
        "price_monthly_eur": 1499.00,
        "billing_mode": "monthly",
        "min_months": 6,
        "recommended": True,
        "features": [
            "Keyword-Recherche (200 Keywords)",
            "On-Page-Optimierung (15 Seiten/Mo.)",
            "Wöchentlicher SEO-Report",
            "Content-Strategie & KI-Briefings",
            "Technisches SEO (monatlich)",
            "Linkbuilding-Strategie",
            "Wettbewerberanalyse",
            "Multilingual SEO (DE/NL/EN)",
        ],
        "target": "Mittelstand, Scale-ups",
        "status": "active",
    },
    "seo_enterprise": {
        "tariff_number": "NXA-SEO-E-IND",
        "slug": "seo-enterprise",
        "name": "SEO Enterprise",
        "category": "seo",
        "price_monthly_eur": 0,
        "billing_mode": "custom",
        "features": [
            "Unbegrenzte Keywords",
            "Tagesaktuelle Reports & Dashboards",
            "Vollständige Content-Produktion",
            "Dediziertes SEO-Team",
            "International SEO (5+ Märkte)",
            "API-Zugang & Custom Reporting",
            "Executive Quarterly Reviews",
        ],
        "target": "Enterprise, Konzerne",
        "status": "active",
    },
}

BUNDLE_CATALOG = {
    "digital_starter": {
        "tariff_number": "NXA-BDL-DS-3990",
        "slug": "digital-starter-bundle",
        "name": "Digital Starter Bundle",
        "description": "Website Starter + SEO Starter (3 Monate) — der ideale Einstieg für KMU.",
        "includes": ["web_starter", "seo_starter"],
        "bundle_price_eur": 3990.00,
        "savings_eur": 299.00,
        "savings_desc": "Statt 4.289 EUR (Website 2.990 + SEO 3x 799/Mo. anteilig)",
        "billing_mode": "one_time_plus_monthly",
        "one_time_eur": 2990.00,
        "monthly_eur": 333.33,
        "monthly_months": 3,
        "status": "active",
    },
    "growth_digital": {
        "tariff_number": "NXA-BDL-GD-17490",
        "slug": "growth-digital-bundle",
        "name": "Growth Digital Bundle",
        "description": "Website Professional + SEO Growth (6 Monate) + KI-Chatbot — 15 % Bundle-Rabatt.",
        "includes": ["web_professional", "seo_growth", "ai_addon_chatbot"],
        "bundle_price_eur": 17490.00,
        "savings_eur": 1977.00,
        "savings_desc": "Statt 19.467 EUR — 15 % Bundle-Rabatt",
        "billing_mode": "custom",
        "one_time_website_eur": 6370.00,
        "seo_monthly_eur": 1274.15,
        "seo_months": 6,
        "chatbot_monthly_eur": 211.75,
        "chatbot_months": 6,
        "status": "active",
        "badge": "BELIEBT",
    },
    "enterprise_digital": {
        "tariff_number": "NXA-BDL-ED-39900",
        "slug": "enterprise-digital-bundle",
        "name": "Enterprise Digital Bundle",
        "description": "Website Enterprise + App + SEO Enterprise + Growth AI Agenten AG + dediziertes Projektteam.",
        "includes": ["web_enterprise", "app_professional", "seo_enterprise", "growth"],
        "bundle_price_eur": 39900.00,
        "savings_eur": 0,
        "savings_desc": "Individuelles Angebot — ab 39.900 EUR",
        "billing_mode": "custom",
        "status": "active",
    },
}

# ═══════════════════════════════════════════════════
# COMPLIANCE & TRUST METADATA
# ═══════════════════════════════════════════════════
COMPLIANCE_STATUS = {
    "gdpr": {"status": "implemented", "label": "DSGVO / AVG", "detail": "Verordnung (EU) 2016/679 — vollständig umgesetzt"},
    "eu_ai_act": {"status": "implemented", "label": "EU AI Act", "detail": "Verordnung (EU) 2024/1689 — Transparenz- und Kennzeichnungspflichten umgesetzt"},
    "uavg": {"status": "implemented", "label": "UAVG (NL)", "detail": "Uitvoeringswet AVG — niederländische Datenschutz-Implementierung"},
    "iso_27001": {"status": "aligned", "label": "ISO/IEC 27001", "detail": "Informationssicherheits-Managementsystem — orientiert, nicht zertifiziert"},
    "iso_27701": {"status": "aligned", "label": "ISO/IEC 27701", "detail": "Privacy Information Management — orientiert, nicht zertifiziert"},
    "pci_dss": {"status": "delegated", "label": "PCI DSS", "detail": "Zahlungssicherheit via Revolut (PCI DSS Level 1 zertifiziert)"},
    "ssl_tls": {"status": "implemented", "label": "SSL/TLS", "detail": "Verschlüsselte Übertragung aller Daten"},
    "eu_hosting": {"status": "implemented", "label": "EU-Hosting", "detail": "Datenverarbeitung ausschließlich in EU-Rechenzentren"},
}

# ═══════════════════════════════════════════════════
# PRODUCT DESCRIPTIONS — Professional marketing/legal content
# ═══════════════════════════════════════════════════
PRODUCT_DESCRIPTIONS = {
    "starter": {
        "what": "Einstiegstarif für den Aufbau KI-gestützter Geschäftsprozesse mit zwei dedizierten KI-Agenten in einer geteilten Cloud-Umgebung.",
        "for_whom": "KMU, Startups und Unternehmen, die erste KI-Automatisierungen einführen möchten, ohne eigene Infrastruktur aufzubauen.",
        "results": "Automatisierung wiederkehrender Aufgaben, schnellere Reaktionszeiten, Entlastung des Teams bei Routineprozessen.",
        "included": "2 KI-Agenten, Shared Cloud Infrastructure, E-Mail-Support (48h), Basis-Integrationen (REST API), Standard-Monitoring, monatlicher Performance-Report.",
        "not_included": "CRM/ERP-Kit, dedizierter Onboarding-Manager, Private Cloud, Priority Support.",
        "process": "Bedarfsanalyse → Konzeptfreigabe → Setup & Konfiguration → Testphase → Go-Live. Ca. 3–4 Wochen.",
        "prerequisites": "Zugang zu den Systemen, die angebunden werden sollen. Ansprechpartner für fachliche Abstimmung.",
        "contract_terms": "24 Monate Laufzeit. 30 % Aktivierungsanzahlung bei Auftragserteilung (3.592,80 EUR netto). Restbetrag in 24 gleichen Monatsraten à 349,30 EUR netto.",
        "support": "E-Mail-Support mit Reaktionszeit bis 48 Stunden (Werktage).",
        "reporting": "Monatlicher Performance-Report mit KPI-Übersicht, Agenten-Auslastung und Optimierungsempfehlungen.",
        "infrastructure": "Shared Cloud Infrastructure (EU-Hosting, Frankfurt/Amsterdam). 99,5 % Verfügbarkeit.",
    },
    "growth": {
        "what": "Professioneller Tarif für den skalierten Einsatz von KI-Agenten mit dedizierten Ressourcen, erweitertem Support und CRM/ERP-Integration.",
        "for_whom": "Mittelständische Unternehmen, Scale-ups und Organisationen mit komplexen Prozesslandschaften und mehreren Abteilungen.",
        "results": "Skalierbare Prozessautomation, tiefere Systemintegration, kürzere Durchlaufzeiten, datengestützte Entscheidungsgrundlagen.",
        "included": "10 KI-Agenten, Private Cloud Infrastructure, Priority Support (24h), CRM/ERP-Kit (SAP, HubSpot, Salesforce), Advanced Monitoring & Analytics, wöchentlicher Report, dedizierter Onboarding-Manager.",
        "not_included": "Enterprise-SLA mit garantiertem 4h-Support, benutzerdefinierte ML-Modelle.",
        "process": "Bedarfsanalyse → Architektur-Workshop → Setup & Integration → Testphase → Go-Live → Onboarding. Ca. 4–6 Wochen.",
        "prerequisites": "Systemzugänge, fachlicher Ansprechpartner, Klarheit über Zielprozesse. Optional: API-Dokumentation bestehender Systeme.",
        "contract_terms": "24 Monate Laufzeit. 30 % Aktivierungsanzahlung bei Auftragserteilung (9.352,80 EUR netto). Restbetrag in 24 gleichen Monatsraten à 909,30 EUR netto.",
        "support": "Priority Support mit Reaktionszeit bis 24 Stunden (inkl. Wochenende bei kritischen Incidents).",
        "reporting": "Wöchentlicher Performance-Report mit detaillierten KPIs, Agenten-Analytics, Integrationsmetriken und strategischen Empfehlungen.",
        "infrastructure": "Private Cloud Infrastructure (EU-Hosting, dedizierte Ressourcen). 99,9 % Verfügbarkeit. Automatische Skalierung.",
    },
    "web_starter": {
        "what": "Professionelle Business-Website mit bis zu 5 Seiten, responsivem Design und SEO-Grundoptimierung.",
        "for_whom": "Einzelunternehmer, Startups und KMU, die eine moderne Online-Präsenz benötigen.",
        "results": "Sichtbarkeit im Web, professioneller Ersteindruck, Grundlage für Kundengewinnung.",
        "included": "Responsive Design, CI-konformes Layout, SEO-Basis, Kontaktformular, SSL, CMS-Integration, 1 Monat Support.",
        "not_included": "Blog-System, Animationen, Multi-Language, E-Commerce, Analytics-Integration.",
        "process": "Briefing → Designentwurf → Umsetzung → Feedbackrunde → Go-Live. Ca. 3 Wochen.",
        "contract_terms": "Einmaliger Projektpreis 2.990 EUR netto. 50 % bei Auftragserteilung, 50 % bei Abnahme.",
    },
    "web_professional": {
        "what": "Umfangreiche Business-Website mit bis zu 15 Seiten, Animationen, Blog-System und Analytics-Integration.",
        "for_whom": "Mittelständische Unternehmen, die ihre digitale Präsenz ausbauen und Content-Marketing starten möchten.",
        "results": "Professioneller Web-Auftritt, Content-Marketing-Basis, Lead-Generierung, messbare Performance.",
        "included": "Alle Starter-Features plus: Animationen, Blog/News, Google Analytics 4, Mehrsprachig (DE/NL/EN), Performance-Optimierung, 3 Monate Support.",
        "not_included": "Headless CMS, E-Commerce, Custom API-Anbindungen, WCAG-Barrierefreiheit.",
        "process": "Briefing → Konzept → Designentwurf → Umsetzung → Content-Einpflege → Testing → Go-Live. Ca. 5 Wochen.",
        "contract_terms": "Einmaliger Projektpreis 7.490 EUR netto. 50 % bei Auftragserteilung, 50 % bei Abnahme.",
    },
    "seo_starter": {
        "what": "KI-gesteuerte Suchmaschinenoptimierung mit Keyword-Recherche, On-Page-Optimierung und monatlichem Reporting.",
        "for_whom": "KMU und Startups, die organisch wachsen möchten, ohne ein dediziertes SEO-Team aufzubauen.",
        "results": "Verbesserte Sichtbarkeit bei relevanten Suchbegriffen, technisch saubere Website, nachvollziehbare Fortschritte.",
        "included": "50 Keywords, On-Page (5 Seiten/Mo.), monatlicher Report, Core Web Vitals, Google Search Console, quartalsweiser Tech-Audit.",
        "not_included": "Content-Strategie, Linkbuilding, Multilingual SEO, wöchentliches Reporting.",
        "process": "SEO-Audit → Keyword-Strategie → technische Optimierung → monatliche On-Page-Runden → Reporting.",
        "contract_terms": "799 EUR/Monat netto. Mindestlaufzeit 6 Monate. Monatliche Abrechnung.",
    },
    "seo_growth": {
        "what": "Umfassende KI-gesteuerte SEO mit Content-Strategie, Linkbuilding, Wettbewerberanalyse und multilingualer Optimierung.",
        "for_whom": "Mittelständische Unternehmen und Scale-ups, die in kompetitiven Märkten organisch dominieren wollen.",
        "results": "Signifikante Ranking-Verbesserungen, qualifizierter organischer Traffic, Content-Pipeline, internationales Wachstum.",
        "included": "200 Keywords, On-Page (15 Seiten/Mo.), wöchentlicher Report, Content-Strategie & KI-Briefings, technisches SEO (monatlich), Linkbuilding, Wettbewerberanalyse, Multilingual SEO (DE/NL/EN).",
        "not_included": "Dediziertes SEO-Team, tagesaktuelle Reports, vollständige Content-Produktion.",
        "process": "SEO-Audit → Keyword-Strategie → technische Optimierung → Content-Plan → monatliche Zyklen → Linkbuilding → wöchentliche Reports.",
        "contract_terms": "1.499 EUR/Monat netto. Mindestlaufzeit 6 Monate. Monatliche Abrechnung. Empfohlener Tarif.",
    },
    "web_enterprise": {
        "what": "Enterprise-Website mit unbegrenzten Seiten, Headless CMS, E-Commerce-Integration und WCAG-Barrierefreiheit.",
        "for_whom": "Enterprise-Unternehmen und Konzerne mit komplexen Anforderungen an Content-Management, Internationalisierung und Barrierefreiheit.",
        "results": "Vollständige digitale Präsenz, skalierbare Content-Infrastruktur, E-Commerce-fähig, barrierefrei und international.",
        "included": "Alle Professional-Features, Headless CMS (Strapi/Sanity), E-Commerce-Integration, Multi-Language-Support, Custom API-Anbindungen, Performance-Optimierung (Lighthouse 95+), WCAG 2.1 AA Barrierefreiheit, SLA-gesicherter Betrieb, dedizierter Projektmanager, 6 Monate Support.",
        "not_included": "Laufende Content-Produktion, externe Marketplace-Integrationen über Standardumfang hinaus.",
        "process": "Discovery → Architektur-Workshop → Design → Entwicklung → Content-Migration → QA → Go-Live. Ca. 8 Wochen.",
        "contract_terms": "Einmaliger Projektpreis 14.900 EUR netto. 50 % bei Auftragserteilung, 50 % bei Abnahme.",
    },
    "app_mvp": {
        "what": "Cross-Platform App (iOS + Android) mit bis zu 5 Kernfeatures, User-Authentifizierung und Push-Benachrichtigungen.",
        "for_whom": "Startups und Product Teams, die eine Idee schnell am Markt validieren möchten.",
        "results": "Marktreifes MVP, validiertes Produkt, Nutzerfeedback, Grundlage für Skalierung.",
        "included": "iOS + Android (React Native/Flutter), 5 Kernfunktionen, User Authentication, Push Notifications, Backend-API (FastAPI/Node), App Store Deployment, 2 Monate Support.",
        "not_included": "Admin-Dashboard, Payment-Integration, CRM-Anbindung, Analytics-Dashboard.",
        "process": "Product Workshop → UI/UX Design → Entwicklung → Testing → App Store Deployment. Ca. 8 Wochen.",
        "contract_terms": "Einmaliger Projektpreis 9.900 EUR netto. 50 % bei Auftragserteilung, 50 % bei Abnahme.",
    },
    "app_professional": {
        "what": "Full-Stack App mit unbegrenzten Features, Admin-Dashboard, Payment-Integration und CRM/ERP-Anbindung.",
        "for_whom": "Mittelständische Unternehmen und Scale-ups, die eine vollständige App-Lösung mit professionellem Backend benötigen.",
        "results": "Skalierbare App-Plattform, professionelles Admin-Backend, integrierte Zahlungsabwicklung, CRM-Synchronisation.",
        "included": "Alle MVP-Features, Admin-Dashboard, Payment-Integration, CRM/ERP-Anbindung, Analytics & Reporting, App Store Optimization (ASO), dedizierter Support, 6 Monate Support.",
        "not_included": "Laufende Marketingkampagnen, externe API-Anbindungen über Standardumfang hinaus.",
        "process": "Product Workshop → Architektur → UI/UX → Entwicklung → Integration → QA → Deployment → Onboarding. Ca. 14 Wochen.",
        "contract_terms": "Einmaliger Projektpreis 24.900 EUR netto. 50 % bei Auftragserteilung, 50 % bei Abnahme.",
    },
    "seo_enterprise": {
        "what": "Enterprise-SEO mit dediziertem Team, tagesaktuellen Reports, vollständiger Content-Produktion und internationaler Ausrichtung.",
        "for_whom": "Konzerne und international agierende Unternehmen mit komplexen SEO-Anforderungen in mehreren Märkten.",
        "results": "Marktdominanz in organischen Suchergebnissen, internationale Sichtbarkeit, vollständige Content-Pipeline.",
        "included": "Unbegrenzte Keywords, tagesaktuelle Reports & Dashboards, vollständige Content-Produktion, dediziertes SEO-Team, International SEO (5+ Märkte), API-Zugang & Custom Reporting, Executive Quarterly Reviews.",
        "not_included": "Paid-Media-Kampagnen, Social-Media-Management.",
        "process": "Executive Workshop → Audit → Strategie → Umsetzung → fortlaufende Optimierung → Quarterly Reviews.",
        "contract_terms": "Individuelles Angebot auf Anfrage. Mindestlaufzeit 12 Monate.",
    },
    "ai_addon_chatbot": {
        "what": "KI-gesteuerter Website-Chatbot für Lead-Qualifizierung, Terminbuchung und Kundenservice.",
        "for_whom": "Unternehmen aller Größen, die ihre Website-Besucher aktiv qualifizieren und Kundenservice automatisieren möchten.",
        "results": "Automatisierte Lead-Qualifizierung, 24/7-Verfügbarkeit, höhere Conversion-Rate, reduzierter Support-Aufwand.",
        "included": "KI-Chatbot mit Training auf Unternehmensdaten, Lead-Qualifizierung, Terminbuchung, CRM-Sync, Mehrsprachig (DE/EN/NL), Analyse-Dashboard.",
        "not_included": "Individuelle ML-Modelle, Telefon-Integration.",
        "process": "Briefing → Training → Integration → Testing → Go-Live. Ca. 1–2 Wochen.",
        "contract_terms": "249 EUR/Monat netto. Monatlich kündbar. Keine Mindestlaufzeit.",
    },
    "ai_addon_automation": {
        "what": "KI-gesteuerte Prozessautomation für Workflows, E-Mail-Automation und CRM-Synchronisation.",
        "for_whom": "KMU und Mittelstand, die manuelle Prozesse automatisieren und Systembrüche eliminieren möchten.",
        "results": "Automatisierte Workflows, eliminierte Medienbrüche, synchronisierte Systeme, messbare Zeitersparnis.",
        "included": "Workflow-Automation (Zapier/n8n/custom), E-Mail-Automation, Dokumentenverarbeitung, CRM-Sync, API-Integrationen, Monitoring & Alerting.",
        "not_included": "Individuelle ML-Modelle, Hardware-Integration.",
        "process": "Prozessanalyse → Automation-Design → Implementierung → Testing → Go-Live. Ca. 2–3 Wochen.",
        "contract_terms": "499 EUR/Monat netto. Monatlich kündbar. Keine Mindestlaufzeit.",
    },
}

ISO_GAP_ANALYSIS = {
    "iso_27001": {
        "name": "ISO/IEC 27001:2022 — Informationssicherheit",
        "controls": {
            "A.5_Organizational": {"status": "fulfilled", "note": "Sicherheitsrichtlinien dokumentiert, Rollen definiert"},
            "A.6_People": {"status": "fulfilled", "note": "Vertraulichkeitsvereinbarungen, Zugangskontrollen"},
            "A.7_Physical": {"status": "delegated", "note": "Cloud-Hosting — physische Sicherheit beim Anbieter"},
            "A.8_Technological": {"status": "fulfilled", "note": "Argon2 Hashing, JWT Token, Rate Limiting, HTTPS"},
            "A.8_Access_Control": {"status": "fulfilled", "note": "RBAC, Admin-only Routen, Token-Expiry"},
            "A.8_Cryptography": {"status": "fulfilled", "note": "AES-256 at rest, TLS 1.3 in transit"},
            "A.8_Logging": {"status": "fulfilled", "note": "Audit-Logs für alle kommerziellen Events"},
            "A.8_Network": {"status": "fulfilled", "note": "CORS-Konfiguration, API-Rate-Limiting"},
            "A.8_Vulnerability": {"status": "partial", "note": "Regelmäßige Updates, kein formales Penetration-Testing"},
            "A.8_Data_Classification": {"status": "partial", "note": "Kundendaten separiert, keine formale Klassifizierung"},
            "A.8_Backup": {"status": "delegated", "note": "MongoDB Atlas automatische Backups"},
        },
    },
    "iso_27701": {
        "name": "ISO/IEC 27701:2019 — Privacy Information Management",
        "controls": {
            "Privacy_by_Design": {"status": "fulfilled", "note": "Datenminimierung, Zweckbindung, Speicherfristen"},
            "Privacy_by_Default": {"status": "fulfilled", "note": "Minimale Datenerfassung, keine Tracking-Cookies"},
            "Data_Subject_Rights": {"status": "fulfilled", "note": "Auskunft, Loeschung, Berichtigung implementiert"},
            "Data_Processing_Records": {"status": "fulfilled", "note": "Audit-Logs, Event-Tracking"},
            "Third_Party_Management": {"status": "fulfilled", "note": "SCC mit Auftragsverarbeitern (Resend, OpenAI)"},
            "Data_Breach_Notification": {"status": "partial", "note": "Prozess definiert, kein automatisiertes Meldesystem"},
            "DPIA": {"status": "partial", "note": "Risikobewertung durchgeführt, kein formales DPIA-Dokument"},
            "DPO": {"status": "open", "note": "Kein benannter Datenschutzbeauftragter (bei KMU optional)"},
        },
    },
}

# ═══════════════════════════════════════════════════
# OFFER & INVOICE STATES
# ═══════════════════════════════════════════════════
OFFER_STATES = [
    "draft", "generated", "sent", "opened", "access_verified",
    "accepted", "declined", "revision_requested",
]

INVOICE_STATES = [
    "created", "sent", "payment_pending", "payment_completed",
    "payment_failed", "partially_paid", "overdue", "refunded",
]


def get_tariff(tier_key: str) -> dict:
    """Get tariff config by key"""
    return TARIFF_CONFIG.get(tier_key, {})


def calc_contract(tier_key: str) -> dict:
    """Calculate full contract values from tariff config"""
    tariff = TARIFF_CONFIG.get(tier_key)
    if not tariff or tariff.get("status") != "active":
        return {}
    return {
        "tier": tier_key,
        "tier_name": tariff["name"],
        "tariff_number": tariff["tariff_number"],
        "reference_monthly_eur": tariff["reference_monthly_eur"],
        "contract_months": tariff["contract_months"],
        "upfront_percent": tariff["upfront_percent"],
        "total_contract_eur": tariff["total_contract_eur"],
        "upfront_eur": tariff["upfront_eur"],
        "remaining_eur": tariff["remaining_eur"],
        "recurring_count": tariff["recurring_count"],
        "recurring_eur": tariff["recurring_eur"],
        "vat_rate": VAT_RATE,
        "upfront_vat": round(tariff["upfront_eur"] * VAT_RATE / 100, 2),
        "upfront_gross": round(tariff["upfront_eur"] * (1 + VAT_RATE / 100), 2),
        "currency": "EUR",
    }


# ═══════════════════════════════════════════════════
# SEQUENTIAL NUMBERING
# ═══════════════════════════════════════════════════

async def get_next_number(db, sequence_type: str) -> str:
    """Atomic counter for invoice/quote numbers"""
    result = await db.counters.find_one_and_update(
        {"_id": sequence_type},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = result["seq"]
    if sequence_type == "invoice":
        base_major = 14552
        base_minor = 5457
        total = base_minor + seq - 1
        return f"{base_major}.{total}.nf"
    elif sequence_type == "quote":
        base = 45525545 + seq - 1
        prefix = str(base)[:5]
        suffix = str(base)[5:]
        return f"ag{prefix}.{suffix}"
    return f"{sequence_type}-{seq}"


# ═══════════════════════════════════════════════════
# REVOLUT PAYMENT
# ═══════════════════════════════════════════════════

REVOLUT_SECRET_KEY = os.environ.get("REVOLUT_SECRET_KEY", "")
REVOLUT_PUBLIC_KEY = os.environ.get("REVOLUT_PUBLIC_KEY", "")
REVOLUT_API_URL = os.environ.get("REVOLUT_API_URL", "https://merchant.revolut.com")
REVOLUT_API_VERSION = os.environ.get("REVOLUT_API_VERSION", "2025-12-04")


async def create_revolut_order(
    amount_cents: int, currency: str, customer_email: str,
    description: str, merchant_order_id: str,
) -> dict:
    """Create a Revolut Merchant API payment order"""
    if not REVOLUT_SECRET_KEY:
        logger.warning("Revolut secret key not configured — returning bank transfer fallback")
        return {"error": "revolut_not_configured", "fallback": "bank_transfer"}

    headers = {
        "Authorization": f"Bearer {REVOLUT_SECRET_KEY}",
        "Revolut-Api-Version": REVOLUT_API_VERSION,
        "Content-Type": "application/json",
    }
    payload = {
        "amount": amount_cents,
        "currency": currency,
        "customer": {"email": customer_email},
        "description": description,
        "merchant_order_ext_ref": merchant_order_id,
        "capture_mode": "automatic",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{REVOLUT_API_URL}/api/1.0/orders",
                headers=headers,
                json=payload,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.info(f"Revolut order created: {data.get('id')}")
                return {
                    "order_id": data.get("id"),
                    "token": data.get("token"),
                    "state": data.get("state"),
                    "checkout_url": data.get("checkout_url"),
                    "public_id": data.get("public_id"),
                }
            else:
                logger.error(f"Revolut order failed: {resp.status_code} {resp.text}")
                return {"error": f"revolut_{resp.status_code}", "details": resp.text}
        except Exception as e:
            logger.error(f"Revolut API error: {e}")
            return {"error": str(e)}


async def get_revolut_order(order_id: str) -> dict:
    """Retrieve Revolut order status"""
    headers = {
        "Authorization": f"Bearer {REVOLUT_SECRET_KEY}",
        "Revolut-Api-Version": REVOLUT_API_VERSION,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{REVOLUT_API_URL}/api/1.0/orders/{order_id}",
            headers=headers,
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.text}


def verify_revolut_webhook(
    signing_secret: str, timestamp: str, raw_body: str, signature: str,
) -> bool:
    """Verify Revolut webhook HMAC-SHA256 signature"""
    payload_to_sign = f"v1.{timestamp}.{raw_body}"
    expected = "v1=" + hmac.new(
        signing_secret.encode(),
        payload_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ═══════════════════════════════════════════════════
# MAGIC LINK / SECURE ACCESS
# ═══════════════════════════════════════════════════

def generate_access_token(customer_id: str, document_type: str = "all") -> dict:
    """Generate a time-limited magic link token (24h)"""
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    return {
        "token": token,
        "token_hash": token_hash,
        "customer_id": customer_id,
        "document_type": document_type,
        "expires_at": expires.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def verify_access_token(provided_token: str, stored_hash: str, expires_at: str) -> bool:
    """Verify a magic link token"""
    if datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
        return False
    computed_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    return hmac.compare_digest(computed_hash, stored_hash)


# ═══════════════════════════════════════════════════
# PDF GENERATION
# ═══════════════════════════════════════════════════

CI_ORANGE = colors.Color(255 / 255, 155 / 255, 122 / 255)
CI_DARK = colors.Color(12 / 255, 17 / 255, 23 / 255)
CI_GRAY = colors.Color(120 / 255, 130 / 255, 145 / 255)


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "BrandTitle", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=18, textColor=CI_DARK, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "BrandSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10, textColor=CI_GRAY, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "SectionHead", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, textColor=CI_DARK, spaceBefore=16, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "BodyText2", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9.5, textColor=CI_DARK, leading=14,
    ))
    styles.add(ParagraphStyle(
        "SmallGray", parent=styles["Normal"], fontName="Helvetica",
        fontSize=7.5, textColor=CI_GRAY, leading=10,
    ))
    styles.add(ParagraphStyle(
        "RightAligned", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9.5, textColor=CI_DARK, alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        "TotalBold", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=11, textColor=CI_DARK, alignment=TA_RIGHT,
    ))
    return styles


def _fmt_eur(amount) -> str:
    """Format amount to EUR string (accepts float or int cents)"""
    if isinstance(amount, int) and amount > 10000:
        val = amount / 100
    else:
        val = float(amount)
    formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} EUR"


def _header_footer(canvas, doc, doc_type, doc_number, doc_date):
    """Draw CI header and footer on each page"""
    canvas.saveState()
    canvas.setStrokeColor(CI_ORANGE)
    canvas.setLineWidth(2)
    canvas.line(20 * mm, A4[1] - 18 * mm, A4[0] - 20 * mm, A4[1] - 18 * mm)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(CI_DARK)
    canvas.drawString(20 * mm, A4[1] - 14 * mm, "NeXify")
    canvas.setFillColor(CI_ORANGE)
    w = canvas.stringWidth("NeXify", "Helvetica-Bold", 14)
    canvas.drawString(20 * mm + w, A4[1] - 14 * mm, "AI")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CI_GRAY)
    canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 12 * mm, f"{doc_type} {doc_number}")
    canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 16 * mm, f"Datum: {doc_date}")
    canvas.setStrokeColor(CI_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 22 * mm, A4[0] - 20 * mm, 22 * mm)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(CI_GRAY)
    y = 18 * mm
    canvas.drawString(20 * mm, y,
        f"{COMPANY_DATA['name']} | {COMPANY_DATA['address_nl']['street']}, "
        f"{COMPANY_DATA['address_nl']['city']} | KvK: {COMPANY_DATA['kvk']}")
    canvas.drawString(20 * mm, y - 8,
        f"USt-ID: {COMPANY_DATA['vat_id']} | IBAN: {COMPANY_DATA['bank']['iban']} "
        f"| BIC: {COMPANY_DATA['bank']['bic']}")
    canvas.drawRightString(A4[0] - 20 * mm, y, f"Seite {doc.page}")
    canvas.restoreState()


def generate_quote_pdf(quote_data: dict) -> bytes:
    """Generate a CI-branded quote PDF with new tariff model"""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=28 * mm, bottomMargin=28 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = _build_styles()
    elements = []

    number = quote_data.get("quote_number", "---")
    date_str = quote_data.get("date", datetime.now(timezone.utc).strftime("%d.%m.%Y"))
    customer = quote_data.get("customer", {})
    calc = quote_data.get("calculation", {})
    tier_key = calc.get("tier", "starter")
    tariff = TARIFF_CONFIG.get(tier_key, {})

    elements.append(Spacer(1, 8 * mm))
    if customer.get("company"):
        elements.append(Paragraph(customer["company"], styles["BodyText2"]))
    if customer.get("name"):
        elements.append(Paragraph(customer["name"], styles["BodyText2"]))
    if customer.get("email"):
        elements.append(Paragraph(customer["email"], styles["SmallGray"]))
    elements.append(Spacer(1, 12 * mm))

    elements.append(Paragraph(f"Angebot {number}", styles["BrandTitle"]))
    elements.append(Paragraph(
        f"{tariff.get('name', '')} | Tarif-Nr. {tariff.get('tariff_number', '')}",
        styles["BrandSub"],
    ))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=CI_GRAY, spaceBefore=4, spaceAfter=12,
    ))

    elements.append(Paragraph(
        f"Sehr geehrte Damen und Herren,<br/><br/>"
        f"vielen Dank für Ihr Interesse an NeXify<font color='#ff9b7a'><b>AI</b></font>. "
        f"Nachfolgend unterbreiten wir Ihnen unser Angebot für das Produkt "
        f"<b>{tariff.get('name', '')}</b>.",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Leistungsumfang", styles["SectionHead"]))
    feat_data = [[Paragraph(f"- {f}", styles["BodyText2"])] for f in tariff.get("features", [])]
    if feat_data:
        feat_table = Table(feat_data, colWidths=[doc.width])
        feat_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(feat_table)
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Kommerzielle Konditionen", styles["SectionHead"]))
    fin_data = [
        [Paragraph("<b>Position</b>", styles["BodyText2"]),
         Paragraph("<b>Betrag</b>", styles["RightAligned"])],
        [Paragraph(f"Tarifpreis pro Monat ({tariff.get('name', '')})", styles["BodyText2"]),
         Paragraph(_fmt_eur(calc.get("reference_monthly_eur", 0)), styles["RightAligned"])],
        [Paragraph("Vertragslaufzeit", styles["BodyText2"]),
         Paragraph(f"{calc.get('contract_months', 24)} Monate", styles["RightAligned"])],
        [Paragraph("<b>Gesamtvertragswert (netto)</b>", styles["BodyText2"]),
         Paragraph(f"<b>{_fmt_eur(calc.get('total_contract_eur', 0))}</b>", styles["RightAligned"])],
        [Paragraph("", styles["BodyText2"]), Paragraph("", styles["RightAligned"])],
        [Paragraph("Aktivierungsanzahlung (30 %) — sofort fällig", styles["BodyText2"]),
         Paragraph(_fmt_eur(calc.get("upfront_eur", 0)), styles["RightAligned"])],
        [Paragraph(f"zzgl. {calc.get('vat_rate', 21)} % USt.", styles["SmallGray"]),
         Paragraph(_fmt_eur(calc.get("upfront_vat", 0)), styles["RightAligned"])],
        [Paragraph("<b>Aktivierungsanzahlung (brutto)</b>", styles["BodyText2"]),
         Paragraph(f"<b>{_fmt_eur(calc.get('upfront_gross', 0))}</b>", styles["RightAligned"])],
        [Paragraph("", styles["BodyText2"]), Paragraph("", styles["RightAligned"])],
        [Paragraph("Verbleibender Restbetrag (netto)", styles["BodyText2"]),
         Paragraph(_fmt_eur(calc.get("remaining_eur", 0)), styles["RightAligned"])],
        [Paragraph(f"Monatliche Folgerate ({calc.get('recurring_count', 24)} Raten)", styles["BodyText2"]),
         Paragraph(_fmt_eur(calc.get("recurring_eur", 0)), styles["RightAligned"])],
    ]
    fin_table = Table(fin_data, colWidths=[doc.width * 0.65, doc.width * 0.35])
    fin_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, CI_DARK),
        ("LINEBELOW", (0, 3), (-1, 3), 0.5, CI_ORANGE),
        ("LINEBELOW", (0, 7), (-1, 7), 0.5, CI_ORANGE),
        ("BACKGROUND", (0, 3), (-1, 3), colors.Color(255 / 255, 155 / 255, 122 / 255, 0.05)),
        ("BACKGROUND", (0, 7), (-1, 7), colors.Color(255 / 255, 155 / 255, 122 / 255, 0.05)),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Vertragsbedingungen", styles["SectionHead"]))
    elements.append(Paragraph(
        "- Vertragslaufzeit: 24 Monate ab Beauftragung<br/>"
        "- Aktivierungsanzahlung: 30 % des Gesamtvertragswerts, sofort fällig bei Beauftragung<br/>"
        "- Die Anzahlung deckt: Projektstart, Priorisierung, Setup, Kapazitätsreservierung, Implementierungsfreigabe<br/>"
        "- Restbetrag: In 24 gleichen monatlichen Folgeraten<br/>"
        "- Alle Preise verstehen sich zzgl. der gesetzlichen USt. (21 % NL / 19 % DE)<br/>"
        "- Gültigkeit dieses Angebots: 30 Tage ab Ausstellungsdatum<br/>"
        "- DSGVO- und EU-AI-Act-konforme Umsetzung garantiert<br/>"
        "- Gerichtsstand: Venlo, Niederlande (Burgerlijk Wetboek)",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("Zahlungsinformationen", styles["SectionHead"]))
    elements.append(Paragraph(
        f"<b>Online-Zahlung:</b> Sie erhalten einen sicheren Zahlungslink via Revolut Checkout.<br/><br/>"
        f"<b>Überweisung innerhalb des EWR:</b><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"Kontoinhaber: {COMPANY_DATA['bank']['account_holder']}<br/><br/>"
        f"<b>Überweisung von außerhalb des EWR:</b><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"BIC der zwischengeschalteten Bank: {COMPANY_DATA['bank']['intermediary_bic']}",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(
        "Wir freuen uns auf die Zusammenarbeit. Bei Fragen stehen wir Ihnen unter "
        f"<b>{COMPANY_DATA['phone']}</b> oder <b>{COMPANY_DATA['email']}</b> zur Verfügung.",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph("Mit freundlichen Grüßen,", styles["BodyText2"]))
    elements.append(Paragraph(
        f"<b>{COMPANY_DATA['ceo']}</b><br/>{COMPANY_DATA['ceo_title']}, NeXifyAI",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(
        "<font size='7' color='#78829a'>Datenschutzorientiert für den europäischen Rechtsraum entwickelt. "
        "DSGVO (EU) 2016/679 | EU AI Act (EU) 2024/1689 | ISO/IEC 27001 orientiert | EU-Hosting"
        "</font>",
        styles["SmallGray"],
    ))

    def make_header(canvas, doc):
        _header_footer(canvas, doc, "Angebot", number, date_str)

    doc.build(elements, onFirstPage=make_header, onLaterPages=make_header)
    return buf.getvalue()


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """Generate a CI-branded invoice PDF"""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=28 * mm, bottomMargin=28 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = _build_styles()
    elements = []

    number = invoice_data.get("invoice_number", "---")
    date_str = invoice_data.get("date", datetime.now(timezone.utc).strftime("%d.%m.%Y"))
    due_date = invoice_data.get("due_date", "")
    customer = invoice_data.get("customer", {})
    inv_type = invoice_data.get("type", "deposit")
    items = invoice_data.get("items", [])
    totals = invoice_data.get("totals", {})

    elements.append(Spacer(1, 8 * mm))
    if customer.get("company"):
        elements.append(Paragraph(customer["company"], styles["BodyText2"]))
    if customer.get("name"):
        elements.append(Paragraph(customer["name"], styles["BodyText2"]))
    if customer.get("email"):
        elements.append(Paragraph(customer["email"], styles["SmallGray"]))
    elements.append(Spacer(1, 12 * mm))

    type_labels = {
        "deposit": "Aktivierungsanzahlung",
        "monthly": "Monatsrechnung",
        "final": "Schlussrechnung",
        "correction": "Korrekturrechnung",
    }
    title = type_labels.get(inv_type, "Rechnung")
    elements.append(Paragraph(f"{title} {number}", styles["BrandTitle"]))
    if due_date:
        elements.append(Paragraph(f"Faellig am: {due_date}", styles["BrandSub"]))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=CI_GRAY, spaceBefore=4, spaceAfter=12,
    ))

    item_header = [
        Paragraph("<b>Pos.</b>", styles["BodyText2"]),
        Paragraph("<b>Beschreibung</b>", styles["BodyText2"]),
        Paragraph("<b>Betrag (netto)</b>", styles["RightAligned"]),
    ]
    item_rows = [item_header]
    for idx, item in enumerate(items, 1):
        item_rows.append([
            Paragraph(str(idx), styles["BodyText2"]),
            Paragraph(item.get("description", ""), styles["BodyText2"]),
            Paragraph(_fmt_eur(item.get("amount_net", 0)), styles["RightAligned"]),
        ])

    item_table = Table(item_rows, colWidths=[doc.width * 0.08, doc.width * 0.62, doc.width * 0.30])
    item_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, CI_DARK),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, CI_GRAY),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 6 * mm))

    total_data = [
        [Paragraph("Nettobetrag", styles["BodyText2"]),
         Paragraph(_fmt_eur(totals.get("net", 0)), styles["RightAligned"])],
        [Paragraph(f"USt. {totals.get('vat_rate', 21)} %", styles["BodyText2"]),
         Paragraph(_fmt_eur(totals.get("vat", 0)), styles["RightAligned"])],
        [Paragraph("<b>Gesamtbetrag (brutto)</b>", styles["BodyText2"]),
         Paragraph(f"<b>{_fmt_eur(totals.get('gross', 0))}</b>", styles["TotalBold"])],
    ]
    total_table = Table(total_data, colWidths=[doc.width * 0.65, doc.width * 0.35])
    total_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 1, CI_ORANGE),
        ("BACKGROUND", (0, -1), (-1, -1), colors.Color(255 / 255, 155 / 255, 122 / 255, 0.05)),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 8 * mm))

    ref = invoice_data.get("payment_reference", number)
    elements.append(Paragraph("Zahlungsinformationen", styles["SectionHead"]))
    elements.append(Paragraph(
        f"Bitte überweisen Sie den Betrag unter Angabe der Rechnungsnummer <b>{ref}</b>.<br/><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']}<br/>"
        f"BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"Kontoinhaber: {COMPANY_DATA['bank']['account_holder']}<br/><br/>"
        f"Von außerhalb des EWR zusätzlich:<br/>"
        f"BIC der zwischengeschalteten Bank: {COMPANY_DATA['bank']['intermediary_bic']}",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph(
        f"Bei Fragen zu dieser Rechnung wenden Sie sich bitte an "
        f"{COMPANY_DATA['email']} oder {COMPANY_DATA['phone']}.",
        styles["SmallGray"],
    ))

    def make_header(canvas, doc):
        _header_footer(canvas, doc, title, number, date_str)

    doc.build(elements, onFirstPage=make_header, onLaterPages=make_header)
    return buf.getvalue()


# ═══════════════════════════════════════════════════
# TARIFF COMPARISON SHEET PDF
# ═══════════════════════════════════════════════════

def generate_tariff_sheet_pdf(category: str = "all") -> bytes:
    """Generate a premium CI-branded tariff comparison PDF"""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=28 * mm, bottomMargin=28 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    styles = _build_styles()
    styles.add(ParagraphStyle(
        "SheetTitle", parent=styles["BrandTitle"], fontSize=22, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "SheetSub", parent=styles["BrandSub"], fontSize=9, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "CatTitle", parent=styles["SectionHead"], fontSize=13, spaceBefore=20, spaceAfter=10,
        textColor=CI_ORANGE,
    ))
    styles.add(ParagraphStyle(
        "CellText", parent=styles["BodyText2"], fontSize=7.5, leading=10,
    ))
    styles.add(ParagraphStyle(
        "CellBold", parent=styles["BodyText2"], fontName="Helvetica-Bold", fontSize=8, leading=11,
    ))
    styles.add(ParagraphStyle(
        "FootNote", parent=styles["SmallGray"], fontSize=6.5, leading=9,
    ))
    elements = []

    now_str = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    # Title
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph("Tarif- und Leistungsübersicht", styles["SheetTitle"]))
    elements.append(Paragraph(
        f"NeXifyAI | Stand: {now_str} | Alle Preise in EUR, zzgl. gesetzlicher USt.",
        styles["SheetSub"],
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=CI_ORANGE, spaceBefore=2, spaceAfter=12))

    # --- KI Agenten ---
    if category in ("all", "agents"):
        elements.append(Paragraph("KI-Agenten-Tarife", styles["CatTitle"]))
        agent_header = [
            Paragraph("<b>Merkmal</b>", styles["CellBold"]),
            Paragraph("<b>Starter AI Agenten AG</b>", styles["CellBold"]),
            Paragraph("<b>Growth AI Agenten AG</b>", styles["CellBold"]),
        ]
        st = TARIFF_CONFIG["starter"]
        gr = TARIFF_CONFIG["growth"]
        agent_rows = [agent_header]
        comparisons = [
            ("Tarif-Nr.", st["tariff_number"], gr["tariff_number"]),
            ("Monatspreis (Referenz)", f'{st["reference_monthly_eur"]:.2f} EUR', f'{gr["reference_monthly_eur"]:.2f} EUR'),
            ("KI-Agenten", str(st["agents"]), str(gr["agents"])),
            ("Infrastruktur", st["infrastructure"], gr["infrastructure"]),
            ("Support", st["support"], gr["support"]),
            ("Laufzeit", f'{st["contract_months"]} Monate', f'{gr["contract_months"]} Monate'),
            ("Anzahlung", f'{st["upfront_percent"]} %', f'{gr["upfront_percent"]} %'),
            ("Gesamtvertragswert", _fmt_eur(st["total_contract_eur"]), _fmt_eur(gr["total_contract_eur"])),
            ("Anzahlung (netto)", _fmt_eur(st["upfront_eur"]), _fmt_eur(gr["upfront_eur"])),
            ("Monatsrate (netto)", _fmt_eur(st["recurring_eur"]), _fmt_eur(gr["recurring_eur"])),
        ]
        for feat in st.get("features", []):
            comparisons.append((feat, "Inkl.", "Inkl."))
        for feat in gr.get("features", []):
            if feat not in [f for f in st.get("features", [])]:
                comparisons.append((feat, "—", "Inkl."))
        for row in comparisons:
            agent_rows.append([
                Paragraph(row[0], styles["CellText"]),
                Paragraph(row[1], styles["CellText"]),
                Paragraph(row[2], styles["CellText"]),
            ])
        w = doc.width
        t = Table(agent_rows, colWidths=[w * 0.40, w * 0.30, w * 0.30])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, CI_DARK),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, CI_GRAY),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(255/255, 155/255, 122/255, 0.08)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

    # --- Websites ---
    if category in ("all", "websites"):
        elements.append(Paragraph("Website-Tarife", styles["CatTitle"]))
        web_header = [
            Paragraph("<b>Merkmal</b>", styles["CellBold"]),
            Paragraph("<b>Starter</b>", styles["CellBold"]),
            Paragraph("<b>Professional</b>", styles["CellBold"]),
            Paragraph("<b>Enterprise</b>", styles["CellBold"]),
        ]
        ws = SERVICE_CATALOG["web_starter"]
        wp = SERVICE_CATALOG["web_professional"]
        we = SERVICE_CATALOG["web_enterprise"]
        web_rows = [web_header]
        web_rows.append([Paragraph("Tarif-Nr.", styles["CellText"]), Paragraph(ws["tariff_number"], styles["CellText"]), Paragraph(wp["tariff_number"], styles["CellText"]), Paragraph(we["tariff_number"], styles["CellText"])])
        web_rows.append([Paragraph("Preis (netto)", styles["CellText"]), Paragraph(_fmt_eur(ws["price_eur"]), styles["CellText"]), Paragraph(_fmt_eur(wp["price_eur"]), styles["CellText"]), Paragraph(_fmt_eur(we["price_eur"]), styles["CellText"])])
        web_rows.append([Paragraph("Lieferzeit", styles["CellText"]), Paragraph(f'{ws["delivery_weeks"]} Wochen', styles["CellText"]), Paragraph(f'{wp["delivery_weeks"]} Wochen', styles["CellText"]), Paragraph(f'{we["delivery_weeks"]} Wochen', styles["CellText"])])
        all_feats = set()
        for s in [ws, wp, we]:
            all_feats.update(s["features"])
        for f in sorted(all_feats):
            web_rows.append([
                Paragraph(f[:50], styles["CellText"]),
                Paragraph("Inkl." if f in ws["features"] else "—", styles["CellText"]),
                Paragraph("Inkl." if f in wp["features"] else "—", styles["CellText"]),
                Paragraph("Inkl." if f in we["features"] else "—", styles["CellText"]),
            ])
        w = doc.width
        t = Table(web_rows, colWidths=[w * 0.34, w * 0.22, w * 0.22, w * 0.22])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, CI_DARK),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(255/255, 155/255, 122/255, 0.08)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

    # --- SEO ---
    if category in ("all", "seo"):
        elements.append(Paragraph("KI-gesteuertes SEO", styles["CatTitle"]))
        seo_header = [
            Paragraph("<b>Merkmal</b>", styles["CellBold"]),
            Paragraph("<b>SEO Starter</b>", styles["CellBold"]),
            Paragraph("<b>SEO Growth</b>", styles["CellBold"]),
            Paragraph("<b>SEO Enterprise</b>", styles["CellBold"]),
        ]
        ss = SERVICE_CATALOG["seo_starter"]
        sg = SERVICE_CATALOG["seo_growth"]
        se = SERVICE_CATALOG["seo_enterprise"]
        seo_rows = [seo_header]
        seo_rows.append([Paragraph("Tarif-Nr.", styles["CellText"]), Paragraph(ss["tariff_number"], styles["CellText"]), Paragraph(sg["tariff_number"], styles["CellText"]), Paragraph(se["tariff_number"], styles["CellText"])])
        seo_rows.append([Paragraph("Preis (netto/Mo.)", styles["CellText"]), Paragraph(f'{ss["price_monthly_eur"]:.2f} EUR', styles["CellText"]), Paragraph(f'{sg["price_monthly_eur"]:.2f} EUR', styles["CellText"]), Paragraph("Individuell", styles["CellText"])])
        seo_rows.append([Paragraph("Mindestlaufzeit", styles["CellText"]), Paragraph(f'{ss.get("min_months",6)} Monate', styles["CellText"]), Paragraph(f'{sg.get("min_months",6)} Monate', styles["CellText"]), Paragraph("Individuell", styles["CellText"])])
        all_seo = set()
        for s in [ss, sg, se]:
            all_seo.update(s["features"])
        for f in sorted(all_seo):
            seo_rows.append([
                Paragraph(f[:50], styles["CellText"]),
                Paragraph("Inkl." if f in ss["features"] else "—", styles["CellText"]),
                Paragraph("Inkl." if f in sg["features"] else "—", styles["CellText"]),
                Paragraph("Inkl." if f in se["features"] else "—", styles["CellText"]),
            ])
        w = doc.width
        t = Table(seo_rows, colWidths=[w * 0.34, w * 0.22, w * 0.22, w * 0.22])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, CI_DARK),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(255/255, 155/255, 122/255, 0.08)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

    # --- Apps ---
    if category in ("all", "apps"):
        elements.append(Paragraph("App-Entwicklung", styles["CatTitle"]))
        app_header = [
            Paragraph("<b>Merkmal</b>", styles["CellBold"]),
            Paragraph("<b>App MVP</b>", styles["CellBold"]),
            Paragraph("<b>App Professional</b>", styles["CellBold"]),
        ]
        am = SERVICE_CATALOG["app_mvp"]
        ap = SERVICE_CATALOG["app_professional"]
        app_rows = [app_header]
        app_rows.append([Paragraph("Tarif-Nr.", styles["CellText"]), Paragraph(am["tariff_number"], styles["CellText"]), Paragraph(ap["tariff_number"], styles["CellText"])])
        app_rows.append([Paragraph("Preis (netto)", styles["CellText"]), Paragraph(_fmt_eur(am["price_eur"]), styles["CellText"]), Paragraph(_fmt_eur(ap["price_eur"]), styles["CellText"])])
        app_rows.append([Paragraph("Lieferzeit", styles["CellText"]), Paragraph(f'{am["delivery_weeks"]} Wochen', styles["CellText"]), Paragraph(f'{ap["delivery_weeks"]} Wochen', styles["CellText"])])
        app_rows.append([Paragraph("Zahlungsbedingungen", styles["CellText"]), Paragraph("50 % bei Auftrag, 50 % bei Abnahme", styles["CellText"]), Paragraph("50 % bei Auftrag, 50 % bei Abnahme", styles["CellText"])])
        all_app = set()
        for s in [am, ap]:
            all_app.update(s["features"])
        for f in sorted(all_app):
            app_rows.append([
                Paragraph(f[:50], styles["CellText"]),
                Paragraph("Inkl." if f in am["features"] else "—", styles["CellText"]),
                Paragraph("Inkl." if f in ap["features"] else "—", styles["CellText"]),
            ])
        w = doc.width
        t = Table(app_rows, colWidths=[w * 0.40, w * 0.30, w * 0.30])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, CI_DARK),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(255/255, 155/255, 122/255, 0.08)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

    # --- KI Add-ons ---
    if category in ("all", "addons"):
        elements.append(Paragraph("KI Add-ons", styles["CatTitle"]))
        addon_header = [
            Paragraph("<b>Merkmal</b>", styles["CellBold"]),
            Paragraph("<b>KI-Chatbot</b>", styles["CellBold"]),
            Paragraph("<b>KI-Automation</b>", styles["CellBold"]),
        ]
        ac = SERVICE_CATALOG["ai_addon_chatbot"]
        aa = SERVICE_CATALOG["ai_addon_automation"]
        addon_rows = [addon_header]
        addon_rows.append([Paragraph("Tarif-Nr.", styles["CellText"]), Paragraph(ac["tariff_number"], styles["CellText"]), Paragraph(aa["tariff_number"], styles["CellText"])])
        addon_rows.append([Paragraph("Preis (netto/Mo.)", styles["CellText"]), Paragraph(f'{ac["price_monthly_eur"]:.2f} EUR', styles["CellText"]), Paragraph(f'{aa["price_monthly_eur"]:.2f} EUR', styles["CellText"])])
        addon_rows.append([Paragraph("Abrechnungsmodus", styles["CellText"]), Paragraph("Monatlich", styles["CellText"]), Paragraph("Monatlich", styles["CellText"])])
        all_addon = set()
        for s in [ac, aa]:
            all_addon.update(s["features"])
        for f in sorted(all_addon):
            addon_rows.append([
                Paragraph(f[:50], styles["CellText"]),
                Paragraph("Inkl." if f in ac["features"] else "—", styles["CellText"]),
                Paragraph("Inkl." if f in aa["features"] else "—", styles["CellText"]),
            ])
        w = doc.width
        t = Table(addon_rows, colWidths=[w * 0.40, w * 0.30, w * 0.30])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, CI_DARK),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(255/255, 155/255, 122/255, 0.08)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6 * mm))

    # --- Bundles ---
    if category in ("all", "bundles"):
        elements.append(Paragraph("Bundles & Kombiangebote", styles["CatTitle"]))
        elements.append(Paragraph(
            "Cross-Sell-Rabatte bis 15 %. Alle Bundles kombinieren mehrere Leistungen zu einem vergünstigten Gesamtpreis.",
            styles["CellText"],
        ))
        elements.append(Spacer(1, 3 * mm))
        for bkey, b in BUNDLE_CATALOG.items():
            badge_str = f' [{b["badge"]}]' if b.get("badge") else ""
            elements.append(Paragraph(
                f'<b>{b["name"]}{badge_str}</b> (Tarif-Nr. {b["tariff_number"]})',
                styles["CellBold"],
            ))
            elements.append(Paragraph(
                f'{b["description"]}<br/>'
                f'Bundle-Preis: <b>{_fmt_eur(b["bundle_price_eur"])}</b>'
                f'{" | " + b["savings_desc"] if b.get("savings_desc") else ""}',
                styles["CellText"],
            ))
            if b.get("includes"):
                inc_names = []
                for inc_key in b["includes"]:
                    if inc_key in SERVICE_CATALOG:
                        inc_names.append(SERVICE_CATALOG[inc_key]["name"])
                    elif inc_key in ("starter", "growth"):
                        inc_names.append(TARIFF_CONFIG[inc_key]["name"])
                if inc_names:
                    elements.append(Paragraph(f'Enthaltene Leistungen: {", ".join(inc_names)}', styles["CellText"]))
            elements.append(Spacer(1, 4 * mm))

    # Footnotes
    elements.append(Spacer(1, 8 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=CI_GRAY, spaceBefore=4, spaceAfter=6))
    elements.append(Paragraph(
        f"<b>Rechtliche Hinweise:</b><br/>"
        f"Alle Preise in EUR, zzgl. der gesetzlichen Umsatzsteuer (21 % NL / 19 % DE).<br/>"
        f"Preise gültig ab {now_str}. Änderungen vorbehalten.<br/>"
        f"Individuelle Konditionen und Sondervereinbarungen auf Anfrage.<br/>"
        f"Es gelten die AGB der {COMPANY_DATA['name']}.<br/><br/>"
        f"<b>Kontakt:</b> {COMPANY_DATA['email']} | {COMPANY_DATA['phone']}<br/>"
        f"<b>Web:</b> {COMPANY_DATA['web']}",
        styles["FootNote"],
    ))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        "Datenschutzorientiert für den europäischen Rechtsraum entwickelt. "
        "DSGVO (EU) 2016/679 | EU AI Act (EU) 2024/1689 | EU-Hosting (Frankfurt, Amsterdam)",
        styles["FootNote"],
    ))

    def header_fn(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(CI_ORANGE)
        canvas.setLineWidth(2)
        canvas.line(15 * mm, A4[1] - 18 * mm, A4[0] - 15 * mm, A4[1] - 18 * mm)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(CI_DARK)
        canvas.drawString(15 * mm, A4[1] - 14 * mm, "NeXify")
        canvas.setFillColor(CI_ORANGE)
        w = canvas.stringWidth("NeXify", "Helvetica-Bold", 14)
        canvas.drawString(15 * mm + w, A4[1] - 14 * mm, "AI")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(CI_GRAY)
        canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 12 * mm, f"Tarif- und Leistungsübersicht")
        canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 16 * mm, f"Stand: {now_str}")
        canvas.setStrokeColor(CI_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, 18 * mm, A4[0] - 15 * mm, 18 * mm)
        canvas.setFont("Helvetica", 6)
        canvas.drawString(15 * mm, 14 * mm,
            f"{COMPANY_DATA['name']} | {COMPANY_DATA['address_nl']['street']}, "
            f"{COMPANY_DATA['address_nl']['city']} | KvK: {COMPANY_DATA['kvk']} | USt-ID: {COMPANY_DATA['vat_id']}")
        canvas.drawRightString(A4[0] - 15 * mm, 14 * mm, f"Seite {doc.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=header_fn, onLaterPages=header_fn)
    return buf.getvalue()

def get_commercial_faq() -> list:
    """Return FAQ derived from TARIFF_CONFIG — no duplicate sources"""
    starter = TARIFF_CONFIG["starter"]
    growth = TARIFF_CONFIG["growth"]
    bank = COMPANY_DATA["bank"]

    return [
        {
            "q": "Welche Tarife gibt es?",
            "a": (
                f"Wir bieten zwei aktive Kern-Tarife an:\n\n"
                f"1. **{starter['name']}** (Tarif-Nr. {starter['tariff_number']}): "
                f"ab {starter['reference_monthly_eur']:.2f} EUR/Monat bei {starter['contract_months']} Monaten Laufzeit. "
                f"{starter['agents']} KI-Agenten, {starter['infrastructure']}, {starter['support']}.\n\n"
                f"2. **{growth['name']}** (Tarif-Nr. {growth['tariff_number']}): "
                f"ab {growth['reference_monthly_eur']:.2f} EUR/Monat bei {growth['contract_months']} Monaten Laufzeit. "
                f"{growth['agents']} KI-Agenten, {growth['infrastructure']}, {growth['support']}.\n\n"
                f"Alle Preise zzgl. gesetzlicher USt."
            ),
        },
        {
            "q": "Was bedeutet 24 Monate Laufzeit?",
            "a": (
                "Der Vertrag läuft über 24 Monate ab Beauftragung. Dies ermöglicht eine nachhaltige "
                "Implementierung, Optimierung und kontinuierliche Weiterentwicklung Ihrer KI-Agenten. "
                "Die Laufzeit sichert planbare Kosten und priorisierte Ressourcen."
            ),
        },
        {
            "q": "Wie funktioniert die 30-%-Aktivierungsanzahlung?",
            "a": (
                "Bei Beauftragung wird eine Aktivierungsanzahlung von 30 % des Gesamtvertragswerts fällig. "
                "Diese deckt ab:\n"
                "- Strategischer Projektstart und Priorisierung\n"
                "- Setup und Initialkonfiguration\n"
                "- Ressourcen- und Kapazitätsreservierung\n"
                "- Implementierungsfreigabe\n\n"
                "Die Anzahlung ist Teil des Gesamtvertragswerts — keine zusätzliche Gebühr."
            ),
        },
        {
            "q": "Was ist im Starter enthalten?",
            "a": "\n".join([f"- {f}" for f in starter["features"]]) + (
                f"\n\nTarifpreis: {starter['reference_monthly_eur']:.2f} EUR/Monat | "
                f"Gesamtvertragswert: {starter['total_contract_eur']:.2f} EUR | "
                f"Anzahlung: {starter['upfront_eur']:.2f} EUR"
            ),
        },
        {
            "q": "Was ist im Growth enthalten?",
            "a": "\n".join([f"- {f}" for f in growth["features"]]) + (
                f"\n\nTarifpreis: {growth['reference_monthly_eur']:.2f} EUR/Monat | "
                f"Gesamtvertragswert: {growth['total_contract_eur']:.2f} EUR | "
                f"Anzahlung: {growth['upfront_eur']:.2f} EUR"
            ),
        },
        {
            "q": "Wie wird abgerechnet?",
            "a": (
                "Die Abrechnung erfolgt in zwei Phasen:\n"
                "1. **Aktivierungsanzahlung (30 %)** — sofort fällig nach Beauftragung/Angebotsannahme\n"
                "2. **Monatliche Folgeraten** — der Restbetrag in 24 gleichen monatlichen Raten\n\n"
                "Alle Rechnungen werden per E-Mail zugestellt und sind im sicheren Kundencenter abrufbar."
            ),
        },
        {
            "q": "Wann wird die Anzahlungsrechnung erstellt?",
            "a": (
                "Sofort nach Angebotsannahme wird automatisch eine Anzahlungsrechnung erstellt und per E-Mail zugestellt. "
                "Die Frist beträgt 14 Tage. Zusätzlich erhalten Sie einen Online-Zahlungslink."
            ),
        },
        {
            "q": "Wie funktionieren die Monatsraten?",
            "a": (
                f"Starter: {starter['recurring_eur']:.2f} EUR/Monat über {starter['recurring_count']} Monate | "
                f"Growth: {growth['recurring_eur']:.2f} EUR/Monat über {growth['recurring_count']} Monate.\n\n"
                "Alle Beträge zzgl. USt. Rechnungen werden automatisch monatlich erstellt."
            ),
        },
        {
            "q": "Wie erfolgt die Zahlung per Revolut Checkout?",
            "a": (
                "Sie erhalten per E-Mail einen sicheren Zahlungslink von Revolut. "
                "Unterstützte Zahlungsmethoden: Kredit-/Debitkarte, Bankkonto, Apple Pay, Google Pay. "
                "Nach Zahlungseingang wird der Status automatisch aktualisiert."
            ),
        },
        {
            "q": "Wie erfolgt die Zahlung per Banküberweisung?",
            "a": (
                f"Überweisen Sie den Rechnungsbetrag unter Angabe der Rechnungsnummer an:\n\n"
                f"IBAN: {bank['iban']}\nBIC: {bank['bic']}\nKontoinhaber: {bank['account_holder']}\n\n"
                f"Der Zahlungseingang wird manuell oder halbautomatisch abgeglichen."
            ),
        },
        {
            "q": "Welche Bankdaten gelten im EWR?",
            "a": f"IBAN: {bank['iban']}\nBIC: {bank['bic']}\nKontoinhaber: {bank['account_holder']}",
        },
        {
            "q": "Welche Bankdaten gelten außerhalb des EWR?",
            "a": (
                f"IBAN: {bank['iban']}\nBIC: {bank['bic']}\n"
                f"BIC der zwischengeschalteten Bank: {bank['intermediary_bic']}\n"
                f"Kontoinhaber: {bank['account_holder']}"
            ),
        },
        {
            "q": "Wie funktioniert die Angebotsannahme?",
            "a": (
                "1. Sie erhalten Ihr Angebot per E-Mail mit sicherem Zugangslink\n"
                "2. Nach Öffnen können Sie: Angebot annehmen, Änderung anfragen oder ablehnen\n"
                "3. Bei Annahme wird sofort die Anzahlungsrechnung erstellt\n"
                "4. Alle Zugriffe werden DSGVO-konform protokolliert"
            ),
        },
        {
            "q": "Wie funktioniert der sichere Angebotszugriff?",
            "a": (
                "Über zeitlich begrenzte Magic-Links (24h Gültigkeit). "
                "Kein Passwort nötig — der Link wird per E-Mail an die verifizierte Adresse gesendet. "
                "Alle Zugriffe werden im Audit-Log protokolliert."
            ),
        },
        {
            "q": "Wie werden Daten DSGVO-konform verarbeitet?",
            "a": (
                "- Alle Daten werden in EU-Rechenzentren verarbeitet\n"
                "- Kein Datentransfer in Drittländer\n"
                "- Zeitlich begrenzte Zugriffslinks statt Passwörter\n"
                "- Vollständige Audit-Logs aller Dokumentenzugriffe\n"
                "- Verschlüsselte Speicherung und Übertragung\n"
                "- EU-AI-Act-konforme Umsetzung"
            ),
        },
        {
            "q": "Bietet NeXifyAI auch Websites und Apps an?",
            "a": (
                "Ja. Neben unseren KI-Agenten-Tarifen bieten wir:\n\n"
                "**Websites:** Starter (2.990 EUR), Professional (7.490 EUR), Enterprise (14.900 EUR)\n"
                "**Apps:** MVP (9.900 EUR), Professional (24.900 EUR)\n"
                "**KI Add-ons:** Chatbot (249 EUR/Mo.), Prozessautomation (499 EUR/Mo.)\n"
                "**Bundles:** Kombinationsangebote mit Ersparnissen bis zu 6.176 EUR\n\n"
                "Alle Preise zzgl. USt."
            ),
        },
        {
            "q": "Gibt es Kombiangebote / Bundles?",
            "a": (
                "Ja. Unsere aktuellen Bundles:\n"
                "- **Digital Starter Bundle:** Website Starter + SEO Starter (3 Monate) — 3.990 EUR (statt 4.289 EUR)\n"
                "- **Growth Digital Bundle:** Website Professional + SEO Growth (6 Monate) + KI-Chatbot — 17.490 EUR (15 % Rabatt)\n"
                "- **Enterprise Digital Bundle:** Website Enterprise + App + SEO Enterprise + Growth AI Agenten AG — ab 39.900 EUR\n\n"
                "Individuelle Kombinationen auf Anfrage. Cross-Sell-Rabatte bis 15 %."
            ),
        },
        {
            "q": "Bietet NeXifyAI auch KI-gesteuertes SEO an?",
            "a": (
                "Ja. Unsere SEO-Tarife:\n"
                "- **SEO Starter:** 799 EUR/Monat — 50 Keywords, On-Page (5 Seiten/Mo.), monatlicher Report\n"
                "- **SEO Growth:** 1.499 EUR/Monat — 200 Keywords, Content-Strategie, Linkbuilding, Multilingual SEO\n"
                "- **SEO Enterprise:** Individuell — dediziertes Team, 5+ Märkte, tagesaktuelle Reports\n\n"
                "Mindestlaufzeit: 6 Monate. Alle Preise zzgl. USt."
            ),
        },
    ]

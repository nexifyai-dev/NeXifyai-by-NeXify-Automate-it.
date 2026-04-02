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
    "ceo_title": "Geschaeftsfuehrer",
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
            "Woechentliches Reporting",
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
}

BUNDLE_CATALOG = {
    "digital_starter": {
        "tariff_number": "NXA-BDL-DS-3990",
        "slug": "digital-starter-bundle",
        "name": "Digital Starter Bundle",
        "description": "Website + KI-Chatbot",
        "includes": ["web_starter", "ai_addon_chatbot"],
        "bundle_price_eur": 3990.00,
        "savings_eur": 1248.00,
        "savings_desc": "Website Starter + 12 Monate KI-Chatbot",
        "billing_mode": "one_time_plus_monthly",
        "one_time_eur": 2990.00,
        "monthly_eur": 199.00,
        "monthly_months": 12,
        "status": "active",
    },
    "growth_digital": {
        "tariff_number": "NXA-BDL-GD-11900",
        "slug": "growth-digital-bundle",
        "name": "Growth Digital Bundle",
        "description": "Website Professional + Starter AI Agenten AG (24 Mo.)",
        "includes": ["web_professional", "starter"],
        "bundle_price_eur": 17490.00,
        "savings_eur": 1976.00,
        "savings_desc": "Website + Starter AI Agenten AG (24 Monate)",
        "billing_mode": "custom",
        "one_time_website_eur": 5990.00,
        "ai_monthly_eur": 479.00,
        "ai_months": 24,
        "status": "active",
    },
    "enterprise_digital": {
        "tariff_number": "NXA-BDL-ED-39900",
        "slug": "enterprise-digital-bundle",
        "name": "Enterprise Digital Bundle",
        "description": "Website Enterprise + Growth AI Agenten AG (24 Mo.)",
        "includes": ["web_enterprise", "growth"],
        "bundle_price_eur": 39900.00,
        "savings_eur": 6176.00,
        "savings_desc": "Website + Growth AI Agenten AG (24 Monate)",
        "billing_mode": "custom",
        "one_time_website_eur": 9900.00,
        "ai_monthly_eur": 1249.00,
        "ai_months": 24,
        "status": "active",
    },
}

# ═══════════════════════════════════════════════════
# COMPLIANCE & TRUST METADATA
# ═══════════════════════════════════════════════════
COMPLIANCE_STATUS = {
    "gdpr": {"status": "implemented", "label": "DSGVO / AVG", "detail": "Verordnung (EU) 2016/679 — vollstaendig umgesetzt"},
    "eu_ai_act": {"status": "implemented", "label": "EU AI Act", "detail": "Verordnung (EU) 2024/1689 — Transparenz- und Kennzeichnungspflichten umgesetzt"},
    "uavg": {"status": "implemented", "label": "UAVG (NL)", "detail": "Uitvoeringswet AVG — niederlaendische Datenschutz-Implementierung"},
    "iso_27001": {"status": "aligned", "label": "ISO/IEC 27001", "detail": "Informationssicherheits-Managementsystem — orientiert, nicht zertifiziert"},
    "iso_27701": {"status": "aligned", "label": "ISO/IEC 27701", "detail": "Privacy Information Management — orientiert, nicht zertifiziert"},
    "pci_dss": {"status": "delegated", "label": "PCI DSS", "detail": "Zahlungssicherheit via Revolut (PCI DSS Level 1 zertifiziert)"},
    "ssl_tls": {"status": "implemented", "label": "SSL/TLS", "detail": "Verschluesselte Uebertragung aller Daten"},
    "eu_hosting": {"status": "implemented", "label": "EU-Hosting", "detail": "Datenverarbeitung ausschliesslich in EU-Rechenzentren"},
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
            "A.8_Logging": {"status": "fulfilled", "note": "Audit-Logs fuer alle kommerziellen Events"},
            "A.8_Network": {"status": "fulfilled", "note": "CORS-Konfiguration, API-Rate-Limiting"},
            "A.8_Vulnerability": {"status": "partial", "note": "Regelmaessige Updates, kein formales Penetration-Testing"},
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
            "DPIA": {"status": "partial", "note": "Risikobewertung durchgefuehrt, kein formales DPIA-Dokument"},
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
        f"vielen Dank fuer Ihr Interesse an NeXify<font color='#ff9b7a'><b>AI</b></font>. "
        f"Nachfolgend unterbreiten wir Ihnen unser Angebot fuer das Produkt "
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
        [Paragraph("Aktivierungsanzahlung (30 %) — sofort faellig", styles["BodyText2"]),
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
        "- Aktivierungsanzahlung: 30 % des Gesamtvertragswerts, sofort faellig bei Beauftragung<br/>"
        "- Die Anzahlung deckt: Projektstart, Priorisierung, Setup, Kapazitaetsreservierung, Implementierungsfreigabe<br/>"
        "- Restbetrag: In 24 gleichen monatlichen Folgeraten<br/>"
        "- Alle Preise verstehen sich zzgl. der gesetzlichen USt. (21 % NL / 19 % DE)<br/>"
        "- Gueltigkeit dieses Angebots: 30 Tage ab Ausstellungsdatum<br/>"
        "- DSGVO- und EU-AI-Act-konforme Umsetzung garantiert<br/>"
        "- Gerichtsstand: Venlo, Niederlande (Burgerlijk Wetboek)",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("Zahlungsinformationen", styles["SectionHead"]))
    elements.append(Paragraph(
        f"<b>Online-Zahlung:</b> Sie erhalten einen sicheren Zahlungslink via Revolut Checkout.<br/><br/>"
        f"<b>Ueberweisung innerhalb des EWR:</b><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"Kontoinhaber: {COMPANY_DATA['bank']['account_holder']}<br/><br/>"
        f"<b>Ueberweisung von ausserhalb des EWR:</b><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"BIC der zwischengeschalteten Bank: {COMPANY_DATA['bank']['intermediary_bic']}",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(
        "Wir freuen uns auf die Zusammenarbeit. Bei Fragen stehen wir Ihnen unter "
        f"<b>{COMPANY_DATA['phone']}</b> oder <b>{COMPANY_DATA['email']}</b> zur Verfuegung.",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph("Mit freundlichen Gruessen,", styles["BodyText2"]))
    elements.append(Paragraph(
        f"<b>{COMPANY_DATA['ceo']}</b><br/>{COMPANY_DATA['ceo_title']}, NeXifyAI",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(
        "<font size='7' color='#78829a'>Datenschutzorientiert fuer den europaeischen Rechtsraum entwickelt. "
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
        f"Bitte ueberweisen Sie den Betrag unter Angabe der Rechnungsnummer <b>{ref}</b>.<br/><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']}<br/>"
        f"BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"Kontoinhaber: {COMPANY_DATA['bank']['account_holder']}<br/><br/>"
        f"Von ausserhalb des EWR zusaetzlich:<br/>"
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
# FAQ — Single Source of Truth
# ═══════════════════════════════════════════════════

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
                "Der Vertrag laeuft ueber 24 Monate ab Beauftragung. Dies ermoeglicht eine nachhaltige "
                "Implementierung, Optimierung und kontinuierliche Weiterentwicklung Ihrer KI-Agenten. "
                "Die Laufzeit sichert planbare Kosten und priorisierte Ressourcen."
            ),
        },
        {
            "q": "Wie funktioniert die 30-%-Aktivierungsanzahlung?",
            "a": (
                "Bei Beauftragung wird eine Aktivierungsanzahlung von 30 % des Gesamtvertragswerts faellig. "
                "Diese deckt ab:\n"
                "- Strategischer Projektstart und Priorisierung\n"
                "- Setup und Initialkonfiguration\n"
                "- Ressourcen- und Kapazitaetsreservierung\n"
                "- Implementierungsfreigabe\n\n"
                "Die Anzahlung ist Teil des Gesamtvertragswerts — keine zusaetzliche Gebuehr."
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
                "1. **Aktivierungsanzahlung (30 %)** — sofort faellig nach Beauftragung/Angebotsannahme\n"
                "2. **Monatliche Folgeraten** — der Restbetrag in 24 gleichen monatlichen Raten\n\n"
                "Alle Rechnungen werden per E-Mail zugestellt und sind im sicheren Kundencenter abrufbar."
            ),
        },
        {
            "q": "Wann wird die Anzahlungsrechnung erstellt?",
            "a": (
                "Sofort nach Angebotsannahme wird automatisch eine Anzahlungsrechnung erstellt und per E-Mail zugestellt. "
                "Die Frist betraegt 14 Tage. Zusaetzlich erhalten Sie einen Online-Zahlungslink."
            ),
        },
        {
            "q": "Wie funktionieren die Monatsraten?",
            "a": (
                f"Starter: {starter['recurring_eur']:.2f} EUR/Monat ueber {starter['recurring_count']} Monate | "
                f"Growth: {growth['recurring_eur']:.2f} EUR/Monat ueber {growth['recurring_count']} Monate.\n\n"
                "Alle Betraege zzgl. USt. Rechnungen werden automatisch monatlich erstellt."
            ),
        },
        {
            "q": "Wie erfolgt die Zahlung per Revolut Checkout?",
            "a": (
                "Sie erhalten per E-Mail einen sicheren Zahlungslink von Revolut. "
                "Unterstuetzte Zahlungsmethoden: Kredit-/Debitkarte, Bankkonto, Apple Pay, Google Pay. "
                "Nach Zahlungseingang wird der Status automatisch aktualisiert."
            ),
        },
        {
            "q": "Wie erfolgt die Zahlung per Bankueberweisung?",
            "a": (
                f"Ueberweisen Sie den Rechnungsbetrag unter Angabe der Rechnungsnummer an:\n\n"
                f"IBAN: {bank['iban']}\nBIC: {bank['bic']}\nKontoinhaber: {bank['account_holder']}\n\n"
                f"Der Zahlungseingang wird manuell oder halbautomatisch abgeglichen."
            ),
        },
        {
            "q": "Welche Bankdaten gelten im EWR?",
            "a": f"IBAN: {bank['iban']}\nBIC: {bank['bic']}\nKontoinhaber: {bank['account_holder']}",
        },
        {
            "q": "Welche Bankdaten gelten ausserhalb des EWR?",
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
                "2. Nach Oeffnen koennen Sie: Angebot annehmen, Aenderung anfragen oder ablehnen\n"
                "3. Bei Annahme wird sofort die Anzahlungsrechnung erstellt\n"
                "4. Alle Zugriffe werden DSGVO-konform protokolliert"
            ),
        },
        {
            "q": "Wie funktioniert der sichere Angebotszugriff?",
            "a": (
                "Ueber zeitlich begrenzte Magic-Links (24h Gueltigkeit). "
                "Kein Passwort noetig — der Link wird per E-Mail an die verifizierte Adresse gesendet. "
                "Alle Zugriffe werden im Audit-Log protokolliert."
            ),
        },
        {
            "q": "Wie werden Daten DSGVO-konform verarbeitet?",
            "a": (
                "- Alle Daten werden in EU-Rechenzentren verarbeitet\n"
                "- Kein Datentransfer in Drittlaender\n"
                "- Zeitlich begrenzte Zugriffslinks statt Passwoerter\n"
                "- Vollstaendige Audit-Logs aller Dokumentenzugriffe\n"
                "- Verschluesselte Speicherung und Uebertragung\n"
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
                "Ja. Beispiele:\n"
                "- **Digital Starter Bundle:** Website + KI-Chatbot (12 Mo.) ab 3.990 EUR\n"
                "- **Growth Digital Bundle:** Website Pro + Starter AI Agenten AG (24 Mo.) ab 17.490 EUR\n"
                "- **Enterprise Digital Bundle:** Website Enterprise + Growth AI Agenten AG (24 Mo.) ab 39.900 EUR\n\n"
                "Individuelle Kombinationen auf Anfrage."
            ),
        },
    ]

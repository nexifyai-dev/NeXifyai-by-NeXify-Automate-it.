"""
NeXifyAI Commercial Engine — Starter AI Agenten AG
Invoice/Quote Engine, Revolut Payment, Customer Access, PDF Generation
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
from motor.motor_asyncio import AsyncIOMotorClient
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

logger = logging.getLogger("nexifyai.commercial")

REVOLUT_SECRET_KEY = os.environ.get("REVOLUT_SECRET_KEY", "")
REVOLUT_PUBLIC_KEY = os.environ.get("REVOLUT_PUBLIC_KEY", "")
REVOLUT_API_URL = os.environ.get("REVOLUT_API_URL", "https://merchant.revolut.com")
REVOLUT_API_VERSION = os.environ.get("REVOLUT_API_VERSION", "2025-12-04")

# ═══════════ COMPANY MASTER DATA ═══════════
COMPANY_DATA = {
    "name": "NeXify Automate",
    "brand": "NeXifyAI",
    "ceo": "Pascal Courbois",
    "address_nl": {
        "street": "Graaf van Loonstraat 1E",
        "city": "5921 JA Venlo",
        "country": "Niederlande"
    },
    "address_de": {
        "street": "Wallstraße 9",
        "city": "41334 Nettetal-Kaldenkirchen",
        "country": "Deutschland"
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
        "bank_name": "Revolut"
    }
}

# ═══════════ PRODUCT: STARTER AI AGENTEN AG ═══════════
STARTER_PRODUCT = {
    "id": "starter-ai-agenten-ag",
    "name": "Starter AI Agenten AG",
    "contract_months": 24,
    "deposit_percent": 30,
    "tiers": {
        "starter": {
            "name": "Starter",
            "monthly_net": 1900_00,  # cents
            "agents": 2,
            "infrastructure": "Shared Cloud",
            "support": "E-Mail (48h)",
            "features": [
                "2 KI-Agenten",
                "Shared Cloud Infrastructure",
                "E-Mail-Support (48h Response)",
                "Basis-Integrationen (REST API)",
                "Standard-Monitoring",
                "Monatliches Reporting"
            ]
        },
        "growth": {
            "name": "Growth",
            "monthly_net": 4500_00,
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
                "Dedizierter Onboarding-Manager"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "monthly_net": None,  # individual
            "agents": "Unlimitiert",
            "infrastructure": "On-Premise / Dedicated",
            "support": "SLA-gesichert (4h)",
            "features": [
                "Unlimitierte KI-Agenten",
                "On-Premise oder dedizierte Infrastruktur",
                "SLA-gesicherter Support (4h Response)",
                "Custom LLM Training",
                "Vollständige Enterprise-Integration",
                "24/7 Monitoring",
                "Dediziertes Success Team"
            ]
        }
    }
}


def calc_contract(tier_key: str, custom_monthly_net: int = None) -> dict:
    """Calculate full contract values for a tier"""
    tier = STARTER_PRODUCT["tiers"].get(tier_key)
    if not tier:
        return {}
    monthly = custom_monthly_net or tier["monthly_net"]
    if not monthly:
        return {"tier": tier_key, "requires_custom_quote": True}
    months = STARTER_PRODUCT["contract_months"]
    total_net = monthly * months
    deposit = int(total_net * STARTER_PRODUCT["deposit_percent"] / 100)
    remaining = total_net - deposit
    vat_rate = 21  # NL BTW
    deposit_vat = int(deposit * vat_rate / 100)
    monthly_remaining = remaining // (months - 1) if months > 1 else remaining
    return {
        "tier": tier_key,
        "tier_name": tier["name"],
        "monthly_net": monthly,
        "months": months,
        "total_net": total_net,
        "deposit_net": deposit,
        "deposit_vat": deposit_vat,
        "deposit_gross": deposit + deposit_vat,
        "remaining_net": remaining,
        "monthly_remaining_net": monthly_remaining,
        "vat_rate": vat_rate,
        "currency": "EUR"
    }


# ═══════════ SEQUENTIAL NUMBERING ═══════════

async def get_next_number(db, sequence_type: str) -> str:
    """Atomic counter for invoice/quote numbers"""
    result = await db.counters.find_one_and_update(
        {"_id": sequence_type},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
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


# ═══════════ REVOLUT PAYMENT ═══════════

async def create_revolut_order(amount_cents: int, currency: str, customer_email: str,
                                description: str, merchant_order_id: str) -> dict:
    """Create a Revolut Merchant API payment order"""
    if not REVOLUT_SECRET_KEY:
        logger.warning("Revolut secret key not configured")
        return {"error": "Payment system not configured"}

    headers = {
        "Authorization": f"Bearer {REVOLUT_SECRET_KEY}",
        "Revolut-Api-Version": REVOLUT_API_VERSION,
        "Content-Type": "application/json"
    }
    payload = {
        "amount": amount_cents,
        "currency": currency,
        "customer": {"email": customer_email},
        "description": description,
        "merchant_order_ext_ref": merchant_order_id,
        "capture_mode": "automatic"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{REVOLUT_API_URL}/api/1.0/orders",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Revolut order created: {data.get('id')}")
                return {
                    "order_id": data.get("id"),
                    "token": data.get("token"),
                    "state": data.get("state"),
                    "checkout_url": data.get("checkout_url"),
                    "public_id": data.get("public_id")
                }
            else:
                logger.error(f"Revolut order failed: {resp.status_code} {resp.text}")
                return {"error": f"Payment creation failed: {resp.status_code}", "details": resp.text}
        except Exception as e:
            logger.error(f"Revolut API error: {e}")
            return {"error": str(e)}


async def get_revolut_order(order_id: str) -> dict:
    """Retrieve Revolut order status"""
    headers = {
        "Authorization": f"Bearer {REVOLUT_SECRET_KEY}",
        "Revolut-Api-Version": REVOLUT_API_VERSION
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{REVOLUT_API_URL}/api/1.0/orders/{order_id}", headers=headers)
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.text}


def verify_revolut_webhook(signing_secret: str, timestamp: str, raw_body: str, signature: str) -> bool:
    """Verify Revolut webhook signature"""
    payload_to_sign = f"v1.{timestamp}.{raw_body}"
    expected = "v1=" + hmac.new(
        signing_secret.encode(),
        payload_to_sign.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ═══════════ MAGIC LINK / CUSTOMER ACCESS ═══════════

def generate_access_token(customer_id: str, document_type: str = "all") -> dict:
    """Generate a time-limited magic link token"""
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    return {
        "token": token,
        "token_hash": token_hash,
        "customer_id": customer_id,
        "document_type": document_type,
        "expires_at": expires.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def verify_access_token(provided_token: str, stored_hash: str, expires_at: str) -> bool:
    """Verify a magic link token"""
    if datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
        return False
    computed_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    return hmac.compare_digest(computed_hash, stored_hash)


# ═══════════ PDF GENERATION ═══════════

CI_ORANGE = colors.Color(255/255, 155/255, 122/255)
CI_DARK = colors.Color(12/255, 17/255, 23/255)
CI_GRAY = colors.Color(120/255, 130/255, 145/255)

def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BrandTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
                               fontSize=18, textColor=CI_DARK, spaceAfter=6))
    styles.add(ParagraphStyle('BrandSub', parent=styles['Normal'], fontName='Helvetica',
                               fontSize=10, textColor=CI_GRAY, spaceAfter=12))
    styles.add(ParagraphStyle('SectionHead', parent=styles['Heading2'], fontName='Helvetica-Bold',
                               fontSize=12, textColor=CI_DARK, spaceBefore=16, spaceAfter=6))
    styles.add(ParagraphStyle('BodyText2', parent=styles['Normal'], fontName='Helvetica',
                               fontSize=9.5, textColor=CI_DARK, leading=14))
    styles.add(ParagraphStyle('SmallGray', parent=styles['Normal'], fontName='Helvetica',
                               fontSize=7.5, textColor=CI_GRAY, leading=10))
    styles.add(ParagraphStyle('RightAligned', parent=styles['Normal'], fontName='Helvetica',
                               fontSize=9.5, textColor=CI_DARK, alignment=TA_RIGHT))
    styles.add(ParagraphStyle('TotalBold', parent=styles['Normal'], fontName='Helvetica-Bold',
                               fontSize=11, textColor=CI_DARK, alignment=TA_RIGHT))
    return styles


def _fmt_eur(cents: int) -> str:
    """Format cents to EUR string"""
    return f"{cents / 100:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def _header_footer(canvas, doc, doc_type, doc_number, doc_date):
    """Draw header and footer on each page"""
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(CI_ORANGE)
    canvas.setLineWidth(2)
    canvas.line(20*mm, A4[1] - 18*mm, A4[0] - 20*mm, A4[1] - 18*mm)
    # Brand
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(CI_DARK)
    canvas.drawString(20*mm, A4[1] - 14*mm, "NeXify")
    canvas.setFillColor(CI_ORANGE)
    canvas.drawString(20*mm + canvas.stringWidth("NeXify", "Helvetica-Bold", 14), A4[1] - 14*mm, "AI")
    # Doc info right
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CI_GRAY)
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 12*mm, f"{doc_type} {doc_number}")
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 16*mm, f"Datum: {doc_date}")
    # Footer
    canvas.setStrokeColor(CI_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 22*mm, A4[0] - 20*mm, 22*mm)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(CI_GRAY)
    y = 18*mm
    canvas.drawString(20*mm, y, f"{COMPANY_DATA['name']} | {COMPANY_DATA['address_nl']['street']}, {COMPANY_DATA['address_nl']['city']} | KvK: {COMPANY_DATA['kvk']}")
    canvas.drawString(20*mm, y - 8, f"USt-ID: {COMPANY_DATA['vat_id']} | IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}")
    canvas.drawRightString(A4[0] - 20*mm, y, f"Seite {doc.page}")
    canvas.restoreState()


def generate_quote_pdf(quote_data: dict) -> bytes:
    """Generate a professional quote PDF"""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=28*mm, bottomMargin=28*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    styles = _build_styles()
    elements = []

    number = quote_data.get("quote_number", "—")
    date_str = quote_data.get("date", datetime.now(timezone.utc).strftime("%d.%m.%Y"))
    customer = quote_data.get("customer", {})
    calc = quote_data.get("calculation", {})
    tier = STARTER_PRODUCT["tiers"].get(calc.get("tier", ""), {})

    # Customer address block
    elements.append(Spacer(1, 8*mm))
    if customer.get("company"):
        elements.append(Paragraph(customer["company"], styles['BodyText2']))
    if customer.get("name"):
        elements.append(Paragraph(customer["name"], styles['BodyText2']))
    if customer.get("email"):
        elements.append(Paragraph(customer["email"], styles['SmallGray']))
    elements.append(Spacer(1, 12*mm))

    # Title
    elements.append(Paragraph(f"Angebot {number}", styles['BrandTitle']))
    elements.append(Paragraph(f"Starter AI Agenten AG — Tarif {calc.get('tier_name', '')}", styles['BrandSub']))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=CI_GRAY, spaceBefore=4, spaceAfter=12))

    # Intro
    elements.append(Paragraph(
        f"Sehr geehrte Damen und Herren,<br/><br/>"
        f"vielen Dank für Ihr Interesse an NeXify<font color='#ff9b7a'><b>AI</b></font>. "
        f"Nachfolgend unterbreiten wir Ihnen unser Angebot für das Produkt "
        f"<b>Starter AI Agenten AG</b> im Tarif <b>{calc.get('tier_name', '')}</b>.",
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8*mm))

    # Features table
    elements.append(Paragraph("Leistungsumfang", styles['SectionHead']))
    feat_data = [[Paragraph(f"• {f}", styles['BodyText2'])] for f in tier.get("features", [])]
    if feat_data:
        feat_table = Table(feat_data, colWidths=[doc.width])
        feat_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(feat_table)
    elements.append(Spacer(1, 8*mm))

    # Financial table
    elements.append(Paragraph("Kommerzielle Konditionen", styles['SectionHead']))
    fin_data = [
        [Paragraph("<b>Position</b>", styles['BodyText2']), Paragraph("<b>Betrag (netto)</b>", styles['RightAligned'])],
        [Paragraph(f"Monatliche Lizenz ({calc.get('tier_name', '')})", styles['BodyText2']),
         Paragraph(_fmt_eur(calc.get('monthly_net', 0)), styles['RightAligned'])],
        [Paragraph(f"Vertragslaufzeit", styles['BodyText2']),
         Paragraph(f"{calc.get('months', 24)} Monate", styles['RightAligned'])],
        [Paragraph(f"<b>Gesamtvertragswert (netto)</b>", styles['BodyText2']),
         Paragraph(f"<b>{_fmt_eur(calc.get('total_net', 0))}</b>", styles['RightAligned'])],
        [Paragraph("", styles['BodyText2']), Paragraph("", styles['RightAligned'])],
        [Paragraph(f"Anzahlung (30 %) — fällig bei Beauftragung", styles['BodyText2']),
         Paragraph(_fmt_eur(calc.get('deposit_net', 0)), styles['RightAligned'])],
        [Paragraph(f"zzgl. 21 % USt.", styles['SmallGray']),
         Paragraph(_fmt_eur(calc.get('deposit_vat', 0)), styles['RightAligned'])],
        [Paragraph(f"<b>Anzahlung (brutto)</b>", styles['BodyText2']),
         Paragraph(f"<b>{_fmt_eur(calc.get('deposit_gross', 0))}</b>", styles['RightAligned'])],
        [Paragraph("", styles['BodyText2']), Paragraph("", styles['RightAligned'])],
        [Paragraph(f"Verbleibender Restbetrag (netto)", styles['BodyText2']),
         Paragraph(_fmt_eur(calc.get('remaining_net', 0)), styles['RightAligned'])],
        [Paragraph(f"Monatliche Rate (23 Monate)", styles['BodyText2']),
         Paragraph(_fmt_eur(calc.get('monthly_remaining_net', 0)), styles['RightAligned'])],
    ]
    fin_table = Table(fin_data, colWidths=[doc.width * 0.65, doc.width * 0.35])
    fin_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, CI_DARK),
        ('LINEBELOW', (0, 3), (-1, 3), 0.5, CI_ORANGE),
        ('LINEBELOW', (0, 7), (-1, 7), 0.5, CI_ORANGE),
        ('BACKGROUND', (0, 3), (-1, 3), colors.Color(255/255, 155/255, 122/255, 0.05)),
        ('BACKGROUND', (0, 7), (-1, 7), colors.Color(255/255, 155/255, 122/255, 0.05)),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 8*mm))

    # Terms
    elements.append(Paragraph("Vertragsbedingungen", styles['SectionHead']))
    elements.append(Paragraph(
        "• Vertragslaufzeit: 24 Monate ab Beauftragung<br/>"
        "• Anzahlung: 30 % des Gesamtvertragswerts, sofort fällig nach Beauftragung<br/>"
        "• Restbetrag: In 23 gleichen monatlichen Raten<br/>"
        "• Alle Preise verstehen sich zzgl. der gesetzlichen USt. (21 % NL / 19 % DE)<br/>"
        "• Gültigkeit dieses Angebots: 30 Tage ab Ausstellungsdatum<br/>"
        "• DSGVO- und EU-AI-Act-konforme Umsetzung garantiert<br/>"
        "• Gerichtsstand: Venlo, Niederlande (Burgerlijk Wetboek)",
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 6*mm))

    # Bank details
    elements.append(Paragraph("Zahlungsinformationen", styles['SectionHead']))
    elements.append(Paragraph(
        f"Überweisung innerhalb des EWR:<br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}<br/><br/>"
        f"Überweisung von außerhalb des EWR:<br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']} | BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"BIC der zwischengeschalteten Bank: {COMPANY_DATA['bank']['intermediary_bic']}",
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 10*mm))

    # CTA
    elements.append(Paragraph(
        "Wir freuen uns auf die Zusammenarbeit. Bei Fragen stehen wir Ihnen unter "
        f"<b>{COMPANY_DATA['phone']}</b> oder <b>{COMPANY_DATA['email']}</b> zur Verfügung.",
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("Mit freundlichen Grüßen,", styles['BodyText2']))
    elements.append(Paragraph(f"<b>{COMPANY_DATA['ceo']}</b><br/>Geschäftsführer, NeXifyAI", styles['BodyText2']))

    def make_header(canvas, doc):
        _header_footer(canvas, doc, "Angebot", number, date_str)

    doc.build(elements, onFirstPage=make_header, onLaterPages=make_header)
    return buf.getvalue()


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """Generate a professional invoice PDF"""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=28*mm, bottomMargin=28*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    styles = _build_styles()
    elements = []

    number = invoice_data.get("invoice_number", "—")
    date_str = invoice_data.get("date", datetime.now(timezone.utc).strftime("%d.%m.%Y"))
    due_date = invoice_data.get("due_date", "")
    customer = invoice_data.get("customer", {})
    inv_type = invoice_data.get("type", "deposit")
    items = invoice_data.get("items", [])
    totals = invoice_data.get("totals", {})

    # Customer address
    elements.append(Spacer(1, 8*mm))
    if customer.get("company"):
        elements.append(Paragraph(customer["company"], styles['BodyText2']))
    if customer.get("name"):
        elements.append(Paragraph(customer["name"], styles['BodyText2']))
    if customer.get("email"):
        elements.append(Paragraph(customer["email"], styles['SmallGray']))
    elements.append(Spacer(1, 12*mm))

    # Title
    type_labels = {"deposit": "Anzahlungsrechnung", "monthly": "Monatsrechnung", "final": "Schlussrechnung", "correction": "Korrekturrechnung"}
    title = type_labels.get(inv_type, "Rechnung")
    elements.append(Paragraph(f"{title} {number}", styles['BrandTitle']))
    if due_date:
        elements.append(Paragraph(f"Fällig am: {due_date}", styles['BrandSub']))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=CI_GRAY, spaceBefore=4, spaceAfter=12))

    # Items table
    item_header = [
        Paragraph("<b>Position</b>", styles['BodyText2']),
        Paragraph("<b>Beschreibung</b>", styles['BodyText2']),
        Paragraph("<b>Betrag (netto)</b>", styles['RightAligned'])
    ]
    item_rows = [item_header]
    for idx, item in enumerate(items, 1):
        item_rows.append([
            Paragraph(str(idx), styles['BodyText2']),
            Paragraph(item.get("description", ""), styles['BodyText2']),
            Paragraph(_fmt_eur(item.get("amount_net", 0)), styles['RightAligned'])
        ])

    item_table = Table(item_rows, colWidths=[doc.width * 0.08, doc.width * 0.62, doc.width * 0.30])
    item_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, CI_DARK),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, CI_GRAY),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 6*mm))

    # Totals
    total_data = [
        [Paragraph("Nettobetrag", styles['BodyText2']), Paragraph(_fmt_eur(totals.get("net", 0)), styles['RightAligned'])],
        [Paragraph(f"USt. {totals.get('vat_rate', 21)} %", styles['BodyText2']), Paragraph(_fmt_eur(totals.get("vat", 0)), styles['RightAligned'])],
        [Paragraph("<b>Gesamtbetrag (brutto)</b>", styles['BodyText2']), Paragraph(f"<b>{_fmt_eur(totals.get('gross', 0))}</b>", styles['TotalBold'])],
    ]
    total_table = Table(total_data, colWidths=[doc.width * 0.65, doc.width * 0.35])
    total_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, -1), (-1, -1), 1, CI_ORANGE),
        ('BACKGROUND', (0, -1), (-1, -1), colors.Color(255/255, 155/255, 122/255, 0.05)),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 8*mm))

    # Payment info
    elements.append(Paragraph("Zahlungsinformationen", styles['SectionHead']))
    ref = invoice_data.get("payment_reference", number)
    elements.append(Paragraph(
        f"Bitte überweisen Sie den Betrag unter Angabe der Rechnungsnummer <b>{ref}</b>.<br/><br/>"
        f"IBAN: {COMPANY_DATA['bank']['iban']}<br/>"
        f"BIC: {COMPANY_DATA['bank']['bic']}<br/>"
        f"Kontoinhaber: {COMPANY_DATA['name']}<br/><br/>"
        f"Von außerhalb des EWR zusätzlich:<br/>"
        f"BIC der zwischengeschalteten Bank: {COMPANY_DATA['bank']['intermediary_bic']}",
        styles['BodyText2']
    ))
    elements.append(Spacer(1, 6*mm))

    # Legal footer text
    elements.append(Paragraph(
        f"Bei Fragen zu dieser Rechnung wenden Sie sich bitte an {COMPANY_DATA['email']} oder {COMPANY_DATA['phone']}.",
        styles['SmallGray']
    ))

    def make_header(canvas, doc):
        _header_footer(canvas, doc, title, number, date_str)

    doc.build(elements, onFirstPage=make_header, onLaterPages=make_header)
    return buf.getvalue()

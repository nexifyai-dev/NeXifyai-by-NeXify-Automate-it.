"""
Server.py → Modular Routes: Automatic Extraction Script
Extracts route functions from server.py into modular route files.
"""
import re
import os
import ast

BACKEND_DIR = "/app/backend"
SERVER_FILE = os.path.join(BACKEND_DIR, "server.py")
ROUTES_DIR = os.path.join(BACKEND_DIR, "routes")

with open(SERVER_FILE, "r") as f:
    source = f.read()
    lines = source.splitlines(keepends=True)

# Route prefix → module mapping (order matters: longer prefixes first)
MODULE_MAP = [
    # AUTH
    ("/api/admin/login", "auth"),
    ("/api/auth/", "auth"),
    ("/api/customer/me", "auth"),
    ("/api/admin/me", "auth"),
    # MONITORING (before admin to catch /api/admin/monitoring, /api/admin/workers, etc.)
    ("/api/admin/monitoring", "monitoring"),
    ("/api/admin/workers", "monitoring"),
    ("/api/admin/agents", "monitoring"),
    ("/api/admin/audit/", "monitoring"),
    ("/api/admin/llm/", "monitoring"),
    ("/api/admin/e2e/", "monitoring"),
    # OUTBOUND (before admin)
    ("/api/admin/outbound", "outbound"),
    # CONTRACT (before admin)
    ("/api/admin/contracts", "contract"),
    ("/api/customer/contracts", "contract"),
    # PROJECT (before admin/customer)
    ("/api/admin/projects", "project"),
    ("/api/customer/projects", "project"),
    # BILLING (before admin)
    ("/api/admin/quotes", "billing"),
    ("/api/admin/invoices", "billing"),
    ("/api/admin/access-link", "billing"),
    ("/api/admin/billing/", "billing"),
    ("/api/admin/email/", "billing"),
    ("/api/admin/webhooks/", "billing"),
    ("/api/admin/legal/", "billing"),
    ("/api/admin/commercial/stats", "billing"),
    ("/api/payments/", "billing"),
    ("/api/webhooks/stripe", "billing"),
    ("/api/webhooks/revolut", "billing"),
    ("/api/documents/", "billing"),
    ("/api/chat/generate-offer", "billing"),
    # COMMS
    ("/api/admin/conversations", "comms"),
    ("/api/admin/memory", "comms"),
    ("/api/admin/chat-sessions", "comms"),
    ("/api/admin/customer-memory", "comms"),
    ("/api/admin/comms/", "comms"),
    ("/api/admin/whatsapp/", "comms"),
    ("/api/webhooks/whatsapp/", "comms"),
    # PORTAL
    ("/api/portal/", "portal"),
    ("/api/customer/dashboard", "portal"),
    ("/api/customer/finance", "portal"),
    # ADMIN CRM
    ("/api/admin/stats", "admin"),
    ("/api/admin/leads", "admin"),
    ("/api/admin/bookings", "admin"),
    ("/api/admin/blocked-slots", "admin"),
    ("/api/admin/customers", "admin"),
    ("/api/admin/calendar-data", "admin"),
    ("/api/admin/timeline", "admin"),
    # PUBLIC
    ("/api/health", "public"),
    ("/api/company", "public"),
    ("/api/contact", "public"),
    ("/api/booking", "public"),
    ("/api/analytics/", "public"),
    ("/api/chat/message", "public"),
    ("/api/product/", "public"),
    ("/api/public/", "public"),
]


def get_module(path):
    for prefix, mod in MODULE_MAP:
        if path.startswith(prefix):
            return mod
    return None


# Parse route decorators
route_pattern = re.compile(r'^@app\.(get|post|put|patch|delete)\("([^"]+)"')

# Find all route functions: decorator line → function end line
route_functions = []  # (start_line, end_line, method, path, module, func_name)

i = 0
while i < len(lines):
    m = route_pattern.match(lines[i])
    if m:
        method = m.group(1)
        path = m.group(2)
        module = get_module(path)
        
        # Find the function definition line
        decorator_start = i
        j = i + 1
        func_name = ""
        while j < len(lines):
            func_match = re.match(r'^(?:async )?def (\w+)\(', lines[j])
            if func_match:
                func_name = func_match.group(1)
                break
            # Could be another decorator
            if lines[j].strip() and not lines[j].strip().startswith('@') and not lines[j].strip().startswith('#'):
                break
            j += 1
        
        if func_name:
            # Find end of function (next line at indent level 0 that's not empty/comment)
            k = j + 1
            while k < len(lines):
                line = lines[k]
                # End of function: next decorator, class, or top-level code
                if line.strip() and not line[0].isspace() and not line.startswith('#'):
                    break
                k += 1
            
            route_functions.append((decorator_start, k, method, path, module, func_name))
            i = k
            continue
    i += 1

print(f"Extracted {len(route_functions)} route functions")

# Group by module
from collections import defaultdict
module_routes = defaultdict(list)
for start, end, method, path, module, func_name in route_functions:
    if module:
        module_routes[module].append((start, end, method, path, func_name))

# Also find standalone helper functions that are used within specific modules
# _compute_doc_hash → contract
# PAYMENT_STATUS_MAP, REMINDER_LEVEL_MAP → portal  
# These will be included in their respective module files

# Find _compute_doc_hash
for i, line in enumerate(lines):
    if line.startswith("def _compute_doc_hash"):
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or lines[j][0].isspace()):
            j += 1
        module_routes["contract"].insert(0, (i, j, "helper", "_compute_doc_hash", "_compute_doc_hash"))
        break

# Find PAYMENT_STATUS_MAP and REMINDER_LEVEL_MAP
for i, line in enumerate(lines):
    if line.startswith("PAYMENT_STATUS_MAP"):
        j = i + 1
        while j < len(lines) and (lines[j].strip().startswith('"') or lines[j].strip().startswith('}') or lines[j].strip().startswith("'") or not lines[j].strip()):
            j += 1
            if lines[j-1].strip() == '}':
                break
        # Find REMINDER_LEVEL_MAP too
        k = j
        while k < len(lines):
            if lines[k].startswith("REMINDER_LEVEL_MAP"):
                k2 = k + 1
                while k2 < len(lines) and (lines[k2].strip().startswith('"') or lines[k2].strip().startswith("'") or lines[k2].strip().startswith('}') or not lines[k2].strip() or lines[k2][0].isspace()):
                    k2 += 1
                    if lines[k2-1].strip() == '}':
                        break
                module_routes["portal"].insert(0, (i, k2, "helper", "status_maps", "status_maps"))
                break
            k += 1
        break

# Generate import header for each module
MODULE_IMPORTS = {
    "auth": '''"""NeXifyAI — Auth Routes"""
import os
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from routes.shared import (
    db, memory_svc, oauth2_scheme,
    create_access_token, get_current_admin, get_current_customer,
    verify_password, check_rate_limit, log_audit, send_email, email_template,
    RESEND_API_KEY, logger,
)
from domain import create_contact, create_timeline_event, utcnow
from memory_service import AGENT_IDS
from commercial import generate_access_token, verify_access_token

router = APIRouter(tags=["auth"])
''',
    "public": '''"""NeXifyAI — Public Routes"""
import os
import re
import json
import secrets
import asyncio
from datetime import datetime, timezone, timedelta
from io import BytesIO
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from routes.shared import (
    db, llm_provider, memory_svc, legal_svc,
    check_rate_limit, send_email, email_template, _log_event,
    _build_customer_memory, log_audit,
    RESEND_API_KEY, SENDER_EMAIL, NOTIFICATION_EMAILS, EMERGENT_LLM_KEY, ADVISOR_SYSTEM_PROMPT,
    logger,
)
from domain import create_contact, create_timeline_event, new_id, utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["public"])

class ContactForm(BaseModel):
    vorname: str = Field(..., min_length=2, max_length=100)
    nachname: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefon: Optional[str] = None
    unternehmen: Optional[str] = None
    nachricht: str = Field(..., min_length=10, max_length=5000)
    source: str = "contact_form"
    consent: bool = True
    datenschutz_akzeptiert: bool = True
    honeypot: Optional[str] = Field(None, alias="_hp")

class BookingRequest(BaseModel):
    vorname: str = Field(..., min_length=2)
    nachname: str = Field(..., min_length=2)
    email: EmailStr
    telefon: Optional[str] = None
    unternehmen: Optional[str] = None
    date: str
    time: str
    thema: Optional[str] = None
    datenschutz_akzeptiert: bool = True

class ChatMessage(BaseModel):
    session_id: str
    message: str
    context: Optional[dict] = None
    language: Optional[str] = "de"

class AnalyticsEvent(BaseModel):
    event: str
    properties: Optional[dict] = {}
    session_id: Optional[str] = None

''',
    "admin": '''"""NeXifyAI — Admin CRM Routes"""
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from routes.shared import (
    db, memory_svc,
    get_current_admin, log_audit, send_email, email_template,
    RESEND_API_KEY, NOTIFICATION_EMAILS, logger,
)
from domain import create_contact, create_timeline_event, utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["admin"])
''',
    "billing": '''"""NeXifyAI — Billing Routes (Quotes, Invoices, Stripe, Revolut, Documents, Legal, Email)"""
import os
import json
import hashlib
import secrets
import asyncio
from datetime import datetime, timezone, timedelta
from io import BytesIO
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from routes.shared import (
    db, memory_svc, billing_svc, legal_svc, worker_mgr,
    get_current_admin, get_current_customer, check_rate_limit,
    log_audit, _log_event, send_email, email_template, archive_pdf_to_storage,
    RESEND_API_KEY, SENDER_EMAIL, NOTIFICATION_EMAILS,
    STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, logger,
)
from domain import (
    create_timeline_event, create_contract, create_contract_appendix,
    ContractStatus, utcnow, LEGAL_MODULES, APPENDIX_TYPE_LABELS,
)
from commercial import (
    COMPANY_DATA as COMM_COMPANY, TARIFF_CONFIG,
    calc_contract, get_tariff, get_next_number,
    generate_quote_pdf, generate_invoice_pdf, generate_contract_pdf,
    generate_access_token, verify_access_token,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["billing"])

class QuoteRequest(BaseModel):
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: Optional[str] = ""
    customer_phone: Optional[str] = ""
    customer_country: Optional[str] = "DE"
    notes: Optional[str] = ""

class OfferDiscoveryRequest(BaseModel):
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: Optional[str] = ""
    customer_phone: Optional[str] = ""
    customer_country: Optional[str] = "DE"
    customer_industry: Optional[str] = ""
    session_id: Optional[str] = ""
    use_case: Optional[str] = ""
    target_systems: Optional[str] = ""
    automations: Optional[str] = ""
    channels: Optional[str] = ""
    gdpr_relevant: Optional[bool] = True
    timeline: Optional[str] = ""
    special_requirements: Optional[str] = ""

''',
    "portal": '''"""NeXifyAI — Portal Routes (Customer Portal, Dashboard, Finance)"""
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import (
    db, memory_svc,
    get_current_admin, get_current_customer,
    log_audit, _log_event, _build_customer_memory,
    logger,
)
from domain import create_timeline_event, utcnow
from commercial import COMPANY_DATA as COMM_COMPANY, verify_access_token

router = APIRouter(tags=["portal"])
''',
    "comms": '''"""NeXifyAI — Communications Routes (Conversations, WhatsApp, Memory, Chat-Sessions)"""
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import (
    db, comms_svc, memory_svc,
    get_current_admin, _build_customer_memory,
    logger,
)
from domain import (
    Channel, MessageDirection, WhatsAppSessionStatus,
    create_contact, create_conversation, create_message,
    create_timeline_event, create_whatsapp_session,
    utcnow,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["comms"])
''',
    "contract": '''"""NeXifyAI — Contract OS Routes"""
import os
import json
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from routes.shared import (
    db, memory_svc, legal_svc,
    get_current_admin, get_current_customer,
    send_email, email_template, archive_pdf_to_storage,
    RESEND_API_KEY, logger,
)
from domain import (
    create_contract, create_contract_appendix, create_contract_evidence,
    create_timeline_event, ContractStatus, utcnow,
    LEGAL_MODULES, APPENDIX_TYPE_LABELS,
)
from commercial import (
    calc_contract, get_next_number, generate_contract_pdf,
    generate_access_token,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["contract"])
''',
    "project": '''"""NeXifyAI — Project Routes"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import (
    db, memory_svc,
    get_current_admin, get_current_customer,
    logger,
)
from domain import (
    create_project, create_project_section, create_project_chat_message,
    create_project_version, create_timeline_event,
    PROJECT_SECTIONS, PROJECT_SECTION_LABELS,
    utcnow,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["project"])
''',
    "outbound": '''"""NeXifyAI — Outbound Lead Machine Routes"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import (
    db, outbound_svc, legal_svc, memory_svc,
    get_current_admin,
    logger,
)
from domain import create_contact, create_timeline_event, utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["outbound"])
''',
    "monitoring": '''"""NeXifyAI — Monitoring, LLM, Workers, Agents, Audit, E2E Routes"""
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import (
    db, worker_mgr, llm_provider, orchestrator, agents, memory_svc,
    get_current_admin, _build_customer_memory, logger,
)
from domain import utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["monitoring"])
''',
}

# Generate route files
for module_name, routes in module_routes.items():
    # Skip if already manually created (auth, monitoring, public already done)
    filepath = os.path.join(ROUTES_DIR, f"{module_name}_routes.py")
    
    header = MODULE_IMPORTS.get(module_name, f'"""NeXifyAI — {module_name.title()} Routes"""\nfrom fastapi import APIRouter\nrouter = APIRouter(tags=["{module_name}"])\n')
    
    body_parts = []
    for start, end, method, path, func_name in routes:
        # Extract code block
        block = lines[start:end]
        # Replace @app. with @router.
        code = ""
        for line in block:
            code += line.replace("@app.", "@router.")
        body_parts.append(code)
    
    content = header + "\n\n" + "\n".join(body_parts)
    
    with open(filepath, "w") as f:
        f.write(content)
    
    route_count = sum(1 for _, _, m, _, _ in routes if m != "helper")
    print(f"Generated {filepath} ({route_count} routes)")

print("\nDone! Route files generated.")

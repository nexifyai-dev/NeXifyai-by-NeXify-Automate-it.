"""
Server.py → Modular Routes: FIXED Extraction Script
Properly handles multi-line function signatures.
"""
import re
import os
import tokenize
import io

BACKEND_DIR = "/app/backend"
SERVER_FILE = os.path.join(BACKEND_DIR, "server_monolith_backup.py")
ROUTES_DIR = os.path.join(BACKEND_DIR, "routes")

with open(SERVER_FILE, "r") as f:
    lines = f.readlines()

# Module classification (order: longest prefix first)
MODULE_MAP = [
    ("/api/admin/login", "auth"),
    ("/api/auth/", "auth"),
    ("/api/customer/me", "auth"),
    ("/api/admin/me", "auth"),
    ("/api/admin/monitoring", "monitoring"),
    ("/api/admin/workers", "monitoring"),
    ("/api/admin/agents", "monitoring"),
    ("/api/admin/audit/", "monitoring"),
    ("/api/admin/llm/", "monitoring"),
    ("/api/admin/e2e/", "monitoring"),
    ("/api/admin/outbound", "outbound"),
    ("/api/admin/contracts", "contract"),
    ("/api/customer/contracts", "contract"),
    ("/api/admin/projects", "project"),
    ("/api/customer/projects", "project"),
    ("/api/admin/quotes", "billing"),
    ("/api/admin/invoices", "billing"),
    ("/api/admin/access-link", "billing"),
    ("/api/admin/billing/", "billing"),
    ("/api/admin/email/", "billing"),
    ("/api/admin/webhooks/", "billing"),
    ("/api/admin/legal/", "billing"),
    ("/api/admin/commercial/", "billing"),
    ("/api/payments/", "billing"),
    ("/api/webhooks/stripe", "billing"),
    ("/api/webhooks/revolut", "billing"),
    ("/api/documents/", "billing"),
    ("/api/chat/generate-offer", "billing"),
    ("/api/admin/conversations", "comms"),
    ("/api/admin/memory", "comms"),
    ("/api/admin/chat-sessions", "comms"),
    ("/api/admin/customer-memory", "comms"),
    ("/api/admin/comms/", "comms"),
    ("/api/admin/whatsapp/", "comms"),
    ("/api/webhooks/whatsapp/", "comms"),
    ("/api/portal/", "portal"),
    ("/api/customer/dashboard", "portal"),
    ("/api/customer/finance", "portal"),
    ("/api/admin/stats", "admin"),
    ("/api/admin/leads", "admin"),
    ("/api/admin/bookings", "admin"),
    ("/api/admin/blocked-slots", "admin"),
    ("/api/admin/customers", "admin"),
    ("/api/admin/calendar-data", "admin"),
    ("/api/admin/timeline", "admin"),
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


def find_function_end(lines, func_start_line):
    """Find the end of a function by tracking indentation.
    func_start_line is the line with 'def ...' or 'async def ...'"""
    # First, find the colon that ends the function signature
    # Handle multi-line signatures
    i = func_start_line
    paren_depth = 0
    found_colon = False
    while i < len(lines):
        line = lines[i]
        for ch in line:
            if ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth -= 1
        # After all parens are closed, look for the colon
        if paren_depth <= 0 and ':' in line:
            found_colon = True
            break
        i += 1

    if not found_colon:
        return func_start_line + 1

    # Now find the end of the function body
    # The function body starts at i+1 and continues until we hit
    # a line at indent level 0 that's not empty/comment
    body_start = i + 1
    j = body_start
    while j < len(lines):
        line = lines[j]
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            j += 1
            continue
        # If line starts at column 0, it's the end of the function
        # (unless it's a decorator for the next function, which is also a boundary)
        if not line[0].isspace():
            break
        j += 1
    return j


# Find all route decorators
route_pattern = re.compile(r'^@app\.(get|post|put|patch|delete)\("([^"]+)"')

# Build list of (decorator_start, function_end, method, path, module, func_name)
route_blocks = []
i = 0
while i < len(lines):
    m = route_pattern.match(lines[i])
    if m:
        method = m.group(1)
        path = m.group(2)
        module = get_module(path)

        # Find the function def line (skip additional decorators)
        decorator_start = i
        j = i + 1
        func_name = ""
        while j < len(lines):
            func_match = re.match(r'^(?:async )?def (\w+)\(', lines[j])
            if func_match:
                func_name = func_match.group(1)
                break
            # Skip other decorators and comments
            stripped = lines[j].strip()
            if stripped and not stripped.startswith('@') and not stripped.startswith('#'):
                break
            j += 1

        if func_name:
            func_end = find_function_end(lines, j)
            route_blocks.append((decorator_start, func_end, method, path, module, func_name))
            i = func_end
            continue
    i += 1

print(f"Extracted {len(route_blocks)} route blocks")

# Also find standalone helpers needed by specific modules
helper_blocks = {}

# _compute_doc_hash → contract
for i, line in enumerate(lines):
    if line.startswith("def _compute_doc_hash"):
        end = find_function_end(lines, i)
        helper_blocks["contract"] = helper_blocks.get("contract", [])
        helper_blocks["contract"].append((i, end))
        break

# PAYMENT_STATUS_MAP + REMINDER_LEVEL_MAP → portal
for i, line in enumerate(lines):
    if line.startswith("PAYMENT_STATUS_MAP"):
        # Find end of both dicts
        j = i
        found_reminder = False
        brace_depth = 0
        while j < len(lines):
            for ch in lines[j]:
                if ch == '{': brace_depth += 1
                elif ch == '}': brace_depth -= 1
            if "REMINDER_LEVEL_MAP" in lines[j] and j > i:
                found_reminder = True
            if found_reminder and brace_depth <= 0:
                j += 1
                break
            j += 1
        helper_blocks["portal"] = helper_blocks.get("portal", [])
        helper_blocks["portal"].append((i, j))
        break

# Group routes by module
from collections import defaultdict
module_routes = defaultdict(list)
for start, end, method, path, module, func_name in route_blocks:
    if module:
        module_routes[module].append((start, end))
    else:
        print(f"  UNASSIGNED: {method.upper()} {path} (line {start+1})")

# Module imports
MODULE_IMPORTS = {
    "auth": '''"""NeXifyAI — Auth Routes"""
import os
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from routes.shared import (
    db, memory_svc,
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
    check_rate_limit, send_email, email_template,
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
    "billing": '''"""NeXifyAI — Billing Routes"""
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
    create_timeline_event, OfferStatus, utcnow,
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
    "portal": '''"""NeXifyAI — Portal Routes"""
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import (
    db, memory_svc,
    get_current_admin, get_current_customer,
    log_audit, _log_event, send_email, email_template,
    _build_customer_memory,
    RESEND_API_KEY, logger,
)
from domain import create_timeline_event, utcnow
from commercial import COMPANY_DATA as COMM_COMPANY, verify_access_token

router = APIRouter(tags=["portal"])
''',
    "comms": '''"""NeXifyAI — Communications Routes"""
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

# Write route files
for module_name, routes in module_routes.items():
    filepath = os.path.join(ROUTES_DIR, f"{module_name}_routes.py")
    header = MODULE_IMPORTS.get(module_name, f'"""NeXifyAI — {module_name.title()} Routes"""\nfrom fastapi import APIRouter\nrouter = APIRouter(tags=["{module_name}"])\n\n')

    body_parts = []

    # Add helper blocks first
    if module_name in helper_blocks:
        for hstart, hend in helper_blocks[module_name]:
            block = "".join(lines[hstart:hend])
            body_parts.append(block)

    for start, end in routes:
        block = "".join(lines[start:end])
        # Replace @app. with @router.
        block = block.replace("@app.", "@router.")
        body_parts.append(block)

    content = header + "\n" + "\n".join(body_parts)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Generated {filepath} ({len(routes)} route blocks, {sum(end-start for start,end in routes)} lines)")

# Verify syntax
import ast
errors = 0
for module_name in module_routes:
    filepath = os.path.join(ROUTES_DIR, f"{module_name}_routes.py")
    try:
        with open(filepath) as f:
            ast.parse(f.read())
        print(f"  PASS: {filepath}")
    except SyntaxError as e:
        print(f"  FAIL: {filepath} — {e}")
        errors += 1

print(f"\n{'All files pass syntax check!' if errors == 0 else f'{errors} files have syntax errors'}")

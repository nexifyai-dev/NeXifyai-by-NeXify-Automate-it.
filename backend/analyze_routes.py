"""
Server.py → Modular Routes Migration Script
Extracts routes from monolith to modular router files.
Run once from /app/backend/
"""
import re
import os

# Read original server.py
with open("/app/backend/server.py", "r") as f:
    lines = f.readlines()

# Map every @app route to a module
# (line_number, module_name)
ROUTE_MAP = {
    # AUTH
    "/api/admin/login": "auth",
    "/api/auth/check-email": "auth",
    "/api/auth/request-magic-link": "auth",
    "/api/auth/verify-token": "auth",
    "/api/customer/me": "auth",
    "/api/admin/me": "auth",
    # PUBLIC
    "/api/health": "public",
    "/api/company": "public",
    "/api/contact": "public",
    "/api/booking/slots": "public",
    "/api/booking": "public",
    "/api/analytics/track": "public",
    "/api/chat/message": "public",
    "/api/chat/generate-offer": "public",
    "/api/product/tariffs": "public",
    "/api/product/faq": "public",
    "/api/product/services": "public",
    "/api/product/compliance": "public",
    "/api/product/tariff-sheet": "public",
    "/api/product/descriptions": "public",
    "/api/public/opt-out": "public",
    # ADMIN CRM
    "/api/admin/stats": "admin",
    "/api/admin/leads": "admin",
    "/api/admin/bookings": "admin",
    "/api/admin/blocked-slots": "admin",
    "/api/admin/customers": "admin",
    "/api/admin/calendar-data": "admin",
    "/api/admin/commercial/stats": "admin",
    "/api/admin/timeline": "admin",
    "/api/admin/leads/{lead_id}/notes": "admin",
    # BILLING
    "/api/admin/quotes": "billing",
    "/api/admin/invoices": "billing",
    "/api/admin/access-link": "billing",
    "/api/admin/invoices/{invoice_id}": "billing",
    "/api/admin/invoices/{invoice_id}/create-stripe-checkout": "billing",
    "/api/admin/invoices/{invoice_id}/send": "billing",
    "/api/admin/invoices/{invoice_id}/mark-paid": "billing",
    "/api/admin/invoices/{invoice_id}/send-reminder": "billing",
    "/api/admin/billing/status": "billing",
    "/api/admin/billing/reconcile": "billing",
    "/api/admin/billing/status/{email}": "billing",
    "/api/admin/billing/sync-quote/{quote_id}": "billing",
    "/api/admin/billing/sync-invoice/{invoice_id}": "billing",
    "/api/admin/email/stats": "billing",
    "/api/admin/email/test": "billing",
    "/api/admin/webhooks/history": "billing",
    "/api/admin/legal/": "billing",
    "/api/payments/checkout/status/{session_id}": "billing",
    "/api/webhooks/stripe": "billing",
    "/api/webhooks/revolut": "billing",
    "/api/documents/{doc_type}/{ref_id}/pdf": "billing",
    # PORTAL
    "/api/portal/customer/{token}": "portal",
    "/api/portal/quote/{quote_id}/accept": "portal",
    "/api/portal/quote/{quote_id}/decline": "portal",
    "/api/portal/quote/{quote_id}/revision": "portal",
    "/api/customer/dashboard": "portal",
    "/api/customer/finance": "portal",
    # COMMS
    "/api/admin/conversations": "comms",
    "/api/admin/memory": "comms",
    "/api/admin/chat-sessions": "comms",
    "/api/admin/customer-memory": "comms",
    "/api/admin/comms/": "comms",
    "/api/admin/whatsapp/": "comms",
    "/api/webhooks/whatsapp/inbound": "comms",
    # CONTRACT
    "/api/admin/contracts": "contract",
    "/api/customer/contracts": "contract",
    # PROJECT
    "/api/admin/projects": "project",
    "/api/customer/projects": "project",
    # OUTBOUND
    "/api/admin/outbound": "outbound",
    # MONITORING
    "/api/admin/monitoring": "monitoring",
    "/api/admin/workers": "monitoring",
    "/api/admin/agents": "monitoring",
    "/api/admin/audit/": "monitoring",
    "/api/admin/llm/": "monitoring",
    "/api/admin/e2e/": "monitoring",
}


def get_module_for_route(path):
    """Determine which module a route belongs to."""
    # Exact match first
    if path in ROUTE_MAP:
        return ROUTE_MAP[path]
    # Prefix match
    for prefix, module in sorted(ROUTE_MAP.items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix.rstrip("/")):
            return module
    return None


# Find all route decorators and their line numbers
route_pattern = re.compile(r'^@app\.(get|post|put|patch|delete)\("([^"]+)"')
route_blocks = []

for i, line in enumerate(lines):
    m = route_pattern.match(line)
    if m:
        method = m.group(1)
        path = m.group(2)
        module = get_module_for_route(path)
        if module:
            route_blocks.append((i, method, path, module))

print(f"Found {len(route_blocks)} route blocks")

# Count by module
from collections import Counter
counts = Counter(module for _, _, _, module in route_blocks)
for mod, count in sorted(counts.items()):
    print(f"  {mod}: {count} routes")

# Verify all routes are assigned
unassigned = [(i, method, path) for i, method, path, module in route_blocks if not module]
if unassigned:
    print(f"\nWARNING: {len(unassigned)} unassigned routes:")
    for i, method, path in unassigned:
        print(f"  Line {i+1}: {method.upper()} {path}")

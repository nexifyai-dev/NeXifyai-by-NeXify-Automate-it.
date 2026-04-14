# NeXifyAI — Supabase Schema Design
## Version: 0.1 (Draft)

**Status:** Design-Phase, noch nicht migriert
**Zweck:** Eigene Datenbank statt Emergent MongoDB

---

## TENANT-MODELL (MANDANTENTRENNUNG)

Alle Tabellen haben `tenant_id` für Mandantentrennung.

```sql
-- Master-Tabelle für Mandanten
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,  -- studienkolleg-aachen, nexifyai-intern
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Admin-User pro Tenant
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    role TEXT DEFAULT 'member',  -- admin, member, viewer
    name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);
```

---

## CRM & CUSTOMERS

```sql
-- Kunden (extern)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Basis
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    website TEXT,
    
    -- Klassifizierung
    type TEXT,  -- prospect, customer, partner
    status TEXT DEFAULT 'active',  -- active, inactive, churned
    
    -- Lead-Score
    score INTEGER DEFAULT 0,
    source TEXT,  -- inbound, outbound, referral
    
    -- Meta
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Kontakte (Personen bei Kunden)
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,
    is_primary BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projekte
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',  -- active, completed, cancelled
    
    -- Budget & Timeline
    budget DECIMAL(12,2),
    start_date DATE,
    end_date DATE,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## TASKS & ORACLE

```sql
-- Oracle Tasks (zentral)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Referenzen
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    assigned_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Task-Daten
    title TEXT NOT NULL,
    description TEXT,
    type TEXT,  -- intake, research, outreach, offer, support, etc.
    priority TEXT DEFAULT 'normal',  -- low, normal, high, urgent
    status TEXT DEFAULT 'backlog',  -- backlog, todo, in_progress, review, done, cancelled
    
    -- Oracle-spezifisch
    source TEXT,  -- chat, brain_scan, monitoring, manual
    agent_type TEXT,  -- Welcher Agent soll das machen?
    agent_run_id UUID,
    parent_task_id UUID REFERENCES tasks(id),
    
    -- Feedback-Loop
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_feedback TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Task-Log (Audit-Trail)
CREATE TABLE task_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    action TEXT NOT NULL,  -- created, assigned, status_changed, commented, completed
    actor TEXT,  -- user_id, agent_type, system
    details JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Runs
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    agent_type TEXT NOT NULL,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Performance
    tokens_used INTEGER,
    cost_usd DECIMAL(10,6),
    duration_ms INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

---

## OFFERS & CONTRACTS

```sql
-- Angebote
CREATE TABLE offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',  -- draft, sent, accepted, rejected, expired
    
    -- Finanzen
    total_amount DECIMAL(12,2),
    currency TEXT DEFAULT 'EUR',
    valid_until DATE,
    
    -- PDF
    pdf_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Offer-Positionen
CREATE TABLE offer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_id UUID REFERENCES offers(id) ON DELETE CASCADE,
    
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1,
    unit_price DECIMAL(12,2),
    total_price DECIMAL(12,2),
    
    sort_order INTEGER DEFAULT 0
);
```

---

## INVOICES & FINANCE

```sql
-- Rechnungen
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
    
    invoice_number TEXT NOT NULL,
    status TEXT DEFAULT 'draft',  -- draft, sent, paid, overdue, cancelled
    
    amount DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    currency TEXT DEFAULT 'EUR',
    
    issue_date DATE,
    due_date DATE,
    paid_date DATE,
    
    -- PDF
    pdf_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Zahlungen
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    
    amount DECIMAL(12,2),
    currency TEXT DEFAULT 'EUR',
    method TEXT,  -- bank_transfer, credit_card, paypal
    
    status TEXT DEFAULT 'pending',  -- pending, completed, failed
    transaction_id TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## SUPPORT & TICKETS

```sql
-- Tickets
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    
    title TEXT NOT NULL,
    description TEXT,
    type TEXT,  -- technical, billing, general
    priority TEXT DEFAULT 'normal',  -- low, normal, high, critical
    status TEXT DEFAULT 'open',  -- open, in_progress, pending, resolved, closed
    
    assigned_user_id UUID REFERENCES users(id),
    
    sla_due_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ticket-Kommentare
CREATE TABLE ticket_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
    
    author_type TEXT,  -- customer, user, agent
    author_id UUID,
    content TEXT NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## COMMUNICATION

```sql
-- E-Mails
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    ticket_id UUID REFERENCES tickets(id) ON DELETE SET NULL,
    
    direction TEXT NOT NULL,  -- inbound, outbound
    subject TEXT NOT NULL,
    body TEXT,
    from_email TEXT,
    to_email TEXT,
    
    status TEXT DEFAULT 'received',  -- received, processed, failed
    
    headers JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Termine
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    
    title TEXT NOT NULL,
    description TEXT,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    
    status TEXT DEFAULT 'scheduled',  -- scheduled, confirmed, cancelled, completed
    
    location TEXT,
    meeting_url TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## KNOWLEDGE & AUDIT

```sql
-- Knowledge Base
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    title TEXT NOT NULL,
    content TEXT,
    category TEXT,
    tags TEXT[],
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log (ISO 9001)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    entity_type TEXT NOT NULL,  -- task, invoice, customer, etc.
    entity_id UUID,
    
    action TEXT NOT NULL,  -- created, updated, deleted, status_changed
    actor_type TEXT,  -- user, system, api
    actor_id UUID,
    
    old_values JSONB,
    new_values JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## INDEXES

```sql
-- Performance Indexes
CREATE INDEX idx_tasks_tenant_status ON tasks(tenant_id, status);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_user_id);
CREATE INDEX idx_tasks_due ON tasks(due_at) WHERE status NOT IN ('done', 'cancelled');
CREATE INDEX idx_invoices_tenant_status ON invoices(tenant_id, status);
CREATE INDEX idx_customers_tenant_type ON customers(tenant_id, type);
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);
```

---

## ROW LEVEL SECURITY (RLS)

```sql
-- RLS aktivieren für alle Tabellen
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
-- etc.

-- Policy: Nur eigener Tenant
CREATE POLICY tenant_isolation ON tasks
    USING (tenant_id = current_tenant_id());

-- Helper Function
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.tenant_id', true), '')::UUID;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## MIGRATION VON MONGODB

```
MongoDB Collections → Supabase Tables
─────────────────────────────────────
conversations    → conversations (Chat-History)
vector_memories  → mem0 (Brain)
users           → users
organizations   → tenants
...
```

**Phase 10 des Implementierungsplans kümmert sich um die Migration.**

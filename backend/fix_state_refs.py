"""
Fix all route files to use S.xxx for mutable state references.
Replaces bare state variable access with S.xxx pattern.
"""
import re
import os
import ast

ROUTES_DIR = "/app/backend/routes"

# State variables that need S. prefix (these are rebound after import)
STATE_VARS = [
    "db", "worker_mgr", "comms_svc", "billing_svc", "outbound_svc",
    "legal_svc", "llm_provider", "orchestrator", "agents", "memory_svc",
]

# Config variables (also rebound via init_config)
CONFIG_VARS = [
    "RESEND_API_KEY", "SENDER_EMAIL", "SECRET_KEY", "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES", "NOTIFICATION_EMAILS", "EMERGENT_LLM_KEY",
    "ADMIN_EMAIL", "STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET", "ADVISOR_SYSTEM_PROMPT",
]

# Functions that DON'T need S. prefix (they resolve their own module globals correctly)
# create_access_token, get_current_admin, get_current_customer, verify_password,
# check_rate_limit, log_audit, _log_event, send_email, email_template,
# archive_pdf_to_storage, _build_customer_memory, hash_password, oauth2_scheme, logger

ALL_STATE = STATE_VARS + CONFIG_VARS

def fix_imports(content, filename):
    """Replace from routes.shared import (state_vars) with S-based imports."""
    # Find the import block from routes.shared
    import_pattern = re.compile(
        r'from routes\.shared import \((.*?)\)',
        re.DOTALL
    )
    
    match = import_pattern.search(content)
    if not match:
        # Try single-line import
        import_pattern2 = re.compile(r'from routes\.shared import (.+)')
        match = import_pattern2.search(content)
    
    if not match:
        return content
    
    # Parse imported names
    import_text = match.group(1)
    imported_names = [n.strip().rstrip(',') for n in import_text.replace('\n', ' ').split(',')]
    imported_names = [n for n in imported_names if n]
    
    # Separate state vars from functions
    state_imports = [n for n in imported_names if n in ALL_STATE]
    func_imports = [n for n in imported_names if n not in ALL_STATE]
    
    # Build new import statement
    new_imports = "from routes.shared import S"
    if func_imports:
        new_imports += f"\nfrom routes.shared import (\n    " + ",\n    ".join(func_imports) + ",\n)"
    
    # Replace the import
    content = content[:match.start()] + new_imports + content[match.end():]
    
    # Now replace bare state var references with S.xxx
    for var in state_imports:
        # Replace standalone references but NOT:
        # - Part of another word (e.g., 'db_client' should not become 'S.db_client')
        # - Already prefixed with S. or self.
        # - In import statements
        # - In string literals
        
        # Use word boundary matching
        # Pattern: \bvar\b but NOT preceded by S. or . or _ 
        # and NOT followed by _ or alnum (to avoid matching db_client etc)
        if var == "db":
            # Special case: db is common prefix. Match db. (attribute access) and standalone db
            # Replace 'db.' with 'S.db.' (most common pattern)
            content = re.sub(r'(?<!\w)(?<!S\.)db\.', 'S.db.', content)
            # Replace standalone 'db' in conditions like 'if db:' or 'if not db'
            content = re.sub(r'(?<!\w)(?<!S\.)db(?!\w|\.)', 'S.db', content)
        elif var == "agents":
            content = re.sub(r'(?<!\w)(?<!S\.)agents(?!\w)', 'S.agents', content)
        else:
            # For other state vars, replace word-boundary matches
            content = re.sub(r'(?<!\w)' + re.escape(var) + r'(?!\w)', f'S.{var}', content)
    
    return content


def fix_shared_py():
    """Fix routes/shared.py itself - functions reference S.db, S.memory_svc etc."""
    filepath = os.path.join(ROUTES_DIR, "shared.py")
    with open(filepath, 'r') as f:
        content = f.read()
    
    # In shared.py, functions like send_email, get_current_admin etc. 
    # access module-level vars db, memory_svc etc. 
    # These need to reference S.db, S.memory_svc etc.
    
    for var in STATE_VARS:
        if var == "db":
            # Replace 'db.' with 'S.db.' but not in class _AppState or in S.db already
            content = re.sub(r'(?<!\w)(?<!S\.)(?<!_AppState\.)db\.', 'S.db.', content)
            # Replace standalone 'db' in conditions
            content = re.sub(r'(?<!\w)(?<!S\.)(?<!_AppState\.)db(?!\w|\.)', 'S.db', content)
        elif var == "agents":
            content = re.sub(r'(?<!\w)(?<!S\.)agents(?!\w)', 'S.agents', content)
        elif var == "rate_limit_storage":
            content = re.sub(r'(?<!\w)(?<!S\.)rate_limit_storage', 'S.rate_limit_storage', content)
        else:
            # In function bodies only (not in class definition)
            content = re.sub(r'(?<!\w)(?<!S\.)' + re.escape(var) + r'(?!\w)', f'S.{var}', content)
    
    # Also fix config vars in function bodies
    for var in CONFIG_VARS:
        content = re.sub(r'(?<!\w)(?<!S\.)' + re.escape(var) + r'(?!\w)', f'S.{var}', content)
    
    # Fix double S.S. references
    content = content.replace('S.S.', 'S.')
    
    # Fix the class definition - remove S. prefix from class body
    # The class _AppState should NOT have S. prefixes
    lines = content.split('\n')
    in_class = False
    fixed_lines = []
    for line in lines:
        if 'class _AppState:' in line:
            in_class = True
            fixed_lines.append(line)
            continue
        if in_class:
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                in_class = False
            else:
                # Remove S. prefix from class body
                line = line.replace('S.', '')
        fixed_lines.append(line)
    content = '\n'.join(fixed_lines)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed: {filepath}")


def fix_route_file(filename):
    """Fix a single route file."""
    filepath = os.path.join(ROUTES_DIR, filename)
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = fix_imports(content, filename)
    
    # Fix double S.S. references
    content = content.replace('S.S.', 'S.')
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed: {filepath}")


# Fix shared.py first
fix_shared_py()

# Fix all route files
for filename in os.listdir(ROUTES_DIR):
    if filename.endswith('_routes.py'):
        fix_route_file(filename)

# Verify syntax
errors = 0
for filename in os.listdir(ROUTES_DIR):
    if filename.endswith('.py'):
        filepath = os.path.join(ROUTES_DIR, filename)
        try:
            with open(filepath) as f:
                ast.parse(f.read())
            print(f"  PASS: {filepath}")
        except SyntaxError as e:
            print(f"  FAIL: {filepath} — {e}")
            errors += 1

print(f"\n{'All files pass!' if errors == 0 else f'{errors} errors'}")

from __future__ import annotations

import ast
import builtins
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
errors=[]


def fail(message):
    errors.append(message)


def read(path):
    return path.read_text(encoding='utf-8',errors='strict')


# Python syntax + duplicate top-level API definitions
python_files=list((ROOT/'backend').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
for path in python_files:
    try:
        tree=ast.parse(read(path),filename=str(path))
    except Exception as exc:
        fail(f'Python syntax: {path.relative_to(ROOT)}: {exc}')
        continue
    if 'backend/apps/core/api' in path.as_posix():
        seen={}
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                if node.name in seen:
                    fail(f'Duplicate top-level API definition: {path.relative_to(ROOT)} {node.name} lines {seen[node.name]}/{node.lineno}')
                seen[node.name]=node.lineno


# Migration integrity
apps_root=ROOT/'backend/apps'
migration_apps=[]
concrete_models=[]
for models_path in apps_root.glob('*/models.py'):
    app=models_path.parent.name
    try:
        tree=ast.parse(read(models_path))
    except Exception:
        continue
    names=[]
    for node in tree.body:
        if not isinstance(node,ast.ClassDef):
            continue
        bases={ast.unparse(base) for base in node.bases}
        if not bases.intersection({'TimeStampedModel','models.Model','AbstractUser'}):
            continue
        if app=='core' and node.name=='TimeStampedModel':
            continue
        names.append(node.name)
    if names:
        migration_apps.append(app)
        concrete_models.extend((app,name) for name in names)

for app in sorted(migration_apps):
    migration_dir=apps_root/app/'migrations'
    if not migration_dir.exists():
        fail(f'Missing migrations directory for app: {app}')
        continue
    initial=migration_dir/'0001_initial.py'
    relations=migration_dir/'0002_relations.py'
    constraints=migration_dir/'0003_constraints.py'
    for required in [initial,relations,constraints]:
        if not required.exists():
            fail(f'Missing committed migration: {required.relative_to(ROOT)}')
    if initial.exists():
        text=read(initial)
        for model_app,model_name in [x for x in concrete_models if x[0]==app]:
            if f"name='{model_name}'" not in text and f'name="{model_name}"' not in text:
                fail(f'Model {app}.{model_name} missing from 0001_initial.py')

migration_files=list(apps_root.glob('*/migrations/[0-9]*.py'))
builtins_set=set(dir(builtins))
for path in migration_files:
    try:
        tree=ast.parse(read(path),filename=str(path))
    except Exception as exc:
        fail(f'Migration syntax: {path.relative_to(ROOT)}: {exc}')
        continue
    imported=set();defined=set()
    for node in tree.body:
        if isinstance(node,ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(node,ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
        elif isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
            defined.add(node.name)
        elif isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target,ast.Name):
                    defined.add(target.id)
    allowed=imported|defined|builtins_set|{'True','False','None'}
    unknown=sorted({
        node.id for node in ast.walk(tree)
        if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load) and node.id not in allowed
    })
    if unknown:
        fail(f"Unresolved migration references: {path.relative_to(ROOT)} -> {', '.join(unknown)}")
    for node in ast.walk(tree):
        if not isinstance(node,ast.Assign):
            continue
        if not any(isinstance(t,ast.Name) and t.id=='dependencies' for t in node.targets):
            continue
        if not isinstance(node.value,(ast.List,ast.Tuple)):
            continue
        for dep in node.value.elts:
            if not isinstance(dep,ast.Tuple) or len(dep.elts)!=2:
                continue
            if not all(isinstance(x,ast.Constant) and isinstance(x.value,str) for x in dep.elts):
                continue
            dep_app,dep_name=(x.value for x in dep.elts)
            # Dependencies on Django/contrib or third-party apps are resolved by installed packages in CI.
            if not (apps_root/dep_app).exists():
                continue
            target=apps_root/dep_app/'migrations'/f'{dep_name}.py'
            if not target.exists():
                fail(f'Broken migration dependency in {path.relative_to(ROOT)}: {dep_app}.{dep_name}')


# Frontend preflight
frontend=ROOT/'frontend'
root_app=frontend/'app'
src_app=frontend/'src/app'
if root_app.exists() and src_app.exists():
    fail('Both frontend/app and frontend/src/app exist. Cafino must have one App Router.')
if not src_app.exists():
    fail('frontend/src/app is missing.')
if root_app.exists():
    fail('Stale frontend/app tree exists; clean extraction is required.')
frontend_sources=[p for p in (frontend/'src').rglob('*') if p.is_file() and p.suffix in {'.ts','.tsx','.js','.jsx','.css'}]
for path in frontend_sources:
    text=read(path)
    if 'next/font' in text:
        fail(f'Network/font dependency forbidden for local-first build: {path.relative_to(ROOT)}')
    if 'CoffeeSan' in text or 'Coffee San' in text:
        fail(f'Stale CoffeeSan identity found: {path.relative_to(ROOT)}')
layout=src_app/'layout.tsx'
if not layout.exists():
    fail('frontend/src/app/layout.tsx missing')
elif 'Cafino' not in read(layout):
    fail('Root layout metadata/identity does not contain Cafino.')

import_pattern=re.compile(r'''(?:from\s+|import\s*\(\s*|require\(\s*)["'](@/[^"']+)["']''')
extensions=['.ts','.tsx','.js','.jsx','.json']
for path in frontend_sources:
    if path.suffix=='.css':
        continue
    for alias in import_pattern.findall(read(path)):
        rel=alias[2:]
        base=frontend/'src'/rel
        candidates=[base]
        candidates += [Path(str(base)+ext) for ext in extensions]
        candidates += [base/f'index{ext}' for ext in extensions]
        if not any(candidate.exists() for candidate in candidates):
            fail(f'Unresolved frontend alias {alias} imported by {path.relative_to(ROOT)}')


# Tenant/security static guards
api_root=ROOT/'backend/apps/core/api'
try:
    viewset_files=sorted(api_root.glob('viewsets_*.py'))
    if not viewset_files:
        fail('Domain ViewSet modules are missing')
    for viewsets_path in viewset_files:
        viewsets_tree=ast.parse(read(viewsets_path))
        for cls in [n for n in viewsets_tree.body if isinstance(n,ast.ClassDef) and any(isinstance(b,ast.Name) and b.id=='BaseVS' for b in n.bases)]:
            attrs={
                node.targets[0].id for node in cls.body
                if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            }
            if cls.name not in {'BusinessVS','BranchVS'} and 'cafino_read_permission' not in attrs:
                fail(f'BaseVS missing explicit read permission: {cls.name}')
except Exception as exc:
    fail(f'Unable to inspect BaseVS read permissions: {exc}')
for path in (ROOT/'backend/apps').rglob('*.py'):
    if '/migrations/' in path.as_posix():
        continue
    text=read(path)
    for forbidden in ['Branch.objects.first()', 'Business.objects.first()', 'request.user.branch or']:
        if forbidden in text:
            fail(f'Unsafe tenant fallback {forbidden} in {path.relative_to(ROOT)}')
accounts_models=read(ROOT/'backend/apps/accounts/models.py')
for required in ['business=models.ForeignKey','user_tenant_scope_required','OPERATIONAL_ROLES']:
    if required not in accounts_models:
        fail(f'Tenant user invariant missing: {required}')
purchase_service=read(ROOT/'backend/apps/purchasing/services.py')
for required in ['_validate_purchase_scope','supplier.branch_id!=branch.id','item.branch_id!=branch.id','select_for_update']:
    if required not in purchase_service:
        fail(f'Purchasing tenant/locking invariant missing: {required}')
for path in [ROOT/'scripts/setup-local.ps1',ROOT/'scripts/build-release.ps1']:
    for line in read(path).splitlines():
        if 'makemigrations' in line and not ('--check' in line and '--dry-run' in line):
            fail(f'Runtime migration generation is forbidden: {path.relative_to(ROOT)}: {line.strip()}')


# JS/Electron static validation
for path in [ROOT/'electron/src/main.js',ROOT/'electron/src/preload.js']:
    result=subprocess.run(['node','--check',str(path)],capture_output=True,text=True)
    if result.returncode:
        fail(f'Node syntax: {path.relative_to(ROOT)}: {result.stderr.strip()}')


# Release contract files
required=[
    'backend/requirements.txt','backend/requirements-dev.txt','frontend/package.json','electron/package.json',
    'docker-compose.yml','.github/workflows/ci.yml','docs/FINAL_RELEASE.md',
    'scripts/setup-local.ps1','scripts/build-release.ps1',
]
for rel in required:
    if not (ROOT/rel).exists():
        fail(f'Missing release file: {rel}')

if errors:
    print('Cafino static release gate FAILED:\n')
    print('\n'.join(f'- {error}' for error in errors))
    sys.exit(1)

print(f'Cafino static release gate PASSED ({len(python_files)} Python files, {len(migration_files)} migration files, {len(frontend_sources)} frontend source files).')
print('Runtime authority remains CI: PostgreSQL migrations/tests + Next production build must pass in .github/workflows/ci.yml.')

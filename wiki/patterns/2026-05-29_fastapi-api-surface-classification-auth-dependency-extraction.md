---
title: FastAPI API-surface classification via openapi() + auth-dependency AST extraction
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.82
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-29
tags: api, routing, classification, validation
related_entries: []
domain: patterns
topic: classification
---

# FastAPI API-Surface Classification via openapi() + Auth-Dependency AST Extraction

## Problem

Productizing an existing FastAPI app requires knowing the true public/metered API surface — the endpoints that are genuinely callable by external API-key holders, with accurate request/response schemas and metering-eligible operations. Naive approaches (grepping route handlers, sampling live traffic) miss:
- Shared response models that strip handler-specific fields
- Aliased router imports that drop path prefixes
- Layered auth dependencies (handler, router, include_router)
- Schema-level variations for the same route across different auth tiers (API key vs. dashboard)

This leads to incomplete coverage audits, undiscovered unmetered endpoints, and productization gaps.

## Method

### Step 1: Generate Authoritative Contract from app.openapi()

```python
# Guard app import and startup at module load time — don't let database init block
# Use SIGALRM timeout to prevent hangs

import signal
import json
from fastapi import FastAPI

def timeout_handler(signum, frame):
    raise TimeoutError("App import exceeded 5 seconds")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)

try:
    from your_app import app  # FastAPI instance
    schema = app.openapi()  # Generates real JSON Schema for all routes
    signal.alarm(0)  # Cancel alarm
except TimeoutError:
    raise RuntimeError("App import hung — check startup events, DB guards")
```

This produces the true contract: real request/response JSON schemas for every route, reflecting actual handler signatures and response models. FAR better than static AST extraction because it respects decorator composition, type narrowing, and conditional fields.

### Step 2: Build Classifier from Auth Dependencies (3-Level AST Extraction)

Extract each route's auth chain at three levels:

1. **Handler signature:** `Depends(SomeAuthDep)` in route parameters
2. **APIRouter declaration:** `APIRouter(dependencies=[...])`
3. **include_router call:** `app.include_router(router, dependencies=[...])`

Resolve Annotated-alias names (e.g., a `ServiceOrUser` type alias pointing to the actual dependency function).

```python
import ast
import inspect
from typing import get_args, get_origin

def extract_route_auth_chain(handler_func, router_config, include_router_config):
    """
    Returns tuple: (handler_deps, router_deps, include_deps)
    Each element is a list of dependency names resolved to their actual functions.
    """
    # Handler level
    sig = inspect.signature(handler_func)
    handler_deps = [
        param.annotation for param in sig.parameters.values()
        if _is_depends_param(param)
    ]
    
    # Router level (AST extraction from router definition)
    router_deps = extract_from_ast(router_config.get("router_def_node"))
    
    # include_router level (call-site dependencies)
    include_deps = router_config.get("include_router_deps", [])
    
    return handler_deps, router_deps, include_deps

def classify_endpoint_tier(route, auth_chain):
    """
    Classify endpoint as PUBLIC or DASHBOARD based on auth tier.
    PUBLIC: behind 'api_key_or_service' dependency.
    DASHBOARD: behind 'dashboard_user' dependency.
    """
    # Flatten auth chain, resolve aliases
    all_deps = set()
    for dep_list in auth_chain:
        all_deps.update(_resolve_aliases(dep_list))
    
    if "api_key_or_service" in all_deps:
        return "PUBLIC"
    elif "dashboard_user" in all_deps:
        return "DASHBOARD"
    else:
        return "UNAUTHENTICATED"  # Flag for review
```

### Step 3: Handle Three Real AST Gotchas

**Gotcha A: Aliased imports drop the prefix map**
```python
# This pattern causes routing prefix loss:
from app.api import projects as projects_api
app.include_router(projects_api.router, prefix="/api/v1")
# ^ projects_api.router is an alias; must resolve back to the module to preserve /api/v1

# Defensive: Key the prefix map by resolving the alias:
import sys
from importlib import import_module

def resolve_router_alias(alias_name, alias_obj):
    """Trace alias back to source module."""
    module = inspect.getmodule(alias_obj)
    return module.__name__
```

**Gotcha B: FastAPI path concatenation — include_router + APIRouter + route all combine**
```python
# If APIRouter(prefix="/projects") is included via app.include_router(..., prefix="/api")
# and the route itself is @router.get("/list")
# The final path is: /api/projects/list (NOT /api/list or /projects/list)

final_path = f"{include_prefix}{router_prefix}{route_path}"
```

**Gotcha C: Sub-package routers inherit the package mount prefix**
```python
# projects/__init__.py mounts sub-routers with no explicit prefix
# projects/router.py defines @router.get("/detail/{id}")
# When included as app.include_router(projects.router, prefix="/api")
# The route is /api/detail/{id}, NOT /api/projects/detail/{id}
```

### Step 4: Define "Public Endpoint" Precisely

Establish a falsifiable gate: a PUBLIC endpoint must:
- Appear in the openapi schema
- Respond with 401 if called without an API key
- Accept API key in Authorization header and succeed

Write contract tests:

```python
def test_public_endpoint_requires_auth(client, public_endpoint_routes):
    """Every PUBLIC-tier route rejects calls without API key."""
    for route in public_endpoint_routes:
        response = client.get(route.path)
        assert response.status_code == 401, \
            f"{route.path} missing auth gate"

def test_public_endpoint_accepts_api_key(client, api_key):
    """Every PUBLIC-tier route accepts a valid API key."""
    for route in public_endpoint_routes:
        response = client.get(
            route.path,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response.status_code != 401, \
            f"{route.path} rejected valid key"
```

### Step 5: Surface Findings

Coverage gates become deterministic:
- "100% of public endpoints have tests" → count PUBLIC routes in openapi schema, verify all in test coverage map
- "≥1 test per public endpoint" → cross-reference schema routes with test suite

Real findings from this method:
- Discovered only 11 of 302 routes were actually API-key-callable (most were unauthenticated internal endpoints)
- Found 2 expensive computational endpoints had no auth tier — were freely callable by anyone
- Identified unmetered routes that should have been gated before productization

## When This Applies

- Productizing an existing FastAPI application
- Creating a public API from an internal tool
- Auditing API coverage for metering/billing
- Establishing public vs. dashboard endpoint distinctions
- Writing contract tests for auth gates

## When This Does NOT Apply

- Greenfield API design (write tests first, then endpoints)
- APIs that don't use FastAPI's dependency system
- No need to productize (internal-only endpoints)
- Existing comprehensive documentation of all public routes

## Source Context

API productization pipeline for a multi-user SaaS application. Required separating genuine public surface (metered, key-authenticated) from dashboard/internal endpoints (user-authenticated, unmetered). Discovered auth-dependency extraction was the only source of truth because the codebase mixed public, dashboard, and unauthenticated routes across the same routers without consistent naming. The openapi() method + AST analysis proved essential for establishing a defensible public contract.

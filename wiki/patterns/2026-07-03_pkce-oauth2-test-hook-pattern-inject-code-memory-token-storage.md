---
title: PKCE OAuth2 test hook pattern — _inject_code + MemoryTokenStorage
source_mode: builder
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
domain: patterns
topic: validation
tags: [api, quality-gate, grounding, empirical]
created: 2026-07-03
pinned: false
related_entries: []
---

# PKCE OAuth2 Test Hook Pattern — _inject_code + MemoryTokenStorage

## The Pattern

When implementing an OAuth2 authorization code flow with PKCE in Python, the browser redirect + local callback server makes the flow impossible to test without special design. The pattern below makes the entire flow fully mocked in tests — no real Google API calls, no browser, no local TCP server needed.

### Two components required

**1. `_inject_code` parameter on the authorize() method**

Add a private keyword argument `_inject_code: str | None = None` to the authorize classmethod. When set, it bypasses both `webbrowser.open()` and `_run_oauth_callback_server()` entirely, using the injected value as the authorization code:

```python
@classmethod
async def authorize(
    cls,
    client_id: str,
    client_secret: str,
    token_path: str | Path,
    *,
    scopes: list[str] | None = None,
    token_storage: TokenStorage | None = None,
    _open_browser: bool = True,
    _inject_code: str | None = None,
) -> "GmailAdapter":
    if _inject_code is not None:
        auth_code = _inject_code
    else:
        if _open_browser:
            webbrowser.open(auth_url)
        auth_code = await _run_oauth_callback_server(port=port, expected_state=state)
    # ... token exchange, storage ...
```

**2. `MemoryTokenStorage` class**

Replace the real token storage (keyring / encrypted file) with an in-process dict. The interface is the same TokenStorage Protocol:

```python
class MemoryTokenStorage:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def load(self, token_path: Path) -> dict[str, Any]:
        return dict(self._store.get(str(token_path), {}))

    def save(self, token_path: Path, data: dict[str, Any]) -> None:
        self._store[str(token_path)] = dict(data)
```

Key properties: load() returns empty dict when nothing stored; both methods make defensive copies so caller mutations don't affect storage.

### Test structure

```python
async def test_refresh_token_saved_to_storage(self):
    storage = MemoryTokenStorage()
    with patch("mymodule.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=_mock_token_response())

        adapter = await GmailAdapter.authorize(
            client_id="client-id-123",
            client_secret="client-secret-xyz",
            token_path=TOKEN_PATH,
            token_storage=storage,
            _open_browser=False,
            _inject_code="auth-code-abc",
        )
    stored = storage.load(TOKEN_PATH)
    assert stored["refresh_token"] == "1//fake-refresh-token"
```

### What this enables

- Full PKCE code_verifier/challenge logic executes (not mocked away)
- Token exchange POST is tested with captured request data
- Error paths (missing refresh_token, HTTP 4xx) are testable
- Storage persistence and copy semantics are testable
- The asyncio callback server tests run as separate unit tests with real TCP connections to localhost

### When to use

Any authorization code flow where:
- The flow involves webbrowser.open() + a local callback server
- You want unit tests that run in CI without browser automation
- The flow is async and uses httpx or similar HTTP client

### When NOT to use

- When the entire OAuth flow is server-side (no browser redirect needed)
- When you are using an OAuth library that already provides test doubles
- For the live first-auth smoke test — that still needs a real browser and real credentials (file a separate bead for it)

## Grounding

Verified 2026-07-02 in agent-os repo, commit 9b0e65c. 17 tests across 6 test classes, all passing (pytest-asyncio, asyncio mode=AUTO, Python 3.14). The callback server tests make real asyncio.open_connection() calls to localhost and validate state mismatch, error param, and valid code paths.

## Source Context

Extracted from agent-os gmail-oauth2 implementation during session agent-os-gmail-oauth2-bd-ql8. The pattern enables full end-to-end OAuth2 flow testing without a live Google API or browser automation.

# Deployment

Living documentation for hosting topology, infrastructure decisions, and SLLM access strategy.

---

## Topology

```
app.preon.systems     →  Vercel       (user-facing frontend)
admin.preon.systems   →  Vercel       (operator / pipeline-trace frontend)
api.preon.systems     →  Fly.io       (FastAPI)
db                    →  Fly Postgres (managed, same org, private network)
sllm (Phase 6+)       →  Fly GPU      (vLLM, private network only)
```

The two frontends are separated from the API so that frontend changes don't require API redeploys, and so operator and user surfaces can have independent auth contexts and deploy cadences.

---

## API — Fly.io

**Why Fly.io:**
- Private networking (`.internal` DNS) between apps in the same org — necessary for Phase 6+ SLLM co-location without exposing the model to the public internet
- Multi-region with minimal config
- Managed Postgres as an add-on (migration path from SQLite)
- `PREON_COOKIE_DOMAIN` already wired in `web.py` — set to `preon.systems` so session cookies work across subdomains

**Required env vars on Fly:**
```
PREON_COOKIE_DOMAIN=preon.systems
SECRET_KEY=<random 32-byte hex>
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
XAI_API_KEY=...
GEMINI_API_KEY=...
```

> **Key security rule:** LLM provider keys live only on Fly. Vercel env vars are encrypted at rest but visible to anyone with project access — do not put `ANTHROPIC_API_KEY` or any other runtime secret in Vercel. Vercel only receives public base URLs (see Frontends section).

**Deploy command:**
```bash
fly deploy
```

---

## Frontends — Vercel

Both frontends deploy to Vercel. Zero-config for Vite/Next.js, CDN automatic, preview deployments per PR for free.

| Surface | Domain | Repo path (TBD) |
|---|---|---|
| User app | `app.preon.systems` | `apps/web` |
| Operator dashboard | `admin.preon.systems` | `apps/admin` |

**Vercel env vars (public only):**
```
VITE_API_BASE_URL=https://api.preon.systems
```

No LLM keys. No secrets. Only the API base URL.

---

## Session Cookies Across Subdomains

The frontends (`app.`, `admin.`) and the API (`api.`) are different subdomains. For session cookies to work across them:

- `Domain` must be set explicitly to `preon.systems` — if omitted, the cookie is host-only and won't cover other subdomains
- Modern cookie specs ignore the leading dot, so `Domain=preon.systems` and `Domain=.preon.systems` behave identically — either works, but be consistent
- `Secure` is required for cross-subdomain cookies in modern browsers
- `SameSite=Lax` is sufficient when the frontend and API share a parent domain; use `SameSite=None` only if they are on entirely different domains

In `web.py`, when setting the session cookie:
```python
response.set_cookie(
    "preon_session", token,
    domain="preon.systems",   # explicit domain = covers all subdomains
    secure=True,
    httponly=True,
    samesite="lax",
)
```

`PREON_COOKIE_DOMAIN=preon.systems` on Fly controls this. The test suite bug where `PREON_COOKIE_DOMAIN=localhost` caused cookies to be dropped by httpx is the same class of problem.

---

## CORS

The API must explicitly allow credentialed requests from both frontend origins. Add to `web.py` CORS configuration:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.preon.systems",
        "https://admin.preon.systems",
    ],
    allow_credentials=True,   # required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Frontends must send requests with credentials included:
```typescript
// fetch
fetch("https://api.preon.systems/api/...", { credentials: "include" })

// axios
axios.defaults.withCredentials = true
```

`allow_credentials=True` and a wildcard `allow_origins=["*"]` cannot be combined — origins must be listed explicitly.

---

## Database — Fly Postgres

Fly Postgres runs in the same private network as the API app. The connection string is injected automatically as `DATABASE_URL`.

**Required before production:**
- Automated daily backups enabled (`fly postgres backup`)
- Migration command documented and tested (`alembic upgrade head` or equivalent)
- Restore drill completed — verify a backup can be restored to a staging database
- Connection pooling strategy decided: PgBouncer sidecar or SQLAlchemy pool size tuned to Fly machine count

---

## SLLM Strategy

**SLLM** in the architecture docs means "Small Language Model" — cheaper, faster, lower reasoning depth. This does **not** mean self-hosted by default.

### Now (Phase 1–5): Cloud SLLM via existing registry

The `fast` model class in `MODEL_REGISTRY` already covers SLLM use cases:

| Provider | SLLM model | Speed | Cost |
|---|---|---|---|
| Anthropic | claude-haiku-4-5 | fast / cloud-hosted | low |
| OpenAI | gpt-4o-mini | fast / cloud-hosted | low |
| Grok | grok-3-mini-fast | fast / cloud-hosted | low |
| Gemini | gemini-2.0-flash | fast / cloud-hosted | low |

Exact latency and cost values are registry estimates only — replace with real telemetry from Phase 12.

The `CellModelRouter` routes to these automatically when `cost_tier="cheap"` or `latency_budget_ms <= 1000`. No infra change needed — just API keys on Fly.

### Phase 6+: True local SLLM on Fly GPU

When cost or data sensitivity justifies running a local model:

1. Deploy a vLLM instance as a separate Fly app in the same org:
   ```bash
   fly launch --name preon-sllm --image vllm/vllm-openai:latest
   ```

2. vLLM speaks OpenAI-compatible REST. Add one registry entry:
   ```python
   ProviderModelProfile(
       provider="local",
       model_class="fast",
       model_id="llama-3.1-8b-instruct",
       max_context_tokens=128_000,
       average_latency_ms=0,          # telemetry TBD — fill after benchmarking
       relative_cost=0.0,
       allowed_data_classes=["public", "internal", "confidential", "restricted"],
       supports_json_schema=True,
       supports_tools=True,
       supports_vision=False,
       supports_streaming=True,
       strengths=["cost", "data_sovereignty", "latency"],
       weaknesses=["reasoning_depth"],
   )
   ```

3. Add one env var to the API app:
   ```
   LOCAL_SLLM_BASE_URL=http://preon-sllm.internal:8000
   ```
   The `.internal` hostname is Fly's private DNS — unreachable from the public internet.

4. Add one env key mapping in `cell_router.py`:
   ```python
   _ENV_KEYS = {
       ...
       "local": "LOCAL_SLLM_BASE_URL",
   }
   ```
   And update `_key_present` to check the URL rather than an API key.

**Governance note on restricted data:** `data_class="restricted"` currently only matches `openai/o3`. Registering a local provider with `allowed_data_classes=["restricted"]` makes restricted workloads *eligible* for local routing — but eligibility is not automatic approval. The organism's routing policy and any operator-level `allowed_providers` constraints must also permit it. Confirm the full policy chain before routing restricted data to any new provider.

---

## Routing from API to Providers

```
user browser
     │
     ▼
Vercel (frontend)  ──→  api.preon.systems (Fly)
                              │
                    ┌─────────┼──────────────┐
                    │         │              │
                    ▼         ▼              ▼
              Anthropic    OpenAI        Grok / Gemini
              (HTTPS)      (HTTPS)       (HTTPS)
                    │
              [Phase 6+]
                    │
                    ▼
             preon-sllm.internal (Fly private network)
             vLLM / llama-3.1-8b
```

All outbound LLM calls originate from the Fly API app. The frontends never call LLM providers directly.

---

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-21 | Fly.io for API | Private networking needed for future local SLLM co-location |
| 2026-06-21 | Vercel for both frontends | Independent deploys, CDN, PR previews |
| 2026-06-21 | LLM keys on Fly only | Vercel project access exposes env vars to all project members |
| 2026-06-21 | Cloud SLLM first (fast model class) | Already in registry, no infra, sufficient for Phase 1–5 |
| 2026-06-21 | vLLM for Phase 6+ local SLLM | OpenAI-compatible REST slots into existing adapter pattern |
| 2026-06-21 | `Domain=preon.systems` cookie | Explicit domain required for cross-subdomain session sharing |
| 2026-06-21 | CORS allow_credentials with explicit origins | Wildcard origin incompatible with credentialed requests |

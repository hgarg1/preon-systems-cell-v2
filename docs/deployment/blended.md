# Deployment — Blended Cloud Patterns

Cross-provider combinations that are better than picking one cloud for everything.

**Core principle: blend at the stateless edges. Do not blend the stateful/private core unless there is a very specific reason.**

Frontends are stateless and CDN-delivered — they can live anywhere. The API, database, and future SLLM must share a private network, so they should always be on the same cloud. Splitting those three across providers adds latency, destroys the security boundary, and makes private SLLM routing impossible.

---

## Why blended at all

The three big clouds optimise for different things. Some components of this stack have a clear "best home" that doesn't change depending on where the API lives:

| Component | Best home | Why |
|---|---|---|
| Frontends | Vercel or Cloudflare Pages | PR previews, CDN, fastest DX — stateless, lives anywhere |
| API | Cloud Run / Fly / Container Apps | Serverless container, depends on team familiarity |
| Database | Same cloud as API | Latency + private network; never split from the API |
| SLLM (Phase 6+, public/internal data) | Modal / RunPod | Cheaper than cloud GPU on-demand |
| SLLM (Phase 6+, restricted data) | Same cloud as API | Must stay inside the private network |

The canonical pattern: **Vercel (or Cloudflare Pages) for frontends + one cloud for API + DB + SLLM.**

---

## Pattern 1: Vercel Frontends + One Cloud for Everything Else (Canonical default)

```
app.preon.systems     →  Vercel
admin.preon.systems   →  Vercel
api.preon.systems     →  Fly / AWS ECS / Cloud Run / Container Apps  ┐
db                    →  Same cloud as API (private network)          ├─ never split
sllm (Phase 6+)       →  Same cloud as API (private network)          ┘
```

This is the architecture all four cloud-specific docs implement. API, DB, and private SLLM stay together to preserve latency, security boundary, and network simplicity. Only the frontend crosses the cloud boundary, because it is stateless and has no network dependencies on the private core.

Vercel wins for frontend regardless because:

- **PR preview deployments** are automatic and free. Each PR gets its own `preon-pr-123.vercel.app` URL pointing at the staging API. No equivalent on S3+CloudFront, Azure Static Web Apps, or Firebase Hosting without significant CI setup.
- **Next.js SSR and edge functions** are first-class on Vercel (they built Next.js). Image optimisation, ISR, and middleware work without configuration.
- **Zero-config Vite** — push a Vite repo, it deploys. No CloudFront distribution to configure.
- **API proxy** — Vercel's `rewrites` can proxy `/api/*` to `https://api.preon.systems/api/*`, eliminating CORS entirely if you prefer that over cross-origin requests with credentials.

**Downsides:** Vercel project members can view env vars. Keep Vercel env to public API base URLs only — all secrets stay in the API cloud.

---

## Pattern 2: Cloudflare Pages as a Vercel Alternative

```
app.preon.systems     →  Cloudflare Pages
admin.preon.systems   →  Cloudflare Pages
api.preon.systems     →  Fly / AWS ECS / Cloud Run / Container Apps
```

Cloudflare Pages is the right Vercel alternative when:
- You want WAF and DDoS protection at the CDN layer (Cloudflare has the largest DDoS mitigation network)
- You want Cloudflare Workers at the edge for lightweight API routes (auth token exchange, rate limiting)
- You already manage DNS on Cloudflare (common)

**Tradeoffs vs Vercel:**

| | Vercel | Cloudflare Pages |
|---|---|---|
| Next.js SSR | Native | Partial (Next.js on Workers is improving) |
| PR previews | Automatic | Automatic |
| Edge functions | Vercel Edge Runtime | Workers (V8 isolates, faster cold start) |
| WAF / DDoS | Requires add-on | Built-in |
| Price | Free tier → usage-based | Very generous free tier |
| DNS management | External DNS points to Vercel | Best when DNS is already on Cloudflare |

**Cloudflare-specific setup:**
- `VITE_API_BASE_URL=https://api.preon.systems` in Pages env
- No LLM keys in Cloudflare env
- If using Cloudflare as DNS for `preon.systems`: proxied A/CNAME records give WAF + DDoS automatically, even for `api.preon.systems` pointing at Fly/AWS/GCP

---

## Pattern 3: Neon (Serverless Postgres) as Database

```
api.preon.systems     →  Fly / Cloud Run / ECS
db                    →  Neon (neon.tech)
```

Neon is a serverless Postgres provider with one feature no managed cloud database has: **database branching**. Each branch is a full copy-on-write fork of the database — instant, storage-efficient.

**Why this matters for this project:**
- Each PR can get its own Neon branch: `preon-pr-123` branch = isolated database with production-like data
- Migrations can be tested against a branch before merging, then discarded
- Staging and production are separate branches of the same project, not separate database instances to manage
- Neon's serverless driver works with SQLAlchemy, so no application code changes

> **PII warning:** Do not use production data in PR branches unless PII is masked first or you use schema-only branching. A branch created from production is a full copy-on-write fork — all rows are accessible. Use Neon's schema-only branch option for dev/CI when the database contains user data.

**Tradeoffs:**
- Neon is not co-located inside your cloud's private network — the API connects over TLS to `neon.tech`. Fine for most workloads; adds ~5ms per query vs a co-located RDS/Cloud SQL instance.
- Not appropriate if your compliance requirements mandate the database stays within a private VPC.
- Cold start on a Neon branch (~500ms) if the compute has been idle — use `pgbouncer` connection pooling via Neon's built-in pooler to keep connections warm.

**Setup:** replace `DATABASE_URL` with a Neon connection string. Everything else stays the same.

---

## Pattern 4: Specialised GPU Cloud for SLLM (Phase 6+)

```
api.preon.systems     →  Fly / AWS / GCP / Azure
sllm                  →  Modal.com / RunPod / Lambda Labs
```

AWS, Azure, and GCP GPU on-demand is expensive. Purpose-built GPU clouds are significantly cheaper for inference workloads:

| Provider | Best for | Notes |
|---|---|---|
| **Modal.com** | Serverless GPU inference, auto-scale to zero | Python-native, fastest iteration; cold start is workload/model dependent — benchmark before committing |
| **RunPod** | Persistent GPU pods, spot pricing | Cheapest per-GPU-hour, manual scaling |
| **Lambda Labs** | Reserved GPU instances, on-demand | Good A100/H100 availability, predictable cost |

**How it connects to the API:**

These providers give you an HTTPS endpoint (not a private IP). The API calls it over the public internet, but the endpoint is protected by a token:

```
LOCAL_SLLM_BASE_URL=https://your-modal-endpoint.modal.run
LOCAL_SLLM_API_KEY=modal-secret-token
```

Update `_key_present` in `cell_router.py` to check `LOCAL_SLLM_API_KEY` instead of a URL. Update the adapter to pass the token as a Bearer header.

**This removes the "private network" property** that makes the Fly/AWS/GCP co-location story clean for restricted data. If `data_class="restricted"` must never leave a private network, a public HTTPS endpoint to Modal/RunPod does not satisfy that requirement. Use it for `public` and `internal` data class only until a network isolation layer is added.

**Modal.com** is the recommended starting point because:
- Deploy a vLLM endpoint with one Python file (no Docker, no Kubernetes)
- Scale to zero when idle; scale to N GPUs under load
- OpenAI-compatible REST endpoint out of the box

The sketch below is illustrative only — it initialises the model inside the request handler, which reloads the model weights on every call. Real deployments must initialise the model once in the container lifecycle (Modal's `@app.cls` pattern with `@modal.enter`):

```python
# modal_sllm.py — illustrative structure only, not production-ready
# See Modal docs for @app.cls + @modal.enter for correct model lifecycle
import modal

app = modal.App("preon-sllm")
image = modal.Image.debian_slim().pip_install("vllm")

@app.function(gpu="A10G", image=image)
@modal.web_endpoint(method="POST")
def complete(request: dict):
    from vllm import LLM, SamplingParams
    llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")  # wrong: reloads per request
    outputs = llm.generate([request["prompt"]], SamplingParams(max_tokens=request.get("max_tokens", 512)))
    return {"content": outputs[0].outputs[0].text}
```

---

## Recommendation for Preon

```
Phase 1–5          Vercel + Fly.io (or Cloud Run) + managed Postgres
Phase 6 SLLM       public/internal data → Modal.com
                   restricted data     → GPU co-located in same VPC as API
Dev/staging DB     Neon only if PII policy is clear (schema-only branches for user data)
```

---

## Choosing a Pattern

| Situation | Recommended pattern |
|---|---|
| Getting started, want simplest setup | Fly.io (`deployment.md`) + Vercel |
| Team is AWS-native | ECS Fargate + RDS + Vercel |
| Compliance / Azure AD integration | Azure Container Apps + Key Vault + Vercel |
| GCP-native team, serverless preference | Cloud Run + Cloud SQL + Vercel |
| Want WAF/DDoS on frontends | Any cloud API + Cloudflare Pages |
| Active development with many PRs | Any cloud API + Vercel (PR previews) |
| Cost-sensitive SLLM, public/internal data only | Any cloud API + Modal.com |
| Restricted data, SLLM must stay private | API + SLLM co-located in same cloud VPC |
| Dev/staging DB isolation per PR, no PII | Any cloud API + Neon (schema-only branches) |

# Deployment — GCP

GCP variant of the reference topology in `docs/deployment.md`.

GCP is the cleanest big-cloud option for Phase 1–5: Cloud Run + Cloud SQL is lighter to operate than ECS/RDS or Azure Container Apps/PostgreSQL, and the Secret Manager IAM integration is straightforward.

---

## Topology

```
app.preon.systems     →  Vercel (or Firebase Hosting)    user-facing frontend
admin.preon.systems   →  Vercel (or Firebase Hosting)    operator frontend
api.preon.systems     →  Cloud Run                       FastAPI
db                    →  Cloud SQL (PostgreSQL)           private IP, same VPC
secrets               →  Secret Manager                   IAM-controlled, audit-logged
sllm (Phase 6+)       →  Compute Engine GPU (T4 / A100)  same VPC, private
```

### Why Cloud Run

Fully serverless, auto-scales to zero, cold starts under one second for this app size. Direct VPC Egress (preferred) or a Serverless VPC Access connector gives it private connectivity to Cloud SQL and the future SLLM instance without any cluster to manage.

---

## Networking

```
VPC (10.0.0.0/16)
├── Cloud Run (Direct VPC Egress)     — Cloud Run → VPC private resources
├── Cloud SQL subnet                  — PostgreSQL private IP
└── GPU VM subnet (Phase 6+)         — Compute Engine instance running vLLM
```

**Egress routing — important distinction:**

Cloud Run has two egress modes:

| Flag | What goes through VPC | External LLM API calls |
|---|---|---|
| `--vpc-egress private-ranges-only` | RFC-1918 traffic only | Direct Cloud Run internet egress (no Cloud NAT involved) |
| `--vpc-egress all-traffic` | All outbound traffic | Through VPC → Cloud NAT required for internet access |

For this project, `private-ranges-only` is correct: Cloud SQL and SLLM are private IPs that route through the VPC connection; Anthropic/OpenAI/Grok/Gemini API calls go out via Cloud Run's built-in internet egress without touching Cloud NAT. Only add Cloud NAT if you switch to `all-traffic` and need outbound internet from inside the VPC.

---

## VPC Connection — Direct VPC Egress (preferred) or Connector

### Direct VPC Egress (recommended)

Google now recommends Direct VPC Egress over Serverless VPC Access connectors. No connector VM to provision, no connector compute charges, lower latency.

```bash
gcloud run deploy preon-api \
  --image us-docker.pkg.dev/preon-prod/preon/preon-api:latest \
  --region us-central1 \
  --network preon-vpc \
  --subnet preon-subnet \
  --vpc-egress private-ranges-only
```

Direct VPC Egress is GA as of Cloud Run on 2nd gen execution environment. Verify the service uses `--execution-environment gen2`.

### Serverless VPC Access connector (fallback)

If Direct VPC Egress is unavailable in your region or you're on 1st gen:

```bash
# Create the connector once
gcloud compute networks vpc-access connectors create preon-connector \
  --region us-central1 \
  --subnet preon-connector-subnet \
  --min-instances 2 --max-instances 10

# Reference it in the deploy command
gcloud run deploy preon-api \
  --vpc-connector preon-connector \
  --vpc-egress private-ranges-only
```

---

## API — Cloud Run

Build the Docker image and push to Artifact Registry. Deploy a Cloud Run service referencing the image.

Secret Manager secrets are referenced in the Cloud Run service config. At runtime, GCP resolves them and injects them as env vars into the container — the values are not stored in source control or plain config, but they do appear to the container process as env vars (same as any cloud's approach). The service account needs `roles/secretmanager.secretAccessor` on each secret.

**Secrets in Secret Manager:**
```
projects/preon-prod/secrets/SECRET_KEY
projects/preon-prod/secrets/ANTHROPIC_API_KEY
projects/preon-prod/secrets/OPENAI_API_KEY
projects/preon-prod/secrets/XAI_API_KEY
projects/preon-prod/secrets/GEMINI_API_KEY
projects/preon-prod/secrets/DATABASE_URL
```

**Cloud Run service config (key excerpt):**
```yaml
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: ANTHROPIC_API_KEY
        key: latest
  - name: PREON_COOKIE_DOMAIN
    value: preon.systems
```

---

## Frontends — Vercel (recommended) or Firebase Hosting

Vercel is recommended regardless of where the API lives. See `blended.md` for rationale.

If staying within GCP, Firebase Hosting has a good CDN and works for SPAs. It does not match Vercel's PR preview workflow.

**Vercel env vars (public only):**
```
VITE_API_BASE_URL=https://api.preon.systems
```

No LLM keys. No secrets. LLM keys live in Secret Manager, fetched via IAM-controlled service account at deploy time.

---

## Database — Cloud SQL for PostgreSQL

Create the instance with **private IP only** (no public IP). Connect from Cloud Run via:

- **Cloud SQL Auth Proxy** (sidecar) — handles IAM authentication and TLS to Cloud SQL. Does **not** provide connection pooling; that is the application's responsibility.
- **Direct private IP** via VPC connection — simpler if you are already using Direct VPC Egress; connect with standard `psycopg2` to the private IP.

**Connection pooling options (choose one):**
- SQLAlchemy `pool_size` + `max_overflow` tuned to Cloud Run max instance count (simplest)
- PgBouncer sidecar container in the Cloud Run service (transaction-mode pooling, more efficient at high concurrency)
- Cloud SQL language connector with app-side pooling (Google's recommended Python path)

**Required before production:**
- Automated backups enabled (daily, ≥7-day retention)
- Point-in-time recovery enabled
- Migration command tested against a staging clone: `alembic upgrade head`
- Restore drill: clone production instance via backup, run smoke tests against the clone
- `max_connections` database flag tuned to expected Cloud Run instance count × pool size

---

## Session Cookies and CORS

Same rules as the Fly.io reference:
- `Domain=preon.systems` (explicit, no leading dot required)
- `Secure=True`, `HttpOnly=True`, `SameSite=Lax`
- CORS: `allow_origins=["https://app.preon.systems", "https://admin.preon.systems"]`, `allow_credentials=True`

No GCP-specific changes to the application code.

---

## SLLM — Phase 6+ (Compute Engine GPU in VPC)

1. Create a Compute Engine instance with a T4 or A100 GPU in the **GPU subnet**, no external IP:
   ```bash
   gcloud compute instances create preon-sllm \
     --machine-type a2-highgpu-1g \
     --accelerator type=nvidia-tesla-a100,count=1 \
     --image-family debian-11-gpu \
     --no-address \
     --subnet gpu-subnet
   ```

2. Run vLLM on the instance:
   ```bash
   docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest \
     --model meta-llama/Llama-3.1-8B-Instruct
   ```

3. Create an internal DNS record so the address is stable across instance restarts:
   - In the VPC's private DNS zone, add an A record: `sllm.preon.internal → <instance private IP>`
   - Cloud Run resolves this through the VPC connection

4. Firewall rule: allow ingress on TCP 8000 from the Cloud Run subnet (or connector IP range) to the GPU subnet only — no public exposure.

5. Add to Secret Manager and reference from the Cloud Run service:
   ```
   LOCAL_SLLM_BASE_URL=http://sllm.preon.internal:8000
   ```

**Alternative — Vertex AI custom prediction endpoint:** Vertex AI can host a vLLM container with managed GPU auto-scaling, a private VPC Service Control perimeter, and built-in model monitoring. More complex to configure than a raw Compute Engine VM but removes instance management. Evaluate at Phase 6 when scale justifies it.

**Governance note:** Registering the local provider makes restricted workloads *eligible* for local routing. The organism routing policy and any operator `allowed_providers` constraints must also permit it before restricted data actually flows there.

---

## Key Differences from Fly.io Reference

| Concern | Fly.io | GCP |
|---|---|---|
| Private networking | `.internal` DNS automagic | VPC + Direct VPC Egress (or connector) |
| Secrets | Fly env vars (encrypted) | Secret Manager + IAM service account; values injected as env vars at runtime |
| Outbound to LLM APIs | Built-in | Cloud Run internet egress (with `private-ranges-only`); no Cloud NAT needed |
| SLLM private access | Fly private network | Same VPC, internal DNS, firewall rules |
| Connection pooling | N/A | Auth Proxy does not pool — handle in app or with PgBouncer |
| Operational overhead | Low | Low (Cloud Run + Cloud SQL is the lightest big-cloud setup) |
| GPU availability | Limited | T4 / A100 available; preemptible GPU VMs reduce cost |

---

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-21 | Cloud Run over GKE | No cluster management; scale-to-zero; cold start acceptable |
| 2026-06-21 | Direct VPC Egress over VPC connector | No connector compute charges; Google's current recommendation |
| 2026-06-21 | `--vpc-egress private-ranges-only` | External LLM API calls use Cloud Run internet egress; no Cloud NAT needed |
| 2026-06-21 | Secret Manager + IAM service account | Audit-logged, IAM-scoped; values not in source control |
| 2026-06-21 | Cloud SQL private IP; Auth Proxy for IAM/TLS | Private-only access; pooling handled at app layer not proxy layer |
| 2026-06-21 | Internal DNS for SLLM (`sllm.preon.internal`) | Stable address across instance restarts; no raw IP in config |
| 2026-06-21 | Vercel for frontends | Better than Firebase Hosting for Next.js/Vite; see blended.md |
| 2026-06-21 | Compute Engine GPU for Phase 6+ SLLM | Same VPC, no public IP, firewall-isolated |

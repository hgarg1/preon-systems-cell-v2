# Deployment — Azure

Azure variant of the reference topology in `docs/deployment.md`.

---

## Topology

```
app.preon.systems     →  Vercel (or Azure Static Web Apps)   user-facing frontend
admin.preon.systems   →  Vercel (or Azure Static Web Apps)   operator frontend
api.preon.systems     →  Azure Container Apps                FastAPI
db                    →  Azure Database for PostgreSQL        VNet-injected, private
secrets               →  Azure Key Vault + Managed Identity   no secret values in env
sllm (Phase 6+)       →  Azure NC/ND VM (GPU)                same VNet, private
```

### Why Azure Container Apps

Container Apps is the right fit: serverless containers, scale-to-zero, VNet integration, and no Kubernetes to manage. App Service works but is heavier. AKS is overkill at this stage.

---

## Networking

```
VNet (10.0.0.0/16)
├── Container Apps subnet      — Container Apps Environment
├── PostgreSQL subnet          — Flexible Server (VNet injection)
├── GPU VM subnet (Phase 6+)  — NC/ND series VM running vLLM
└── Private DNS zones          — postgres.private.postgres.database.azure.com
                                 keyvault.preon.private
```

Container Apps with VNet integration routes outbound traffic (LLM provider API calls) through the VNet and out via NAT Gateway or a public IP on the subnet. Inbound traffic comes via a Container Apps ingress (managed HTTPS endpoint).

---

## API — Azure Container Apps

Push the Docker image to Azure Container Registry (ACR). Create a Container Apps Environment with VNet integration, then deploy the Container App pointing at the ACR image.

**Managed Identity** is the preferred way to handle secrets — the Container App gets a system-assigned identity that has Key Vault Secrets Officer (read) permission. No secret values ever appear in env vars.

Key Vault secret references in the Container App definition:
```json
{
  "secrets": [
    {
      "name": "anthropic-api-key",
      "keyVaultUrl": "https://preon-kv.vault.azure.net/secrets/ANTHROPIC-API-KEY",
      "identity": "system"
    }
  ],
  "env": [
    { "name": "ANTHROPIC_API_KEY", "secretRef": "anthropic-api-key" }
  ]
}
```

Repeat for `OPENAI_API_KEY`, `XAI_API_KEY`, `GEMINI_API_KEY`, `SECRET_KEY`, `DATABASE_URL`.

**Non-secret env vars** (set directly):
```
PREON_COOKIE_DOMAIN=preon.systems
```

---

## Frontends — Vercel (recommended) or Azure Static Web Apps

Vercel is recommended regardless of where the API lives. See `blended.md` for rationale.

If staying within Azure, Azure Static Web Apps has decent Next.js support and GitHub Actions integration built in. It is not as seamless as Vercel for PR previews.

**Vercel env vars (public only):**
```
VITE_API_BASE_URL=https://api.preon.systems
```

No LLM keys. No secrets. LLM keys live in Key Vault, fetched via Managed Identity at runtime.

---

## Database — Azure Database for PostgreSQL Flexible Server

Deploy with VNet injection (not a public endpoint). The Flexible Server lands in its own delegated subnet inside the VNet, with a private DNS zone for name resolution.

**Required before production:**
- Geo-redundant backups enabled (retention ≥ 7 days)
- High Availability mode (zone-redundant standby)
- Migration command tested against a staging restore: `alembic upgrade head`
- Restore drill: restore to a new Flexible Server instance from backup and run smoke tests
- Connection pooling: PgBouncer sidecar in the Container Apps Environment, or SQLAlchemy pool size matched to Container App replica count

---

## Session Cookies and CORS

Same rules as the Fly.io reference:
- `Domain=preon.systems` (explicit, no leading dot required)
- `Secure=True`, `HttpOnly=True`, `SameSite=Lax`
- CORS: `allow_origins=["https://app.preon.systems", "https://admin.preon.systems"]`, `allow_credentials=True`

No Azure-specific changes to the application code.

---

## SLLM — Phase 6+ (Azure GPU VM in VNet)

1. Deploy an Azure NC A100 v4 or ND A100 v4 VM in the **GPU subnet** within the same VNet.
2. Run vLLM:
   ```bash
   docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest \
     --model meta-llama/Llama-3.1-8B-Instruct
   ```
3. Container Apps reaches the VM via private IP within the VNet. No public IP on the VM.
4. NSG (Network Security Group) on the GPU subnet allows inbound port 8000 from the Container Apps subnet only.
5. Private DNS zone entry: `sllm.preon.internal → 10.0.3.10`
6. Add to Key Vault and reference from Container App:
   ```
   LOCAL_SLLM_BASE_URL=http://sllm.preon.internal:8000
   ```

**Alternative — Azure ML Online Endpoint:** Azure ML can serve a vLLM-backed endpoint with auto-scaling GPU, managed networking, and a built-in private endpoint. More complex to set up but removes VM management. Worth considering at Phase 6 if the team grows.

**Governance note:** Registering the local provider makes restricted workloads *eligible* for local routing. The organism routing policy and any operator `allowed_providers` constraints must also permit it before restricted data actually flows there.

---

## Key Differences from Fly.io Reference

| Concern | Fly.io | Azure |
|---|---|---|
| Private networking | `.internal` DNS automagic | VNet + NSG + Private DNS zones |
| Secrets | Fly env vars (encrypted) | Key Vault + Managed Identity (no secret values in env) |
| Outbound to LLM APIs | Built-in | Via VNet NAT or Container Apps managed egress |
| SLLM private access | Fly private network | Same VNet, NSG rules |
| Operational overhead | Low | Medium |
| GPU availability | Limited | NC A100 / ND H100 series available by region |
| Compliance | Standard | Azure has HIPAA/SOC2/ISO27001 BAAs — relevant for restricted data workloads |

---

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-21 | Azure Container Apps over App Service | Serverless scale-to-zero, VNet integration, no VM management |
| 2026-06-21 | Key Vault + Managed Identity | No secret values in env vars at any layer — strongest secrets posture of the three clouds |
| 2026-06-21 | PostgreSQL Flexible Server with VNet injection | Private-only endpoint, no public IP on database |
| 2026-06-21 | Vercel for frontends | Better than Azure Static Web Apps for Next.js/Vite; see blended.md |
| 2026-06-21 | Azure NC/ND VM for Phase 6+ SLLM | Same VNet as Container Apps, no public exposure |

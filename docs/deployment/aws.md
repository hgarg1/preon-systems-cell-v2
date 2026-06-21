# Deployment — AWS

AWS variant of the reference topology in `docs/deployment.md`.

---

## Topology

```
app.preon.systems     →  Vercel (or S3 + CloudFront)   user-facing frontend
admin.preon.systems   →  Vercel (or S3 + CloudFront)   operator frontend
api.preon.systems     →  ECS Fargate + ALB              FastAPI
db                    →  RDS PostgreSQL                 private subnet, same VPC
secrets               →  AWS Secrets Manager            API keys, never in env
sllm (Phase 6+)       →  EC2 G5 / P4 (GPU)             private subnet, same VPC
```

### Why ECS Fargate over App Runner

App Runner is simpler but its VPC egress is via an outbound connector — fine for RDS, but routing to a private GPU EC2 instance is awkward. ECS Fargate is native to the VPC from the start, which keeps the SLLM private network story clean when Phase 6 arrives.

---

## Networking

```
VPC (10.0.0.0/16)
├── Public subnets     — ALB only
├── Private subnets    — ECS tasks, RDS, EC2-SLLM
└── NAT Gateway        — ECS tasks → external LLM APIs (Anthropic, OpenAI, etc.)
```

Security group rules:
- ALB → ECS: port 8000
- ECS → RDS: port 5432
- ECS → EC2-SLLM (Phase 6+): port 8000
- ECS → internet: via NAT Gateway (all HTTPS outbound for provider API calls)

Without NAT Gateway, ECS tasks in private subnets cannot reach external LLM provider APIs.

---

## API — ECS Fargate

Containerise the FastAPI app (`Dockerfile` at repo root) and push to ECR. Define a Fargate task and service behind an ALB. The ALB handles TLS termination; Fargate tasks run in private subnets.

**Task role** (IAM) needs:
- `secretsmanager:GetSecretValue` for all preon secrets
- Nothing else — least privilege

**Required secrets in Secrets Manager** (injected as env vars in the task definition):
```
/preon/prod/SECRET_KEY
/preon/prod/ANTHROPIC_API_KEY
/preon/prod/OPENAI_API_KEY
/preon/prod/XAI_API_KEY
/preon/prod/GEMINI_API_KEY
/preon/prod/DATABASE_URL
```

**Non-secret env vars** (set directly in task definition):
```
PREON_COOKIE_DOMAIN=preon.systems
```

**Note:** Secrets Manager costs $0.40/secret/month. Alternatively, SSM Parameter Store SecureString is free for standard parameters.

---

## Frontends — Vercel (recommended) or S3 + CloudFront

Vercel is the recommended option regardless of where the API lives — PR previews, zero-config Next.js, and CDN are all better than S3 + CloudFront for this stack. See `blended.md` for rationale.

If you must stay within AWS:
- S3 bucket (static assets, no public website hosting needed)
- CloudFront distribution pointing at S3
- Route 53 for `app.preon.systems` → CloudFront

**Vercel env vars (public only):**
```
VITE_API_BASE_URL=https://api.preon.systems
```

No LLM keys. No secrets. LLM keys live in Secrets Manager on the API side only.

---

## Database — RDS PostgreSQL

Deploy in a private subnet with no public IP. Use a DB subnet group spanning multiple AZs.

**Required before production:**
- Multi-AZ enabled (automatic failover)
- Automated backups with ≥7-day retention
- Parameter group with `log_connections=on` and `log_disconnections=on`
- Migration command tested against a staging snapshot: `alembic upgrade head`
- Restore drill: restore latest backup to a separate RDS instance and run smoke tests
- Connection pooling: set `max_connections` in the parameter group, use RDS Proxy or SQLAlchemy pool size tuned to Fargate task count

---

## Session Cookies and CORS

Same rules as the Fly.io reference:
- `Domain=preon.systems` (explicit, no leading dot required)
- `Secure=True`, `HttpOnly=True`, `SameSite=Lax`
- CORS: `allow_origins=["https://app.preon.systems", "https://admin.preon.systems"]`, `allow_credentials=True`

No AWS-specific changes to the application code.

---

## SLLM — Phase 6+ (EC2 GPU in VPC)

1. Launch an EC2 G5 (A10G) or P4d (A100) instance in the **same private subnet** as the ECS tasks.
2. Run vLLM on the instance:
   ```bash
   docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest \
     --model meta-llama/Llama-3.1-8B-Instruct
   ```
3. ECS tasks reach it via private IP (e.g., `http://10.0.1.45:8000`) or a private Route 53 DNS name.
4. Security group on the EC2 instance allows inbound port 8000 from the ECS task security group only — no public exposure.
5. Add to `model_routing/registry.py`:
   ```python
   ProviderModelProfile(
       provider="local",
       model_class="fast",
       model_id="llama-3.1-8b-instruct",
       average_latency_ms=0,   # telemetry TBD — fill after benchmarking
       relative_cost=0.0,
       allowed_data_classes=["public", "internal", "confidential", "restricted"],
       ...
   )
   ```
6. Add to Secrets Manager (or task definition env):
   ```
   LOCAL_SLLM_BASE_URL=http://10.0.1.45:8000
   ```

**Governance note:** Registering the local provider makes restricted workloads *eligible* for local routing. The organism routing policy and any operator `allowed_providers` constraints must also permit it before restricted data actually flows there.

---

## Key Differences from Fly.io Reference

| Concern | Fly.io | AWS |
|---|---|---|
| Private networking | `.internal` DNS automagic | VPC + Security Groups (explicit) |
| Secrets | Fly env vars (encrypted) | Secrets Manager (IAM-controlled, audited) |
| Outbound to LLM APIs | Built-in | NAT Gateway required (and costs ~$32/month) |
| SLLM private access | Fly private network | Same VPC, Security Group rules |
| Operational overhead | Low | Medium–High |
| GPU availability | Limited | G5 / P4d widely available by region |

---

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-21 | ECS Fargate over App Runner | Native VPC membership simplifies SLLM private networking at Phase 6 |
| 2026-06-21 | Secrets Manager over env vars | IAM-controlled, audit-logged, rotation support |
| 2026-06-21 | Vercel for frontends | Better than S3+CloudFront for Next.js/Vite; see blended.md |
| 2026-06-21 | NAT Gateway for ECS egress | ECS in private subnet cannot reach external APIs otherwise |
| 2026-06-21 | EC2 G5 for Phase 6+ SLLM | Same VPC, Security Group isolation, no public IP |

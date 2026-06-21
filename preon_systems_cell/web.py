from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except ImportError:
    pass

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from preon_systems_cell.api import (
    ENGINE_VERSION,
    RUNTIME,
    activate_genome_version,
    add_food,
    apply_growth_template,
    birth_zygote,
    block_structure_request,
    create_capability,
    create_bone_proposal,
    create_cell,
    create_contract,
    create_genome_version,
    create_memory,
    create_organism,
    create_review,
    create_zygote,
    debug_bundle,
    deprecate_contract,
    deprecate_memory,
    decide_review,
    decide_structure_proposal,
    develop_zygote,
    die_organism,
    check_cell_division_readiness,
    divide_cell,
    export_organism,
    get_genome,
    get_memory,
    get_organism_detail,
    get_soul,
    get_zygote,
    grant_oxygen,
    growth_template,
    health_report,
    get_policies,
    hibernate_organism,
    hibernate_cell,
    import_organism,
    list_bones,
    list_contracts,
    list_capabilities,
    list_cells,
    list_cell_divisions,
    list_events,
    list_genome_versions,
    list_genomes,
    list_memory,
    list_organisms,
    list_organs,
    list_reviews,
    list_souls,
    list_structure_proposals,
    list_structure_requests,
    list_tissues,
    list_zygotes,
    maintenance_status,
    mark_cell_dead,
    negotiate_reproduction,
    preview_genome,
    replay_signal,
    reincarnate_soul,
    resolve_structure_request,
    run_maintenance,
    runtime_metrics,
    self_consume_cell,
    simulate_policy,
    submit_signal,
    test_contract_adapter,
    update_cell,
    update_genome_division_policy,
    update_policies,
    validate_genome,
    validate_contract_adapter,
    validate_policies,
    wake_organism,
)
from preon_systems_cell.email import (
    password_reset_email,
    send_email,
    verification_email,
)
from preon_systems_cell.auth import (
    AuthSessionResponse,
    AuthUser,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    InMemoryAuthRepository,
    LoginRequest,
    OAuthProviderResponse,
    PasswordPolicyResponse,
    ResetPasswordRequest,
    SESSION_COOKIE_NAME,
    SignupRequest,
    VerifyEmailRequest,
    auth_url,
    check_rate_limit,
    clear_session_cookie,
    frontend_base_url,
    hash_password,
    oauth_authorization_url,
    password_policy_errors,
    require_csrf,
    require_current_user,
    session_expires_at,
    set_session_cookie,
    token_expires_at,
    verify_password,
)
from preon_systems_cell.models import (
    AdapterTestRequest,
    Actor,
    ApplyGrowthTemplateRequest,
    BlockStructureRequestRequest,
    CreateBoneProposalRequest,
    CreateCapabilityRequest,
    CreateCellRequest,
    CreateContractRequest,
    CreateGenomeVersionRequest,
    CreateMemoryRequest,
    CreateOrganismRequest,
    CreateReviewRequest,
    CreateZygoteRequest,
    DecideProposalRequest,
    DecideReviewRequest,
    DevelopZygoteRequest,
    DivideCellRequest,
    FoodIntakeRequest,
    Genome,
    GenomePreviewRequest,
    HealthResponse,
    OxygenGrantRequest,
    PolicySimulationRequest,
    PolicyUpdateRequest,
    ReproductionNegotiateRequest,
    ResolveStructureRequestRequest,
    SubmitSignalRequest,
    UpdateCellRequest,
    UpdateDivisionPolicyRequest,
)
from preon_systems_cell.storage.manager import StorageManager


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


class GenomeValidationRequest(BaseModel):
    genome: Genome


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        manager = await StorageManager.create()
        app.state.storage = manager
        app.state.auth = manager.auth
        if manager.postgres is not None:
            RUNTIME.stores = await manager.postgres.load_stores()
            RUNTIME._bind_services()
        try:
            yield
        finally:
            await manager.close()

    app = FastAPI(
        title="Preon Systems Organism Runtime API",
        version=ENGINE_VERSION,
        description="Deterministic organism runtime with membrane admission, ribosome routing, proteins, and contracts.",
        lifespan=lifespan,
    )
    app.state.auth = InMemoryAuthRepository()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def csrf_middleware(request: Request, call_next):
        try:
            require_csrf(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        storage = getattr(app.state, "storage", None)
        storage_status = (
            storage.status.model_dump()
            if storage is not None
            else {"mode": "memory", "primary": "postgres", "fallback": "memory", "degraded": True}
        )
        return HealthResponse(
            status="ok",
            runtime="organism",
            storage=storage_status,
        )

    @app.get("/auth/password-policy", response_model=PasswordPolicyResponse)
    async def get_password_policy() -> PasswordPolicyResponse:
        return PasswordPolicyResponse(policy=await _auth_repository(app).get_password_policy())

    @app.post("/auth/signup", response_model=AuthSessionResponse)
    async def signup(request: Request, response: Response, payload: SignupRequest) -> AuthSessionResponse:
        check_rate_limit(f"signup:{payload.email}")
        auth = _auth_repository(app)
        if payload.confirm_password is not None and payload.confirm_password != payload.password:
            raise HTTPException(status_code=422, detail="passwords do not match")
        policy_errors = password_policy_errors(payload.password, await auth.get_password_policy())
        if policy_errors:
            raise HTTPException(status_code=422, detail=policy_errors)
        try:
            user = await auth.create_user(payload.email, hash_password(payload.password), payload.name)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        token = await auth.create_session(user.id, session_expires_at())
        verification_token = await auth.create_email_verification_token(user.id, token_expires_at())
        set_session_cookie(response, token)
        verification_url = auth_url(request, "/verify-email", verification_token)
        sent = await send_email(user.email, *verification_email(verification_url))
        return AuthSessionResponse(user=user.public(), email_verification_url=None if sent else verification_url)

    @app.post("/auth/login", response_model=AuthSessionResponse)
    async def login(response: Response, payload: LoginRequest) -> AuthSessionResponse:
        check_rate_limit(f"login:{payload.email}")
        auth = _auth_repository(app)
        user = await auth.get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="invalid email or password")
        token = await auth.create_session(user.id, session_expires_at())
        set_session_cookie(response, token)
        return AuthSessionResponse(user=user.public())

    @app.post("/auth/logout")
    async def logout(request: Request, response: Response) -> dict[str, bool]:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            await _auth_repository(app).delete_session(token)
        clear_session_cookie(response)
        return {"ok": True}

    @app.get("/auth/me")
    async def me(request: Request, response: Response, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        response.headers["Cache-Control"] = "no-store"
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if token:
            refreshed = await _auth_repository(app).refresh_session(token)
            if refreshed:
                set_session_cookie(response, token)
        return {"user": user.public().model_dump(mode="json")}

    @app.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
    async def forgot_password(request: Request, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        auth = _auth_repository(app)
        user = await auth.get_user_by_email(payload.email)
        if user is None:
            return ForgotPasswordResponse(ok=True)
        reset_token = await auth.create_password_reset_token(user.id, token_expires_at())
        reset_url = auth_url(request, "/reset-password", reset_token)
        sent = await send_email(user.email, *password_reset_email(reset_url))
        return ForgotPasswordResponse(ok=True, reset_url=None if sent else reset_url)

    @app.post("/auth/reset-password")
    async def reset_password(payload: ResetPasswordRequest) -> dict[str, bool]:
        auth = _auth_repository(app)
        policy_errors = password_policy_errors(payload.password, await auth.get_password_policy())
        if policy_errors:
            raise HTTPException(status_code=422, detail=policy_errors)
        user = await auth.consume_password_reset_token(payload.token)
        if user is None:
            raise HTTPException(status_code=400, detail="invalid or expired reset token")
        await auth.update_password(user.id, hash_password(payload.password))
        await auth.delete_sessions_for_user(user.id)
        return {"ok": True}

    @app.post("/auth/verify-email", response_model=AuthSessionResponse)
    async def verify_email(payload: VerifyEmailRequest) -> AuthSessionResponse:
        user = await _auth_repository(app).consume_email_verification_token(payload.token)
        if user is None:
            raise HTTPException(status_code=400, detail="invalid or expired verification token")
        return AuthSessionResponse(user=user.public())

    @app.get("/auth/oauth/{provider}", response_model=OAuthProviderResponse)
    async def oauth_start(provider: str) -> OAuthProviderResponse:
        if provider not in {"google", "microsoft"}:
            raise HTTPException(status_code=404, detail="unknown OAuth provider")
        url = oauth_authorization_url(provider)
        return OAuthProviderResponse(provider=provider, configured=url is not None, authorization_url=url)

    @app.post("/auth/oauth/{provider}/callback", response_model=AuthSessionResponse)
    async def oauth_callback(provider: str, payload: OAuthCallbackRequest, response: Response) -> AuthSessionResponse:
        if provider not in {"google"}:
            raise HTTPException(status_code=404, detail="unknown OAuth provider")
        prefix = f"PREON_{provider.upper()}_OAUTH"
        client_id = os.getenv(f"{prefix}_CLIENT_ID")
        client_secret = os.getenv(f"{prefix}_CLIENT_SECRET")
        redirect_uri = os.getenv(f"{prefix}_REDIRECT_URI")
        token_url = os.getenv(f"{prefix}_TOKEN_URL", "https://oauth2.googleapis.com/token")
        userinfo_url = os.getenv(f"{prefix}_USERINFO_URL", "https://www.googleapis.com/oauth2/v3/userinfo")
        if not (client_id and client_secret and redirect_uri):
            raise HTTPException(status_code=503, detail=f"{provider} OAuth not configured")
        try:
            userinfo = await asyncio.to_thread(
                _exchange_oauth_code, client_id, client_secret, redirect_uri, payload.code, token_url, userinfo_url
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}") from exc
        email = userinfo.get("email")
        name = userinfo.get("name")
        email_verified = userinfo.get("email_verified", False)
        if not email:
            raise HTTPException(status_code=400, detail="OAuth provider did not return an email address")
        if not email_verified:
            raise HTTPException(status_code=400, detail="OAuth email address is not verified by the provider")
        auth = _auth_repository(app)
        user = await auth.get_user_by_email(email)
        if user is None:
            import secrets as _sec
            user = await auth.create_user(email, f"oauth${_sec.token_hex(32)}", name)
            await auth.mark_email_verified(user.id)
            user = await auth.get_user(user.id)
        token = await auth.create_session(user.id, session_expires_at())
        set_session_cookie(response, token)
        return AuthSessionResponse(user=user.public())

    @app.get("/reset-password")
    def reset_password_page(request: Request) -> RedirectResponse:
        return _redirect_to_frontend(request, "/reset-password")

    @app.get("/verify-email")
    def verify_email_page(request: Request) -> RedirectResponse:
        return _redirect_to_frontend(request, "/verify-email")

    @app.post("/api/organisms")
    async def create_organism_route(payload: CreateOrganismRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organism = create_organism(payload, user.id)
        await _persist_runtime(app)
        return {"organism": organism.model_dump(mode="json")}

    @app.get("/api/organisms")
    async def list_organisms_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"organisms": [organism.model_dump(mode="json") for organism in list_organisms(user.id)]}

    @app.get("/api/organisms/{organism_id}")
    async def get_organism_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        detail = get_organism_detail(organism_id, user.id)
        if detail is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return detail.model_dump(mode="json")

    @app.post("/api/reproduction/negotiate")
    async def negotiate_reproduction_route(payload: ReproductionNegotiateRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        report = negotiate_reproduction(payload, user.id)
        if report is None:
            raise HTTPException(status_code=404, detail="parent organism not found")
        await _persist_runtime(app)
        return {"negotiation": report}

    @app.post("/api/reproduction/zygote")
    async def create_zygote_route(payload: CreateZygoteRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        zygote = create_zygote(payload, user.id)
        if zygote is None:
            raise HTTPException(status_code=404, detail="parent organism not found")
        await _persist_runtime(app)
        return {"zygote": zygote.model_dump(mode="json")}

    @app.get("/api/zygotes")
    async def list_zygotes_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"zygotes": [zygote.model_dump(mode="json") for zygote in list_zygotes(user.id)]}

    @app.get("/api/zygotes/{zygote_id}")
    async def get_zygote_route(zygote_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        zygote = get_zygote(zygote_id, user.id)
        if zygote is None:
            raise HTTPException(status_code=404, detail="zygote not found")
        return {"zygote": zygote.model_dump(mode="json")}

    @app.post("/api/zygotes/{zygote_id}/develop")
    async def develop_zygote_route(zygote_id: str, payload: DevelopZygoteRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        zygote = develop_zygote(zygote_id, payload, user.id)
        if zygote is None:
            raise HTTPException(status_code=404, detail="zygote not found")
        await _persist_runtime(app)
        return {"zygote": zygote.model_dump(mode="json")}

    @app.post("/api/zygotes/{zygote_id}/differentiate")
    async def differentiate_zygote_route(zygote_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        zygote = develop_zygote(zygote_id, DevelopZygoteRequest(target_stage="fetus"), user.id)
        if zygote is None:
            raise HTTPException(status_code=404, detail="zygote not found")
        await _persist_runtime(app)
        return {"zygote": zygote.model_dump(mode="json")}

    @app.post("/api/zygotes/{zygote_id}/birth")
    async def birth_zygote_route(zygote_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organism = birth_zygote(zygote_id, user.id)
        if organism is None:
            raise HTTPException(status_code=404, detail="zygote not found")
        await _persist_runtime(app)
        return {"organism": organism.model_dump(mode="json")}

    @app.get("/api/growth/templates")
    async def growth_templates_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        _ = user
        return {"templates": {"human_minimal_v3": growth_template()}}

    @app.post("/api/organisms/{organism_id}/growth/apply-template")
    async def apply_growth_template_route(organism_id: str, payload: ApplyGrowthTemplateRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        try:
            result = apply_growth_template(organism_id, payload, user.id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if result is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"growth": result}

    @app.get("/api/organisms/{organism_id}/organs")
    async def organs_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organs = list_organs(organism_id, user.id)
        if organs is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"organs": [organ.model_dump(mode="json") for organ in organs]}

    @app.get("/api/organisms/{organism_id}/tissues")
    async def tissues_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        tissues = list_tissues(organism_id, user.id)
        if tissues is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"tissues": [tissue.model_dump(mode="json") for tissue in tissues]}

    @app.post("/api/organisms/{organism_id}/cells/{cell_id}/divide")
    async def divide_cell_route(organism_id: str, cell_id: str, payload: DivideCellRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        try:
            division = divide_cell(organism_id, cell_id, payload, user.id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if division is None:
            raise HTTPException(status_code=404, detail="cell not found")
        await _persist_runtime(app)
        return {"division": division.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/cell-divisions")
    async def cell_divisions_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        divisions = list_cell_divisions(organism_id, user.id)
        if divisions is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"cell_divisions": [division.model_dump(mode="json") for division in divisions]}

    @app.post("/api/organisms/{organism_id}/food")
    async def food_route(organism_id: str, payload: FoodIntakeRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        food = add_food(organism_id, payload, user.id)
        if food is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"food": food.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/oxygen")
    async def oxygen_route(organism_id: str, payload: OxygenGrantRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        oxygen = grant_oxygen(organism_id, payload, user.id)
        if oxygen is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"oxygen": oxygen.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/health")
    async def health_report_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        report = health_report(organism_id, user.id)
        if report is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"health": report}

    @app.post("/api/organisms/{organism_id}/cells/{cell_id}/self-consume")
    async def self_consume_cell_route(organism_id: str, cell_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        cell = self_consume_cell(organism_id, cell_id, user.id)
        if cell is None:
            raise HTTPException(status_code=404, detail="cell not found")
        await _persist_runtime(app)
        return {"cell": cell.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/cells/{cell_id}/mark-dead")
    async def mark_cell_dead_route(organism_id: str, cell_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        cell = mark_cell_dead(organism_id, cell_id, user.id)
        if cell is None:
            raise HTTPException(status_code=404, detail="cell not found")
        await _persist_runtime(app)
        return {"cell": cell.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/die")
    async def die_organism_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        soul = die_organism(organism_id, user.id)
        if soul is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"soul": soul.model_dump(mode="json")}

    @app.get("/api/souls")
    async def souls_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"souls": [soul.model_dump(mode="json") for soul in list_souls(user.id)]}

    @app.get("/api/souls/{soul_id}")
    async def get_soul_route(soul_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        soul = get_soul(soul_id, user.id)
        if soul is None:
            raise HTTPException(status_code=404, detail="soul not found")
        return {"soul": soul.model_dump(mode="json")}

    @app.post("/api/souls/{soul_id}/reincarnate")
    async def reincarnate_soul_route(soul_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organism = reincarnate_soul(soul_id, user.id)
        if organism is None:
            raise HTTPException(status_code=404, detail="soul not found")
        await _persist_runtime(app)
        return {"organism": organism.model_dump(mode="json")}

    @app.get("/api/bones")
    async def bones_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"bones": [bone.model_dump(mode="json") for bone in list_bones(user.id)]}

    @app.get("/api/bones/proposals")
    async def structure_proposals_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"proposals": [proposal.model_dump(mode="json") for proposal in list_structure_proposals(user.id)]}

    @app.post("/api/bones/proposals")
    async def create_structure_proposal_route(payload: CreateBoneProposalRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        proposal = create_bone_proposal(payload, user.id)
        await _persist_runtime(app)
        return {"proposal": proposal.model_dump(mode="json")}

    @app.post("/api/bones/proposals/{proposal_id}/approve")
    async def approve_structure_proposal_route(proposal_id: str, payload: DecideProposalRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        proposal = decide_structure_proposal(proposal_id, payload, True, user.id)
        if proposal is None:
            raise HTTPException(status_code=404, detail="proposal not found")
        await _persist_runtime(app)
        return {"proposal": proposal.model_dump(mode="json")}

    @app.post("/api/bones/proposals/{proposal_id}/reject")
    async def reject_structure_proposal_route(proposal_id: str, payload: DecideProposalRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        proposal = decide_structure_proposal(proposal_id, payload, False, user.id)
        if proposal is None:
            raise HTTPException(status_code=404, detail="proposal not found")
        await _persist_runtime(app)
        return {"proposal": proposal.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/wake")
    async def wake_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organism = wake_organism(organism_id, user.id)
        if organism is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"organism": organism.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/hibernate")
    async def hibernate_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organism = hibernate_organism(organism_id, user.id)
        if organism is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"organism": organism.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/cells")
    async def cells_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        cells = list_cells(organism_id, user.id)
        if cells is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"cells": [cell.model_dump(mode="json") for cell in cells]}

    @app.post("/api/organisms/{organism_id}/cells")
    async def create_cell_route(organism_id: str, payload: CreateCellRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        cell = create_cell(organism_id, payload, user.id)
        if cell is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"cell": cell.model_dump(mode="json")}

    @app.patch("/api/organisms/{organism_id}/cells/{cell_id}")
    async def update_cell_route(organism_id: str, cell_id: str, payload: UpdateCellRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        cell = update_cell(organism_id, cell_id, payload, user.id)
        if cell is None:
            raise HTTPException(status_code=404, detail="cell not found")
        await _persist_runtime(app)
        return {"cell": cell.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/cells/{cell_id}/hibernate")
    async def hibernate_cell_route(organism_id: str, cell_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        cell = hibernate_cell(organism_id, cell_id, user.id)
        if cell is None:
            raise HTTPException(status_code=404, detail="cell not found")
        await _persist_runtime(app)
        return {"cell": cell.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/memory")
    async def memory_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        records = list_memory(organism_id, user.id)
        if records is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"memory_records": [record.model_dump(mode="json") for record in records]}

    @app.post("/api/organisms/{organism_id}/memory")
    async def create_memory_route(organism_id: str, payload: CreateMemoryRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        record = create_memory(organism_id, payload, user.id)
        if record is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"memory_record": record.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/memory/{memory_id}")
    async def get_memory_route(organism_id: str, memory_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        record = get_memory(organism_id, memory_id, user.id)
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        return {"memory_record": record.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/memory/{memory_id}/deprecate")
    async def deprecate_memory_route(organism_id: str, memory_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        record = deprecate_memory(organism_id, memory_id, user.id)
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        await _persist_runtime(app)
        return {"memory_record": record.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/signals")
    async def submit_signal_route(
        organism_id: str,
        payload: SubmitSignalRequest,
        user: AuthUser = Depends(require_current_user),
    ) -> dict[str, object]:
        response = submit_signal(organism_id, payload, user.id, Actor(actor_id=user.id, roles=["operator"]))
        if response is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return response.model_dump(mode="json")

    @app.get("/api/organisms/{organism_id}/events")
    async def organism_events_route(
        organism_id: str,
        cursor: int = 0,
        limit: int = 100,
        type: str | None = None,
        signal_id: str | None = None,
        user: AuthUser = Depends(require_current_user),
    ) -> dict[str, object]:
        page = list_events(organism_id, user.id, event_type=type, signal_id=signal_id, limit=limit, cursor=cursor)
        if page is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return page

    @app.post("/api/organisms/{organism_id}/signals/{signal_id}/replay")
    async def replay_signal_route(organism_id: str, signal_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        replay = replay_signal(organism_id, signal_id, user.id)
        if replay is None:
            raise HTTPException(status_code=404, detail="signal not found")
        await _persist_runtime(app)
        return {"replay": replay.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/signals/{signal_id}/replay")
    async def replay_signal_get_route(organism_id: str, signal_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        replay = replay_signal(organism_id, signal_id, user.id)
        if replay is None:
            raise HTTPException(status_code=404, detail="signal not found")
        return {"replay": replay.model_dump(mode="json")}

    @app.get("/api/contracts")
    async def contracts_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"contracts": [contract.model_dump(mode="json") for contract in list_contracts(user.id)]}

    @app.post("/api/contracts")
    async def create_contract_route(payload: CreateContractRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        contract = create_contract(payload, user.id)
        await _persist_runtime(app)
        return {"contract": contract.model_dump(mode="json")}

    @app.get("/api/capabilities")
    async def capabilities_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"capabilities": [item.model_dump(mode="json") for item in list_capabilities(user.id)]}

    @app.post("/api/capabilities")
    async def create_capability_route(payload: CreateCapabilityRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        capability = create_capability(payload, user.id)
        await _persist_runtime(app)
        return {"capability": capability.model_dump(mode="json")}

    @app.post("/api/contracts/{contract_id}/validate-adapter")
    async def validate_contract_adapter_route(contract_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        report = validate_contract_adapter(contract_id, user.id)
        if report is None:
            raise HTTPException(status_code=404, detail="contract not found")
        return {"report": report.model_dump(mode="json")}

    @app.post("/api/contracts/{contract_id}/test-adapter")
    async def test_contract_adapter_route(contract_id: str, payload: AdapterTestRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        result = test_contract_adapter(contract_id, payload, user.id)
        if result is None:
            raise HTTPException(status_code=404, detail="contract not found")
        return {"result": result}

    @app.post("/api/contracts/{contract_id}/deprecate")
    async def deprecate_contract_route(contract_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        try:
            contract = deprecate_contract(contract_id, user.id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if contract is None:
            raise HTTPException(status_code=404, detail="contract not found")
        await _persist_runtime(app)
        return {"contract": contract.model_dump(mode="json")}

    @app.get("/api/structure-requests")
    async def structure_requests_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"structure_requests": [item.model_dump(mode="json") for item in list_structure_requests(user.id)]}

    @app.post("/api/structure-requests/{request_id}/resolve")
    async def resolve_structure_request_route(
        request_id: str,
        payload: ResolveStructureRequestRequest,
        user: AuthUser = Depends(require_current_user),
    ) -> dict[str, object]:
        request = resolve_structure_request(request_id, payload, user.id)
        if request is None:
            raise HTTPException(status_code=404, detail="structure request not found")
        await _persist_runtime(app)
        return {"structure_request": request.model_dump(mode="json")}

    @app.post("/api/structure-requests/{request_id}/block")
    async def block_structure_request_route(
        request_id: str,
        payload: BlockStructureRequestRequest,
        user: AuthUser = Depends(require_current_user),
    ) -> dict[str, object]:
        request = block_structure_request(request_id, payload, user.id)
        if request is None:
            raise HTTPException(status_code=404, detail="structure request not found")
        await _persist_runtime(app)
        return {"structure_request": request.model_dump(mode="json")}

    @app.get("/api/genomes/{genome_id}")
    async def genome_route(genome_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        genome = get_genome(genome_id)
        if genome is None:
            raise HTTPException(status_code=404, detail="genome not found")
        return {"genome": genome.model_dump(mode="json")}

    @app.get("/api/genomes")
    async def genomes_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"genomes": [genome.model_dump(mode="json") for genome in list_genomes()]}

    @app.post("/api/genomes")
    async def create_genome_route(payload: CreateGenomeVersionRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        version = create_genome_version(payload, user.id)
        await _persist_runtime(app)
        return {"genome_version": version.model_dump(mode="json")}

    @app.post("/api/genomes/{genome_id}/versions")
    async def create_genome_version_route(genome_id: str, payload: CreateGenomeVersionRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        if payload.genome.genome_id != genome_id:
            raise HTTPException(status_code=422, detail="genome id mismatch")
        version = create_genome_version(payload, user.id)
        await _persist_runtime(app)
        return {"genome_version": version.model_dump(mode="json")}

    @app.get("/api/genomes/{genome_id}/versions")
    async def genome_versions_route(genome_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        versions = list_genome_versions(genome_id, user.id)
        return {"genome_versions": [version.model_dump(mode="json") for version in versions or []]}

    @app.post("/api/genomes/{genome_id}/versions/{version}/activate")
    async def activate_genome_version_route(genome_id: str, version: int, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        genome_version = activate_genome_version(genome_id, version, user.id)
        if genome_version is None:
            raise HTTPException(status_code=404, detail="genome version not found")
        await _persist_runtime(app)
        return {"genome_version": genome_version.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/genome/preview")
    async def preview_genome_route(organism_id: str, payload: GenomePreviewRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        result = preview_genome(organism_id, payload, user.id)
        if result is None:
            raise HTTPException(status_code=404, detail="organism or cell not found")
        return {"preview": result}

    @app.post("/api/genomes/{genome_id}/validate")
    async def validate_genome_route(genome_id: str, payload: GenomeValidationRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        if payload.genome.genome_id != genome_id:
            raise HTTPException(status_code=422, detail="genome id mismatch")
        return validate_genome(payload.genome).model_dump(mode="json")

    @app.patch("/api/genomes/{genome_id}/division-policy")
    async def update_division_policy_route(genome_id: str, payload: UpdateDivisionPolicyRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        genome = update_genome_division_policy(genome_id, payload.policy)
        if genome is None:
            raise HTTPException(status_code=404, detail="genome not found")
        await _persist_runtime(app)
        return {"genome": genome.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/cells/{cell_id}/division-readiness")
    async def division_readiness_route(organism_id: str, cell_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        result = check_cell_division_readiness(organism_id, cell_id, user.id)
        if result is None:
            raise HTTPException(status_code=404, detail="organism or cell not found")
        return {"readiness": result.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/policies")
    async def policies_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        version = get_policies(organism_id, user.id)
        if version is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"policy_version": version.model_dump(mode="json")}

    @app.put("/api/organisms/{organism_id}/policies")
    async def update_policies_route(organism_id: str, payload: PolicyUpdateRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        try:
            version = update_policies(organism_id, payload, user.id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if version is None:
            raise HTTPException(status_code=404, detail="organism not found")
        await _persist_runtime(app)
        return {"policy_version": version.model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/policies/validate")
    async def validate_policies_route(organism_id: str, payload: PolicyUpdateRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        if get_organism_detail(organism_id, user.id) is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"report": validate_policies(payload).model_dump(mode="json")}

    @app.post("/api/organisms/{organism_id}/policies/simulate")
    async def simulate_policy_route(organism_id: str, payload: PolicySimulationRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        result = simulate_policy(organism_id, payload, user.id)
        if result is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return result

    @app.get("/api/maintenance/status")
    async def maintenance_status_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return maintenance_status()

    @app.post("/api/maintenance/run")
    async def run_maintenance_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        run = run_maintenance()
        await _persist_runtime(app)
        return {"run": run.model_dump(mode="json")}

    @app.get("/api/metrics/runtime")
    async def runtime_metrics_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        metrics = runtime_metrics()
        return {"metrics": metrics}

    @app.get("/api/metrics/organisms/{organism_id}")
    async def organism_metrics_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        metrics = runtime_metrics(organism_id, user.id)
        if metrics is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"metrics": metrics}

    @app.get("/api/organisms/{organism_id}/export")
    async def export_organism_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        bundle = export_organism(organism_id, user.id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"bundle": bundle}

    @app.post("/api/organisms/import")
    async def import_organism_route(payload: dict[str, object], user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        organism = import_organism(payload.get("bundle", payload), user.id)
        await _persist_runtime(app)
        return {"organism": organism.model_dump(mode="json")}

    @app.get("/api/organisms/{organism_id}/debug-bundle")
    async def debug_bundle_route(organism_id: str, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        bundle = debug_bundle(organism_id, user.id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="organism not found")
        return {"bundle": bundle}

    @app.get("/api/reviews")
    async def reviews_route(user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        return {"reviews": [review.model_dump(mode="json") for review in list_reviews(user.id)]}

    @app.post("/api/reviews")
    async def create_review_route(payload: CreateReviewRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        review = create_review(payload, user.id)
        await _persist_runtime(app)
        return {"review": review.model_dump(mode="json")}

    @app.post("/api/reviews/{review_id}/approve")
    async def approve_review_route(review_id: str, payload: DecideReviewRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        review = decide_review(review_id, payload, True, user.id)
        if review is None:
            raise HTTPException(status_code=404, detail="review not found")
        await _persist_runtime(app)
        return {"review": review.model_dump(mode="json")}

    @app.post("/api/reviews/{review_id}/reject")
    async def reject_review_route(review_id: str, payload: DecideReviewRequest, user: AuthUser = Depends(require_current_user)) -> dict[str, object]:
        review = decide_review(review_id, payload, False, user.id)
        if review is None:
            raise HTTPException(status_code=404, detail="review not found")
        await _persist_runtime(app)
        return {"review": review.model_dump(mode="json")}

    @app.get("/", response_class=FileResponse)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


def _auth_repository(app: FastAPI):
    auth = getattr(app.state, "auth", None)
    if auth is None:
        auth = InMemoryAuthRepository()
        app.state.auth = auth
    return auth


async def _persist_runtime(app: FastAPI) -> None:
    storage = getattr(app.state, "storage", None)
    if storage is not None and storage.postgres is not None:
        await storage.postgres.save_stores(RUNTIME.stores)


def _exchange_oauth_code(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    token_url: str,
    userinfo_url: str,
) -> dict:
    """Synchronous OAuth2 code exchange. Run in a thread executor."""
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    with urllib.request.urlopen(token_url, data=token_data, timeout=10) as resp:
        tokens = json.loads(resp.read())
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError(f"no access_token in response: {list(tokens.keys())}")
    req = urllib.request.Request(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _redirect_to_frontend(request: Request, path: str) -> RedirectResponse:
    query = request.url.query
    suffix = f"?{query}" if query else ""
    return RedirectResponse(f"{frontend_base_url(request)}{path}{suffix}")


app = create_app()


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("preon_systems_cell.web:app", host=host, port=port, reload=False)

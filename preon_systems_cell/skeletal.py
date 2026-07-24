from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import asyncio
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol

from preon_systems_cell.models import StructureProposal


SKELETAL_TISSUE_ID = "skeletal"
OSTEOBLAST = "osteoblast"
OSTEOCLAST = "osteoclast"
OSTEOCYTE = "osteocyte"
SKELETAL_CELL_TYPES = (OSTEOBLAST, OSTEOCLAST, OSTEOCYTE)


def canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class StructuralApplyResult:
    provider_resource_ref: str
    observed_state: dict[str, Any]


class StructuralProvider(Protocol):
    """Provider boundary used by skeletal cells.

    ``plan`` must be side-effect free. ``apply`` may mutate provider state, but
    only after the runtime has recorded an explicit approval for the exact plan
    digest.
    """

    def plan(self, proposal: StructureProposal) -> dict[str, Any]: ...

    def apply(self, proposal: StructureProposal) -> StructuralApplyResult: ...

    def inspect(self, provider_resource_ref: str) -> dict[str, Any]: ...


class InMemoryStructuralProvider:
    """Deterministic Phase 5A provider used for lifecycle and parity testing.

    The proposal retains the requested provider name (postgres, s3, azure_blob,
    and so on), while this adapter safely materializes only an in-process
    representation. Real cloud mutation belongs behind the same provider
    contract and is deliberately not inferred from a provider label.
    """

    def __init__(self) -> None:
        self._resources: dict[str, dict[str, Any]] = {}

    def plan(self, proposal: StructureProposal) -> dict[str, Any]:
        return {
            "operation": proposal.operation.value,
            "provider": proposal.provider,
            "resource_kind": proposal.structure_type,
            "name": proposal.name,
            "definition": proposal.definition,
            "target_resource_id": proposal.target_resource_id,
        }

    def apply(self, proposal: StructureProposal) -> StructuralApplyResult:
        if proposal.plan_digest is None or canonical_digest(proposal.plan) != proposal.plan_digest:
            raise ValueError("approved structural plan digest does not match the reviewed plan")
        provider_ref = (
            str(proposal.plan.get("target_provider_ref") or proposal.target_resource_id)
            if proposal.operation.value != "grow" and proposal.target_resource_id
            else f"{proposal.provider}://{proposal.organism_id or 'shared'}/{proposal.proposal_id}"
        )
        observed = {
            "exists": proposal.operation.value != "retire",
            "provider": proposal.provider,
            "resource_kind": proposal.structure_type,
            "definition": proposal.definition,
            "plan_digest": proposal.plan_digest,
        }
        self._resources[provider_ref] = observed
        return StructuralApplyResult(provider_resource_ref=provider_ref, observed_state=observed)

    def inspect(self, provider_resource_ref: str) -> dict[str, Any]:
        return dict(self._resources.get(provider_resource_ref, {"exists": False}))


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_PG_TYPES = {
    "text": "TEXT",
    "integer": "BIGINT",
    "number": "DOUBLE PRECISION",
    "boolean": "BOOLEAN",
    "json": "JSONB",
    "timestamp": "TIMESTAMPTZ",
}


def _identifier(value: object, field: str) -> str:
    text = str(value or "")
    if not _IDENTIFIER.fullmatch(text):
        raise ValueError(f"{field} must be a lowercase PostgreSQL identifier")
    return text


def _run_async(factory):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="preon-structural") as pool:
        return pool.submit(lambda: asyncio.run(factory())).result()


class PostgresStructuralProvider:
    """Provision structured PostgreSQL resources without accepting arbitrary SQL."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def plan(self, proposal: StructureProposal) -> dict[str, Any]:
        if proposal.structure_type not in {"database_schema", "table", "index"}:
            raise ValueError("postgres supports database_schema, table, and index resources")
        definition = dict(proposal.definition)
        schema = _identifier(
            definition.get("schema") or f"preon_{(proposal.organism_id or 'shared').replace('-', '_')[:48]}",
            "schema",
        )
        plan = {
            "operation": proposal.operation.value,
            "provider": "postgres",
            "resource_kind": proposal.structure_type,
            "schema": schema,
            "name": _identifier(definition.get("name") or proposal.name.replace("-", "_"), "name"),
            "definition": definition,
            "target_resource_id": proposal.target_resource_id,
        }
        if proposal.structure_type == "table":
            columns = definition.get("columns")
            if not isinstance(columns, dict) or not columns:
                raise ValueError("table definitions require a non-empty columns object")
            plan["columns"] = {
                _identifier(name, "column"): _PG_TYPES[str(kind)]
                for name, kind in columns.items()
                if str(kind) in _PG_TYPES
            }
            if len(plan["columns"]) != len(columns):
                raise ValueError("table definition contains an unsupported column type")
        if proposal.structure_type == "index":
            plan["table"] = _identifier(definition.get("table"), "table")
            columns = definition.get("columns")
            if not isinstance(columns, list) or not columns:
                raise ValueError("index definitions require columns")
            plan["columns"] = [_identifier(item, "column") for item in columns]
        return plan

    def apply(self, proposal: StructureProposal) -> StructuralApplyResult:
        if proposal.plan_digest is None or canonical_digest(proposal.plan) != proposal.plan_digest:
            raise ValueError("approved structural plan digest does not match the reviewed plan")

        async def execute() -> StructuralApplyResult:
            try:
                import asyncpg
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError("asyncpg is required for PostgreSQL structural provisioning") from exc
            connection = await asyncpg.connect(self.database_url)
            try:
                schema = proposal.plan["schema"]
                name = proposal.plan["name"]
                retire = proposal.operation.value == "retire"
                if proposal.structure_type == "database_schema":
                    sql = (
                        f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'
                        if retire
                        else f'CREATE SCHEMA IF NOT EXISTS "{schema}"'
                    )
                elif proposal.structure_type == "table":
                    if retire:
                        sql = f'DROP TABLE IF EXISTS "{schema}"."{name}"'
                    else:
                        columns = ", ".join(
                            f'"{column}" {kind}'
                            for column, kind in proposal.plan["columns"].items()
                        )
                        sql = f'CREATE TABLE IF NOT EXISTS "{schema}"."{name}" ({columns})'
                else:
                    if retire:
                        sql = f'DROP INDEX IF EXISTS "{schema}"."{name}"'
                    else:
                        columns = ", ".join(f'"{item}"' for item in proposal.plan["columns"])
                        sql = (
                            f'CREATE INDEX IF NOT EXISTS "{name}" ON '
                            f'"{schema}"."{proposal.plan["table"]}" ({columns})'
                        )
                await connection.execute(sql)
            finally:
                await connection.close()
            ref = f"postgres://{schema}/{name}"
            return StructuralApplyResult(
                provider_resource_ref=ref,
                observed_state={
                    "exists": not retire,
                    "provider": "postgres",
                    "resource_kind": proposal.structure_type,
                    "schema": schema,
                    "name": name,
                    "plan_digest": proposal.plan_digest,
                },
            )

        return _run_async(execute)

    def inspect(self, provider_resource_ref: str) -> dict[str, Any]:
        parts = provider_resource_ref.removeprefix("postgres://").split("/", 1)
        if len(parts) != 2:
            return {"exists": False, "provider": "postgres"}
        schema, name = parts

        async def inspect_resource() -> dict[str, Any]:
            import asyncpg

            connection = await asyncpg.connect(self.database_url)
            try:
                exists = await connection.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.schemata WHERE schema_name = $1
                    ) OR EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = $1 AND table_name = $2
                    )
                    """,
                    schema,
                    name,
                )
                return {"exists": bool(exists), "provider": "postgres", "schema": schema, "name": name}
            finally:
                await connection.close()

        return _run_async(inspect_resource)


class S3StructuralProvider:
    """S3-compatible prefix provider. Credentials remain inside the adapter."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("boto3 is required for S3 structural provisioning") from exc
        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def plan(self, proposal: StructureProposal) -> dict[str, Any]:
        if proposal.structure_type not in {"blob_store", "object_prefix"}:
            raise ValueError("s3 supports blob_store and object_prefix resources")
        namespace = str(
            proposal.definition.get("namespace")
            or f"{proposal.organism_id}/{proposal.name}"
        ).strip("/")
        if not namespace or ".." in namespace:
            raise ValueError("invalid S3 namespace")
        return {
            "operation": proposal.operation.value,
            "provider": "s3",
            "resource_kind": proposal.structure_type,
            "bucket": self.bucket,
            "prefix": f"{namespace}/",
            "target_resource_id": proposal.target_resource_id,
        }

    def apply(self, proposal: StructureProposal) -> StructuralApplyResult:
        if proposal.plan_digest is None or canonical_digest(proposal.plan) != proposal.plan_digest:
            raise ValueError("approved structural plan digest does not match the reviewed plan")
        prefix = proposal.plan["prefix"]
        marker = f"{prefix}.preon-structure"
        retire = proposal.operation.value == "retire"
        if retire:
            self._client.delete_object(Bucket=self.bucket, Key=marker)
        else:
            self._client.put_object(
                Bucket=self.bucket,
                Key=marker,
                Body=proposal.plan_digest.encode(),
                Metadata={"preon-plan-digest": proposal.plan_digest},
            )
        return StructuralApplyResult(
            provider_resource_ref=f"s3://{self.bucket}/{prefix}",
            observed_state={
                "exists": not retire,
                "provider": "s3",
                "bucket": self.bucket,
                "prefix": prefix,
                "plan_digest": proposal.plan_digest,
            },
        )

    def inspect(self, provider_resource_ref: str) -> dict[str, Any]:
        location = provider_resource_ref.removeprefix("s3://")
        bucket, _, prefix = location.partition("/")
        try:
            self._client.head_object(Bucket=bucket, Key=f"{prefix}.preon-structure")
        except Exception as exc:
            response = getattr(exc, "response", {})
            code = str(response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NotFound"}:
                return {"exists": False, "provider": "s3", "bucket": bucket, "prefix": prefix}
            raise
        return {"exists": True, "provider": "s3", "bucket": bucket, "prefix": prefix}


class StructuralProviderRegistry:
    def __init__(
        self,
        default: StructuralProvider,
        providers: dict[str, StructuralProvider] | None = None,
    ) -> None:
        self.default = default
        self.providers = dict(providers or {})

    @classmethod
    def from_env(cls) -> "StructuralProviderRegistry":
        default = InMemoryStructuralProvider()
        providers: dict[str, StructuralProvider] = {
            "memory": default,
            "runtime_store": default,
        }
        database_url = os.getenv("PREON_STRUCTURAL_DATABASE_URL")
        if database_url:
            providers["postgres"] = PostgresStructuralProvider(database_url)
        if os.getenv("PREON_S3_BUCKET"):
            providers["s3"] = S3StructuralProvider(
                bucket=os.environ["PREON_S3_BUCKET"],
                endpoint_url=os.getenv("PREON_S3_ENDPOINT_URL"),
                region=os.getenv("PREON_S3_REGION"),
                access_key_id=os.getenv("PREON_S3_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("PREON_S3_SECRET_ACCESS_KEY"),
            )
        return cls(default, providers)

    def _for(self, provider: str) -> StructuralProvider:
        return self.providers.get(provider, self.default)

    def plan(self, proposal: StructureProposal) -> dict[str, Any]:
        return self._for(proposal.provider).plan(proposal)

    def apply(self, proposal: StructureProposal) -> StructuralApplyResult:
        return self._for(proposal.provider).apply(proposal)

    def inspect(self, provider_resource_ref: str) -> dict[str, Any]:
        provider = provider_resource_ref.split(":", 1)[0]
        return self._for(provider).inspect(provider_resource_ref)

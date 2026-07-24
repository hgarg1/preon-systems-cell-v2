from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from preon_systems_cell.memory import MemoryAdmissionPolicy
from preon_systems_cell.models import (
    MemoryPolicyStatus,
    MemoryPolicyVersion,
    UpdateMemoryPolicyRequest,
    utc_now,
)


class MemoryPolicyStores(Protocol):
    memory_policy_versions: dict[str, list[MemoryPolicyVersion]]


@dataclass
class MemoryPolicyService:
    stores: MemoryPolicyStores
    id_factory: Callable[[str], str]

    def ensure_default(
        self,
        organism_id: str,
        owner_user_id: str | None,
    ) -> MemoryPolicyVersion:
        active = self.active(organism_id)
        if active is not None:
            return active
        version = MemoryPolicyVersion(
            policy_version_id=self.id_factory("memory-policy"),
            organism_id=organism_id,
            owner_user_id=owner_user_id,
            version=1,
            created_by="genesis-default",
        )
        self.stores.memory_policy_versions.setdefault(organism_id, []).append(version)
        return version

    def active(self, organism_id: str) -> MemoryPolicyVersion | None:
        return next(
            (
                item
                for item in reversed(self.stores.memory_policy_versions.get(organism_id, []))
                if item.status == MemoryPolicyStatus.ACTIVE
            ),
            None,
        )

    def update(
        self,
        organism_id: str,
        owner_user_id: str | None,
        request: UpdateMemoryPolicyRequest,
        created_by: str | None,
    ) -> MemoryPolicyVersion:
        previous = self.ensure_default(organism_id, owner_user_id)
        versions = self.stores.memory_policy_versions[organism_id]
        versions[:] = [
            item.model_copy(
                update={
                    "status": MemoryPolicyStatus.SUPERSEDED,
                }
            )
            if item.policy_version_id == previous.policy_version_id
            else item
            for item in versions
        ]
        version = MemoryPolicyVersion(
            policy_version_id=self.id_factory("memory-policy"),
            organism_id=organism_id,
            owner_user_id=owner_user_id,
            version=previous.version + 1,
            created_by=created_by,
            **request.model_dump(),
        )
        versions.append(version)
        return version

    def admission_policy(self, organism_id: str) -> MemoryAdmissionPolicy:
        active = self.active(organism_id)
        return (
            MemoryAdmissionPolicy.from_version(active)
            if active is not None
            else MemoryAdmissionPolicy()
        )

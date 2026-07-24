"""Local reference corpus for the knowledge.reference.lookup bone.

Retrieval proteins must cite a source. This corpus is the organism's own domain
vocabulary — the same material the Primordial Soup seeds as `domain_vocab` and
`genome_study` — with each entry pointing at the document that defines it.

Deliberately local: the default genome sets `external_side_effects: False`, so a
retrieval bone may not reach the network. Network-backed retrieval arrives as a
separate bone contract when the constraint is lifted.
"""
from __future__ import annotations

_README = "README.md#the-biological-model"
_PIPELINE = "README.md#signal-pipeline-trace"
_BONES = "docs/bones-and-llm-routing.md"
_ADR = "docs/architecture/decisions"

# (term, aliases, definition, source)
_CORPUS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("organism", ("organismrecord",),
     "A persistent, named entity that receives signals and maintains state.", _README),
    ("cell", ("cellrecord",),
     "An execution unit within an organism, with its own health and generation.", _README),
    ("genome", ("genes",),
     "Encodes the module set, regulatory rules, capability registry, and division policy.", _README),
    ("signal", ("input event",),
     "An input event admitted through the membrane.", _README),
    ("protein", ("output",),
     "Validated output produced by the ribosome after processing a signal.", _README),
    ("atp", ("energy", "resource budget"),
     "The execution currency: food plus oxygen. Replenished by intake, spent on execution.",
     f"{_ADR}/ADR-001-atp-continuous-stream-model.md"),
    ("food", ("data intake",),
     "Structured data intake: prompts, tasks, identity seeds, domain knowledge.",
     f"{_ADR}/ADR-003-primordial-soup-food-seeding.md"),
    ("oxygen", ("compute grant",),
     "A compute grant: CPU time, memory, context window, GPU units. Always granted before food.",
     f"{_ADR}/ADR-004-oxygen-before-food-invariant.md"),
    ("mitochondria", ("compute budget",),
     "Compute budget manager. Food without oxygen causes suffocation.", _README),
    ("genesis", ("adam", "eve", "first organism"),
     "The first organism has no parents; it is provisioned rather than born.",
     f"{_ADR}/ADR-002-genesis-no-parents.md"),
    ("primordial soup", ("soup", "food seeding"),
     "Pre-seeded food environment with five categories, provisioned before the first spark.",
     f"{_ADR}/ADR-003-primordial-soup-food-seeding.md"),
    ("cell division", ("division", "mitosis", "split"),
     "Genome-gated split producing daughter cells that inherit or differentiate from the parent.",
     f"{_ADR}/ADR-005-three-gate-division-model.md"),
    ("division policy", ("divisionpolicy", "gates"),
     "Division requires three co-required gates: load, capability, and lifecycle.",
     f"{_ADR}/ADR-006-division-policy-in-genome.md"),
    ("division modes", ("symmetric", "asymmetric", "founder", "repair"),
     "Four modes: symmetric, asymmetric, founder, and repair, each with a distinct purpose.",
     f"{_ADR}/ADR-007-division-modes-taxonomy.md"),
    ("soul", ("reincarnation",),
     "Preserved essence of a terminated organism, available for reincarnation.", _README),
    ("membrane", ("admission",),
     "Admission boundary: checks contract match and capability before a signal enters.", _PIPELINE),
    ("cytoplasm", ("cell routing",),
     "Context routing — selects which cell handles a signal. Distinct from CellWorkingState.", _PIPELINE),
    ("nucleus", ("module selection",),
     "Selects the genome module that will express in response to a signal.", _PIPELINE),
    ("ribosome", ("execution",),
     "Deterministic execution: runs a bone enzyme or instantiates an LLM protein.", _PIPELINE),
    ("golgi", ("golgi apparatus", "shaping"),
     "Validates and shapes a protein before it leaves the cell: pass, repair, or destroy.", _PIPELINE),
    ("lysosome", ("destruction",),
     "Destroys misfolded proteins, rolls back slots, and emits a retry signal.", _PIPELINE),
    ("proteasome", ("deconstruction",),
     "Deconstructs a consumed LlmProtein and deposits its answer into cell working state.", _BONES),
    ("cytoskeleton", ("routing",),
     "Routes an AnswerProtein to a cytoplasm slot, another cell, or the membrane.", _BONES),
    ("bone", ("bones", "capability contract"),
     "A structural capability contract: what the organism can do, never how.", _BONES),
    ("enzyme", ("enzymes", "compiled enzyme"),
     "A compiled execution primitive that satisfies a bone contract at runtime.", _BONES),
)

_MAX_MATCHES = 5


def search(payload: dict) -> dict:
    """Look a term up in the local reference corpus.

    Exact term/alias matches rank above substring matches. Always reports the
    source document for every hit so retrieval validation can confirm citation.
    """
    query = str(payload.get("query", "")).strip().lower()
    if not query:
        return {"result": [], "source": [], "match_count": 0, "query": query, "method": "deterministic_retrieval"}

    exact: list[dict[str, str]] = []
    partial: list[dict[str, str]] = []
    for term, aliases, definition, source in _CORPUS:
        entry = {"term": term, "definition": definition, "source": source}
        if query == term or query in aliases:
            exact.append(entry)
        elif query in term or any(query in alias for alias in aliases) or query in definition.lower():
            partial.append(entry)

    matches = (exact + partial)[:_MAX_MATCHES]
    return {
        "result": matches,
        "source": [match["source"] for match in matches],
        "match_count": len(matches),
        "query": query,
        "method": "deterministic_retrieval",
    }

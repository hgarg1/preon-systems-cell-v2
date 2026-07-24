"""Phase 3: the five protein types — prompt construction and per-type validation."""
import pytest

from preon_systems_cell.bones.data import reference
from preon_systems_cell.engine import DEFAULT_MIN_CONFIDENCE, OrganismRuntime, ProteinPipeline, SignalClassifier
from preon_systems_cell.models import (
    ExecutionStrategy,
    Genome,
    GenomeModule,
    MisfoldingType,
    OrganismRecord,
    Protein,
    ProteinStatus,
    ProteinType,
    Signal,
)


def _module(protein_type: ProteinType | None = None, **overrides) -> GenomeModule:
    defaults = dict(
        module_id="module-test",
        signal_types=["query"],
        execution_strategy=ExecutionStrategy.LLM,
        protein_type=protein_type,
    )
    defaults.update(overrides)
    return GenomeModule(**defaults)


def _protein(payload: dict, confidence: float = 0.9) -> Protein:
    return Protein(
        protein_id="protein-test",
        organism_id="organism-test",
        source_signal_id="signal-test",
        type="module-test.result",
        payload=payload,
        confidence=confidence,
    )


def _signal(payload: dict | None = None, signal_type: str = "query") -> Signal:
    return Signal(
        signal_id="signal-test",
        organism_id="organism-test",
        type=signal_type,
        payload=payload if payload is not None else {"prompt": "explain the ATP equation"},
    )


def _validate(payload: dict, module: GenomeModule | None, confidence: float = 0.9) -> Protein:
    return ProteinPipeline().validate(_protein(payload, confidence), _signal(), module)


# --------------------------------------------------------------------------- enum


def test_five_protein_types_are_defined():
    assert [member.value for member in ProteinType] == [
        "reasoning",
        "retrieval",
        "transformation",
        "aggregation",
        "evaluation",
    ]


def test_genome_module_rejects_unknown_protein_type():
    with pytest.raises(ValueError):
        GenomeModule(module_id="bad", protein_type="telepathy")


# ------------------------------------------------------------------- prompt build


@pytest.fixture
def ribosome():
    return OrganismRuntime().ribosome


def test_reasoning_prompt_asks_for_stepwise_reasoning(ribosome):
    prompt = ribosome._build_prompt(_module(ProteinType.REASONING), _signal())

    assert "step by step" in prompt
    assert "explain the ATP equation" in prompt


def test_untagged_module_is_prompted_as_reasoning(ribosome):
    signal = _signal()

    assert ribosome._build_prompt(_module(None), signal) == ribosome._build_prompt(
        _module(ProteinType.REASONING), signal
    )


def test_retrieval_prompt_demands_citation(ribosome):
    prompt = ribosome._build_prompt(_module(ProteinType.RETRIEVAL), _signal())

    assert "cite a source" in prompt
    assert "rather than guessing" in prompt


def test_transformation_prompt_injects_declared_schema(ribosome):
    module = _module(ProteinType.TRANSFORMATION, output_schema={"celsius": "number", "label": "string"})

    prompt = ribosome._build_prompt(module, _signal())

    assert "celsius: number" in prompt
    assert "label: string" in prompt


def test_transformation_prompt_without_schema_still_builds(ribosome):
    prompt = ribosome._build_prompt(_module(ProteinType.TRANSFORMATION), _signal())

    assert "no schema declared" in prompt


def test_aggregation_prompt_lists_inputs_and_counts_them(ribosome):
    signal = _signal({"prompt": "merge the findings", "inputs": ["alpha", "beta", "gamma"]})

    prompt = ribosome._build_prompt(_module(ProteinType.AGGREGATION), signal)

    assert "Combine the 3 input(s)" in prompt
    assert "[0] alpha" in prompt
    assert "[2] gamma" in prompt
    assert "contradict" in prompt


def test_evaluation_prompt_uses_module_criteria(ribosome):
    module = _module(ProteinType.EVALUATION, evaluation_criteria=["factual accuracy", "citation quality"])
    signal = _signal({"prompt": "score it", "subject": "the draft answer"})

    prompt = ribosome._build_prompt(module, signal)

    assert "- factual accuracy" in prompt
    assert "- citation quality" in prompt
    assert "the draft answer" in prompt
    assert "0.0 and 1.0" in prompt


def test_evaluation_prompt_falls_back_to_default_criteria(ribosome):
    prompt = ribosome._build_prompt(_module(ProteinType.EVALUATION), _signal())

    assert "- accuracy" in prompt
    assert "- completeness" in prompt
    assert "- relevance" in prompt


# ------------------------------------------------------------ reasoning validation


def test_reasoning_protein_above_threshold_is_approved():
    validated = _validate({"result": "because X"}, _module(ProteinType.REASONING), confidence=0.85)

    assert validated.status == ProteinStatus.APPROVED


def test_reasoning_protein_below_default_threshold_is_dropped():
    validated = _validate({"result": "maybe"}, _module(ProteinType.REASONING), confidence=0.2)

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.SEMANTIC in validated.validation_report.misfolding_types
    assert "below threshold" in validated.validation_report.errors[0]


def test_reasoning_threshold_is_configurable_per_module():
    module = _module(ProteinType.REASONING, min_confidence=0.95)

    validated = _validate({"result": "fairly sure"}, module, confidence=0.9)

    assert validated.status == ProteinStatus.DROPPED


def test_default_min_confidence_admits_the_stub_ribosome_confidence():
    # The ribosome emits 0.75 for llm_stub and 0.85 for a live call; neither may
    # start failing validation just because a module was tagged reasoning.
    assert DEFAULT_MIN_CONFIDENCE < 0.75


# ------------------------------------------------------------ retrieval validation


def test_retrieval_protein_with_result_and_source_is_approved():
    validated = _validate(
        {"result": [{"term": "atp"}], "source": ["README.md"]}, _module(ProteinType.RETRIEVAL)
    )

    assert validated.status == ProteinStatus.APPROVED


def test_retrieval_protein_without_result_is_dropped():
    validated = _validate({"result": [], "source": ["README.md"]}, _module(ProteinType.RETRIEVAL))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.STRUCTURAL in validated.validation_report.misfolding_types


def test_retrieval_protein_without_source_is_dropped():
    validated = _validate({"result": ["something"]}, _module(ProteinType.RETRIEVAL))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.CONTEXT in validated.validation_report.misfolding_types
    assert "did not cite a source" in validated.validation_report.errors[0]


def test_retrieval_accepts_plural_sources_key():
    validated = _validate(
        {"result": ["something"], "sources": ["README.md"]}, _module(ProteinType.RETRIEVAL)
    )

    assert validated.status == ProteinStatus.APPROVED


# ------------------------------------------------------- transformation validation


def test_transformation_matching_schema_is_approved():
    module = _module(ProteinType.TRANSFORMATION, output_schema={"celsius": "number", "label": "string"})

    validated = _validate({"celsius": 21.5, "label": "mild"}, module)

    assert validated.status == ProteinStatus.APPROVED


def test_transformation_missing_declared_field_is_dropped():
    module = _module(ProteinType.TRANSFORMATION, output_schema={"celsius": "number", "label": "string"})

    validated = _validate({"celsius": 21.5}, module)

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.STRUCTURAL in validated.validation_report.misfolding_types
    assert "'label'" in validated.validation_report.errors[0]


def test_transformation_wrong_field_type_is_dropped():
    module = _module(ProteinType.TRANSFORMATION, output_schema={"celsius": "number"})

    validated = _validate({"celsius": "twenty one"}, module)

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.SEMANTIC in validated.validation_report.misfolding_types


def test_transformation_rejects_bool_for_a_numeric_field():
    # bool subclasses int, so this would silently pass a naive isinstance check.
    module = _module(ProteinType.TRANSFORMATION, output_schema={"count": "integer"})

    validated = _validate({"count": True}, module)

    assert validated.status == ProteinStatus.DROPPED


def test_transformation_ignores_unrecognised_declared_type():
    module = _module(ProteinType.TRANSFORMATION, output_schema={"blob": "protobuf"})

    validated = _validate({"blob": object()}, module)

    assert validated.status == ProteinStatus.APPROVED


def test_transformation_without_declared_schema_asserts_nothing():
    validated = _validate({"anything": 1}, _module(ProteinType.TRANSFORMATION))

    assert validated.status == ProteinStatus.APPROVED


# ---------------------------------------------------------- aggregation validation


def test_aggregation_with_present_inputs_is_approved():
    validated = _validate({"inputs": ["alpha", "beta"], "result": "alpha+beta"}, _module(ProteinType.AGGREGATION))

    assert validated.status == ProteinStatus.APPROVED


def test_aggregation_without_inputs_is_dropped():
    validated = _validate({"result": "nothing to merge"}, _module(ProteinType.AGGREGATION))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.STRUCTURAL in validated.validation_report.misfolding_types


def test_aggregation_with_an_empty_input_is_dropped():
    validated = _validate({"inputs": ["alpha", ""]}, _module(ProteinType.AGGREGATION))

    assert validated.status == ProteinStatus.DROPPED
    assert "[1] is empty" in validated.validation_report.errors[0]


def test_aggregation_flags_contradicting_boolean_inputs():
    validated = _validate({"inputs": [True, False, True]}, _module(ProteinType.AGGREGATION))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.SEMANTIC in validated.validation_report.misfolding_types
    assert "contradict" in validated.validation_report.errors[0]


def test_aggregation_allows_agreeing_boolean_inputs():
    validated = _validate({"inputs": [True, True]}, _module(ProteinType.AGGREGATION))

    assert validated.status == ProteinStatus.APPROVED


def test_aggregation_does_not_flag_distinct_text_inputs():
    # Free-text divergence is not contradiction; that judgement needs Phase 7.
    validated = _validate({"inputs": ["Paris is the capital", "France is in Europe"]}, _module(ProteinType.AGGREGATION))

    assert validated.status == ProteinStatus.APPROVED


# ----------------------------------------------------------- evaluation validation


def test_evaluation_with_score_and_criteria_is_approved():
    validated = _validate({"score": 0.82, "criteria": ["accuracy"]}, _module(ProteinType.EVALUATION))

    assert validated.status == ProteinStatus.APPROVED


def test_evaluation_boundary_scores_are_valid():
    module = _module(ProteinType.EVALUATION)

    assert _validate({"score": 0.0, "criteria": ["a"]}, module).status == ProteinStatus.APPROVED
    assert _validate({"score": 1, "criteria": ["a"]}, module).status == ProteinStatus.APPROVED


def test_evaluation_score_out_of_range_is_dropped():
    validated = _validate({"score": 1.4, "criteria": ["accuracy"]}, _module(ProteinType.EVALUATION))

    assert validated.status == ProteinStatus.DROPPED
    assert "outside [0, 1]" in validated.validation_report.errors[0]


def test_evaluation_non_numeric_score_is_dropped():
    validated = _validate({"score": "high", "criteria": ["accuracy"]}, _module(ProteinType.EVALUATION))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.SEMANTIC in validated.validation_report.misfolding_types


def test_evaluation_missing_score_is_dropped():
    validated = _validate({"criteria": ["accuracy"]}, _module(ProteinType.EVALUATION))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.STRUCTURAL in validated.validation_report.misfolding_types


def test_evaluation_without_criteria_is_dropped():
    validated = _validate({"score": 0.5}, _module(ProteinType.EVALUATION))

    assert validated.status == ProteinStatus.DROPPED
    assert MisfoldingType.CONTEXT in validated.validation_report.misfolding_types


# ------------------------------------------------------------------ compatibility


def test_untagged_module_gets_no_type_validation():
    # A payload that would fail every per-type rule passes when the module is untagged.
    validated = _validate({"score": 99, "inputs": []}, _module(None), confidence=0.01)

    assert validated.status == ProteinStatus.APPROVED


def test_validate_without_module_argument_is_unchanged():
    validated = ProteinPipeline().validate(_protein({"result": "fine"}, confidence=0.01), _signal())

    assert validated.status == ProteinStatus.APPROVED


def test_toxic_payload_outranks_a_type_failure():
    validated = _validate({"result": "delete all records"}, _module(ProteinType.EVALUATION))

    assert validated.status == ProteinStatus.BLOCKED
    assert MisfoldingType.TOXIC in validated.validation_report.misfolding_types


# --------------------------------------------------------------- reference corpus


def test_reference_search_returns_definition_and_source():
    result = reference.search({"query": "ribosome"})

    # Exact term match ranks first; the definition text of other entries also matches.
    assert result["result"][0]["term"] == "ribosome"
    assert result["result"][0]["definition"]
    assert result["source"] == [match["source"] for match in result["result"]]


def test_reference_search_matches_an_alias():
    result = reference.search({"query": "energy"})

    assert result["result"][0]["term"] == "atp"


def test_reference_search_is_case_insensitive():
    assert reference.search({"query": "  ATP  "})["result"][0]["term"] == "atp"


def test_reference_search_ranks_exact_match_first():
    result = reference.search({"query": "cell"})

    assert result["result"][0]["term"] == "cell"
    assert result["match_count"] > 1  # "cell division" also matches as a substring


def test_reference_search_misses_return_no_source():
    result = reference.search({"query": "quantum chromodynamics"})

    assert result["result"] == []
    assert result["source"] == []


def test_reference_search_empty_query_returns_nothing():
    assert reference.search({"query": "   "})["match_count"] == 0


def test_every_corpus_entry_cites_a_source():
    for term, _aliases, definition, source in reference._CORPUS:
        assert term and definition and source, f"incomplete corpus entry: {term}"


# ------------------------------------------------------------------- end-to-end


def test_default_genome_ships_a_retrieval_module():
    module = next(m for m in Genome(genome_id="g").modules if m.module_id == "retrieval")

    assert module.protein_type == ProteinType.RETRIEVAL
    assert module.signal_types == ["search"]
    assert module.deterministic_tool == "knowledge.reference.lookup"


def test_default_genome_tags_the_reasoning_module():
    module = next(m for m in Genome(genome_id="g").modules if m.module_id == "reasoning")

    assert module.protein_type == ProteinType.REASONING


def test_search_signal_produces_an_approved_cited_protein():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-search"))

    decision, _, protein, events, _ = runtime.submit_signal(
        Signal(signal_id="signal-search", organism_id=organism.organism_id, type="search", payload={"query": "oxygen"})
    )

    assert decision.code == "ACCEPTED"
    assert protein is not None
    assert protein.status == ProteinStatus.APPROVED
    assert protein.payload["source"]
    assert next(event for event in events if event.type == "nucleus").values["module_id"] == "retrieval"


def test_search_signal_with_no_corpus_hit_is_dropped_for_missing_source():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-search-miss"))

    _, _, protein, _, _ = runtime.submit_signal(
        Signal(
            signal_id="signal-search-miss",
            organism_id=organism.organism_id,
            type="search",
            payload={"query": "quantum chromodynamics"},
        )
    )

    assert protein is not None
    assert protein.status == ProteinStatus.DROPPED
    assert MisfoldingType.STRUCTURAL in protein.validation_report.misfolding_types
    assert MisfoldingType.CONTEXT in protein.validation_report.misfolding_types


def test_membrane_rejects_search_signal_without_a_query():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-search-bad"))

    decision, _, protein, _, _ = runtime.submit_signal(
        Signal(
            signal_id="signal-search-bad",
            organism_id=organism.organism_id,
            type="search",
            payload={"prompt": "look something up"},
        )
    )

    assert decision.code == "INVALID_STRUCTURE"
    assert protein is None


def test_classifier_routes_an_explicit_query_key_to_search():
    classifier = SignalClassifier()

    assert classifier.reclassify(_signal({"query": "genome"})) == "search"
    assert classifier.reclassify(_signal({"query": "   "})) == "query"
    assert classifier.reclassify(_signal({"prompt": "status"})) == "query"


def test_classifier_leaves_non_query_signals_alone():
    assert SignalClassifier().reclassify(_signal({"query": "genome"}, signal_type="calculate")) == "calculate"


def test_search_policy_and_capability_graph_are_registered():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-caps"))

    assert "search" in organism.policies.allowed_signal_types
    assert "knowledge.reference.lookup" in runtime.bone_cortex.list_bones()
    assert runtime.bone_cortex.graph()["knowledge"]["reference"]["lookup"] == "knowledge.reference.lookup"

# Cell Survival Requirements Implementation Summary

This project has been reset from an abstract ATP simulator to a deterministic organism runtime.

The public runtime is organized around:

- persistent organisms
- executable cells
- genomes and expression profiles
- admitted signals
- routed ribosome execution
- validated proteins
- skeletal contracts
- runtime event logs

The ATP-era concepts of food, oxygen, biomass, toxicity, population runs, scenario YAML, BI exports, and lineage visualization are no longer active product surfaces.

## Runtime Mapping

- Membrane: validates schema, actor role, policy, rate limit, relevance, and safety.
- Cytoplasm: attaches context and routes admitted signals to active cells.
- Nucleus: interprets the genome and selects the matching module.
- Ribosome: executes through `precomputed`, `deterministic_tool`, or `llm_stub` strategies.
- Golgi: shapes and publishes approved protein payloads.
- Lysosome: cleans local temporary execution state.
- Peroxisome: blocks toxic protein output.
- Mitochondria: enforces deterministic resource budgets.
- Vacuole: stores intermediate and protein artifacts.
- Skeleton: manages contracts, dependencies, and structure requests.

## v1 Scope

This implementation is deterministic core only. It does not call live LLM providers, mutate infrastructure, or access enterprise credentials. Missing infrastructure access is represented as a `StructureRequest` rather than invented at runtime.

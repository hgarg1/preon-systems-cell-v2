# Bones: Deterministic Tools & LLM Routing

Reference for what the ribosome can call without an LLM, how routing decisions are made, and how the genome encodes which LLM provider + model class to use.

---

## Genome LLM Config

`GenomeModule` now carries three optional fields that only apply when `execution_strategy = "llm"`:

```json
{
  "module_id": "reasoning",
  "signal_types": ["query", "task.plan"],
  "execution_strategy": "llm",
  "llm_provider": "anthropic",
  "llm_model_class": "standard",
  "llm_model_id": null
}
```

| Field | Values | Notes |
|---|---|---|
| `llm_provider` | `anthropic` \| `openai` \| `grok` \| `gemini` | Which provider to call |
| `llm_model_class` | `fast` \| `standard` \| `reasoning` | Maps to a concrete model ID |
| `llm_model_id` | any string or null | Overrides model_class when set |

`execution_strategy: "llm_stub"` still works as "always mock, never call a provider."

### Provider → model class → model ID defaults

| Provider | fast | standard | reasoning |
|---|---|---|---|
| `anthropic` | claude-haiku-4-5-20251001 | claude-sonnet-4-6 | claude-opus-4-8 |
| `openai` | gpt-4o-mini | gpt-4o | o3 |
| `grok` | grok-3-mini-fast | grok-3 | grok-3-mini |
| `gemini` | gemini-2.0-flash | gemini-2.5-pro | gemini-2.5-pro |

### API keys (env vars)

| Provider | Env var |
|---|---|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Grok (xAI) | `XAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |

Grok uses the OpenAI SDK with `base_url=https://api.x.ai/v1`.

Install SDKs as optional deps:
```
pip install "preon-systems-cell[anthropic]"
pip install "preon-systems-cell[openai]"     # also covers Grok
pip install "preon-systems-cell[gemini]"
pip install "preon-systems-cell[llm]"        # all three
```

The ribosome falls back to stub silently if the env var is missing or the SDK is not installed.

---

## Signal Routing Without an LLM

The `SignalClassifier` (in `engine.py`) runs before module selection on any `type="query"` signal. It reclassifies based on payload heuristics — no LLM token spent.

| Condition | Reclassified to | Module hit |
|---|---|---|
| `payload.expression` matches pure math | `calculate` | `arithmetic` → calculator tool |
| Prompt text is pure math (`2+2`, `3*7`) | `calculate` | `arithmetic` → calculator tool |
| Prompt contains planning language ("steps to", "plan", "break down", "first…then") | `task.plan` | `reasoning` → LLM |
| Everything else | `query` (unchanged) | `reasoning` → LLM |

Typed signals (`calculate`, `contract.call`, etc.) bypass the classifier entirely — callers who know their intent use specific types.

**Rule**: use typed signals at the API boundary whenever possible. The classifier is a safety net for ambiguous free-form inputs.

---

## Bones Catalogue: Deterministic Information Sources

All entries share the same property: the answer is a pure function of the input — no network call, no LLM, no reasoning required. Each is a natural bone.

### Mathematics & Statistics

| Bone | What it gives |
|---|---|
| Calculator | Arithmetic expressions |
| Z-table | Standard normal CDF / p-values |
| t-table | Student's t critical values by df + α |
| Chi-squared table | χ² critical values |
| F-distribution table | ANOVA / regression critical values |
| Binomial / Poisson tables | Probability mass at k given n, p |
| Combinatorics engine | nCr, nPr, factorial |
| Prime checker / sieve | Is N prime? Primes up to N |
| GCD / LCM | Euclidean algorithm |
| Matrix operations | Determinant, inverse, eigenvalues (small n) |
| Trigonometric table | Exact values for common angles |
| Number base converter | Binary ↔ octal ↔ decimal ↔ hex |

### Physics & Engineering

| Bone | What it gives |
|---|---|
| Physical constants table | Speed of light, Planck, Avogadro, Boltzmann, etc. |
| Periodic table | Symbol, atomic number, mass, group, period, electronegativity, ionization energy |
| Resistor color code decoder | 4/5 band → ohm value |
| Ohm's law / power triangle | V, I, R, P given two inputs |
| SI prefix table | nano, micro, milli, kilo, mega, giga, etc. |
| Unit converter | Length, mass, temperature, pressure, energy, speed |
| Decibel converter | dB ↔ power/amplitude ratio |
| Wavelength ↔ frequency | For EM spectrum |
| EM spectrum table | Bands: radio, micro, IR, visible, UV, X-ray, gamma |

### Chemistry & Biology

| Bone | What it gives |
|---|---|
| Molecular weight calculator | Sum atomic masses from formula (e.g. H₂O → 18.015) |
| pH / pKa calculator | pH from [H⁺], Henderson-Hasselbalch |
| Amino acid table | 20 standard AAs: single-letter code, MW, pKa, properties |
| Codon table | DNA/RNA triplet → amino acid |
| Solubility rules | Common ionic compound solubility in water |
| Electrochemical series | Standard reduction potentials |

### Finance

| Bone | What it gives |
|---|---|
| Compound interest | FV given PV, r, n, t |
| Amortization schedule | Monthly payment + breakdown for any loan |
| Black-Scholes | Options pricing given S, K, T, r, σ |
| Present/future value | NPV, IRR (iterative but deterministic) |
| Mortgage / DSCR calculator | Debt service coverage ratio |
| Rule of 72 | Approximate doubling time |

### Geography & Codes

| Bone | What it gives |
|---|---|
| ISO 3166 country codes | Alpha-2, Alpha-3, numeric → country name |
| Country calling codes | +1, +44, etc. |
| Airport IATA/ICAO codes | Code → airport name + city |
| Timezone database (IANA) | City/region → UTC offset + DST rules |
| Haversine calculator | Great-circle distance between two lat/lon points |
| FIPS state/county codes | US-specific |

### Calendar & Time

| Bone | What it gives |
|---|---|
| Day-of-week calculator | Zeller's congruence — any date → weekday |
| Leap year checker | Pure arithmetic |
| Days between dates | Signed day count |
| Business day calculator | Add N business days to a date |
| ISO week number | Date → ISO 8601 week |
| Unix timestamp converter | Epoch ↔ human-readable |
| Holiday calendars | Static tables per country/year |
| Julian Date converter | Astronomical JD ↔ calendar date |

### Text & Encoding

| Bone | What it gives |
|---|---|
| Base64 encoder/decoder | Pure transform |
| Hex / URL / HTML entity encoder | Pure transform |
| Morse code table | Character ↔ dots/dashes |
| NATO phonetic alphabet | Letter → Alpha, Bravo, Charlie… |
| Unicode code point lookup | Character → U+XXXX + name |
| ASCII table | Code point → character + control name |
| Soundex / Metaphone | Phonetic encoding of a name |
| Luhn algorithm | Credit card number checksum validity |

### Networking & Computing

| Bone | What it gives |
|---|---|
| IP subnet / CIDR calculator | Network address, broadcast, host range, mask |
| IPv4 ↔ IPv6 mapping | Pure conversion |
| HTTP status code table | 200, 404, 502 → meaning |
| MIME type lookup | File extension → MIME type |
| ANSI escape code table | Terminal color/format codes |
| Big-O reference table | Algorithm name → time/space complexity |
| CRC / checksum calculators | CRC32, MD5 (of small static input) |

### Medicine & Health

| Bone | What it gives |
|---|---|
| BMI calculator | Weight + height → BMI category |
| BSA calculator | Body surface area (Mosteller, DuBois) |
| Pediatric dosing | mg/kg lookup by drug class |
| Glasgow Coma Scale | Three-component score → severity |
| Apgar score | Newborn 5-factor score |
| eGFR calculator | CKD-EPI / MDRD from creatinine + age + sex |
| Blood pressure categories | Systolic/diastolic → normal/elevated/hypertensive |

### Astronomy

| Bone | What it gives |
|---|---|
| Planetary data table | Mass, radius, distance from sun, orbital period |
| Moon phase calculator | Date → phase (new/quarter/full) |
| Sunrise / sunset | Lat + lon + date → times (pure math, no API) |
| Julian Date | Any calendar date ↔ JD |
| Star magnitude table | Common stars: Sirius, Vega, Polaris |

### Games & Puzzles

| Bone | What it gives |
|---|---|
| Scrabble / Words with Friends tile values | Letter → point value |
| Poker hand probability table | Hand type → probability |
| Dice probability calculator | NdM roll distribution |
| Chess opening ECO codes | Move sequence → opening name |

---

## Full Cell Pipeline (from Cell Survival Requirements PDF, pp. 82-90)

Every signal traverses this pipeline in order. No shortcuts.

```
Incoming signal (prompt / event)
  │
  ▼
[Membrane]         — gatekeeper: schema validity, auth, RBAC, rate limits,
                     prompt-injection check, relevance filter
  │  accept / reject
  ▼
[Cytoplasm]        — internal routing: load memory, attach context & priority
  │
  ▼
[Nucleus]          — gene selection: signal.type → matching GenomeModule
  │                  "what gene should handle this?"
  ▼
[Ribosome]         — execution decision: HOW to produce the protein
  │
  ├──▶ Precomputed path   (cache hit / known pattern — no LLM)
  ├──▶ Deterministic path (calculator, DB query, API — no LLM)
  └──▶ LLM path           (complex, ambiguous, creative, novel)
          │
          └──▶ Hybrid: LLM plans → deterministic tools execute (best pattern)
  │
  ▼
[Protein generated]  — result/output object
  │
  ▼
[Golgi]            — validate + shape before emission
  │                  schema check, content moderation, misfolding detection
  │  pass / repair / destroy
  ▼
[Membrane]         — serialize and emit to caller or next cell
```

**Three decision roles** (critical distinction):
| Organelle | Decides |
|---|---|
| Membrane | **If** to act (accept/reject at boundary) |
| Nucleus | **What** gene handles it (gene selection) |
| Ribosome | **How** to execute (LLM vs deterministic vs cached) |

---

## Osteoblasts & Deterministic Tool Access

Osteoblasts define the schemas that make deterministic routing possible. The ribosome doesn't guess — it pattern-matches the signal against Osteoblast-provisioned schemas.

**Example (calculator):**
```python
# Osteoblast previously defined:
CalculatorRequest  = { expression: str, precision: int | None }
CalculatorResponse = { result: float, method: "deterministic_calculator" }
```

When a signal matches `CalculatorRequest`, the ribosome says: *"This is schema-matched and bounded — use deterministic calculator. Do not use LLM."*

**Routing rule (from the PDF):**

| Signal character | Execution path |
|---|---|
| Exact, bounded, schema-matched | Deterministic tool |
| Ambiguous, semantic, creative, contextual | LLM |
| Needs reasoning then action | LLM plans → deterministic tools execute |

"Using an LLM for 1+1 is like using a whole brain to do a reflex. Wasteful and less reliable." (Cell Survival Requirements, p. 90)

---

## Misfolded Protein Taxonomy (Golgi's concern)

A misfolded protein is **any output that cannot safely and correctly do its job** — not just bad JSON.

| Type | Description | Example |
|---|---|---|
| **Structural** | Invalid schema, wrong types, missing required fields | `user_id: "abc"` when int expected |
| **Semantic** | Valid structure, wrong meaning | Recommends `refund` when user asked for `balance check` |
| **Execution** | Partial completion, inconsistent state | Step 1 charged user ✅, Step 2 DB update ❌ |
| **Context** | Ignores constraints, uses stale data, violates permissions | LLM uses deprecated schema |
| **Toxic** | Harmful, looping, security violations | Generates `delete all user data` or self-triggering signals |

### Misfolding handlers (biology → system)

| Biology | System component | Role |
|---|---|---|
| Chaperone proteins | Validation + auto-repair layer | Schema fix, LLM retry with constraints |
| Lysosome | Discard layer | Drop bad outputs, rollback actions, kill invalid signals |
| Peroxisome | Safety/policy layer | Block harmful actions, enforce policies, detect anomalies |

---

## New Organelles Not Yet Implemented

The PDF surfaces several organelles absent from the current codebase:

| Organelle | Role | Priority |
|---|---|---|
| **Golgi apparatus** | Validates + shapes protein output before emission | High — needed for safe outputs |
| **Lysosome** | Destroys misfolded/toxic proteins | High — needed for error recovery |
| **Peroxisome** | Safety policy enforcement | Medium — needed for governance |
| **Proteasome** | Deconstructs LLM Protein after use; deposits answer in Cytoplasm | High — core lifecycle |
| **Cytoplasm (typed)** | Shared cell working state; accumulates answers | High — core lifecycle |
| **Cytoskeleton** | Routes Answer Proteins to destinations within or between cells | High — core lifecycle |
| **Chaperones** | Repair misfolded proteins before destruction | Medium |

---

## Key Files

| What | File |
|---|---|
| `LlmProvider`, `ModelClass`, `ExecutionStrategy`, `GolgiDecision` enums | `preon_systems_cell/models.py` |
| `GenomeModule` (llm fields) | `preon_systems_cell/models.py` |
| `LlmProtein`, `AnswerProtein`, `ProteinDestination` | `preon_systems_cell/models.py` |
| `ProteasomeReceipt`, `CytoplasmEntry`, `CytoplasmSnapshot` | `preon_systems_cell/models.py` |
| `GolgiReport`, `RetrySignal`, `DestructionRecord` | `preon_systems_cell/models.py` |
| `CellWorkingState`, `Proteasome`, `GolgiApparatus` | `preon_systems_cell/organelles.py` |
| `Lysosome`, `Cytoskeleton` | `preon_systems_cell/organelles.py` |
| Provider adapters + `get_adapter()` | `preon_systems_cell/llm_providers.py` |
| `SignalClassifier` | `preon_systems_cell/engine.py` |
| `Ribosome._llm_execute()` | `preon_systems_cell/engine.py` |
| Optional deps (`[anthropic]`, `[openai]`, `[gemini]`, `[llm]`) | `pyproject.toml` |

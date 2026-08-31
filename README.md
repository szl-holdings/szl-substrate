> **SZL Holdings** · Doctrine v11 · Λ = Conjecture 1 (advisory, never "green"/theorem) · canonical [a-11-oy.com](https://a-11-oy.com)

# szl-substrate
<!-- szl:header v1 -->
<!-- badges: add this repo's CI / release / status badges here -->
[![org: szl-holdings](https://img.shields.io/badge/org-szl--holdings-black)](https://github.com/szl-holdings)
[![doctrine](https://img.shields.io/badge/doctrine-control%20before%20action%20%C2%B7%20evidence%20after-blue)](https://a-11-oy.com)

**Control before action. Evidence after.**

Part of the [szl-holdings](https://github.com/szl-holdings) estate ·
Product: [a-11-oy.com](https://a-11-oy.com) ·
Proof: [a11oy.net](https://a11oy.net)
<!-- /szl:header -->

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

**The installable shared substrate for [a11oy](https://github.com/szl-holdings/a11oy)
and [killinchu](https://github.com/szl-holdings/killinchu).**

Doctrine v11 LOCKED (749/14/163) · Λ = Conjecture 1 (advisory) · SLSA L1 honest · L2 roadmap.

## Why this exists (honest problem statement)

a11oy and killinchu currently ship **69 byte-identical `.py` files** copied into
both repositories (see [`MIGRATION.md`](MIGRATION.md) for the full list). Every
fix, security patch, or doctrine change has to be applied twice and kept in
perfect lockstep by CI drift guards (`shared-file-drift.yml`,
`shared-module-hash-lock.yml`). That duplication is the org's biggest source of
"fixed-in-one-app-only" risk.

`szl-substrate` is the single source of truth those files should live in. The
apps then `import` from the package instead of maintaining local copies.

## What is here today (honest scope)

Extraction is now **functionally complete for the movable universe**: **68 of
the 69** shared modules have been migrated into the package — **98.6%** of the
raw 69-file shared set (100% of the 68 modules that are actually movable; the
69th file, `serve.py`, is the per-app entrypoint and is L-tier "never move" by
design — see [`MIGRATION.md`](MIGRATION.md) for the full wave-by-wave
breakdown). **This was not a big-bang cutover.** The apps still keep their
local copies and import from the package only through a **guarded shim with
fallback to local**, so nothing breaks if the package is not installed in a
given environment.

The original proof-of-concept batch (the first 3 modules extracted, before the
remaining waves landed) established the pattern this package now uses
throughout:

| Module | What it does | Third-party deps | Coupling |
|--------|--------------|------------------|----------|
| `szl_calibration` | ECE / Brier calibration tracking + advisory response gate | none (pure-Python) | leaf |
| `szl_dsse` | DSSE (in-toto) ECDSA-P256-SHA256 signing/verify, cosign-compatible, UNSIGNED-honest fallback | `cryptography` | leaf (one lazy, guarded, optional hook into `szl_corpus_publish`) |
| `szl_brain` | Governed reasoning-brain scaffolding: Λ aggregator (advisory) + trust→tier policy | none (pure-Python) | leaf (one lazy, guarded, optional call into `szl_rag`) |

Every module in the package — all 68 — is **byte-identical** to the copy that
ships in a11oy and killinchu as of its extraction (verified with `cmp`).
Extraction did not change a single line of module logic. See
[`MIGRATION.md`](MIGRATION.md) for the full ranked table of all 69 files and
which wave moved each one.

## Absorbed modules

szl-substrate is the designated canonical absorber for three archived repos —
the archived repos point here (repo-level metadata, set at archive time
2026-08-29: "Canonical: szl-holdings/szl-substrate"):

| Archived repo | What it owned | Pointer evidence |
|---|---|---|
| [`vsp-otel`](https://github.com/szl-holdings/vsp-otel) | Λ-signed OpenTelemetry exporter (Layer-4 Λ-gate exporter) for SZL audit fibers | Archived 2026-08-29; repo description names szl-substrate canonical |
| [`szl-telemetry`](https://github.com/szl-holdings/szl-telemetry) | Daily public-API telemetry snapshots of the SZLHOLDINGS Hugging Face estate | Archived 2026-08-29; repo description names szl-substrate canonical |
| [`szl-mesh`](https://github.com/szl-holdings/szl-mesh) | Doctrine-pinned mesh coordination — DSSE receipt chains over CRDT fleet state | Archived 2026-08-29; repo description names szl-substrate canonical |

## Install

```bash
pip install -e ".[dev]"   # from source (this repo)
```

## Quick start

```python
from szl_substrate import szl_dsse, szl_calibration, szl_brain

# 1. DSSE signing — honest UNSIGNED fallback when no cosign key is present
env = szl_dsse.sign_payload({"model": "a11oy-governed-engine", "score": 0.98})
#   env["signed"] is False and env["honesty"] explains WHY — a signature is
#   NEVER fabricated. With SZL_COSIGN_PRIVATE_PEM set, env["signed"] is True and
#   the ECDSA-P256-SHA256 signature is cosign-verifiable.

# 2. Calibration — ECE / Brier (pure-Python, no numpy)
ece = szl_calibration.expected_calibration_error([0.9, 0.8], [True, False])

# 3. Λ aggregator (advisory — Conjecture 1, never "proven")
tier = szl_brain.pick_tier([0.99, 0.98, 0.97])   # -> high-trust fast tier
```

## The guarded-import pattern (how the apps adopt this)

The apps do **not** delete their local copy in this pass. They import through a
shim that prefers the package and falls back to the vendored local module:

```python
try:
    from szl_substrate import szl_dsse as _dsse          # prefer the package
    _dsse_source = "szl-substrate"
except Exception:                                         # pragma: no cover
    import szl_dsse as _dsse                              # fall back to local copy
    _dsse_source = "local-vendored"
```

This proves the extraction pattern end-to-end **without risking either running
application**. See the proof-of-concept PR referenced in `MIGRATION.md`.

## The Ouroboros loop (what the shared agent-loop modules are)

Beyond the three guarded-import extraction modules above, `src/szl_substrate/` also
carries the estate's shared **governed agent-loop** modules that a11oy and killinchu run
byte-identically:

| Module | What it is (from its own header) |
|--------|----------------------------------|
| `szl_agentic_loop.py` | "THE OPERATIONAL GOVERNED AGENT LOOP" — makes the advertised **RAG → tool-call → policy/trust gate → signed receipt** loop REAL and CLICKABLE end-to-end, with a per-hop trace and a re-verifiable chained, signed receipt. |
| `a11oy_agent_loop.py` | "a GENUINELY agentic, governed finite-state machine": `INTAKE → PLAN → RETRIEVE → ACT → OBSERVE → VERIFY → (REFLECT → ACT) → FINALIZE`, with bounded guards `max_steps=12`, `max_reflect_depth=3`, Λ-floor `0.90` **fail-closed**, and a conformal floor `1/(n+1)` (trust is never 100%). |

These are the estate's concrete instances of the **Ouroboros bounded-recursion loop**.
The canonical definition is the receipt-closed kernel
[`szl-holdings/ouroboros` → `src/loop-kernel.ts`](https://github.com/szl-holdings/ouroboros/blob/main/src/loop-kernel.ts)
(`runLoop`): *bounded recursion with measurable convergence* that MUST terminate on one
of `converged | consistent | aborted | budgetExhausted` and emits a governance receipt
— **the trace is the product**.

**Metaphor (doctrine, not math):** `receipts.in ≡ receipts.out` — the snake eats its own
tail; each run's signed receipt is fed back as an auditable input.

**Honesty (Doctrine v11):** every loop here is **bounded and terminating** (explicit step
budgets, fail-closed gates) — there is **no** perpetual-motion or zero-cost claim. Λ is
**Conjecture 1** (advisory), never a proven theorem.

## Honesty labels

- **Λ = Conjecture 1** — advisory only. Never rendered as "green"/"proven"/a theorem.
- **Signed receipts** — real DSSE in a Space with a cosign key; an explicit,
  clearly-labelled **UNSIGNED** marker otherwise. No fabricated signatures, ever.
- **SLSA** — L1 honest, L2 roadmap. No L2/L3 claim is made for this package.
- **Trust ceiling 0.97.**

## Sources cited in code

- DSSE PAE / envelope — secure-systems-lab/dsse: <https://github.com/secure-systems-lab/dsse>
- Sigstore Cosign key-based blob signing — <https://docs.sigstore.dev/cosign>
- ECE / Brier calibration — arXiv:2505.15437 and arXiv:2605.21566 (baked into `szl_calibration`)
- Λ aggregator (weighted geometric mean, advisory gate) — szl-holdings/lutar-lean; Λ = Conjecture 1

## License

Apache-2.0 — see [LICENSE](LICENSE). © 2026 Lutar, Stephen P. — SZL Holdings.

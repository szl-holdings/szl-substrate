> **SZL Holdings** · Doctrine v11 · Λ = Conjecture 1 (advisory, never "green"/theorem) · canonical [a-11-oy.com](https://a-11-oy.com)

# szl-substrate
<!-- szl:header v1 -->
<!-- Native identity: szl-brand@4309f6fce89179331b0b3ed8c99494e76c5be256; Orbit v2 icon. -->
<p>
  <a href="https://github.com/szl-holdings">
    <img src="https://raw.githubusercontent.com/szl-holdings/szl-brand/4309f6fce89179331b0b3ed8c99494e76c5be256/kit/logos/orbit-v2/suite/szl-icon-32.svg" alt="SZL Holdings — Orbit v2" width="32" height="32" />
  </a>
</p>

**Control before action. Evidence after.**

[Product](https://a-11-oy.com) · [Proof](https://a11oy.net) · [GitHub organization](https://github.com/szl-holdings)
<!-- /szl:header -->

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

**The installable shared substrate for [a11oy](https://github.com/szl-holdings/a11oy)
and [killinchu](https://github.com/szl-holdings/killinchu).**

Doctrine v11 LOCKED (749/14/163) · Λ = Conjecture 1 (advisory) · SLSA L1 honest · L2 roadmap.

## Why this exists (honest problem statement)

When this package started (July 2026), a11oy and killinchu shipped **69
byte-identical `.py` files** copied into both repositories (see
[`MIGRATION.md`](MIGRATION.md) for the full list). Every fix, security patch, or
doctrine change has to be applied twice and kept in lockstep by the apps' CI
drift guards (`shared-file-drift.yml` in both apps, `shared-module-hash-lock.yml`
in a11oy). That duplication is the org's biggest source of
"fixed-in-one-app-only" risk.

`szl-substrate` is the single source of truth those files should live in, so
the apps can `import` from the package instead of maintaining local copies.
That end state is not reached yet: see [Parity with the apps
today](#parity-with-the-apps-today).

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

Every module in the package — all 68 — was **byte-identical** to the copy
that shipped in a11oy and killinchu at the time of its extraction (verified with
`cmp`). Extraction did not change a single line of module logic. See
[`MIGRATION.md`](MIGRATION.md) for the full ranked table of all 69 files and
which wave moved each one.

### Parity with the apps today

The copies have moved independently since extraction. Fixes landed here that
the apps' vendored copies do not carry (for example the DSSE and conformal
boundaries below), and the apps changed their copies together without updating
this package. Measured on 2026-11-06 with `tools/app_parity.py`, comparing each
package module with the app's top-level copy, against a11oy@c524ff3a and
killinchu@ee1a31cd:

| Comparison | Byte-identical modules |
|---|---|
| package vs a11oy | 23 of 68 |
| package vs killinchu | 24 of 68 |
| a11oy vs killinchu | 61 of 68 |

Neither app installs this package: the `szl-substrate @ git+…` line is
commented out in both apps' `requirements.txt`, so their guarded imports
resolve to the vendored copies. This package is the shared source the apps are
meant to import, not the code they run today. Re-measure against your own
checkouts with:

```bash
python tools/app_parity.py a11oy=../a11oy killinchu=../killinchu
```

## Absorbed modules

On 2026-08-29 three repos were archived with repo-level metadata naming
szl-substrate as canonical. The September 2026 archive-portfolio v2 review
([`.github/docs/ARCHIVE_PORTFOLIO_V2.md`](https://github.com/szl-holdings/.github/blob/main/docs/ARCHIVE_PORTFOLIO_V2.md))
restored two of them as active, standalone source owners. Only one remains
absorbed here:

| Repo | What it owns | Status (GitHub metadata, re-checked 2026-10-13) |
|---|---|---|
| [`szl-telemetry`](https://github.com/szl-holdings/szl-telemetry) | Daily public-API telemetry snapshots of the SZLHOLDINGS Hugging Face estate | **Archived** 2026-08-29; repo description names szl-substrate canonical |
| [`vsp-otel`](https://github.com/szl-holdings/vsp-otel) | OTLP collector, signed-span exporter and Helm package | **Active, not archived.** Restored by archive-portfolio v2; its README declares itself the canonical OTel package. Not absorbed into szl-substrate |
| [`szl-mesh`](https://github.com/szl-holdings/szl-mesh) | Disconnected-state CRDT convergence / UDS mesh coordination | **Active, not archived.** Restored by archive-portfolio v2; its README declares itself the active mesh repo. Not absorbed into szl-substrate |

The 2026-08-29 absorption of `vsp-otel` and `szl-mesh` is historical: no
planned extraction of either into this package has been cut over or
deployed. References elsewhere in this package to `szl-mesh` (for example the
`szl-mesh:v0.4.0` UDS bundle in `szl_uds_portability.py`) point at that
standalone repo's artifacts.

## Install

szl-substrate is not on PyPI yet: no release has been cut (`publish-pypi.yml`
publishes only from a GitHub Release). Install from a clone:

```bash
python -m pip install -e .          # core: cryptography only
python -m pip install -e ".[test]"  # + pytest and the web extra, to run the tests
```

Optional runtime extras, named after the modules that need them: `web`
(fastapi, starlette, httpx), `rag` (httpx, numpy), `khipu` (lmdb), `sigstore`,
and `all`. `import szl_substrate` needs only the core dependency.

## Tests

```bash
python -m pip install -e ".[test]"
python -m pytest -q
```

`ci.yml` runs the suite on CPython 3.10-3.14 with dependencies installed from
the hash-locked `requirements/ci/test.txt`. `base-python-ci.yml` runs ruff
(E9/F) and the suite on 3.11 and 3.12 from `requirements/ci/base.txt`, without
the web extra, so the tests that need fastapi/starlette skip there by design.

## Quick start

```python
from szl_substrate import szl_dsse, szl_calibration, szl_brain

# 1. DSSE signing — honest UNSIGNED fallback when no cosign key is present
env = szl_dsse.sign_payload({"model": "a11oy-governed-engine", "score": 0.98})
#   env["signed"] is False and env["honesty"] explains WHY — a signature is
#   NEVER fabricated. With SZL_COSIGN_PRIVATE_PEM set, env["signed"] is True and
#   the ECDSA-P256-SHA256 signature is cosign-verifiable.
#   szl_dsse.verify_envelope(env) checks against the org key embedded in
#   szl_dsse (the key published at szl-holdings/.github/cosign.pub); an
#   envelope signed with any other key reports verified=False.

# 2. Calibration — ECE / Brier (pure-Python, no numpy)
ece = szl_calibration.expected_calibration_error([0.9, 0.8], [True, False])

# 3. Λ aggregator (advisory — Conjecture 1, never "proven")
tier = szl_brain.pick_tier([0.99, 0.98, 0.97])   # -> high-trust fast tier
```

`szl_conformal.conformal_quantile` requires every calibration score to represent
a finite `1-p` value in `[0, 1]`. A malformed, boolean, non-finite, or out-of-range
score makes the entire pool fall back to `q_hat = 1.0`, so `conformal_set` retains
the full label space. Invalid evidence is neither replaced with zero nor dropped.
Finite numeric strings keep their existing conversion behavior. This package
repair does not update app-local fallback copies or attest to their deployment.

### DSSE numeric boundary

New `szl_dsse.canonical_json` / `sign_payload` calls reject `NaN`, positive
infinity, and negative infinity, including nested values and numeric keys,
with `ValueError` before accessing signing material. Finite payloads retain
their previous JSON and PAE bytes; absent keys still produce an honest unsigned
envelope for valid payloads.

`verify_envelope` continues to verify the original signed bytes, without
re-serializing them or invalidating historical signatures. Its `verified`
field is a cryptographic verdict, **not** receipt-schema or numeric-evidence
admission. Historical non-finite payloads still require semantic validation
by their consumer. This package repair does not update the app-local fallback
copies or establish that a running app has adopted the repaired package.

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
carries the estate's shared **governed agent-loop** modules. a11oy's and killinchu's
copies of these two files are byte-identical to each other, and both now differ from
the package copies described here (see [Parity with the apps
today](#parity-with-the-apps-today)):

| Module | What it is (from its own header) |
|--------|----------------------------------|
| `szl_agentic_loop.py` | "THE OPERATIONAL GOVERNED AGENT LOOP" — makes the advertised **RAG → tool-call → policy/trust gate → signed receipt** loop REAL and CLICKABLE end-to-end, with a per-hop trace and a re-verifiable chained, signed receipt. |
| `a11oy_agent_loop.py` | "a GENUINELY agentic, governed finite-state machine": `INTAKE → PLAN → RETRIEVE → ACT → OBSERVE → VERIFY → (REFLECT → ACT) → FINALIZE`, with bounded guards `max_steps=12`, `max_reflect_depth=3`, Λ-floor `0.90` **fail-closed**, and a conformal floor `1/(n+1)` (trust is never 100%). |

These are the estate's concrete instances of the **Ouroboros bounded-recursion loop**.
The kernel is `runLoop`, maintained as the vendored copy in
[`szl-holdings/platform` → `packages/unified-kernel/src/loop/vendor_ouroboros/loop-kernel.ts`](https://github.com/szl-holdings/platform/blob/main/packages/unified-kernel/src/loop/vendor_ouroboros/loop-kernel.ts):
*bounded recursion with measurable convergence* that MUST terminate on one of
`converged | consistent | aborted | budgetExhausted` — **the trace is the product**.
It was recovered from `szl-holdings/ouroboros` (`src/loop-kernel.ts`), which is now
archived; that original also emitted a governance receipt, which the platform copy
does not.

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

The operational-readiness reader compares the deployment's reported commit
against the captured repository HEAD. Build parity is `current` only when
those identities match. Otherwise it reports `behind`, `ahead`, `diverged`,
or `unknown`, retaining repository-only and deployment-only commit counts.
Unavailable, invalid, or contradictory comparison counts remain `unknown`;
cached readings retain their cache label. These comparisons describe reported
source identities and do not independently attest deployed bytes.

## Proof boundary

What this repository's CI shows: `import szl_substrate` works with only the core
dependency installed; the unit tests pass on Linux on CPython 3.10-3.14 with the web
extra (`ci.yml`) and on 3.11 and 3.12 without it (`base-python-ci.yml`); the
dependency contract, the hash-locked CI requirements and the third-party asset
notices are checked by tests.

What it does **not** show:

- that a11oy, killinchu or any Hugging Face Space runs this package (neither app
  installs it; see [Parity with the apps today](#parity-with-the-apps-today));
- that the package and the app copies agree beyond the dated snapshot above;
- that any receipt was signed with the org key: CI has no signing key, and the
  signing tests use throwaway keys or the UNSIGNED path;
- SLSA L2 or higher provenance, which is not claimed.

## Sources cited in code

- DSSE PAE / envelope — secure-systems-lab/dsse: <https://github.com/secure-systems-lab/dsse>
- Sigstore Cosign key-based blob signing — <https://docs.sigstore.dev/cosign>
- ECE / Brier calibration — arXiv:2505.15437 and arXiv:2605.21566 (baked into `szl_calibration`)
- Λ aggregator (weighted geometric mean, advisory gate) — szl-holdings/lutar-lean; Λ = Conjecture 1

## License

Apache-2.0 — see [LICENSE](LICENSE). © 2026 Lutar, Stephen P. — SZL Holdings.

The fonts and the globe image embedded in `src/szl_substrate/_vendor_blobs.py`
are third-party works under the MIT License and the SIL Open Font License 1.1;
see [NOTICE-THIRD-PARTY.md](NOTICE-THIRD-PARTY.md) for their provenance and
license texts.

Estate on Hugging Face: models, datasets and Spaces are published under the [SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS) org.

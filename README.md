> **SZL Holdings** · Doctrine v11 · Λ = Conjecture 1 (advisory, never "green"/theorem) · canonical [a-11-oy.com](https://a-11-oy.com)

# szl-substrate

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

This is the **first, deliberately small** extraction pass — **3 of 69** modules,
chosen for lowest coupling and highest shared value. **This is not a big-bang
cutover.** The apps still keep their local copies and import from the package
only through a **guarded shim with fallback to local**, so nothing breaks if the
package is not installed in a given environment.

| Module | What it does | Third-party deps | Coupling |
|--------|--------------|------------------|----------|
| `szl_calibration` | ECE / Brier calibration tracking + advisory response gate | none (pure-Python) | leaf |
| `szl_dsse` | DSSE (in-toto) ECDSA-P256-SHA256 signing/verify, cosign-compatible, UNSIGNED-honest fallback | `cryptography` | leaf (one lazy, guarded, optional hook into `szl_corpus_publish`) |
| `szl_brain` | Governed reasoning-brain scaffolding: Λ aggregator (advisory) + trust→tier policy | none (pure-Python) | leaf (one lazy, guarded, optional call into `szl_rag`) |

Every module here is **byte-identical** to the copy that ships in a11oy and
killinchu as of extraction (verified with `cmp`). Extraction did not change a
single line of module logic.

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

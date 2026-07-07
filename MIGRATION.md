# MIGRATION.md — extracting the 69 shared modules into `szl-substrate`

> **Goal:** eliminate the 69 byte-identical `.py` files currently duplicated
> across [a11oy](https://github.com/szl-holdings/a11oy) and
> [killinchu](https://github.com/szl-holdings/killinchu) by moving them into
> this single installable package — **without a big-bang cutover and without
> breaking either running application.**

## Method (how this ranking was produced)

Both repos were cloned fresh. Each of the 69 files (`/tmp/shared_py.txt`) was
parsed with Python's `ast` to compute, for every module:

- **intra-shared imports** — imports of *other* modules in the 69-file set
  (creates a move-ordering dependency: a dependency must move first or be
  shimmed);
- **app-specific imports** — imports of modules NOT in the shared set, split
  into **UNGUARDED** (module-level `import` that would raise `ImportError` if the
  dependency is absent) vs **lazy/guarded** (inside a `def`/`try`, degrades
  gracefully);
- **reverse coupling** — how many *app* files and *shared* files import the
  module (its "blast radius" = number of guarded shims an app-side adoption PR
  must touch).

Byte-identity between the two repos was verified with `cmp`. **4 files have
DRIFTED** and are no longer identical (`_vendor_blobs.py`, `serve.py`,
`szl_be_hardening.py`, `szl_evidence_research.py`) — those must be reconciled to
a single canonical version *before* extraction.

## Tier definitions (extraction-safety)

| Tier | Meaning | Move strategy |
|------|---------|---------------|
| **S** — Safe | Pure leaf: imports no other local module. Small reverse-coupling. | Move first. Only needs a guarded shim in each call site. |
| **M** — Medium | Imports only *other shared* modules (move after its deps), and/or is a hub imported by ≥4 shared modules, and/or has drifted between repos, and/or has *lazy/guarded* app-specific imports that degrade gracefully. | Move in dependency order; reconcile drift first. |
| **L** — Large | `serve.py` (the app entrypoint — **never move**; it wires 37 shared + 120 app modules), or a module with a very large blast radius (≥12 call sites across both apps) that is technically source-safe but requires broad, carefully-coordinated shim rollout. | Move last / incrementally; land the guarded shim in a few call sites first (the POC pattern), then widen. |

**Distribution: 36 S · 30 M · 3 L.** The only truly hard file is `serve.py`; the
two other **L** entries (`szl_dsse`, `szl_joules_truth`) are source-clean leaves
whose difficulty is purely their wide fan-out.

## What this pass actually did (honest scope)

- **3 modules extracted** into `src/szl_substrate/`, byte-identical to the app
  copies at extraction time:
  - `szl_calibration.py` (**S** — pure-Python leaf; the ideal first-mover);
  - `szl_brain.py` (**M** — a shared hub used by 4 shared modules; its one intra
    import, `szl_rag`, is lazy + guarded);
  - `szl_dsse.py` (**L** — deliberately included to prove the guarded-shim
    pattern on the **highest-value, widest-used** module: 23 app + 10 shared
    importers. Its one app-specific import, `szl_corpus_publish`, is lazy +
    guarded).
- **The apps are NOT rewired wholesale.** The proof-of-concept PR on a11oy
  imports `szl_calibration` and `szl_dsse` from the package **only where it is
  safe**, each behind a `try: from szl_substrate import … except: import …local`
  shim. If the package is absent, the app falls back to its local copy and keeps
  working. Nothing is deleted from the apps in this pass.

### Wave-S batch (this pass) — 10 more S-tier leaves extracted

Continuing the proven POC pattern (a11oy #735 merged), **10 additional S-tier
leaf modules** were extracted into `src/szl_substrate/`, byte-identical to the
app copies at extraction time. Every one satisfies the *safest* selection
criteria: **0 app-file importers + ≤1 shared-file importer, no local (shared-set)
imports, and byte-identical between a11oy and killinchu (`cmp` verified).** None
is a drifted file, none is M/L:

| Module | Tier | Blast radius | Module-level deps |
|--------|------|--------------|-------------------|
| `szl_allodial.py` | S | 0 app + 1 shared | stdlib only |
| `a11oy_hf_assets.py` | S | 0 app + 1 shared | stdlib only |
| `szl_chain_of_title.py` | S | 0 app + 1 shared | stdlib only |
| `szl_conjecture_factory.py` | S | 0 app + 1 shared | stdlib only |
| `szl_connectors_serve.py` | S | 0 app + 1 shared | **unguarded `import szl_connectors`** → NOT eager-imported in `__init__`; import directly |
| `szl_ecosystem_routes.py` | S | 0 app + 1 shared | stdlib only |
| `szl_entanglement.py` | S | 0 app + 1 shared | stdlib only |
| `szl_metrics_prom.py` | S | 0 app + 1 shared | stdlib only |
| `szl_neuroplasticity.py` | S | 0 app + 1 shared | stdlib only |
| `szl_scaling.py` | S | 0 app + 1 shared | stdlib only |

  9 of the 10 are pure-stdlib at module scope and are eager-imported in
  `szl_substrate/__init__.py`. `szl_connectors_serve` carries an **unguarded
  module-level `import szl_connectors`**, so it is intentionally *excluded* from
  eager import and is instead imported directly
  (`from szl_substrate import szl_connectors_serve`) only where `szl_connectors`
  is present — the package stays importable everywhere.

- **a11oy repoint (guarded, no self-merge).** The companion a11oy PR repoints
  each of these 10 `import X as _alias` call sites (all already inside
  `try/except` blocks in `serve.py` / `organs`) to prefer the package with a
  nested guarded fallback:
  `try: from szl_substrate import X as _alias  except Exception: import X as
  _alias`. If the package is absent the app falls back to its local vendored
  copy; the outer `except` remains the final safety net. **Nothing is deleted
  from the apps; killinchu is untouched, so the a11oy↔killinchu drift guard stays
  green.**

## Recommended rollout order

1. **Reconcile the 4 drifted files** to one canonical copy (out of band).
2. **Land all 36 S modules** into the package (leaves — no ordering constraints),
   with per-call-site guarded shims in each app.
3. **Land the 30 M modules in dependency order** — a module moves only after
   every shared module it imports has moved. Suggested waves:
   - Wave M-1: modules importing only `szl_dsse` (already here): `szl_ken`,
     `szl_provenance`, `szl_qhawaq`, `operator_shell_v4`, `szl_warhacker_aliases`.
   - Wave M-2: modules importing `szl_rag`/`szl_brain` (`szl_llm_registry`, then
     `szl_alloy_models`), and `szl_restraint`→`szl_joules_truth` chain.
   - Wave M-3: multi-dependency composites (`szl_agentic_loop`, `a11oy_org_rag`,
     `a11oy_code_engine`, `szl_unay_routes`).
4. **`szl_joules_truth` (L)** — move once its 11 app + 2 shared shims are staged.
5. **`serve.py` (L)** — never extracted. It is the app entrypoint; it stays in
   each app and imports the shared modules from the package.

Only after a module has "baked" behind the guarded shim in production should the
local copy be deleted and the shim simplified to a direct package import. Until
then the drift-guard CI (`shared-file-drift.yml`, `shared-module-hash-lock.yml`)
keeps the local copies honest.

## Full ranked table (all 69 files)

Legend: `used by N app + M shared file(s)` = reverse coupling (blast radius).
**Bold** flags UNGUARDED app coupling or drift. ✅ = moved in this pass.

| # | File | Tier | Deps note |
|---|------|------|-----------|
| 1 | `a11oy_hf_assets.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 2 | `a11oy_uds_portability_nav.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 3 | `a11oy_waqay_nav.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 4 | `a11oy_yupay_nav.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 5 | `szl_allodial.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 6 | `szl_chain_of_title.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 7 | `szl_conjecture_factory.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 8 | `szl_connector_mcp.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 9 | `szl_connectors_serve.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** (unguarded `import szl_connectors`; not eager-imported) |
| 10 | `szl_contracting.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 11 | `szl_deepdive_gaps.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 12 | `szl_ecosystem_routes.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 13 | `szl_entanglement.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 14 | `szl_formula_wiring.py` | **S** | leaf: no local imports; used by 0 app + 2 shared file(s) |
| 15 | `szl_khipu_lmdb.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) |
| 16 | `szl_khipu_replicate.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) |
| 17 | `szl_logging.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 18 | `szl_mbse_nav.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 19 | `szl_metrics_prom.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 20 | `szl_neuroplasticity.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 21 | `szl_readiness.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) |
| 22 | `szl_rosie_companion.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) |
| 23 | `szl_scaling.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (Wave-S)** |
| 24 | `szl_uds_portability.py` | **S** | leaf: no local imports; used by 0 app + 0 shared file(s) |
| 25 | `szl_unified_formulas.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) |
| 26 | `a11oy_mcp_client.py` | **S** | leaf: no local imports; used by 1 app + 0 shared file(s) |
| 27 | `szl_calibration.py` | **S** | leaf: no local imports; used by 1 app + 1 shared file(s) ✅ **MOVED (this pass)** |
| 28 | `szl_quantum_bio.py` | **S** | leaf: no local imports; used by 1 app + 1 shared file(s) |
| 29 | `szl_unay.py` | **S** | leaf: no local imports; used by 1 app + 1 shared file(s) |
| 30 | `szl_codename_gate.py` | **S** | leaf: no local imports; used by 2 app + 0 shared file(s) |
| 31 | `szl_conformal.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 32 | `szl_cuas_formulas.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 33 | `szl_hf_bucket.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 34 | `szl_khipu_consensus.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 35 | `szl_v4_fleet.py` | **S** | leaf: no local imports; used by 2 app + 0 shared file(s) |
| 36 | `szl_formulas.py` | **S** | leaf: no local imports; used by 5 app + 1 shared file(s) |
| 37 | `operator_shell_v4.py` | **M** | imports shared: szl_dsse; used by 0 app + 1 shared file(s) |
| 38 | `szl_alloy_models.py` | **M** | imports shared: szl_llm_registry; used by 0 app + 1 shared file(s) |
| 39 | `szl_anatomy_routes.py` | **M** | imports shared: szl_formulas; used by 0 app + 2 shared file(s) |
| 40 | `szl_rag.py` | **M** | imports shared: szl_brain; used by 0 app + 3 shared file(s) |
| 41 | `szl_sapa_patch.py` | **M** | imports shared: szl_sapa; used by 0 app + 0 shared file(s) |
| 42 | `szl_spaces_proxy.py` | **M** | imports shared: serve; used by 0 app + 1 shared file(s) |
| 43 | `szl_spaces_surface.py` | **M** | imports shared: serve; used by 0 app + 1 shared file(s) |
| 44 | `szl_warhacker_aliases.py` | **M** | imports shared: szl_dsse; used by 0 app + 1 shared file(s) |
| 45 | `test_szl_hf_bucket.py` | **M** | imports shared: szl_hf_bucket; used by 0 app + 0 shared file(s) |
| 46 | `szl_brain.py` | **M** | imports shared: szl_rag; used by 1 app + 4 shared file(s) ✅ **MOVED (this pass)** |
| 47 | `szl_ken.py` | **M** | imports shared: szl_dsse; used by 1 app + 1 shared file(s) |
| 48 | `szl_llm_registry.py` | **M** | imports shared: szl_rag; used by 1 app + 3 shared file(s) |
| 49 | `szl_provenance.py` | **M** | imports shared: szl_dsse; used by 1 app + 1 shared file(s) |
| 50 | `szl_qhawaq.py` | **M** | imports shared: szl_dsse; used by 1 app + 0 shared file(s) |
| 51 | `szl_sapa.py` | **M** | imports shared: szl_dsse, szl_energy_sovereign; used by 0 app + 1 shared file(s) |
| 52 | `szl_restraint.py` | **M** | imports shared: szl_joules_truth; used by 4 app + 5 shared file(s) |
| 53 | `szl_mbse_cosim.py` | **M** | imports shared: szl_dsse, szl_restraint; used by 1 app + 0 shared file(s) |
| 54 | `szl_waqay.py` | **M** | imports shared: szl_dsse, szl_restraint; used by 1 app + 1 shared file(s) |
| 55 | `szl_yupay.py` | **M** | imports shared: szl_dsse, szl_restraint; used by 1 app + 0 shared file(s) |
| 56 | `a11oy_code_engine.py` | **M** | imports shared: szl_agentic_loop, szl_llm_registry; used by 2 app + 1 shared file(s) |
| 57 | `_vendor_blobs.py` | **M** | leaf: no local imports; used by 0 app + 1 shared file(s); **DRIFTED between repos — reconcile first** |
| 58 | `a11oy_autoreview.py` | **M** | imports shared: szl_calibration, szl_conformal, szl_restraint; used by 0 app + 1 shared file(s) |
| 59 | `szl_evidence_research.py` | **M** | leaf: no local imports; used by 0 app + 1 shared file(s); **DRIFTED between repos — reconcile first** |
| 60 | `szl_unay_routes.py` | **M** | imports shared: szl_khipu_lmdb, szl_khipu_replicate, szl_unay; used by 0 app + 1 shared file(s) |
| 61 | `a11oy_org_rag.py` | **M** | imports shared: szl_brain, szl_rag, szl_waqay; used by 3 app + 1 shared file(s) |
| 62 | `a11oy_agent_loop.py` | **M** | imports shared: szl_brain; imports app-specific (lazy/guarded): a11oy_active_flux_router; used by 2 app + 0 shared file(s) |
| 63 | `szl_live_wires.py` | **M** | imports app-specific (lazy/guarded): szl_jack, szl_wire; used by 0 app + 1 shared file(s) |
| 64 | `szl_energy_sovereign.py` | **M** | imports shared: szl_joules_truth; imports app-specific (lazy/guarded): a11oy_code_orchestrator, szl_energy_operator; used by 4 app + 3 shared file(s) |
| 65 | `szl_be_hardening.py` | **M** | imports shared: szl_dsse; imports app-specific (lazy/guarded): szl_cheapest_watt, szl_energy_operator; used by 0 app + 1 shared file(s); **DRIFTED between repos — reconcile first** |
| 66 | `szl_agentic_loop.py` | **M** | imports shared: szl_anatomy_routes, szl_energy_sovereign, szl_formula_wiring, szl_khipu_consensus; imports app-specific (lazy/guarded): szl_ltc_dynamics, szl_sgh_scheduler; used by 1 app + 2 shared file(s) |
| 67 | `szl_joules_truth.py` | **L** | leaf: no local imports; used by 11 app + 2 shared file(s) |
| 68 | `szl_dsse.py` | **L** | imports app-specific (lazy/guarded): szl_corpus_publish; used by 23 app + 10 shared file(s) ✅ **MOVED (this pass)** |
| 69 | `serve.py` | **L** | imports 37 shared modules; imports 120 app-specific modules (lazy/guarded); used by 1 app + 2 shared file(s); **DRIFTED between repos — reconcile first** |

---

Doctrine v11 LOCKED (749/14/163) · Λ = Conjecture 1 (advisory) · SLSA L1 honest ·
L2 roadmap · Apache-2.0.

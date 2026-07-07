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

Byte-identity between the two repos was verified with `cmp`. **4 files had
DRIFTED** and were no longer identical (`_vendor_blobs.py`, `serve.py`,
`szl_be_hardening.py`, `szl_evidence_research.py`). **These have now been
reconciled** (Wave-E dev 5) — see
[Drift reconciliation](#drift-reconciliation-wave-e-dev-5) below. Three were
reconciled to a single canonical copy and extracted into the package; `serve.py`
is the per-app entrypoint and is **not** a shared module (its divergence is
legitimate), so it stays per-app and is reclassified accordingly.

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

### M-tier wave 1 (this pass) — 7 M-tier modules extracted (deps already moved)

With the S-tier leaves and the 3 reconciled drift files in the package, the first
safe **M-tier** batch was extracted. Selection is strictly dependency-ordered and
drift-safe: **every module's shared-module dependency is ALREADY in the package**,
and each file is **byte-identical between a11oy and killinchu** (`cmp`-verified,
none is a drifted/allow-listed file), so each is extracted byte-for-byte. Their
`szl_dsse` / `szl_rag` / `szl_joules_truth` uses are lazy+guarded inside functions
and degrade gracefully, so no unmoved dependency is required at module scope.

| Module | Tier | Shared dep (status) | Import mode in package |
|--------|------|---------------------|------------------------|
| `szl_ken.py` | M | `szl_dsse` ✅ moved (lazy) | eager (pure-stdlib at module scope) |
| `szl_qhawaq.py` | M | `szl_dsse` ✅ moved (lazy) | eager (pure-stdlib at module scope) |
| `szl_restraint.py` | M | `szl_joules_truth` (lazy+guarded, degrades) | eager (pure-stdlib at module scope) |
| `szl_provenance.py` | M | `szl_dsse` ✅ moved (**module-level**) | import-directly (not eager) |
| `szl_warhacker_aliases.py` | M | `szl_dsse` (lazy) | import-directly (module-level `fastapi`) |
| `operator_shell_v4.py` | M | `szl_dsse` (lazy) | import-directly (module-level `fastapi`) |
| `szl_llm_registry.py` | M | `szl_rag` (lazy+guarded, degrades) | import-directly (module-level `fastapi`) |

3 are eager-imported from `szl_substrate/__init__.py` (pure-stdlib at module
scope). The other 4 carry an **unguarded module-level import** (`szl_provenance`
→ `szl_dsse`; the other three → `fastapi`) and are therefore **excluded from
eager import** and imported directly (`from szl_substrate import X`) only where
that dependency is present — exactly the pattern already used for
`szl_connectors_serve`. This keeps `import szl_substrate` working everywhere
(verified: the package still imports with `fastapi` absent). Coverage:
`tests/test_mtier_wave1.py` (full suite green).

**a11oy repoint (guarded, no self-merge).** The companion a11oy PR repoints each
of these call sites to prefer the package with a nested guarded fallback
(`try: from szl_substrate import X … except Exception: import X …local`). If the
package is absent the app falls back to its local vendored copy. **Nothing is
deleted from the apps; killinchu is untouched and the shared source surface is
unchanged, so the a11oy↔killinchu drift guard stays green.** `serve.py` and any
module whose deps have not moved were NOT touched.

### M-tier wave 2 (this pass) — 6 M-tier modules extracted (deps satisfied)

Continuing the dependency-ordered M-tier rollout, the next safe batch of **6
M-tier modules** was extracted into `src/szl_substrate/`. Selection is strictly
dependency-ordered and drift-safe: **every module's shared-module dependency is
ALREADY in the package** (`szl_dsse`, `szl_restraint`, `szl_llm_registry`,
`szl_brain`), or is referenced only *lazily + guarded inside functions* and
degrades gracefully (`szl_energy_sovereign` for `szl_sapa`; `szl_brain` via a
`try/except -> None` guard for `a11oy_agent_loop`). Each file is **byte-identical
between a11oy and killinchu** (`cmp`-verified, none is a drifted/allow-listed
file), so each is extracted byte-for-byte.

| Module | Tier | Shared dep (status) | Import mode in package |
|--------|------|---------------------|------------------------|
| `szl_alloy_models.py` | M | `szl_llm_registry` ✅ moved (in-function, lazy) | eager (pure-stdlib at module scope) |
| `szl_mbse_cosim.py` | M | `szl_dsse` ✅ + `szl_restraint` ✅ moved (lazy) | eager (pure-stdlib at module scope) |
| `szl_sapa.py` | M | `szl_dsse` ✅ moved (lazy) + `szl_energy_sovereign` (lazy+guarded, degrades) | eager (pure-stdlib at module scope) |
| `a11oy_agent_loop.py` | M | `szl_brain` ✅ moved (module-level but `try/except -> None`) | eager (pure-stdlib at module scope) |
| `szl_waqay.py` | M | `szl_dsse` ✅ + `szl_restraint` ✅ moved (lazy) | import-directly (module-level `fastapi`) |
| `szl_yupay.py` | M | `szl_dsse` ✅ + `szl_restraint` ✅ moved (lazy) | import-directly (module-level `fastapi`) |

4 are eager-imported from `szl_substrate/__init__.py` (pure-stdlib at module
scope; their `szl_dsse` / `szl_restraint` / `szl_llm_registry` /
`szl_energy_sovereign` uses are lazy+guarded inside functions, and
`a11oy_agent_loop`'s `import szl_brain` is wrapped in `try/except -> None`, so the
module import never fails). The other 2 carry an **unguarded module-level
`from fastapi import Request`** (with a starlette fallback that also raises if
neither is installed) and are therefore **excluded from eager import** and
imported directly (`from szl_substrate import X`) only where fastapi/starlette is
present — exactly the pattern already used for `szl_llm_registry` /
`operator_shell_v4` / `szl_connectors_serve`. This keeps `import szl_substrate`
working everywhere (verified: the package still imports with `fastapi` absent).
Coverage: `tests/test_mtier_wave2.py` (full suite green).

`szl_rag` was **deliberately NOT moved** this pass: although `szl_brain` (its
dep) is in the package, `szl_rag` has genuinely **DRIFTED** between a11oy
(`organs/amaru/szl_rag.py`, library-only) and killinchu (adds an optional RRF
hybrid reranker stage) and is not on the reconciled-canonical allow-list, so it
fails the byte-identical / settled-canonical bar. `serve.py` and any module whose
deps have not moved (e.g. `szl_anatomy_routes` → unmoved `szl_formulas` at module
scope) were NOT touched.

**a11oy repoint (guarded, no self-merge).** The companion a11oy PR repoints each
of these call sites to prefer the package with a nested guarded fallback
(`try: from szl_substrate import X … except Exception: import X …local`). If the
package is absent the app falls back to its local vendored copy. **Nothing is
deleted from the apps; killinchu is untouched and the shared source surface is
unchanged, so the a11oy↔killinchu drift guard stays green.**

### M-tier wave 3 (this pass) — 2 M-tier modules extracted (deps satisfied)

Continuing the dependency-ordered M-tier rollout, the next safe batch of **2
M-tier modules** was extracted into `src/szl_substrate/`. Both were selected by
re-running the same `ast`-based dependency + `cmp` byte-identity analysis over
both fresh clones: they are the **only** remaining M modules whose
shared-module dependencies are all satisfied *and* that are byte-identical
between a11oy and killinchu (not drifted, not blocked by an unmoved S leaf,
`serve.py`, or the drifted `szl_rag`). Each is extracted byte-for-byte.

| Module | Tier | Shared dep (status) | Import mode in package |
|--------|------|---------------------|------------------------|
| `szl_live_wires.py` | M | none in shared set — `szl_wire` / `szl_jack` are app-specific and **guarded** (`try/except -> None`); `fastapi` guarded too | eager (pure-stdlib at module scope) |
| `szl_sapa_patch.py` | M | `szl_sapa` ✅ moved (module-level `import szl_sapa`) | import-directly (module-level `fastapi` + bare `import szl_sapa`) |

`szl_live_wires` is eager-imported from `szl_substrate/__init__.py`: every one of
its heavier imports (`fastapi`, and the app-specific `szl_wire` / `szl_jack`,
neither of which is in the shared 69-file set) is wrapped in a module-level
`try/except -> None`, so its module scope is pure-stdlib and `import
szl_substrate` never fails on their absence (verified with fastapi absent). Its
`register(app, ns=...)` integration point stays available regardless.

`szl_sapa_patch` carries an **unguarded module-level `import szl_sapa`** (a bare
top-level name) plus `from fastapi import Request`, so — exactly like `szl_waqay`
/ `szl_yupay` / `operator_shell_v4` — it is **excluded from eager import** and
imported directly (`from szl_substrate import szl_sapa_patch`) only where
`szl_sapa` and fastapi are present. This keeps `import szl_substrate` working
everywhere. Coverage: `tests/test_mtier_wave3.py` (full suite green: 57 passed).

The remaining M modules were **deliberately NOT moved** this pass because each
fails the safe-batch bar: `szl_anatomy_routes` (module-level `szl_formulas`,
an unmoved S leaf), `a11oy_autoreview` (unmoved `szl_conformal`),
`szl_unay_routes` (unmoved `szl_khipu_lmdb` / `szl_khipu_replicate` / `szl_unay`),
`a11oy_code_engine` / `szl_agentic_loop` (unmoved `szl_agentic_loop` /
`szl_anatomy_routes` / `szl_energy_sovereign` / `szl_formula_wiring` /
`szl_khipu_consensus`), `a11oy_org_rag` (depends on the **drifted** `szl_rag`),
`szl_energy_sovereign` (depends on the L-tier `szl_joules_truth`, not yet moved),
`szl_rag` (DRIFTED, not on the reconciled-canonical allow-list), and
`szl_spaces_proxy` / `szl_spaces_surface` (depend on `serve`, which never moves).
`serve.py` was NOT touched.

**a11oy repoint (guarded, no self-merge).** The companion a11oy PR repoints these
call sites to prefer the package with a nested guarded fallback
(`try: from szl_substrate import X … except Exception: import X …local`). If the
package is absent the app falls back to its local vendored copy. **Nothing is
deleted from the apps; killinchu is untouched and the shared source surface is
unchanged, so the a11oy↔killinchu drift guard stays green.**

### M-tier wave 4 (this pass) — dependency-ordered batch: 5 S leaves + 3 M modules

Continuing the dependency-ordered rollout, this pass first lands the **5 remaining
S-tier leaves that block the next M modules**, then the **3 M modules** those
leaves unblock — a single strictly dependency-ordered batch. Selection was
re-derived by re-running the same `ast`-dependency + `cmp` byte-identity analysis
over **fresh clones** of a11oy and killinchu. All 8 are **byte-identical between
a11oy and killinchu** at extraction time (`cmp`-verified against both root copies,
the drift-guard-comparable paths), **none is a drifted/allow-listed file**, so each
is extracted byte-for-byte. The 5 currently allow-listed/drifted modules
(`szl_rag`, `szl_v4_fleet`, `a11oy_code_engine`, `szl_agentic_loop`,
`szl_joules_truth`) were **deliberately excluded** — they carry `"…killinchu sync
pending"` allow-list entries and thus fail the settled-canonical bar.

| Module | Tier | Shared dep (status) | Import mode in package |
|--------|------|---------------------|------------------------|
| `szl_formulas.py` | S | none (leaf; 5 app + 1 shared importers) | eager (pure-stdlib) |
| `szl_conformal.py` | S | none (leaf) | eager (pure-stdlib) |
| `szl_khipu_replicate.py` | S | none (leaf) | eager (pure-stdlib) |
| `szl_unay.py` | S | none (leaf) | eager (pure-stdlib) |
| `szl_khipu_lmdb.py` | S | none (leaf) — but **unguarded `import lmdb`** | import-directly (not eager) |
| `a11oy_autoreview.py` | M | `szl_calibration` ✅ + `szl_conformal` ✅ (this batch) + `szl_restraint` ✅ — ALL guarded (`try/except -> None`) | eager (module scope pure-stdlib) |
| `szl_anatomy_routes.py` | M | `szl_formulas` ✅ (this batch, **module-level bare import**); fastapi guarded | import-directly (not eager) |
| `szl_unay_routes.py` | M | `szl_unay` ✅ + `szl_khipu_lmdb` ✅ + `szl_khipu_replicate` ✅ (this batch, **module-level bare imports**); fastapi guarded | import-directly (not eager) |

5 are eager-imported from `szl_substrate/__init__.py` (pure-stdlib at module
scope; `a11oy_autoreview`'s shared-dep imports are all wrapped in
`try/except -> None`). The other 3 carry an **unguarded module-level import**
(`szl_khipu_lmdb` → `lmdb`; `szl_anatomy_routes` → bare `import szl_formulas`;
`szl_unay_routes` → bare `import szl_unay`/`szl_khipu_lmdb`/`szl_khipu_replicate`)
and are therefore **excluded from eager import** and imported directly
(`from szl_substrate import X`) only where those names resolve — exactly the
pattern already used for `szl_connectors_serve` / `szl_sapa_patch`. This keeps
`import szl_substrate` working everywhere (**verified: the package still imports
with both `fastapi`-absent-path and `lmdb` absent**). Coverage:
`tests/test_mtier_wave4.py`; **full suite 67 passed**; `py_compile` clean.

The remaining unmoved modules still fail the safe-batch bar: `szl_rag` /
`szl_v4_fleet` / `a11oy_code_engine` / `szl_agentic_loop` / `szl_joules_truth`
(allow-listed drift, "killinchu sync pending"), `a11oy_org_rag` (module-level
guarded `szl_rag`, but the app-side blast radius spans the drifted `szl_rag`
surface), `szl_energy_sovereign` (depends on the L-tier drifted `szl_joules_truth`),
`test_szl_hf_bucket` (bare `import szl_hf_bucket`, an unmoved S leaf),
`szl_spaces_proxy` / `szl_spaces_surface` (depend on `serve`, which never moves).
`serve.py` was NOT touched.

**a11oy repoint (guarded, no self-merge).** The companion a11oy PR extends the
`szl_dsse` guarded-shim POC to more call sites (a11oy-only files) with a nested
guarded fallback (`try: from szl_substrate import X … except Exception: import X
…local`). **Nothing is deleted from the apps; killinchu is untouched and the
shared source surface is unchanged, so the a11oy↔killinchu drift guard stays green.**

## Drift reconciliation (Wave-E dev 5)

The 4 files flagged as **DRIFTED** were inspected line-by-line across both repos.
The drift fell into two categories — **accidental** (a fix or asset landed in one
app only: the exact "fixed-in-one-app-only" risk this package exists to kill) and
**legitimate per-app divergence** (config or app-specific content). Each was
handled honestly, without fabricating data:

| File | Nature of drift | Canonical decision |
|------|-----------------|--------------------|
| `_vendor_blobs.py` | **Accidental.** a11oy carries **63** base64 asset blobs; killinchu carries only **21**. killinchu's set is a **strict subset** — every shared key is byte-identical (verified by decode+compare); killinchu is simply missing the two UI fonts (SpaceGrotesk, JetBrainsMono) and all KaTeX `.ttf`/`.woff` fallbacks. | **a11oy (superset).** Extracted byte-identical. killinchu converges *up* to the superset; the extra fonts are unused where a route doesn't serve them — a harmless no-op. |
| `szl_be_hardening.py` | **Mixed.** The rate-limit exempt route lists are app-specific (a11oy `/frontier,/warhacker,…`; killinchu `/drones,/navy,/api/killinchu/…`). But a11oy also carried an **SEC-08 `Server` header redaction** (`resp.headers["Server"]="szl"`) that killinchu had **dropped** — accidental loss of a security fix. | **Reconciled UNION.** Exempt-exact + exempt-prefix sets are the union of both apps' routes (exempting a route an app doesn't define is a no-op); the metered data surface adds killinchu's `/mesh/*`; and the **SEC-08 header is restored** so both apps get the fix. |
| `szl_evidence_research.py` | **Mixed.** killinchu's `CLAIMS` map is a **superset** (adds `finance-live-feeds`, `real-estate-grounding`, `fraud-controls` — all citing real, resolvable sources). The only other delta is the OpenAlex polite-pool contact default (`_MAILTO`): a11oy → `a-11-oy.com`, killinchu → `a11oy.net` (each correct for its own site per Doctrine). | **killinchu (superset claims)** with `_MAILTO` defaulting to the **canonical org domain** `research@a-11-oy.com`, still overridable per-deployment via `SZL_EVIDENCE_MAILTO` (killinchu keeps `a11oy.net` that way). No claim or URL was invented. |
| `serve.py` | **Legitimate.** ~15k lines differ: a11oy is the "Brand Orchestration Layer" React-SPA server; killinchu is the "Andean Drone Intelligence" server. These are **two different applications** that happen to share a filename. | **Not a shared module.** `serve.py` stays per-app (it was already L-tier "never move"). Its drift flag is removed — there is nothing to reconcile into a shared copy. |

The three reconciled modules are eager-imported from `szl_substrate/__init__.py`
(pure-stdlib at module scope; their `szl_dsse`/app-specific imports are lazy +
guarded inside functions, so package import never fails). Apps adopt them through
the same guarded shim as every other module — prefer the package, fall back to the
local vendored copy. Coverage: `tests/test_mtier_reconcile.py`.

## Recommended rollout order

1. ~~**Reconcile the 4 drifted files** to one canonical copy (out of band).~~
   **DONE (Wave-E dev 5)** — 3 reconciled + extracted here; `serve.py` reclassified
   as per-app (never shared). See [Drift reconciliation](#drift-reconciliation-wave-e-dev-5).
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
| 15 | `szl_khipu_lmdb.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (unguarded `import lmdb` → import-directly) |
| 16 | `szl_khipu_replicate.py` | **S** | leaf: no local imports; used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (eager) |
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
| 29 | `szl_unay.py` | **S** | leaf: no local imports; used by 1 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (eager) |
| 30 | `szl_codename_gate.py` | **S** | leaf: no local imports; used by 2 app + 0 shared file(s) |
| 31 | `szl_conformal.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (eager) |
| 32 | `szl_cuas_formulas.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 33 | `szl_hf_bucket.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 34 | `szl_khipu_consensus.py` | **S** | leaf: no local imports; used by 2 app + 1 shared file(s) |
| 35 | `szl_v4_fleet.py` | **S** | leaf: no local imports; used by 2 app + 0 shared file(s) |
| 36 | `szl_formulas.py` | **S** | leaf: no local imports; used by 5 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (eager) |
| 37 | `operator_shell_v4.py` | **M** | imports shared: szl_dsse (lazy); used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 1)** (module-level fastapi → import-directly) |
| 38 | `szl_alloy_models.py` | **M** | imports shared: szl_llm_registry (in-function, lazy); used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 2)** (eager) |
| 39 | `szl_anatomy_routes.py` | **M** | imports shared: szl_formulas; used by 0 app + 2 shared file(s) ✅ **MOVED (M-tier wave 4)** (module-level `import szl_formulas` → import-directly) |
| 40 | `szl_rag.py` | **M** | imports shared: szl_brain; used by 0 app + 3 shared file(s) |
| 41 | `szl_sapa_patch.py` | **M** | imports shared: szl_sapa; used by 0 app + 0 shared file(s) ✅ **MOVED (M-tier wave 3)** (module-level fastapi + bare `import szl_sapa` → import-directly) |
| 42 | `szl_spaces_proxy.py` | **M** | imports shared: serve; used by 0 app + 1 shared file(s) |
| 43 | `szl_spaces_surface.py` | **M** | imports shared: serve; used by 0 app + 1 shared file(s) |
| 44 | `szl_warhacker_aliases.py` | **M** | imports shared: szl_dsse; used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 1)** (module-level fastapi → import-directly) |
| 45 | `test_szl_hf_bucket.py` | **M** | imports shared: szl_hf_bucket; used by 0 app + 0 shared file(s) |
| 46 | `szl_brain.py` | **M** | imports shared: szl_rag; used by 1 app + 4 shared file(s) ✅ **MOVED (this pass)** |
| 47 | `szl_ken.py` | **M** | imports shared: szl_dsse; used by 1 app + 1 shared file(s) ✅ **MOVED (M-tier wave 1)** (eager) |
| 48 | `szl_llm_registry.py` | **M** | imports shared: szl_rag (lazy+guarded, degrades); used by 1 app + 3 shared file(s) ✅ **MOVED (M-tier wave 1)** (module-level fastapi → import-directly) |
| 49 | `szl_provenance.py` | **M** | imports shared: szl_dsse (module-level); used by 1 app + 1 shared file(s) ✅ **MOVED (M-tier wave 1)** (import-directly) |
| 50 | `szl_qhawaq.py` | **M** | imports shared: szl_dsse; used by 1 app + 0 shared file(s) ✅ **MOVED (M-tier wave 1)** (eager) |
| 51 | `szl_sapa.py` | **M** | imports shared: szl_dsse (lazy), szl_energy_sovereign (lazy+guarded, degrades); used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 2)** (eager) |
| 52 | `szl_restraint.py` | **M** | imports shared: szl_joules_truth (lazy+guarded, degrades); used by 4 app + 5 shared file(s) ✅ **MOVED (M-tier wave 1)** (eager) |
| 53 | `szl_mbse_cosim.py` | **M** | imports shared: szl_dsse, szl_restraint (lazy); used by 1 app + 0 shared file(s) ✅ **MOVED (M-tier wave 2)** (eager) |
| 54 | `szl_waqay.py` | **M** | imports shared: szl_dsse, szl_restraint (lazy); used by 1 app + 1 shared file(s) ✅ **MOVED (M-tier wave 2)** (module-level fastapi → import-directly) |
| 55 | `szl_yupay.py` | **M** | imports shared: szl_dsse, szl_restraint (lazy); used by 1 app + 0 shared file(s) ✅ **MOVED (M-tier wave 2)** (module-level fastapi → import-directly) |
| 56 | `a11oy_code_engine.py` | **M** | imports shared: szl_agentic_loop, szl_llm_registry; used by 2 app + 1 shared file(s) |
| 57 | `_vendor_blobs.py` | **M** | leaf: no local imports; used by 0 app + 1 shared file(s); ✅ **RECONCILED + MOVED (Wave-E dev 5)** — canonical = a11oy superset (63 blobs) |
| 58 | `a11oy_autoreview.py` | **M** | imports shared: szl_calibration, szl_conformal, szl_restraint (all guarded); used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (eager) |
| 59 | `szl_evidence_research.py` | **M** | leaf: no local imports; used by 0 app + 1 shared file(s); ✅ **RECONCILED + MOVED (Wave-E dev 5)** — canonical = killinchu superset claims + canonical-domain mailto (env-overridable) |
| 60 | `szl_unay_routes.py` | **M** | imports shared: szl_khipu_lmdb, szl_khipu_replicate, szl_unay; used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 4)** (module-level bare imports → import-directly) |
| 61 | `a11oy_org_rag.py` | **M** | imports shared: szl_brain, szl_rag, szl_waqay; used by 3 app + 1 shared file(s) |
| 62 | `a11oy_agent_loop.py` | **M** | imports shared: szl_brain (module-level, `try/except -> None`); imports app-specific (lazy/guarded): a11oy_active_flux_router; used by 2 app + 0 shared file(s) ✅ **MOVED (M-tier wave 2)** (eager) |
| 63 | `szl_live_wires.py` | **M** | imports app-specific (lazy/guarded): szl_jack, szl_wire; used by 0 app + 1 shared file(s) ✅ **MOVED (M-tier wave 3)** (eager — all heavier imports guarded) |
| 64 | `szl_energy_sovereign.py` | **M** | imports shared: szl_joules_truth; imports app-specific (lazy/guarded): a11oy_code_orchestrator, szl_energy_operator; used by 4 app + 3 shared file(s) |
| 65 | `szl_be_hardening.py` | **M** | imports shared: szl_dsse (lazy/guarded); imports app-specific (lazy/guarded): szl_cheapest_watt, szl_energy_operator; used by 0 app + 1 shared file(s); ✅ **RECONCILED + MOVED (Wave-E dev 5)** — canonical = union of exempt routes + restored SEC-08 Server redaction |
| 66 | `szl_agentic_loop.py` | **M** | imports shared: szl_anatomy_routes, szl_energy_sovereign, szl_formula_wiring, szl_khipu_consensus; imports app-specific (lazy/guarded): szl_ltc_dynamics, szl_sgh_scheduler; used by 1 app + 2 shared file(s) |
| 67 | `szl_joules_truth.py` | **L** | leaf: no local imports; used by 11 app + 2 shared file(s) |
| 68 | `szl_dsse.py` | **L** | imports app-specific (lazy/guarded): szl_corpus_publish; used by 23 app + 10 shared file(s) ✅ **MOVED (this pass)** |
| 69 | `serve.py` | **L** | imports 37 shared modules; imports 120 app-specific modules (lazy/guarded); used by 1 app + 2 shared file(s); **PER-APP ENTRYPOINT — never shared.** Drift is legitimate (a11oy Brand-Orchestration vs killinchu Drone-Intelligence are different apps); reconciliation = keep per-app (Wave-E dev 5) |

---

Doctrine v11 LOCKED (749/14/163) · Λ = Conjecture 1 (advisory) · SLSA L1 honest ·
L2 roadmap · Apache-2.0.

# szl-substrate domain leader study r1 (propose-only)

Date: 2026-11-24. Method: web-verified leader landscape + governing-seat synthesis (Kimi nonce T5-SZL-SUBSTRATE-BRIEF). This card is documentation only; it changes no code, CI, config, or existing PR status. All absorb actions are FUTURE PROPOSALS (non-authorizing); implementation and merges remain separately reviewed and gated.

## Domain: single-source shared substrate for estate apps (guarded-import extraction, UNSIGNED-honest DSSE)

## Leaders studied (web-verified 2026-11-24)
1. Sigstore Cosign (https://github.com/sigstore/cosign) — moat: the key-based/blob signing tool whose envelope compatibility szl_dsse targets.
2. Turborepo (https://github.com/vercel/turborepo) — moat: the shared-code monorepo discipline (single source, cached builds) that extraction projects look to for multi-app lockstep.
3. DSSE specification (https://github.com/secure-systems-lab/dsse) — moat: the standard signing envelope the estate already uses and honestly labels UNSIGNED when no key arms.

## Absorb actions (FUTURE PROPOSALS, non-authorizing)
1. (Sigstore Cosign) Propose a receipted compatibility matrix for szl_dsse ECDSA-P256-SHA256 envelopes against the stated cosign cosmetics target, retaining UNSIGNED-honest fallback, org key verification, and non-finite numeric rejection. No proven trust, universal cosign compatibility, or implementation is claimed; results remain unmeasured until a separately gated live run.
2. (Turborepo) Propose a single-source lockstep checklist for a11oy and killinchu that addresses the HONEST GAP: commented-out package requirements and the dated 2026-11-06 parity result of only 23-24 of 68 modules byte-identical versus the apps. Any guarded-shim or vendored-copy retirement would require fresh parity receipts and separate review; no migration, build caching, or speedup is claimed.
3. (DSSE specification) Propose conformance fixtures for signed and UNSIGNED-honest envelope paths, with explicit labels for armed versus unarmed signing and preservation of the existing numeric boundary. This would not make zl_brain Lambda more than advisory Conjecture 1 OPEN, and no theorem, security guarantee, or implementation is claimed.
4. (baseline) Propose a dated baseline receipt restating the 68-of-69 byte-identical extraction scope, serve.py as the per-app entrypoint that never moves, bounded and terminating Ouroboros agent-loop modules, SLSA L1 honest status, and vsp-otel and szl-mesh as active standalone owners under archive-portfolio v2. Current package use by the apps remains UNAVAILABLE under the verified HONEST GAP; this baseline authorizes no code, CI, config, dependency, or PR change.

## Do not do (per governing seat)
Do not merge, bypass the signature wall, or claim implementation beyond this card.

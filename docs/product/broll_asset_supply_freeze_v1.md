# B-roll / Asset Supply Product Freeze v1

Date: 2026-05-01
Status: Frozen product authority for B-roll / Asset Supply wiring
Owner: Product
Scope: B-roll / Asset Supply surface only

## Purpose

This document freezes the B-roll / Asset Supply product decisions that
blocked wiring of the operator-visible Asset Supply page.

The B-roll / Asset Supply page belongs to the Asset Library /素材供给区. It is
not a task surface, not a delivery surface, and not a tool/provider surface.
It carries asset browsing, filtering, reference, and explicit promote intent
only.

## Boundary

Normative rules:

- Asset and Artifact remain separate stores.
- A task artifact can become an asset only through an explicit promote flow.
- The B-roll page does not author task state, deliverable truth, packet truth,
  ready state, publish state, provider choice, model choice, or runtime route.
- The B-roll page never exposes `vendor`, `model`, `provider`, `engine`, donor,
  worker-routing, or tool-backstage identifiers.
- UI actions emit intent; asset library ownership and governance remain outside
  the operator page.

## 1. Filter Taxonomy

First batch first-class facets:

| Facet | Status | Value domain | Multi-select | Operator-visible |
| --- | --- | --- | --- | --- |
| `line` | kept | Closed line ids: `hot_follow`, `matrix_script`, `digital_anchor` | yes | yes |
| `topic` | kept | Product taxonomy tags owned by Asset Library metadata; free text is search only, not a facet value | yes | yes |
| `style` | kept | Controlled style tags owned by Asset Library metadata, e.g. pacing, visual tone, framing family; no provider/model names | yes | yes |
| `language` | kept | BCP-47-like public language codes used by product surfaces, e.g. `zh`, `en`, `my`; display labels localized | yes | yes |
| `role_id` | kept | Opaque role catalog ids for Digital Anchor role assets only | yes | yes, only when role-capable assets are in result scope |
| `scene` | kept | Controlled scene taxonomy ids owned by Asset Library metadata, e.g. `indoor`, `outdoor`, `studio`, `product_demo` | yes | yes |
| `variation_axis` | kept | Controlled Matrix Script axis ids, e.g. `hook`, `cta`, `audience`, `offer`, `angle` | yes | yes, only when Matrix Script/template assets are in result scope |
| `quality_threshold` | kept | Numeric minimum quality score bucket: `any`, `>=0.6`, `>=0.75`, `>=0.9` | no | yes |

Deferred first-batch facets:

- None of the eight candidate facets are dropped. Facets may be hidden by UI
  context when not applicable, but they remain first-class filter API concepts
  for the first wiring pass.

Facet semantics:

- Multi-select facets use OR within one facet and AND across facets.
- `quality_threshold` is a lower-bound filter, not a quality truth editor.
- Facets are projections of asset metadata. The operator cannot create new
  facet values from the B-roll page.

## 2. Promote Semantics

Frozen main path: **create new asset via async review-gated promote intent**.

Promote is not versioning in this first product pass. It always proposes a new
asset object derived from an artifact reference. The resulting asset becomes
visible in the Asset Library only after the promote job completes and passes
the configured review gate.

Operator initiation:

- Operator initiates Promote from the B-roll / Asset Supply page when viewing
  an eligible artifact hand-off entry or from a Delivery/Workbench hand-off
  that routes to the same promote intent boundary.
- The B-roll page submits `promote_intent` with opaque artifact id, proposed
  asset type, title/tags, intended line availability, and source/license
  metadata.

Object boundary before completion:

- Artifact remains in Artifact Store and keeps all task/deliverable ownership.
- Promote intent is a request object, not an asset.
- No asset id is guaranteed until the review-gated promote process accepts it.

Object boundary after completion:

- Accepted promote creates a new Asset Library object with a new `asset_id`.
- The new asset records provenance back to the source artifact id, hash, and
  task lineage.
- The artifact remains unchanged and is not moved into the Asset Library.

Review and visibility:

- Admin review is required before reusable library visibility.
- Operator receives asynchronous visible status: `submitted`, `under_review`,
  `accepted`, or `rejected`.
- The submit call may return a promote request id synchronously, but not a
  reusable asset object.

## 3. License / Source / Reuse Policy Field Set

Mandatory fields on every Asset Library object:

- `asset_id`
- `asset_type`
- `title`
- `source`
- `license`
- `reuse_policy`
- `available_to_lines`
- `provenance.origin_kind`
- `provenance.origin_ref`
- `provenance.content_hash`
- `created_at`
- `created_by`
- `quality.summary`

Mandatory fields on promote intent:

- source `artifact_id`
- target `asset_type`
- proposed `title`
- proposed `source`
- proposed `license`
- proposed `reuse_policy`
- proposed `available_to_lines`
- provenance content hash when available

`source` enum for this round:

- `operator_upload`
- `task_artifact_promote`
- `external_reference`
- `licensed_stock`
- `admin_seeded`

`license` enum for this round:

- `owned`
- `licensed_reuse_allowed`
- `licensed_single_use`
- `public_domain`
- `unknown_review_required`

Reuse restriction visibility:

- Operator-visible: `reuse_policy`, available-to-lines, human-readable license
  label, source label, and visible restriction notes.
- Admin-only: raw license document, contract ids, submitter audit, reviewer
  identity, internal risk notes, storage backend paths, and any provider/tool
  execution metadata.

`reuse_policy` enum:

- `reuse_allowed`
- `line_limited`
- `task_limited`
- `review_required`
- `blocked`

## 4. Canonical / Reusable Marking

Frozen model: **admin-only state with operator-visible read-only badges**.

Definitions:

- `reusable` means the asset may be referenced into new tasks under its
  `reuse_policy` and `available_to_lines`.
- `canonical` means the asset is the preferred reference for a specific
  product taxonomy slot, role, scene, template, or campaign family.
- Canonical is not equal to reusable. Every canonical asset must be reusable;
  not every reusable asset is canonical.

Operator behavior:

- Operator can see `reusable` and `canonical` badges.
- Operator cannot directly change either state.
- Operator may submit a `mark_reusable_or_canonical_intent`, but the state is
  changed only in the admin/governance path.

Approval chain:

- Required for both reusable and canonical state changes.
- Approval lives in the admin management surface, not in B-roll.

## 5. Detail Actions Scope

| Action | Operator-visible on B-roll page | Decision |
| --- | --- | --- |
| `archive` | no | Admin management control only |
| `deprecate` | no | Admin management control only |
| `supersede` | no | Admin management control only |
| `unlink` | no | Admin management control only |
| `replace_preview` | no | Admin management control only |

The operator page may show read-only badges such as archived/deprecated when
the Asset Library projects them, but it cannot perform those actions.

## 6. Artifact To Asset Hand-off Boundary

Artifact-to-asset flow:

1. Artifact is produced under task/delivery ownership.
2. Operator explicitly starts promote intent.
3. Promote intent captures source artifact ref, proposed asset metadata, and
   provenance.
4. Admin/review-gated promote process validates policy, license, quality, and
   reuse eligibility.
5. Accepted promote creates a new Asset Library object.
6. Rejected promote leaves the artifact unchanged and creates no asset.

UI authority:

- UI can only initiate promote intent and display request status.
- UI cannot directly complete promote.
- UI cannot write Asset Library truth.
- Promote depends on backend/admin review before reusable visibility.

Asset != Artifact guarantee:

- Artifact ids and asset ids are different namespaces.
- Promote copies or references immutable artifact content into asset provenance;
  it does not move task artifacts.
- Asset Library cards are projected only from Asset Library objects, never from
  raw Artifact Store rows.

## 7. Reference Into Task Pre-population Mapping

| Asset type / ref | Allowed lines | New Tasks pre-population target | Notes |
| --- | --- | --- | --- |
| `role_ref` | `digital_anchor` | `role_profile_ref` / `digital_anchor_role_pack.appearance_ref` | Opaque role id only; no model/provider metadata |
| `reference_video` | `hot_follow` | Hot Follow intake `reference_url` or `source_video` ref | Used as primary reference input |
| `template` | `matrix_script`, `digital_anchor` | Matrix Script seed template refs; Digital Anchor scene/template hint | Does not create packet truth until New Tasks submits |
| `variation_axis` | `matrix_script` | `variation_axes_decl` / Matrix Script variation seed | Axis ids and candidate values only |
| `background` | `matrix_script`, `digital_anchor` | `reference_assets[]` with background role; Digital Anchor scene binding hint when applicable | Optional, never ready-state truth |
| `broll` | `hot_follow`, `matrix_script`, `digital_anchor` | `reference_assets[]` with broll role | Optional reference material; not a deliverable |
| `product_shot` | `matrix_script` | `reference_assets[]` with product shot role | Optional product evidence / visual seed |
| `scene_pack_ref` | `hot_follow`, `matrix_script`, `digital_anchor` | `reference_assets[]` with scene-pack reference role | Optional; absence never blocks publish |
| `audio_ref` | `hot_follow`, `matrix_script`, `digital_anchor` | Hot Follow `source_audio` ref when separated; Matrix Script optional audio reference; Digital Anchor audio/voice reference hint | Opaque audio ref only; no TTS/provider selection |

Pre-population rules:

- B-roll passes only `asset_id`, `asset_type`, display label, and allowed
  mapping target.
- New Tasks owns packet creation and validation.
- If an asset is not allowed for the selected line, New Tasks must reject or
  ignore the pre-population intent.

## Deferred Items

Deferred beyond this freeze:

- Facet value administration UI.
- Bulk asset import.
- Bulk promote.
- Asset versioning as the primary promote path.
- Operator-side archive/deprecate/supersede/unlink/replace-preview actions.
- Provider/tool/runtime metadata on the asset surface.

## Wiring Readiness

B-roll wiring may open after review of this freeze document. The next wiring
step must be scoped to projection/intent consumption only and must not add UI
truth ownership, packet/schema redesign, Platform Runtime Assembly, W2.2/W2.3,
or provider/model/vendor concepts.

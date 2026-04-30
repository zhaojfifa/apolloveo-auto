# ops/env/

**Status**: P1.5 host reservation (empty until env / runtime patterns are captured)
**Authority**: Master Plan v1.1 Part I Q8, Part IV.1; Donor Boundary §3.7; Capability Mapping rows O-01..O-03

## Purpose

Independent operations domain (NOT one of the back-end ten domains). Hosts:

- `env_matrix_v1.md` — provider env-key matrix (planned; absorbed pattern from SwiftCraft `.env.example`)
- `storage_layout_v1.md` — storage layout (R2 / S3 split, regional assumptions; absorbed pattern from SwiftCraft)
- Future env / runtime / deploy patterns

## Consumes

- ApolloVeo deploy and runtime configuration
- (Pattern reference) SwiftCraft env organization

## Does not

- Hold business truth or task state
- Expose secrets — secret values live in deploy systems / vaults; this directory documents key shape and organization only
- Import any `swiftcraft.*` package — pattern reference only

## Absorption pre-condition

Patterns captured here per Capability Mapping rows O-01..O-03 (Pattern-only). No file copy from SwiftCraft.

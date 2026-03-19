# Engineering Rules

## 1. File Size Rules

- router file target: `< 1200` lines
- service file target: `< 900` lines
- oversized threshold:
  - router: `> 1800` lines
  - service: `> 1400` lines
- if a file crosses the oversized threshold, the PR must state a thinning plan or a follow-up thinning path

## 2. Function Size Rules

- normal function target: `< 40` lines
- orchestration function target: `< 80` lines
- decomposition threshold:
  - normal function: `> 60` lines
  - orchestration function: `> 120` lines

## 3. Router Rules

Router may only own:

- request parsing
- auth / permission entry
- response mapping
- thin compatibility wrapper

Router must not own:

- business orchestration
- media flow control
- line-specific state logic
- artifact truth derivation

## 4. Service Rules

- service owns business / runtime flow
- service must not become a dumping ground
- unrelated orchestration must be split instead of appended

## 5. Import / Dependency Rules

- no router-to-router coupling
- no circular imports
- no lazy import used to hide architecture problems
- cross-boundary interaction should go through service / contract / registry boundaries

## 6. Contract-First Rules

- if runtime semantics change, the related contract / runbook / execution doc must be updated in the same PR
- do not let docs lag behind behavior changes

## 7. Compatibility Rules

- compatibility helpers must be explicitly temporary
- new compatibility helpers require a stated removal path
- compatibility code must not absorb new business logic

## 8. Truth-Source Rules

- presentation must derive from artifact / runtime facts
- legacy status must not override fact-based truth
- no UI patching to hide source-of-truth problems

## 9. Validation Rules

- no merge without required regression
- interpreter / environment must be stated
- distinguish code regressions from environment limitations

## 10. Scope Control Rules

Every PR must state:

- what it fixes
- what it does not fix
- what remains follow-up
